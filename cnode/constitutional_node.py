"""
Constitutional Node v1.0 - Main Implementation

This module implements the complete Constitutional Node as specified in
CIEMS-CNODE-SPEC-001, orchestrating all five layers for ISL processing.
"""

from typing import Optional

from isl.payload import ISLPayload
from isl.validation import ISLValidationError

from .layers.intent_layer import IntentLayer
from .layers.isl_interpreter import ISLInterpreter
from .layers.constraint_engine import ConstraintEngine, Disposition
from .layers.evidence_layer import EvidenceLayer
from .layers.audit_ledger import AuditLedger, LedgerEventType


class ConstitutionalNode:
    """
    Constitutional Node - Foundational governance unit of CIEMS.
    
    As specified in Section 1.1, the C-Node is the atomic structural element
    through which all constitutional governance is instantiated, enforced, and
    audited within the CIEMS framework.
    
    This implementation orchestrates the five-layer architecture:
    1. Intent Layer - Ingestion boundary
    2. ISL Interpreter - Parsing and validation
    3. Constraint Engine - Enforcement core
    4. Evidence Layer - Provenance management
    5. Audit Ledger - Append-only cryptographically chained record
    """
    
    def __init__(
        self,
        node_id: str,
        agent_registry: Optional[dict] = None,
        constraint_registry: Optional[dict] = None,
        evidence_store: Optional[dict] = None,
        public_key_registry: Optional[dict] = None,
    ):
        """
        Initialize the Constitutional Node.
        
        Args:
            node_id: Unique identifier for this C-Node
            agent_registry: Registry of CIEMS-registered agents
            constraint_registry: Registry of constitutional constraints
            evidence_store: Federated evidence store
            public_key_registry: Registry of public keys for signature verification
        """
        self.node_id = node_id
        
        # Initialize the five layers
        self.intent_layer = IntentLayer()
        self.isl_interpreter = ISLInterpreter(
            agent_registry=agent_registry,
            constraint_registry=constraint_registry,
            evidence_store=evidence_store,
        )
        self.constraint_engine = ConstraintEngine()
        self.evidence_layer = EvidenceLayer(
            evidence_store=evidence_store,
            public_key_registry=public_key_registry,
        )
        self.audit_ledger = AuditLedger(node_id=node_id)
        
        # Registries
        self.agent_registry = agent_registry or {}
        self.constraint_registry = constraint_registry or {}
        self.evidence_store = evidence_store or {}
        self.public_key_registry = public_key_registry or {}
    
    def process_intent(self, payload: dict) -> dict:
        """
        Process an ISL payload through the complete C-Node pipeline.
        
        This implements the full validation pipeline as specified in Section 4.3:
        1. Schema Check (Intent Layer)
        2. Constitutional Flag Resolution (ISL Interpreter)
        3. Evidence Anchor Verification (Evidence Layer)
        4. Constraint Engine Pass (Constraint Engine)
        5. Co-Signature (if disposition is proceed)
        6. Ledger Entry (Audit Ledger)
        
        Args:
            payload: The incoming ISL payload (dict or ISLPayload)
            
        Returns:
            Processing result with disposition and details
        """
        result = {
            "node_id": self.node_id,
            "intent_id": None,
            "disposition": None,
            "stages": {},
            "error": None,
        }
        
        try:
            # Stage 1: Intent Layer - Schema Check
            is_accepted, isl_payload, rejection_reason = self.intent_layer.ingest(payload)
            result["stages"]["intent_layer"] = {
                "accepted": is_accepted,
                "rejection_reason": rejection_reason,
            }
            
            if not is_accepted:
                result["disposition"] = "rejected"
                result["error"] = rejection_reason
                return result
            
            result["intent_id"] = str(isl_payload.intent_id)
            
            # Record intent received in ledger
            self.audit_ledger.record_intent_received(
                isl_payload.intent_id,
                isl_payload.model_dump(),
            )
            
            # Stage 2: ISL Interpreter - Validation
            is_valid, validation_error, validation_context = self.isl_interpreter.interpret(isl_payload)
            result["stages"]["isl_interpreter"] = {
                "valid": is_valid,
                "error": validation_error.message if validation_error else None,
                "context": validation_context,
            }
            
            if not is_valid:
                self.audit_ledger.record_intent_rejected(
                    isl_payload.intent_id,
                    validation_error.message,
                    validation_error.code,
                    validation_error.details,
                )
                result["disposition"] = "rejected"
                result["error"] = validation_error.message
                return result
            
            # Record intent validated in ledger
            self.audit_ledger.record_intent_validated(
                isl_payload.intent_id,
                validation_context or {},
            )
            
            # Stage 3: Evidence Layer - Evidence Anchor Verification
            evidence_refs = isl_payload.evidence_refs or []
            all_evidence_valid, resolved_anchors, failed_evidence_ids = self.evidence_layer.resolve_evidence_refs(
                evidence_refs
            )
            
            evidence_context = self.evidence_layer.attach_evidence_context(
                isl_payload,
                resolved_anchors,
            )
            
            result["stages"]["evidence_layer"] = {
                "all_valid": all_evidence_valid,
                "resolved_count": len(resolved_anchors),
                "failed_ids": failed_evidence_ids,
            }
            
            if not all_evidence_valid:
                self.audit_ledger.record_intent_rejected(
                    isl_payload.intent_id,
                    f"Evidence verification failed for: {failed_evidence_ids}",
                    "ISL-E003",
                    {"failed_evidence_ids": failed_evidence_ids},
                )
                result["disposition"] = "rejected"
                result["error"] = f"Evidence verification failed"
                return result
            
            # Stage 4: Constraint Engine - Constraint Evaluation
            disposition, evaluations, modification = self.constraint_engine.evaluate(
                isl_payload,
                validation_context,
            )
            
            result["stages"]["constraint_engine"] = {
                "disposition": disposition.value,
                "evaluations": [
                    {
                        "constraint_id": e.constraint_id,
                        "tier": e.tier.value,
                        "passed": e.passed,
                        "disposition": e.disposition.value,
                        "reason": e.reason,
                    }
                    for e in evaluations
                ],
                "modification": modification,
            }
            
            # Record each constraint evaluation
            for eval in evaluations:
                self.audit_ledger.record_constraint_evaluation(
                    isl_payload.intent_id,
                    eval.constraint_id,
                    eval.tier.value,
                    eval.passed,
                    eval.disposition.value,
                )
            
            # Handle disposition
            if disposition == Disposition.REJECT:
                self.audit_ledger.record_intent_rejected(
                    isl_payload.intent_id,
                    "Constraint evaluation resulted in rejection",
                    None,
                    {"failed_constraints": [e.constraint_id for e in evaluations if not e.passed]},
                )
                result["disposition"] = "rejected"
                result["error"] = "Constraint evaluation rejected the intent"
                return result
            
            elif disposition == Disposition.ESCALATE:
                self.audit_ledger.record_intent_rejected(
                    isl_payload.intent_id,
                    "Constraint evaluation resulted in escalation",
                    None,
                    {"escalated_constraints": [e.constraint_id for e in evaluations if e.disposition.value == "escalate"]},
                )
                result["disposition"] = "escalated"
                result["error"] = "Constraint evaluation escalated the intent"
                return result
            
            elif disposition == Disposition.MODIFY:
                # Log modification
                self.audit_ledger.append_entry(
                    event_type=LedgerEventType.INTENT_MODIFIED,
                    data={
                        "intent_id": str(isl_payload.intent_id),
                        "modification": modification,
                    },
                )
                result["disposition"] = "modified"
                result["modification"] = modification
                # In a full implementation, would apply modification and re-evaluate
                return result
            
            # Stage 5: Co-Signature (for proceed disposition)
            if disposition == Disposition.PROCEED:
                # In a full implementation, would generate C-Node co-signature
                co_signature = f"cnode-sig-{self.node_id}"  # Placeholder
                
                self.audit_ledger.record_intent_proceeded(
                    isl_payload.intent_id,
                    disposition.value,
                    co_signature,
                )
                
                result["disposition"] = "proceeded"
                result["co_signature"] = co_signature
                return result
            
        except Exception as e:
            result["error"] = f"Processing error: {str(e)}"
            result["disposition"] = "error"
            
            # Record error in ledger
            if result.get("intent_id"):
                try:
                    from uuid import UUID
                    self.audit_ledger.append_entry(
                        event_type=LedgerEventType.INTENT_REJECTED,
                        data={
                            "intent_id": result["intent_id"],
                            "error": str(e),
                        },
                    )
                except:
                    pass
        
        return result
    
    def get_ledger_stats(self) -> dict:
        """Get Audit Ledger statistics."""
        return self.audit_ledger.get_stats()
    
    def get_intent_layer_stats(self) -> dict:
        """Get Intent Layer statistics."""
        return self.intent_layer.get_stats()
    
    def verify_ledger_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify the cryptographic chain integrity of the Audit Ledger."""
        return self.audit_ledger.verify_chain_integrity()
