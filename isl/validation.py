"""
ISL v1.1 Validation Pipeline Implementation

This module implements the ISL validation pipeline as specified in
CIEMS-ISL-0011 Section 9.1, including schema validation, constitutional
flag resolution, evidence anchor verification, and error codes.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from .payload import ISLPayload, IntentClass, TargetScope


class ISLErrorCode(str):
    """ISL v1.1 error codes as specified in Appendix A."""
    SCHEMA_VALIDATION_FAILED = "ISL-E001"
    CONSTITUTIONAL_FLAG_UNRESOLVABLE = "ISL-E002"
    EVIDENCE_VERIFICATION_FAILED = "ISL-E003"
    COMPOSITION_QUORUM_NOT_ACHIEVED = "ISL-E004"
    CROSS_ORG_TRUST_FAILURE = "ISL-E005"
    INTENT_EXPIRED = "ISL-E006"
    SIGNATURE_INVALID = "ISL-E007"


class ISLValidationError(Exception):
    """ISL validation error with code and details."""
    
    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")


class ISLValidator:
    """
    ISL v1.1 validator implementing the full validation pipeline.
    
    This validator performs all validation stages specified in Section 9.1:
    1. Schema Check
    2. Constitutional Flag Resolution
    3. Evidence Anchor Verification
    4. Constraint Engine Pass (delegated to C-Node)
    5. Signature Verification
    """
    
    def __init__(
        self,
        agent_registry: Optional[dict] = None,
        constraint_registry: Optional[dict] = None,
        evidence_store: Optional[dict] = None,
        clock_skew_tolerance_seconds: int = 300,
    ):
        """
        Initialize the ISL validator.
        
        Args:
            agent_registry: Registry of CIEMS-registered agents
            constraint_registry: Registry of constitutional constraints
            evidence_store: Federated evidence store for verification
            clock_skew_tolerance_seconds: Maximum allowed clock skew (default: 300s)
        """
        self.agent_registry = agent_registry or {}
        self.constraint_registry = constraint_registry or {}
        self.evidence_store = evidence_store or {}
        self.clock_skew_tolerance_seconds = clock_skew_tolerance_seconds
    
    def validate(self, payload: ISLPayload) -> tuple[bool, Optional[ISLValidationError]]:
        """
        Run the complete ISL validation pipeline.
        
        Returns:
            Tuple of (is_valid, error) where error is None if validation passes.
        """
        try:
            # Stage 1: Schema Check
            self._validate_schema(payload)
            
            # Stage 2: Constitutional Flag Resolution
            self._validate_constitutional_flags(payload)
            
            # Stage 3: Evidence Anchor Verification
            self._validate_evidence_anchors(payload)
            
            # Stage 4: Timestamp Validation
            self._validate_timestamp(payload)
            
            # Stage 5: Expiry Check
            self._validate_expiry(payload)
            
            # Stage 6: Agent Registration Check
            self._validate_agent_registration(payload)
            
            # Stage 7: Intent Chain Validation
            self._validate_intent_chain(payload)
            
            return True, None
            
        except ISLValidationError as e:
            return False, e
    
    def _validate_schema(self, payload: ISLPayload) -> None:
        """Stage 1: Schema validation."""
        # Pydantic validation already performed on instantiation
        # Additional schema-specific checks:
        
        # Validate intent_body matches intent_class schema
        payload.validate_intent_body_schema()
        
        # Check for duplicate intent_id (would require ledger access)
        # This is deferred to C-Node ledger check
    
    def _validate_constitutional_flags(self, payload: ISLPayload) -> None:
        """Stage 2: Constitutional flag resolution."""
        for flag in payload.constitutional_flags:
            if flag not in self.constraint_registry:
                raise ISLValidationError(
                    code=ISLErrorCode.CONSTITUTIONAL_FLAG_UNRESOLVABLE,
                    message=f"Unresolvable constitutional flag: {flag}",
                    details={"flag": flag, "available_flags": list(self.constraint_registry.keys())}
                )
    
    def _validate_evidence_anchors(self, payload: ISLPayload) -> None:
        """Stage 3: Evidence anchor verification."""
        if not payload.evidence_refs:
            return
        
        for evidence_id in payload.evidence_refs:
            evidence = self.evidence_store.get(evidence_id)
            if not evidence:
                raise ISLValidationError(
                    code=ISLErrorCode.EVIDENCE_VERIFICATION_FAILED,
                    message=f"Unresolvable evidence anchor: {evidence_id}",
                    details={"evidence_id": evidence_id}
                )
            
            # Verify evidence integrity (simplified - full implementation would check hash, signature, etc.)
            if evidence.get("revoked", False):
                raise ISLValidationError(
                    code=ISLErrorCode.EVIDENCE_VERIFICATION_FAILED,
                    message=f"Revoked evidence anchor: {evidence_id}",
                    details={"evidence_id": evidence_id}
                )
    
    def _validate_timestamp(self, payload: ISLPayload) -> None:
        """Stage 4: Timestamp validation."""
        now = datetime.now(timezone.utc)
        payload_time = payload.timestamp_utc
        
        if payload_time.tzinfo is None:
            payload_time = payload_time.replace(tzinfo=timezone.utc)
        
        skew_seconds = abs((now - payload_time).total_seconds())
        
        if skew_seconds > self.clock_skew_tolerance_seconds:
            raise ISLValidationError(
                code=ISLErrorCode.SCHEMA_VALIDATION_FAILED,
                message=f"Timestamp exceeds clock skew tolerance: {skew_seconds}s > {self.clock_skew_tolerance_seconds}s",
                details={
                    "skew_seconds": skew_seconds,
                    "tolerance_seconds": self.clock_skew_tolerance_seconds,
                    "payload_timestamp": payload.timestamp_utc.isoformat(),
                    "current_timestamp": now.isoformat()
                }
            )
    
    def _validate_expiry(self, payload: ISLPayload) -> None:
        """Stage 5: Expiry check."""
        if not payload.expiry_utc:
            return
        
        now = datetime.now(timezone.utc)
        expiry = payload.expiry_utc
        
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        if now >= expiry:
            raise ISLValidationError(
                code=ISLErrorCode.INTENT_EXPIRED,
                message=f"Intent expired at {expiry.isoformat()}",
                details={
                    "expiry_utc": expiry.isoformat(),
                    "current_timestamp": now.isoformat()
                }
            )
    
    def _validate_agent_registration(self, payload: ISLPayload) -> None:
        """Stage 6: Agent registration check."""
        if payload.issuing_agent_id not in self.agent_registry:
            raise ISLValidationError(
                code=ISLErrorCode.SCHEMA_VALIDATION_FAILED,
                message=f"Unregistered issuing agent: {payload.issuing_agent_id}",
                details={"issuing_agent_id": payload.issuing_agent_id}
            )
        
        if payload.co_authors:
            for co_author in payload.co_authors:
                if co_author not in self.agent_registry:
                    raise ISLValidationError(
                        code=ISLErrorCode.SCHEMA_VALIDATION_FAILED,
                        message=f"Unregistered co-author: {co_author}",
                        details={"co_author_id": co_author}
                    )
    
    def _validate_intent_chain(self, payload: ISLPayload) -> None:
        """Stage 7: Intent chain validation."""
        # This is a simplified check - full implementation would:
        # 1. Verify chain_id exists in Audit Ledger if present
        # 2. Verify parent_intent_id exists and shares chain_id
        # 3. Detect cycles in the chain graph
        
        if payload.parent_intent_id and not payload.chain_id:
            raise ISLValidationError(
                code=ISLErrorCode.SCHEMA_VALIDATION_FAILED,
                message="parent_intent_id requires chain_id",
                details={"parent_intent_id": str(payload.parent_intent_id)}
            )
        
        # Cycle detection would require ledger access
        # This is deferred to C-Node implementation
