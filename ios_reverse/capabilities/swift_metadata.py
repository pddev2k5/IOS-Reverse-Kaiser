"""
Swift Metadata Capabilities for IOS REVERSE KAISER.

CAP-016: swift.metadata - Swift metadata extraction
CAP-017: swift.demangle - Swift symbol demangling
"""

import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import field

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, EvidenceRecord, ProvenanceRecord
)
from ios_reverse.models.swift import (
    SwiftModel, SwiftDemangleResult, EvidenceStrength
)
from ios_reverse.adapters.swift.swift_adapter import SwiftAdapter
from ios_reverse.adapters.swift.swift_demangler import SwiftDemangler


# =============================================================================
# CAP-016: swift.metadata
# =============================================================================

class SwiftMetadataContract(CapabilityContract):
    """Contract for CAP-016 swift.metadata."""

    def __init__(self):
        super().__init__(
            id="swift.metadata",
            version="1.0.0",
            domain="swift",
            name="Swift Metadata",
            description="Extract Swift metadata from binary"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "extract_types", "type": "boolean", "default": True},
            {"name": "extract_protocols", "type": "boolean", "default": True},
            {"name": "extract_functions", "type": "boolean", "default": True},
            {"name": "sections", "type": "object", "required": False},
            {"name": "symbols", "type": "array", "required": False},
        ]
        self.supported_input_types = ["macho"]
        self.output_types = ["swift_types", "swift_protocols", "swift_functions"]
        self.required_adapters = []
        self.optional_adapters = ["swift_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Binary not found"},
            "E002": {"name": "EXTRACTION_FAILED", "description": "Metadata extraction failed"},
            "E003": {"name": "NO_SWIFT_METADATA", "description": "No Swift metadata found"},
        }
        self.warning_codes = {
            "W001": {"name": "PARTIAL_EXTRACTION", "description": "Some metadata could not be extracted"},
            "W002": {"name": "DEMANGLING_FAILED", "description": "Some symbols could not be demangled"},
        }


class SwiftMetadataCapability(CapabilityExecutor):
    """
    CAP-016: Extract and normalize Swift metadata.

    Extracts:
    - Swift types (structs, classes, enums)
    - Protocols
    - Conformance records
    - Fields
    - Functions
    - Symbols (with demangling)

    Distinguishes between:
    - Structurally parsed metadata
    - Symbol-derived information
    - String-derived hints
    """

    def __init__(self):
        super().__init__()
        self._adapter = SwiftAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return SwiftMetadataContract()

    def _generate_id(self) -> str:
        """Generate unique ID for this execution."""
        self._id_counter += 1
        return f"swift-meta-{self._id_counter:04d}"

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs before execution."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """
        Execute Swift metadata extraction.

        Args:
            inputs: Must contain artifact_path

        Returns:
            CapabilityResult with Swift metadata
        """
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        # Validate preconditions
        valid, error = self.validate_preconditions(inputs)
        if not valid:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E001",
                error_message=error
            )

        artifact_path = inputs["artifact_path"]

        try:
            # Extract metadata
            sections = inputs.get("sections")
            symbols = inputs.get("symbols")

            result = self._adapter.extract_metadata(
                artifact_path=artifact_path,
                sections=sections,
                symbols=symbols,
                compute_hashes=True
            )

            if not result.success:
                return CapabilityResult(
                    status=CapabilityStatus.FAILURE,
                    execution_id=execution_id,
                    timestamp=timestamp,
                    metadata={},
                    error_code="E002",
                    error_message=result.error or "Extraction failed"
                )

            # Extract model from result
            model_dict = result.metadata.get("model", {})

            # Check if we found any Swift
            if not model_dict.get("has_swift", False):
                return CapabilityResult(
                    status=CapabilityStatus.SUCCESS,
                    execution_id=execution_id,
                    timestamp=timestamp,
                    metadata={
                        "artifact_path": artifact_path,
                        "artifact_hash": model_dict.get("artifact_hash", ""),
                        "has_swift": False,
                        "type_count": 0,
                        "protocol_count": 0,
                        "symbol_count": 0,
                    },
                    provenance=self._build_provenance(execution_id, inputs)
                )

            # Build evidence records
            evidence = self._build_evidence(model_dict, execution_id, timestamp, artifact_path)

            # Build metadata output
            demangle_stats = model_dict.get("demangling_stats", {})

            metadata = {
                "artifact_path": artifact_path,
                "artifact_hash": model_dict.get("artifact_hash", ""),
                "file_size": model_dict.get("file_size", 0),
                "has_swift": model_dict.get("has_swift", False),
                "swift_version": model_dict.get("swift_version"),
                "module_count": model_dict.get("module_count", 0),
                "type_count": model_dict.get("type_count", 0),
                "protocol_count": model_dict.get("protocol_count", 0),
                "conformance_count": model_dict.get("conformance_count", 0),
                "field_count": model_dict.get("field_count", 0),
                "function_count": model_dict.get("function_count", 0),
                "symbol_count": model_dict.get("symbol_count", 0),
                "demangling_stats": demangle_stats,
                "sections_found": model_dict.get("sections_found", []),
                "evidence_distribution": model_dict.get("evidence_distribution", {}),
                # Include detailed entity lists
                "modules": model_dict.get("modules", [])[:20],
                "types": model_dict.get("types", [])[:50],
                "protocols": model_dict.get("protocols", [])[:50],
                "symbols": model_dict.get("symbols", [])[:100],
            }

            # Add warnings if needed
            warnings = []
            if demangle_stats.get("failed", 0) > 0:
                warnings.append(f"W002: {demangle_stats['failed']} symbols could not be demangled")
            if model_dict.get("warnings"):
                warnings.extend([f"W001: {w}" for w in model_dict["warnings"]])

            status = CapabilityStatus.SUCCESS
            if len(warnings) > 0:
                status = CapabilityStatus.PARTIAL

            return CapabilityResult(
                status=status,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata=metadata,
                evidence=evidence,
                provenance=self._build_provenance(execution_id, inputs),
                warnings=warnings
            )

        except Exception as e:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E002",
                error_message=str(e)
            )

    def _build_evidence(
        self,
        model_dict: Dict,
        execution_id: str,
        timestamp: datetime,
        artifact_path: str
    ) -> List[EvidenceRecord]:
        """Build evidence records for the extraction."""
        evidence = []

        # Create evidence for types
        for t in model_dict.get("types", [])[:20]:
            ev = EvidenceRecord(
                id=f"ev-{uuid.uuid4().hex[:8]}",
                type="derived",
                capability_id="swift.metadata",
                execution_id=execution_id,
                timestamp=timestamp,
                file_path=artifact_path,
                size=model_dict.get("file_size") if model_dict.get("file_size") else None,
                derived_from=["swift_adapter"],
                references={"type_name": t.get("name")}
            )
            evidence.append(ev)

        return evidence

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="swift.metadata",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="swift_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )


# =============================================================================
# CAP-017: swift.demangle
# =============================================================================

class SwiftDemangleContract(CapabilityContract):
    """Contract for CAP-017 swift.demangle."""

    def __init__(self):
        super().__init__(
            id="swift.demangle",
            version="1.0.0",
            domain="swift",
            name="Swift Demangle",
            description="Demangle Swift symbols"
        )
        self.required_inputs = [
            {"name": "symbols", "type": "array", "required": True}
        ]
        self.optional_inputs = [
            {"name": "backend", "type": "string", "default": "auto"},
            {"name": "preserve_mangled", "type": "boolean", "default": True},
        ]
        self.supported_input_types = []
        self.output_types = ["demangled_symbols"]
        self.required_adapters = []
        self.optional_adapters = ["swift_demangler"]
        self.error_codes = {
            "E001": {"name": "NO_SYMBOLS", "description": "No symbols provided"},
            "E002": {"name": "DEMANGLING_FAILED", "description": "Demangling failed"},
        }
        self.warning_codes = {}


class SwiftDemangleCapability(CapabilityExecutor):
    """
    CAP-017: Demangle Swift symbols with honest fallback.

    Supports multiple backends:
    1. swift-demangle tool (if available)
    2. xcrun swift-demangle (macOS)
    3. Python fallback (limited)

    IMPORTANT: Failed demangling is a valid result, not an error.
    """

    def __init__(self):
        super().__init__()
        self._demangler = SwiftDemangler()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return SwiftDemangleContract()

    def _generate_id(self) -> str:
        """Generate unique ID for this execution."""
        self._id_counter += 1
        return f"swift-dem-{self._id_counter:04d}"

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs before execution."""
        symbols = inputs.get("symbols", [])

        if not symbols:
            return False, "symbols array is required"

        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """
        Execute Swift demangling.

        Args:
            inputs: Must contain symbols array

        Returns:
            CapabilityResult with demangled symbols
        """
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        # Validate preconditions
        valid, error = self.validate_preconditions(inputs)
        if not valid:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E001",
                error_message=error
            )

        symbols = inputs["symbols"]
        preserve_mangled = inputs.get("preserve_mangled", True)
        backend_used = self._demangler.get_backend()

        try:
            results = []
            success_count = 0
            fail_count = 0

            for symbol in symbols:
                # Handle both string and dict inputs
                if isinstance(symbol, str):
                    mangled = symbol
                    original_address = None
                else:
                    mangled = symbol.get("name", "")
                    original_address = symbol.get("address")

                if not mangled:
                    continue

                result = self._demangler.demangle(mangled)

                result_dict = {
                    "mangled_name": result.mangled_name,
                    "demangled_name": result.demangled_name,
                    "success": result.success,
                    "demangler_used": result.demangler_used,
                    "evidence": result.evidence.value,
                }

                if original_address is not None:
                    result_dict["address"] = original_address

                if not result.success and result.error:
                    result_dict["error"] = result.error

                results.append(result_dict)

                if result.success:
                    success_count += 1
                else:
                    fail_count += 1

            metadata = {
                "backend_used": backend_used,
                "total_symbols": len(results),
                "succeeded": success_count,
                "failed": fail_count,
                "results": results,
            }

            # Determine status
            status = CapabilityStatus.SUCCESS
            warnings = []

            if fail_count > 0 and success_count == 0:
                # All failed - still a valid result
                status = CapabilityStatus.PARTIAL
                warnings.append(f"All {fail_count} symbols failed demangling")

            return CapabilityResult(
                status=status,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata=metadata,
                provenance=self._build_provenance(execution_id, inputs)
            )

        except Exception as e:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E002",
                error_message=str(e)
            )

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="swift.demangle",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={"symbol_count": len(inputs.get("symbols", []))},
            adapter_id="swift_demangler",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the demangling backend."""
        return {
            "backend": self._demangler.get_backend(),
            "available": self._demangler.is_available(),
        }
