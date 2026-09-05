# Troubleshooting

## Common Issues

### Tool Unavailable

**Symptom**: Warning about missing tool

**Cause**: Optional tool not installed

**Solution**:
```bash
# Verify tool status
python -c "from ios_reverse.adapters import get_health_service; print(get_health_service().generate_report())"

# Install optional tools if needed
# macOS tools (otool, plutil, codesign) come with Xcode
```

---

### IDA Session Required

**Symptom**: `ios.ida` workflow shows BLOCKED

**Cause**: IDA Pro not installed or MCP server not running

**Solution**: This workflow requires:
1. IDA Pro installed
2. `ida-pro-mcp` server running
3. Valid IDA license

For static analysis without IDA, use `ios.dump` or `ios.macho`.

---

### IDA Target Mismatch

**Symptom**: IDA analysis shows different results than expected

**Cause**: IDA database not synced with current binary

**Solution**:
1. Close IDA
2. Delete `.idb` file
3. Re-run analysis

---

### Ghidra Unavailable

**Symptom**: `ios.ghidra` shows unavailable

**Cause**: Ghidra not installed or headless server not running

**Solution**:
1. Install Ghidra from https://ghidra-sre.org/
2. Start headless server: `ghidraRun -analysisServer`

---

### macOS Native Tool Missing

**Symptom**: Warnings about `otool`, `plutil`, etc.

**Cause**: Xcode Command Line Tools not installed

**Solution**:
```bash
xcode-select --install
```

---

### Invalid IPA

**Symptom**: `IPA validation failed`

**Cause**: File is not a valid IPA

**Solution**:
1. Verify file is a valid IPA (ZIP archive)
2. Check file is not encrypted
3. Try re-downloading from App Store

---

### Encrypted/Limited Binary

**Symptom**: Analysis produces limited results

**Cause**: App is encrypted or uses App Store FairPlay

**Solution**: Analysis can only work with decrypted binaries. Use tools like:
- `frida-ios-dump` (jailbroken devices)
- `Clutch` (jailbroken devices)
- `dumpdecrypted` (jailbroken devices)

---

### Unsupported Swift Metadata

**Symptom**: Swift analysis incomplete

**Cause**: App uses newer Swift ABI or stripped symbols

**Solution**: This is a known limitation. Static analysis has bounds with stripped binaries.

---

### Case Lock

**Symptom**: Cannot modify case

**Cause**: Case is locked by another process

**Solution**:
```bash
# Check for lock
cat workspace/cases/<case-id>/.lock

# If stale, remove lock
rm workspace/cases/<case-id>/.lock
```

**Warning**: Only remove lock if you're sure no other process is using the case.

---

### Stale Checkpoint

**Symptom**: Resume shows outdated state

**Cause**: Checkpoint references missing files

**Solution**:
```bash
# Check latest checkpoint
cat workspace/cases/<case-id>/checkpoints/latest.json

# List available checkpoints
ls workspace/cases/<case-id>/checkpoints/

# If latest is corrupted, point to previous
```

---

### Corrupted Latest Pointer

**Symptom**: `latest.json` points to non-existent checkpoint

**Cause**: Checkpoint file was deleted or corrupted

**Solution**:
1. List valid checkpoints: `ls workspace/cases/<case-id>/checkpoints/*.json`
2. Update `latest.json` to point to valid checkpoint
3. Or delete case and restart

---

### Resume Issues

**Symptom**: Resume doesn't pick up where it left off

**Cause**: Checkpoint state inconsistent

**Solution**:
1. Check checkpoint integrity
2. Verify evidence files exist
3. Review case STATUS.md
4. If corrupted, start fresh case

---

### Partial Coverage

**Symptom**: Coverage shows < 100% on full workflow

**Cause**: Some targets could not be analyzed

**Solution**: This is expected. Coverage reflects actual analysis:
- `covered`: Successfully analyzed
- `partial`: Partially analyzed
- `failed`: Analysis failed
- `not_attempted`: Skipped due to budget

---

### Partial Case Report

**Symptom**: Report shows incomplete data

**Cause**: Case was interrupted before completion

**Solution**: Resume the case:
```bash
/ios-reverse resume <case-id>
```

---

### Open Conflicts

**Symptom**: Report shows unresolved claim conflicts

**Cause**: Evidence validator found conflicting evidence

**Solution**:
1. Review conflicting claims in `claims/` directory
2. Add additional evidence to resolve
3. Re-run validator

---

### Slow Analysis

**Symptom**: Analysis taking too long

**Cause**: Large binary, network timeout, or tool performance

**Solution**:
1. Use `quick` depth for fast scan
2. Increase timeout in configuration
3. Check tool health

---

### Memory Issues

**Symptom**: Out of memory errors

**Cause**: Large binary or deep analysis

**Solution**:
1. Use smaller depth (`quick` or `standard`)
2. Analyze specific components only
3. Increase system memory

---

### Permission Denied

**Symptom**: Cannot read/write workspace

**Cause**: File permission issues

**Solution**:
```bash
# Fix permissions (Linux/macOS)
chmod -R 755 workspace/

# On Windows, run as administrator or fix in Explorer
```

---

### Path Issues

**Symptom**: Cannot find IPA or workspace

**Cause**: Relative/absolute path confusion

**Solution**: Use absolute paths:
```bash
# Absolute path
/ios-reverse /full/path/to/App.ipa unpack

# Or ensure working directory is correct
cd /path/to/workspace
/ios-reverse App.ipa unpack
```

---

### Import Errors

**Symptom**: `ModuleNotFoundError`

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -e .
```

---

### Version Mismatch

**Symptom**: Unexpected behavior or errors

**Cause**: Version incompatibility

**Solution**: Check version:
```bash
python -c "import ios_reverse; print(ios_reverse.__version__)"
```

---

## Getting Help

### Check Status

```bash
# View case status
/ios-reverse status <case-id>

# View execution plan
/ios-reverse plan <case-id>
```

### Debug Mode

Enable debug logging:
```python
# In config.py
ENABLE_DEBUG = True
DEBUG_AGENTS = True
DEBUG_TOOLS = True
```

### Health Check

```python
from ios_reverse.adapters import get_health_service
print(get_health_service().generate_report())
```

### Test Suite

Run tests to verify installation:
```bash
python -m pytest tests/ -v
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `TOOL_NOT_FOUND` | Required tool missing | Install tool or use fallback |
| `TIMEOUT` | Operation timed out | Increase timeout |
| `PARSE_ERROR` | Cannot parse output | Check tool version |
| `PERMISSION_ERROR` | Access denied | Fix permissions |
| `LOCK_HELD` | Case locked | Wait or remove lock |
| `CHECKPOINT_INVALID` | Checkpoint corrupted | Use previous checkpoint |
