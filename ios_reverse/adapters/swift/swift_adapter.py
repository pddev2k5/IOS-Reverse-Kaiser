"""
Swift metadata adapter for IOS REVERSE KAISER.

Extracts Swift metadata from Mach-O binaries.
"""

import struct
import hashlib
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from ios_reverse.adapters.base import ToolInfo

from ios_reverse.models.swift import (
    SwiftModel, SwiftModule, SwiftType, SwiftProtocol, SwiftConformance,
    SwiftField, SwiftFunction, SwiftSymbol, SwiftMetadataReference,
    SwiftAddress, SwiftDemangleResult, EvidenceStrength, AddressType
)
from ios_reverse.adapters.base import AdapterResult, ToolAdapter
from ios_reverse.adapters.swift.swift_demangler import SwiftDemangler


# Swift 5 section names
SWIFT5_SECTIONS = [
    "__swift5_types",
    "__swift5_proto",
    "__swift5_protos",
    "__swift5_fieldmd",
    "__swift5_reflstr",
    "__swift5_typeref",
    "__swift5_assocty",
    "__swift5_capture",
    "__swift5_builtin",
    "__swift5_stub",
    "__swift5_refldata",
]

# Swift symbol patterns
SWIFT_SYMBOL_PATTERNS = [
    (r'^_\$s', True),  # Modern Swift mangled
    (r'^\$s', True),
    (r'^_T', True),    # Old Swift
    (r'^_\$Ss', False), # Other Swift-like
]


class SwiftAdapter(ToolAdapter):
    """
    Adapter for extracting Swift metadata from Mach-O binaries.

    Uses section parsing for structural extraction and symbol analysis.
    Distinguishes between structural metadata and symbol hints.
    """

    def __init__(self):
        super().__init__("swift_adapter", "1.0.0")
        self._id_counter = 0
        self._demangler = SwiftDemangler()

    def _next_id(self) -> str:
        """Generate unique ID."""
        self._id_counter += 1
        return f"swift-{self._id_counter:04d}"

    def _make_address(self, value: int, addr_type: AddressType, slice_idx: int = 0) -> SwiftAddress:
        """Create a SwiftAddress."""
        return SwiftAddress(value=value, address_type=addr_type, slice_index=slice_idx)

    def is_available(self) -> bool:
        """Adapter is always available (has Python fallback)."""
        return True

    def get_tool_info(self) -> ToolInfo:
        """Get information about the adapter."""
        return ToolInfo(
            name="swift_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        """Validate environment - always valid for pure Python."""
        return True, None

    def execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[bytes] = None
    ):
        """Execute is not used for pure Python adapter."""
        from ios_reverse.adapters.base import AdapterResult
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def get_capabilities(self) -> List[str]:
        """Return supported capabilities."""
        return [
            "metadata_extraction",
            "structural_parsing",
            "symbol_analysis",
            "demangling"
        ]

    def get_demangler_backend(self) -> str:
        """Get the demangling backend in use."""
        return self._demangler.get_backend()

    def extract_metadata(
        self,
        artifact_path: str,
        sections: Optional[Dict[str, bytes]] = None,
        symbols: Optional[List[Dict[str, Any]]] = None,
        slice_index: int = 0,
        compute_hashes: bool = False
    ) -> AdapterResult:
        """
        Extract Swift metadata from a binary.

        Args:
            artifact_path: Path to the Mach-O binary
            sections: Dict of section_name -> section_data
            symbols: List of symbol info
            slice_index: Architecture slice index
            compute_hashes: Whether to compute file hashes

        Returns:
            AdapterResult with SwiftModel in metadata["model"]
        """
        try:
            model = SwiftModel(artifact_path=artifact_path)

            if compute_hashes and os.path.exists(artifact_path):
                with open(artifact_path, 'rb') as f:
                    model.artifact_hash = hashlib.sha256(f.read()).hexdigest()
                    model.file_size = os.path.getsize(artifact_path)

            # Extract from sections
            if sections:
                self._extract_from_sections(model, sections, slice_index)
            else:
                model.warnings.append("No Swift sections provided")

            # Extract from symbols
            if symbols:
                self._extract_from_symbols(model, symbols, slice_index)

            # Build indexes
            model.build_indexes()

            # Detect Swift version if possible
            if "__swift5" in str(model.sections_found):
                model.swift_version = "5.0"

            # Check if we found any Swift
            model.has_swift = (
                len(model.types) > 0 or
                len(model.protocols) > 0 or
                len(model.modules) > 0 or
                len(model.symbols) > 0
            )

            return AdapterResult(
                success=True,
                metadata={"model": self._model_to_dict(model)},
                artifacts=[artifact_path]
            )

        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Swift extraction failed: {str(e)}"
            )

    def _extract_from_sections(
        self,
        model: SwiftModel,
        sections: Dict[str, bytes],
        slice_index: int
    ):
        """Extract Swift metadata from Mach-O sections."""

        # Track which Swift sections we found
        model.sections_found = [
            name for name in sections.keys()
            if name.startswith("__swift5_") or name.startswith("__swift4_")
        ]

        # Extract reflection strings
        if "__swift5_reflstr" in sections:
            self._extract_reflection_strings(model, sections["__swift5_reflstr"], slice_index)

        # Extract type references
        if "__swift5_typeref" in sections:
            self._extract_type_references(model, sections["__swift5_typeref"], slice_index)

        # Extract field metadata
        if "__swift5_fieldmd" in sections:
            self._extract_field_metadata(model, sections["__swift5_fieldmd"], slice_index)

        # Extract protocol conformances
        if "__swift5_protos" in sections or "__swift5_proto" in sections:
            section_name = "__swift5_protos" if "__swift5_protos" in sections else "__swift5_proto"
            self._extract_protocols(model, sections[section_name], slice_index)

        # Extract type descriptors
        if "__swift5_types" in sections:
            self._extract_type_descriptors(model, sections["__swift5_types"], slice_index)

    def _extract_reflection_strings(
        self,
        model: SwiftModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract reflection strings from __swift5_reflstr."""
        # Reflection strings are null-terminated C strings
        offset = 0
        strings_found = []

        while offset < len(section_data):
            null_pos = section_data.find(b'\x00', offset)
            if null_pos < 0:
                break

            string_data = section_data[offset:null_pos]
            if 1 < len(string_data) < 512:
                try:
                    str_value = string_data.decode('utf-8', errors='replace')
                    if str_value and not str_value.startswith("\x00"):
                        strings_found.append((offset, str_value))
                except:
                    pass

            offset = null_pos + 1

        # Create type hints from strings that look like Swift names
        for str_offset, str_value in strings_found:
            # Swift type names typically:
            # - Start with uppercase letter for types
            # - Contain no spaces
            # - May have module prefix like ModuleName.TypeName

            if not str_value:
                continue

            # Skip if it looks like ObjC
            if str_value.startswith("+[") or str_value.startswith("-["):
                continue

            # Check if it looks like a Swift type
            is_type = str_value[0].isupper() if str_value else False
            is_likely_swift = (
                is_type and
                len(str_value) > 2 and
                not '_' in str_value.split('.')[-1]  # No underscore in final component
            )

            if is_likely_swift:
                swift_type = SwiftType(
                    id=self._next_id(),
                    name=str_value.split('.')[-1],  # Use just the type name
                    mangled_name=str_value,  # Reflection string as hint
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.types.append(swift_type)

    def _extract_type_references(
        self,
        model: SwiftModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract type references from __swift5_typeref."""
        # Type references are relative pointers into the reflection strings section
        # Format: relative pointer (4 bytes) pointing to type name string

        pointer_size = 4  # Relative pointers
        count = len(section_data) // pointer_size

        for i in range(min(count, 1000)):  # Limit processing
            offset = i * pointer_size
            if offset + pointer_size > len(section_data):
                break

            try:
                # Read relative offset (little-endian)
                rel_offset = struct.unpack('<I', section_data[offset:offset + pointer_size])[0]

                # Create a reference
                ref = SwiftMetadataReference(
                    id=self._next_id(),
                    reference_type="typeref",
                    source_id=f"typeref_{i}",
                    target_id=f"type_{rel_offset:x}",
                    source_name=f"TypeRef_{i}",
                    target_name=f"Offset_{rel_offset:x}",
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.references.append(ref)
            except Exception:
                break

    def _extract_field_metadata(
        self,
        model: SwiftModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract field metadata from __swift5_fieldmd."""
        # Field metadata contains field descriptors
        # Each descriptor: type reference, field name offset, flags, etc.

        # This is complex structure - for now extract what we can
        # Field metadata is typically variable-length

        offset = 0
        field_count = 0

        while offset < len(section_data) and field_count < 500:
            # Try to read field metadata
            # Structure varies by Swift version
            try:
                # Minimum field descriptor size
                if offset + 8 > len(section_data):
                    break

                # Read field count and first offset
                # This is simplified - real parsing needs version-specific structures

                field = SwiftField(
                    id=self._next_id(),
                    name=f"field_{field_count}",
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.fields.append(field)
                field_count += 1
                offset += 8  # Advance (simplified)
            except Exception:
                break

    def _extract_protocols(
        self,
        model: SwiftModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract protocol metadata."""
        # Protocol list contains pointers to protocol descriptors
        pointer_size = 8
        count = len(section_data) // pointer_size

        for i in range(min(count, 100)):
            offset = i * pointer_size
            if offset + pointer_size > len(section_data):
                break

            try:
                ptr_value = struct.unpack('<Q', section_data[offset:offset + pointer_size])[0]

                proto = SwiftProtocol(
                    id=self._next_id(),
                    name=f"Protocol_{ptr_value:x}",
                    address=self._make_address(ptr_value, AddressType.VM_ADDRESS, slice_index),
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.protocols.append(proto)
            except Exception:
                break

    def _extract_type_descriptors(
        self,
        model: SwiftModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract type descriptors from __swift5_types."""
        # Type descriptors contain nominal type information
        # Each descriptor: kind, name offset, etc.

        offset = 0
        type_count = 0

        while offset < len(section_data) and type_count < 500:
            try:
                if offset + 16 > len(section_data):
                    break

                # Read type descriptor header
                kind = struct.unpack('<I', section_data[offset:offset + 4])[0]
                name_offset = struct.unpack('<I', section_data[offset + 4:offset + 8])[0]

                # Create a type entry
                swift_type = SwiftType(
                    id=self._next_id(),
                    name=f"Type_{offset:x}",
                    kind=self._get_type_kind_name(kind),
                    nominal_descriptor_offset=offset,
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.types.append(swift_type)
                type_count += 1
                offset += 16  # Advance
            except Exception:
                break

    def _get_type_kind_name(self, kind: int) -> str:
        """Map type kind to name."""
        kinds = {
            0: "struct",
            1: "enum",
            2: "class",
            3: "protocol",
            4: "class_protocol",
            5: "metatype",
            6: "existential",
        }
        return kinds.get(kind, "unknown")

    def _extract_from_symbols(
        self,
        model: SwiftModel,
        symbols: List[Dict[str, Any]],
        slice_index: int
    ):
        """Extract Swift metadata from symbol table."""

        swift_symbols = []
        mangled_count = 0

        for sym in symbols:
            name = sym.get("name", "")
            if not name:
                continue

            # Check if it's a Swift mangled symbol
            is_swift = self._is_swift_symbol(name)

            if is_swift:
                mangled_count += 1

                # Demangle
                demangle_result = self._demangler.demangle(name)
                model.demangle_results.append(demangle_result)

                if demangle_result.success:
                    model.demangling_succeeded += 1
                else:
                    model.demangling_failed += 1

                model.demangling_attempted += 1

                # Create Swift symbol
                swift_sym = SwiftSymbol(
                    id=self._next_id(),
                    name=demangle_result.demangled_name or name,
                    mangled_name=name,
                    demangled_name=demangle_result.demangled_name,
                    demangling_status="success" if demangle_result.success else "failed",
                    demangler_used=demangle_result.demangler_used,
                    evidence=EvidenceStrength.MANGLED_SYMBOL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )

                if sym.get("address"):
                    swift_sym.address = self._make_address(
                        sym["address"], AddressType.VM_ADDRESS, slice_index
                    )

                model.symbols.append(swift_sym)

        # Create module hints from symbol prefixes
        if mangled_count > 0:
            # Swift symbols found - create a module hint
            module = SwiftModule(
                id=self._next_id(),
                name="DetectedModule",
                evidence=EvidenceStrength.MANGLED_SYMBOL,
                source_artifact=model.artifact_path,
                source_slice=slice_index
            )
            model.modules.append(module)

    def _is_swift_symbol(self, name: str) -> bool:
        """Check if a symbol is Swift mangled."""
        for pattern, _ in SWIFT_SYMBOL_PATTERNS:
            if re.match(pattern, name):
                return True
        return False

    def detect_swift_in_binary(self, data: bytes) -> Tuple[bool, Dict[str, int]]:
        """
        Detect if binary contains Swift metadata.

        Returns:
            Tuple of (has_swift, section_counts)
        """
        has_swift = False
        section_counts = {}

        swift_markers = [
            "__swift5_types",
            "__swift5_proto",
            "__swift5_protos",
            "__swift5_fieldmd",
            "__swift5_reflstr",
        ]

        for marker in swift_markers:
            count = data.count(marker.encode())
            if count > 0:
                has_swift = True
                section_counts[marker] = count

        # Also check for Swift mangled symbols
        swift_pattern_count = (
            data.count(b'_$s') +
            data.count(b'$s') +
            data.count(b'_T')
        )
        if swift_pattern_count > 0:
            has_swift = True
            section_counts["swift_mangled_patterns"] = swift_pattern_count

        return has_swift, section_counts

    def _model_to_dict(self, model: SwiftModel) -> Dict[str, Any]:
        """Convert model to dictionary for serialization."""
        return {
            "artifact_path": model.artifact_path,
            "artifact_hash": model.artifact_hash,
            "file_size": model.file_size,
            "has_swift": model.has_swift,
            "swift_version": model.swift_version,
            "module_count": len(model.modules),
            "type_count": len(model.types),
            "protocol_count": len(model.protocols),
            "conformance_count": len(model.conformances),
            "field_count": len(model.fields),
            "function_count": len(model.functions),
            "symbol_count": len(model.symbols),
            "reference_count": len(model.references),
            "demangling_stats": {
                "attempted": model.demangling_attempted,
                "succeeded": model.demangling_succeeded,
                "failed": model.demangling_failed,
            },
            "sections_found": model.sections_found,
            "evidence_distribution": model.evidence_strength_distribution,
            "warnings": model.warnings,
            # Include entity lists
            "modules": [m.to_dict() for m in model.modules[:50]],
            "types": [t.to_dict() for t in model.types[:100]],
            "protocols": [p.to_dict() for p in model.protocols[:100]],
            "fields": [f.to_dict() for f in model.fields[:100]],
            "symbols": [s.to_dict() for s in model.symbols[:100]],
        }

    def demangle(self, mangled_name: str) -> SwiftDemangleResult:
        """Convenience method for demangling."""
        return self._demangler.demangle(mangled_name)
