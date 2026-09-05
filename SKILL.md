# SKILL: IOS Reverse Engineering

**Purpose**: Evidence-driven iOS application reverse-engineering framework

## When to Use This Skill

Use `/ios-reverse` when:
- Analyzing iOS application (IPA) security
- Auditing network endpoints in iOS apps
- Reverse-engineering iOS authentication flows
- Detecting crypto implementations in iOS binaries
- Identifying anti-analysis protections in iOS apps
- Generating structured iOS analysis reports

Do NOT use for:
- Windows PE analysis (use PE-reverse-skill)
- Android analysis
- Binary modification/patching

## Slash Command Contract

```
/ios-reverse <target> <intent> [depth] [options]
```

### Core Syntax

```bash
# Basic analysis
/ios-reverse <ipa-file> unpack
/ios-reverse <ipa-file> inspect
/ios-reverse <ipa-file> dump
/ios-reverse <ipa-file> <intent>

# With depth
/ios-reverse <ipa-file> dump-full
/ios-reverse <ipa-file> network-deep

# Case operations
/ios-reverse status <case-id>
/ios-reverse resume <case-id>
```

## Routing Invariants

### 1. Narrow Request = Narrow Workflow

```
/ios-reverse App.ipa network
```
Must NOT:
- Run full crypto analysis
- Run anti-analysis detection
- Spawn all available agents

### 2. Depth Controls Budget, Not Intent

```
/ios-reverse App.ipa dump-full
```
Means "stronger declared coverage" not "run every tool blindly."

Depth levels:
- `quick` = 1 agent task
- `standard` = 2 agent tasks
- `deep` = 4 agent tasks
- `full` = 6 agent tasks

### 3. Intent Selection

| Intent | Purpose |
|--------|---------|
| `unpack` | Extract IPA |
| `inspect` | Bundle inventory |
| `dump` | Standard analysis |
| `macho` | Mach-O binary analysis |
| `objc` | Objective-C metadata |
| `swift` | Swift metadata |
| `network` | Network endpoints |
| `login-flow` | Authentication analysis |
| `crypto` | Crypto primitives |
| `anti-analysis` | Anti-debug detection |
| `report` | Generate report |

## Evidence/Claim Discipline

### Evidence vs Claim

**Evidence**: Direct observation from analysis
```
STRING_HINT: "/auth/login" found in binary
STRUCTURAL: AppDelegate contains network method
REFERENCE: URL scheme "myapp://" declared
```

**Claim**: Analytical interpretation
```
"The app authenticates users via POST to /auth/login"
```

### Claim States

| State | Meaning |
|-------|---------|
| `verified` | Confirmed by multiple evidence |
| `inferred` | Reasonable conclusion from evidence |
| `suspected` | Possible but unconfirmed |
| `rejected` | Contradicted by evidence |
| `unknown` | Insufficient data |

### Traceability

```
Report → Claim → Evidence → Capability → Tool → Artifact
```

Every claim in a report traces to specific evidence.

## Filesystem Source of Truth

**Critical**: The filesystem is the source of truth.

```
workspace/cases/<case-id>/
├── CASE.md              # Case identity
├── STATUS.md            # Current state
├── checkpoints/         # Execution snapshots
├── evidence/           # Analytical evidence
│   └── raw/           # Immutable source observations
├── claims/            # Analytical claims
├── artifacts/         # Derived artifacts
└── provenance/       # Evidence lineage
```

Conversation context is CACHE only. On resume, fresh session reads filesystem.

## Blocked/Deferred Capabilities

| Capability | Status | Reason |
|------------|--------|--------|
| `ios.decompile` | BLOCKED | Requires commercial decompiler |
| `ios.ida` | BLOCKED | Requires IDA Pro + MCP server |
| `ios.runtime` | BLOCKED | Requires runtime provider |

These are documented honestly. Workflow selection will indicate BLOCKED status.

## Workflow Reference

See [WORKFLOWS.md](WORKFLOWS.md) for:
- All 15 canonical workflows
- DAG diagrams
- Coverage policies
- Tool escalation rules

## Tool Adapter Reference

See [TOOLS.md](TOOLS.md) for:
- Available tool adapters
- Platform availability
- Required/optional classification
- Configuration options

## Case Model

See [CASE_MODEL.md](CASE_MODEL.md) for:
- Case directory structure
- Checkpoint format
- Resume mechanism
- Context pack structure

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for:
- Layered architecture
- Component responsibilities
- Agent selection
- Provenance tracking

## Extension Rules

### Adding New Capability

1. Define in `ios_reverse/capabilities/`
2. Register in capability registry
3. Add provenance output
4. Write tests
5. Document in capability reference

### Adding New Workflow

1. Define DAG in `ios_reverse/workflows/registry.py`
2. Add scope leakage rules to validator
3. Register workflow status
4. Write routing tests
5. Document in WORKFLOWS.md

### Adding New Adapter

1. Implement `ToolAdapterContract`
2. Add fallback chain to selector
3. Register in health service
4. Test failure modes
5. Document in TOOLS.md

**Prohibited**: Adding tool calls directly in workflows. All external tool access goes through adapters.

## Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for:
- Tool path configuration
- Timeout settings
- Case workspace location
- Optional provider settings

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Tool availability issues
- Case lock problems
- Resume failures
- Platform-specific issues

## Quality Gates

This skill enforces:

1. **Narrow Scope**: Unpack workflow never runs network analysis
2. **Evidence Integrity**: Claims trace to verifiable evidence
3. **Immutable Raw**: Raw evidence never modified
4. **Checkpoint Persistence**: State survives session termination
5. **Tool Fallback**: Graceful degradation when tools unavailable
6. **Coverage Honesty**: No false 100% coverage reports
