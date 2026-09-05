# Changelog

All notable changes to IOS REVERSE KAISER will be documented in this file.

## [0.2.0] - 2026-09-05 - Deep Analysis Release

### Added

#### Deep Analysis Adapters (P14-P17)
- **IDA Pro MCP Adapter**: Full IDA Pro integration via ida-pro-mcp server
- **Ghidra Headless Adapter**: Batch analysis via Ghidra's headless analyzer
- **Rizin Adapter**: Integration with rizin/radare2 CLI
- **Runtime Provider Adapter**: Frida and LLDB integration for iOS runtime analysis
- **Decompiler Manager**: Unified decompiler interface with provider selection

#### New Capabilities
- **ida.analysis**: IDA function listing, imports/exports, strings, xrefs
- **ida.target_verification**: Binary target verification for IDA sessions
- **decompiler.analyze**: Unified decompilation across IDA/Ghidra/rizin
- **decompiler.xref_analysis**: Cross-reference analysis
- **runtime.analysis**: Runtime analysis (classes, modules, methods)
- **runtime.session**: Runtime session management
- **static.sdk_fingerprinting**: Third-party SDK detection (20+ SDKs)
- **static.secret_scanning**: API key, JWT, connection string detection
- **static.keychain_analysis**: Keychain API usage detection
- **static.jailbreak_detection**: Jailbreak indicator detection
- **static.obfuscation_detection**: Code obfuscation analysis

#### Ghidra Scripts
- **FunctionExporter.java**: Export all functions to JSON
- **XrefExporter.java**: Export cross-references to JSON
- **StringExporter.java**: Export strings to JSON
- **DecompilerExporter.java**: Export decompiled pseudocode

#### Workflow Updates
- **ios.ida**: Changed from BLOCKED to IMPLEMENTED
- **ios.decompile**: Changed from BLOCKED to IMPLEMENTED
- **ios.runtime**: Changed from BLOCKED to PARTIAL (requires device)

### Changed

- **WorkflowStatus enum**: Added PARTIAL status for workflows with environment requirements
- **SOURCE_PARITY.md**: Updated with new adapter/capability mappings

### Source Parity

| Source | Relevant | PARITY | PARTIAL | MISSING |
|--------|----------|--------|---------|---------|
| Patr1ck-S | 29 | 29 | 0 | 0 |
| anatoly505 | 46 | 46 | 0 | 0 |
| DamonZS | 8 | 7 | 1 | 0 |
| **TOTAL** | **83** | **82** | **1** | **0** |

### Known Limitations (Updated)

- Decompile workflow requires IDA Pro, Ghidra, or rizin installed
- Runtime workflow requires jailbroken device + Frida/LLDB
- File locking is best-effort on Windows
- Encrypted binaries cannot be analyzed without decryption

---

## [0.1.0] - 2024-09-04 - Initial Functional Preview

### Added

#### Core Engine
- **Evidence-driven architecture**: All claims trace to verifiable evidence
- **Provenance tracking**: Full lineage from artifact to finding
- **Immutable raw evidence**: Raw observations never modified
- **Claim lifecycle**: verified → inferred → suspected → rejected

#### Workflow Layer
- **15 canonical workflows**: unpack, inspect, dump, macho, objc, swift, network, login-flow, crypto, anti-analysis, report, full
- **Depth profiles**: quick (1 agent), standard (2), deep (4), full (6)
- **Scope leakage prevention**: Narrow request = narrow workflow
- **Workflow validation**: DAG structure, cycle detection, dependency validation

#### Multi-Agent System
- **8 agent roles**: planner, artifact-analyst, objc-swift-analyst, binary-analyst, network-analyst, evidence-validator, coverage-auditor, reporter
- **Budget enforcement**: No unbounded spawning
- **Adaptive selection**: Based on workflow complexity
- **Agent handoffs**: Through persisted artifacts

#### Case Persistence
- **Checkpoint/resume**: Full state persistence
- **Resume engine**: Stale detection, corruption recovery
- **Context pack**: Bounded conversation context
- **Case workspace**: Structured directory layout

#### Tool Adapters
- **Canonical contract**: ToolAdapterContract for all adapters
- **Fallback chains**: Graceful degradation when tools unavailable
- **Tool selector**: Best available tool selection
- **Health service**: Availability monitoring
- **8 availability states**: available, unavailable, degraded, etc.

#### Reliability
- **571 tests passing**: Comprehensive test suite
- **Reliability scorecard**: Categorical status validation
- **Determinism**: Same inputs = same outputs
- **Idempotency**: Re-running doesn't corrupt state

### Capabilities

#### Foundation
- Artifact detection
- File operations

#### Bundle
- IPA validation
- IPA extraction
- Bundle inventory

#### Mach-O
- Header parsing
- Load commands
- Segments
- Symbols
- Imports/Exports

#### Binary Analysis
- String extraction
- Symbol analysis
- Import analysis
- Export analysis

#### Objective-C
- Class list
- Method list
- Selector extraction
- Metadata extraction

#### Swift
- Type references
- Metadata extraction
- Symbol demangling

#### Network Analysis
- Endpoint detection
- URL scheme extraction
- TLS configuration
- Architecture mapping
- Callflow analysis

#### Cryptography
- Primitive detection
- Key management analysis
- Algorithm identification

#### Anti-Analysis
- Debugger detection
- Tamper detection
- Emulator detection

#### Coverage
- Target tracking
- Coverage calculation
- Gap identification

### Platforms

| Platform | Status |
|----------|--------|
| Windows | ✓ Core + tools |
| Linux | ✓ Core + tools |
| macOS | ✓ Core + tools + native |

### Known Limitations

- Decompile workflow requires IDA/Ghidra
- Runtime workflow requires jailbreak + Frida
- File locking is best-effort on Windows
- Encrypted binaries cannot be analyzed without decryption

### Documentation

- README.md
- SKILL.md
- ARCHITECTURE.md
- WORKFLOWS.md
- AGENTS.md
- CASE_MODEL.md
- TOOLS.md
- CONFIGURATION.md
- TROUBLESHOOTING.md
- KNOWN_LIMITATIONS.md
- INSTALL.md
- CHANGELOG.md

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- MAJOR version: Incompatible API changes
- MINOR version: New functionality (backwards-compatible)
- PATCH version: Bug fixes

Current: **0.2.0** (Deep Analysis Release)

---

## Release History

| Version | Date | Status |
|---------|------|--------|
| 0.2.0 | 2026-09-05 | Deep Analysis Release |
| 0.1.0 | 2024-09-04 | Initial Functional Preview |
