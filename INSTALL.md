# Installation

## Requirements

- Python 3.11 or higher
- pip (Python package manager)

## Quick Install

```bash
# Clone the repository
git clone <repository-url>
cd ios-reverse-kaiser

# Install in development mode
pip install -e .

# Verify installation
python -c "import ios_reverse; print(ios_reverse.__version__)"
```

## Dependencies

Core dependencies are installed automatically:
- Python 3.11+
- Standard library modules (json, pathlib, dataclasses, etc.)

No external dependencies are required for core functionality.

## Optional Tools

### macOS Tools (Optional)

Install Xcode Command Line Tools for enhanced functionality:

```bash
xcode-select --install
```

This provides:
- `otool` - Mach-O analysis
- `plutil` - plist parsing
- `codesign` - Code signing verification
- `nm` - Symbol listing

### Commercial Tools (Optional)

For full functionality:

#### IDA Pro
1. Purchase IDA Pro license
2. Install IDA Pro
3. Install ida-pro-mcp server
4. Configure in TOOLS.md

#### Ghidra
1. Download from https://ghidra-sre.org/
2. Install Ghidra
3. Configure headless server

### ipsw Tool (Optional)

For enhanced Mach-O inspection:
```bash
# Download from https://github.com/nicko170/ipsw
# or
brew install ipsw  # macOS
```

## Verification

### Test Installation

```bash
# Run test suite
python -m pytest tests/ -v

# Test core imports
python -c "
from ios_reverse.workflows import list_intents
from ios_reverse.capabilities import list_capabilities
from ios_reverse.agents import list_agents
print('Intents:', list_intents())
print('Capabilities:', len(list_capabilities()))
print('Agents:', list_agents())
"

# Check tool health
python -c "
from ios_reverse.adapters import get_health_service
print(get_health_service().generate_report())
"
```

### Test Analysis (Synthetic)

```bash
# Create synthetic IPA for testing
mkdir -p test_app/Payload
echo "Mach-O binary content" > test_app/Payload/test.app/test_binary
echo '<?xml version="1.0"?><plist version="1.0"><dict><key>CFBundleExecutable</key><string>test_binary</string></dict></plist>' > test_app/Payload/test.app/Info.plist
cd test_app && zip -r test.ipa Payload && cd ..
/ios-reverse test.ipa unpack
```

## Configuration

Create `config.py` for customization:

```python
from ios_reverse.config import Config

config = Config()
config.WORKSPACE_ROOT = "my_workspace"
config.ENABLE_DEBUG = False
```

See [CONFIGURATION.md](CONFIGURATION.md) for all options.

## Uninstall

```bash
pip uninstall ios-reverse-kaiser
rm -rf workspace  # Optional: remove workspace
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
pip install -e .
```

### Permission Errors

On Linux/macOS:
```bash
chmod +x /path/to/script
```

### Python Version

Check Python version:
```bash
python --version  # Should be 3.11+
```

## Next Steps

1. Read [README.md](README.md) for quick start
2. Review [WORKFLOWS.md](WORKFLOWS.md) for available commands
3. Check [TOOLS.md](TOOLS.md) for optional tools
4. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for issues
