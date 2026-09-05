"""
Ghidra Headless Adapter for IOS REVERSE KAISER.

Provides integration with Ghidra headless analyzer.

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
class GhidraFunction:
    """Ghidra function record."""
    address: int
    name: str
    signature: str
    calling_convention: str = ""
    local_variables: int = 0


@dataclass
class GhidraXref:
    """Ghidra cross-reference."""
    from_address: int
    to_address: int
    type: str


@dataclass
class GhidraDecompileResult:
    """Ghidra decompilation result."""
    address: int
    name: str
    pseudocode: str
    warnings: List[str] = field(default_factory=list)


class GhidraHeadlessAdapter(SubprocessAdapterContract):
    """
    Ghidra headless analyzer adapter.

    Uses Ghidra's headless analyzer for batch analysis and decompilation.

    Required Environment:
    - Ghidra installed with GHIDRA_INSTALL_DIR set
    - Java 11+

    Usage:
    analyzeHeadless <repo_path> <project_name> -import <binary> -scriptPath <scripts> ...
    """

    ADAPTER_ID = "ghidra-headless"
    VERSION = "0.1.0"
    TOOL_NAME = "Ghidra"

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {}
        self._ghidra_install_dir = self._detect_ghidra_install()

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
        """Check if Ghidra headless is available."""
        if not self._ghidra_install_dir:
            return ToolAvailability.UNAVAILABLE

        headless_path = Path(self._ghidra_install_dir) / "support" / "analyzeHeadless.bat"
        if not headless_path.exists():
            headless_path = Path(self._ghidra_install_dir) / "support" / "analyzeHeadless"

        if not headless_path.exists():
            return ToolAvailability.UNAVAILABLE

        return ToolAvailability.AVAILABLE

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
            health.reason = "Ghidra not found. Set GHIDRA_INSTALL_DIR or install Ghidra."
            health.suggested_fallback = "rizin"
        else:
            health.reason = f"Ghidra installed at {self._ghidra_install_dir}"

        return health

    def tool_version(self) -> Optional[str]:
        """Detect Ghidra version."""
        if not self._ghidra_install_dir:
            return None

        version_file = Path(self._ghidra_install_dir) / "version"
        if version_file.exists():
            return version_file.read_text().strip()

        return "Ghidra (version unknown)"

    def _detect_ghidra_install(self) -> Optional[str]:
        """Detect Ghidra installation directory."""
        import os

        # Check GHIDRA_INSTALL_DIR
        ghidra_dir = os.environ.get("GHIDRA_INSTALL_DIR")
        if ghidra_dir and Path(ghidra_dir).exists():
            return ghidra_dir

        # Common installation paths
        common_paths = [
            "C:\\ghidra",
            "C:\\Program Files\\Ghidra",
            "/opt/ghidra",
            "/usr/local/ghidra",
            str(Path.home() / "ghidra"),
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    def required_dependencies(self) -> List[Dict]:
        """List required dependencies."""
        return [
            {
                "name": "Ghidra",
                "required": True,
                "installed": bool(self._ghidra_install_dir),
            },
            {
                "name": "Java 11+",
                "required": True,
                "installed": self._check_java(),
            }
        ]

    def optional_dependencies(self) -> List[Dict]:
        """List optional dependencies."""
        return [
            {
                "name": "GHIDRA_INSTALL_DIR env var",
                "required": False,
                "installed": bool(os.environ.get("GHIDRA_INSTALL_DIR")),
            }
        ]

    def _check_java(self) -> bool:
        """Check if Java is available."""
        import os
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def supported_capabilities(self) -> Set[str]:
        """Set of capabilities this adapter supports."""
        return {
            "ghidra.analyze",
            "ghidra.list_functions",
            "ghidra.get_function",
            "ghidra.decompile",
            "ghidra.list_xrefs",
            "ghidra.list_strings",
            "ghidra.export_json",
        }

    def execute(
        self,
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult:
        """Execute Ghidra capability."""
        import time
        start = time.time()

        if self.availability() != ToolAvailability.AVAILABLE:
            return AdapterExecutionResult(
                success=False,
                error="Ghidra headless not available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        # Map capability to operation
        if capability_id == "ghidra.analyze":
            return self._analyze(inputs, context, start)
        elif capability_id == "ghidra.list_functions":
            return self._list_functions(inputs, context, start)
        elif capability_id == "ghidra.get_function":
            return self._get_function(inputs, context, start)
        elif capability_id == "ghidra.decompile":
            return self._decompile(inputs, context, start)
        elif capability_id == "ghidra.list_xrefs":
            return self._list_xrefs(inputs, context, start)
        elif capability_id == "ghidra.list_strings":
            return self._list_strings(inputs, context, start)
        elif capability_id == "ghidra.export_json":
            return self._export_json(inputs, context, start)

        return AdapterExecutionResult(
            success=False,
            error=f"Unknown capability: {capability_id}",
            failure_classification=FailureClassification.INVALID_INPUT,
        )

    def _analyze(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
        start: float
    ) -> AdapterExecutionResult:
        """Run Ghidra headless analysis."""
        target_path = inputs.get("target_path")
        if not target_path:
            return AdapterExecutionResult(
                success=False,
                error="target_path required",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        project_name = inputs.get("project_name", "kaiser_project")
        output_dir = inputs.get("output_dir", "ghidra_output")
        script_path = inputs.get("script_path", "")

        # Build analyzeHeadless command
        cmd = [
            str(Path(self._ghidra_install_dir) / "support" / "analyzeHeadless.bat"
                if subprocess.os.name == "nt" else
                Path(self._ghidra_install_dir) / "support" / "analyzeHeadless"),
            context.get("workspace", "."),  # Repository path
            project_name,
            "-import", target_path,
            "-scriptPath", script_path if script_path else "",
            "-postScript", "FunctionExporter.java",
            output_dir,
        ]

        # Filter empty args
        cmd = [c for c in cmd if c]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600000,  # 1 hour timeout
            )

            duration_ms = int((time.time() - start) * 1000)

            return AdapterExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration_ms=duration_ms,
                artifacts=[output_dir] if result.returncode == 0 else [],
            )

        except subprocess.TimeoutExpired:
            return AdapterExecutionResult(
                success=False,
                error="Ghidra analysis timed out",
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

    def _list_functions(self, inputs, context, start):
        """List functions from Ghidra analysis."""
        # Read from exported JSON
        output_dir = inputs.get("output_dir", "ghidra_output")
        functions_file = Path(output_dir) / "functions.json"

        if not functions_file.exists():
            return AdapterExecutionResult(
                success=False,
                error="Functions file not found. Run analysis first.",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        try:
            with open(functions_file) as f:
                data = json.load(f)
            return AdapterExecutionResult(
                success=True,
                duration_ms=int((time.time() - start) * 1000),
                normalized_output=data,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
                failure_classification=FailureClassification.PARSE_ERROR,
            )

    def _get_function(self, inputs, context, start):
        """Get single function details."""
        output_dir = inputs.get("output_dir", "ghidra_output")
        address = inputs.get("address")

        functions_file = Path(output_dir) / "functions.json"
        if not functions_file.exists():
            return AdapterExecutionResult(
                success=False,
                error="Functions file not found",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        try:
            with open(functions_file) as f:
                functions = json.load(f)

            for func in functions:
                if func.get("address") == address:
                    return AdapterExecutionResult(
                        success=True,
                        duration_ms=int((time.time() - start) * 1000),
                        normalized_output=func,
                    )

            return AdapterExecutionResult(
                success=False,
                error=f"Function not found: {address}",
                failure_classification=FailureClassification.INVALID_INPUT,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
            )

    def _decompile(self, inputs, context, start):
        """Decompile function."""
        output_dir = inputs.get("output_dir", "ghidra_output")
        address = inputs.get("address")

        decompiled_file = Path(output_dir) / "decompiled" / f"{address}.json"
        if not decompiled_file.exists():
            return AdapterExecutionResult(
                success=False,
                error="Decompiled output not found",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        try:
            with open(decompiled_file) as f:
                data = json.load(f)
            return AdapterExecutionResult(
                success=True,
                duration_ms=int((time.time() - start) * 1000),
                normalized_output=data,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
            )

    def _list_xrefs(self, inputs, context, start):
        """List cross-references."""
        output_dir = inputs.get("output_dir", "ghidra_output")
        xrefs_file = Path(output_dir) / "xrefs.json"

        if not xrefs_file.exists():
            return AdapterExecutionResult(
                success=False,
                error="Xrefs file not found",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        try:
            with open(xrefs_file) as f:
                data = json.load(f)
            return AdapterExecutionResult(
                success=True,
                duration_ms=int((time.time() - start) * 1000),
                normalized_output=data,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
            )

    def _list_strings(self, inputs, context, start):
        """List strings from Ghidra."""
        output_dir = inputs.get("output_dir", "ghidra_output")
        strings_file = Path(output_dir) / "strings.json"

        if not strings_file.exists():
            return AdapterExecutionResult(
                success=False,
                error="Strings file not found",
                failure_classification=FailureClassification.INVALID_INPUT,
            )

        try:
            with open(strings_file) as f:
                data = json.load(f)
            return AdapterExecutionResult(
                success=True,
                duration_ms=int((time.time() - start) * 1000),
                normalized_output=data,
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
            )

    def _export_json(self, inputs, context, start):
        """Export full analysis as JSON."""
        output_dir = inputs.get("output_dir", "ghidra_output")

        export_file = Path(output_dir) / "export.json"
        if not export_file.exists():
            return AdapterExecutionResult(
                success=False,
                error="Export file not found",
            )

        try:
            with open(export_file) as f:
                data = json.load(f)
            return AdapterExecutionResult(
                success=True,
                duration_ms=int((time.time() - start) * 1000),
                normalized_output=data,
                artifacts=[str(export_file)],
            )
        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                error=str(e),
            )

    def execute_raw(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None,
        timeout_ms: int = 3600000
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
        """Normalize Ghidra output."""
        return raw_output

    def configure(self, config: Dict[str, Any]):
        """Apply configuration."""
        self._config.update(config)

    def default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "timeout_ms": 3600000,  # 1 hour
            "ghidra_install_dir": self._ghidra_install_dir,
            "project_name": "kaiser_project",
            "output_dir": "ghidra_output",
        }
