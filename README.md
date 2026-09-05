# IOS REVERSE KAISER

**iOS Reverse Engineering Workflow Framework**

[![Tests](https://img.shields.io/badge/tests-603%20passed-green)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

## What is IOS REVERSE KAISER?

IOS REVERSE KAISER is an evidence-driven iOS reverse-engineering workflow framework. It systematically analyzes iOS applications (IPA files) using layered capabilities that produce verifiable, provenance-tracked analytical findings.

## What Problem Does It Solve?

- **Structured Analysis**: Transforms ad-hoc reverse engineering into repeatable, auditable workflows
- **Evidence Tracking**: Every analytical claim traces back to verifiable evidence
- **Resumable Sessions**: Analysis can be interrupted and resumed without losing progress
- **Multi-Agent Orchestration**: Adaptive agent selection based on workflow complexity
- **Tool Integration**: Graceful fallback when commercial tools (IDA, Ghidra) are unavailable

## Target vs Host Platform

| Component | Platform |
|-----------|----------|
| **Analysis Target** | iOS applications (IPA files) |
| **Framework Host** | Windows, Linux, macOS |

Core static analysis works on all host platforms. macOS-native tools (otool, codesign, plutil) enrich analysis when available.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Analyze an IPA
/ios-reverse App.ipa unpack
/ios-reverse App.ipa inspect
/ios-reverse App.ipa dump
/ios-reverse App.ipa network
/ios-reverse App.ipa report

# Resume a case
/ios-reverse status <case-id>
/ios-reverse resume <case-id>
```

## Core Commands

### Analysis Workflows

| Command | Purpose | Status |
|---------|---------|--------|
| `unpack` | Extract IPA contents | ✓ IMPLEMENTED |
| `inspect` | Basic bundle inspection | ✓ IMPLEMENTED |
| `dump` | Standard analysis dump | ✓ IMPLEMENTED |
| `macho` | Mach-O binary analysis | ✓ IMPLEMENTED |
| `objc` | Objective-C metadata | ✓ IMPLEMENTED |
| `swift` | Swift metadata extraction | ✓ IMPLEMENTED |
| `network` | Network endpoint analysis | ✓ IMPLEMENTED |
| `login-flow` | Authentication callflow | ✓ IMPLEMENTED |
| `crypto` | Crypto primitive detection | ✓ IMPLEMENTED |
| `anti-analysis` | Anti-analysis detection | ✓ IMPLEMENTED |
| `decompile` | Decompiled pseudocode | ✓ IMPLEMENTED |
| `ida` | IDA Pro integration | ✓ IMPLEMENTED |
| `runtime` | Runtime instrumentation | ◐ PARTIAL |
| `report` | Generate analysis report | ✓ IMPLEMENTED |

### Depth Levels

| Depth | Budget | Use Case |
|-------|--------|----------|
| `quick` | 1 agent | Fast surface scan |
| `standard` | 2 agents | Standard analysis |
| `deep` | 4 agents | Thorough investigation |
| `full` | 6 agents | Comprehensive coverage |

**Note**: Depth controls agent budget, not tool aggressiveness. `full` means stronger declared coverage, not "run every tool blindly."

### Case Operations

```bash
/ios-reverse status <case-id>  # View case status
/ios-reverse plan <case-id>    # View execution plan
/ios-reverse resume <case-id>  # Resume interrupted case
```

## Architecture

```
Slash Command
      ↓
Intent + Depth Resolver
      ↓
Workflow Registry (15 workflows)
      ↓
Agent Selector (budget-aware)
      ↓
Capabilities (50+ operations)
      ↓
Tool Adapters (fallback-aware)
      ↓
Evidence / Claims / Provenance
      ↓
Coverage Tracking
      ↓
Case Workspace (checkpoint/resume)
      ↓
Reports
```

**Key Invariants**:
- Narrow request = narrow workflow
- Capability ≠ Adapter (tools are swappable)
- Workflow controls scope, not agents
- Evidence ≠ Claim (observation ≠ interpretation)
- Raw evidence is immutable

## Resume Mechanism

Analysis state persists to filesystem:

```
workspace/cases/<case-id>/
├── CASE.md           # Case metadata
├── STATUS.md         # Current state
├── checkpoints/      # Execution snapshots
├── evidence/         # Analytical evidence
├── claims/           # Analytical claims
└── artifacts/       # Derived artifacts
```

Interruption → Resume:
1. Fresh session reads `/ios-reverse resume <case-id>`
2. Validates checkpoint integrity
3. Identifies stale nodes
4. Reuses valid completed work
5. Continues execution

## Optional Tools

| Tool | Purpose | Required? |
|------|---------|-----------|
| Python core | Core parsing | ✓ Yes |
| ipsw | Mach-O inspection | No |
| otool | Mach-O commands (macOS) | No |
| plutil | plist parsing (macOS) | No |
| codesign | Code signing verification | No |
| nm | Symbol listing (macOS) | No |
| IDA Pro | Deep analysis + decompilation | No |
| ida-pro-mcp | IDA MCP server | No |
| Ghidra | Headless decompilation | No |
| rizin | CLI binary analysis | No |
| Frida | Runtime instrumentation | No |
| strings | String extraction | No |
| IDA Pro | Deep disassembly | No |
| Ghidra | Alternative disassembly | No |
| radare2/rizin | CLI reversing | No |

Core workflows work without optional tools. Their absence is truthfully reported.

## What IS NOT Included

- ✗ Windows/Android/other platform analysis
- ✗ Automatic source code reconstruction
- ✗ Commercial tool licenses (IDA, Ghidra require separate purchase)
- ✗ Runtime analysis on physical devices (without jailbreak)
- ✗ Binary patching/modification

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [WORKFLOWS.md](WORKFLOWS.md) - Workflow reference
- [AGENTS.md](AGENTS.md) - Agent roles
- [CASE_MODEL.md](CASE_MODEL.md) - Case workspace model
- [TOOLS.md](TOOLS.md) - Tool adapter reference
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration options
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) - Known limitations

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run fast tests only
python -m pytest tests/ -m "not slow"

# Run specific category
python -m pytest tests/test_workflows.py
```

**Test Results**: 571 passed, 2 skipped

## Version

**0.1.0** - Initial functional preview release

## License

See [ATTRIBUTION.md](ATTRIBUTION.md) for source provenance and licensing information.
