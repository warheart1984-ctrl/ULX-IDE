"""
ISL v1.1 Cross-Organization Governance Implementation

This module implements the cross-organization governance primitives as specified
in CIEMS-ISL-0011 Section 8, including trust model, cross-org ISL flow,
constitutional compatibility, and Governance Interoperability Agreements (GIA).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class TrustLevel(str, Enum):
    """Trust level for cross-organization relationships."""
    FULL = "full"
    LIMITED = "limited"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class CompatibilityStatus(str, Enum):
    """Constitutional compatibility status."""
    COMPATIBLE = "compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    PENDING_REVIEW = "pending_review"


@dataclass
class TrustRegistryEntry:
    """Trust registry entry for an organization."""
    org_id: str
    trust_level: TrustLevel
    registered_at: datetime
    last_updated: datetime
    public_key: str
    constitutional_version: str
    notes: Optional[str] = None


@dataclass
class GovernanceInteroperabilityAgreement:
    """
    Governance Interoperability Agreement (GIA) as per Section 8.5.
    
    A GIA defines the terms under which two organizations exchange ISL payloads
    across organizational boundaries.
    """
    agreement_id: str
    org_a_id: str
    org_b_id: str
    effective_date: datetime
    expiry_date: Optional[datetime]
    acknowledgment_timeout_seconds: int
    evidence_sharing_policy: str
    dispute_resolution_authority: str
    constitutional_compatibility: CompatibilityStatus
    sanctions_enabled: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "agreement_id": self.agreement_id,
            "org_a_id": self.org_a_id,
            "org_b_id": self.org_b_id,
            "effective_date": self.effective_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "acknowledgment_timeout_seconds": self.acknowledgment_timeout_seconds,
            "evidence_sharing_policy": self.evidence_sharing_policy,
            "dispute_resolution_authority": self.dispute_resolution_authority,
            "constitutional_compatibility": self.constitutional_compatibility.value,
            "sanctions_enabled": self.sanctions_enabled,
        }


class CrossOrgTrustRegistry:
    """
    Trust registry for cross-organization governance.
    
    Maintains trust relationships with other CIEMS-enrolled organizations
    as specified in Section 8.2.
    """
    
    def __init__(self, local_org_id: str):
        """
        Initialize the trust registry.
        
        Args:
            local_org_id: The local organization's ID
        """
        self.local_org_id = local_org_id
        self.entries: dict[str, TrustRegistryEntry] = {}
    
    def register_organization(
        self,
        org_id: str,
        public_key: str,
        constitutional_version: str,
        trust_level: TrustLevel = TrustLevel.LIMITED,
        notes: Optional[str] = None,
    ) -> TrustRegistryEntry:
        """
        Register a new organization in the trust registry.
        
        Args:
            org_id: The organization ID to register
            public_key: The organization's public key
            constitutional_version: The organization's constitutional version
            trust_level: Initial trust level
            notes: Optional notes
            
        Returns:
            The created trust registry entry
        """
        now = datetime.utcnow()
        
        entry = TrustRegistryEntry(
            org_id=org_id,
            trust_level=trust_level,
            registered_at=now,
            last_updated=now,
            public_key=public_key,
            constitutional_version=constitutional_version,
            notes=notes,
        )
        
        self.entries[org_id] = entry
        return entry
    
    def get_entry(self, org_id: str) -> Optional[TrustRegistryEntry]:
        """Retrieve a trust registry entry."""
        return self.entries.get(org_id)
    
    def update_trust_level(self, org_id: str, trust_level: TrustLevel) -> None:
        """Update the trust level for an organization."""
        entry = self.get_entry(org_id)
        if not entry:
            raise ValueError(f"Organization not found in trust registry: {org_id}")
        
        entry.trust_level = trust_level
        entry.last_updated = datetime.utcnow()
    
    def revoke_organization(self, org_id: str, reason: str) -> None:
        """Revoke trust for an organization."""
        entry = self.get_entry(org_id)
        if not entry:
            raise ValueError(f"Organization not found in trust registry: {org_id}")
        
        entry.trust_level = TrustLevel.REVOKED
        entry.last_updated = datetime.utcnow()
        entry.notes = f"REVOKED: {reason}"
    
    def is_trusted(self, org_id: str, minimum_level: TrustLevel = TrustLevel.LIMITED) -> bool:
        """
        Check if an organization is trusted at or above the minimum level.
        
        Args:
            org_id: The organization ID to check
            minimum_level: The minimum required trust level
            
        Returns:
            True if trusted, False otherwise
        """
        entry = self.get_entry(org_id)
        if not entry:
            return False
        
        trust_hierarchy = {
            TrustLevel.REVOKED: 0,
            TrustLevel.SUSPENDED: 1,
            TrustLevel.LIMITED: 2,
            TrustLevel.FULL: 3,
        }
        
        return trust_hierarchy.get(entry.trust_level, 0) >= trust_hierarchy.get(minimum_level, 0)


class GIARegistry:
    """
    Registry for Governance Interoperability Agreements.
    
    Manages GIAs as specified in Section 8.5.
    """
    
    def __init__(self):
        """Initialize an empty GIA registry."""
        self.agreements: dict[str, GovernanceInteroperabilityAgreement] = {}
    
    def register_agreement(self, gia: GovernanceInteroperabilityAgreement) -> None:
        """Register a new GIA."""
        self.agreements[gia.agreement_id] = gia
    
    def get_agreement(self, agreement_id: str) -> Optional[GovernanceInteroperabilityAgreement]:
        """Retrieve a GIA by ID."""
        return self.agreements.get(agreement_id)
    
    def find_agreement_between(self, org_a_id: str, org_b_id: str) -> Optional[GovernanceInteroperabilityAgreement]:
        """Find a GIA between two organizations."""
        for gia in self.agreements.values():
            if (gia.org_a_id == org_a_id and gia.org_b_id == org_b_id) or \
               (gia.org_a_id == org_b_id and gia.org_b_id == org_a_id):
                return gia
        return None
    
    def check_compatibility(self, org_a_id: str, org_b_id: str) -> CompatibilityStatus:
        """
        Check constitutional compatibility between two organizations.
        
        Args:
            org_a_id: First organization ID
            org_b_id: Second organization ID
            
        Returns:
            Compatibility status
        """
        gia = self.find_agreement_between(org_a_id, org_b_id)
        if not gia:
            return CompatibilityStatus.PENDING_REVIEW
        
        return gia.constitutional_compatibility


class CrossOrgGateway:
    """
    Cross-organization gateway for ISL payload transmission.
    
    Implements the cross-org ISL flow as specified in Section 8.3.
    """
    
    def __init__(
        self,
        local_org_id: str,
        trust_registry: CrossOrgTrustRegistry,
        gia_registry: GIARegistry,
    ):
        """
        Initialize the cross-org gateway.
        
        Args:
            local_org_id: The local organization's ID
            trust_registry: The trust registry
            gia_registry: The GIA registry
        """
        self.local_org_id = local_org_id
        self.trust_registry = trust_registry
        self.gia_registry = gia_registry
    
    def validate_outbound_payload(self, target_org_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate an outbound cross-org ISL payload.
        
        Args:
            target_org_id: The target organization ID
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if target organization is trusted
        if not self.trust_registry.is_trusted(target_org_id):
            return False, f"Target organization not trusted: {target_org_id}"
        
        # Check if GIA exists
        gia = self.gia_registry.find_agreement_between(self.local_org_id, target_org_id)
        if not gia:
            return False, f"No GIA exists between {self.local_org_id} and {target_org_id}"
        
        # Check GIA expiry
        if gia.expiry_date and datetime.utcnow() > gia.expiry_date:
            return False, f"GIA has expired: {gia.agreement_id}"
        
        # Check constitutional compatibility
        if gia.constitutional_compatibility == CompatibilityStatus.INCOMPATIBLE:
            return False, f"Constitutional incompatibility with {target_org_id}"
        
        return True, None
    
    def validate_inbound_payload(self, source_org_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate an inbound cross-org ISL payload.
        
        Args:
            source_org_id: The source organization ID
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if source organization is trusted
        if not self.trust_registry.is_trusted(source_org_id):
            return False, f"Source organization not trusted: {source_org_id}"
        
        # Check if GIA exists
        gia = self.gia_registry.find_agreement_between(self.local_org_id, source_org_id)
        if not gia:
            return False, f"No GIA exists between {self.local_org_id} and {source_org_id}"
        
        # Check GIA expiry
        if gia.expiry_date and datetime.utcnow() > gia.expiry_date:
            return False, f"GIA has expired: {gia.agreement_id}"
        
        return True, None
    
    def record_transmission(
        self,
        intent_id: UUID,
        source_org_id: str,
        target_org_id: str,
        direction: str,
    ) -> dict:
        """
        Record a cross-org transmission for audit purposes.
        
        Args:
            intent_id: The transmitted intent ID
            source_org_id: Source organization ID
            target_org_id: Target organization ID
            direction: "outbound" or "inbound"
            
        Returns:
            Audit record
        """
        return {
            "intent_id": str(intent_id),
            "source_org_id": source_org_id,
            "target_org_id": target_org_id,
            "direction": direction,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "local_org_id": self.local_org_id,
        }
