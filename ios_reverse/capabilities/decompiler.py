"""
Decompiler Capability for IOS REVERSE KAISER.

Provides unified decompilation through available providers (IDA, Ghidra, rizin).

Maturity Level: L1 (Contract + basic implementation)
Target Level: L3 (Full provider integration)
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


class DecompilerCapability(CapabilityExecutor):
    """
    Decompiler capability.

    Provides unified decompilation interface through provider selection:
    1. IDA Pro (preferred)
    2. Ghidra
    3. rizin (limited)
    """

    CAPABILITY_ID = "decompiler.analyze"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()
        self._manager = None

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
            "binary_path": "Path to binary",
            "function_addresses": "Optional list of addresses to decompile",
            "provider": "Optional specific provider (ida, ghidra, rizin)",
        }

    def outputs(self) -> Dict[str, Any]:
        """Capability outputs."""
        return {
            "functions": "List of decompiled functions",
            "provider": "Provider used",
            "quality": "Decompilation quality assessment",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """
        Execute decompilation.

        Args:
            context: Execution context with binary_path, etc.

        Returns:
            CapabilityResult with decompiled functions as evidence
        """
        binary_path = context.get("binary_path")
        function_addresses = context.get("function_addresses", [])
        provider_preference = context.get("provider")

        if not binary_path:
            return CapabilityResult.error("binary_path required")

        # Import manager
        try:
            from ios_reverse.adapters.decompiler import (
                DecompilerManager,
                DecompilerProvider,
            )
            from ios_reverse.adapters.ida import IDAMCPAdapter
            from ios_reverse.adapters.ghidra import GhidraHeadlessAdapter
            from ios_reverse.adapters.rizin import RizinAdapter
        except ImportError as e:
            return CapabilityResult.error(f"Adapter not available: {e}")

        # Create and configure manager
        manager = DecompilerManager()

        # Register providers
        ida_adapter = IDAMCPAdapter()
        ghidra_adapter = GhidraHeadlessAdapter()
        rizin_adapter = RizinAdapter()

        manager.register_provider(DecompilerProvider.IDA, ida_adapter)
        manager.register_provider(DecompilerProvider.GHIDRA, ghidra_adapter)
        manager.register_provider(DecompilerProvider.RIZIN, rizin_adapter)

        # Select provider
        if provider_preference:
            # Use specified provider
            provider_map = {
                "ida": DecompilerProvider.IDA,
                "ghidra": DecompilerProvider.GHIDRA,
                "rizin": DecompilerProvider.RIZIN,
            }
            selected = provider_map.get(provider_preference.lower())
            if selected and selected in [
                DecompilerProvider.IDA,
                DecompilerProvider.GHIDRA,
                DecompilerProvider.RIZIN,
            ]:
                adapter = {
                    DecompilerProvider.IDA: ida_adapter,
                    DecompilerProvider.GHIDRA: ghidra_adapter,
                    DecompilerProvider.RIZIN: rizin_adapter,
                }.get(selected)
                if adapter and adapter.availability().value == "available":
                    manager._selected_provider = selected
        else:
            # Auto-select best available
            manager.select_best_provider()

        selected_provider = manager.get_provider()
        if not selected_provider:
            return CapabilityResult(
                success=False,
                error="No decompiler provider available (need IDA, Ghidra, or rizin)",
                evidence=[],
                metadata={
                    "ida_available": ida_adapter.availability().value,
                    "ghidra_available": ghidra_adapter.availability().value,
                    "rizin_available": rizin_adapter.availability().value,
                },
            )

        # Build evidence
        evidence_list = []

        # List functions
        list_result = manager.list_functions(binary_path)
        if list_result.success and list_result.normalized_output:
            functions = list_result.normalized_output
            if isinstance(functions, list):
                for func in functions[:100]:  # Limit to 100 functions
                    evidence_list.append(Evidence(
                        evidence_id=f"decomp-func-{func.get('address', 0):x}",
                        evidence_type=EvidenceType.STRUCTURAL,
                        strength=EvidenceStrength.STRUCTURAL,
                        source_artifact=binary_path,
                        content={
                            "type": "decompiled_function",
                            "address": func.get("address"),
                            "name": func.get("name"),
                            "size": func.get("size"),
                            "provider": selected_provider.value,
                        },
                        capability_id=self.capability_id,
                        metadata={
                            "category": "function",
                            "provider": selected_provider.value,
                        },
                    ))

        # Decompile specific functions if requested
        if function_addresses:
            for addr in function_addresses:
                decomp_result = manager.decompile_function(binary_path, addr)
                if decomp_result.success and decomp_result.normalized_output:
                    func_data = decomp_result.normalized_output
                    evidence_list.append(Evidence(
                        evidence_id=f"decomp-pseudo-{addr:x}",
                        evidence_type=EvidenceType.CORRELATED,
                        strength=EvidenceStrength.CORRELATED,
                        source_artifact=binary_path,
                        content={
                            "type": "pseudocode",
                            "address": addr,
                            "pseudocode": func_data.get("pseudocode", ""),
                            "provider": selected_provider.value,
                        },
                        capability_id=self.capability_id,
                        metadata={
                            "category": "pseudocode",
                            "provider": selected_provider.value,
                        },
                    ))

        return CapabilityResult(
            success=True,
            evidence=evidence_list,
            metadata={
                "provider": selected_provider.value,
                "function_count": len([e for e in evidence_list if e.metadata.get("category") == "function"]),
                "pseudocode_count": len([e for e in evidence_list if e.metadata.get("category") == "pseudocode"]),
            },
        )


class XrefAnalysisCapability(CapabilityExecutor):
    """
    Cross-reference analysis capability.

    Analyzes cross-references to/from functions.
    """

    CAPABILITY_ID = "decompiler.xref_analysis"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()
        self._manager = None

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
        return ["decompiler.analyze"]

    def inputs(self) -> Dict[str, Any]:
        return {
            "binary_path": "Path to binary",
            "target_address": "Address to analyze xrefs for",
        }

    def outputs(self) -> Dict[str, Any]:
        return {
            "xrefs": "Cross-references to/from address",
            "callers": "Functions calling target",
            "callees": "Functions called by target",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Execute xref analysis."""
        binary_path = context.get("binary_path")
        target_address = context.get("target_address")

        if not binary_path:
            return CapabilityResult.error("binary_path required")

        try:
            from ios_reverse.adapters.decompiler import DecompilerManager, DecompilerProvider
            from ios_reverse.adapters.ida import IDAMCPAdapter
            from ios_reverse.adapters.ghidra import GhidraHeadlessAdapter
            from ios_reverse.adapters.rizin import RizinAdapter
        except ImportError:
            return CapabilityResult.error("Adapters not available")

        manager = DecompilerManager()
        manager.register_provider(DecompilerProvider.IDA, IDAMCPAdapter())
        manager.register_provider(DecompilerProvider.GHIDRA, GhidraHeadlessAdapter())
        manager.register_provider(DecompilerProvider.RIZIN, RizinAdapter())
        manager.select_best_provider()

        if not manager.get_provider():
            return CapabilityResult.error("No provider available")

        evidence_list = []

        # Get xrefs
        if target_address:
            xrefs_result = manager.get_xrefs(binary_path, target_address)
            if xrefs_result.success and xrefs_result.normalized_output:
                for xref in xrefs_result.normalized_output:
                    evidence_list.append(Evidence(
                        evidence_id=f"xref-{xref.get('from_addr', 0):x}",
                        evidence_type=EvidenceType.STRUCTURAL,
                        strength=EvidenceStrength.CORRELATED,
                        source_artifact=binary_path,
                        content={
                            "type": "xref",
                            "from_address": xref.get("from_addr"),
                            "to_address": xref.get("to_addr"),
                            "xref_type": xref.get("type"),
                        },
                        capability_id=self.capability_id,
                    ))

            # Get callers
            callers_result = manager.get_callers(binary_path, target_address)
            if callers_result.success and callers_result.normalized_output:
                evidence_list.append(Evidence(
                    evidence_id=f"callers-{target_address:x}",
                    evidence_type=EvidenceType.CORRELATED,
                    strength=EvidenceStrength.CORRELATED,
                    source_artifact=binary_path,
                    content={
                        "type": "callers",
                        "function": target_address,
                        "callers": callers_result.normalized_output,
                    },
                    capability_id=self.capability_id,
                ))

            # Get callees
            callees_result = manager.get_callees(binary_path, target_address)
            if callees_result.success and callees_result.normalized_output:
                evidence_list.append(Evidence(
                    evidence_id=f"callees-{target_address:x}",
                    evidence_type=EvidenceType.CORRELATED,
                    strength=EvidenceStrength.CORRELATED,
                    source_artifact=binary_path,
                    content={
                        "type": "callees",
                        "function": target_address,
                        "callees": callees_result.normalized_output,
                    },
                    capability_id=self.capability_id,
                ))

        return CapabilityResult(
            success=True,
            evidence=evidence_list,
            metadata={
                "provider": manager.get_provider().value if manager.get_provider() else "none",
                "xref_count": len([e for e in evidence_list if e.content.get("type") == "xref"]),
            },
        )
