"""
Runtime Capability for IOS REVERSE KAISER.

Provides iOS runtime analysis through Frida/LLDB integration.

Maturity Level: L1 (Contract + basic implementation)
Target Level: L2 (Basic integration)
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass

from ios_reverse.capabilities.base import (
    CapabilityExecutor,
    CapabilityResult,
    Evidence,
    EvidenceType,
    EvidenceStrength,
)


@dataclass
class RuntimeObservation:
    """Runtime observation record."""
    timestamp: str
    provider: str
    type: str
    target: str
    data: Dict[str, Any]


class RuntimeAnalysisCapability(CapabilityExecutor):
    """
    Runtime analysis capability.

    Provides:
    - Device/session discovery
    - Process attachment
    - Module enumeration
    - Class enumeration
    - Method enumeration
    - Targeted tracing
    - Runtime observation capture
    """

    CAPABILITY_ID = "runtime.analysis"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()
        self._adapter = None

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    def dependencies(self) -> List[str]:
        """Required capabilities."""
        return ["bundle.unpack"]

    def supported_architectures(self) -> Set[str]:
        """Supported architectures."""
        return {"arm", "arm64"}

    def inputs(self) -> Dict[str, Any]:
        """Required inputs."""
        return {
            "target": "Bundle ID or PID",
            "device": "Optional device ID",
            "observation_type": "Type of observation (classes, modules, trace, etc.)",
            "scope": "Scope of observation (limited, targeted, broad)",
        }

    def outputs(self) -> Dict[str, Any]:
        """Capability outputs."""
        return {
            "devices": "Available devices/simulators",
            "processes": "Running processes",
            "modules": "Loaded modules",
            "classes": "Objective-C classes",
            "methods": "Methods of a class",
            "observations": "Runtime observations",
            "session_id": "Session identifier for resume",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """
        Execute runtime analysis.

        Args:
            context: Execution context with target, device, etc.

        Returns:
            CapabilityResult with runtime evidence
        """
        from datetime import datetime

        try:
            from ios_reverse.adapters.runtime import (
                RuntimeProviderAdapter,
                RuntimeProvider,
                SessionState,
            )
        except ImportError:
            return CapabilityResult.error("Runtime adapter not available")

        adapter = RuntimeProviderAdapter()
        availability = adapter.availability()

        if availability.value == "unavailable":
            return CapabilityResult(
                success=False,
                error="No runtime provider available (Frida or LLDB required)",
                evidence=[],
                metadata={
                    "availability": "unavailable",
                    "frida_check": "not_installed",
                    "lldb_check": "not_available",
                },
            )

        target = context.get("target")
        observation_type = context.get("observation_type", "generic")
        device = context.get("device")
        scope = context.get("scope", "limited")

        evidence_list = []

        # 1. List devices if requested
        if context.get("list_devices"):
            devices_result = adapter.execute("runtime.list_devices", {}, {})
            if devices_result.success and devices_result.normalized_output:
                devices = devices_result.normalized_output.get("devices", [])
                for device in devices:
                    evidence_list.append(Evidence(
                        evidence_id=f"runtime-device-{device.get('id', 'unknown')}",
                        evidence_type=EvidenceType.REFERENCE,
                        strength=EvidenceStrength.VERIFIED,
                        source_artifact="runtime",
                        content={
                            "type": "runtime_device",
                            "device_id": device.get("id"),
                            "name": device.get("name"),
                            "platform": device.get("platform"),
                        },
                        capability_id=self.capability_id,
                        metadata={"category": "device"},
                    ))

        # 2. Attach to target
        attach_result = adapter.execute(
            "runtime.attach" if scope != "spawn" else "runtime.spawn",
            {"target": target} if scope != "spawn" else {"bundle_id": target},
            {}
        )

        if not attach_result.success:
            return CapabilityResult(
                success=False,
                error=f"Failed to attach: {attach_result.error}",
                evidence=[],
                metadata={"stage": "attach"},
            )

        session_id = attach_result.normalized_output.get("session_id") if attach_result.normalized_output else None

        # 3. List modules
        if scope in ["limited", "targeted", "broad"]:
            modules_result = adapter.execute("runtime.list_modules", {"target": target}, {})
            if modules_result.success and modules_result.normalized_output:
                modules = modules_result.normalized_output.get("modules", [])
                for module in modules:
                    evidence_list.append(Evidence(
                        evidence_id=f"runtime-module-{module.get('name', 'unknown')}",
                        evidence_type=EvidenceType.STRUCTURAL,
                        strength=EvidenceStrength.VERIFIED,
                        source_artifact=f"runtime://{target}",
                        content={
                            "type": "runtime_module",
                            "name": module.get("name"),
                            "base": module.get("base"),
                            "size": module.get("size"),
                        },
                        capability_id=self.capability_id,
                        metadata={"category": "module", "session_id": session_id},
                    ))

        # 4. List classes
        if scope in ["limited", "targeted"]:
            classes_result = adapter.execute("runtime.list_classes", {"target": target}, {})
            if classes_result.success and classes_result.normalized_output:
                classes = classes_result.normalized_output.get("classes", [])
                for cls in classes[:500]:  # Limit to 500 classes
                    evidence_list.append(Evidence(
                        evidence_id=f"runtime-class-{cls.get('name', 'unknown')}",
                        evidence_type=EvidenceType.STRUCTURAL,
                        strength=EvidenceStrength.VERIFIED,
                        source_artifact=f"runtime://{target}",
                        content={
                            "type": "runtime_class",
                            "name": cls.get("name"),
                            "methods": cls.get("methods", []),
                            "properties": cls.get("properties", []),
                        },
                        capability_id=self.capability_id,
                        metadata={"category": "class", "session_id": session_id},
                    ))

        # 5. Enumerate methods if class specified
        if context.get("class_name"):
            methods_result = adapter.execute(
                "runtime.enumerate_methods",
                {"class_name": context.get("class_name")},
                {}
            )
            if methods_result.success and methods_result.normalized_output:
                methods_data = methods_result.normalized_output
                evidence_list.append(Evidence(
                    evidence_id=f"runtime-methods-{methods_data.get('class', 'unknown')}",
                    evidence_type=EvidenceType.STRUCTURAL,
                    strength=EvidenceStrength.VERIFIED,
                    source_artifact=f"runtime://{target}",
                    content={
                        "type": "runtime_methods",
                        "class": methods_data.get("class"),
                        "methods": methods_data.get("methods", []),
                    },
                    capability_id=self.capability_id,
                    metadata={"category": "methods", "session_id": session_id},
                ))

        # 6. Runtime observation
        observation_result = adapter.execute(
            "runtime.observation",
            {
                "type": observation_type,
                "target": target,
                "params": context.get("params", {}),
            },
            {}
        )

        if observation_result.success and observation_result.normalized_output:
            obs_data = observation_result.normalized_output
            evidence_list.append(Evidence(
                evidence_id=f"runtime-obs-{obs_data.get('timestamp', 'unknown')}",
                evidence_type=EvidenceType.DYNAMIC,
                strength=EvidenceStrength.DYNAMIC,
                source_artifact=f"runtime://{target}",
                content={
                    "type": "runtime_observation",
                    "timestamp": obs_data.get("timestamp"),
                    "provider": obs_data.get("provider"),
                    "observation_type": obs_data.get("type"),
                    "data": obs_data.get("data", {}),
                },
                capability_id=self.capability_id,
                metadata={
                    "category": "observation",
                    "session_id": session_id,
                },
            ))

        # 7. Detach
        adapter.execute("runtime.detach", {}, {})

        return CapabilityResult(
            success=True,
            evidence=evidence_list,
            metadata={
                "provider": adapter.get_provider().value if adapter.get_provider() else "unknown",
                "session_id": session_id,
                "session_state": adapter.get_session_state().value,
                "device_count": len([e for e in evidence_list if e.metadata.get("category") == "device"]),
                "module_count": len([e for e in evidence_list if e.metadata.get("category") == "module"]),
                "class_count": len([e for e in evidence_list if e.metadata.get("category") == "class"]),
                "observation_count": len([e for e in evidence_list if e.metadata.get("category") == "observation"]),
                "availability": availability.value,
            },
        )


class RuntimeSessionCapability(CapabilityExecutor):
    """Runtime session management capability."""

    CAPABILITY_ID = "runtime.session"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()
        self._adapter = None

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Manage runtime session lifecycle."""
        try:
            from ios_reverse.adapters.runtime import RuntimeProviderAdapter, SessionState
        except ImportError:
            return CapabilityResult.error("Runtime adapter not available")

        adapter = RuntimeProviderAdapter()
        action = context.get("action", "status")

        if action == "status":
            return CapabilityResult(
                success=True,
                evidence=[],
                metadata={
                    "availability": adapter.availability().value,
                    "session_state": adapter.get_session_state().value,
                    "session_id": adapter.get_session_id(),
                    "provider": adapter.get_provider().value if adapter.get_provider() else None,
                },
            )

        elif action == "detach":
            result = adapter.execute("runtime.detach", {}, {})
            return CapabilityResult(
                success=result.success,
                evidence=[],
                metadata={
                    "action": "detach",
                    "session_state": adapter.get_session_state().value,
                },
            )

        return CapabilityResult.error(f"Unknown action: {action}")
