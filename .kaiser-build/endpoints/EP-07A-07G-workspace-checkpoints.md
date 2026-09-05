# EP-07A-07G: Case Workspace, Evidence, Checkpoints, Resume

**Date**: 2026-09-04
**Phase**: P07 - Persistent Case Workspace + Resume System
**Subphase**: EP-07A-07G

## Summary

Created persistent case workspace and resume system for P07.

## Case Structure

```
workspace/cases/<case-id>/
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
  evidence/raw/
  evidence/derived/
  network/endpoints/
  artifacts/original/
  artifacts/extracted/
  artifacts/derived/
  logs/
  checkpoints/
  agents/
  .context/
    current.md
    history/
```

## Key Components

### Case Manager
- `ios_reverse/workspace/manager.py`
- Create, load, list, checkpoint cases
- Case locking (cross-platform)

### Evidence Store
- `ios_reverse/workspace/evidence.py`
- Raw vs derived separation
- Indexed evidence

### Claims Store
- `ios_reverse/workspace/evidence.py`
- State transitions tracked
- Verified, rejected, open claims

### Resume Engine
- `ios_reverse/workspace/resume.py`
- ResumePlan generation
- Stale detection

### Context Pack
- `ios_reverse/workspace/context_pack.py`
- Minimal context for agents
- Living docs support

## Test Results

```
30 passed in 0.65s
```
