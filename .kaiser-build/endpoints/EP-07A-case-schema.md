# EP-07A: P07 Pre-Flight & Case Schema

**Date**: 2026-09-04
**Phase**: P07 - Persistent Case Workspace + Resume System
**Subphase**: EP-07A

## Summary

Pre-flight check and case schema design for P07.

## Pre-Flight Checklist

### 1. Load P05 Workflow Registry ✓
- 15 workflows defined
- Agent policies declared

### 2. Load P06 Agent System ✓
- 8 canonical agent roles
- Task scheduler
- Evidence validator

### 3. Design Case Workspace

```
workspace/
  cases/
    <case-id>/
      CASE.md
      PLAN.md
      STATUS.md
      NEXT.md
      DECISIONS.md
      TODO.md
      FAILURES.md
      manifest.json
      phases/
      endpoints/
      functions/
      callflows/
      claims/
      evidence/
        raw/
        derived/
      network/
        endpoints/
      artifacts/
        original/
        extracted/
        derived/
      logs/
      checkpoints/
      agents/
      .context/
        current.md
        history/
```

## Case Schema Design

### Case Identity
```
Case
├── case_id: str
├── display_name: str
├── created_at: str
├── updated_at: str
├── target_name: str
├── target_hash: str
├── canonical_intent: str
├── depth: str
├── workflow_id: str
├── schema_version: str
└── status: CaseStatus
```

### CaseManifest
```
manifest.json
├── case_id
├── workflow
├── depth
├── target
│   ├── name
│   ├── path
│   └── hash
├── state
│   ├── current_phase
│   ├── current_node
│   └── overall_status
├── checkpoint
│   ├── latest
│   └── history
├── claims
│   └── index_path
├── evidence
│   └── index_path
├── artifacts
│   └── index_path
├── agents
│   └── state_path
├── coverage
│   └── summary_path
├── outputs
│   └── paths
└── schema_versions
```

### WorkflowState
```
WorkflowState
├── workflow_id: str
├── depth: str
├── nodes: Dict[node_id, NodeState]
├── completed_nodes: List[str]
├── failed_nodes: List[str]
├── blocked_nodes: List[str]
└── current_node: Optional[str]
```

### NodeState
```
NodeState
├── node_id: str
├── status: TaskStatus
├── started_at: Optional[str]
├── completed_at: Optional[str]
├── findings: Dict
├── errors: List[str]
├── evidence_refs: List[str]
└── stale: bool
```

### EvidenceIndex
```
evidence/index.json
└── entries: List[EvidenceRecord]
    ├── evidence_id: str
    ├── case_id: str
    ├── type: str
    ├── strength: EvidenceStrength
    ├── source_artifact: str
    ├── component: Optional[str]
    ├── capability: str
    ├── path: str
    ├── hash: str
    ├── created_at: str
    ├── immutable: bool
    ├── parent_refs: List[str]
    └── provenance: List[str]
```

### ClaimsIndex
```
claims/index.json
└── entries: List[ClaimRecord]
    ├── claim_id: str
    ├── statement: str
    ├── state: ClaimState
    ├── evidence_refs: List[str]
    ├── component_refs: List[str]
    ├── function_refs: List[str]
    ├── endpoint_refs: List[str]
    ├── created_by: str
    ├── validated_by: Optional[str]
    ├── created_at: str
    ├── updated_at: str
    └── transitions: List[Transition]
```

## Next Steps

1. Create case model (ios_reverse/workspace/model.py)
2. Create case manager
3. Create evidence/claims stores
4. Create checkpoint engine
5. Create resume engine
6. Add tests
