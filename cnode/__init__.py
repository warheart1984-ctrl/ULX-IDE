"""
Constitutional Node v1.0 Implementation

This module implements the Constitutional Node (C-Node) as specified in
CIEMS-CNODE-SPEC-001, the foundational governance unit of the CIEMS architecture.
"""

from .constitutional_node import ConstitutionalNode
from .layers.intent_layer import IntentLayer
from .layers.isl_interpreter import ISLInterpreter
from .layers.constraint_engine import ConstraintEngine, ConstraintTier
from .layers.evidence_layer import EvidenceLayer
from .layers.audit_ledger import AuditLedger, LedgerEntry

__version__ = "1.0.0"
__all__ = [
    "ConstitutionalNode",
    "IntentLayer",
    "ISLInterpreter",
    "ConstraintEngine",
    "ConstraintTier",
    "EvidenceLayer",
    "AuditLedger",
    "LedgerEntry",
]
