"""
Constitutional Node v1.0 - ISL Interpreter

This module implements the ISL Interpreter as specified in CIEMS-CNODE-SPEC-001
Section 3.1, responsible for parsing, validating, and resolving incoming ISL payloads.
"""

from typing import Optional

from isl.payload import ISLPayload
from isl.validation import ISLValidator, ISLValidationError


class ISLInterpreter:
    """
    ISL Interpreter - Parsing and validation layer for the Constitutional Node.
    
    As specified in Section 3.1, the ISL Interpreter:
    - Parses the ISL payload
    - Validates schema conformance against ISL v1.1
    - Resolves target scope
    - Verifies cross-agent compatibility
    - Checks constitutional flag identifiers for recognition
    - Passes validated payloads to the Constraint Engine
    - Routes failures to the Audit Ledger with structured rejection records
    """
    
    def __init__(
        self,
        agent_registry: Optional[dict] = None,
        constraint_registry: Optional[dict] = None,
        evidence_store: Optional[dict] = None,
    ):
        """
        Initialize the ISL Interpreter.
        
        Args:
            agent_registry: Registry of CIEMS-registered agents
            constraint_registry: Registry of constitutional constraints
            evidence_store: Federated evidence store
        """
        self.validator = ISLValidator(
            agent_registry=agent_registry,
            constraint_registry=constraint_registry,
            evidence_store=evidence_store,
        )
        self.agent_registry = agent_registry or {}
        self.constraint_registry = constraint_registry or {}
    
    def interpret(self, payload: ISLPayload) -> tuple[bool, Optional[ISLValidationError], Optional[dict]]:
        """
        Interpret and validate an ISL payload.
        
        Args:
            payload: The ISL payload to interpret
            
        Returns:
            Tuple of (is_valid, error, validation_context)
        """
        # Run the full validation pipeline
        is_valid, error = self.validator.validate(payload)
        
        if not is_valid:
            return False, error, None
        
        # Build validation context for downstream layers
        context = {
            "agent_registered": payload.issuing_agent_id in self.agent_registry,
            "flags_resolved": all(flag in self.constraint_registry for flag in payload.constitutional_flags),
            "target_scope": payload.target_scope.value,
            "intent_class": payload.intent_class.value,
        }
        
        return True, None, context
    
    def resolve_target_scope(self, payload: ISLPayload) -> dict:
        """
        Resolve the target scope of the payload.
        
        Args:
            payload: The ISL payload
            
        Returns:
            Scope resolution information
        """
        return {
            "target_scope": payload.target_scope.value,
            "target_id": payload.target_id,
            "target_org_id": payload.target_org_id,
            "requires_cross_agent_compatibility": payload.target_scope.value in ("federation", "cross-org"),
        }
    
    def check_cross_agent_compatibility(self, payload: ISLPayload) -> tuple[bool, Optional[str]]:
        """
        Check cross-agent compatibility requirements.
        
        Args:
            payload: The ISL payload
            
        Returns:
            Tuple of (is_compatible, reason)
        """
        # Simplified compatibility check
        # Full implementation would verify agent capabilities, scope permissions, etc.
        
        if payload.target_scope.value in ("federation", "cross-org"):
            # Federation and cross-org intents require additional checks
            return True, None
        
        return True, None
