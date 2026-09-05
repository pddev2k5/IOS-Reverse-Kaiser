# EP-06C-06K: Task Scheduler, Validator, Context, Integration Tests

**Date**: 2026-09-04
**Phase**: P06 - Adaptive Multi-Agent Orchestration
**Subphase**: EP-06C-06K

## Summary

Completed task scheduler, evidence validator, context pack generator, and integration tests.

## Task Scheduler

### DependencyGraph
- Tracks task dependencies
- Provides dependency-aware readiness
- Supports blocking on failed tasks

### TaskScheduler
- Deterministic execution order
- Retry limits
- Blocked task handling
- Status tracking (PENDING, READY, RUNNING, DONE, FAILED, BLOCKED)

### Methods
- `add_task()` - Add task to scheduler
- `add_dependency()` - Add task dependency
- `get_ready_tasks()` - Get tasks ready to execute
- `mark_task_done()` - Mark task complete
- `mark_task_failed()` - Mark task failed (blocks dependents)
- `mark_task_blocked()` - Mark task blocked
- `get_next_task()` - Get next task deterministically
- `retry_task()` - Retry failed task if allowed

## Evidence Validator

### EvidenceValidator
- Validates claims against evidence
- Supports DOWNGRADE, REJECT, ACCEPT, NEEDS_MORE_EVIDENCE
- Tracks claim conflicts
- Strength-based validation

### EvidenceStrength Levels
1. STRING_HINT
2. REFERENCE
3. STRUCTURAL
4. CORRELATED
5. VERIFIED

## Context Pack Generator

### ContextPack
- Minimal deterministic context for agent tasks
- Includes only relevant facts, evidence, artifacts
- Supports JSON and Markdown output

### Agent Workspace Structure
```
workspace/cases/<case>/agents/<role>/
├── STATUS.md
├── TASKS.json
├── findings/
├── handoffs/
└── errors/
```

## Integration Tests

### Workflow-Agent Integration
- ✓ unpack workflow → single artifact-analyst
- ✓ dump workflow → multiple specialists
- ✓ network workflow → network-analyst
- ✓ report workflow → reporter only
- ✓ login-flow → planner + specialists

### Scope Leakage Prevention
- ✓ unpack does NOT select network-analyst
- ✓ unpack does NOT select coverage-auditor
- ✓ report does NOT spawn unnecessary agents

### Task Scheduling
- ✓ Dependency resolution
- ✓ Failed task blocks dependents
- ✓ Deterministic ordering

### Evidence Validation
- ✓ Valid claims accepted
- ✓ Missing evidence requires more
- ✓ Weak evidence causes downgrade

## Files
- `ios_reverse/agents/scheduler.py` - Task scheduler
- `ios_reverse/agents/validator.py` - Evidence validator
- `ios_reverse/agents/context.py` - Context pack generator
- `tests/test_agents.py` - 35 agent tests

## Test Summary

| Category | Count | Status |
|----------|-------|--------|
| Agent Roles | 2 | ✓ PASS |
| Agent Registry | 3 | ✓ PASS |
| Agent Budget | 1 | ✓ PASS |
| Agent Selector | 4 | ✓ PASS |
| Task Scheduler | 5 | ✓ PASS |
| Evidence Validator | 4 | ✓ PASS |
| Context Pack | 2 | ✓ PASS |
| Workflow Integration | 6 | ✓ PASS |
| Agent Task | 3 | ✓ PASS |
| Deterministic ID | 2 | ✓ PASS |
| **TOTAL** | **35** | **✓ PASS** |
