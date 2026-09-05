"""
Objective-C metadata adapter for IOS REVERSE KAISER.

Extracts Objective-C runtime metadata from Mach-O binaries using section parsing.
Supports both structural extraction and symbol-based hints.
"""

import struct
import hashlib
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from ios_reverse.adapters.base import ToolInfo
from dataclasses import asdict

from ios_reverse.models.objc import (
    ObjCModel, ObjCClass, ObjCProtocol, ObjCCategory, ObjCMethod,
    ObjCSelector, ObjCProperty, ObjCIvar, ObjCReference, ObjCAddress,
    EvidenceStrength, AddressType
)
from ios_reverse.adapters.base import AdapterResult, ToolAdapter


# Objective-C magic constants (for reference)
# OBJC_MAGIC = 0xDEADEEF  # Objective-C 1 magic (not used in modern binaries)
# OBJC2_MAGIC = 0xC0DEBABE  # Objective-C 2 magic (not used)

# Known ObjC section names
OBJC_SECTIONS = [
    "__objc_classlist",
    "__objc_catlist",
    "__objc_protolist",
    "__objc_selrefs",
    "__objc_classrefs",
    "__objc_superrefs",
    "__objc_methname",
    "__objc_methtype",
    "__objc_const",
    "__objc_data",
    "__objc_nlclslist",  # non-lazy class list
    "__objc_nlcatlist",  # non-lazy category list
]

# Swift section names (for mixed binaries)
SWIFT_SECTIONS = [
    "__swift5_types",
    "__swift5_proto",
    "__swift5_protos",
    "__swift5_fieldmd",
    "__swift5_reflstr",
    "__swift5_typeref",
    "__swift5_assocty",
    "__swift5_capture",
    "__swift5_builtin",
]

# Common selector patterns
SELECTOR_PATTERN = re.compile(b'^[a-zA-Z_][a-zA-Z0-9_]*$')


class ObjCAdapter(ToolAdapter):
    """
    Adapter for extracting Objective-C metadata from Mach-O binaries.

    Uses section parsing for structural extraction and symbol analysis for hints.
    Distinguishes between structural metadata and string hints.
    """

    def __init__(self):
        super().__init__("objc_adapter", "1.0.0")
        self._id_counter = 0

    def _next_id(self) -> str:
        """Generate unique ID."""
        self._id_counter += 1
        return f"objc-{self._id_counter:04d}"

    def _make_address(self, value: int, addr_type: AddressType, slice_idx: int = 0) -> ObjCAddress:
        """Create an ObjCAddress."""
        return ObjCAddress(value=value, address_type=addr_type, slice_index=slice_idx)

    def is_available(self) -> bool:
        """Adapter is always available (pure Python)."""
        return True

    def get_tool_info(self) -> ToolInfo:
        """Get information about the adapter."""
        return ToolInfo(
            name="objc_adapter",
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
        return ["metadata_extraction", "structural_parsing", "symbol_analysis"]

    def extract_metadata(
        self,
        artifact_path: str,
        sections: Optional[Dict[str, bytes]] = None,
        symbols: Optional[List[Dict[str, Any]]] = None,
        slice_index: int = 0,
        compute_hashes: bool = False
    ) -> AdapterResult:
        """
        Extract Objective-C metadata from a binary.

        Args:
            artifact_path: Path to the Mach-O binary
            sections: Dict of section_name -> section_data (from Mach-O parser)
            symbols: List of symbol info (from nm or parser)
            slice_index: Architecture slice index
            compute_hashes: Whether to compute file hashes

        Returns:
            AdapterResult with ObjCModel in metadata["model"]
        """
        try:
            # Build model
            model = ObjCModel(artifact_path=artifact_path)

            if compute_hashes and os.path.exists(artifact_path):
                with open(artifact_path, 'rb') as f:
                    model.artifact_hash = hashlib.sha256(f.read()).hexdigest()
                    model.file_size = os.path.getsize(artifact_path)

            # Check if we have sections or symbols
            if sections:
                # Structural extraction from sections
                self._extract_from_sections(model, sections, slice_index)
            else:
                model.warnings.append("No ObjC sections provided")

            # Extract from symbols if available
            if symbols:
                self._extract_from_symbols(model, symbols, slice_index)

            # Build indexes for relationship lookups
            model.build_indexes()

            # Build relationships
            self._build_references(model, slice_index)

            # Check if we found any ObjC
            model.has_objc = (
                len(model.classes) > 0 or
                len(model.protocols) > 0 or
                len(model.categories) > 0
            )

            return AdapterResult(
                success=True,
                metadata={"model": self._model_to_dict(model)},
                artifacts=[artifact_path]
            )

        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"ObjC extraction failed: {str(e)}"
            )

    def _extract_from_sections(
        self,
        model: ObjCModel,
        sections: Dict[str, bytes],
        slice_index: int
    ):
        """Extract ObjC metadata from Mach-O sections."""

        # Track which ObjC sections we found
        model.sections_found = [name for name in sections.keys()
                                if name.startswith("__objc_") or name.startswith("__swift5_")]

        # Extract selectors from __objc_selrefs
        if "__objc_selrefs" in sections:
            self._extract_selector_refs(model, sections["__objc_selrefs"], slice_index)

        # Extract method names
        if "__objc_methname" in sections:
            self._extract_method_names(model, sections["__objc_methname"], slice_index)

        # Extract method types
        if "__objc_methtype" in sections:
            self._extract_method_types(model, sections["__objc_methtype"], slice_index)

        # Extract class refs
        if "__objc_classrefs" in sections:
            self._extract_class_refs(model, sections["__objc_classrefs"], slice_index)

        # Extract protocol list
        if "__objc_protolist" in sections:
            self._extract_protocols(model, sections["__objc_protolist"], slice_index)

        # Extract category list
        if "__objc_catlist" in sections:
            self._extract_categories(model, sections["__objc_catlist"], slice_index)

        # Extract class list
        if "__objc_classlist" in sections:
            self._extract_classes(model, sections["__objc_classlist"], slice_index)

    def _extract_selector_refs(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract selector references from __objc_selrefs."""
        # SEL refs are pointers to selector names in __objc_methname
        # Each is a 4-byte (32-bit) or 8-byte (64-bit) pointer
        # This is weak evidence - points to selector but doesn't prove it exists

        pointer_size = 8  # Assume 64-bit
        count = len(section_data) // pointer_size

        for i in range(min(count, 1000)):  # Limit processing
            offset = i * pointer_size
            try:
                ptr_value = struct.unpack('<Q' if pointer_size == 8 else '<I',
                                         section_data[offset:offset + pointer_size])[0]

                # Create a selector for this reference
                # Note: We don't have the actual name yet - that's in __objc_methname
                # This is REFERENCE evidence, not structural
                selector = ObjCSelector(
                    id=self._next_id(),
                    name=f"@selector_ref_{i}",  # Placeholder
                    address=self._make_address(ptr_value, AddressType.VM_ADDRESS, slice_index),
                    evidence=EvidenceStrength.REFERENCE,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.selectors.append(selector)
            except Exception:
                break

    def _extract_method_names(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract method names from __objc_methname section."""
        # Method names are null-terminated C strings
        offset = 0
        string_offsets = []

        while offset < len(section_data):
            # Find null terminator
            null_pos = section_data.find(b'\x00', offset)
            if null_pos < 0:
                break

            string_data = section_data[offset:null_pos]
            if len(string_data) > 0:
                string_offsets.append((offset, string_data.decode('utf-8', errors='replace')))

            offset = null_pos + 1

        # Create selectors for found names
        for str_offset, str_value in string_offsets:
            if len(str_value) > 0 and len(str_value) < 256:
                selector = ObjCSelector(
                    id=self._next_id(),
                    name=str_value,
                    address=self._make_address(str_offset, AddressType.SLICE_RELATIVE, slice_index),
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.selectors.append(selector)

    def _extract_method_types(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract method type encodings from __objc_methtype section."""
        # Type encodings are null-terminated C strings
        offset = 0
        type_offsets = []

        while offset < len(section_data):
            null_pos = section_data.find(b'\x00', offset)
            if null_pos < 0:
                break

            type_data = section_data[offset:null_pos]
            if len(type_data) > 0:
                type_offsets.append((offset, type_data.decode('utf-8', errors='replace')))

            offset = null_pos + 1

        # Store type encodings - they correlate with methods
        for type_offset, type_value in type_offsets:
            if len(type_value) > 0 and len(type_value) < 128:
                # Create a method placeholder with type encoding
                method = ObjCMethod(
                    id=self._next_id(),
                    name=f"method_type_{type_offset}",
                    selector=f"method_type_{type_offset}",
                    type_encoding=type_value,
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.methods.append(method)

    def _extract_class_refs(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract class references from __objc_classrefs."""
        pointer_size = 8
        count = len(section_data) // pointer_size

        for i in range(min(count, 500)):  # Limit processing
            offset = i * pointer_size
            try:
                ptr_value = struct.unpack('<Q' if pointer_size == 8 else '<I',
                                         section_data[offset:offset + pointer_size])[0]

                # This is a class reference - create a class entry as hint
                if ptr_value > 0:
                    cls = ObjCClass(
                        id=self._next_id(),
                        name=f"ClassRef_{ptr_value:x}",  # Placeholder name
                        address=self._make_address(ptr_value, AddressType.VM_ADDRESS, slice_index),
                        evidence=EvidenceStrength.REFERENCE,
                        source_artifact=model.artifact_path,
                        source_slice=slice_index
                    )
                    model.classes.append(cls)
            except Exception:
                break

    def _extract_protocols(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract protocols from __objc_protolist section."""
        # Protocol structures contain name pointers, etc.
        # For now, extract any string that looks like a protocol name
        # Real protocol parsing requires following the structure pointers

        # Look for strings that look like ObjC protocol names
        offset = 0
        while offset < len(section_data):
            null_pos = section_data.find(b'\x00', offset)
            if null_pos < 0 or null_pos - offset > 256:
                break

            string_data = section_data[offset:null_pos]
            str_value = string_data.decode('utf-8', errors='replace')

            # Protocol names typically start with uppercase and contain no spaces
            if (str_value and str_value[0].isupper() and
                str_value.isalnum() and '_' in str_value):
                proto = ObjCProtocol(
                    id=self._next_id(),
                    name=str_value,
                    evidence=EvidenceStrength.STRING_HINT,  # Found in pointer chain
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.protocols.append(proto)

            offset = null_pos + 1

    def _extract_categories(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract categories from __objc_catlist section."""
        # Category list contains pointers to category structures
        # Each pointer points to: cat_name, target_class, ...

        pointer_size = 8
        count = len(section_data) // pointer_size

        for i in range(min(count, 100)):
            offset = i * pointer_size
            try:
                ptr_value = struct.unpack('<Q' if pointer_size == 8 else '<I',
                                         section_data[offset:offset + pointer_size])[0]

                if ptr_value > 0 and ptr_value < len(section_data) * 1000:
                    # Try to read strings near this pointer
                    # This is a weak extraction - proper parsing needs structure traversal
                    pass
            except Exception:
                break

    def _extract_classes(
        self,
        model: ObjCModel,
        section_data: bytes,
        slice_index: int
    ):
        """Extract classes from __objc_classlist section."""
        # Class list contains pointers to class structures
        pointer_size = 8
        count = len(section_data) // pointer_size

        for i in range(min(count, 500)):
            offset = i * pointer_size
            try:
                ptr_value = struct.unpack('<Q' if pointer_size == 8 else '<I',
                                         section_data[offset:offset + pointer_size])[0]

                if ptr_value > 0:
                    cls = ObjCClass(
                        id=self._next_id(),
                        name=f"Class_{ptr_value:x}",
                        address=self._make_address(ptr_value, AddressType.VM_ADDRESS, slice_index),
                        evidence=EvidenceStrength.REFERENCE,
                        source_artifact=model.artifact_path,
                        source_slice=slice_index
                    )
                    model.classes.append(cls)
            except Exception:
                break

    def _extract_from_symbols(
        self,
        model: ObjCModel,
        symbols: List[Dict[str, Any]],
        slice_index: int
    ):
        """Extract ObjC metadata hints from symbol table."""

        for sym in symbols:
            name = sym.get("name", "")
            if not name:
                continue

            # Check for ObjC class symbols: +[ClassName method] or -[ClassName method]
            if name.startswith("+[") or name.startswith("-["):
                self._parse_objc_symbol(model, name, sym, slice_index)

            # Check for ObjC class symbols: _OBJC_CLASS_$_ClassName
            elif name.startswith("_OBJC_CLASS_$_"):
                class_name = name[14:]  # Remove prefix
                cls = ObjCClass(
                    id=self._next_id(),
                    name=class_name,
                    evidence=EvidenceStrength.SYMBOL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                if sym.get("address"):
                    cls.address = self._make_address(
                        sym["address"], AddressType.VM_ADDRESS, slice_index
                    )
                model.classes.append(cls)

            # Check for ObjC metaclass symbols
            elif name.startswith("_OBJC_METACLASS_$_"):
                class_name = name[18:]  # Remove prefix
                cls = ObjCClass(
                    id=self._next_id(),
                    name=class_name,
                    is_meta=True,
                    evidence=EvidenceStrength.SYMBOL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.classes.append(cls)

            # Check for ObjC protocol symbols
            elif name.startswith("_OBJC_PROTOCOL_$_"):
                proto_name = name[16:]  # Remove prefix
                proto = ObjCProtocol(
                    id=self._next_id(),
                    name=proto_name,
                    evidence=EvidenceStrength.SYMBOL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.protocols.append(proto)

    def _parse_objc_symbol(
        self,
        model: ObjCModel,
        symbol: str,
        sym_info: Dict[str, Any],
        slice_index: int
    ):
        """Parse ObjC method symbol like +[ClassName methodName:arg]."""
        is_class_method = symbol.startswith("+")
        symbol = symbol[2:-1]  # Remove +/- and ]

        # Split on first space to get class and method
        parts = symbol.split(maxsplit=1)
        if len(parts) < 2:
            return

        class_name = parts[0]
        method_name = parts[1]

        # Determine if method is property accessor
        is_property = method_name.startswith("set") or "." in method_name

        method = ObjCMethod(
            id=self._next_id(),
            name=method_name,
            selector=method_name,
            is_class_method=is_class_method,
            owning_class=class_name,
            evidence=EvidenceStrength.SYMBOL,
            source_artifact=model.artifact_path,
            source_slice=slice_index
        )

        if sym_info.get("address"):
            method.implementation_address = self._make_address(
                sym_info["address"], AddressType.VM_ADDRESS, slice_index
            )

        model.methods.append(method)

    def _build_references(self, model: ObjCModel, slice_index: int):
        """Build relationship references between ObjC entities."""

        # Build class name to ID map
        class_by_name = {c.name: c for c in model.classes}

        # Class to superclass references
        for cls in model.classes:
            if cls.superclass_name:
                target = class_by_name.get(cls.superclass_name)
                if target:
                    ref = ObjCReference(
                        id=self._next_id(),
                        reference_type="class_to_superclass",
                        source_id=cls.id,
                        target_id=target.id,
                        source_name=cls.name,
                        target_name=cls.superclass_name,
                        evidence=EvidenceStrength.STRUCTURAL,
                        source_artifact=model.artifact_path,
                        source_slice=slice_index
                    )
                    model.references.append(ref)

        # Category to target class references
        for cat in model.categories:
            target = class_by_name.get(cat.target_class)
            if target:
                ref = ObjCReference(
                    id=self._next_id(),
                    reference_type="category_to_class",
                    source_id=cat.id,
                    target_id=target.id,
                    source_name=cat.name,
                    target_name=cat.target_class,
                    evidence=EvidenceStrength.STRUCTURAL,
                    source_artifact=model.artifact_path,
                    source_slice=slice_index
                )
                model.references.append(ref)

    def _model_to_dict(self, model: ObjCModel) -> Dict[str, Any]:
        """Convert model to dictionary for serialization."""
        return {
            "artifact_path": model.artifact_path,
            "artifact_hash": model.artifact_hash,
            "file_size": model.file_size,
            "has_objc": model.has_objc,
            "class_count": len(model.classes),
            "protocol_count": len(model.protocols),
            "category_count": len(model.categories),
            "method_count": len(model.methods),
            "selector_count": len(model.selectors),
            "property_count": len(model.properties),
            "ivar_count": len(model.ivars),
            "reference_count": len(model.references),
            "sections_found": model.sections_found,
            "evidence_distribution": model.evidence_strength_distribution,
            "warnings": model.warnings,
            # Include entity lists
            "classes": [c.to_dict() for c in model.classes[:100]],
            "protocols": [p.to_dict() for p in model.protocols[:100]],
            "categories": [c.to_dict() for c in model.categories[:100]],
            "methods": [m.to_dict() for m in model.methods[:100]],
            "selectors": [s.to_dict() for s in model.selectors[:100]],
        }

    def detect_objc_in_binary(
        self,
        data: bytes
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Detect if binary contains Objective-C metadata.

        Returns:
            Tuple of (has_objc, section_counts)
        """
        has_objc = False
        section_counts = {}

        # Check for ObjC section indicators in the data
        objc_markers = [
            b"__objc_classlist",
            b"__objc_catlist",
            b"__objc_protolist",
            b"__objc_methname",
            b"objc_msgSend",
            b"OBJC_CLASS_",
        ]

        for marker in objc_markers:
            count = data.count(marker)
            if count > 0:
                has_objc = True
                section_counts[marker.decode('utf-8', errors='replace')] = count

        return has_objc, section_counts
