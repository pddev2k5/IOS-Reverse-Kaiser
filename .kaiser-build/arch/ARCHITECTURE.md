# IOS REVERSE KAISER — Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                     /ios-reverse <intent> [depth]                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         COMMAND ROUTER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Parser    │──│  Resolver   │──│   Scorer    │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│       │                │                │                          │
│       │                │                │                          │
│       ▼                ▼                ▼                          │
│  Intent+Depth    Workflow Select   Orchestration                   │
│     Model         + Capabilities      Tier                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW ENGINE                             │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Workflow Registry                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │  │
│  │  │ unpack  │ │  dump   │ │network  │ │ crypto  │ ...      │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    DAG Executor                             │  │
│  │     PENDING → READY → RUNNING → DONE/SKIPPED/FAILED      │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPABILITY LAYER                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Atomic Capabilities (31 planned)               │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐              │  │
│  │  │ foundation │ │   macho   │ │  binary    │              │  │
│  │  └────────────┘ └────────────┘ └────────────┘              │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐              │  │
│  │  │   objc     │ │   swift   │ │  network   │              │  │
│  │  └────────────┘ └────────────┘ └────────────┘              │  │
│  │  ... 12 domains total ...                                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Tool Adapters                            │  │
│  │  ipsw │ otool │ plutil │ strings │ Ghidra │ IDA │ Frida │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AGENT ORCHESTRATION                           │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│  │ Planner │───▶│ Analyst │───▶│Validator│───▶│ Reporter│        │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘        │
│       │              │              │                             │
│       ▼              ▼              ▼                             │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              Artifact Exchange (Filesystem)              │      │
│  └─────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       PERSISTENCE LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   Cases     │  │  Checkpoints │  │  Evidence   │               │
│  │  workspace  │  │   protocol   │  │  manifest   │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │    Claims   │  │   Provenance │  │   Context   │               │
│  │   registry  │  │    tracking   │  │    packs    │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### Command Router

The entry point that normalizes user input into structured execution plans.

**Components**:
- **Parser**: Extracts intent and options from `/ios-reverse` command
- **Resolver**: Maps intent to canonical workflow
- **Scorer**: Evaluates complexity to select orchestration tier

**Outputs**:
- Normalized intent + depth
- Selected workflow ID
- Orchestration tier (simple/moderate/complex/full)

### Workflow Engine

Executes declarative workflows as directed acyclic graphs (DAGs).

**Components**:
- **Workflow Registry**: Maps intent to workflow definitions
- **DAG Executor**: Runs nodes based on dependencies
- **State Machine**: Tracks node states (PENDING/READY/RUNNING/DONE/SKIPPED/FAILED)

**Key Properties**:
- Deterministic execution order
- Skip DONE nodes unless invalidated
- Checkpoint after each node
- Full coverage auditing for deep/full modes

### Capability Layer

Atomic, independently callable operations that form the building blocks.

**Properties**:
- Each capability emits structured output
- Each capability records provenance
- Each capability returns explicit success/failure
- Capabilities do not broaden scope

**Domains**:
1. Foundation (artifact detection, IPA handling, bundle analysis)
2. Mach-O Analysis (structure, slices, load commands)
3. Binary Analysis (imports, exports, symbols, strings)
4. Metadata (ObjC, Swift)
5. Framework/Dylib/Extension
6. Architecture Discovery
7. Network Analysis
8. Callflow Reconstruction
9. Crypto Identification
10. Anti-Analysis Detection
11. Runtime Abstraction
12. Reporting

### Tool Adapters

Abstract external tools behind capability interfaces.

**Tool Stack**:
- ipsw (class-dump, Mach-O analysis)
- otool (linked libraries, symbols)
- plutil (Info.plist parsing)
- codesign (entitlements extraction)
- strings (string extraction)
- nm (symbol extraction)
- Ghidra headless (decompilation, xrefs)
- IDA Pro MCP (advanced analysis)
- Frida (runtime instrumentation)

**Adapter Properties**:
- Conditional escalation (lightest sufficient tool)
- Abstract interfaces
- Version checking

### Agent Orchestration

Adaptive multi-agent system based on workflow complexity.

**Roles**:
- **planner**: Creates execution plans
- **artifact-analyst**: Analyzes extracted artifacts
- **objc-swift-analyst**: Focuses on metadata
- **binary-analyst**: Analyzes binary structure
- **network-analyst**: Analyzes network patterns
- **evidence-validator**: Validates claims against evidence
- **coverage-auditor**: Audits full/deep coverage
- **reporter**: Generates reports

**Orchestration Tiers**:
- **simple**: Single executor
- **moderate**: Executor + validator
- **complex**: Planner + specialists + validator
- **full**: Planner + specialists + validator + coverage-auditor + reporter

**Agent Exchange Protocol**:
- Artifact-based handoffs (filesystem)
- No long conversational handoffs
- No uncontrolled recursive loops

### Persistence Layer

Filesystem-based state management for resumability.

**Components**:
- **Case Workspace**: Per-task persistent workspace
- **Checkpoint Protocol**: Machine-readable state snapshots
- **Evidence Manifest**: SHA-256 verified artifacts
- **Claims Registry**: Machine-readable claims with evidence refs
- **Provenance Tracking**: Complete artifact lineage
- **Context Packs**: Compressed context for resume

---

## Data Flows

### Intent Processing Flow

```
User Input
    │
    ▼
Parser (extract intent, options)
    │
    ▼
Resolver (normalize aliases)
    │
    ▼
Depth Resolver (quick/standard/deep/full)
    │
    ▼
Complexity Scorer (evaluate scope)
    │
    ▼
Workflow Registry (select workflow)
    │
    ▼
DAG Definition (nodes + edges)
    │
    ▼
Orchestration Tier (select agents)
    │
    ▼
Execution
```

### Evidence Flow

```
Capability Execution
    │
    ▼
Structured Output
    │
    ▼
SHA-256 Computation
    │
    ▼
Evidence Manifest Entry
    │
    ▼
Claim Creation (if applicable)
    │
    ▼
Coverage Audit (if deep/full)
    │
    ▼
Checkpoint
```

---

## Quality Properties

1. **Deterministic**: Same input → same output, every time
2. **Resumable**: Checkpoint-based continuation from any state
3. **Auditable**: Every claim has evidence references
4. **Scalable**: Single → multi agent based on complexity
5. **Testable**: Semantic tests for routing, resume, coverage
6. **Minimal**: Narrow requests → narrow execution

---

## Non-Goals (Explicitly Excluded)

- Windows PE reverse engineering
- Android reverse engineering
- Web attack capabilities
- DRM bypass
- Credential extraction
- Real service probing

---

## Version

| Field | Value |
|-------|-------|
| Version | 0.0.2 |
| Phase | P02 |
| Status | ARCHITECTURE FROZEN |

---

*This document defines the complete system architecture for IOS REVERSE KAISER.*
