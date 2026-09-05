# EP-06B: Agent Schema, Registry & Selector

**Date**: 2026-09-04
**Phase**: P06 - Adaptive Multi-Agent Orchestration
**Subphase**: EP-06B

## Summary

Created agent schema, registry, and selector for P06.

## Agent Schema

### Agent Definition Model
```
AgentDefinition
├── agent_id: str
├── role: AgentRole
├── description: str
├── allowed_domains: List[str]
├── allowed_capabilities: List[str]
├── allowed_artifacts: List[str]
├── required_inputs: List[str]
├── expected_outputs: List[str]
├── max_scope: Complexity
├── context_policy: ContextPolicy
├── handoff_policy: HandoffPolicy
├── retry_policy: RetryPolicy
└── failure_semantics: FailureSemantics
```

### AgentTask Model
```
AgentTask
├── task_id: str
├── case_id: str
├── workflow_id: str
├── node_id: str
├── agent_role: AgentRole
├── objective: str
├── allowed_capabilities: List[str]
├── input_artifacts: List[str]
├── evidence_refs: List[str]
├── status: TaskStatus
├── retry_count: int
├── findings: Dict
└── validation_result: ValidationResult
```

## Canonical Agent Roles (8)

| Role | Description | Max Scope |
|------|-------------|-----------|
| planner | Workflow decomposition | VERY_HIGH |
| artifact-analyst | IPA/bundle analysis | MEDIUM |
| objc-swift-analyst | ObjC/Swift metadata | HIGH |
| binary-analyst | Mach-O analysis | HIGH |
| network-analyst | Network framework analysis | HIGH |
| evidence-validator | Claim validation | HIGH |
| coverage-auditor | Coverage compliance | MEDIUM |
| reporter | Report generation | LOW |

## Agent Budget

| Depth | Max Active Specialists |
|-------|----------------------|
| quick | 1 |
| standard | 2 |
| deep | 4 |
| full | 6 |

## Agent Selection

Workflow-bounded selection:
- ios.unpack → artifact-analyst only
- ios.dump → artifact + binary + objc-swift (+ coverage if full)
- ios.network → network-analyst + evidence-validator
- ios.login-flow → planner + specialists
- ios.report → reporter only

## Files
- `ios_reverse/agents/model.py` - Agent models
- `ios_reverse/agents/registry.py` - Agent registry
- `ios_reverse/agents/selector.py` - Agent selector

## Test Results

```
35 passed in 0.13s
```
