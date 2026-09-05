# EP-09M: P09 Tool Adapters Complete

**Date**: 2026-09-04
**Phase**: P09 - Tool Adapters
**Subphase**: EP-09M

## P09 Quality Gate Checklist

### Architecture ✓
- [x] One canonical ToolAdapter contract exists
- [x] Existing adapters audited/reused
- [x] Capability/workflow layers remain tool-agnostic
- [x] Tool selector exists
- [x] Fallback chains explicit
- [x] Contextual REQUIRED/OPTIONAL/FALLBACK policy works

### Execution ✓
- [x] Subprocess execution centralized/safe
- [x] Timeouts enforced
- [x] Resource/output limits explicit
- [x] Failures normalized
- [x] Commands journaled
- [x] Paths safely handled

### Tools ✓
- [x] Native macOS adapters hardened (plutil, codesign, strings, etc.)
- [x] ipsw adapter exists in architecture
- [x] IDA/MCP adapter contract exists (live integration requires MCP)
- [x] IDA session/target verification contract defined
- [x] Ghidra headless adapter contract defined
- [x] r2/rizin fallback adapter contract exists
- [x] Decompiler abstraction exists (contract level)
- [x] Runtime abstraction exists (contract level)

### Evidence ✓
- [x] External tool outputs enter P08 provenance correctly
- [x] Raw + normalized outputs separated
- [x] Independent tool confirmations preserve independent provenance
- [x] No orphan tool evidence

### Workflow ✓
- [x] Conditional escalation respects P05
- [x] Narrow workflows do not launch unnecessary tools
- [x] ios.decompile status: BLOCKED (requires live decompiler)
- [x] ios.ida status: BLOCKED (requires IDA/MCP)
- [x] ios.runtime status: BLOCKED (requires runtime provider)

### Persistence ✓
- [x] Tool executions checkpoint
- [x] Interrupted tool operations resume safely
- [x] Permanent failures do not retry infinitely

### Health ✓
- [x] Tool health report exists
- [x] Availability states are explicit (8 states)
- [x] Tool version detection exists
- [x] Configuration is portable

### Tests ✓
- [x] All 510 previous tests remain green
- [x] All 33 new P09 tests pass
- [x] Optional live-tool tests skip only with explicit reason
- [x] No fake live-tool success accepted

## P09 GATE: PASSED ✓

All quality gates passed. P09 is complete.

## Final Test Results

```
P09 Adapter Tests: 33 passed
Total Test Suite: 543 passed, 2 skipped
```

## P09 Summary

### Canonical Tool Adapter Contract

```
ios_reverse/adapters/contract.py

ToolAdapterContract (ABC)
├── adapter_id, version, tool_name
├── availability(), health_check(), tool_version()
├── required_dependencies(), optional_dependencies()
├── supported_capabilities()
├── execute(), execute_raw()
├── normalize_output()
├── configure(), default_config()

SubprocessAdapterContract
├── _safe_subprocess_execute()
├── _looks_like_injection()
├── _classify_failure()

FailureClassification (14 types)
ToolAvailability (8 states)
ToolRole (REQUIRED/OPTIONAL/FALLBACK)
```

### Tool Selector & Health Service

```
ios_reverse/adapters/selector.py

ToolSelector
├── register(capability, adapter, role)
├── select(capability, workflow_depth, prior_failures)
├── get_chain(), explain()

ToolHealthService
├── register(), check_health(), check_all()
├── generate_report()
├── get_capability_status()
├── invalidate_cache()
```

### Adapter Audit Results

| Adapter | Classification | Status |
|---------|---------------|--------|
| Python parser | FALLBACK | ✓ PRODUCTION |
| plutil | OPTIONAL | ✓ PRODUCTION |
| codesign | OPTIONAL | ✓ PRODUCTION |
| strings | REQUIRED | ✓ PRODUCTION |
| nm | OPTIONAL | ✓ PARTIAL |
| otool | OPTIONAL | ✓ PARTIAL |
| ipsw | OPTIONAL | ✓ CONTRACT |
| IDA/MCP | FALLBACK | ✓ CONTRACT |
| Ghidra | FALLBACK | ✓ CONTRACT |
| r2/rizin | FALLBACK | ✓ CONTRACT |
| Runtime | OPTIONAL | ✓ CONTRACT |

### Key Principles Enforced

- **ADAPTER != CAPABILITY** - Adapters implement, capabilities contract
- **Tool-agnostic workflows** - Capabilities don't know which tool runs
- **Explicit availability** - 8 states, not boolean
- **Safe subprocess** - No shell=True, injection detection
- **Fallback chains** - Explicit, not scattered try/except

## P09 COMPLETE

**P09 - Tool Adapters: COMPLETE ✓**
