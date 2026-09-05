# EP-06A: P06 Pre-Flight & Agent Schema

**Date**: 2026-09-04
**Phase**: P06 - Adaptive Multi-Agent Orchestration
**Subphase**: EP-06A

## Summary

Pre-flight compatibility check and agent schema design for P06.

## Pre-Flight Checklist

### 1. Load P05 Workflow Registry ✓
- 15 workflows defined
- Agent policies declared per workflow
- Complexity levels assigned

### 2. Load P04 Capability Registry ✓
- 27 capabilities implemented
- All contracts verified

### 3. Verify P05 Agent Policies

| Workflow | Allowed Agents |
|----------|---------------|
| ios.unpack | artifact-analyst |
| ios.inspect | artifact-analyst |
| ios.dump | artifact-analyst, objc-swift-analyst, coverage-auditor (full) |
| ios.macho | binary-analyst |
| ios.objc | objc-swift-analyst |
| ios.swift | objc-swift-analyst |
| ios.network | artifact-analyst, network-analyst, evidence-validator |
| ios.login-flow | planner, network-analyst, objc-swift-analyst, binary-analyst, evidence-validator |
| ios.crypto | binary-analyst |
| ios.anti-analysis | binary-analyst |
| ios.report | reporter |
| ios.decompile | (BLOCKED) |
| ios.ida | (BLOCKED) |
| ios.runtime | (BLOCKED) |
| ios.full | planner, artifact-analyst, objc-swift-analyst, binary-analyst, network-analyst, evidence-validator, coverage-auditor, reporter |

### 4. Agent Budget Model

| Depth | Max Active Specialists |
|-------|----------------------|
| quick | 1 |
| standard | 2 |
| deep | 4 |
| full | 6 |

## Agent Schema Design

### Agent Definition Model
```
AgentDefinition
├── agent_id: str
├── role: AgentRole
├── version: str
├── description: str
├── allowed_domains: List[str]
├── allowed_capabilities: List[str]
├── allowed_artifacts: List[str]
├── required_inputs: List[str]
├── expected_outputs: List[str]
├── max_scope: Complexity
├── allowed_tools: List[str]
├── context_policy: ContextPolicy
├── handoff_policy: HandoffPolicy
├── termination_conditions: List[str]
├── retry_policy: RetryPolicy
└── failure_semantics: FailureSemantics
```

### Canonical Agent Roles (8)
1. **planner** - Workflow decomposition, task planning
2. **artifact-analyst** - IPA/bundle/component analysis
3. **objc-swift-analyst** - Objective-C/Swift metadata
4. **binary-analyst** - Mach-O, imports/exports, symbols
5. **network-analyst** - Network framework evidence, endpoints
6. **evidence-validator** - Claim verification, conflict resolution
7. **coverage-auditor** - Coverage policy compliance
8. **reporter** - Report generation from normalized data

## Pre-Flight Actions

1. Create agent schema (ios_reverse/agents/model.py)
2. Create agent registry (ios_reverse/agents/registry.py)
3. Create agent task model
4. Create agent selector
5. Implement task scheduler
6. Implement evidence validator
7. Add integration tests

## Decision Points

### How to handle blocked workflows?

**Decision**: Agent roles may be defined for future use, but tasks requiring missing adapters remain BLOCKED.

**Rationale**: P05 workflow status is authoritative.

### How to prevent recursive spawning?

**Decision**: Only orchestrator/planner may create tasks. Agents operate on assigned tasks only.

**Implementation**: Centralized task scheduler with task creation permissions.

## Next Steps

1. Create agent model schema
2. Create agent registry
3. Define all 8 agent roles
4. Build agent selector
5. Implement task scheduler
