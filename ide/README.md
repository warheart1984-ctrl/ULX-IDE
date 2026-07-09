# ULX + ISL/CNode Integrated Desktop IDE

A professional desktop development environment for governed systems, integrating ULX Universa with the ISL v1.1 and Constitutional Node v1.0 specifications, plus AI Factory, CRK-2 governance verification, and Nova Studio lineage visualization.

## Features

- **Multi-Tab Editor**: Separate editors for ULX constitution/modules, ISL payloads, and AI Factory build specs
- **Syntax Highlighting**: Custom syntax highlighting for ULX and JSON/ISL formats
- **Integrated Runtime**: Direct Python embedding of ULX interpreter + ISL/CNode libraries
- **Governance Dashboard**: Real-time view of:
  - ULX invariant violations
  - CNode constraint evaluations
  - Audit ledger (merged from both systems)
- **Audit Trail**: Live monitoring of governance events
- **Bytecode Compilation**: Compile ULX to .ulxb bytecode format
- **ISL Payload Processing**: Process ISL intents through Constitutional Node
- **AI Factory Integration**: Validate and build governed AI systems using AI Factory spec
- **CRK-2 Governance Verification**: Verify constitutional compliance across runtime events using dLAP checks
- **Constitutional Node Test Harness**: Simulate payloads and governance decisions to validate constitutional logic
- **Arena Replay Validation**: Validate ULX→ISL transitions with evidence-based promotion
- **Nova Studio Lineage Sync**: Export audit outputs for lineage visualization in Nova Studio
- **Promotion v1.0 Constitutional Elevation Protocol**: Transform substrations into stable substrates through evidence, replay, governance review, and lineage certification

## Installation

```bash
cd ide
pip install -r requirements.txt
```

## Usage

Run the IDE:

```bash
python main.py
```

### ULX Editor

1. Write ULX code in the "ULX Source" tab
2. Click "Run" to execute
3. Click "Compile" to generate bytecode
4. View output and audit events in the right panel

### ISL Payload Editor

1. Edit ISL payload JSON in the "ISL Payload" tab
2. Click "Validate ISL" to parse and validate
3. View validation results in the "ISL Check" tab

### AI Factory Editor

1. Edit AI Factory build spec JSON in the "AI Factory Spec" tab
2. Click "AI Factory Build" to validate the spec
3. View validation results in the "Output" tab

### CRK-2 Governance Verification

1. Run ULX code to generate audit trail
2. Click "CRK-2 Verify" to check constitutional compliance
3. View invariant violations and governance status in "CRK-2 Governance" tab

### Constitutional Node Test Harness

1. Edit ISL payload with test data
2. Click "CNode Test" to run governance tests
3. View test results in "CNode Harness" tab

### Arena Replay Validation

1. Run ULX code to emit signals
2. Edit ISL payload with corresponding intent
3. Click "Arena Replay" to validate ULX→ISL transition
4. View evidence chain and promotion status in "Arena Replay" tab

### Nova Studio Lineage Sync

1. Run any ULX code to generate audit events
2. Click "Nova Sync" to export lineage data
3. View lineage graph in "Nova Lineage" tab
4. Export data for Nova Studio visualization

## Architecture

```
IDE Main Window
├── ULX Source Editor (with syntax highlighting)
├── ISL Payload Editor (JSON)
├── AI Factory Spec Editor (JSON)
├── Runtime Engine
│   ├── ULX Interpreter
│   ├── ISL Validator
│   ├── CNode Processor
│   ├── AI Factory Validator
│   ├── CRK-2 dLAP Engine
│   └── Arena Replay Validator
├── Output Console
├── Bytecode View
├── Audit Trail
├── Runtime State
├── Signal Monitor
├── ISL Check
├── CRK-2 Governance
├── CNode Harness
├── Arena Replay
└── Nova Lineage
```

## Integration Points

- **Constitutional Constraints**: ULX's `@constitution` with `@article` invariants define CNode constraints
- **Authority Levels**: ULX's pure/lawful/reactive/sovereign maps to CNode's governance hierarchy
- **Audit Integration**: ULX's audit trail merges with CNode's cryptographically chained ledger
- **Trust System**: ULX's Trust entities work with ISL's agent registry
- **Signal System**: ULX's reactive signals enable real-time governance monitoring
- **AI Factory**: Governed AI build specs integrate with ULX constitution for AI system governance
- **CRK-2**: dLAP checks verify constitutional compliance across runtime events
- **Arena**: Evidence-based promotion validates ULX→ISL transitions
- **Nova Studio**: Lineage data export for visualization of governance chains

## Dependencies

- PyQt6 - Desktop GUI framework
- PyQt6-WebEngine - Web components (for future features)
- ulx.py - ULX language interpreter
- isl/ - ISL v1.1 implementation
- cnode/ - Constitutional Node v1.0 implementation
- ai_factory/ - Governed AI build system (optional)
- crk2/ - CRK-2 governance kernel (optional, via bridge)

## Project Sources

- ULX: E:\ulx\ulx.py
- AI Factory: E:\ai_factory\
- CRK-2: E:\agentic-coding-agent\crk2\
- ISL/CNode: Current project directory
