#!/usr/bin/env python3
"""
ULX Universa — reference implementation (lexer, parser, bytecode compiler,
VM, invariant engine, signal system, anchor system, stdlib, REPL, CLI).

Implements ULX-SPEC-0001 v0.1 (draft) PLUS the v0.2 ratification decisions
below. This file is the reference *interpreter*, not a conformant compiler
— see Decision #6.

v0.2 RATIFICATION DECISIONS (resolving v0.1's grammar/example inconsistencies):

  RATIFIED — now part of the formal grammar:
  1. Member access (`a.b.c`) — added as postfix `.` IDENTIFIER, chainable.
  2. Record literals (`TypeName { field: expr, ... }`) — added in expression
     position. Disambiguated structurally, not by capitalization: blocks
     are only ever produced by explicit `parse_block()` call sites
     (function bodies, if/else, match, observe) and never appear in
     primary-expression position, so IDENTIFIER immediately followed by
     `{` is unambiguously a record literal — no runtime type registry
     needed at parse time. Field validity against a declared type is a
     separate, deferred concern (see Decision #6).
  4. `rollback: expr;` — ratified as a statement keyword, alongside
     `anchor:` and `enforce:` (not sugar for calling the stdlib fn).
  5. `.ulxb` bytecode format — ratified as JSON, tagged "ULXB-JSON-v1".
     Binary encoding is reserved for a later version, not defined here.
  8. Arithmetic operators (`+ - * / %`) — ratified with conventional
     precedence (multiplicative binds tighter than additive), since
     Section 2.3's operator table omitted them entirely despite Section
     8.3's own example requiring division.

  DEFERRED:
  6. Static type checking (required by Section 4.3 at module/constitution
     boundaries) — NOT implemented. This interpreter performs runtime
     tagging only (Lawful/Governed/Signal/Trust wrapper classes). A
     program that would fail static type-checking under a conformant
     compiler may still run here. Do not treat successful execution under
     this file as proof of type-conformance.

  REJECTED — removed; these are now parse errors, not accepted syntax:
  3. `expr to expr` call-sugar (`data.transmit to UNVERIFIED_CHANNEL`) —
     rejected. `to` is no longer a keyword. Write explicit calls instead:
     `data.transmit(UNVERIFIED_CHANNEL)`.
  7. Inline `always:`/`never:`/`when: ... then:` used as statements inside
     a function body (as Section 8.2/8.3's examples did) — rejected.
     `always`/`never`/`when` are reserved exclusively for `@article`
     invariant declarations. Use `enforce:` and `if` inside function
     bodies instead.
"""

import sys
import os
import re
import json
import time
import hashlib
import argparse
from dataclasses import dataclass, field
from typing import Any, Optional


# ============================================================
# 1. LEXER
# ============================================================

KEYWORDS = {
    "always", "anchor", "any", "article", "assert", "bind", "bool",
    "constitution", "declare", "emit", "enforce", "float", "fn",
    "governed", "int", "lawful", "let", "match", "module", "never",
    "observe", "pure", "reactive", "return", "signal", "sovereign",
    "str", "then", "trust", "type", "void", "when", "with",
    "rollback", "if", "else", "true", "false",
}

# multi-char operators must be tried longest-first
OPERATORS = ["->", "=>", "|>", "::", "==", "!=", ">=", "<=", "&&", "||",
             "=", ">", "<", "!", ":", ";", ",", ".", "(", ")", "{", "}",
             "[", "]"]

TOKEN_RE = re.compile(r"""
    (?P<WS>\s+)
  | (?P<LCOMMENT>//[^\n]*)
  | (?P<MCOMMENT>/\*.*?\*/)
  | (?P<DOC>@doc\s*\{[^}]*\})
  | (?P<FLOAT>\d+\.\d+(?:[eE][+-]?\d+)?)
  | (?P<INT>\d[\d_]*)
  | (?P<STRING>"(?:[^"\\]|\\.)*")
  | (?P<ANNOTATION>@[a-zA-Z_][a-zA-Z0-9_]*)
  | (?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)
  | (?P<OP>->|=>|\|>|::|==|!=|>=|<=|&&|\|\||[=><!:;,.\(\)\{\}\[\]+\-*/%])
""", re.VERBOSE | re.DOTALL)


@dataclass
class Token:
    kind: str
    value: str
    pos: int


class LexError(Exception):
    pass


def lex(source: str) -> list:
    tokens = []
    i = 0
    n = len(source)
    while i < n:
        m = TOKEN_RE.match(source, i)
        if not m:
            raise LexError(f"Unexpected character {source[i]!r} at {i}")
        i = m.end()
        kind = m.lastgroup
        text = m.group()
        if kind in ("WS", "LCOMMENT", "MCOMMENT", "DOC"):
            continue
        if kind == "IDENT" and text in KEYWORDS:
            tokens.append(Token(text, text, m.start()))
        elif kind == "IDENT":
            tokens.append(Token("IDENT", text, m.start()))
        elif kind == "ANNOTATION":
            tokens.append(Token("ANNOTATION", text, m.start()))
        elif kind == "STRING":
            tokens.append(Token("STRING", json.loads(text), m.start()))
        elif kind == "FLOAT":
            tokens.append(Token("FLOAT", float(text), m.start()))
        elif kind == "INT":
            tokens.append(Token("INT", int(text.replace("_", "")), m.start()))
        elif kind == "OP":
            tokens.append(Token(text, text, m.start()))
        else:
            raise LexError(f"Unhandled token kind {kind}")
    tokens.append(Token("EOF", "", n))
    return tokens


# ============================================================
# 2. AST
# ============================================================

class Node:
    """Base AST node — subclasses are plain attribute bags for brevity."""
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)

    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items() if k != "kind"}
        return f"{self.kind}({attrs})"


# ============================================================
# 3. PARSER (recursive descent)
# ============================================================

class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peek(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def at(self, kind):
        return self.peek().kind == kind

    def advance(self):
        t = self.toks[self.i]
        if self.i < len(self.toks) - 1:
            self.i += 1
        return t

    def expect(self, kind):
        if not self.at(kind):
            t = self.peek()
            raise ParseError(f"Expected {kind!r}, got {t.kind!r} ({t.value!r}) at {t.pos}")
        return self.advance()

    # ---- program ::= constitution? module* ----
    def parse_program(self):
        constitution = None
        modules = []
        if self.at("ANNOTATION") and self.peek().value == "@constitution":
            constitution = self.parse_constitution()
        while not self.at("EOF"):
            modules.append(self.parse_module())
        return Node("Program", constitution=constitution, modules=modules)

    def parse_constitution(self):
        self.expect("ANNOTATION")  # @constitution
        self.expect("{")
        articles = []
        while self.at("ANNOTATION") and self.peek().value == "@article":
            articles.append(self.parse_article())
        self.expect("}")
        return Node("Constitution", articles=articles)

    def parse_article(self):
        self.expect("ANNOTATION")  # @article
        name = self.expect("IDENT").value
        self.expect("{")
        invariants = []
        while not self.at("}"):
            invariants.append(self.parse_invariant())
        self.expect("}")
        return Node("Article", name=name, invariants=invariants)

    def parse_invariant(self):
        if self.at("always"):
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            self.expect(";")
            return Node("Always", expr=expr)
        if self.at("never"):
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            self.expect(";")
            return Node("Never", expr=expr)
        if self.at("when"):
            # Spec's own examples (Sec. 6.1 etc.) put a colon after `when`
            # too ("when: x then: y;"), though the EBNF in Sec. 3 shows
            # `'when' expression 'then' ':' expression ';'` with no colon
            # after `when`. Accept the colon since every actual example has it.
            self.advance()
            self.expect(":")
            trigger = self.parse_expression()
            self.expect("then")
            self.expect(":")
            response = self.parse_expression()
            self.expect(";")
            return Node("WhenThen", trigger=trigger, response=response)
        raise ParseError(f"Expected invariant, got {self.peek()}")

    # ---- module ::= 'module' IDENT governed_context '{' declaration* '}' ----
    def parse_module(self):
        self.expect("module")
        name = self.expect("IDENT").value
        authority = self.parse_governed_context()
        self.expect("{")
        decls = []
        while not self.at("}"):
            decls.append(self.parse_declaration())
        self.expect("}")
        return Node("Module", name=name, authority=authority, decls=decls)

    def parse_governed_context(self):
        self.expect("[")
        level = self.advance().kind  # pure|lawful|reactive|sovereign
        self.expect("]")
        return level

    def parse_declaration(self):
        if self.at("fn"):
            return self.parse_function()
        if self.at("type"):
            return self.parse_type_def()
        if self.at("bind"):
            return self.parse_bind()
        if self.at("observe"):
            return self.parse_observe()
        if self.at("emit"):
            return self.parse_emit_decl()
        raise ParseError(f"Expected declaration, got {self.peek()}")

    def parse_function(self):
        self.expect("fn")
        name = self.expect("IDENT").value
        self.expect("(")
        params = []
        if not self.at(")"):
            params.append(self.parse_param())
            while self.at(","):
                self.advance()
                params.append(self.parse_param())
        self.expect(")")
        self.expect("->")
        ret_type = self.parse_type_expr()
        authority = None
        if self.at("["):
            authority = self.parse_governed_context()
        body = self.parse_block()
        return Node("Function", name=name, params=params, ret_type=ret_type,
                    authority=authority, body=body)

    def parse_param(self):
        name = self.expect("IDENT").value
        self.expect(":")
        t = self.parse_type_expr()
        return (name, t)

    def parse_type_def(self):
        self.expect("type")
        name = self.expect("IDENT").value
        self.expect("=")
        t = self.parse_type_expr()
        return Node("TypeDef", name=name, type=t)

    def parse_type_expr(self):
        if self.at("IDENT"):
            name = self.advance().value
            if self.at("<"):
                self.advance()
                args = [self.parse_type_expr()]
                while self.at(","):
                    self.advance()
                    args.append(self.parse_type_expr())
                self.expect(">")
                return Node("GenericType", name=name, args=args)
            t = Node("BaseType", name=name)
        elif self.peek().kind in ("bool", "int", "float", "str", "void", "any"):
            t = Node("BaseType", name=self.advance().kind)
        elif self.peek().kind in ("pure", "lawful", "reactive", "sovereign"):
            # authority level used as the 2nd arg of Governed<T, AuthLevel>
            t = Node("AuthLevelType", name=self.advance().kind)
        elif self.at("("):
            self.advance()
            items = [self.parse_type_expr()]
            while self.at(","):
                self.advance()
                items.append(self.parse_type_expr())
            self.expect(")")
            t = Node("TupleType", items=items)
        else:
            raise ParseError(f"Expected type, got {self.peek()}")
        if self.at("->"):
            self.advance()
            ret = self.parse_type_expr()
            return Node("FunctionType", param=t, ret=ret)
        return t

    def parse_bind(self):
        self.expect("bind")
        name = self.expect("IDENT").value
        self.expect(":")
        t = self.parse_type_expr()
        self.expect("=")
        expr = self.parse_expression()
        self.expect(";")
        return Node("Bind", name=name, type=t, expr=expr)

    def parse_observe(self):
        # observe SIGNAL as binding { block }
        # 'as' is not a reserved keyword in the spec's own keyword list
        # (Section 2.2), so it lexes as a plain IDENT here; matched by value.
        self.expect("observe")
        signal = self.expect("IDENT").value
        as_tok = self.expect("IDENT")
        if as_tok.value != "as":
            raise ParseError(f"Expected 'as' in observe declaration, got {as_tok.value!r}")
        binding = self.expect("IDENT").value
        body = self.parse_block()
        return Node("Observe", signal=signal, binding=binding, body=body)

    def parse_emit_decl(self):
        self.expect("emit")
        name = self.expect("IDENT").value
        self.expect(":")
        t = self.parse_type_expr()
        self.expect(";")
        return Node("EmitDecl", name=name, type=t)

    def parse_block(self):
        self.expect("{")
        stmts = []
        while not self.at("}"):
            stmts.append(self.parse_statement())
        self.expect("}")
        return Node("Block", stmts=stmts)

    def parse_statement(self):
        if self.at("bind"):
            return self.parse_bind()
        if self.at("return"):
            self.advance()
            expr = self.parse_expression()
            self.expect(";")
            return Node("Return", expr=expr)
        if self.at("enforce"):
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            self.expect(";")
            return Node("Enforce", expr=expr)
        if self.at("anchor"):
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            self.expect(";")
            return Node("Anchor", expr=expr)
        if self.at("rollback"):
            # Decision #4 (ratified): rollback: is a first-class statement,
            # alongside anchor: and enforce: — not sugar for a stdlib call.
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            self.expect(";")
            return Node("Rollback", expr=expr)
        if self.at("emit"):
            self.advance()
            name = self.expect("IDENT").value
            self.expect(":")
            expr = self.parse_expression()
            self.expect(";")
            return Node("Emit", name=name, expr=expr)
        expr = self.parse_expression()
        self.expect(";")
        return Node("ExprStmt", expr=expr)

    # ---- expressions (precedence climbing) ----
    def parse_expression(self):
        return self.parse_pipe()

    def parse_pipe(self):
        left = self.parse_or()
        while self.at("|>"):
            self.advance()
            right = self.parse_or()
            left = Node("Pipe", left=left, right=right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.at("||"):
            self.advance()
            left = Node("BinOp", op="||", left=left, right=self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.at("&&"):
            self.advance()
            left = Node("BinOp", op="&&", left=left, right=self.parse_equality())
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.peek().kind in ("==", "!="):
            op = self.advance().kind
            left = Node("BinOp", op=op, left=left, right=self.parse_comparison())
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().kind in (">", "<", ">=", "<="):
            op = self.advance().kind
            left = Node("BinOp", op=op, left=left, right=self.parse_additive())
        return left

    # SPEC GAP #8: arithmetic precedence, not defined by the grammar at all
    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().kind in ("+", "-"):
            op = self.advance().kind
            left = Node("BinOp", op=op, left=left, right=self.parse_multiplicative())
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek().kind in ("*", "/", "%"):
            op = self.advance().kind
            left = Node("BinOp", op=op, left=left, right=self.parse_unary())
        return left

    def parse_unary(self):
        if self.at("!"):
            self.advance()
            return Node("UnOp", op="!", expr=self.parse_unary())
        if self.at("-"):
            self.advance()
            return Node("UnOp", op="-", expr=self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.at("."):
                self.advance()
                field_name = self.expect("IDENT").value
                expr = Node("Member", target=expr, field=field_name)
            elif self.at("("):
                self.advance()
                args = []
                if not self.at(")"):
                    args.append(self.parse_expression())
                    while self.at(","):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(")")
                expr = Node("Call", target=expr, args=args)
            elif self.at("::"):
                self.advance()
                name = self.expect("IDENT").value
                expr = Node("ScopeResolve", target=expr, name=name)
            else:
                break
        return expr

    def parse_primary(self):
        t = self.peek()
        if t.kind == "INT" or t.kind == "FLOAT" or t.kind == "STRING":
            self.advance()
            return Node("Literal", value=t.value)
        if t.kind == "true":
            self.advance()
            return Node("Literal", value=True)
        if t.kind == "false":
            self.advance()
            return Node("Literal", value=False)
        if t.kind == "void":
            self.advance()
            return Node("Literal", value=None)
        if t.kind == "let":
            self.advance()
            name = self.expect("IDENT").value
            self.expect(":")
            typ = self.parse_type_expr()
            self.expect("=")
            expr = self.parse_expression()
            return Node("Let", name=name, type=typ, expr=expr)
        if t.kind == "if":
            self.advance()
            cond = self.parse_expression()
            self.expect("then") if self.at("then") else None
            then_b = self.parse_block()
            else_b = None
            if self.at("else"):
                self.advance()
                else_b = self.parse_block()
            return Node("If", cond=cond, then=then_b, orelse=else_b)
        if t.kind == "match":
            self.advance()
            subject = self.parse_expression()
            self.expect("{")
            arms = []
            while not self.at("}"):
                pat = self.parse_pattern()
                self.expect("=>")
                res = self.parse_expression()
                self.expect(",") if self.at(",") else None
                arms.append((pat, res))
            self.expect("}")
            return Node("Match", subject=subject, arms=arms)
        if t.kind == "assert":
            self.advance()
            expr = self.parse_expression()
            return Node("Assert", expr=expr)
        if t.kind == "enforce":
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            return Node("EnforceExpr", expr=expr)
        if t.kind == "trust":
            self.advance()
            name = self.expect("IDENT").value
            return Node("TrustRef", name=name)
        if t.kind == "anchor":
            self.advance()
            self.expect(":")
            expr = self.parse_expression()
            return Node("AnchorExpr", expr=expr)
        if t.kind == "(":
            self.advance()
            items = [self.parse_expression()]
            while self.at(","):
                self.advance()
                items.append(self.parse_expression())
            self.expect(")")
            if len(items) == 1:
                return items[0]
            return Node("Tuple", items=items)
        if t.kind == "IDENT":
            name = self.advance().value
            # Decision #2 (ratified): TypeName { field: expr, ... } record
            # literal. Disambiguated structurally: blocks never occur in
            # primary-expression position (they're only ever produced by
            # parse_block() at fixed call sites — function/if/else/match/
            # observe bodies), so IDENT immediately followed by `{` here is
            # unambiguously a record literal, regardless of capitalization.
            if self.at("{"):
                self.advance()
                fields = {}
                while not self.at("}"):
                    fname = self.expect("IDENT").value
                    self.expect(":")
                    fval = self.parse_expression()
                    fields[fname] = fval
                    if self.at(","):
                        self.advance()
                self.expect("}")
                return Node("Record", type_name=name, fields=fields)
            return Node("Ident", name=name)
        raise ParseError(f"Unexpected token in expression: {t}")

    def parse_pattern(self):
        if self.at("IDENT") and self.peek().value == "_":
            self.advance()
            return Node("WildcardPat")
        if self.peek().kind in ("INT", "FLOAT", "STRING", "true", "false"):
            v = self.advance()
            val = v.value if v.kind not in ("true", "false") else (v.kind == "true")
            return Node("LiteralPat", value=val)
        name = self.expect("IDENT").value
        return Node("BindPat", name=name)


def parse(source: str):
    return Parser(lex(source)).parse_program()


# ============================================================
# 4. RUNTIME VALUES
# ============================================================

class GovernanceViolation(Exception):
    def __init__(self, message, entity=None):
        super().__init__(message)
        self.entity = entity


class TrustFailure(Exception):
    pass


class Lawful:
    __slots__ = ("value", "type_name")
    def __init__(self, value, type_name="Any"):
        self.value = value
        self.type_name = type_name
    def __repr__(self):
        return f"Lawful<{self.type_name}>({self.value!r})"


class Governed:
    __slots__ = ("value", "auth")
    def __init__(self, value, auth):
        self.value = value
        self.auth = auth
    def __repr__(self):
        return f"Governed<{self.auth}>({self.value!r})"


class Signal:
    __slots__ = ("name", "value")
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
    def __repr__(self):
        return f"Signal({self.name}={self.value!r})"


class Trust:
    __slots__ = ("entity", "scope")
    def __init__(self, entity, scope="ENTITY"):
        self.entity = entity
        self.scope = scope
    def __repr__(self):
        return f"Trust<{self.scope}>({self.entity!r})"


class Record:
    def __init__(self, type_name, fields):
        self.type_name = type_name
        self.fields = dict(fields)
    def __getattr__(self, item):
        if item in ("type_name", "fields"):
            return object.__getattribute__(self, item)
        try:
            return self.fields[item]
        except KeyError:
            raise AttributeError(item)
    def __repr__(self):
        return f"{self.type_name}{self.fields!r}"


AUTH_ORDER = {"pure": 0, "lawful": 1, "reactive": 2, "sovereign": 3}


# ============================================================
# 5. INVARIANT ENGINE
# ============================================================

class InvariantEngine:
    def __init__(self, interp):
        self.interp = interp
        self.articles = {}  # name -> Article node

    def load_constitution(self, constitution_node):
        if constitution_node is None:
            return
        for art in constitution_node.articles:
            self.articles[art.name] = art

    def check_all(self, env, trigger_response_fn):
        """Evaluate always/never/when-then across all articles against env.
        Called after every statement (runtime-continuous, per Section 5.2)."""
        for art in self.articles.values():
            for inv in art.invariants:
                if inv.kind == "Always":
                    ok = self._safe_eval(inv.expr, env)
                    if ok is False:
                        self._violate(f"ALWAYS violated in @article {art.name}: {inv.expr}", env)
                elif inv.kind == "Never":
                    triggered = self._safe_eval(inv.expr, env)
                    if triggered is True:
                        self._violate(f"NEVER violated in @article {art.name}: {inv.expr}", env)
                elif inv.kind == "WhenThen":
                    triggered = self._safe_eval(inv.trigger, env)
                    if triggered is True:
                        trigger_response_fn(inv.response, env)

    def _safe_eval(self, expr_node, env):
        try:
            return self.interp.eval_expr(expr_node, env)
        except Exception:
            # Unbound/unknown identifiers in a not-yet-relevant invariant
            # are treated as "not applicable yet", not a violation.
            return None

    def _violate(self, message, env):
        self.interp.audit_trail.append({
            "type": "GOVERNANCE_VIOLATION", "message": message, "t": time.time()
        })
        if self.interp.anchors.stack:
            self.interp.rollback_to_last_anchor()
        raise GovernanceViolation(message)


# ============================================================
# 6. SIGNAL BUS + ANCHOR STORE
# ============================================================

class SignalBus:
    def __init__(self):
        self.observers = {}  # name -> list of (binding, block, closure_env)

    def register(self, name, binding, block, env):
        self.observers.setdefault(name, []).append((binding, block, env))

    def emit(self, name, value, interp):
        for binding, block, env in self.observers.get(name, []):
            local = dict(env)
            local[binding] = value
            interp.exec_block(block, local)


class AnchorStore:
    def __init__(self):
        self.stack = []  # list of (label, snapshot_dict, hash)

    def create(self, label, snapshot):
        blob = json.dumps({k: repr(v) for k, v in snapshot.items()}, sort_keys=True)
        h = hashlib.sha3_256(blob.encode()).hexdigest()
        self.stack.append((label, dict(snapshot), h))
        return h

    def last(self):
        return self.stack[-1] if self.stack else None


# ============================================================
# 7. STDLIB
# ============================================================

def build_stdlib(interp):
    def _now(*a):
        return time.time_ns()

    def _hash(value):
        return hashlib.sha3_256(repr(value).encode()).hexdigest()

    def _verify(signature, entity):
        return isinstance(entity, Trust) and signature == _hash(entity.entity)

    def _quarantine(entity):
        interp.quarantined.add(id(entity))
        interp.audit_trail.append({"type": "QUARANTINE", "entity": repr(entity), "t": time.time()})
        return None

    def _rollback(anchor_ref=None):
        interp.rollback_to_last_anchor()
        return None

    def _audit(event):
        interp.audit_trail.append({"type": "AUDIT", "event": repr(event), "t": time.time()})
        return None

    def _merge(a, b):
        return Signal(f"merge({a.name},{b.name})", (a.value, b.value))

    def _filter(sig, predicate):
        if interp.call_callable(predicate, [sig.value]):
            return sig
        return Signal(sig.name, None)

    def _map(sig, fn):
        return Signal(sig.name, interp.call_callable(fn, [sig.value]))

    def _verify_entity(id_str):
        return Trust(id_str, "ENTITY")

    def _bind_trust(entity, scope):
        return Trust(entity.entity, scope)

    def _revoke_trust(entity):
        interp.quarantined.add(id(entity))
        return None

    return {
        "now": _now, "hash": _hash, "verify": _verify,
        "quarantine": _quarantine, "rollback": _rollback, "audit": _audit,
        "merge": _merge, "filter": _filter, "map": _map,
        "verify_entity": _verify_entity, "bind_trust": _bind_trust,
        "revoke_trust": _revoke_trust,
    }


# ============================================================
# 8. BYTECODE COMPILER  (.ulxb)
# ============================================================
# Opcodes operate on a stack VM. Each function compiles to a flat list of
# (op, arg) tuples. See SPEC GAP #5 for file-format rationale.

class Compiler:
    def __init__(self):
        self.constants = []

    def const(self, value):
        self.constants.append(value)
        return len(self.constants) - 1

    def compile_program(self, program_node):
        functions = {}
        constitution = None
        if program_node.constitution:
            constitution = self._serialize_constitution(program_node.constitution)
        for module in program_node.modules:
            for decl in module.decls:
                if decl.kind == "Function":
                    functions[f"{module.name}::{decl.name}"] = {
                        "params": [p[0] for p in decl.params],
                        "code": self.compile_block(decl.body),
                        "authority": decl.authority or module.authority,
                    }
        # Decision #5 (ratified): .ulxb is JSON, format-tagged "ULXB-JSON-v1".
        # Binary encoding is reserved for a later version, not this one.
        return {"format": "ULXB-JSON-v1", "constants": self.constants,
                "functions": functions, "constitution": constitution}

    def _serialize_constitution(self, node):
        # Stored as data (source-form expressions re-parsed at load time by
        # the interpreter's invariant engine) rather than compiled to
        # bytecode — invariants are evaluated by tree-walk, see Section 5.
        return {"_ast_marker": "constitution"}

    def compile_block(self, block):
        code = []
        for stmt in block.stmts:
            code.extend(self.compile_stmt(stmt))
        return code

    def compile_stmt(self, stmt):
        k = stmt.kind
        if k == "Bind":
            return self.compile_expr(stmt.expr) + [("STORE", stmt.name)]
        if k == "Return":
            return self.compile_expr(stmt.expr) + [("RETURN", None)]
        if k == "Enforce":
            return self.compile_expr(stmt.expr) + [("ENFORCE", None)]
        if k == "Anchor":
            return self.compile_expr(stmt.expr) + [("ANCHOR", None)]
        if k == "Rollback":
            return self.compile_expr(stmt.expr) + [("ROLLBACK", None)]
        if k == "Emit":
            return self.compile_expr(stmt.expr) + [("EMIT", stmt.name)]
        if k == "ExprStmt":
            return self.compile_expr(stmt.expr) + [("POP", None)]
        if k == "If":
            return [("EVAL_IF_STMT", stmt)]
        raise NotImplementedError(f"compile_stmt: {k}")

    def compile_expr(self, e):
        k = e.kind
        if k == "Literal":
            return [("PUSH_CONST", self.const(e.value))]
        if k == "Ident":
            return [("LOAD", e.name)]
        if k == "Member":
            return self.compile_expr(e.target) + [("GETATTR", e.field)]
        if k == "BinOp":
            return self.compile_expr(e.left) + self.compile_expr(e.right) + [("BINOP", e.op)]
        if k == "UnOp":
            return self.compile_expr(e.expr) + [("UNOP", e.op)]
        if k == "Pipe":
            # a |> f  ==  f(a)
            return self.compile_expr(e.left) + [("PIPE_CALL", e.right)]
        if k == "Call":
            code = []
            for a in e.args:
                code.extend(self.compile_expr(a))
            code += [("CALL", (e.target, len(e.args)))]
            return code
        if k == "Tuple":
            code = []
            for it in e.items:
                code.extend(self.compile_expr(it))
            return code + [("MAKE_TUPLE", len(e.items))]
        if k == "Record":
            return [("MAKE_RECORD", (e.type_name, e.fields))]
        if k == "If":
            return [("EVAL_IF", e)]
        if k == "Match":
            return [("EVAL_MATCH", e)]
        if k == "Let":
            return self.compile_expr(e.expr) + [("STORE", e.name), ("LOAD", e.name)]
        if k == "AnchorExpr":
            return self.compile_expr(e.expr) + [("ANCHOR", None)]
        if k == "EnforceExpr":
            return self.compile_expr(e.expr) + [("ENFORCE", None)]
        if k == "Assert":
            return self.compile_expr(e.expr) + [("ENFORCE", None)]
        if k == "TrustRef":
            return [("LOAD", e.name)]
        if k == "ScopeResolve":
            return [("SCOPE_CALL", (e.target, e.name))]
        raise NotImplementedError(f"compile_expr: {k}")


def save_ulxb(compiled, path):
    with open(path, "w") as f:
        json.dump(compiled, f, indent=2, default=str)


def load_ulxb(path):
    with open(path) as f:
        data = json.load(f)
    if data.get("format") != "ULXB-JSON-v1":
        raise ValueError(
            f".ulxb format tag missing or unrecognized: {data.get('format')!r} "
            f"(expected 'ULXB-JSON-v1')"
        )
    return data


# ============================================================
# 9. VM / INTERPRETER
# ============================================================

class Interpreter:
    def __init__(self):
        self.globals = {}
        self.functions = {}       # "module::name" -> Function AST node
        self.invariants = InvariantEngine(self)
        self.signals = SignalBus()
        self.anchors = AnchorStore()
        self.audit_trail = []
        self.quarantined = set()
        self.stdlib = build_stdlib(self)
        self.current_authority = "lawful"
        self.out = []  # captured stdout for embedding (REPL/IDE)

    # ---- top-level load/run of parsed AST (tree-walk; see class docstring) ----
    def load_program(self, program_node):
        self.invariants.load_constitution(program_node.constitution)
        for module in program_node.modules:
            for decl in module.decls:
                if decl.kind == "Function":
                    self.functions[f"{module.name}::{decl.name}"] = (decl, module.authority)
                    self.functions[decl.name] = (decl, module.authority)  # unqualified lookup
                elif decl.kind == "Observe":
                    self.signals.register(decl.signal, decl.binding, decl.body, self.globals)
                elif decl.kind == "Bind":
                    self.exec_stmt(decl, self.globals)

    def run_function(self, qualified_name, args=None):
        entry = self.functions.get(qualified_name)
        if entry is None:
            raise NameError(f"No such function: {qualified_name}")
        fn_node, mod_authority = entry
        auth = fn_node.authority or mod_authority
        prev_auth = self.current_authority
        if AUTH_ORDER.get(auth, 1) > AUTH_ORDER.get(prev_auth, 1):
            self.audit_trail.append({"type": "AUTHORITY_ESCALATION",
                                      "from": prev_auth, "to": auth, "t": time.time()})
        self.current_authority = auth
        local = dict(self.globals)
        for (pname, _t), val in zip(fn_node.params, args or []):
            local[pname] = val
        try:
            return self.exec_block(fn_node.body, local)
        finally:
            self.current_authority = prev_auth

    # ---- statement execution (tree-walk) ----
    def exec_block(self, block, env):
        for stmt in block.stmts:
            result = self.exec_stmt(stmt, env)
            self.invariants.check_all(env, lambda resp, e: self.eval_expr(resp, e))
            if isinstance(result, _ReturnSignal):
                return result.value
        return None  # only an explicit `return` produces a function result,
                      # per the spec's grammar (Section 3: return_stmt)

    def exec_stmt(self, stmt, env):
        k = stmt.kind
        if k == "Bind":
            val = self.eval_expr(stmt.expr, env)
            env[stmt.name] = self._tag_value(stmt.type, val)
            self.globals.setdefault(stmt.name, env[stmt.name])
            return None
        if k == "Return":
            return _ReturnSignal(self.eval_expr(stmt.expr, env))
        if k == "Enforce":
            ok = self.eval_expr(stmt.expr, env)
            if not ok:
                self.audit_trail.append({"type": "ENFORCE_FAIL", "t": time.time()})
                raise GovernanceViolation(f"enforce failed: {stmt.expr}")
            return None
        if k == "Anchor":
            val = self.eval_expr(stmt.expr, env)
            self.anchors.create("anchor", dict(env))
            return None
        if k == "Rollback":
            self.rollback_to_last_anchor()
            return None
        if k == "Emit":
            val = self.eval_expr(stmt.expr, env)
            self.signals.emit(stmt.name, val, self)
            return None
        if k == "ExprStmt":
            return self.eval_expr(stmt.expr, env)
        if k == "If":
            cond = self.eval_expr(stmt.cond, env)
            branch = stmt.then if cond else stmt.orelse
            if branch is not None:
                return self.exec_block(branch, env)
            return None
        raise NotImplementedError(f"exec_stmt: {k}")

    def rollback_to_last_anchor(self):
        last = self.anchors.last()
        if last:
            _, snapshot, _ = last
            self.globals.update(snapshot)
        self.audit_trail.append({"type": "ROLLBACK", "t": time.time()})

    def _tag_value(self, type_node, val):
        if type_node is None:
            return val
        if type_node.kind == "GenericType":
            if type_node.name == "Lawful":
                return Lawful(val, type_node.args[0].name if type_node.args else "Any")
            if type_node.name == "Governed":
                auth = type_node.args[1].name if len(type_node.args) > 1 else "lawful"
                return Governed(val, auth)
            if type_node.name == "Signal":
                return val if isinstance(val, Signal) else Signal("anon", val)
            if type_node.name == "Trust":
                return val if isinstance(val, Trust) else Trust(val)
        return val

    # ---- expression evaluation (tree-walk) ----
    def eval_expr(self, e, env):
        k = e.kind
        if k == "Literal":
            return e.value
        if k == "Ident":
            if e.name in env:
                v = env[e.name]
            elif e.name in self.globals:
                v = self.globals[e.name]
            elif e.name in self.stdlib:
                v = self.stdlib[e.name]
            else:
                raise NameError(f"Unbound identifier: {e.name}")
            return self._unwrap(v)
        if k == "Member":
            target = self.eval_expr(e.target, env)
            return self._get_field(target, e.field)
        if k == "BinOp":
            l = self.eval_expr(e.left, env)
            r = self.eval_expr(e.right, env)
            return self._binop(e.op, l, r)
        if k == "UnOp":
            v = self.eval_expr(e.expr, env)
            if e.op == "!":
                return not v
            if e.op == "-":
                return -v
        if k == "Tuple":
            return tuple(self.eval_expr(it, env) for it in e.items)
        if k == "Record":
            fields = {name: self.eval_expr(v, env) for name, v in e.fields.items()}
            return Record(e.type_name, fields)
        if k == "Call":
            return self._eval_call(e.target, e.args, env)
        if k == "Pipe":
            left_val = self.eval_expr(e.left, env)
            return self._invoke_target(e.right, [left_val], env)
        if k == "If":
            cond = self.eval_expr(e.cond, env)
            branch = e.then if cond else e.orelse
            if branch is None:
                return None
            return self.exec_block(branch, dict(env))
        if k == "Match":
            subj = self.eval_expr(e.subject, env)
            for pat, res in e.arms:
                bound = dict(env)
                if self._match_pattern(pat, subj, bound):
                    return self.eval_expr(res, bound)
            return None
        if k == "Let":
            val = self._tag_value(e.type, self.eval_expr(e.expr, env))
            env[e.name] = val
            return val
        if k == "AnchorExpr":
            val = self.eval_expr(e.expr, env)
            self.anchors.create("anchor", dict(env))
            return val
        if k == "EnforceExpr" or k == "Assert":
            val = self.eval_expr(e.expr, env)
            if not val:
                raise GovernanceViolation(f"enforce failed: {e.expr}")
            return val
        if k == "TrustRef":
            return env.get(e.name) or self.globals.get(e.name)
        if k == "ScopeResolve":
            qualified = f"{e.target.name}::{e.name}" if e.target.kind == "Ident" else e.name
            return ("__fnref__", qualified)
        raise NotImplementedError(f"eval_expr: {k}")

    def _unwrap(self, v):
        # Lawful<T>/Governed<T,Auth> are transparent wrappers for value
        # comparison/arithmetic — the invariant/authority bookkeeping they
        # carry doesn't change what the underlying value equals or computes
        # to. Signal/Trust are NOT unwrapped here; those require explicit
        # `.value`/`.entity` field access per Section 4.1, since silently
        # unwrapping a Trust would defeat the point of the type.
        while isinstance(v, (Lawful, Governed)):
            v = v.value
        return v

    def _get_field(self, target, field_name):
        target = self._unwrap(target)
        if isinstance(target, (Lawful, Governed, Signal, Trust)):
            if field_name == "value" and hasattr(target, "value"):
                return target.value
            if field_name == "entity" and isinstance(target, Trust):
                return target.entity
        if isinstance(target, Record):
            return target.fields.get(field_name)
        if isinstance(target, dict):
            return target.get(field_name)
        # Unknown/absent nested attribute paths (e.g. `context.threat_level`
        # with no `context` bound) resolve to None so invariants that
        # reference not-yet-relevant state don't crash the engine.
        return None

    def _binop(self, op, l, r):
        l = self._unwrap(l)
        r = self._unwrap(r)
        if op == "==":
            return l == r
        if op == "!=":
            return l != r
        if op == ">":
            return l is not None and r is not None and l > r
        if op == "<":
            return l is not None and r is not None and l < r
        if op == ">=":
            return l is not None and r is not None and l >= r
        if op == "<=":
            return l is not None and r is not None and l <= r
        if op == "&&":
            return bool(l) and bool(r)
        if op == "||":
            return bool(l) or bool(r)
        if op == "+":
            return l + r
        if op == "-":
            return l - r
        if op == "*":
            return l * r
        if op == "/":
            return l / r
        if op == "%":
            return l % r
        raise NotImplementedError(f"binop {op}")

    def _match_pattern(self, pat, subj, bound):
        if pat.kind == "WildcardPat":
            return True
        if pat.kind == "LiteralPat":
            return pat.value == subj
        if pat.kind == "BindPat":
            bound[pat.name] = subj
            return True
        return False

    def _eval_call(self, target_node, arg_nodes, env):
        args = [self.eval_expr(a, env) for a in arg_nodes]
        return self._invoke_target(target_node, args, env)

    def _invoke_target(self, target_node, args, env):
        name = target_node.name if target_node.kind == "Ident" else None
        if name and name in self.stdlib:
            return self.stdlib[name](*args)
        if name and (name in self.functions):
            return self.run_function(name, args)
        if target_node.kind == "ScopeResolve":
            qualified = f"{target_node.target.name}::{target_node.name}"
            return self.run_function(qualified, args)
        if name is None and target_node.kind == "Member":
            # a.b(...) with no matching user function: no-op, returns None
            return None
        raise NameError(f"Unknown callable: {getattr(target_node, 'name', target_node)}")

    def call_callable(self, ref, args):
        if isinstance(ref, tuple) and ref and ref[0] == "__fnref__":
            return self.run_function(ref[1], args)
        if isinstance(ref, Node) and ref.kind == "Ident":
            return self._invoke_target(ref, args, self.globals)
        return None


class _ReturnSignal:
    def __init__(self, value):
        self.value = value


# ============================================================
# 10. HIGH-LEVEL RUN HELPERS
# ============================================================

def run_source(source: str, entry: Optional[str] = None):
    program = parse(source)
    interp = Interpreter()
    interp.load_program(program)
    if entry is None:
        # default: run first function named "main" in first module
        for module in program.modules:
            for decl in module.decls:
                if decl.kind == "Function" and decl.name == "main":
                    entry = f"{module.name}::main"
                    break
            if entry:
                break
    result = interp.run_function(entry) if entry else None
    return interp, result


def compile_source_to_ulxb(source: str, out_path: str):
    program = parse(source)
    compiler = Compiler()
    compiled = compiler.compile_program(program)
    save_ulxb(compiled, out_path)
    return compiled


# ============================================================
# 11. REPL
# ============================================================

def repl():
    print("ULX Universa REPL v0.1 — reference interpreter (no static type-checking; "
          "see Decision #6). Type :q to quit, :help for help")
    interp = Interpreter()
    env = interp.globals
    buf = ""
    while True:
        try:
            line = input("ulx> " if not buf else "...> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not buf and line.strip() in (":q", ":quit", "exit"):
            break
        if not buf and line.strip() == ":help":
            print("Enter a statement (ending in ';') or a full module. :q to quit.")
            continue
        buf += line + "\n"
        if buf.count("{") != buf.count("}"):
            continue  # keep buffering multi-line blocks
        try:
            if buf.strip().startswith("module") or buf.strip().startswith("@constitution"):
                program = parse(buf)
                interp.load_program(program)
                print("(loaded)")
            else:
                toks = lex(buf)
                p = Parser(toks)
                stmt = p.parse_statement()
                result = interp.exec_stmt(stmt, env)
                interp.invariants.check_all(env, lambda r, e: interp.eval_expr(r, e))
                if result is not None:
                    print(result)
        except GovernanceViolation as gv:
            print(f"[GOVERNANCE VIOLATION] {gv}")
        except Exception as ex:
            print(f"[ERROR] {type(ex).__name__}: {ex}")
        buf = ""


# ============================================================
# 12. CLI
# ============================================================

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ulx",
        description="ULX Universa reference interpreter (v0.2 ratifications applied; "
                     "no static type-checking — not a conformant compiler, see Decision #6)")
    sub = ap.add_subparsers(dest="cmd")

    run_p = sub.add_parser("run", help="Parse and execute a .ulx source file")
    run_p.add_argument("file")
    run_p.add_argument("--entry", default=None, help="module::function to run")

    compile_p = sub.add_parser("compile", help="Compile a .ulx file to .ulxb bytecode (JSON)")
    compile_p.add_argument("file")
    compile_p.add_argument("-o", "--output", default=None)

    exec_p = sub.add_parser("exec", help="Load a .ulxb bytecode file and print its structure")
    exec_p.add_argument("file")

    sub.add_parser("repl", help="Start the interactive REPL")

    args = ap.parse_args(argv)

    if args.cmd == "run":
        with open(args.file) as f:
            source = f.read()
        interp, result = run_source(source, args.entry)
        print("=== result ===")
        print(result)
        print("=== audit trail ===")
        for a in interp.audit_trail:
            print(a)
    elif args.cmd == "compile":
        with open(args.file) as f:
            source = f.read()
        out = args.output or os.path.splitext(args.file)[0] + ".ulxb"
        compiled = compile_source_to_ulxb(source, out)
        print(f"Compiled -> {out}")
        print(f"  functions: {list(compiled['functions'].keys())}")
    elif args.cmd == "exec":
        data = load_ulxb(args.file)
        print(json.dumps(data, indent=2))
    elif args.cmd == "repl" or args.cmd is None:
        repl()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
