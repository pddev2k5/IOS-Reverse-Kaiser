# IOS REVERSE KAISER — Intent Model

## Intent + Depth Architecture

All user requests normalize to intent + depth before routing to workflows.

```
User Input
    │
    ├── /ios-reverse app.ipa unpack
    │       ├── Intent: unpack
    │       └── Depth: standard (default)
    │
    ├── /ios-reverse app.ipa dump-full
    │       ├── Intent: dump
    │       └── Depth: full
    │
    ├── /ios-reverse app.ipa decompile-deep
    │       ├── Intent: decompile
    │       └── Depth: deep
    │
    └── /ios-reverse app.ipa network-full
            ├── Intent: network
            └── Depth: full
```

---

## Supported Intents

| Intent | Description | Default Depth | Aliases |
|--------|-------------|---------------|---------|
| `unpack` | Extract IPA contents | quick | extract |
| `inspect` | Surface-level examination | quick | examine |
| `dump` | Comprehensive extraction | standard | inventory |
| `decompile` | Binary decompilation | standard | disassemble |
| `macho` | Mach-O binary analysis | standard | mach-o |
| `objc` | Objective-C metadata | standard | objective-c |
| `swift` | Swift metadata/demangling | standard | — |
| `network` | Network analysis | standard | net, http |
| `login-flow` | Authentication flow | standard | auth, login |
| `crypto` | Crypto identification | standard | crypt, encryption |
| `anti-analysis` | Anti-RE detection | quick | anti-tamper |
| `ida` | IDA-specific analysis | deep | ida-pro |
| `runtime` | Runtime instrumentation | deep | dynamic |
| `report` | Generate findings | standard | — |
| `full` | Complete coverage | full | all, complete |

---

## Depth Semantics

### quick
- Minimal useful analysis
- Essential checks only
- No optional tools
- No coverage auditing

**Example**: `unpack quick` → Just extract the IPA

### standard
- Normal requested analysis
- Core tooling
- Standard coverage
- Basic validation

**Example**: `dump standard` → Standard dump workflow

### deep
- Deeper correlation
- Tool escalation
- Cross-reference analysis
- Extended validation

**Example**: `network deep` → Network analysis with decompilation assist

### full
- Coverage-oriented completion
- Strict validation
- Measurable completeness
- All eligible scope covered

**Example**: `dump full` → Full dump with coverage auditing

---

## Alias Normalization

| Alias | Normalizes To |
|-------|--------------|
| `extract` | `unpack` |
| `examine` | `inspect` |
| `inventory` | `dump` |
| `disassemble` | `decompile` |
| `mach-o` | `macho` |
| `objective-c` | `objc` |
| `net` | `network` |
| `http` | `network` |
| `auth` | `login-flow` |
| `login` | `login-flow` |
| `crypt` | `crypto` |
| `encryption` | `crypto` |
| `anti-tamper` | `anti-analysis` |
| `ida-pro` | `ida` |
| `dynamic` | `runtime` |
| `all` | `full` |
| `complete` | `full` |

---

## Intent → Workflow Mapping

| Intent | Primary Workflow | Depth Profiles |
|--------|-----------------|----------------|
| unpack | `workflow-unpack` | quick, standard |
| inspect | `workflow-inspect` | quick |
| dump | `workflow-dump` | standard, full |
| decompile | `workflow-decompile` | standard, full |
| macho | `workflow-macho` | quick, standard, deep, full |
| objc | `workflow-objc` | quick, standard, deep |
| swift | `workflow-swift` | quick, standard, deep |
| network | `workflow-network` | quick, standard, full |
| login-flow | `workflow-login` | standard, deep |
| crypto | `workflow-crypto` | quick, standard, deep |
| anti-analysis | `workflow-anti` | quick, standard |
| ida | `workflow-ida` | deep, full |
| runtime | `workflow-runtime` | deep, full |
| report | `workflow-report` | standard, full |
| full | `workflow-full` | full |

---

## Depth Extension Model

Workflows can extend base depth profiles:

```yaml
workflow-dump:
  base_depths: [standard]
  extensions:
    full:
      additional_nodes:
        - all_macho_slices
        - deep_objc_extraction
        - deep_swift_extraction
        - all_frameworks
        - all_extensions
        - coverage_audit
```

This prevents workflow duplication while enabling depth-aware execution.

---

## Complexity Scoring

Complexity determines orchestration tier.

### Scoring Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| artifact_count | 1.0 | Number of artifacts |
| depth_multiplier | 2.0 | quick=1, standard=2, deep=3, full=5 |
| domains | 1.5 | Number of analysis domains |
| binary_count | 1.0 | Embedded binaries count |
| decompilation_needed | 3.0 | Requires Ghidra/IDA |
| xref_analysis | 2.0 | Cross-reference analysis |
| callflow_needed | 2.5 | Call flow reconstruction |
| runtime_needed | 3.0 | Runtime instrumentation |
| coverage_audit | 2.0 | Full coverage required |

### Complexity → Tier Mapping

| Score Range | Tier | Agents |
|-------------|------|--------|
| 0-10 | simple | executor |
| 11-25 | moderate | executor + validator |
| 26-50 | complex | planner + specialists + validator |
| 51+ | full | planner + specialists + validator + auditor + reporter |

---

## Routing Examples

### Example 1: Simple Unpack
```
Input: /ios-reverse app.ipa unpack
Intent: unpack
Depth: standard
Complexity: 5 (simple)
Tier: simple
Workflow: workflow-unpack
```

### Example 2: Standard Dump
```
Input: /ios-reverse app.ipa dump
Intent: dump
Depth: standard
Complexity: 15 (moderate)
Tier: moderate
Workflow: workflow-dump (standard profile)
```

### Example 3: Full Dump
```
Input: /ios-reverse app.ipa dump-full
Intent: dump
Depth: full
Complexity: 40 (complex)
Tier: complex
Workflow: workflow-dump (full profile with coverage audit)
```

### Example 4: Network Full
```
Input: /ios-reverse app.ipa network-full
Intent: network
Depth: full
Complexity: 35 (complex)
Tier: complex
Workflow: workflow-network (full profile)
```

### Example 5: Full Analysis
```
Input: /ios-reverse app.ipa full
Intent: full
Depth: full
Complexity: 80 (full)
Tier: full
Workflow: workflow-full
```

---

## Critical Routing Rule

**Narrow Request = Narrow Execution**

The router MUST NOT automatically expand scope:

- `unpack` must NOT invoke network analysis
- `unpack` must NOT invoke crypto analysis
- `dump` must NOT invoke runtime instrumentation
- `dump` must NOT invoke IDA analysis

Scope expansion only occurs:
1. When explicitly requested (e.g., `dump-full`)
2. When workflow dependencies require it
3. When user confirms expansion

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the intent + depth routing model.*
