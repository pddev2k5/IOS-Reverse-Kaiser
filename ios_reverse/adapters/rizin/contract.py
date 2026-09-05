"""
Rizin/radare2 Adapter for IOS REVERSE KAISER.

Provides integration with rizin (fork of radare2) CLI.

Maturity Level: L1 (Contract + Implementation skeleton)
Target Level: L3 (Kaiser integration)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
import json
import subprocess
from pathlib import Path

from ios_reverse.adapters.contract import (
    ToolAdapterContract,
    SubprocessAdapterContract,
    ToolAvailability,
    ToolRole,
    FailureClassification,
    AdapterHealth,
    AdapterExecutionResult,
)


@dataclass
class RizinFunction:
    """Rizin function record."""
    offset: int
    name: str
    size: int
    cc: int = 0  # Cyclomatic complexity


@dataclass
class RizinXref:
    """Rizin cross-reference."""
    from_addr: int
    to_addr: int
    type: str


@dataclass
class RizinImport:
    """Rizin import record."""
    ordinal: int
    name: str
    plt: int


@dataclass
class RizinExport:
    """Rizin export record."""
    ordinal: int
    name: str
    vaddr: int


class RizinAdapter(SubprocessAdapterContract):
    """
    Rizin CLI adapter.

    Uses rizin in batch/pipe mode for analysis.

    Required Environment:
    - rizin installed (apt install rizin, brew install rizin)

    Usage:
    rizin -q -c "aaa" binary
    """

    ADAPTER_ID = "rizin"
    VERSION = "0.1.0"
    TOOL_NAME = "rizin"

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {}
        self._current_binary: Optional[str] = None

    @property
    def adapter_id(self) -> str:
        return self.ADAPTER_ID

    @property
    def version(self) -> str:
        return self.VERSION

    @property
    def tool_name(self) -> str:
        return self.TOOL_NAME

    def availability(self) -> ToolAvailability:
        """Check if rizin is available."""
        try:
            result = subprocess.run(
                ["rizin", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ToolAvailability.AVAILABLE
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # Fallback to radare2
        try:
            result = subprocess.run(
                ["r2", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ToolAvailability.AVAILABLE
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

        return ToolAvailability.UNAVAILABLE

    def health_check(self) -> AdapterHealth:
        """Perform detailed health check."""
        availability = self.availability()

        health = AdapterHealth(
            availability=availability,
            adapter_id=self.adapter_id,
            tool_name=self.tool_name,
            tool_version=self.tool_version(),
            capabilities=list(self.supported_capabilities()),
        )

        if availability == ToolAvailability.UNAVAILABLE:
            health.reason = "rizin/radare2 not found in PATH"
            health.suggested_fallback = "python_parser"

        return health

    def tool_version(self) -> Optional[str]:
        """Detect rizin/radare2 version."""
        try:
            result = subprocess.run(
                ["rizin", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        try:
            result = subprocess.run(
                ["r2", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        return None

    def required_dependencies(self) -> List[Dict]:
        """List required dependencies."""
        return [
            {
                "name": "rizin",
                "required": True,
                "installed": self._check_rizin(),
            }
        ]

    def optional_dependencies(self) -> List[Dict]:
        """List optional dependencies."""
        return [
            {
                "name": "radare2 (fallback)",
                "required": False,
                "installed": self._check_radare2(),
            }
        ]

    def _check_rizin(self) -> bool:
        """Check if rizin is installed."""
        try:
            result = subprocess.run(
                ["rizin", "-v"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _check_radare2(self) -> bool:
        """Check if radare2 is installed."""
        try:
            result = subprocess.run(
                ["r2", "-v"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def supported_capabilities(self) -> Set[str]:
        """Set of capabilities this adapter supports."""
        return {
            "rizin.info",
            "rizin.sections",
            "rizin.imports",
            "rizin.exports",
            "rizin.symbols",
            "rizin.strings",
            "rizin.functions",
            "rizin.xrefs",
            "rizin.disassemble",
            "rizin.analyze",
        }

    def execute(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult:
        """Execute rizin capability."""
        import time
        start = time.time()

        if self.availability() == ToolAvailability.UNAVAILABLE:
            return AdapterExecutionResult(
                success=False,
                error="rizin/radare2 not available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        binary_path = inputs.get("binary_path") or context.get("binary_path")
        if not binary_path:
            return AdapterExecutionResult(
                success=False,
                error="binary_path required",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        self._current_binary = binary_path

        # Map capability to rizin command
        if capability_id == "rizin.info":
            return self._info(binary_path, start)
        elif capability_id == "rizin.sections":
            return self._sections(binary_path, start)
        elif capability_id == "rizin.imports":
            return self._imports(binary_path, start)
        elif capability_id == "rizin.exports":
            return self._exports(binary_path, start)
        elif capability_id == "rizin.symbols":
            return self._symbols(binary_path, start)
        elif capability_id == "rizin.strings":
            return self._strings(binary_path, start)
        elif capability_id == "rizin.functions":
            return self._functions(binary_path, start)
        elif capability_id == "rizin.xrefs":
            return self._xrefs(binary_path, inputs, start)
        elif capability_id == "rizin.disassemble":
            return self._disassemble(binary_path, inputs, start)
        elif capability_id == "rizin.analyze":
            return self._analyze(binary_path, start)

        return AdapterExecutionResult(
            success=False,
            error=f"Unknown capability: {capability_id}",
            failure_classification=FailureClassification.INVALID_INPUT,
        )

    def _run_rizin(self, binary_path: str, commands: List[str]) -> AdapterExecutionResult:
        """Run rizin with commands."""
        import time
        start = time.time()

        try:
            # Build command
            cmd = ["rizin", "-q", "-c", ";".join(commands), binary_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300000  # 5 minutes
            )

            duration_ms = int((time.time() - start) * 1000)

            return AdapterExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            return AdapterExecutionResult(
                success=False,
                error="rizin analysis timed out",
                duration_ms=int((time.time() - start) * 1000),
                failure_classification=FailureClassification.TIMEOUT,
                retryable=True,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                failure_classification=FailureClassification.PROCESS_ERROR,
            )

    def _info(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get binary info."""
        commands = ["iI", "iE", "il"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            result.normalized_output = self._parse_info(result.stdout)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _sections(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get sections."""
        commands = ["iS", "S"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            result.normalized_output = self._parse_sections(result.stdout)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _imports(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get imports in JSON format."""
        commands = ["iij"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            try:
                result.normalized_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Fallback to non-JSON
                result.normalized_output = self._parse_imports(result.stdout)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _exports(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get exports."""
        commands = ["iEj"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            try:
                result.normalized_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                result.normalized_output = self._parse_exports(result.stdout)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _symbols(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get symbols."""
        commands = ["isj"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            try:
                result.normalized_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                result.normalized_output = []

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _strings(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get strings."""
        commands = ["izj"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            try:
                result.normalized_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                result.normalized_output = []

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _functions(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Get functions."""
        commands = ["aflc", "afll"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            result.normalized_output = self._parse_functions(result.stdout)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _xrefs(self, binary_path: str, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Get cross-references."""
        addr = inputs.get("address")
        if addr:
            commands = [f"axt {addr}", f"axf {addr}"]
        else:
            commands = ["axtj"]  # All xrefs as JSON

        result = self._run_rizin(binary_path, commands)

        if result.success:
            try:
                result.normalized_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                result.normalized_output = []

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _disassemble(self, binary_path: str, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Disassemble at address."""
        addr = inputs.get("address", "0")
        limit = inputs.get("limit", 10)

        commands = [f"pd {limit} @ {addr}"]
        result = self._run_rizin(binary_path, commands)

        if result.success:
            result.normalized_output = {
                "address": addr,
                "disassembly": result.stdout
            }

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _analyze(self, binary_path: str, start: float) -> AdapterExecutionResult:
        """Run full analysis."""
        commands = ["aaa"]  # Analyze all
        result = self._run_rizin(binary_path, commands)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def _parse_info(self, output: str) -> Dict:
        """Parse info output."""
        info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info

    def _parse_sections(self, output: str) -> List[Dict]:
        """Parse sections output."""
        sections = []
        for line in output.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    sections.append({
                        "name": parts[0],
                        "addr": parts[1],
                        "size": parts[2],
                    })
        return sections

    def _parse_imports(self, output: str) -> List[Dict]:
        """Parse imports output."""
        imports = []
        for line in output.split('\n'):
            if line.strip():
                imports.append({"name": line.strip()})
        return imports

    def _parse_exports(self, output: str) -> List[Dict]:
        """Parse exports output."""
        exports = []
        for line in output.split('\n'):
            if line.strip():
                exports.append({"name": line.strip()})
        return exports

    def _parse_functions(self, output: str) -> List[Dict]:
        """Parse functions output."""
        functions = []
        current = None

        for line in output.split('\n'):
            if line.startswith('0x'):
                parts = line.split()
                if len(parts) >= 4:
                    current = {
                        "address": parts[0],
                        "size": parts[1],
                        "cc": parts[2] if len(parts) > 2 else "0",
                        "name": ' '.join(parts[3:]) if len(parts) > 3 else ""
                    }
                    functions.append(current)
            elif current and line.strip():
                # Continuation
                current['name'] += ' ' + line.strip()

        return functions

    def execute_raw(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        timeout_ms: int = 300000
    ) -> AdapterExecutionResult:
        """Execute raw command."""
        import time
        start = time.time()

        try:
            proc, truncated, truncation_reason = self._safe_subprocess_execute(
                command,
                cwd=cwd,
                env=env,
                input_data=input_data.decode() if input_data else None,
                timeout_ms=timeout_ms,
            )

            return AdapterExecutionResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                duration_ms=int((time.time() - start) * 1000),
                truncated=truncated,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                failure_classification=FailureClassification.PROCESS_ERROR,
            )

    def normalize_output(
        self,
        capability_id: str,
        raw_output: Any
    ) -> Any:
        """Normalize rizin output."""
        return raw_output

    def configure(self, config: Dict[str, Any]):
        """Apply configuration."""
        self._config.update(config)

    def default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "timeout_ms": 300000,
        }
