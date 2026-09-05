"""
IDA Pro MCP Adapter for IOS REVERSE KAISER.

Provides integration with IDA Pro through the ida-pro-mcp server.

Maturity Level: L1 (Contract + Implementation skeleton)
Target Level: L3 (Kaiser integration)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from enum import Enum
import json
import subprocess
import asyncio
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


class IDAConnectionState(str, Enum):
    """IDA session connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IDLE = "idle"
    ANALYZING = "analyzing"
    ERROR = "error"


@dataclass
class IDATargetInfo:
    """Information about loaded IDA target."""
    path: str
    processor: str
    bitness: int
    image_base: int
    entry_point: int
    analysis_complete: bool
    hash_sha256: Optional[str] = None


@dataclass
class IDAFunction:
    """IDA function record."""
    address: int
    name: str
    size: int
    flags: List[str] = field(default_factory=list)


@dataclass
class IDAXref:
    """IDA cross-reference."""
    from_addr: int
    to_addr: int
    type: str
    is_code: bool


@dataclass
class IDAString:
    """IDA string record."""
    address: int
    value: str
    length: int
    type: str  # ascii, unicode, etc.


@dataclass
class IDAImport:
    """IDA import record."""
    ordinal: int
    name: str
    library: str
    address: int


@dataclass
class IDAExport:
    """IDA export record."""
    ordinal: int
    name: str
    address: int


class IDAMCPAdapter(SubprocessAdapterContract):
    """
    IDA Pro MCP adapter.

    Integrates with ida-pro-mcp server for IDA analysis operations.

    Required Environment:
    - IDA Pro installed
    - ida-pro-mcp server installed and in PATH
    - IDA license available

    MCP Server Command:
    ida-pro-mcp

    MCP Tools Expected:
    - ida_load_database
    - ida_get_database_info
    - ida_list_functions
    - ida_get_function
    - ida_list_imports
    - ida_list_exports
    - ida_list_strings
    - ida_get_xrefs
    - ida_get_func_xrefs
    - ida_get_func_refs
    - ida_decompile_function
    """

    ADAPTER_ID = "ida-pro-mcp"
    VERSION = "0.1.0"
    TOOL_NAME = "IDA Pro"
    MCP_COMMAND = "ida-pro-mcp"

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {}
        self._mcp_process: Optional[subprocess.Popen] = None
        self._connection_state = IDAConnectionState.DISCONNECTED
        self._current_target: Optional[IDATargetInfo] = None

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
        """Check if IDA MCP is available."""
        # Check if ida-pro-mcp is in PATH
        try:
            result = subprocess.run(
                ["ida-pro-mcp", "--version"],
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

        # Check if IDA is installed
        ida_paths = [
            "C:\\Program Files\\IDA Pro 8.x\\ida.exe",
            "C:\\Program Files\\IDA Pro\\ida.exe",
            "/Applications/IDA Pro.app/Contents/MacOS/ida",
            "/usr/local/bin/ida",
        ]
        for path in ida_paths:
            if Path(path).exists():
                # IDA exists but MCP not available
                return ToolAvailability.DEGRADED

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
            health.reason = "ida-pro-mcp not found in PATH and IDA installation not detected"
            health.suggested_fallback = "ghidra"
        elif availability == ToolAvailability.DEGRADED:
            health.reason = "IDA installed but ida-pro-mcp not available"
            health.suggested_fallback = "ida-mcp-server"

        return health

    def tool_version(self) -> Optional[str]:
        """Detect IDA version."""
        try:
            # Try ida-pro-mcp version
            result = subprocess.run(
                ["ida-pro-mcp", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        # Try IDA directly
        ida_paths = [
            "C:\\Program Files\\IDA Pro 8.x\\ida.exe",
            "C:\\Program Files\\IDA Pro\\ida.exe",
        ]
        for path in ida_paths:
            if Path(path).exists():
                return "IDA Pro (version unknown)"

        return None

    def required_dependencies(self) -> List:
        """List required dependencies."""
        return [
            {
                "name": "IDA Pro",
                "required": True,
                "installed": self._is_ida_installed(),
            }
        ]

    def optional_dependencies(self) -> List:
        """List optional dependencies."""
        return [
            {
                "name": "ida-pro-mcp",
                "required": False,
                "installed": self._is_mcp_installed(),
            }
        ]

    def supported_capabilities(self) -> Set[str]:
        """Set of capabilities this adapter supports."""
        return {
            "ida.load_database",
            "ida.database_info",
            "ida.list_functions",
            "ida.get_function",
            "ida.list_imports",
            "ida.list_exports",
            "ida.list_strings",
            "ida.get_xrefs",
            "ida.get_func_xrefs",
            "ida.get_func_refs",
            "ida.decompile_function",
            "ida.disassemble",
        }

    def _is_ida_installed(self) -> bool:
        """Check if IDA is installed."""
        ida_paths = [
            "C:\\Program Files\\IDA Pro 8.x\\ida.exe",
            "C:\\Program Files\\IDA Pro\\ida.exe",
            "/Applications/IDA Pro.app/Contents/MacOS/ida",
            "/usr/local/bin/ida",
        ]
        return any(Path(p).exists() for p in ida_paths)

    def _is_mcp_installed(self) -> bool:
        """Check if ida-pro-mcp is installed."""
        try:
            subprocess.run(
                ["ida-pro-mcp", "--version"],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False

    def execute(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult:
        """
        Execute IDA MCP capability.

        Args:
            capability_id: The IDA capability to execute
            inputs: Capability-specific inputs (target_path, function_addr, etc.)
            context: Execution context

        Returns:
            AdapterExecutionResult with normalized output
        """
        # Map capability to MCP tool
        capability_map = {
            "ida.load_database": "ida_load_database",
            "ida.database_info": "ida_get_database_info",
            "ida.list_functions": "ida_list_functions",
            "ida.get_function": "ida_get_function",
            "ida.list_imports": "ida_list_imports",
            "ida.list_exports": "ida_list_exports",
            "ida.list_strings": "ida_list_strings",
            "ida.get_xrefs": "ida_get_xrefs",
            "ida.get_func_xrefs": "ida_get_func_xrefs",
            "ida.get_func_refs": "ida_get_func_refs",
            "ida.decompile_function": "ida_decompile_function",
            "ida.disassemble": "ida_disassemble",
        }

        mcp_tool = capability_map.get(capability_id)
        if not mcp_tool:
            return AdapterExecutionResult(
                success=False,
                error=f"Unknown capability: {capability_id}",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        # Check availability
        if self.availability() == ToolAvailability.UNAVAILABLE:
            return AdapterExecutionResult(
                success=False,
                error="IDA Pro MCP not available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        # Execute MCP command
        return self._execute_mcp(mcp_tool, inputs, context)

    def _execute_mcp(
        self,
        tool: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult:
        """Execute MCP tool command."""
        import time
        start = time.time()

        try:
            # Build MCP command
            cmd = ["ida-pro-mcp", tool]

            # Add inputs as JSON to stdin
            input_json = json.dumps(inputs)
            result = subprocess.run(
                cmd,
                input=input_json,
                capture_output=True,
                text=True,
                timeout=300000  # 5 minute timeout for analysis
            )

            duration_ms = int((time.time() - start) * 1000)

            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    return AdapterExecutionResult(
                        success=True,
                        stdout=result.stdout,
                        returncode=0,
                        duration_ms=duration_ms,
                        normalized_output=output,
                    )
                except json.JSONDecodeError:
                    return AdapterExecutionResult(
                        success=True,
                        stdout=result.stdout,
                        returncode=0,
                        duration_ms=duration_ms,
                    )
            else:
                return AdapterExecutionResult(
                    success=False,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                    duration_ms=duration_ms,
                    error=result.stderr or "MCP command failed",
                    failure_classification=self._classify_mcp_error(result.stderr),
                )

        except subprocess.TimeoutExpired:
            return AdapterExecutionResult(
                success=False,
                error="IDA analysis timed out",
                duration_ms=int((time.time() - start) * 1000),
                failure_classification=FailureClassification.TIMEOUT,
                retryable=True,
            )
        except FileNotFoundError:
            return AdapterExecutionResult(
                success=False,
                error="ida-pro-mcp not found",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                failure_classification=FailureClassification.UNKNOWN_ERROR,
            )

    def _classify_mcp_error(self, stderr: str) -> FailureClassification:
        """Classify MCP-specific errors."""
        stderr_lower = stderr.lower()

        if "connection" in stderr_lower or "connect" in stderr_lower:
            return FailureClassification.SESSION_UNAVAILABLE
        if "timeout" in stderr_lower:
            return FailureClassification.TIMEOUT
        if "not found" in stderr_lower or "missing" in stderr_lower:
            return FailureClassification.INVALID_INPUT
        if "permission" in stderr_lower or "denied" in stderr_lower:
            return FailureClassification.PERMISSION_ERROR

        return FailureClassification.PROCESS_ERROR

    def execute_raw(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        timeout_ms: int = 60000
    ) -> AdapterExecutionResult:
        """Execute raw command through subprocess."""
        import time
        start = time.time()

        try:
            proc, truncated, truncation_reason = self._safe_subprocess_execute(
                command,
                cwd=cwd,
                env=env,
                input_data=input_data.decode() if input_data else None,
                timeout_ms=timeout_ms,
                check_path=True
            )

            return AdapterExecutionResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                duration_ms=int((time.time() - start) * 1000),
                truncated=truncated,
                error=truncation_reason if truncated else None,
                failure_classification=FailureClassification.PROCESS_ERROR if proc.returncode != 0 else None,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                failure_classification=self._classify_failure(e),
            )

    def normalize_output(
        self,
        capability_id: str,
        raw_output: Any
    ) -> Any:
        """
        Normalize IDA output for evidence creation.

        Args:
            capability_id: The capability that produced output
            raw_output: Raw IDA output

        Returns:
            Normalized output suitable for evidence creation
        """
        if not raw_output:
            return None

        # Normalize based on capability
        normalizers = {
            "ida.list_functions": self._normalize_functions,
            "ida.get_function": self._normalize_function,
            "ida.list_imports": self._normalize_imports,
            "ida.list_exports": self._normalize_exports,
            "ida.list_strings": self._normalize_strings,
            "ida.get_xrefs": self._normalize_xrefs,
            "ida.get_func_xrefs": self._normalize_xrefs,
            "ida.get_func_refs": self._normalize_func_refs,
            "ida.decompile_function": self._normalize_decompile,
        }

        normalizer = normalizers.get(capability_id)
        if normalizer:
            return normalizer(raw_output)

        return raw_output

    def _normalize_functions(self, output: Any) -> List[Dict]:
        """Normalize function list."""
        if isinstance(output, dict) and "functions" in output:
            return output["functions"]
        if isinstance(output, list):
            return output
        return []

    def _normalize_function(self, output: Any) -> Dict:
        """Normalize single function."""
        if isinstance(output, dict):
            return {
                "address": output.get("address", 0),
                "name": output.get("name", ""),
                "size": output.get("size", 0),
                "flags": output.get("flags", []),
            }
        return {}

    def _normalize_imports(self, output: Any) -> List[Dict]:
        """Normalize import list."""
        if isinstance(output, dict) and "imports" in output:
            return output["imports"]
        if isinstance(output, list):
            return output
        return []

    def _normalize_exports(self, output: Any) -> List[Dict]:
        """Normalize export list."""
        if isinstance(output, dict) and "exports" in output:
            return output["exports"]
        if isinstance(output, list):
            return output
        return []

    def _normalize_strings(self, output: Any) -> List[Dict]:
        """Normalize string list."""
        if isinstance(output, dict) and "strings" in output:
            return output["strings"]
        if isinstance(output, list):
            return output
        return []

    def _normalize_xrefs(self, output: Any) -> List[Dict]:
        """Normalize cross-reference list."""
        if isinstance(output, dict) and "xrefs" in output:
            return output["xrefs"]
        if isinstance(output, list):
            return output
        return []

    def _normalize_func_refs(self, output: Any) -> Dict:
        """Normalize function callers/callees."""
        if isinstance(output, dict):
            return {
                "callers": output.get("callers", []),
                "callees": output.get("callees", []),
            }
        return {"callers": [], "callees": []}

    def _normalize_decompile(self, output: Any) -> Dict:
        """Normalize decompilation output."""
        if isinstance(output, dict):
            return {
                "address": output.get("address", 0),
                "name": output.get("name", ""),
                "pseudocode": output.get("pseudocode", ""),
                "warnings": output.get("warnings", []),
            }
        return {}

    def configure(self, config: Dict[str, Any]):
        """Apply configuration to adapter."""
        self._config.update(config)

    def default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "timeout_ms": 300000,  # 5 minutes for analysis
            "ida_path": None,
            "mcp_path": "ida-pro-mcp",
        }

    # --- IDA-Specific Methods ---

    def verify_target(
        self,
        target_path: str,
        expected_hash: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify loaded target matches expected binary.

        Args:
            target_path: Expected binary path
            expected_hash: Expected SHA256 hash (optional)

        Returns:
            (is_valid, reason)
        """
        info_result = self.execute(
            "ida.database_info",
            {"path": target_path},
            {}
        )

        if not info_result.success:
            return False, "Failed to get database info"

        info = info_result.normalized_output
        if not info:
            return False, "No database info returned"

        loaded_path = info.get("path", "")

        # Normalize paths for comparison
        import os
        if os.path.normpath(loaded_path) != os.path.normpath(target_path):
            return False, f"TARGET_MISMATCH: loaded={loaded_path}, expected={target_path}"

        if expected_hash and info.get("hash") != expected_hash:
            return False, f"TARGET_MISMATCH: hash mismatch"

        self._current_target = IDATargetInfo(
            path=info.get("path", ""),
            processor=info.get("processor", ""),
            bitness=info.get("bitness", 0),
            image_base=info.get("image_base", 0),
            entry_point=info.get("entry_point", 0),
            analysis_complete=info.get("analysis_complete", False),
            hash_sha256=info.get("hash"),
        )

        return True, None

    def get_connection_state(self) -> IDAConnectionState:
        """Get current connection state."""
        return self._connection_state

    def get_current_target(self) -> Optional[IDATargetInfo]:
        """Get current loaded target info."""
        return self._current_target
