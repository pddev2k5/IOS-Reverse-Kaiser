"""
IDA Analysis Capability for IOS REVERSE KAISER.

Provides IDA Pro analysis capabilities through MCP integration.

Maturity Level: L1 (Contract + basic implementation)
Target Level: L3 (Full integration)
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path

from ios_reverse.capabilities.base import (
    CapabilityExecutor,
    CapabilityResult,
    Evidence,
    EvidenceType,
    EvidenceStrength,
)


@dataclass
class IDAFunction:
    """IDA function record for evidence."""
    address: int
    name: str
    size: int
    flags: List[str]


@dataclass
class IDAXref:
    """IDA cross-reference for evidence."""
    from_address: int
    to_address: int
    type: str


class IDAAnalysisCapability(CapabilityExecutor):
    """
    IDA Pro analysis capability.

    Provides:
    - Function listing
    - Import/export analysis
    - String listing
    - Cross-reference analysis
    - Caller/callee tracing
    - Target verification
    - Evidence export
    """

    CAPABILITY_ID = "ida.analysis"
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
        return ["bundle.unpack", "macho.basic"]

    def supported_architectures(self) -> Set[str]:
        """Supported architectures."""
        return {"arm", "arm64", "x86", "x86_64"}

    def inputs(self) -> Dict[str, Any]:
        """Required inputs."""
        return {
            "artifact_path": "Path to IPA or extracted app",
            "component": "Optional specific component",
            "target_functions": "Optional list of function addresses",
        }

    def outputs(self) -> Dict[str, Any]:
        """Capability outputs."""
        return {
            "functions": "List of IDAFunction records",
            "imports": "List of imported functions",
            "exports": "List of exported functions",
            "strings": "List of strings with addresses",
            "xrefs": "List of cross-references",
            "callers": "Dict of function -> callers",
            "callees": "Dict of function -> callees",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """
        Execute IDA analysis.

        Args:
            context: Execution context with artifact_path, component, etc.

        Returns:
            CapabilityResult with evidence
        """
        artifact_path = context.get("artifact_path")
        component = context.get("component")
        target_functions = context.get("target_functions", [])

        if not artifact_path:
            return CapabilityResult.error("artifact_path required")

        # Check if adapter is available
        try:
            from ios_reverse.adapters.ida import IDAMCPAdapter
            adapter = IDAMCPAdapter()

            if adapter.availability().value == "unavailable":
                return CapabilityResult(
                    success=False,
                    error="IDA Pro MCP not available",
                    evidence=[],
                    metadata={"availability": "unavailable"},
                )
        except ImportError:
            return CapabilityResult(
                success=False,
                error="IDA adapter not available",
                evidence=[],
                metadata={"adapter": "not_found"},
            )

        # Build evidence
        evidence_list = []

        # 1. Verify target (if IDB loaded)
        if context.get("idb_path"):
            is_valid, reason = adapter.verify_target(
                artifact_path,
                context.get("expected_hash")
            )
            if not is_valid:
                return CapabilityResult(
                    success=False,
                    error=f"Target verification failed: {reason}",
                    evidence=[],
                    metadata={"verification": "failed"},
                )

        # 2. List functions
        functions_result = adapter.execute("ida.list_functions", {"path": artifact_path}, {})
        if functions_result.success:
            functions = adapter.normalize_output("ida.list_functions", functions_result.normalized_output)
            for func in functions:
                evidence_list.append(Evidence(
                    evidence_id=f"ida-func-{func.get('address', 0):x}",
                    evidence_type=EvidenceType.STRUCTURAL,
                    strength=EvidenceStrength.STRUCTURAL,
                    source_artifact=artifact_path,
                    content={
                        "type": "ida_function",
                        "address": func.get("address"),
                        "name": func.get("name"),
                        "size": func.get("size"),
                    },
                    capability_id=self.capability_id,
                    metadata={"category": "function"},
                ))

        # 3. List imports
        imports_result = adapter.execute("ida.list_imports", {"path": artifact_path}, {})
        if imports_result.success:
            imports = adapter.normalize_output("ida.list_imports", imports_result.normalized_output)
            for imp in imports:
                evidence_list.append(Evidence(
                    evidence_id=f"ida-imp-{imp.get('name', 'unknown')}",
                    evidence_type=EvidenceType.STRUCTURAL,
                    strength=EvidenceStrength.STRING_HINT,
                    source_artifact=artifact_path,
                    content={
                        "type": "ida_import",
                        "name": imp.get("name"),
                        "library": imp.get("library"),
                    },
                    capability_id=self.capability_id,
                    metadata={"category": "import"},
                ))

        # 4. List exports
        exports_result = adapter.execute("ida.list_exports", {"path": artifact_path}, {})
        if exports_result.success:
            exports = adapter.normalize_output("ida.list_exports", exports_result.normalized_output)
            for exp in exports:
                evidence_list.append(Evidence(
                    evidence_id=f"ida-exp-{exp.get('name', 'unknown')}",
                    evidence_type=EvidenceType.STRUCTURAL,
                    strength=EvidenceStrength.STRING_HINT,
                    source_artifact=artifact_path,
                    content={
                        "type": "ida_export",
                        "name": exp.get("name"),
                        "address": exp.get("address"),
                    },
                    capability_id=self.capability_id,
                    metadata={"category": "export"},
                ))

        # 5. List strings
        strings_result = adapter.execute("ida.list_strings", {"path": artifact_path}, {})
        if strings_result.success:
            strings = adapter.normalize_output("ida.list_strings", strings_result.normalized_output)
            for s in strings[:1000]:  # Limit to 1000 strings
                evidence_list.append(Evidence(
                    evidence_id=f"ida-str-{s.get('address', 0):x}",
                    evidence_type=EvidenceType.STRING_HINT,
                    strength=EvidenceStrength.STRING_HINT,
                    source_artifact=artifact_path,
                    content={
                        "type": "ida_string",
                        "address": s.get("address"),
                        "value": s.get("value"),
                        "length": s.get("length"),
                    },
                    capability_id=self.capability_id,
                    metadata={"category": "string"},
                ))

        # 6. Analyze xrefs for target functions
        if target_functions:
            for func_addr in target_functions:
                xrefs_result = adapter.execute(
                    "ida.get_xrefs",
                    {"address": func_addr},
                    {}
                )
                if xrefs_result.success:
                    xrefs = adapter.normalize_output("ida.get_xrefs", xrefs_result.normalized_output)
                    for xref in xrefs:
                        evidence_list.append(Evidence(
                            evidence_id=f"ida-xref-{xref.get('from_addr', 0):x}",
                            evidence_type=EvidenceType.STRUCTURAL,
                            strength=EvidenceStrength.CORRELATED,
                            source_artifact=artifact_path,
                            content={
                                "type": "ida_xref",
                                "from_address": xref.get("from_addr"),
                                "to_address": xref.get("to_addr"),
                                "xref_type": xref.get("type"),
                            },
                            capability_id=self.capability_id,
                            metadata={"category": "xref", "target": func_addr},
                        ))

        # 7. Analyze callers/callees
        if target_functions:
            for func_addr in target_functions:
                refs_result = adapter.execute(
                    "ida.get_func_refs",
                    {"address": func_addr},
                    {}
                )
                if refs_result.success:
                    refs = adapter.normalize_output("ida.get_func_refs", refs_result.normalized_output)
                    evidence_list.append(Evidence(
                        evidence_id=f"ida-refs-{func_addr:x}",
                        evidence_type=EvidenceType.CORRELATED,
                        strength=EvidenceStrength.CORRELATED,
                        source_artifact=artifact_path,
                        content={
                            "type": "ida_callers_callees",
                            "function": func_addr,
                            "callers": refs.get("callers", []),
                            "callees": refs.get("callees", []),
                        },
                        capability_id=self.capability_id,
                        metadata={"category": "call_graph"},
                    ))

        return CapabilityResult(
            success=True,
            evidence=evidence_list,
            metadata={
                "adapter": "ida-pro-mcp",
                "artifact": artifact_path,
                "function_count": len([e for e in evidence_list if e.metadata.get("category") == "function"]),
                "import_count": len([e for e in evidence_list if e.metadata.get("category") == "import"]),
                "export_count": len([e for e in evidence_list if e.metadata.get("category") == "export"]),
                "string_count": len([e for e in evidence_list if e.metadata.get("category") == "string"]),
                "xref_count": len([e for e in evidence_list if e.metadata.get("category") == "xref"]),
            },
        )


class IDATargetVerificationCapability(CapabilityExecutor):
    """IDA target verification capability."""

    CAPABILITY_ID = "ida.target_verification"
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
        """
        Verify IDA target matches expected binary.

        Returns:
            CapabilityResult with verification status
        """
        idb_path = context.get("idb_path")
        expected_path = context.get("expected_path")
        expected_hash = context.get("expected_hash")

        if not idb_path:
            return CapabilityResult.error("idb_path required")

        try:
            from ios_reverse.adapters.ida import IDAMCPAdapter
            adapter = IDAMCPAdapter()

            if adapter.availability().value == "unavailable":
                return CapabilityResult(
                    success=False,
                    error="IDA Pro MCP not available",
                    evidence=[],
                    metadata={"availability": "unavailable"},
                )

            is_valid, reason = adapter.verify_target(expected_path, expected_hash)

            evidence_list = []
            if is_valid:
                evidence_list.append(Evidence(
                    evidence_id="ida-verification-success",
                    evidence_type=EvidenceType.REFERENCE,
                    strength=EvidenceStrength.VERIFIED,
                    source_artifact=idb_path,
                    content={"verification": "passed", "target": expected_path},
                    capability_id=self.capability_id,
                ))

            return CapabilityResult(
                success=is_valid,
                evidence=evidence_list,
                metadata={
                    "verification": "passed" if is_valid else "failed",
                    "reason": reason,
                },
            )
        except ImportError:
            return CapabilityResult(
                success=False,
                error="IDA adapter not available",
                evidence=[],
            )
