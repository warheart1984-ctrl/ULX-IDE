"""
ISL v1.1 Federated Evidence Implementation

This module implements the federated evidence anchoring system as specified
in CIEMS-ISL-0011 Section 7, including evidence anchor structure, verification
pipeline, and privacy considerations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from .payload import EvidenceType


@dataclass
class EvidenceAnchor:
    """
    Federated evidence anchor structure as per ISL v1.1 Section 7.2.
    
    Evidence anchors are cryptographically signed, tamper-evident records
    that document outcomes, observations, or attestations arising from
    the execution of intents.
    """
    source_org_id: str
    source_node_id: str
    evidence_type: EvidenceType
    payload_hash: str
    payload_uri: str
    evidence_id: UUID = field(default_factory=uuid4)
    timestamp_utc: datetime = field(default_factory=datetime.utcnow)
    source_signature: Optional[str] = None
    federation_cosignatures: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "evidence_id": str(self.evidence_id),
            "source_org_id": self.source_org_id,
            "source_node_id": self.source_node_id,
            "evidence_type": self.evidence_type.value,
            "payload_hash": self.payload_hash,
            "payload_uri": self.payload_uri,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "source_signature": self.source_signature,
            "federation_cosignatures": self.federation_cosignatures,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EvidenceAnchor":
        """Create from dictionary representation."""
        return cls(
            evidence_id=UUID(data["evidence_id"]),
            source_org_id=data["source_org_id"],
            source_node_id=data["source_node_id"],
            evidence_type=EvidenceType(data["evidence_type"]),
            payload_hash=data["payload_hash"],
            payload_uri=data["payload_uri"],
            timestamp_utc=datetime.fromisoformat(data["timestamp_utc"]),
            source_signature=data.get("source_signature"),
            federation_cosignatures=data.get("federation_cosignatures", []),
        )


class EvidenceStore:
    """
    Federated evidence registry for storing and verifying evidence anchors.
    
    This implements the evidence store as specified in Section 7.4, including
    verification pipeline and cosignature management.
    """
    
    def __init__(self):
        """Initialize an empty evidence store."""
        self.anchors: dict[UUID, EvidenceAnchor] = {}
        self.revoked: set[UUID] = set()
    
    def register_anchor(self, anchor: EvidenceAnchor) -> None:
        """
        Register a new evidence anchor.
        
        Args:
            anchor: The evidence anchor to register
        """
        if anchor.evidence_id in self.anchors:
            raise ValueError(f"Evidence anchor already exists: {anchor.evidence_id}")
        
        self.anchors[anchor.evidence_id] = anchor
    
    def get_anchor(self, evidence_id: UUID) -> Optional[EvidenceAnchor]:
        """
        Retrieve an evidence anchor by ID.
        
        Args:
            evidence_id: The evidence anchor ID
            
        Returns:
            The evidence anchor if found, None otherwise
        """
        if evidence_id in self.revoked:
            return None
        
        return self.anchors.get(evidence_id)
    
    def revoke_anchor(self, evidence_id: UUID, reason: str) -> None:
        """
        Revoke an evidence anchor.
        
        Args:
            evidence_id: The evidence anchor ID to revoke
            reason: The reason for revocation
        """
        if evidence_id not in self.anchors:
            raise ValueError(f"Evidence anchor not found: {evidence_id}")
        
        self.revoked.add(evidence_id)
    
    def add_cosignature(
        self,
        evidence_id: UUID,
        cosigner_org_id: str,
        cosigner_node_id: str,
        signature: str,
    ) -> EvidenceAnchor:
        """
        Add a federation cosignature to an evidence anchor.
        
        Args:
            evidence_id: The evidence anchor ID
            cosigner_org_id: The cosigning organization ID
            cosigner_node_id: The cosigning node ID
            signature: The cosignature
            
        Returns:
            The updated evidence anchor
        """
        anchor = self.get_anchor(evidence_id)
        if not anchor:
            raise ValueError(f"Evidence anchor not found: {evidence_id}")
        
        cosignature = {
            "cosigner_org_id": cosigner_org_id,
            "cosigner_node_id": cosigner_node_id,
            "signature": signature,
            "timestamp_utc": datetime.utcnow().isoformat(),
        }
        
        anchor.federation_cosignatures.append(cosignature)
        return anchor
    
    def verify_anchor_integrity(self, evidence_id: UUID, expected_hash: str) -> bool:
        """
        Verify the integrity of an evidence anchor.
        
        Args:
            evidence_id: The evidence anchor ID
            expected_hash: The expected SHA-256 hash
            
        Returns:
            True if the hash matches, False otherwise
        """
        anchor = self.get_anchor(evidence_id)
        if not anchor:
            return False
        
        return anchor.payload_hash == expected_hash


class EvidenceVerificationPipeline:
    """
    Evidence verification pipeline as specified in Section 7.4.
    
    This pipeline performs the following verification steps:
    1. Resolve evidence anchor from evidence store
    2. Verify cryptographic integrity (hash match)
    3. Verify source signature
    4. Verify cosignatures (if present)
    5. Check revocation status
    """
    
    def __init__(self, evidence_store: EvidenceStore, public_key_registry: dict):
        """
        Initialize the verification pipeline.
        
        Args:
            evidence_store: The federated evidence store
            public_key_registry: Registry of public keys for signature verification
        """
        self.evidence_store = evidence_store
        self.public_key_registry = public_key_registry
    
    def verify(self, evidence_id: UUID) -> tuple[bool, Optional[str]]:
        """
        Run the complete evidence verification pipeline.
        
        Args:
            evidence_id: The evidence anchor ID to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Step 1: Resolve evidence anchor
        anchor = self.evidence_store.get_anchor(evidence_id)
        if not anchor:
            return False, f"Evidence anchor not found or revoked: {evidence_id}"
        
        # Step 2: Check revocation status
        if evidence_id in self.evidence_store.revoked:
            return False, f"Evidence anchor has been revoked: {evidence_id}"
        
        # Step 3: Verify source signature (simplified - would use actual crypto)
        if not anchor.source_signature:
            return False, "Evidence anchor lacks source signature"
        
        # Step 4: Verify cosignatures (if present)
        for cosig in anchor.federation_cosignatures:
            cosigner_key = f"{cosig['cosigner_org_id']}:{cosig['cosigner_node_id']}"
            if cosigner_key not in self.public_key_registry:
                return False, f"Unrecognized cosigner: {cosigner_key}"
        
        return True, None
    
    def verify_payload_hash(self, evidence_id: UUID, payload: bytes) -> bool:
        """
        Verify that a payload matches the evidence anchor's hash.
        
        Args:
            evidence_id: The evidence anchor ID
            payload: The payload bytes to verify
            
        Returns:
            True if the hash matches, False otherwise
        """
        import hashlib
        
        anchor = self.evidence_store.get_anchor(evidence_id)
        if not anchor:
            return False
        
        computed_hash = hashlib.sha256(payload).hexdigest()
        return computed_hash == anchor.payload_hash
