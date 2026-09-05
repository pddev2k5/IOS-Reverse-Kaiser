# Contributing

## Overview

Contributions to IOS REVERSE KAISER are welcome. This document outlines guidelines for adding new capabilities, workflows, agents, and adapters.

## Extension Rules

### Adding a New Capability

1. **Define in `ios_reverse/capabilities/`**
   - Create `new_cap.py`
   - Implement `Capability` abstract base
   - Add provenance output

2. **Register in capability registry**
   ```python
   # ios_reverse/capabilities/registry.py
   CAPABILITIES = {
       "new.cap": NewCapability(),
       ...
   }
   ```

3. **Add to workflow DAG**
   ```python
   # ios_reverse/workflows/registry.py
   WORKFLOWS = {
       "ios.workflow": {
           "nodes": [
               {"capability_id": "new.cap", ...},
           ]
       }
   }
   ```

4. **Write tests**
   - Unit tests in `tests/test_capabilities_*.py`
   - Integration tests

5. **Document**
   - Add to capability reference
   - Update WORKFLOWS.md if needed

### Adding a New Workflow

1. **Define DAG in workflow registry**
   ```python
   # ios_reverse/workflows/registry.py
   WORKFLOWS = {
       "ios.new_workflow": {
           "intent": Intent.NEW_WORKFLOW,
           "nodes": [...],
           "scope_rules": {...}
       }
   }
   ```

2. **Add scope leakage rules**
   ```python
   # ios_reverse/workflows/validator.py
   WORKFLOW_SCOPE_LEAKAGE = {
       "ios.new_workflow": {
           "allowed": [...],
           "forbidden": [...]
       }
   }
   ```

3. **Register status**
   - IMPLEMENTED
   - PARTIAL
   - BLOCKED

4. **Write routing tests**
   - Verify scope leakage prevention
   - Verify depth handling

5. **Document**
   - Add to WORKFLOWS.md
   - Update SKILL.md

### Adding a New Agent

1. **Define role in agent registry**
   ```python
   # ios_reverse/agents/registry.py
   AGENT_ROLES = {
       "new-agent": {
           "purpose": "...",
           "capabilities": [...]
       }
   }
   ```

2. **Add to selector logic**
   ```python
   # ios_reverse/agents/selector.py
   def _select_for_workflow(self, workflow, depth):
       if workflow == "ios.new":
           return ["planner", "new-agent"]
   ```

3. **Write tests**
   - Agent selection tests
   - Budget enforcement tests

4. **Document**
   - Add to AGENTS.md
   - Update architecture docs

### Adding a New Adapter

1. **Implement ToolAdapterContract**
   ```python
   # ios_reverse/adapters/new_tool.py
   class NewToolAdapter(ToolAdapterContract):
       @property
       def adapter_id(self): return "new_tool"

       def availability(self): return ToolAvailability.AVAILABLE

       def execute(self, capability, inputs, context):
           # Implementation
           ...
   ```

2. **Add to tool selector**
   ```python
   # ios_reverse/adapters/selector.py
   FALLBACK_CHAINS = {
       "capability": ["new_tool", "fallback"],
       ...
   }
   ```

3. **Register in health service**
   ```python
   # ios_reverse/adapters/selector.py
   def __init__(self):
       self._adapters["new_tool"] = NewToolAdapter()
   ```

4. **Write tests**
   - Availability tests
   - Fallback tests
   - Failure classification tests

5. **Document**
   - Add to TOOLS.md
   - Update platform matrix

## Prohibited Changes

### DO NOT

1. **Add tool calls directly in workflows**
   - All external tool access goes through adapters
   - No hardcoded subprocess calls

2. **Bypass capability layer**
   - Workflows must go through capabilities
   - No direct tool usage from agents

3. **Modify raw evidence**
   - Raw evidence is immutable
   - Derived evidence references raw

4. **Hardcode paths**
   - Use configuration
   - Make portable

5. **Skip testing**
   - All new code needs tests
   - Run test suite before PR

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add tests
5. Run test suite: `python -m pytest tests/`
6. Update documentation
7. Submit PR

## Code Style

- Follow PEP 8
- Use type hints where practical
- Add docstrings to public APIs
- Keep functions focused

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_capabilities_new.py

# Run with coverage
python -m pytest tests/ --cov=ios_reverse

# Run fast tests only
python -m pytest tests/ -m "not slow"
```

## Questions

For questions about contributing:
[INSERT CONTACT INFORMATION]
