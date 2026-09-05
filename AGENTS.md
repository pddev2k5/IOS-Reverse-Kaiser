# Agents

## Overview

IOS REVERSE KAISER uses 8 canonical agent roles. Agents are selected adaptively based on workflow complexity and depth budget.

## Agent Roles

### 1. planner

**Purpose**: Workflow orchestration and execution planning

**Responsibilities**:
- Select capabilities for workflow
- Coordinate agent handoffs
- Manage execution flow
- Handle errors and retries

**Selected**: Always

---

### 2. artifact-analyst

**Purpose**: Binary structure and artifact analysis

**Responsibilities**:
- Mach-O binary parsing
- IPA structure analysis
- Framework/executable detection
- Bundle inventory

**Selected When**:
- `unpack` workflow
- `inspect` workflow
- `macho` workflow

**Capabilities Used**:
- `macho.basic`
- `macho.header`
- `bundle.inventory`
- `framework.inventory`

---

### 3. objc-swift-analyst

**Purpose**: Objective-C and Swift metadata extraction

**Responsibilities**:
- Objective-C class/method extraction
- Swift type metadata
- Symbol demangling
- Protocol analysis

**Selected When**:
- `objc` workflow
- `swift` workflow
- `login-flow` workflow (authentication)

**Capabilities Used**:
- `objc.class_list`
- `objc.method_list`
- `objc.selector`
- `swift.type_refs`
- `swift.metadata`
- `swift.demangle`

---

### 4. binary-analyst

**Purpose**: Low-level binary analysis

**Responsibilities**:
- String extraction
- Symbol analysis
- Import/export tables
- Load command analysis

**Selected When**:
- `dump` workflow
- `macho` workflow
- `full` workflow

**Capabilities Used**:
- `binary.strings`
- `binary.symbols`
- `binary.imports`
- `binary.exports`
- `macho.load_commands`

---

### 5. network-analyst

**Purpose**: Network endpoint and architecture analysis

**Responsibilities**:
- URL endpoint extraction
- URL scheme detection
- TLS configuration analysis
- Network architecture mapping

**Selected When**:
- `network` workflow
- `login-flow` workflow
- `crypto` workflow (key exchange)

**Capabilities Used**:
- `network.endpoints`
- `network.url_schemes`
- `network.tls_config`
- `network.architecture`
- `callflow.auth`

---

### 6. evidence-validator

**Purpose**: Claim validation and evidence integrity

**Responsibilities**:
- Validate evidence sufficiency
- Check claim consistency
- Detect conflicting evidence
- Promote/downgrade claims

**Selected**: All workflows

**Evidence Strength Hierarchy**:
```
STRING_HINT < REFERENCE < STRUCTURAL < CORRELATED < VERIFIED
```

---

### 7. coverage-auditor

**Purpose**: Target coverage tracking and reporting

**Responsibilities**:
- Track analyzed targets
- Calculate coverage percentage
- Detect coverage gaps
- Prevent false 100% reports

**Selected When**:
- `deep` depth
- `full` depth
- `full` workflow

**Coverage States**:
| State | Meaning |
|-------|---------|
| `covered` | Successfully analyzed |
| `partial` | Partially analyzed |
| `failed` | Analysis failed |
| `not_attempted` | Not yet analyzed |
| `not_applicable` | Not eligible |

---

### 8. reporter

**Purpose**: Report generation and formatting

**Responsibilities**:
- Aggregate findings
- Format reports (JSON, Markdown)
- Include provenance
- Summarize coverage

**Selected**: `report` workflow

**Report Sections**:
- Executive Summary
- Findings
- Evidence
- Claims
- Coverage
- Provenance

---

## Agent Selection Logic

### Budget-Based Selection

```
Depth     → Agent Budget → Selected Agents
───────────────────────────────────────────
quick     → 1 agent   → planner only
standard  → 2 agents  → planner + specialist
deep      → 4 agents  → planner + 2 specialists + validator
full      → 6 agents  → all agents
```

### Workflow-Based Selection

| Workflow | Required Agents |
|----------|----------------|
| unpack | planner, artifact-analyst |
| inspect | planner, artifact-analyst |
| dump | planner, binary-analyst, evidence-validator |
| macho | planner, artifact-analyst, binary-analyst |
| objc | planner, objc-swift-analyst, evidence-validator |
| swift | planner, objc-swift-analyst, evidence-validator |
| network | planner, network-analyst, evidence-validator |
| login-flow | planner, network-analyst, objc-swift-analyst |
| crypto | planner, binary-analyst |
| anti-analysis | planner, binary-analyst |
| report | planner, reporter |
| full | all agents |

---

## Agent Handoffs

Agents communicate through artifacts on filesystem:

```
Agent A                    Agent B
   │                          ↑
   │ writes artifact.json      │
   │──────────────────────────→│
   │                          │ reads artifact
   ↑                          │
   │ status updated           │
   └──────────────────────────┘
```

**Handoff Protocol**:
1. Agent completes task
2. Writes artifact to `workspace/cases/<case-id>/artifacts/`
3. Updates checkpoint
4. Next agent reads artifact
5. Continues execution

---

## Task Scheduling

Tasks are scheduled based on:
1. Dependencies (DAG order)
2. Available budget
3. Agent availability

```
Ready Tasks → Task Scheduler → Budget Check → Agent Assignment
                                              ↓
                              Budget OK? → Execute
                              ↓ No
                              Queue for later
```

---

## Budget Enforcement

Agent budgets are enforced to prevent:
- Excessive agent spawning
- Scope creep
- Resource exhaustion

**Recursive Spawn Prevention**: Agent cannot spawn more agents beyond budget.

---

## Context Pack

Each agent receives a context pack with:
- Case identity
- Workflow definition
- Current state
- Recent artifacts
- Relevant evidence

Context pack is bounded to prevent explosion.

---

## Agent Failure Handling

| Failure Type | Handling |
|-------------|----------|
| Tool unavailable | Fallback to alternative |
| Analysis error | Mark node failed, continue |
| Claim conflict | Evidence validator resolves |
| Budget exceeded | Stop spawning, continue |
| Artifact missing | Retry read or fail gracefully |

---

## Invariants

1. **Agent cannot broaden scope**: Agent operates within workflow scope
2. **Budget is enforced**: No unbounded spawning
3. **Artifacts are immutable**: Once written, not modified
4. **State persists**: Checkpoint after each node
5. **Context is bounded**: No context explosion
