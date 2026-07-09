"""
ISL v1.1 - Intent Specification Language Implementation

This module implements the Intent Specification Language v1.1 specification
(CIEMS-ISL-0011) for expressing, transmitting, validating, and auditing intent
within CIEMS-governed systems.
"""

from .payload import (
    ISLPayload,
    IntentClass,
    TargetScope,
    Priority,
    DirectiveBody,
    QueryBody,
    EscalationBody,
    VetoBody,
    EndorsementBody,
    CompositionRequestBody,
    FederationBroadcastBody,
    CoAuthorSignature,
)
from .validation import ISLValidationError, ISLValidator
from .signature import SignatureScheme, verify_signature, create_signature

__version__ = "1.1.0"
__all__ = [
    "ISLPayload",
    "IntentClass",
    "TargetScope",
    "Priority",
    "DirectiveBody",
    "QueryBody",
    "EscalationBody",
    "VetoBody",
    "EndorsementBody",
    "CompositionRequestBody",
    "FederationBroadcastBody",
    "CoAuthorSignature",
    "ISLValidationError",
    "ISLValidator",
    "SignatureScheme",
    "verify_signature",
    "create_signature",
]
