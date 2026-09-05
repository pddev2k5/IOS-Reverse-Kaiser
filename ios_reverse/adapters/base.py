"""
Tool Adapter Base Classes for IOS REVERSE KAISER.

Adapters provide a consistent interface to external tools.
Adapters are replaceable implementations; capability contracts are immutable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import subprocess
import shutil
import os


class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass


class ToolUnavailableError(AdapterError):
    """Raised when a required tool is not available."""
    pass


class ToolExecutionError(AdapterError):
    """Raised when tool execution fails."""
    pass


class VersionError(AdapterError):
    """Raised when tool version is insufficient."""
    pass


@dataclass
class AdapterResult:
    """Result from adapter execution."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ToolInfo:
    """Information about an available tool."""
    name: str
    path: str
    version: Optional[str] = None
    min_version: Optional[str] = None

    def is_available(self) -> bool:
        """Check if tool is available."""
        return bool(self.path)

    def check_version(self) -> bool:
        """Check if version meets minimum requirement."""
        if not self.version or not self.min_version:
            return True
        return self._compare_versions(self.version, self.min_version) >= 0

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare versions. Returns -1, 0, or 1."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        return 0


class ToolAdapter(ABC):
    """
    Base class for tool adapters.

    Adapters provide a consistent interface to external tools.
    Subclasses must implement:
    - get_tool_info()
    - execute()
    - validate_environment()
    """

    def __init__(
        self,
        required: bool = True,
        min_version: Optional[str] = None,
        timeout_ms: int = 60000
    ):
        self._required = required
        self._min_version = min_version
        self._timeout_ms = timeout_ms
        self._tool_info: Optional[ToolInfo] = None

    @property
    def id(self) -> str:
        """Unique adapter identifier."""
        return self.__class__.__name__.replace('Adapter', '').lower()

    @property
    def required(self) -> bool:
        """Whether this adapter is required."""
        return self._required

    @property
    def min_version(self) -> Optional[str]:
        """Minimum required version."""
        return self._min_version

    @abstractmethod
    def get_tool_info(self) -> Optional[ToolInfo]:
        """Get information about the tool."""
        pass

    @abstractmethod
    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that the tool is available and meets requirements.

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None
    ) -> AdapterResult:
        """
        Execute a command using this adapter.

        Args:
            command: Command and arguments
            cwd: Working directory
            env: Environment variables
            input_data: stdin data

        Returns:
            AdapterResult with execution results
        """
        pass

    def is_available(self) -> bool:
        """Check if tool is available."""
        valid, _ = self.validate_environment()
        return valid

    def run(
        self,
        *args,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        check: bool = True
    ) -> AdapterResult:
        """
        Run the adapter with given arguments.

        Args:
            *args: Command arguments
            cwd: Working directory
            env: Environment variables
            input_data: stdin data
            check: Raise exception on failure

        Returns:
            AdapterResult
        """
        # Validate environment
        valid, error = self.validate_environment()
        if not valid:
            return AdapterResult(
                success=False,
                error=error or "Tool unavailable"
            )

        # Execute
        result = self.execute(list(args), cwd, env, input_data)

        # Check return code
        if check and not result.success:
            raise ToolExecutionError(
                f"Command failed: {' '.join(args)}\nError: {result.error}"
            )

        return result


class SubprocessAdapter(ToolAdapter):
    """
    Adapter that executes commands via subprocess.

    This is the base adapter for most command-line tools.
    """

    def __init__(
        self,
        command: str,
        required: bool = True,
        min_version: Optional[str] = None,
        version_flag: str = "--version",
        version_pattern: Optional[str] = None,
        timeout_ms: int = 60000
    ):
        super().__init__(required, min_version, timeout_ms)
        self._command = command
        self._version_flag = version_flag
        self._version_pattern = version_pattern

    def get_tool_info(self) -> Optional[ToolInfo]:
        """Get tool information."""
        path = shutil.which(self._command)
        if not path:
            return None

        version = None
        if self._version_flag:
            try:
                result = subprocess.run(
                    [self._command, self._version_flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    output = result.stdout + result.stderr
                    if self._version_pattern:
                        import re
                        match = re.search(self._version_pattern, output)
                        if match:
                            version = match.group(1)
                    else:
                        # Try to extract first line
                        version = output.split('\n')[0].strip()
            except Exception:
                pass

        return ToolInfo(
            name=self._command,
            path=path,
            version=version,
            min_version=self._min_version
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        """Validate tool is available."""
        info = self.get_tool_info()
        if not info:
            return False, f"Tool '{self._command}' not found"

        if not info.is_available():
            return False, f"Tool '{self._command}' not executable"

        if self._min_version:
            if not info.check_version():
                return False, (
                    f"Tool '{self._command}' version {info.version} "
                    f"is below minimum {self._min_version}"
                )

        self._tool_info = info
        return True, None

    def execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None
    ) -> AdapterResult:
        """Execute command via subprocess."""
        full_command = [self._command] + command

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                input=input_data,
                timeout=self._timeout_ms / 1000
            )

            return AdapterResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )
        except subprocess.TimeoutExpired:
            return AdapterResult(
                success=False,
                error=f"Command timed out after {self._timeout_ms}ms"
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )


class FallbackAdapter(SubprocessAdapter):
    """
    Adapter with fallback to alternative tools.

    If primary tool is unavailable, tries fallback tools.
    """

    def __init__(
        self,
        primary_command: str,
        fallback_commands: List[str],
        **kwargs
    ):
        super().__init__(primary_command, **kwargs)
        self._fallback_commands = fallback_commands
        self._active_command = primary_command

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        """Validate with fallback support."""
        # Try primary
        valid, error = super().validate_environment()
        if valid:
            self._active_command = self._command
            return True, None

        # Try fallbacks
        for cmd in self._fallback_commands:
            path = shutil.which(cmd)
            if path:
                self._active_command = cmd
                return True, None

        return False, f"No suitable tool found (tried: {self._command}, {self._fallback_commands})"

    def get_tool_info(self) -> Optional[ToolInfo]:
        """Get tool info for active command."""
        return super().get_tool_info()
