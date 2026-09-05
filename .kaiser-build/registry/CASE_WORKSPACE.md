# IOS REVERSE KAISER — Case Workspace Schema

## Case Workspace Structure

Every reverse engineering task creates a persistent case workspace.

---

## Directory Structure

```
workspace/
└── cases/
    └── <case-id>/
        ├── CASE.md
        ├── PLAN.md
        ├── STATUS.md
        ├── NEXT.md
        ├── DECISIONS.md
        ├── TODO.md
        ├── FAILURES.md
        
        ├── phases/
        │   ├── phase-00-triage.md
        │   ├── phase-01-extraction.md
        │   └── ...
        
        ├── endpoints/
        │   ├── EP-000.md
        │   ├── EP-001.md
        │   └── ...
        
        ├── functions/
        │   ├── function-name-1.md
        │   ├── function-name-2.md
        │   └── ...
        
        ├── callflows/
        │   ├── login-flow.md
        │   └── ...
        
        ├── claims/
        │   ├── CLAIM-001.md
        │   ├── CLAIM-002.md
        │   └── ...
        
        ├── evidence/
        │   ├── raw/
        │   │   ├── E-001-strings-main.txt
        │   │   ├── E-002-nm-output.json
        │   │   └── ...
        │   ├── derived/
        │   │   ├── E-101-extracted-urls.json
        │   │   └── ...
        │   └── manifest.json
        
        ├── network/
        │   ├── endpoints/
        │   │   ├── POST-auth-login.md
        │   │   ├── GET-user-profile.md
        │   │   └── ...
        │   └── analysis.md
        
        ├── artifacts/
        │   ├── unpacked/
        │   │   ├── Payload/
        │   │   └── ...
        │   ├── macho/
        │   │   └── ...
        │   ├── objc/
        │   │   └── ...
        │   ├── swift/
        │   │   └── ...
        │   └── reports/
        │       ├── analysis-report.md
        │       └── coverage-report.md
        
        ├── logs/
        │   ├── workflow.log
        │   └── agent.log
        
        ├── checkpoints/
        │   ├── CP-001.json
        │   ├── CP-002.json
        │   └── latest.json
        
        ├── agents/
        │   ├── planner/
        │   │   └── findings.json
        │   ├── artifact-analyst/
        │   │   └── findings.json
        │   └── ...
        
        └── .context/
            ├── current.md
            └── context-history/
                ├── cp-001.md
                └── cp-002.md
```

---

## Required Files

### CASE.md
```markdown
# Case: <case-id>

## Target
- Artifact: <path>
- Type: IPA | App | Mach-O | Framework | Dylib
- Size: <bytes>
- Hash: <SHA-256>

## Objective
<user-stated goal>

## Scope
- Intents: <array>
- Depth: <quick|standard|deep|full>
- Exclusions: <array>

## Timeline
- Created: <ISO8601>
- Last Updated: <ISO8601>

## Status
<active|completed|aborted>
```

### PLAN.md
```markdown
# Plan: <case-id>

## Objective
<specific objective>

## Workflow
- Workflow ID: <workflow-id>
- Complexity: <score>
- Tier: <simple|moderate|complex|full>

## Phases
1. Phase 1: <description>
2. Phase 2: <description>
...

## Resources
- Capabilities: <array>
- Tools: <array>
- Agents: <array>

## Success Criteria
- Required nodes: <array>
- Minimum coverage: <percentage>

## Timeline
- Estimated duration: <duration>
- Checkpoint interval: <interval>
```

### STATUS.md
```markdown
# Status: <case-id>

## Current State
- Phase: <current phase>
- Node: <current node>
- Status: <PENDING|RUNNING|DONE|FAILED>

## Progress
- Total Nodes: <count>
- Completed: <count>
- Skipped: <count>
- Failed: <count>
- Pending: <count>

## Active Workflow
- Workflow ID: <workflow-id>
- Started: <ISO8601>
- Duration: <duration>

## Last Checkpoint
- Checkpoint ID: <CP-XXX>
- Timestamp: <ISO8601>

## Next Action
<immediate next action>
```

### DECISIONS.md
```markdown
# Decisions: <case-id>

## Decision Log

### D-001
- Date: <ISO8601>
- Decision: <description>
- Rationale: <why>
- Impact: <what changed>

...
```

### TODO.md
```markdown
# TODO: <case-id>

## Pending Tasks
- [ ] Task 1
- [ ] Task 2

## In Progress
- [x] Task in progress

## Completed
- [x] Completed task
```

### FAILURES.md
```markdown
# Known Failures: <case-id>

## Dead Ends (Do Not Retry)
- Approach 1: <reason>
- Approach 2: <reason>

## Partial Solutions
- Feature X: Works partially, <limitation>

## Open Issues
- Issue 1: <description>
- Issue 2: <description>
```

---

## Evidence Directory

### Structure
```
evidence/
├── raw/           # Direct tool outputs
├── derived/       # Processed interpretations
└── manifest.json # Evidence index
```

### manifest.json
```json
{
  "case_id": "string",
  "version": "1.0",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  
  "entries": [
    {
      "id": "E-001",
      "type": "raw",
      "file": "raw/strings-main.txt",
      "sha256": "string",
      "size": "number",
      "capability": "binary.strings",
      "created_at": "ISO8601"
    },
    {
      "id": "E-002",
      "type": "derived",
      "file": "derived/extracted-urls.json",
      "sha256": "string",
      "size": "number",
      "capability": "network.endpoint_extract",
      "sources": ["E-001"],
      "created_at": "ISO8601"
    }
  ],
  
  "total_raw": "number",
  "total_derived": "number"
}
```

---

## Claims Directory

### CLAIM-XXX.md
```markdown
# Claim: CLM-XXX

## Statement
<the claim>

## State
verified | inferred | suspected | rejected | unknown

## Evidence
- E-001: <description>
- E-002: <description>

## Reasoning
<how the claim was derived>

## Confidence
<0-100>%

## Validation
- Validated by: <agent>
- Validated at: <ISO8601>

## History
- Created: <ISO8601>
- Updated: <ISO8601>
- State changes:
  - <ISO8601>: unknown → suspected (reason)
  - <ISO8601>: suspected → inferred (additional evidence)
```

---

## Living Documents

Documents are "living" when they evolve as analysis progresses.

### Function Documents

```
functions/
├── T0x00___ExampleClass__loginWithUser.md
├── T0x01___ExampleClass__validateToken.md
└── T0x02___ExampleClass__refreshToken.md
```

### Callflow Documents

```
callflows/
├── login-flow.md
├── register-flow.md
└── payment-flow.md
```

### Network Endpoint Documents

```
network/
└── endpoints/
    ├── POST-auth-login.md
    ├── GET-user-profile.md
    ├── PUT-user-settings.md
    └── POST-payments-process.md
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the case workspace schema.*
