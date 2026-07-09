"""
Example usage of ISL v1.1 and Constitutional Node v1.0 implementation.

This script demonstrates how to create ISL payloads and process them
through a Constitutional Node.
"""

from isl.payload import (
    ISLPayload,
    IntentClass,
    TargetScope,
    DirectiveBody,
    RollbackPolicy,
)
from isl.signature import SignatureScheme, create_signature
from cnode.constitutional_node import ConstitutionalNode


def main():
    """Demonstrate ISL payload creation and C-Node processing."""
    
    # Generate a key pair for the agent
    private_key, public_key = SignatureScheme.generate_key_pair()
    
    # Create an ISL payload
    payload = ISLPayload(
        intent_class=IntentClass.DIRECTIVE,
        issuing_agent_id="agent-001",
        target_scope=TargetScope.SUBSYSTEM,
        target_id="subsystem-A",
        intent_body={
            "action": "deploy",
            "target_resource": "service-X",
            "parameters": {"version": "1.0.0", "region": "us-east-1"},
            "rollback_policy": "immediate-rollback",
        },
        constitutional_flags=["CC-001", "OC-001"],
        evidence_refs=[],  # No evidence references for this example
        priority="routine",
    )
    
    # Sign the payload
    canonical_serialization = payload.get_canonical_serialization()
    signature = create_signature(canonical_serialization, private_key)
    payload.issuer_signature = signature
    
    print(f"Created ISL payload: {payload.intent_id}")
    print(f"Intent class: {payload.intent_class}")
    print(f"Target scope: {payload.target_scope}")
    print(f"Signature: {signature[:32]}...")
    
    # Initialize a Constitutional Node
    agent_registry = {
        "agent-001": public_key,
    }
    
    constraint_registry = {
        "CC-001": "No agent may bypass constitutional constraints",
        "OC-001": "Resource allocation requires approval",
    }
    
    cnode = ConstitutionalNode(
        node_id="cnode-001",
        agent_registry=agent_registry,
        constraint_registry=constraint_registry,
    )
    
    # Process the payload through the C-Node
    print("\n--- Processing through Constitutional Node ---")
    result = cnode.process_intent(payload.model_dump())
    
    print(f"\nDisposition: {result['disposition']}")
    print(f"Intent ID: {result['intent_id']}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    print("\n--- Stage Results ---")
    for stage_name, stage_result in result["stages"].items():
        print(f"{stage_name}: {stage_result}")
    
    print("\n--- Ledger Statistics ---")
    ledger_stats = cnode.get_ledger_stats()
    print(f"Total entries: {ledger_stats['total_entries']}")
    print(f"Event counts: {ledger_stats['event_counts']}")
    print(f"Chain integrity valid: {ledger_stats['chain_integrity_valid']}")
    
    print("\n--- Intent Layer Statistics ---")
    intent_stats = cnode.get_intent_layer_stats()
    print(f"Accepted: {intent_stats['accepted']}")
    print(f"Rejected: {intent_stats['rejected']}")
    
    print("\n--- Ledger Integrity Verification ---")
    is_valid, error = cnode.verify_ledger_integrity()
    print(f"Chain integrity: {'VALID' if is_valid else 'INVALID'}")
    if error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
