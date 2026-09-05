"""
iOS Runtime Provider Adapter for IOS REVERSE KAISER.

Provides integration with iOS runtime analysis tools (Frida, LLDB).

Maturity Level: L1 (Contract + Implementation skeleton)
Target Level: L2 (Basic implementation)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
import json
import subprocess
from pathlib import Path
from enum import Enum

from ios_reverse.adapters.contract import (
    ToolAdapterContract,
    SubprocessAdapterContract,
    ToolAvailability,
    ToolRole,
    FailureClassification,
    AdapterHealth,
    AdapterExecutionResult,
)


class RuntimeProvider(str, Enum):
    """Runtime provider types."""
    FRIDA = "frida"
    LLDB = "lldb"
    UNKNOWN = "unknown"


class SessionState(str, Enum):
    """Runtime session states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ATTACHED = "attached"
    SPAWNED = "spawned"
    ERROR = "error"


@dataclass
class RuntimeDevice:
    """Runtime device/simulator info."""
    id: str
    name: str
    type: str  # device, simulator
    platform: str  # ios, tvos, watchos
    os_version: str


@dataclass
class RuntimeProcess:
    """Runtime process info."""
    pid: int
    name: str
    bundle_id: Optional[str] = None


@dataclass
class RuntimeModule:
    """Runtime module/library info."""
    name: str
    base: int
    size: int
    path: Optional[str] = None


@dataclass
class RuntimeClass:
    """Runtime Objective-C class info."""
    name: str
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)


@dataclass
class RuntimeObservation:
    """Runtime observation record."""
    timestamp: str
    provider: RuntimeProvider
    type: str  # method_trace, class_list, module_list, etc.
    data: Dict[str, Any]
    session_id: str


class RuntimeProviderAdapter(SubprocessAdapterContract):
    """
    iOS runtime analysis provider adapter.

    Supports multiple runtime providers:
    - Frida: frida-trace, frida, frida-ps
    - LLDB: lldb CLI (with debugserver)

    Required Environment:
    - For Frida: frida-tools installed (pip install frida-tools)
    - For LLDB: lldb CLI available (Xcode CLT on macOS)
    - For device: usbmuxd, debugserver on device (jailbroken)
    """

    ADAPTER_ID = "runtime-provider"
    VERSION = "0.1.0"
    TOOL_NAME = "iOS Runtime"

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {}
        self._session_state = SessionState.DISCONNECTED
        self._current_provider: Optional[RuntimeProvider] = None
        self._session_id: Optional[str] = None

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
        """Check if any runtime provider is available."""
        # Check Frida first
        if self._check_frida():
            return ToolAvailability.AVAILABLE

        # Check LLDB
        if self._check_lldb():
            return ToolAvailability.AVAILABLE

        return ToolAvailability.UNAVAILABLE

    def health_check(self) -> AdapterHealth:
        """Perform detailed health check."""
        availability = self.availability()

        providers = []
        if self._check_frida():
            providers.append("frida")
        if self._check_lldb():
            providers.append("lldb")

        health = AdapterHealth(
            availability=availability,
            adapter_id=self.adapter_id,
            tool_name=self.tool_name,
            tool_version=self.tool_version(),
            capabilities=list(self.supported_capabilities()),
        )

        if availability == ToolAvailability.UNAVAILABLE:
            health.reason = "No runtime provider available (need Frida or LLDB)"
            health.suggested_fallback = "static_analysis"
        else:
            health.reason = f"Available providers: {', '.join(providers)}"

        return health

    def tool_version(self) -> Optional[str]:
        """Get runtime provider versions."""
        versions = []

        if self._check_frida():
            try:
                result = subprocess.run(
                    ["frida", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    versions.append(f"frida {result.stdout.strip()}")
            except:
                pass

        if self._check_lldb():
            versions.append("lldb (available)")

        return ", ".join(versions) if versions else None

    def _check_frida(self) -> bool:
        """Check if Frida is available."""
        try:
            result = subprocess.run(
                ["frida", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _check_lldb(self) -> bool:
        """Check if LLDB is available."""
        try:
            result = subprocess.run(
                ["lldb", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def required_dependencies(self) -> List[Dict]:
        """List required dependencies."""
        deps = []
        if not self._check_frida():
            deps.append({
                "name": "Frida",
                "required": False,  # Optional - can use LLDB
                "installed": False,
                "install_cmd": "pip install frida-tools"
            })
        if not self._check_lldb():
            deps.append({
                "name": "LLDB",
                "required": False,
                "installed": False,
                "install_cmd": "Install Xcode Command Line Tools"
            })
        return deps

    def optional_dependencies(self) -> List[Dict]:
        """List optional dependencies."""
        return [
            {
                "name": "usbmuxd",
                "required": False,
                "installed": self._check_usbmuxd(),
            },
            {
                "name": "debugserver (device)",
                "required": False,
                "installed": False,
            }
        ]

    def _check_usbmuxd(self) -> bool:
        """Check if usbmuxd is available."""
        try:
            subprocess.run(
                ["iproxy", "--version"],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False

    def supported_capabilities(self) -> Set[str]:
        """Set of capabilities this adapter supports."""
        return {
            "runtime.list_devices",
            "runtime.list_processes",
            "runtime.attach",
            "runtime.spawn",
            "runtime.detach",
            "runtime.list_modules",
            "runtime.list_classes",
            "runtime.enumerate_methods",
            "runtime.trace",
            "runtime.observation",
        }

    def execute(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult:
        """Execute runtime capability."""
        import time
        from datetime import datetime
        start = time.time()

        if self.availability() == ToolAvailability.UNAVAILABLE:
            return AdapterExecutionResult(
                success=False,
                error="No runtime provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        # Use Frida if available
        if self._check_frida():
            self._current_provider = RuntimeProvider.FRIDA
            return self._execute_frida(capability_id, inputs, context, start)

        # Fallback to LLDB
        self._current_provider = RuntimeProvider.LLDB
        return self._execute_lldb(capability_id, inputs, context, start)

    def _execute_frida(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
        start: float
    ) -> AdapterExecutionResult:
        """Execute via Frida."""
        import uuid

        if capability_id == "runtime.list_devices":
            return self._frida_list_devices(start)
        elif capability_id == "runtime.list_processes":
            return self._frida_list_processes(start)
        elif capability_id == "runtime.attach":
            return self._frida_attach(inputs, start)
        elif capability_id == "runtime.spawn":
            return self._frida_spawn(inputs, start)
        elif capability_id == "runtime.detach":
            return self._frida_detach(start)
        elif capability_id == "runtime.list_modules":
            return self._frida_list_modules(inputs, start)
        elif capability_id == "runtime.list_classes":
            return self._frida_list_classes(inputs, start)
        elif capability_id == "runtime.enumerate_methods":
            return self._frida_enumerate_methods(inputs, start)
        elif capability_id == "runtime.observation":
            return self._frida_observation(inputs, start)

        return AdapterExecutionResult(
            success=False,
            error=f"Unknown capability: {capability_id}",
            failure_classification=FailureClassification.INVALID_INPUT,
        )

    def _execute_lldb(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
        start: float
    ) -> AdapterExecutionResult:
        """Execute via LLDB."""
        if capability_id == "runtime.list_processes":
            return self._lldb_list_processes(start)
        elif capability_id == "runtime.attach":
            return self._lldb_attach(inputs, start)
        elif capability_id == "runtime.detach":
            return self._lldb_detach(start)
        elif capability_id == "runtime.list_modules":
            return self._lldb_list_modules(inputs, start)

        return AdapterExecutionResult(
            success=False,
            error=f"Unknown capability: {capability_id}",
            failure_classification=FailureClassification.INVALID_INPUT,
        )

    def _frida_list_devices(self, start: float) -> AdapterExecutionResult:
        """List available Frida devices."""
        import time
        try:
            result = subprocess.run(
                ["frida-ls-devices", "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )

            duration_ms = int((time.time() - start) * 1000)

            if result.returncode == 0:
                try:
                    devices = json.loads(result.stdout)
                    return AdapterExecutionResult(
                        success=True,
                        stdout=result.stdout,
                        duration_ms=duration_ms,
                        normalized_output={"devices": devices},
                    )
                except json.JSONDecodeError:
                    return AdapterExecutionResult(
                        success=True,
                        stdout=result.stdout,
                        duration_ms=duration_ms,
                    )
            else:
                return AdapterExecutionResult(
                    success=False,
                    stderr=result.stderr,
                    duration_ms=duration_ms,
                    error=result.stderr,
                )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )

    def _frida_list_processes(self, start: float) -> AdapterExecutionResult:
        """List processes via Frida."""
        import time
        try:
            result = subprocess.run(
                ["frida-ps", "-U", "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )

            duration_ms = int((time.time() - start) * 1000)

            if result.returncode == 0:
                try:
                    processes = json.loads(result.stdout)
                    return AdapterExecutionResult(
                        success=True,
                        stdout=result.stdout,
                        duration_ms=duration_ms,
                        normalized_output={"processes": processes},
                    )
                except json.JSONDecodeError:
                    return AdapterExecutionResult(
                        success=True,
                        stdout=result.stdout,
                        duration_ms=duration_ms,
                    )
            else:
                return AdapterExecutionResult(
                    success=False,
                    stderr=result.stderr,
                    duration_ms=duration_ms,
                )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )

    def _frida_attach(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Attach to process."""
        import time
        import uuid

        target = inputs.get("target")  # PID or process name
        if not target:
            return AdapterExecutionResult(
                success=False,
                error="target (PID or name) required",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        session_id = str(uuid.uuid4())
        self._session_id = session_id
        self._session_state = SessionState.ATTACHED

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={
                "session_id": session_id,
                "target": target,
                "provider": "frida",
            },
        )

    def _frida_spawn(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Spawn and attach to app."""
        import time
        import uuid

        bundle_id = inputs.get("bundle_id")
        if not bundle_id:
            return AdapterExecutionResult(
                success=False,
                error="bundle_id required",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        session_id = str(uuid.uuid4())
        self._session_id = session_id
        self._session_state = SessionState.SPAWNED

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={
                "session_id": session_id,
                "bundle_id": bundle_id,
                "provider": "frida",
            },
        )

    def _frida_detach(self, start: float) -> AdapterExecutionResult:
        """Detach from session."""
        import time
        self._session_state = SessionState.DISCONNECTED
        self._session_id = None

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={"detached": True},
        )

    def _frida_list_modules(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """List loaded modules."""
        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={"modules": []},
        )

    def _frida_list_classes(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """List Objective-C classes."""
        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={"classes": []},
        )

    def _frida_enumerate_methods(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Enumerate methods of a class."""
        class_name = inputs.get("class_name")
        if not class_name:
            return AdapterExecutionResult(
                success=False,
                error="class_name required",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={
                "class": class_name,
                "methods": [],
            },
        )

    def _frida_observation(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Perform runtime observation."""
        import time
        from datetime import datetime

        observation_type = inputs.get("type", "generic")
        target = inputs.get("target")
        params = inputs.get("params", {})

        observation = RuntimeObservation(
            timestamp=datetime.utcnow().isoformat(),
            provider=self._current_provider or RuntimeProvider.UNKNOWN,
            type=observation_type,
            data={"target": target, "params": params},
            session_id=self._session_id or "none",
        )

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={
                "timestamp": observation.timestamp,
                "provider": observation.provider.value,
                "type": observation.type,
                "data": observation.data,
                "session_id": observation.session_id,
            },
        )

    def _lldb_list_processes(self, start: float) -> AdapterExecutionResult:
        """List processes via LLDB."""
        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={"processes": []},
        )

    def _lldb_attach(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """Attach via LLDB."""
        import time
        import uuid

        target = inputs.get("target")
        if not target:
            return AdapterExecutionResult(
                success=False,
                error="target required",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        session_id = str(uuid.uuid4())
        self._session_id = session_id
        self._session_state = SessionState.ATTACHED

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={
                "session_id": session_id,
                "target": target,
                "provider": "lldb",
            },
        )

    def _lldb_detach(self, start: float) -> AdapterExecutionResult:
        """Detach via LLDB."""
        import time
        self._session_state = SessionState.DISCONNECTED
        self._session_id = None

        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={"detached": True},
        )

    def _lldb_list_modules(self, inputs: Dict, start: float) -> AdapterExecutionResult:
        """List modules via LLDB."""
        return AdapterExecutionResult(
            success=True,
            duration_ms=int((time.time() - start) * 1000),
            normalized_output={"modules": []},
        )

    def execute_raw(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        timeout_ms: int = 60000
    ) -> AdapterExecutionResult:
        """Execute raw command."""
        import time
        start = time.time()

        try:
            proc, truncated, _ = self._safe_subprocess_execute(
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
        """Normalize runtime output."""
        return raw_output

    def configure(self, config: Dict[str, Any]):
        """Apply configuration."""
        self._config.update(config)

    def default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "timeout_ms": 60000,
            "provider": "auto",  # auto, frida, lldb
        }

    def get_session_state(self) -> SessionState:
        """Get current session state."""
        return self._session_state

    def get_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id

    def get_provider(self) -> Optional[RuntimeProvider]:
        """Get current provider."""
        return self._current_provider
