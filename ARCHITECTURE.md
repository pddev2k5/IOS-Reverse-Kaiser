# Architecture

## Overview

IOS REVERSE KAISER follows a layered architecture with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Slash Command Layer                      │
│                   /ios-reverse <target>                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Command Parser Layer                      │
│              Intent + Depth Resolution                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Workflow Registry Layer                    │
│              15 Canonical Workflows (DAGs)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Complexity Scorer                         │
│                  Agent Budget Allocation                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Agent Selector                          │
│              8 Canonical Agent Roles                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Capability Layer                          │
│                  50+ Analysis Operations                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Adapter Layer                            │
│               Tool Adapter Contracts                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Evidence / Provenance                     │
│              Claim / Coverage Tracking                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Case Workspace                            │
│            Checkpoint / Resume / Context                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Report Layer                           │
│                 JSON + Markdown Reports                    │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Slash Command Layer

**Responsibility**: Parse `/ios-reverse` commands

**Components**:
- Command parser
- Intent extractor
- Depth extractor
- Target validator

### 2. Workflow Registry Layer

**Responsibility**: Map intent + depth to execution DAG

**Components**:
- `WorkflowRegistry` - 15 canonical workflows
- `WorkflowValidator` - Scope leakage prevention
- `WorkflowDAG` - Directed acyclic graph of capabilities

**Invariant**: Narrow intent = narrow scope. `network` workflow MUST NOT include `crypto` analysis.

### 3. Capability Layer

**Responsibility**: Single atomic analysis operations

**Components**:
- `Foundation` - Basic file operations
- `BundleInventory` - IPA/framework detection
- `MachOAnalysis` - Binary structure parsing
- `ObjCMetadata` - Objective-C class/method extraction
- `SwiftMetadata` - Swift type extraction
- `NetworkAnalysis` - Endpoint detection
- `CryptoAnalysis` - Primitive identification
- `AntiAnalysis` - Debugger detection
- `CoverageTracking` - Target coverage

**Key Principle**: Capability ≠ Adapter. Capabilities define WHAT to analyze; Adapters define HOW.

### 4. Adapter Layer

**Responsibility**: External tool integration

**Components**:
- `ToolAdapterContract` - Abstract interface
- `SubprocessAdapterContract` - Safe subprocess execution
- `ToolSelector` - Best available tool selection
- `ToolHealthService` - Tool availability tracking

**Fallback Chain**: When `otool` unavailable → `python_parser`

### 5. Evidence/Provenance Layer

**Responsibility**: Traceability and claim validation

**Components**:
- `EvidenceStore` - Immutable evidence records
- `ClaimsStore` - Claim lifecycle management
- `ProvenanceGraph` - Evidence lineage
- `IntegrityChecker` - State validation

**Evidence Hierarchy**:
```
STRING_HINT < REFERENCE < STRUCTURAL < CORRELATED < VERIFIED
```

### 6. Case Workspace Layer

**Responsibility**: State persistence and resume

**Components**:
- `CaseManager` - Case lifecycle
- `CheckpointManager` - Execution snapshots
- `ResumeEngine` - Recovery from interruption
- `ContextPack` - Conversation context generation

**Source of Truth**: Filesystem. Conversation context is cache only.

## Separation: Skill vs Workflow vs Capability vs Agent vs Adapter

| Layer | Definition | Examples |
|-------|-----------|----------|
| **Skill** | When to use, routing contract | `/ios-reverse` |
| **Workflow** | Multi-capability execution plan | `ios.unpack`, `ios.network` |
| **Capability** | Single atomic operation | `bundle.inventory`, `network.analysis` |
| **Agent** | Worker role | `artifact-analyst`, `network-analyst` |
| **Adapter** | External tool wrapper | `otool`, `python_parser` |

## Agent Roles

| Role | Purpose | Selected When |
|------|---------|---------------|
| `planner` | Workflow orchestration | Always |
| `artifact-analyst` | Binary structure | Unpack, inspect |
| `objc-swift-analyst` | Language metadata | ObjC, Swift workflows |
| `binary-analyst` | Low-level analysis | MachO, dump |
| `network-analyst` | Network endpoints | Network, login-flow |
| `evidence-validator` | Claim validation | All workflows |
| `coverage-auditor` | Coverage tracking | Deep, full depth |
| `reporter` | Report generation | Report workflow |

## Data Flow

### Evidence → Claim → Finding

```
1. Tool extracts raw observation
   ↓
2. Capability normalizes to evidence
   ↓
3. Evidence stored (immutable)
   ↓
4. Agent interprets evidence
   ↓
5. Claim created with state
   ↓
6. Validator validates claim
   ↓
7. Coverage tracks target
   ↓
8. Report aggregates findings
```

### Checkpoint → Resume

```
1. Execution in progress
   ↓
2. Checkpoint created (workflow state + artifacts)
   ↓
3. Session interrupted
   ↓
4. New session: /ios-reverse resume <case-id>
   ↓
5. ResumeEngine reads checkpoint
   ↓
6. Validates integrity
   ↓
7. Identifies stale nodes
   ↓
8. Reuses valid completed work
   ↓
9. Continues execution
```

## Key Design Principles

1. **Narrow Scope**: `network` workflow never runs `crypto` analysis
2. **Evidence Integrity**: Claims trace to verifiable evidence
3. **Immutable Raw**: Raw evidence never modified after creation
4. **Checkpoint Persistence**: State survives session termination
5. **Tool Fallback**: Graceful degradation when tools unavailable
6. **Coverage Honesty**: No false 100% coverage reports
7. **Deterministic**: Same inputs produce same outputs
8. **Idempotent**: Re-running doesn't corrupt state

## Technology Stack

| Component | Technology |
|-----------|------------|
| Core | Python 3.11+ |
| Mach-O Parser | Pure Python |
| Testing | pytest |
| Evidence | JSON files |
| Provenance | Dicts + DAG |
| Reports | JSON + Markdown |

## Extensions

### Adding a New Capability

1. Create `ios_reverse/capabilities/new_cap.py`
2. Implement `Capability` abstract base
3. Register in `ios_reverse/capabilities/registry.py`
4. Add to workflow DAG
5. Write tests in `tests/test_capabilities_*.py`

### Adding a New Adapter

1. Create `ios_reverse/adapters/new_tool.py`
2. Implement `ToolAdapterContract`
3. Register in tool selector
4. Add fallback chain
5. Write tests in `tests/test_adapters.py`

### Adding a New Workflow

1. Define DAG in `ios_reverse/workflows/registry.py`
2. Add scope leakage rules to validator
3. Register status (IMPLEMENTED, PARTIAL, BLOCKED)
4. Write tests in `tests/test_workflows.py`
