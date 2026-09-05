# IOS REVERSE KAISER — State Machine & Checkpoint Protocol

## Node States

Each workflow node has one of the following states:

| State | Description | Can Transition To |
|-------|-------------|-------------------|
| PENDING | Not yet ready to execute | READY |
| READY | Dependencies satisfied | RUNNING |
| RUNNING | Currently executing | DONE, SKIPPED, FAILED |
| DONE | Successfully completed | — |
| SKIPPED | Intentionally skipped | — |
| BLOCKED | Dependency failed | — |
| FAILED | Execution failed | — |
| STALE | Outputs invalidated | PENDING, SKIPPED |

---

## State Transitions

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│ PENDING │───▶│  READY  │───▶│ RUNNING │───▶│   DONE   │     │
└─────────┘    └─────────┘    └─────────┘    └─────────┘     │
     │              │              │                          │
     │              │              ├─────────────────────────┼──▶ SKIPPED
     │              │              │                         │
     │              │              │                         ▼
     │              │              │                   ┌─────────┐
     │              │              └──────────────────▶│  FAILED │
     │              │                                  └─────────┘
     │              │                                        │
     │              │                                        ▼
     │              │                               ┌─────────────────┐
     │              └──────────────────────────────▶│    BLOCKED      │
     │                                                └─────────────────┘
     │
     │   (outputs invalidated)
     ▼
┌─────────┐
│  STALE  │──────────────▶ PENDING (re-run)
└─────────┘          or
                     SKIPPED (if not needed)
```

---

## State Transition Rules

### PENDING → READY
- All dependencies in DONE or SKIPPED state
- Required artifacts exist or can be produced

### READY → RUNNING
- Agent selected for node
- Execution begins

### RUNNING → DONE
- Capability executed successfully
- Outputs produced
- Provenance recorded

### RUNNING → SKIPPED
- Explicit skip condition met
- Optional node with alternate satisfied
- User requested skip

### RUNNING → FAILED
- Execution error
- Tool unavailable
- Timeout exceeded
- Invalid inputs

### ANY → STALE
- Input artifacts changed
- Dependencies invalidated
- Workflow definition updated

---

## Workflow State

The overall workflow state aggregates node states:

```json
{
  "workflow_id": "string",
  "workflow_version": "semver",
  "status": "PENDING | RUNNING | DONE | FAILED | ABORTED",
  
  "nodes": {
    "node_id": {
      "state": "PENDING | READY | RUNNING | DONE | SKIPPED | BLOCKED | FAILED | STALE",
      "started_at": "ISO8601 (optional)",
      "completed_at": "ISO8601 (optional)",
      "error": "string (if failed)",
      "retry_count": "number"
    }
  },
  
  "summary": {
    "total": "number",
    "done": "number",
    "skipped": "number",
    "failed": "number",
    "pending": "number",
    "running": "number"
  },
  
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

## Checkpoint Protocol

### Checkpoint Trigger Points

Checkpoints are created at:
1. Before each node execution
2. After each node completion (success/failure/skip)
3. At workflow completion
4. On explicit user request
5. On context limit warning

### Checkpoint File Format

```json
{
  "id": "CP-XXX",
  "build": "ios-reverse-kaiser",
  "case_id": "string (if case workspace)",
  
  "phase": "string (e.g., 'P02')",
  "endpoint": "string (e.g., 'EP-002')",
  "workflow_id": "string",
  "workflow_version": "semver",
  
  "status": "RUNNING | DONE | FAILED | ABORTED",
  
  "created": "ISO8601",
  "updated": "ISO8601",
  "version": "string",
  
  "completed_nodes": ["array of completed node IDs"],
  "current_node": "string (node ID or 'WORKFLOW_COMPLETE')",
  "next_actions": ["array of next actions"],
  
  "workflow_state": {
    /* WorkflowState object */
  },
  
  "important_files": ["array of file paths"],
  
  "tests": {
    /* Test results at checkpoint */
  },
  
  "known_failures": ["array of known failure reasons"],
  
  "metrics": {
    /* Arbitrary metrics */
  },
  
  "resume_instructions": "string"
}
```

### Checkpoint Files

| File | Purpose |
|------|---------|
| `CP-XXX.json` | Machine-readable checkpoint |
| `latest.json` | Pointer to most recent checkpoint |
| `workflow-state.json` | Current workflow state |

### Checkpoint Storage

```
.kaiser-build/
├── checkpoints/
│   ├── CP-000.json
│   ├── CP-001.json
│   ├── ...
│   ├── CP-XXX.json
│   └── latest.json
├── workflows/
│   └── <workflow-id>/
│       ├── workflow-state.json
│       └── nodes/
│           └── <node-id>/
│               ├── state.json
│               ├── output.json
│               └── provenance.json
```

---

## Resume Logic

### Resume Algorithm

```python
def resume_from_checkpoint(checkpoint):
    # 1. Load workflow state
    workflow_state = load_workflow_state(checkpoint)
    
    # 2. Identify nodes to rerun
    nodes_to_run = []
    for node_id, node_state in workflow_state.nodes.items():
        if node_state.status == 'PENDING':
            nodes_to_run.append(node_id)
        elif node_state.status == 'STALE':
            # Check if inputs changed
            if inputs_invalidated(node_id):
                nodes_to_run.append(node_id)
        elif node_state.status == 'FAILED':
            # Check retry policy
            if node_state.retry_count < MAX_RETRIES:
                nodes_to_run.append(node_id)
    
    # 3. Skip DONE/SKIPPED unless invalidated
    # Already handled in step 2
    
    # 4. Resume execution
    for node_id in topological_sort(nodes_to_run):
        execute_node(node_id)
        create_checkpoint()
    
    # 5. Update workflow state
    update_workflow_state()
```

### Resume Conditions

A node is rerun only if:
1. Its state is PENDING
2. Its state is STALE and inputs are invalidated
3. Its state is FAILED and retry count < MAX_RETRIES
4. User explicitly requests rerun

### Resume Safety Rules

1. Never rerun DONE nodes unless inputs changed
2. Never rerun SKIPPED nodes
3. Always verify outputs exist before skipping
4. Always record why a node was skipped
5. Never skip if provenance chain is broken

---

## Context Pack Generation

### When to Generate

- At checkpoint creation
- At phase transitions
- On explicit request
- When context warning appears

### Context Pack Format

```json
{
  "phase": "string",
  "status": "string",
  
  "current_objective": "string",
  
  "verified_facts": ["array of confirmed facts"],
  
  "open_claims": [
    {
      "claim": "string",
      "state": "inferred | suspected | unknown",
      "evidence": ["array of evidence refs"]
    }
  ],
  
  "active_artifacts": ["array of important files"],
  
  "decisions_made": [
    {
      "id": "string",
      "decision": "string",
      "rationale": "string"
    }
  ],
  
  "known_failures": ["array of failure reasons"],
  
  "next_actions": ["array of next actions"],
  
  "required_files": ["array of files to read"],
  
  "resume_instructions": "string"
}
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the state machine and checkpoint protocol.*
