# IOS REVERSE KAISER — Agent Role Specifications

## Agent System Overview

The agent system provides adaptive orchestration based on workflow complexity.

### Design Principles

1. **Single by default**: Don't run multiple agents unless needed
2. **Artifact-based handoffs**: Agents exchange files, not conversation
3. **No recursive loops**: Bounded execution depth
4. **Role specialization**: Each role has clear responsibilities

---

## Agent Roles

### executor
**Description**: Primary execution agent for simple workflows  
**Complexity Range**: 0-10  
**Responsibilities**:
- Execute single-capability workflows
- Produce structured outputs
- Record provenance
- Handle errors gracefully

**Allowed Tools**:
- Bash
- Read
- Write
- Glob
- Grep

### planner
**Description**: Creates execution plans for complex workflows  
**Complexity Range**: 26-50+  
**Responsibilities**:
- Analyze workflow requirements
- Create execution plan
- Allocate capabilities to phases
- Handle workflow branching

**Allowed Tools**:
- All tools
- Artifact analysis
- Plan generation

### artifact-analyst
**Description**: Analyzes extracted artifacts  
**Complexity Range**: 11-50+  
**Responsibilities**:
- Analyze extracted data
- Identify patterns
- Generate insights
- Produce structured findings

**Specializations**:
- Plist analysis
- Entitlements analysis
- Bundle structure analysis

### objc-swift-analyst
**Description**: Specializes in Objective-C and Swift metadata  
**Complexity Range**: 11-50+  
**Responsibilities**:
- Analyze ObjC class/method metadata
- Analyze Swift type/method metadata
- Handle demangling
- Identify patterns

**Specializations**:
- ObjC class hierarchy
- Swift protocol conformance
- Selector patterns
- Swift dispatch patterns

### binary-analyst
**Description**: Analyzes binary structure and content  
**Complexity Range**: 11-50+  
**Responsibilities**:
- Analyze Mach-O structure
- Extract imports/exports/symbols
- Analyze load commands
- Identify architecture

**Specializations**:
- Mach-O internals
- Symbol tables
- String analysis
- Architecture detection

### network-analyst
**Description**: Specializes in network pattern analysis  
**Complexity Range**: 11-50+  
**Responsibilities**:
- Analyze network frameworks
- Extract endpoints
- Identify authentication patterns
- Document API surfaces

**Specializations**:
- URLSession patterns
- Alamofire/AFNetworking
- GraphQL analysis
- WebSocket detection
- Certificate pinning patterns

### evidence-validator
**Description**: Validates claims against evidence  
**Complexity Range**: 11-50+  
**Responsibilities**:
- Verify claims have evidence
- Check claim states
- Ensure evidence integrity
- Flag unsupported claims

**Specializations**:
- SHA-256 verification
- Provenance tracking
- Claim/evidence mapping

### coverage-auditor
**Description**: Audits coverage for full/deep workflows  
**Complexity Range**: 51+  
**Responsibilities**:
- Measure coverage dimensions
- Flag uncovered scope
- Ensure completeness
- Generate coverage reports

**Specializations**:
- Coverage dimension analysis
- Threshold validation
- Coverage visualization

### reporter
**Description**: Generates final reports  
**Complexity Range**: 51+  
**Responsibilities**:
- Aggregate findings
- Generate structured reports
- Document evidence
- Format output

**Specializations**:
- Markdown generation
- JSON report generation
- Evidence documentation

---

## Orchestration Tiers

### Tier 1: Simple (0-10 complexity)

```
User Input
    │
    ▼
Command Router
    │
    ▼
executor
    │
    ▼
Structured Output
```

**Agents**: executor only  
**Workflows**: unpack, inspect, dump (quick)  

### Tier 2: Moderate (11-25 complexity)

```
User Input
    │
    ▼
Command Router
    │
    ▼
executor
    │
    ▼
Evidence Validator
    │
    ▼
Validated Output
```

**Agents**: executor + evidence-validator  
**Workflows**: dump (standard), macho, objc, swift, network  

### Tier 3: Complex (26-50 complexity)

```
User Input
    │
    ▼
Command Router
    │
    ▼
planner
    │
    ▼
┌───────┴───────┐
│               │
▼               ▼
artifact    binary
-analyst    -analyst
    │               │
    ▼               ▼
network     objc-swift
-analyst    -analyst
    │               │
    └───────┬───────┘
            │
            ▼
    evidence-validator
            │
            ▼
    Structured Findings
```

**Agents**: planner + specialists + evidence-validator  
**Workflows**: dump (deep), network (full), login-flow, crypto  

### Tier 4: Full (51+ complexity)

```
User Input
    │
    ▼
Command Router
    │
    ▼
planner
    │
    ▼
┌───────┴───────┬───────────┐
│               │           │
▼               ▼           ▼
artifact    binary      network
-analyst    -analyst   -analyst
    │               │           │
    ▼               ▼           ▼
objc-swift  crypto     runtime
-analyst    -analyst   -abstract
    │               │           │
    └───────┬───────┴───┬───────┘
            │           │
            ▼           ▼
    evidence-validator  coverage
            │           -auditor
            │           │
            ▼           ▼
    ┌───────┴───────────┘
    │
    ▼
    reporter
    │
    ▼
    Final Report
```

**Agents**: planner + specialists + validator + auditor + reporter  
**Workflows**: full, dump-full, network-full  

---

## Agent Exchange Protocol

Agents exchange data via the filesystem:

```
workspace/cases/<case-id>/
├── .context/
│   └── current.md
├── agents/
│   ├── planner/
│   │   └── plan.md
│   ├── artifact-analyst/
│   │   └── findings.json
│   ├── binary-analyst/
│   │   └── findings.json
│   └── ...
├── evidence/
│   └── ...
└── reports/
    └── ...
```

**Handoff Protocol**:
1. Agent A produces artifact at `<agent>/output.<ext>`
2. Agent A updates `<agent>/STATUS.md`
3. Agent B reads artifact
4. Agent B verifies provenance
5. Agent B produces own output

---

## Agent Prompt Structure

Each agent role has a standard prompt structure:

```markdown
# Role: <role-name>

## Context
- Case ID: <case-id>
- Current Phase: <phase>
- Workflow: <workflow-id>
- Complexity: <score>

## Objective
<objective statement>

## Constraints
- Only analyze authorized artifacts
- Do not broaden scope
- Record all provenance
- Output structured results

## Input
- Available artifacts: <list>
- Previous findings: <references>

## Output
- Structured findings (JSON)
- Evidence references
- Provenance chain

## Tools
<allowed tools list>
```

---

## State Machine Integration

Agents interact with the workflow state machine:

```
Node State: PENDING
    │
    ▼
Agent Selected for Node
    │
    ▼
Node State: RUNNING
    │
    ▼
Agent Executes
    │
    ├─── Success ───▶ Node State: DONE
    │
    ├─── Skip ──────▶ Node State: SKIPPED
    │
    └─── Failure ──▶ Node State: FAILED
                          │
                          ▼
                   Stop Condition Check
                          │
                          ├─── continue ──▶ Next Node
                          └─── abort ─────▶ Workflow FAILED
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the agent role specifications.*
