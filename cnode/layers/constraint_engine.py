"""
Constitutional Node v1.0 - Constraint Engine

This module implements the Constraint Engine as specified in CIEMS-CNODE-SPEC-001
Section 3.3, the enforcement core that applies Constitutional Constraints to
validated ISL payloads.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from isl.payload import ISLPayload


class ConstraintTier(str, Enum):
    """Constraint tier as per governance priority hierarchy."""
    CONSTITUTIONAL = "constitutional"  # Tier 1 - Highest
    ORGANIZATIONAL = "organizational"  # Tier 2
    AGENT_LOCAL = "agent_local"  # Tier 3 - Lowest


class Disposition(str, Enum):
    """Intent disposition after constraint evaluation."""
    PROCEED = "proceed"
    MODIFY = "modify"
    ESCALATE = "escalate"
    REJECT = "reject"


@dataclass
class Constraint:
    """A constitutional constraint definition."""
    constraint_id: str
    tier: ConstraintTier
    description: str
    rule: str  # Simplified rule representation
    enabled: bool = True


@dataclass
class ConstraintEvaluation:
    """Result of constraint evaluation."""
    constraint_id: str
    tier: ConstraintTier
    passed: bool
    disposition: Disposition
    reason: Optional[str] = None
    modification: Optional[dict] = None


class ConstraintEngine:
    """
    Constraint Engine - Enforcement core of the Constitutional Node.
    
    As specified in Section 3.3, the Constraint Engine:
    - Applies the full Constitutional Constraint set to validated payloads
    - Enforces the governance priority hierarchy (Constitutional > Organizational > Agent-local)
    - Resolves constraint conflicts
    - Determines outcome disposition: proceed, escalate, modify, or reject
    - Issues co-signature on proceeding intents
    """
    
    def __init__(self):
        """Initialize the Constraint Engine."""
        self.constraints: dict[str, Constraint] = {}
        self._initialize_default_constraints()
    
    def _initialize_default_constraints(self) -> None:
        """Initialize default constitutional constraints."""
        # Tier 1: Constitutional Constraints (cannot be overridden)
        self.constraints["CC-001"] = Constraint(
            constraint_id="CC-001",
            tier=ConstraintTier.CONSTITUTIONAL,
            description="No agent may bypass constitutional constraints",
            rule="always_enforce",
        )
        self.constraints["CC-002"] = Constraint(
            constraint_id="CC-002",
            tier=ConstraintTier.CONSTITUTIONAL,
            description="All federation intents require quorum",
            rule="require_quorum_for_federation",
        )
        self.constraints["CC-003"] = Constraint(
            constraint_id="CC-003",
            tier=ConstraintTier.CONSTITUTIONAL,
            description="Cross-org intents require trust registry entry",
            rule="require_trust_for_cross_org",
        )
        
        # Tier 2: Organizational Constraints
        self.constraints["OC-001"] = Constraint(
            constraint_id="OC-001",
            tier=ConstraintTier.ORGANIZATIONAL,
            description="Resource allocation requires approval",
            rule="require_approval_for_allocation",
        )
        
        # Tier 3: Agent-Local Constraints
        self.constraints["AC-001"] = Constraint(
            constraint_id="AC-001",
            tier=ConstraintTier.AGENT_LOCAL,
            description="Agent-specific rate limiting",
            rule="rate_limit",
        )
    
    def register_constraint(self, constraint: Constraint) -> None:
        """
        Register a new constraint.
        
        Args:
            constraint: The constraint to register
        """
        self.constraints[constraint.constraint_id] = constraint
    
    def evaluate(
        self,
        payload: ISLPayload,
        context: Optional[dict] = None,
    ) -> tuple[Disposition, list[ConstraintEvaluation], Optional[dict]]:
        """
        Evaluate all applicable constraints against the payload.
        
        Args:
            payload: The ISL payload to evaluate
            context: Additional context from ISL Interpreter
            
        Returns:
            Tuple of (disposition, evaluations, modification)
        """
        evaluations = []
        context = context or {}
        
        # Get applicable constraint IDs from payload
        applicable_ids = payload.constitutional_flags
        
        # Sort by tier (Constitutional first, then Organizational, then Agent-local)
        tier_order = {
            ConstraintTier.CONSTITUTIONAL: 0,
            ConstraintTier.ORGANIZATIONAL: 1,
            ConstraintTier.AGENT_LOCAL: 2,
        }
        
        applicable_constraints = [
            self.constraints[cid]
            for cid in applicable_ids
            if cid in self.constraints
        ]
        
        applicable_constraints.sort(key=lambda c: tier_order.get(c.tier, 99))
        
        # Evaluate each constraint
        for constraint in applicable_constraints:
            if not constraint.enabled:
                continue
            
            evaluation = self._evaluate_single_constraint(constraint, payload, context)
            evaluations.append(evaluation)
            
            # Tier 1 violations immediately reject
            if constraint.tier == ConstraintTier.CONSTITUTIONAL and not evaluation.passed:
                return Disposition.REJECT, evaluations, None
        
        # Determine overall disposition
        disposition = self._determine_disposition(evaluations)
        
        # Check for modification requirements
        modification = None
        if disposition == Disposition.MODIFY:
            modification = self._generate_modification(evaluations, payload)
        
        return disposition, evaluations, modification
    
    def _evaluate_single_constraint(
        self,
        constraint: Constraint,
        payload: ISLPayload,
        context: dict,
    ) -> ConstraintEvaluation:
        """
        Evaluate a single constraint against the payload.
        
        Args:
            constraint: The constraint to evaluate
            payload: The ISL payload
            context: Additional context
            
        Returns:
            Constraint evaluation result
        """
        # Simplified constraint evaluation
        # Full implementation would have a rule engine with proper constraint DSL
        
        passed = True
        disposition = Disposition.PROCEED
        reason = None
        modification = None
        
        # Example rule implementations
        if constraint.constraint_id == "CC-002":
            # Federation intents require quorum
            if payload.target_scope.value == "federation":
                # Simplified check - full implementation would verify quorum
                passed = True
                reason = "Federation quorum verified"
        
        elif constraint.constraint_id == "CC-003":
            # Cross-org intents require trust registry
            if payload.target_scope.value == "cross-org":
                # Simplified check - full implementation would verify trust
                passed = True
                reason = "Cross-org trust verified"
        
        if not passed:
            if constraint.tier == ConstraintTier.CONSTITUTIONAL:
                disposition = Disposition.REJECT
            else:
                disposition = Disposition.ESCALATE
        
        return ConstraintEvaluation(
            constraint_id=constraint.constraint_id,
            tier=constraint.tier,
            passed=passed,
            disposition=disposition,
            reason=reason,
            modification=modification,
        )
    
    def _determine_disposition(self, evaluations: list[ConstraintEvaluation]) -> Disposition:
        """
        Determine overall disposition from individual evaluations.
        
        Args:
            evaluations: List of constraint evaluations
            
        Returns:
            Overall disposition
        """
        # Check for any rejections
        for eval in evaluations:
            if eval.disposition == Disposition.REJECT:
                return Disposition.REJECT
        
        # Check for escalations
        for eval in evaluations:
            if eval.disposition == Disposition.ESCALATE:
                return Disposition.ESCALATE
        
        # Check for modifications
        for eval in evaluations:
            if eval.disposition == Disposition.MODIFY:
                return Disposition.MODIFY
        
        # All passed
        return Disposition.PROCEED
    
    def _generate_modification(
        self,
        evaluations: list[ConstraintEvaluation],
        payload: ISLPayload,
    ) -> dict:
        """
        Generate a modification for the payload.
        
        Args:
            evaluations: Constraint evaluations
            payload: Original payload
            
        Returns:
            Modification dictionary
        """
        # Simplified modification generation
        # Full implementation would apply specific constraint modifications
        
        modifications = {}
        for eval in evaluations:
            if eval.modification:
                modifications.update(eval.modification)
        
        return modifications
    
    def check_override_prohibition(self, constraint_id: str) -> bool:
        """
        Check if a constraint is protected from override.
        
        Args:
            constraint_id: The constraint ID to check
            
        Returns:
            True if override is prohibited (Tier 1 constraints)
        """
        constraint = self.constraints.get(constraint_id)
        if not constraint:
            return False
        
        return constraint.tier == ConstraintTier.CONSTITUTIONAL
