"""
Constitutional Node v1.0 - Evidence Layer

This module implements the Evidence Layer as specified in CIEMS-CNODE-SPEC-001
Section 3.1, responsible for provenance management and federated evidence verification.
"""

from typing import Optional

from isl.evidence import EvidenceAnchor, EvidenceStore, EvidenceVerificationPipeline


class EvidenceLayer:
    """
    Evidence Layer - Provenance management for the Constitutional Node.
    
    As specified in Section 3.1, the Evidence Layer:
    - Resolves and verifies evidence_refs[] anchors against the federated evidence store
    - Attaches resolved evidence records to the intent context for Constraint Engine use
    - Generates new Federated Evidence records for decisions of constitutional significance
    """
    
    def __init__(self, evidence_store: Optional[EvidenceStore] = None, public_key_registry: Optional[dict] = None):
        """
        Initialize the Evidence Layer.
        
        Args:
            evidence_store: The federated evidence store
            public_key_registry: Registry of public keys for signature verification
        """
        self.evidence_store = evidence_store or EvidenceStore()
        self.public_key_registry = public_key_registry or {}
        self.verification_pipeline = EvidenceVerificationPipeline(
            self.evidence_store,
            self.public_key_registry,
        )
    
    def resolve_evidence_refs(self, evidence_refs: list[str]) -> tuple[bool, list[Optional[EvidenceAnchor]], list[str]]:
        """
        Resolve evidence references from an ISL payload.
        
        Args:
            evidence_refs: List of evidence_id strings from the payload
            
        Returns:
            Tuple of (all_valid, resolved_anchors, failed_ids)
        """
        if not evidence_refs:
            return True, [], []
        
        resolved_anchors = []
        failed_ids = []
        all_valid = True
        
        for evidence_id_str in evidence_refs:
            try:
                from uuid import UUID
                evidence_id = UUID(evidence_id_str)
                
                # Verify the evidence anchor
                is_valid, error = self.verification_pipeline.verify(evidence_id)
                
                if is_valid:
                    anchor = self.evidence_store.get_anchor(evidence_id)
                    resolved_anchors.append(anchor)
                else:
                    failed_ids.append(evidence_id_str)
                    all_valid = False
                    
            except Exception as e:
                failed_ids.append(evidence_id_str)
                all_valid = False
        
        return all_valid, resolved_anchors, failed_ids
    
    def attach_evidence_context(
        self,
        payload,
        resolved_anchors: list[EvidenceAnchor],
    ) -> dict:
        """
        Attach resolved evidence records to intent context.
        
        Args:
            payload: The ISL payload
            resolved_anchors: List of resolved evidence anchors
            
        Returns:
            Evidence context dictionary for Constraint Engine
        """
        context = {
            "evidence_count": len(resolved_anchors),
            "evidence_types": [anchor.evidence_type.value for anchor in resolved_anchors],
            "evidence_sources": [anchor.source_org_id for anchor in resolved_anchors],
            "evidence_timestamps": [anchor.timestamp_utc.isoformat() for anchor in resolved_anchors],
        }
        
        return context
    
    def generate_evidence_anchor(
        self,
        source_org_id: str,
        source_node_id: str,
        evidence_type: str,
        payload_hash: str,
        payload_uri: str,
        source_signature: Optional[str] = None,
    ) -> EvidenceAnchor:
        """
        Generate a new federated evidence anchor.
        
        Args:
            source_org_id: Source organization ID
            source_node_id: Source node ID
            evidence_type: Type of evidence
            payload_hash: SHA-256 hash of the evidence payload
            payload_uri: URI pointing to the evidence payload
            source_signature: Optional source signature
            
        Returns:
            The created evidence anchor
        """
        from isl.payload import EvidenceType
        
        anchor = EvidenceAnchor(
            source_org_id=source_org_id,
            source_node_id=source_node_id,
            evidence_type=EvidenceType(evidence_type),
            payload_hash=payload_hash,
            payload_uri=payload_uri,
            source_signature=source_signature,
        )
        
        self.evidence_store.register_anchor(anchor)
        return anchor
    
    def add_cosignature(
        self,
        evidence_id_str: str,
        cosigner_org_id: str,
        cosigner_node_id: str,
        signature: str,
    ) -> bool:
        """
        Add a federation cosignature to an evidence anchor.
        
        Args:
            evidence_id_str: The evidence anchor ID as string
            cosigner_org_id: Cosigning organization ID
            cosigner_node_id: Cosigning node ID
            signature: The cosignature
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from uuid import UUID
            evidence_id = UUID(evidence_id_str)
            
            self.evidence_store.add_cosignature(
                evidence_id,
                cosigner_org_id,
                cosigner_node_id,
                signature,
            )
            return True
            
        except Exception:
            return False
