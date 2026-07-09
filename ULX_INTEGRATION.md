# ULX Integration with ISL/CNode

This document describes the comprehensive integration between ULX (Universa Language) and the ISL v1.1 / Constitutional Node v1.0 specifications within the CIEMS framework.

## Overview

ULX is a governed programming language designed for constitutional intelligent systems. It integrates with the Intent Specification Language (ISL) and Constitutional Node (CNode) to provide a unified development environment for building governed, compliant systems.

### Key Integration Points

- **Constitutional Constraints**: ULX's `@constitution` with `@article` invariants define CNode constraints
- **Authority Levels**: ULX's pure/lawful/reactive/sovereign maps to CNode's governance hierarchy
- **Audit Integration**: ULX's audit trail merges with CNode's cryptographically chained ledger
- **Trust System**: ULX's Trust entities work with ISL's agent registry
- **Signal System**: ULX's reactive signals enable real-time governance monitoring

## Architecture

```
ULX + ISL/CNode Integrated System
├── ULX Language Layer
│   ├── Constitution/Articles (Governance Rules)
│   ├── Modules (Code Organization)
│   ├── Authority Levels (pure/lawful/reactive/sovereign)
│   ├── Trust System (Entity Trust Management)
│   └── Signal System (Reactive Governance)
│
├── ISL v1.1 Layer
│   ├── Payload Schema (Intent Specification)
│   ├── Validation Pipeline (Intent Validation)
│   ├── Signature Scheme (Ed25519 Cryptography)
│   ├── Multi-Agent Composition (Collaborative Intents)
│   └── Cross-Org Governance (Federation Support)
│
└── Constitutional Node v1.0
    ├── Intent Layer (Ingestion Boundary)
    ├── ISL Interpreter (Parsing & Validation)
    ├── Constraint Engine (Enforcement Core)
    ├── Evidence Layer (Provenance Management)
    └── Audit Ledger (Cryptographic Chaining)
```

## ULX Language Features

### Constitution and Articles

ULX allows defining constitutional constraints that map to CNode constraints:

```ulx
@constitution {
  @article BASIC {
    always: output.valid == true;
  }
  
  @article RESOURCE_MANAGEMENT {
    enforce: resource_allocation <= max_threshold;
  }
}
```

These articles are automatically converted to CNode constraint registry entries.

### Authority Levels

ULX provides four authority levels that map to governance priorities:

- **pure**: Immutable, no side effects (highest trust)
- **lawful**: Governed operations with constitutional compliance
- **reactive**: Event-driven with signal-based governance
- **sovereign**: Autonomous operations with full authority

```ulx
module Core [lawful] {
  fn process() -> Governed<Str, lawful> {
    // Operations must comply with constitution
  }
}

module Monitor [reactive] {
  @signal alert_threshold_exceeded
  fn monitor() {
    // Reactive governance
  }
}
```

### Trust System

ULX's Trust entities integrate with ISL's agent registry:

```ulx
module TrustCore [sovereign] {
  fn register_agent(agent_id: Str, trust_level: Trust) {
    anchor: agent_id;
    // Maps to ISL agent registry
  }
}
```

### Signal System

Reactive signals enable real-time governance monitoring:

```ulx
module GovernanceMonitor [reactive] {
  @signal constraint_violation
  @signal audit_event_logged
  
  fn monitor_governance() {
    observe: audit_trail;
    when: violation_detected {
      emit constraint_violation;
    }
  }
}
```

## IDE Integration

The desktop IDE provides a unified development environment:

### Multi-Tab Editor

- **ULX Constitution Tab**: Edit ULX code with syntax highlighting
- **ISL Payload Tab**: Edit ISL JSON payloads with validation
- **Output Tab**: View runtime output and compilation results
- **Audit Trail Tab**: Monitor governance events in real-time
- **Governance Tab**: View constraint evaluation and system status

### Runtime Integration

The IDE embeds both ULX interpreter and ISL/CNode libraries:

```python
import ulx
from isl.payload import ISLPayload
from cnode.constitutional_node import ConstitutionalNode

# ULX Runtime
program = ulx.parse(source)
interp = ulx.Interpreter()
interp.load_program(program)
result = interp.run_function("module::main")

# ISL/CNode Runtime
payload = ISLPayload(**payload_json)
cnode = ConstitutionalNode(...)
result = cnode.process_intent(payload.model_dump())
```

### Syntax Highlighting

Custom ULX syntax highlighting with:
- Keywords (always, enforce, bind, emit, etc.)
- Types (Lawful, Governed, Signal, Trust)
- Annotations (@constitution, @article, @signal)
- Strings, comments, numbers

## Integration Workflow

### 1. Define ULX Constitution

```ulx
@constitution {
  @article SAFETY {
    always: operation.safe == true;
  }
}

module Deployment [lawful] {
  fn deploy_service(service: Str) -> Governed<Bool, lawful> {
    bind config: Lawful<Str> = load_config(service);
    enforce: config.valid == true;
    emit DEPLOYMENT_INITIATED: service;
    return true;
  }
}
```

### 2. Compile ULX to Bytecode

The IDE compiles ULX to `.ulxb` bytecode format for execution.

### 3. Create ISL Payload

```json
{
  "intent_class": "directive",
  "issuing_agent_id": "agent-001",
  "target_scope": "subsystem",
  "target_id": "subsystem-A",
  "intent_body": {
    "action": "deploy",
    "target_resource": "service-X"
  },
  "constitutional_flags": ["SAFETY"],
  "priority": "routine"
}
```

### 4. Process Through Constitutional Node

The ISL payload is processed through the 5-layer CNode architecture:
1. Intent Layer: Ingestion and schema validation
2. ISL Interpreter: Parsing and context generation
3. Constraint Engine: Enforcement of ULX-defined constraints
4. Evidence Layer: Provenance and anchor verification
5. Audit Ledger: Cryptographic event recording

### 5. Monitor Results

View disposition, constraint evaluations, and audit events in the IDE dashboard.

## Mapping Between Systems

### ULX to ISL Mapping

| ULX Concept | ISL Equivalent |
|-------------|----------------|
| @constitution | constitutional_flags |
| @article | constraint_registry entries |
| lawful/reactive/sovereign | governance priority |
| Trust entities | agent_registry |
| emit signals | intent_body actions |

### ULX to CNode Mapping

| ULX Concept | CNode Equivalent |
|-------------|------------------|
| @constitution articles | Constraint Engine rules |
| Authority levels | Governance priority hierarchy |
| Audit trail | Audit Ledger entries |
| enforce statements | Constraint evaluations |
| bind operations | Evidence context |

## Usage Examples

### Example 1: Simple Governed Operation

```ulx
@constitution {
  @article VALIDATION {
    always: input.valid == true;
  }
}

module Validator [lawful] {
  fn validate(data: Str) -> Governed<Bool, lawful> {
    bind parsed: Lawful<Data> = parse(data);
    enforce: parsed.valid == true;
    emit VALIDATION_COMPLETE: parsed;
    return true;
  }
}
```

### Example 2: Reactive Governance

```ulx
module Monitor [reactive] {
  @signal threshold_exceeded
  @signal resource_depleted
  
  fn monitor_resources() {
    observe: resource_pool;
    when: resource_pool.level < threshold {
      emit threshold_exceeded;
      enforce: trigger_allocation_policy();
    }
  }
}
```

### Example 3: Multi-Agent Composition

```ulx
module Coordinator [sovereign] {
  fn coordinate_agents(agents: List<Agent>) -> Governed<Bool, sovereign> {
    bind quorum: Lawful<Int> = calculate_quorum(agents);
    anchor: quorum;
    
    for agent in agents {
      emit AGENT_REQUEST: agent.id;
    }
    
    when: responses_received >= quorum {
      emit QUORUM_REACHED;
      return true;
    }
  }
}
```

## ULX Language Specification

### Keywords

ULX reserves the following keywords:
- always, anchor, any, article, assert, bind, bool
- constitution, declare, emit, enforce, float, fn
- governed, int, lawful, let, match, module, never
- observe, pure, reactive, return, signal, sovereign
- str, then, trust, type, void, when, with
- rollback, if, else, true, false

### Types

- **Base types**: bool, int, float, str, void, any
- **Governed types**: Governed<T, AuthLevel>
- **Lawful types**: Lawful<T>
- **Signal types**: Signal<T>
- **Trust types**: Trust<T>

### Operators

- Arithmetic: +, -, *, /, %
- Comparison: ==, !=, >, <, >=, <=
- Logical: &&, ||, !
- Assignment: =
- Pipe: |>
- Scope resolution: ::

### Statements

- bind: Type-safe variable binding
- enforce: Runtime constraint enforcement
- anchor: Create rollback checkpoint
- rollback: Rollback to last anchor
- emit: Emit signal
- return: Return from function
- if/else: Conditional branching
- match: Pattern matching

## Bytecode Format

ULX compiles to `.ulxb` bytecode format (JSON-based, tagged "ULXB-JSON-v1"):

```json
{
  "format": "ULXB-JSON-v1",
  "constants": [...],
  "functions": {
    "module::function": {
      "params": ["param1", "param2"],
      "code": [...],
      "authority": "lawful"
    }
  },
  "constitution": {...}
}
```

## Runtime Components

### Invariant Engine

The invariant engine continuously evaluates constitutional invariants:
- **always**: Must always evaluate to true
- **never**: Must never evaluate to true
- **when-then**: Conditional response to triggers

### Signal Bus

Manages reactive signal propagation:
- Signal registration
- Observer pattern implementation
- Value propagation

### Anchor Store

Provides rollback capabilities:
- Snapshot creation
- Hash-based integrity
- Stack-based checkpoint management

### Audit Trail

Merges with CNode audit ledger:
- Event logging
- Governance violation tracking
- Cryptographic chaining

## Installation

```bash
cd ide
pip install -r requirements.txt
```

## Running the IDE

```bash
python main.py
```

## Dependencies

- PyQt6 - Desktop GUI framework
- PyQt6-WebEngine - Web components
- ulx.py - ULX language interpreter
- isl/ - ISL v1.1 implementation
- cnode/ - Constitutional Node v1.0 implementation
- pydantic - Data validation
- cryptography - Ed25519 signatures

## Specification Compliance

### ULX-SPEC-0001 v0.2

The implementation follows ULX-SPEC-0001 v0.2 with ratified decisions:
- Member access syntax
- Record literals
- Rollback statement
- .ulxb JSON format
- Arithmetic operators

### ISL v1.1 (CIEMS-ISL-0011)

- Intent payload schema
- Validation pipeline
- Signature scheme
- Multi-agent composition
- Cross-organization governance

### Constitutional Node v1.0 (CIEMS-CNODE-SPEC-001)

- Five-layer architecture
- Constraint engine
- Audit ledger
- Evidence layer

## Advanced IDE Features

### 1. Governance Timeline Visualization

A visual timeline view showing the complete governance execution path through all CNode layers.

**Timeline View Component**

```python
class TimelineView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events = []
        self.setMinimumHeight(200)

    def update_timeline(self, timeline: list[GovernanceTimelineEvent]):
        self.events = timeline
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw timeline with stages, execution times, and status indicators
```

**Governance Profiler View**

```python
class GovernanceProfilerView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Stage", "Exec Time (ms)", "Invariant Count", 
            "Evidence Count", "Evidence Weight"
        ])

    def update_profile(self, timeline: list[GovernanceTimelineEvent]):
        self.setRowCount(0)
        for ev in timeline:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(ev.stage))
            self.setItem(row, 1, QTableWidgetItem(f"{ev.exec_time * 1000:.2f}"))
            self.setItem(row, 2, QTableWidgetItem(str(ev.invariant_count)))
            self.setItem(row, 3, QTableWidgetItem(str(ev.evidence_count)))
            self.setItem(row, 4, QTableWidgetItem(str(ev.evidence_weight)))
```

**Integration with Debugger**

```python
timeline = debugger.run(payload.model_dump())
self.profiler_view.update_profile(timeline)
```

### 2. Constitutional Replay File Format (.cnode-trace)

Save and replay full governance runs for debugging and analysis.

**Trace Schema**

```python
trace = {
    "version": "1.0",
    "intent_id": result["intent_id"],
    "timestamp": time.time(),
    "timeline": [
        {
            "stage": ev.stage,
            "result": ev.result,
            "exec_time": ev.exec_time,
            "invariants": ev.invariants,
            "evidence": ev.evidence,
            "state_delta": ev.state_delta,
            "ledger_entry": ev.ledger_entry,
        }
        for ev in timeline
    ]
}
```

**Save/Load Functions**

```python
def save_trace(path: str, trace: dict):
    with open(path, "w") as f:
        json.dump(trace, f, indent=2)

def load_trace(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)
```

**IDE Menu Integration**

- File → Export Governance Trace (.cnode-trace)
- File → Load Governance Trace

On load, feed timeline into:
- TimelineView.update_timeline(...)
- GovernanceProfilerView.update_profile(...)
- AnimatedTimeline.set_timeline(...)

### 3. Multi-Agent Intent Battlefield Simulator

A StarCraft-inspired simulator for visualizing multi-agent governance conflicts.

**Core Model**

```python
@dataclass
class Agent:
    agent_id: str
    faction: str
    strategy: str  # "aggressive", "defensive", "macro"

@dataclass
class BattlefieldIntent:
    agent_id: str
    payload: dict
    timestamp: float
```

**Simulator**

```python
class IntentBattlefieldSimulator:
    def __init__(self, cnode_network: CNodeNetworkSimulator, agents: list[Agent]):
        self.network = cnode_network
        self.agents = {a.agent_id: a}
        self.events = []

    def issue_intent(self, agent_id: str, payload: dict):
        ts = time.time()
        visited = self.network.route_intent(payload, entry_node_id="cnode-001")
        self.events.append({
            "agent_id": agent_id,
            "payload": payload,
            "timestamp": ts,
            "path": visited,
        })

    def run_scenario(self, scenario_script: list[dict]):
        for step in scenario_script:
            self.issue_intent(step["agent_id"], step["payload"])
```

**Battlefield UI (StarCraft-style)**

New tab: "Battlefield"

Components:
- Map view: nodes as bases, intents as projectiles (lines/arrows)
- Agent panel: list of agents, faction colors
- Event log: per-intent path, disposition, violations

```python
class BattlefieldView(QWidget):
    def set_events(self, events):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw nodes, agents, arrows for intents
```

**Scenario Examples**

- Two factions competing for resource allocation intents
- One "rogue" agent trying to bypass constraints
- CIEMS-driven commercial conflict (multiple agents chasing same deal)

### 4. Real-Time Tick-Based Battlefield Loop

A governed simulation loop that updates every N milliseconds.

**Core Loop**

```python
class BattlefieldLoop:
    def __init__(self, simulator, tick_rate_ms=250):
        self.simulator = simulator
        self.tick_rate_ms = tick_rate_ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

    def start(self):
        self.timer.start(self.tick_rate_ms)

    def stop(self):
        self.timer.stop()

    def tick(self):
        self.simulator.update()  # agents act, intents fire, governance runs
```

**Simulator Update Cycle**

```python
class IntentBattlefieldSimulator:
    def __init__(self, agents, cnode_network):
        self.agents = agents
        self.network = cnode_network
        self.events = []
        self.tick_count = 0

    def update(self):
        self.tick_count += 1

        for agent in self.agents.values():
            intent = agent.strategy.decide(self.tick_count)
            if intent:
                visited = self.network.route_intent(intent, entry_node_id="cnode-001")
                self.events.append({
                    "agent_id": agent.agent_id,
                    "intent": intent,
                    "path": visited,
                    "tick": self.tick_count
                })
```

### 5. Agent AI Strategies

Agents choose intents based on StarCraft-style strategy patterns.

**Strategy Interface**

```python
class AgentStrategy:
    def decide(self, tick):
        raise NotImplementedError
```

**Rush Strategy (Early Aggression)**

```python
class RushStrategy(AgentStrategy):
    def decide(self, tick):
        if tick % 3 == 0:
            return {"action": "capture", "resource": "node-A"}
```

**Turtle Strategy (Defensive, Governance-Safe)**

```python
class TurtleStrategy(AgentStrategy):
    def decide(self, tick):
        if tick % 10 == 0:
            return {"action": "fortify", "resource": "node-home"}
```

**Macro Strategy (Economic Scaling, CIEMS-Driven)**

```python
class MacroStrategy(AgentStrategy):
    def decide(self, tick):
        if tick % 5 == 0:
            return {"action": "deal-progress", "deal_id": f"deal-{tick//5}"}
```

**Agent Model**

```python
class Agent:
    def __init__(self, agent_id, faction, strategy):
        self.agent_id = agent_id
        self.faction = faction
        self.strategy = strategy
        self.elo = 1000
```

### 6. Governance ELO Rating

Agents gain or lose rating based on constitutional outcomes.

**ELO Update Rules**

- Accepted intent → +K
- Constrained intent → −K
- Invariant violation → −2K
- High evidence weight → +small bonus
- High invariant density → −small penalty

**Implementation**

```python
class GovernanceELO:
    def __init__(self, K=16):
        self.K = K

    def update(self, agent, stage_result):
        if stage_result.get("accepted"):
            agent.elo += self.K
        else:
            agent.elo -= self.K

        for inv in stage_result.get("invariant_events", []):
            if inv.get("status") == "violated":
                agent.elo -= 2 * self.K

        evidence_weight = sum(ev.get("weight", 1) for ev in stage_result.get("evidence", []))
        agent.elo += int(evidence_weight * 0.5)
```

**Battlefield Integration**

```python
for node_id, result in visited:
    elo.update(agent, result)
```

### Complete Battlefield Features

The battlefield simulator provides:
- Real-time tick loop for governed simulation
- Agents with StarCraft-style strategies (Rush, Turtle, Macro)
- Governance-aware ELO scoring system
- Multi-node CNode routing
- Evidence, invariants, constraints, and CIEMS integration
- Visual representation of governance conflicts

## Future Enhancements

Potential enhancements for production deployment:
1. **Static Type Checking**: Full type checking at module/constitution boundaries
2. **Persistence**: Database backing for audit ledger and registries
3. **Networking**: Inter-node protocol for federation
4. **Performance**: Caching and optimization for high-throughput scenarios
5. **Security**: Key rotation, certificate management, secure key storage
6. **Monitoring**: Metrics, logging, and observability
7. **Testing**: Expanded test coverage with integration tests
8. **Binary Bytecode**: Binary .ulxb encoding for performance
9. **Advanced Visualization**: 3D battlefield view with real-time intent propagation
10. **AI Strategy Learning**: Machine learning for agent strategy optimization
