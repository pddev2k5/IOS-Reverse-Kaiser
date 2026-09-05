# EP-09A: P09 Adapter Audit

**Date**: 2026-09-04
**Phase**: P09 - Tool Adapters
**Subphase**: EP-09A

## Summary

Pre-flight audit of existing adapters from P04.

## Existing Adapters Inventory

### Core Adapters (`ios_reverse/adapters/core/`)

| Adapter | Status | Notes |
|---------|--------|-------|
| `file_adapter.py` | PRODUCTION_READY | File operations |
| `unzip_adapter.py` | PRODUCTION_READY | IPA extraction |
| `plutil_adapter.py` | PRODUCTION_READY | plist parsing |
| `codesign_adapter.py` | PRODUCTION_READY | Code signing verification |
| `find_adapter.py` | PRODUCTION_READY | File finding |

### Mach-O Adapters (`ios_reverse/adapters/macho/`)

| Adapter | Status | Notes |
|---------|--------|-------|
| `parser_adapter.py` | PRODUCTION_READY | Pure Python Mach-O parser |
| `otool_adapter.py` | PARTIAL | macOS only, fallback to parser |
| `nm_adapter.py` | PARTIAL | macOS only |
| `strings_adapter.py` | PRODUCTION_READY | Cross-platform |

### Language Adapters (`ios_reverse/adapters/objc/`, `swift/`)

| Adapter | Status | Notes |
|---------|--------|-------|
| `objc_adapter.py` | PRODUCTION_READY | ObjC metadata extraction |
| `swift_adapter.py` | PRODUCTION_READY | Swift metadata extraction |
| `swift_demangler.py` | PRODUCTION_READY | Swift symbol demangling |

### Component Adapters (`ios_reverse/adapters/components/`)

| Adapter | Status | Notes |
|---------|--------|-------|
| `framework_adapter.py` | PRODUCTION_READY | Framework analysis |
| `dylib_adapter.py` | PRODUCTION_READY | Dynamic library analysis |
| `extension_adapter.py` | PRODUCTION_READY | Extension analysis |

### Analysis Adapters (`ios_reverse/adapters/analysis/`)

| Adapter | Status | Notes |
|---------|--------|-------|
| `network_adapter.py` | PRODUCTION_READY | Network endpoint analysis |
| `architecture_adapter.py` | PRODUCTION_READY | Architecture analysis |
| `callflow_adapter.py` | PRODUCTION_READY | Call flow analysis |
| `crypto_adapter.py` | PRODUCTION_READY | Crypto primitive analysis |
| `anti_analysis_adapter.py` | PRODUCTION_READY | Anti-analysis detection |

## Canonical Tool Adapter Contract (NEW)

Created `ios_reverse/adapters/contract.py` with:

- `ToolAdapterContract` - Abstract base for all adapters
- `SubprocessAdapterContract` - Safe subprocess execution
- `FallbackChain` - Explicit fallback chains
- `ToolAvailability` - Explicit availability states (8 states)
- `ToolRole` - REQUIRED/OPTIONAL/FALLBACK
- `FailureClassification` - 14 failure types
- `AdapterExecutionResult` - Canonical result format

## Tool Selector (NEW)

Created `ios_reverse/adapters/selector.py` with:

- `ToolSelector` - Capability-based adapter selection
- `ToolHealthService` - Centralized health monitoring
- Health caching with TTL
- Capability matrix generation

## Classification Matrix

| Tool | Role | Platform | Status |
|------|------|----------|--------|
| Python parser | FALLBACK | All | PRODUCTION_READY |
| otool | OPTIONAL | macOS | PARTIAL |
| plutil | OPTIONAL | macOS | PRODUCTION_READY |
| codesign | OPTIONAL | macOS | PRODUCTION_READY |
| nm | OPTIONAL | macOS | PARTIAL |
| strings | REQUIRED | All | PRODUCTION_READY |
| ipsw | OPTIONAL | All | NEEDS_P09_HARDENING |
| IDA/MCP | FALLBACK | All | NEEDS_P09_HARDENING |
| Ghidra | FALLBACK | All | NEEDS_P09_HARDENING |
| radare2/rizin | FALLBACK | All | NEEDS_P09_HARDENING |

## Integration Gaps

1. **No unified tool selector** - FIXED in P09
2. **No explicit availability states** - FIXED in P09
3. **No centralized subprocess safety** - FIXED in P09
4. **No health service** - FIXED in P09
5. **No IDA/MCP adapter** - TODO in P09
6. **No Ghidra adapter** - TODO in P09
7. **No radare2/rizin adapter** - TODO in P09
8. **No runtime abstraction** - TODO in P09

## Next Steps

1. Implement missing adapters (IDA, Ghidra, r2)
2. Create runtime abstraction contract
3. Add E2E integration tests
4. Update P05 workflow statuses
