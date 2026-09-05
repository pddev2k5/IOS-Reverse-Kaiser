# EP-05B: Workflow Schema & Registry

**Date**: 2026-09-04
**Phase**: P05 - Workflow Maps
**Subphase**: EP-05B

## Summary

Created canonical workflow schema and registry for IOS REVERSE KAISER.

## Schema Components

### Core Enums
- **Intent**: unpack, inspect, dump, decompile, macho, objc, swift, network, login-flow, crypto, anti-analysis, ida, runtime, report, full
- **Depth**: quick, standard, deep, full
- **WorkflowStatus**: implemented, blocked, deferred, planned
- **Complexity**: low, medium, high, very_high

### Core Classes
- **WorkflowDefinition**: Complete workflow definition with DAG structure
- **WorkflowNode**: Node in the workflow DAG with capability/condition support
- **WorkflowEdge**: Edge connecting nodes with optional conditions
- **CoveragePolicy**: Coverage policy for workflows
- **AgentPolicy**: Agent policy declarations
- **WorkflowExecutionState**: Runtime state for execution tracking

## Workflow Registry

| Workflow ID | Intent | Status | Complexity |
|------------|--------|--------|------------|
| ios.unpack | unpack | IMPLEMENTED | LOW |
| ios.inspect | inspect | IMPLEMENTED | MEDIUM |
| ios.dump | dump | IMPLEMENTED | HIGH |
| ios.macho | macho | IMPLEMENTED | MEDIUM |
| ios.objc | objc | IMPLEMENTED | MEDIUM |
| ios.swift | swift | IMPLEMENTED | MEDIUM |
| ios.network | network | IMPLEMENTED | HIGH |
| ios.login-flow | login-flow | IMPLEMENTED | HIGH |
| ios.crypto | crypto | IMPLEMENTED | MEDIUM |
| ios.anti-analysis | anti-analysis | IMPLEMENTED | MEDIUM |
| ios.report | report | IMPLEMENTED | LOW |
| ios.decompile | decompile | BLOCKED | HIGH |
| ios.ida | ida | BLOCKED | HIGH |
| ios.runtime | runtime | BLOCKED | VERY_HIGH |
| ios.full | full | IMPLEMENTED | VERY_HIGH |

## Intent Normalization

Supported aliases and depth modifiers:
- `dump-full` → intent: dump, depth: full
- `unpack-quick` → intent: unpack, depth: quick
- `network-deep` → intent: network, depth: deep

## Depth Control

| Depth | Scope | Coverage |
|-------|-------|----------|
| quick | Minimal | None |
| standard | Common | None |
| deep | Extended | Partial |
| full | Maximum | Complete |

## Scope Leakage Prevention

Validators enforce that:
- `ios.unpack` does NOT include: macho.*, binary.*, objc.*, swift.*, network.*, crypto.*, anti_analysis.*
- `ios.report` does NOT include any analysis capabilities
- Each workflow only references its declared scope

## Files

- `ios_reverse/workflows/schema.py` - Workflow schema and models
- `ios_reverse/workflows/definitions.py` - All workflow definitions
- `ios_reverse/workflows/registry.py` - Workflow registry
- `ios_reverse/workflows/validator.py` - Workflow validator
- `tests/test_workflows.py` - 50 workflow tests

## Test Results

```
50 passed in 0.12s
```
