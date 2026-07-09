"""
ISL v1.1 Payload Schema Implementation

This module defines the complete ISL v1.1 payload schema as specified in
CIEMS-ISL-0011, including all intent body types and validation rules.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class IntentClass(str, Enum):
    """Intent class enumeration as per ISL v1.1 specification."""
    DIRECTIVE = "directive"
    QUERY = "query"
    ESCALATION = "escalation"
    VETO = "veto"
    ENDORSEMENT = "endorsement"
    COMPOSITION_REQUEST = "composition-request"
    FEDERATION_BROADCAST = "federation-broadcast"


class TargetScope(str, Enum):
    """Target scope enumeration as per ISL v1.1 specification."""
    AGENT = "agent"
    SUBSYSTEM = "subsystem"
    NODE = "node"
    FEDERATION = "federation"
    CROSS_ORG = "cross-org"


class Priority(str, Enum):
    """Processing priority enumeration."""
    ROUTINE = "routine"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RollbackPolicy(str, Enum):
    """Rollback policy for directive intents."""
    IMMEDIATE_ROLLBACK = "immediate-rollback"
    CHECKPOINT_ROLLBACK = "checkpoint-rollback"
    NO_ROLLBACK = "no-rollback"
    ESCALATE_ON_FAILURE = "escalate-on-failure"


class CompositionLogic(str, Enum):
    """Composition logic for multi-agent intent composition."""
    AND = "AND"
    OR = "OR"
    SEQUENCE = "SEQUENCE"


class EvidenceType(str, Enum):
    """Evidence type enumeration."""
    OUTCOME = "outcome"
    OBSERVATION = "observation"
    AUDIT_RECORD = "audit-record"
    EXTERNAL_ATTESTATION = "external-attestation"


# Intent Body Types

class DirectiveBody(BaseModel):
    """Directive intent body (intent_class: directive)."""
    action: str = Field(..., description="The action to be performed")
    target_resource: str = Field(..., description="Identifier of the resource")
    parameters: Optional[dict[str, Any]] = Field(default=None, description="Action-specific parameters")
    rollback_policy: RollbackPolicy = Field(..., description="Rollback behavior on failure")


class QueryBody(BaseModel):
    """Query intent body (intent_class: query)."""
    query_expression: str = Field(..., description="Structured query expression")
    response_schema: Optional[dict[str, Any]] = Field(default=None, description="Expected response structure")
    timeout_ms: Optional[int] = Field(default=None, description="Maximum wait time in milliseconds")


class EscalationBody(BaseModel):
    """Escalation intent body (intent_class: escalation)."""
    escalation_reason: str = Field(..., description="Human-readable description")
    escalation_target: str = Field(..., description="Identifier of escalation recipient")
    supporting_evidence: Optional[list[str]] = Field(default=None, description="Array of evidence_id or intent_id values")


class VetoBody(BaseModel):
    """Veto intent body (intent_class: veto)."""
    vetoed_intent_id: UUID = Field(..., description="The intent_id being vetoed")
    veto_reason: str = Field(..., description="Human-readable explanation")
    constitutional_basis: list[str] = Field(..., description="Constitutional constraint identifiers")


class EndorsementBody(BaseModel):
    """Endorsement intent body (intent_class: endorsement)."""
    endorsed_intent_id: UUID = Field(..., description="The intent_id being endorsed")
    endorsing_rationale: str = Field(..., description="Endorsing agent's rationale")


class ComponentIntent(BaseModel):
    """Component intent for composition requests."""
    intent_body: dict[str, Any] = Field(..., description="Individual intent payload")


class CompositionRequestBody(BaseModel):
    """Composition-request intent body (intent_class: composition-request)."""
    component_intents: list[ComponentIntent] = Field(..., description="Individual intent payloads to compose", min_length=2)
    composition_logic: CompositionLogic = Field(..., description="Logical relationship governing composition")
    resolution_authority: str = Field(..., description="Identifier of C-Node or human principal for conflict resolution")


class FederationBroadcastBody(BaseModel):
    """Federation-broadcast intent body (intent_class: federation-broadcast)."""
    broadcast_payload: dict[str, Any] = Field(..., description="Content to broadcast")
    target_org_ids: list[str] = Field(..., description="Array of target organization identifiers", min_length=1)
    acknowledgment_required: bool = Field(..., description="Whether to await acknowledgment from each target")


class CoAuthorSignature(BaseModel):
    """Co-author signature object for multi-agent composition."""
    agent_id: str = Field(..., description="CIEMS-registered agent identifier")
    signature: str = Field(..., description="Cryptographic signature over canonical payload")


# Main ISL Payload

class ISLPayload(BaseModel):
    """
    Complete ISL v1.1 payload structure.
    
    This is the canonical representation of an ISL intent payload as specified
    in CIEMS-ISL-0011. All fields are validated according to the specification.
    """
    intent_id: UUID = Field(default_factory=uuid4, description="Globally unique identifier")
    schema_version: str = Field(default="ISL-1.1", description="ISL schema version")
    intent_class: IntentClass = Field(..., description="Intent type classification")
    issuing_agent_id: str = Field(..., description="CIEMS-registered agent identifier")
    co_authors: Optional[list[str]] = Field(default=None, description="Array of co-author agent IDs")
    target_scope: TargetScope = Field(..., description="Scope of the intent's target")
    target_id: Optional[str] = Field(default=None, description="Specific target entity identifier")
    target_org_id: Optional[str] = Field(default=None, description="Target organization identifier for cross-org")
    human_intent_ref: Optional[str] = Field(default=None, description="Reference to originating UCR_SPEC entry")
    intent_body: dict[str, Any] = Field(..., description="Structured payload of the intent")
    constitutional_flags: list[str] = Field(..., description="Constitutional constraint identifiers", min_length=1)
    evidence_refs: Optional[list[str]] = Field(default=None, description="References to federated evidence anchors")
    priority: Optional[Priority] = Field(default=None, description="Processing priority")
    expiry_utc: Optional[datetime] = Field(default=None, description="UTC timestamp after which intent is void")
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of payload creation")
    issuer_signature: Optional[str] = Field(default=None, description="Cryptographic signature of issuing agent")
    co_author_signatures: Optional[list[CoAuthorSignature]] = Field(default=None, description="Co-author signatures")
    chain_id: Optional[UUID] = Field(default=None, description="Link to existing intent chain")
    parent_intent_id: Optional[UUID] = Field(default=None, description="Intent_id of direct predecessor in chain")

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        """Validate that schema_version is exactly 'ISL-1.1'."""
        if v != "ISL-1.1":
            raise ValueError(f"Unsupported schema version: {v}. Only ISL-1.1 is supported.")
        return v

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, v: Optional[str], info) -> Optional[str]:
        """Validate target_id conditional on target_scope."""
        target_scope = info.data.get("target_scope")
        if target_scope in (TargetScope.FEDERATION, TargetScope.CROSS_ORG) and v is not None:
            raise ValueError(f"target_id must be omitted when target_scope is {target_scope}")
        if target_scope in (TargetScope.AGENT, TargetScope.SUBSYSTEM, TargetScope.NODE) and v is None:
            raise ValueError(f"target_id is required when target_scope is {target_scope}")
        return v

    @field_validator("target_org_id")
    @classmethod
    def validate_target_org_id(cls, v: Optional[str], info) -> Optional[str]:
        """Validate target_org_id conditional on target_scope."""
        target_scope = info.data.get("target_scope")
        if target_scope == TargetScope.CROSS_ORG and v is None:
            raise ValueError("target_org_id is required when target_scope is cross-org")
        if target_scope != TargetScope.CROSS_ORG and v is not None:
            raise ValueError(f"target_org_id must be omitted when target_scope is {target_scope}")
        return v

    @field_validator("co_authors")
    @classmethod
    def validate_co_authors(cls, v: Optional[list[str]], info) -> Optional[list[str]]:
        """Validate co_authors array."""
        issuing_agent_id = info.data.get("issuing_agent_id")
        intent_class = info.data.get("intent_class")
        
        if intent_class == IntentClass.COMPOSITION_REQUEST and (not v or len(v) < 1):
            raise ValueError("co_authors must contain at least one entry for composition-request")
        
        if v and issuing_agent_id in v:
            raise ValueError("co_authors must not contain issuing_agent_id")
        
        return v

    @field_validator("co_author_signatures")
    @classmethod
    def validate_co_author_signatures(cls, v: Optional[list[CoAuthorSignature]], info) -> Optional[list[CoAuthorSignature]]:
        """Validate co_author_signatures conditional on co_authors."""
        co_authors = info.data.get("co_authors")
        if co_authors and not v:
            raise ValueError("co_author_signatures is required when co_authors is populated")
        return v

    @field_validator("parent_intent_id")
    @classmethod
    def validate_parent_intent_id(cls, v: Optional[UUID], info) -> Optional[UUID]:
        """Validate parent_intent_id conditional on chain_id."""
        chain_id = info.data.get("chain_id")
        if chain_id and not v:
            # Allow if this is the first in the chain
            pass
        if v and not chain_id:
            raise ValueError("chain_id should be present when parent_intent_id is present")
        return v

    def get_canonical_serialization(self) -> str:
        """
        Return canonical serialization for signature calculation.
        
        This excludes signature fields (issuer_signature, co_author_signatures)
        as per ISL v1.1 specification Section 10.1.
        """
        data = self.model_dump(exclude={"issuer_signature", "co_author_signatures"})
        # Convert UUIDs to strings for consistent serialization
        if "intent_id" in data and data["intent_id"]:
            data["intent_id"] = str(data["intent_id"])
        if "chain_id" in data and data["chain_id"]:
            data["chain_id"] = str(data["chain_id"])
        if "parent_intent_id" in data and data["parent_intent_id"]:
            data["parent_intent_id"] = str(data["parent_intent_id"])
        if "expiry_utc" in data and data["expiry_utc"]:
            data["expiry_utc"] = data["expiry_utc"].isoformat()
        if "timestamp_utc" in data and data["timestamp_utc"]:
            data["timestamp_utc"] = data["timestamp_utc"].isoformat()
        
        import json
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def validate_intent_body_schema(self) -> None:
        """Validate intent_body matches the schema for the intent_class."""
        body = self.intent_body
        
        try:
            if self.intent_class == IntentClass.DIRECTIVE:
                DirectiveBody(**body)
            elif self.intent_class == IntentClass.QUERY:
                QueryBody(**body)
            elif self.intent_class == IntentClass.ESCALATION:
                EscalationBody(**body)
            elif self.intent_class == IntentClass.VETO:
                VetoBody(**body)
            elif self.intent_class == IntentClass.ENDORSEMENT:
                EndorsementBody(**body)
            elif self.intent_class == IntentClass.COMPOSITION_REQUEST:
                CompositionRequestBody(**body)
            elif self.intent_class == IntentClass.FEDERATION_BROADCAST:
                FederationBroadcastBody(**body)
        except Exception as e:
            raise ValueError(f"intent_body validation failed for {self.intent_class}: {e}")
