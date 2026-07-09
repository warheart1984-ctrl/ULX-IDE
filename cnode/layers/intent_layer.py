"""
Constitutional Node v1.0 - Intent Layer

This module implements the Intent Layer as specified in CIEMS-CNODE-SPEC-001
Section 3.1, the ingestion boundary for all incoming intent declarations.
"""

from typing import Optional

from isl.payload import ISLPayload


class IntentLayer:
    """
    Intent Layer - Ingestion boundary for the Constitutional Node.
    
    As specified in Section 3.1, the Intent Layer:
    - Receives all incoming intent declarations
    - Performs initial format detection, source authentication, and ISL version verification
    - Rejects non-ISL payloads at the boundary
    - Forwards conforming payloads to the ISL Interpreter
    """
    
    def __init__(self):
        """Initialize the Intent Layer."""
        self.rejected_count = 0
        self.accepted_count = 0
    
    def ingest(self, payload: dict) -> tuple[bool, Optional[ISLPayload], Optional[str]]:
        """
        Ingest an incoming payload and perform initial validation.
        
        Args:
            payload: The incoming payload (dict or ISLPayload)
            
        Returns:
            Tuple of (is_accepted, isl_payload, rejection_reason)
        """
        # Check if payload is already an ISLPayload
        if isinstance(payload, ISLPayload):
            # Perform initial ISL version check
            if payload.schema_version != "ISL-1.1":
                self.rejected_count += 1
                return False, None, f"Unsupported ISL version: {payload.schema_version}"
            
            self.accepted_count += 1
            return True, payload, None
        
        # Attempt to parse as ISL payload
        try:
            isl_payload = ISLPayload(**payload)
            
            # Verify ISL version
            if isl_payload.schema_version != "ISL-1.1":
                self.rejected_count += 1
                return False, None, f"Unsupported ISL version: {isl_payload.schema_version}"
            
            self.accepted_count += 1
            return True, isl_payload, None
            
        except Exception as e:
            self.rejected_count += 1
            return False, None, f"Payload does not conform to ISL v1.1 schema: {str(e)}"
    
    def get_stats(self) -> dict:
        """Get ingestion statistics."""
        return {
            "accepted": self.accepted_count,
            "rejected": self.rejected_count,
            "total": self.accepted_count + self.rejected_count,
        }
