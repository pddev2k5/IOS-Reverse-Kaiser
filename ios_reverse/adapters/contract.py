"""
Canonical Tool Adapter Contract for IOS REVERSE KAISER.

Defines the stable interface all tool adapters must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import subprocess

if TYPE_CHECKING:
    import subprocess as sp


class ToolAvailability(str, Enum):
    """Explicit availability states for tools."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MISCONFIGURED = "misconfigured"
    DEGRADED = "degraded"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    SESSION_REQUIRED = "session_required"
    AUTH_REQUIRED = "auth_required"
    UNKNOWN = "unknown"


class ToolRole(str, Enum):
    """Tool role classification per capability context."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    FALLBACK = "fallback"


class FailureClassification(str, Enum):
    """Normalized failure types from external tools."""
    TOOL_NOT_FOUND = "tool_not_found"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    SESSION_UNAVAILABLE = "session_unavailable"
    TIMEOUT = "timeout"
    PROCESS_ERROR = "process_error"
    INVALID_INPUT = "invalid_input"
    PARSE_ERROR = "parse_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_LIMIT = "resource_limit"
    TOOL_VERSION_UNSUPPORTED = "tool_version_unsupported"
    PARTIAL_OUTPUT = "partial_output"
    SESSION_LOST = "session_lost"
    TARGET_MISMATCH = "target_mismatch"
    UNKNOWN_ERROR = "unknown_error"


class ExecutionMode(str, Enum):
    """Execution mode for adapters."""
    SUBPROCESS = "subprocess"
    LIBRARY = "library"
    MCP_SESSION = "mcp_session"
    REMOTE = "remote"
    LOCAL = "local"


@dataclass
class ToolMetadata:
    """Metadata about a tool."""
    adapter_id: str
    version: str
    tool_name: str
    tool_version: Optional[str] = None
    supported_platforms: List[str] = field(default_factory=list)
    supported_architectures: List[str] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SUBPROCESS


@dataclass
class DependencyInfo:
    """Dependency information."""
    name: str
    required: bool = True
    installed: bool = False
    version: Optional[str] = None


@dataclass
class AdapterHealth:
    """Health status of an adapter."""
    availability: ToolAvailability
    adapter_id: str
    tool_name: str
    tool_version: Optional[str] = None
    platform: str = ""
    capabilities: List[str] = field(default_factory=list)
    reason: str = ""
    suggested_fallback: Optional[str] = None
    dependencies: List[DependencyInfo] = field(default_factory=list)
    checked_at: str = ""


@dataclass
class AdapterExecutionResult:
    """
    Canonical result from adapter execution.

    All external tool outputs must be wrapped in this type.
    """
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    duration_ms: int = 0
    artifacts: List[str] = field(default_factory=list)  # Paths to output artifacts
    raw_output_ref: Optional[str] = None  # Ref to raw output in case workspace
    normalized_output: Optional[Any] = None  # Structured normalized output
    error: Optional[str] = None
    failure_classification: Optional[FailureClassification] = None
    retryable: bool = False
    truncated: bool = False
    truncation_limit: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_provenance_dict(self) -> Dict[str, Any]:
        """Convert to provenance-compatible dict."""
        return {
            "success": self.success,
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "artifacts": self.artifacts,
            "raw_output_ref": self.raw_output_ref,
            "error": self.error,
            "failure_classification": self.failure_classification.value if self.failure_classification else None,
            "truncated": self.truncated,
        }


class ToolAdapterContract(ABC):
    """
    Canonical tool adapter contract.

    All adapters must implement this interface.
    """

    # --- Identity ---

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique adapter identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Adapter version."""
        pass

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the underlying tool."""
        pass

    # --- Availability ---

    @abstractmethod
    def availability(self) -> ToolAvailability:
        """Check tool availability."""
        pass

    @abstractmethod
    def health_check(self) -> AdapterHealth:
        """Perform detailed health check."""
        pass

    @abstractmethod
    def tool_version(self) -> Optional[str]:
        """Detect tool version."""
        pass

    # --- Dependencies ---

    @abstractmethod
    def required_dependencies(self) -> List[DependencyInfo]:
        """List required dependencies."""
        pass

    @abstractmethod
    def optional_dependencies(self) -> List[DependencyInfo]:
        """List optional dependencies."""
        pass

    # --- Capabilities ---

    @abstractmethod
    def supported_capabilities(self) -> Set[str]:
        """Set of capability IDs this adapter supports."""
        pass

    # --- Execution ---

    @abstractmethod
    def execute(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult:
        """
        Execute a capability through this adapter.

        Args:
            capability_id: The capability to execute
            inputs: Capability-specific inputs
            context: Execution context (artifact path, etc.)

        Returns:
            AdapterExecutionResult
        """
        pass

    @abstractmethod
    def execute_raw(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        timeout_ms: int = 60000
    ) -> AdapterExecutionResult:
        """
        Execute a raw command through this adapter.

        Args:
            command: Command and arguments (argv list)
            cwd: Working directory
            env: Environment variables
            input_data: stdin data
            timeout_ms: Timeout in milliseconds

        Returns:
            AdapterExecutionResult
        """
        pass

    # --- Normalization ---

    @abstractmethod
    def normalize_output(
        self,
        capability_id: str,
        raw_output: Any
    ) -> Any:
        """
        Normalize tool output for analytical layer.

        Args:
            capability_id: The capability that produced output
            raw_output: Raw tool output

        Returns:
            Normalized output suitable for evidence creation
        """
        pass

    # --- Configuration ---

    @abstractmethod
    def configure(self, config: Dict[str, Any]):
        """Apply configuration to adapter."""
        pass

    @abstractmethod
    def default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        pass


class SubprocessAdapterContract(ToolAdapterContract):
    """
    Contract for subprocess-based adapters.

    Implements centralized subprocess execution with safety.
    """

    DEFAULT_TIMEOUT_MS: int = 60000
    MAX_STDOUT_BYTES: int = 50 * 1024 * 1024  # 50MB
    MAX_STDERR_BYTES: int = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self._config: Dict[str, Any] = {}

    # --- Subprocess Safety ---

    def _safe_subprocess_execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        check_path: bool = True
    ) -> Tuple[subprocess.CompletedProcess, bool, Optional[str]]:
        """
        Centralized subprocess execution.

        Returns:
            (CompletedProcess, truncated, truncation_reason)
        """
        truncated = False
        truncation_reason = None

        # Validate paths in command to prevent injection
        if check_path:
            for arg in command:
                if self._looks_like_injection(arg):
                    raise ValueError(f"Potential injection detected in: {arg}")

        try:
            proc = sp.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                input=input_data,
                timeout=timeout_ms / 1000
            )

            # Check output size
            if len(proc.stdout) > self.MAX_STDOUT_BYTES:
                truncated = True
                proc.stdout = proc.stdout[:self.MAX_STDOUT_BYTES]
                truncation_reason = f"stdout exceeded {self.MAX_STDOUT_BYTES} bytes"

            if len(proc.stderr) > self.MAX_STDERR_BYTES:
                truncated_stderr = True
                proc.stderr = proc.stderr[:self.MAX_STDERR_BYTES]
                if not truncation_reason:
                    truncation_reason = f"stderr exceeded {self.MAX_STDERR_BYTES} bytes"

            return proc, truncated, truncation_reason

        except sp.TimeoutExpired:
            raise
        except Exception as e:
            raise

    @staticmethod
    def _looks_like_injection(arg: str) -> bool:
        """Check for potential command injection."""
        # Check for shell metacharacters that shouldn't be in paths
        dangerous = [';', '|', '&', '&&', '||', '$(', '`', '\\n', '\\r']
        for pattern in dangerous:
            if pattern in arg:
                return True
        return False

    def _classify_failure(
        self,
        error: Exception,
        returncode: Optional[int] = None
    ) -> FailureClassification:
        """Classify a failure."""
        error_msg = str(error).lower()

        if isinstance(error, FileNotFoundError):
            return FailureClassification.TOOL_NOT_FOUND
        if "timeout" in error_msg:
            return FailureClassification.TIMEOUT
        if "permission" in error_msg or "denied" in error_msg:
            return FailureClassification.PERMISSION_ERROR
        if "not found" in error_msg or "no such file" in error_msg:
            return FailureClassification.INVALID_INPUT
        if returncode == -9:
            return FailureClassification.RESOURCE_LIMIT
        if "parse" in error_msg or "format" in error_msg:
            return FailureClassification.PARSE_ERROR

        return FailureClassification.UNKNOWN_ERROR


class FallbackChain:
    """Represents an explicit fallback chain."""

    def __init__(self):
        self._adapters: List[Tuple[ToolAdapterContract, ToolRole]] = []

    def add(self, adapter: ToolAdapterContract, role: ToolRole):
        """Add adapter to chain."""
        self._adapters.append((adapter, role))

    def get_available(self) -> List[Tuple[ToolAdapterContract, ToolRole]]:
        """Get adapters in priority order that are available."""
        available = []
        for adapter, role in self._adapters:
            if adapter.availability() == ToolAvailability.AVAILABLE:
                available.append((adapter, role))
        return available

    def select_best(self) -> Optional[Tuple[ToolAdapterContract, ToolRole]]:
        """Select best available adapter."""
        available = self.get_available()
        if not available:
            return None

        # Priority: REQUIRED > OPTIONAL > FALLBACK
        for role in [ToolRole.REQUIRED, ToolRole.OPTIONAL, ToolRole.FALLBACK]:
            for adapter, r in available:
                if r == role:
                    return adapter, r

        return available[0]

    def explain(self) -> Dict[str, Any]:
        """Explain chain status."""
        return {
            "total": len(self._adapters),
            "available": len(self.get_available()),
            "adapters": [
                {
                    "id": adapter.adapter_id,
                    "role": role.value,
                    "availability": adapter.availability().value,
                    "version": adapter.tool_version()
                }
                for adapter, role in self._adapters
            ]
        }


def is_retryable_failure(classification: FailureClassification) -> bool:
    """Determine if a failure is retryable."""
    retryable = {
        FailureClassification.TIMEOUT,
        FailureClassification.SESSION_LOST,
        FailureClassification.SESSION_UNAVAILABLE,
        FailureClassification.PARTIAL_OUTPUT,
    }
    return classification in retryable
