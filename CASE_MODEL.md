# Case Model

## Overview

Cases are the fundamental unit of analysis in IOS REVERSE KAISER. Each case represents a single target analysis session with full state persistence.

## Case Directory Structure

```
workspace/cases/<case-id>/
├── manifest.json           # Case identity
├── CASE.md               # Case metadata
├── STATUS.md             # Current execution status
├── PLAN.md              # Execution plan
├── NEXT.md              # Next action
├── DECISIONS.md         # Architectural decisions
├── FAILURES.md          # Failure log
│
├── phases/              # Phase documentation
├── endpoints/           # Execution endpoints
├── functions/           # Function documentation
├── callflows/           # Callflow documentation
│
├── claims/              # Analytical claims
│   └── *.json          # Claim records
│
├── evidence/            # Evidence store
│   ├── raw/            # Immutable raw evidence
│   │   └── *.json      # Raw observation records
│   └── derived/        # Derived evidence
│       └── *.json      # Processed evidence
│
├── network/             # Network analysis
│   └── endpoints/      # Endpoint data
│
├── artifacts/           # Derived artifacts
│   ├── unpacked/      # Unpacked IPA contents
│   ├── macho/         # Mach-O binary data
│   └── *.json         # Structured analysis data
│
├── logs/               # Execution logs
│   └── *.log
│
├── checkpoints/        # Execution snapshots
│   ├── latest.json     # Latest checkpoint pointer
│   └── checkpoint-*.json
│
├── agents/             # Agent state
│   └── *.json
│
├── .lock               # Case lock file
└── .context/          # Cached context pack
```

## Key Files

### manifest.json

Case identity and configuration:

```json
{
  "case_id": "case-20240904-a1b2c3",
  "created_at": "2024-09-04T10:00:00Z",
  "target": {
    "name": "App.ipa",
    "path": "/path/to/App.ipa",
    "size": 1048576,
    "hash": "sha256:..."
  },
  "intent": "network",
  "depth": "standard",
  "status": "in_progress",
  "version": "0.1.0"
}
```

### STATUS.md

Human-readable execution status:

```markdown
# Case: App.ipa

## Status
**In Progress** - Last updated: 2024-09-04 10:30:00

## Workflow
- ios.network (depth: standard)
- Progress: 3/8 nodes completed

## Current Node
- network.endpoints (running)

## Completed
- [x] bundle.unpack
- [x] bundle.inventory
- [x] network.endpoints

## Pending
- [ ] network.tls_config
- [ ] network.url_schemes
```

### checkpoints/latest.json

Latest checkpoint pointer:

```json
{
  "checkpoint_id": "checkpoint-20240904-003",
  "created_at": "2024-09-04T10:35:00Z",
  "workflow_state": {
    "completed_nodes": ["bundle.unpack", "bundle.inventory"],
    "pending_nodes": ["network.tls_config"],
    "current_node": "network.endpoints"
  }
}
```

## Checkpoint Format

Checkpoints capture complete execution state:

```json
{
  "checkpoint_id": "checkpoint-20240904-003",
  "case_id": "case-20240904-a1b2c3",
  "created_at": "2024-09-04T10:35:00Z",
  "workflow_state": {
    "workflow_id": "ios.network",
    "depth": "standard",
    "nodes": {
      "bundle.unpack": {
        "status": "completed",
        "artifacts": ["artifacts/unpacked"],
        "completed_at": "2024-09-04T10:15:00Z"
      },
      "network.endpoints": {
        "status": "completed",
        "artifacts": ["artifacts/endpoints.json"],
        "completed_at": "2024-09-04T10:30:00Z"
      },
      "network.tls_config": {
        "status": "pending",
        "dependencies_met": false
      }
    },
    "completed_nodes": ["bundle.unpack", "network.endpoints"],
    "failed_nodes": [],
    "pending_nodes": ["network.tls_config", "network.url_schemes"]
  },
  "evidence": [
    "evidence/raw/ev-001.json",
    "evidence/raw/ev-002.json"
  ],
  "claims": [
    "claims/claim-001.json"
  ]
}
```

## Evidence Structure

### Raw Evidence (Immutable)

```json
{
  "evidence_id": "ev-20240904-001",
  "case_id": "case-20240904-a1b2c3",
  "type": "raw",
  "strength": "structural",
  "source_artifact": "App.app/Frameworks/LoginSDK.framework/LoginSDK",
  "capability": "network.endpoints",
  "path": "evidence/raw/ev-001.json",
  "hash": "sha256:...",
  "created_at": "2024-09-04T10:30:00Z",
  "immutable": true,
  "content": {
    "endpoint": "https://api.example.com/auth/login",
    "method": "POST",
    "headers": ["Content-Type: application/json"]
  }
}
```

### Derived Evidence

```json
{
  "evidence_id": "ev-derived-001",
  "case_id": "case-20240904-a1b2c3",
  "type": "derived",
  "strength": "inferred",
  "source_artifact": "App.app",
  "capability": "network.endpoints",
  "created_at": "2024-09-04T10:35:00Z",
  "immutable": true,
  "parent_refs": ["ev-20240904-001"],
  "content": {
    "summary": "Authentication endpoint identified",
    "confidence": "high"
  }
}
```

## Claim Structure

```json
{
  "claim_id": "claim-20240904-001",
  "case_id": "case-20240904-a1b2c3",
  "statement": "The app authenticates users via POST to /auth/login",
  "state": "inferred",
  "created_by": "network-analyst",
  "created_at": "2024-09-04T10:40:00Z",
  "evidence_refs": [
    "ev-20240904-001"
  ],
  "strength": "inferred",
  "confidence": "high",
  "metadata": {
    "endpoint": "https://api.example.com/auth/login",
    "method": "POST"
  }
}
```

## Resume Mechanism

### Resume Flow

```
1. Session Interrupted
       ↓
2. Checkpoint Saved
   (workflow_state + artifacts)
       ↓
3. New Session Starts
   /ios-reverse resume <case-id>
       ↓
4. ResumeEngine Reads Checkpoint
       ↓
5. Validates Integrity
   - Checkpoint not corrupted
   - Artifacts exist
   - Evidence valid
       ↓
6. Identifies Stale Nodes
   - Completed nodes: reuse
   - Failed nodes: retry
   - Pending nodes: continue
       ↓
7. Reuses Valid Artifacts
   - Evidence unchanged
   - Claims preserved
       ↓
8. Continues Execution
```

### Stale Detection

A node is considered stale if:
1. Its artifacts are missing or corrupted
2. Its parent nodes were re-run
3. Checkpoint references invalidated evidence

### Integrity Validation

```
ResumeEngine._validate_checkpoint()
       ↓
Checkpoint Exists? → No → Error
       ↓ Yes
Checkpoint Valid JSON? → No → Try Previous
       ↓ Yes
Artifacts Exist? → No → Mark Stale
       ↓ Yes
Evidence Valid? → No → Error
       ↓ Yes
Resume Valid
```

## Context Pack

Context pack is generated for each agent task:

```json
{
  "case_id": "case-20240904-a1b2c3",
  "workflow": "ios.network",
  "depth": "standard",
  "current_node": "network.endpoints",
  "relevant_artifacts": [
    "artifacts/unpacked/Info.plist",
    "artifacts/macho/executables.json"
  ],
  "relevant_evidence": [
    "evidence/raw/ev-001.json"
  ],
  "recent_claims": [
    "claims/claim-001.json"
  ],
  "context_size_bytes": 524288
}
```

**Bound**: Context pack is bounded (default: 512KB) to prevent explosion.

## Case Lifecycle

```
Created → In Progress → Completed/Failed
   ↓          ↓
   └──────────┴──→ Interrupted → Resumed → ...
```

### States

| State | Meaning |
|-------|---------|
| `created` | Case initialized |
| `in_progress` | Execution running |
| `interrupted` | Execution paused |
| `completed` | All nodes finished |
| `failed` | Critical failure |

## Execution vs HTTP Endpoints

**Execution Endpoint**: In-case execution record (`.kaiser-build/endpoints/`)

**HTTP Endpoint**: Not applicable. This is a CLI/agent framework, not a web service.

## Invariants

1. **Immutability**: Raw evidence never modified after creation
2. **Checkpoint Atomicity**: Checkpoint is complete or nothing
3. **Source of Truth**: Filesystem is authoritative
4. **Resume Determinism**: Same checkpoint = same resume behavior
5. **Evidence Hierarchy**: Raw evidence is foundation for derived
