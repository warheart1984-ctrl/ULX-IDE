"""
ISL v1.1 Multi-Agent Intent Composition Implementation

This module implements the multi-agent intent composition lifecycle as specified
in CIEMS-ISL-0011 Section 6, including composition lifecycle, quorum rules,
conflict handling, and timeout behavior.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from .payload import (
    ISLPayload,
    IntentClass,
    CompositionLogic,
    CoAuthorSignature,
    CompositionRequestBody,
)


class CompositionPhase(str, Enum):
    """Composition lifecycle phases."""
    INITIATION = "initiation"
    CO_AUTHOR_SOLICITATION = "co_author_solicitation"
    ENDORSEMENT_COLLECTION = "endorsement_collection"
    QUORUM_CHECK = "quorum_check"
    COMPOSITION_FINALIZATION = "composition_finalization"
    BROADCAST = "broadcast"
    EXPIRED = "expired"


class EndorsementStatus(str, Enum):
    """Endorsement status from co-authors."""
    ENDORSED = "endorsed"
    ESCALATED = "escalated"
    NO_RESPONSE = "no_response"
    VETOED = "vetoed"


@dataclass
class Endorsement:
    """Endorsement record from a co-author."""
    agent_id: str
    status: EndorsementStatus
    timestamp: datetime
    rationale: Optional[str] = None
    escalation_target: Optional[str] = None


@dataclass
class CompositionSession:
    """Active composition session state."""
    chain_id: UUID
    initiating_agent_id: str
    co_authors: list[str]
    component_intents: list[dict]
    composition_logic: CompositionLogic
    resolution_authority: str
    phase: CompositionPhase
    endorsements: dict[str, Endorsement]
    initiated_at: datetime
    timeout_seconds: int = 3600
    quorum_threshold: Optional[int] = None
    
    @property
    def expires_at(self) -> datetime:
        """Calculate expiry timestamp."""
        return self.initiated_at + timedelta(seconds=self.timeout_seconds)
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def participating_count(self) -> int:
        """Count of co-authors who responded (endorsed, escalated, or vetoed)."""
        return sum(
            1 for e in self.endorsements.values()
            if e.status in (EndorsementStatus.ENDORSED, EndorsementStatus.ESCALATED, EndorsementStatus.VETOED)
        )
    
    @property
    def endorsed_count(self) -> int:
        """Count of endorsements."""
        return sum(1 for e in self.endorsements.values() if e.status == EndorsementStatus.ENDORSED)
    
    @property
    def vetoed_count(self) -> int:
        """Count of vetoes."""
        return sum(1 for e in self.endorsements.values() if e.status == EndorsementStatus.VETOED)


class CompositionEngine:
    """
    Multi-agent intent composition engine.
    
    Implements the composition lifecycle as specified in Section 6.1:
    1. Initiation
    2. Co-Author Solicitation
    3. Endorsement Collection
    4. Quorum Check
    5. Composition Finalization
    6. Broadcast
    """
    
    def __init__(self, default_timeout_seconds: int = 3600):
        """
        Initialize the composition engine.
        
        Args:
            default_timeout_seconds: Default timeout for composition sessions (default: 3600s)
        """
        self.default_timeout_seconds = default_timeout_seconds
        self.active_sessions: dict[UUID, CompositionSession] = {}
    
    def initiate_composition(
        self,
        initiating_agent_id: str,
        composition_request: CompositionRequestBody,
        co_authors: list[str],
        timeout_seconds: Optional[int] = None,
    ) -> CompositionSession:
        """
        Phase 1: Initiation - Create a new composition session.
        
        Args:
            initiating_agent_id: Agent initiating the composition
            composition_request: The composition-request intent body
            co_authors: List of co-author agent IDs
            timeout_seconds: Optional timeout override
            
        Returns:
            The created composition session
        """
        chain_id = uuid4()
        
        session = CompositionSession(
            chain_id=chain_id,
            initiating_agent_id=initiating_agent_id,
            co_authors=co_authors,
            component_intents=[ci.model_dump() for ci in composition_request.component_intents],
            composition_logic=composition_request.composition_logic,
            resolution_authority=composition_request.resolution_authority,
            phase=CompositionPhase.CO_AUTHOR_SOLICITATION,
            endorsements={},
            initiated_at=datetime.utcnow(),
            timeout_seconds=timeout_seconds or self.default_timeout_seconds,
        )
        
        self.active_sessions[chain_id] = session
        return session
    
    def record_endorsement(
        self,
        chain_id: UUID,
        agent_id: str,
        status: EndorsementStatus,
        rationale: Optional[str] = None,
        escalation_target: Optional[str] = None,
    ) -> CompositionSession:
        """
        Phase 3: Record an endorsement from a co-author.
        
        Args:
            chain_id: Composition session identifier
            agent_id: Co-author agent ID
            status: Endorsement status
            rationale: Optional rationale for the endorsement
            escalation_target: Optional escalation target if status is escalated
            
        Returns:
            The updated composition session
        """
        session = self.active_sessions.get(chain_id)
        if not session:
            raise ValueError(f"Composition session not found: {chain_id}")
        
        if agent_id not in session.co_authors:
            raise ValueError(f"Agent {agent_id} is not a co-author in this composition")
        
        session.endorsements[agent_id] = Endorsement(
            agent_id=agent_id,
            status=status,
            timestamp=datetime.utcnow(),
            rationale=rationale,
            escalation_target=escalation_target,
        )
        
        return session
    
    def check_quorum(self, session: CompositionSession) -> tuple[bool, str]:
        """
        Phase 4: Evaluate quorum achievement.
        
        Args:
            session: The composition session to evaluate
            
        Returns:
            Tuple of (quorum_achieved, reason)
        """
        # Check for vetoes - veto immediately fails quorum
        if session.vetoed_count > 0:
            return False, f"Quorum not achieved: {session.vetoed_count} veto(es) received"
        
        # Determine quorum threshold
        threshold = session.quorum_threshold or self._calculate_default_quorum(session)
        
        # Apply quorum rules based on composition logic
        if session.composition_logic == CompositionLogic.SEQUENCE:
            # Sequential: all co-authors must endorse
            required = len(session.co_authors)
            achieved = session.endorsed_count
        elif session.composition_logic == CompositionLogic.AND:
            # AND: simple majority of co_authors
            required = (len(session.co_authors) // 2) + 1
            achieved = session.endorsed_count
        else:  # OR
            # OR: any endorsement constitutes partial success
            required = 1
            achieved = session.endorsed_count
        
        quorum_achieved = achieved >= required
        reason = f"Quorum {'achieved' if quorum_achieved else 'not achieved'}: {achieved}/{required} endorsements"
        
        return quorum_achieved, reason
    
    def _calculate_default_quorum(self, session: CompositionSession) -> int:
        """Calculate default quorum threshold based on composition logic."""
        if session.composition_logic == CompositionLogic.SEQUENCE:
            return len(session.co_authors)
        elif session.composition_logic == CompositionLogic.AND:
            return (len(session.co_authors) // 2) + 1
        else:  # OR
            return 1
    
    def detect_conflict(self, session: CompositionSession) -> Optional[dict]:
        """
        Phase 6.3: Detect conflicts in component intents.
        
        Args:
            session: The composition session to check
            
        Returns:
            Conflict details if detected, None otherwise
        """
        # Simplified conflict detection - full implementation would compare
        # component intent fields for material differences
        
        # Check for escalations (indicates conflict)
        escalations = [
            e for e in session.endorsements.values()
            if e.status == EndorsementStatus.ESCALATED
        ]
        
        if escalations:
            return {
                "conflict_type": "escalation",
                "escalating_agents": [e.agent_id for e in escalations],
                "escalation_targets": [e.escalation_target for e in escalations],
            }
        
        return None
    
    def finalize_composition(
        self,
        session: CompositionSession,
        co_author_signatures: list[CoAuthorSignature],
    ) -> ISLPayload:
        """
        Phase 5: Finalize the composition into a single ISL payload.
        
        Args:
            session: The composition session to finalize
            co_author_signatures: List of co-author signatures
            
        Returns:
            The finalized ISL payload with all signatures
        """
        if session.phase != CompositionPhase.QUORUM_CHECK:
            raise ValueError(f"Cannot finalize composition in phase: {session.phase}")
        
        # Create the final ISL payload
        # This is a simplified version - full implementation would merge component intents
        # according to composition_logic
        
        payload = ISLPayload(
            intent_class=IntentClass.DIRECTIVE,  # Simplified - would be determined by composition
            issuing_agent_id=session.initiating_agent_id,
            co_authors=session.co_authors,
            target_scope="subsystem",  # Simplified
            intent_body={
                "action": "composed_action",
                "target_resource": "composed_target",
                "rollback_policy": "immediate-rollback",
            },
            constitutional_flags=["composition-finalized"],
            co_author_signatures=co_author_signatures,
            chain_id=session.chain_id,
        )
        
        session.phase = CompositionPhase.BROADCAST
        return payload
    
    def expire_session(self, chain_id: UUID) -> CompositionSession:
        """
        Phase 6.4: Mark a composition session as expired.
        
        Args:
            chain_id: Composition session identifier
            
        Returns:
            The expired session
        """
        session = self.active_sessions.get(chain_id)
        if not session:
            raise ValueError(f"Composition session not found: {chain_id}")
        
        session.phase = CompositionPhase.EXPIRED
        return session
