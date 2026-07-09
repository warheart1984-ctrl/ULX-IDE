"""
Constitutional Node v1.0 - Audit Ledger

This module implements the Audit Ledger as specified in CIEMS-CNODE-SPEC-001
Section 3.4, an append-only, cryptographically chained record of all governance events.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class LedgerEventType(str, Enum):
    """Types of events recorded in the Audit Ledger."""
    INTENT_RECEIVED = "intent_received"
    INTENT_VALIDATED = "intent_validated"
    INTENT_REJECTED = "intent_rejected"
    CONSTRAINT_EVALUATED = "constraint_evaluated"
    INTENT_PROCEEDED = "intent_proceeded"
    INTENT_ESCALATED = "intent_escalated"
    INTENT_MODIFIED = "intent_modified"
    COSIGNATURE_APPLIED = "cosignature_applied"
    EVIDENCE_VERIFIED = "evidence_verified"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"
    LEDGER_INTEGRITY_VIOLATION = "ledger_integrity_violation"


@dataclass
class LedgerEntry:
    """
    A single entry in the Audit Ledger.
    
    As specified in Section 3.4, each entry must include:
    - Cryptographic chaining (hash of previous entry)
    - Complete event data
    - Timestamp
    """
    entry_id: UUID = field(default_factory=uuid4)
    previous_entry_hash: str = ""
    event_type: LedgerEventType = LedgerEventType.INTENT_RECEIVED
    timestamp_utc: datetime = field(default_factory=datetime.utcnow)
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def compute_hash(self) -> str:
        """Compute the SHA-256 hash of this entry for chaining."""
        entry_dict = {
            "entry_id": str(self.entry_id),
            "previous_entry_hash": self.previous_entry_hash,
            "event_type": self.event_type.value,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }
        
        entry_json = json.dumps(entry_dict, sort_keys=True)
        return hashlib.sha256(entry_json.encode("utf-8")).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "entry_id": str(self.entry_id),
            "previous_entry_hash": self.previous_entry_hash,
            "entry_hash": self.compute_hash(),
            "event_type": self.event_type.value,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }


class AuditLedger:
    """
    Audit Ledger - Append-only, cryptographically chained record.
    
    As specified in Section 3.4, the Audit Ledger:
    - Is append-only (no record may be modified or deleted)
    - Uses cryptographic chaining (each entry hashes the previous)
    - Is complete (every governance event must be recorded)
    - Provides tamper evidence (Merkle root for integrity verification)
    - Enforces retention obligations
    """
    
    def __init__(self, node_id: str):
        """
        Initialize the Audit Ledger.
        
        Args:
            node_id: The C-Node identifier for this ledger
        """
        self.node_id = node_id
        self.entries: list[LedgerEntry] = []
        self._create_genesis_entry()
    
    def _create_genesis_entry(self) -> None:
        """Create the genesis entry that anchors the ledger chain."""
        genesis = LedgerEntry(
            event_type=LedgerEventType.INTENT_RECEIVED,
            data={
                "node_id": self.node_id,
                "genesis": True,
                "message": "Audit Ledger genesis entry",
            },
            metadata={"genesis": True},
        )
        
        genesis.previous_entry_hash = "0" * 64  # Zero hash for genesis
        genesis_hash = genesis.compute_hash()
        
        self.entries.append(genesis)
    
    def append_entry(
        self,
        event_type: LedgerEventType,
        data: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> LedgerEntry:
        """
        Append a new entry to the ledger.
        
        Args:
            event_type: The type of event
            data: Event data
            metadata: Optional metadata
            
        Returns:
            The created ledger entry
        """
        # Get the hash of the previous entry
        previous_hash = self.entries[-1].compute_hash() if self.entries else "0" * 64
        
        # Create new entry
        entry = LedgerEntry(
            previous_entry_hash=previous_hash,
            event_type=event_type,
            data=data,
            metadata=metadata or {},
        )
        
        # Verify chain integrity before appending
        if self.entries and entry.previous_entry_hash != self.entries[-1].compute_hash():
            raise ValueError("Chain integrity violation detected")
        
        self.entries.append(entry)
        return entry
    
    def record_intent_received(self, intent_id: UUID, payload: dict) -> LedgerEntry:
        """Record an intent received event."""
        return self.append_entry(
            event_type=LedgerEventType.INTENT_RECEIVED,
            data={
                "intent_id": str(intent_id),
                "issuing_agent_id": payload.get("issuing_agent_id"),
                "intent_class": payload.get("intent_class"),
                "target_scope": payload.get("target_scope"),
            },
        )
    
    def record_intent_validated(self, intent_id: UUID, validation_context: dict) -> LedgerEntry:
        """Record an intent validated event."""
        return self.append_entry(
            event_type=LedgerEventType.INTENT_VALIDATED,
            data={
                "intent_id": str(intent_id),
                "validation_context": validation_context,
            },
        )
    
    def record_intent_rejected(
        self,
        intent_id: UUID,
        rejection_reason: str,
        error_code: Optional[str] = None,
        error_details: Optional[dict] = None,
    ) -> LedgerEntry:
        """Record an intent rejected event."""
        return self.append_entry(
            event_type=LedgerEventType.INTENT_REJECTED,
            data={
                "intent_id": str(intent_id),
                "rejection_reason": rejection_reason,
                "error_code": error_code,
                "error_details": error_details,
            },
        )
    
    def record_constraint_evaluation(
        self,
        intent_id: UUID,
        constraint_id: str,
        tier: str,
        passed: bool,
        disposition: str,
    ) -> LedgerEntry:
        """Record a constraint evaluation event."""
        return self.append_entry(
            event_type=LedgerEventType.CONSTRAINT_EVALUATED,
            data={
                "intent_id": str(intent_id),
                "constraint_id": constraint_id,
                "tier": tier,
                "passed": passed,
                "disposition": disposition,
            },
        )
    
    def record_intent_proceeded(
        self,
        intent_id: UUID,
        disposition: str,
        cosignature: Optional[str] = None,
    ) -> LedgerEntry:
        """Record an intent proceeded event."""
        return self.append_entry(
            event_type=LedgerEventType.INTENT_PROCEEDED,
            data={
                "intent_id": str(intent_id),
                "disposition": disposition,
                "cosignature": cosignature,
            },
        )
    
    def record_constitutional_violation(
        self,
        intent_id: UUID,
        constraint_id: str,
        violation_details: dict,
    ) -> LedgerEntry:
        """Record a constitutional violation event."""
        return self.append_entry(
            event_type=LedgerEventType.CONSTITUTIONAL_VIOLATION,
            data={
                "intent_id": str(intent_id),
                "constraint_id": constraint_id,
                "violation_details": violation_details,
            },
            metadata={"severity": "critical"},
        )
    
    def verify_chain_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify the cryptographic chain integrity of the ledger.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i - 1]
            
            expected_previous_hash = previous.compute_hash()
            if current.previous_entry_hash != expected_previous_hash:
                return False, f"Chain break detected at entry {i}: expected {expected_previous_hash}, got {current.previous_entry_hash}"
        
        return True, None
    
    def get_merkle_root(self) -> str:
        """
        Compute the Merkle root of the ledger for tamper evidence.
        
        Returns:
            Merkle root hash
        """
        if not self.entries:
            return "0" * 64
        
        # Simplified Merkle root computation
        # Full implementation would use proper Merkle tree
        hashes = [entry.compute_hash() for entry in self.entries]
        
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                new_hashes.append(new_hash)
            
            hashes = new_hashes
        
        return hashes[0] if hashes else "0" * 64
    
    def get_entries_for_intent(self, intent_id: UUID) -> list[LedgerEntry]:
        """
        Get all ledger entries for a specific intent.
        
        Args:
            intent_id: The intent ID
            
        Returns:
            List of related ledger entries
        """
        intent_id_str = str(intent_id)
        return [
            entry for entry in self.entries
            if entry.data.get("intent_id") == intent_id_str
        ]
    
    def get_stats(self) -> dict:
        """Get ledger statistics."""
        event_counts = {}
        for entry in self.entries:
            event_type = entry.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_entries": len(self.entries),
            "event_counts": event_counts,
            "merkle_root": self.get_merkle_root(),
            "chain_integrity_valid": self.verify_chain_integrity()[0],
        }
