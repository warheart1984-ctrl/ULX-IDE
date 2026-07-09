# ISL v1.1 and Constitutional Node v1.0 Implementation

This project implements the Intent Specification Language (ISL) v1.1 and Constitutional Node (C-Node) v1.0 specifications for the Constitutional Intelligent Engineering Management System (CIEMS).

## Specifications Implemented

- **ISL v1.1** (CIEMS-ISL-0011): Intent Specification Language with Multi-Agent Composition, Federated Evidence, and Cross-Organization Governance
- **Constitutional Node v1.0** (CIEMS-CNODE-SPEC-001): ISL-Integrated Governance Specification

## Architecture

### ISL v1.1 Components
- `isl/` - ISL payload schema and validation
- `isl/payload.py` - Core payload data structures
- `isl/validation.py` - Validation pipeline
- `isl/signature.py` - Cryptographic signature handling
- `isl/composition.py` - Multi-agent intent composition
- `isl/evidence.py` - Federated evidence anchoring
- `isl/cross_org.py` - Cross-organization governance

### Constitutional Node v1.0 Components
- `cnode/` - Constitutional Node implementation
- `cnode/layers/` - Five-layer architecture
  - `intent_layer.py` - Intent ingestion boundary
  - `isl_interpreter.py` - ISL parsing and validation
  - `constraint_engine.py` - Constraint enforcement
  - `evidence_layer.py` - Evidence provenance management
  - `audit_ledger.py` - Append-only cryptographically chained ledger
- `cnode/constraints/` - Constraint definitions
- `cnode/registry.py` - Agent and organization registries

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from isl.payload import ISLPayload
from cnode.constitutional_node import ConstitutionalNode

# Create an ISL payload
payload = ISLPayload(
    intent_class="directive",
    issuing_agent_id="agent-001",
    target_scope="subsystem",
    intent_body={"action": "deploy", "target_resource": "service-A"}
)

# Process through Constitutional Node
cnode = ConstitutionalNode()
result = cnode.process_intent(payload)
```

## Status

- [x] ISL v1.1 payload schema
- [x] ISL validation pipeline
- [x] Constitutional Node 5-layer architecture
- [ ] Multi-agent composition lifecycle
- [ ] Federated evidence verification
- [ ] Cross-organization governance
- [ ] Inter-node protocol
