"""
Swift Metadata Model for IOS REVERSE KAISER.

Provides normalized, address-aware Swift metadata.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class EvidenceStrength(Enum):
    """Evidence strength for metadata extraction."""
    STRUCTURAL = "structural"  # Recovered from metadata structures
    SYMBOL = "symbol"          # Recovered from symbol table
    MANGLED_SYMBOL = "mangled_symbol"  # From mangled Swift symbols
    STRING_HINT = "string_hint"  # From strings only


class AddressType(Enum):
    """Explicit address type to avoid mixing semantics."""
    FILE_OFFSET = "file_offset"
    VIRTUAL_ADDRESS = "virtual_address"
    VM_ADDRESS = "vm_address"
    RELATIVE_OFFSET = "relative_offset"
    SLICE_RELATIVE = "slice_relative"


@dataclass
class SwiftAddress:
    """Address with explicit type semantics."""
    value: int
    address_type: AddressType
    slice_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "type": self.address_type.value,
            "slice_index": self.slice_index,
            "hex": hex(self.value) if self.value >= 0 else "unavailable"
        }


@dataclass
class SwiftModule:
    """Swift module."""
    id: str
    name: str
    types: List[str] = field(default_factory=list)  # Type IDs
    protocols: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type_count": len(self.types),
            "protocol_count": len(self.protocols),
            "function_count": len(self.functions),
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftType:
    """Swift type (class, struct, enum, etc.)."""
    id: str
    name: str
    mangled_name: Optional[str] = None
    kind: str = "unknown"  # class, struct, enum, protocol, etc.
    address: Optional[SwiftAddress] = None
    nominal_descriptor_offset: Optional[int] = None
    module: Optional[str] = None
    module_id: Optional[str] = None
    superclass: Optional[str] = None
    superclass_id: Optional[str] = None
    conformances: List[str] = field(default_factory=list)  # Protocol names
    fields: List[str] = field(default_factory=list)  # Field IDs
    methods: List[str] = field(default_factory=list)  # Method names
    vtable_size: Optional[int] = None
    is_generic: bool = False
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mangled_name": self.mangled_name,
            "kind": self.kind,
            "address": self.address.to_dict() if self.address else None,
            "module": self.module,
            "superclass": self.superclass,
            "conformance_count": len(self.conformances),
            "field_count": len(self.fields),
            "method_count": len(self.methods),
            "is_generic": self.is_generic,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftProtocol:
    """Swift protocol."""
    id: str
    name: str
    mangled_name: Optional[str] = None
    address: Optional[SwiftAddress] = None
    module: Optional[str] = None
    module_id: Optional[str] = None
    required_methods: List[str] = field(default_factory=list)
    default_implementations: List[str] = field(default_factory=list)
    associated_types: List[str] = field(default_factory=list)
    is_objc: bool = False  # @objc protocol
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mangled_name": self.mangled_name,
            "address": self.address.to_dict() if self.address else None,
            "module": self.module,
            "required_method_count": len(self.required_methods),
            "associated_type_count": len(self.associated_types),
            "is_objc": self.is_objc,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftConformance:
    """Swift protocol conformance record."""
    id: str
    type_name: str
    protocol_name: str
    type_id: Optional[str] = None
    protocol_id: Optional[str] = None
    mangled_type: Optional[str] = None
    mangled_conformance: Optional[str] = None
    witness_table_offset: Optional[int] = None
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type_name,
            "protocol": self.protocol_name,
            "mangled_type": self.mangled_type,
            "witness_table_offset": self.witness_table_offset,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftField:
    """Swift type field/member."""
    id: str
    name: str
    owning_type: Optional[str] = None
    owning_type_id: Optional[str] = None
    type_name: Optional[str] = None
    mangled_type_name: Optional[str] = None
    offset: Optional[int] = None
    is_var: bool = True
    is_lazy: bool = False
    is_mutable: bool = False
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owning_type": self.owning_type,
            "type_name": self.type_name,
            "mangled_type_name": self.mangled_type_name,
            "offset": self.offset,
            "is_var": self.is_var,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftFunction:
    """Swift function/method."""
    id: str
    name: str
    demangled_name: Optional[str] = None
    mangled_name: Optional[str] = None
    address: Optional[SwiftAddress] = None
    module: Optional[str] = None
    module_id: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    is_throwing: bool = False
    is_rethrows: bool = False
    is_async: bool = False
    is_curried: bool = False
    is_property_accessor: bool = False
    is_init: bool = False
    is_deinit: bool = False
    is_class_method: bool = False
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "demangled_name": self.demangled_name,
            "mangled_name": self.mangled_name,
            "address": self.address.to_dict() if self.address else None,
            "module": self.module,
            "return_type": self.return_type,
            "is_throwing": self.is_throwing,
            "is_async": self.is_async,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftSymbol:
    """Swift symbol from symbol table."""
    id: str
    name: str
    mangled_name: Optional[str] = None
    demangled_name: Optional[str] = None
    address: Optional[SwiftAddress] = None
    demangling_status: str = "unknown"  # success, failed, not_attempted
    demangler_used: Optional[str] = None
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mangled_name": self.mangled_name,
            "demangled_name": self.demangled_name,
            "address": self.address.to_dict() if self.address else None,
            "demangling_status": self.demangling_status,
            "demangler_used": self.demangler_used,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftMetadataReference:
    """Reference between Swift metadata entities."""
    id: str
    reference_type: str  # e.g., "type_to_protocol", "function_to_module"
    source_id: str
    target_id: str
    source_name: str
    target_name: str
    address: Optional[SwiftAddress] = None
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.reference_type,
            "source": self.source_name,
            "target": self.target_name,
            "address": self.address.to_dict() if self.address else None,
            "evidence": self.evidence.value,
        }


@dataclass
class SwiftDemangleResult:
    """Result of demangling operation."""
    mangled_name: str
    demangled_name: Optional[str]
    success: bool
    demangler_used: Optional[str] = None
    error: Optional[str] = None
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mangled_name": self.mangled_name,
            "demangled_name": self.demangled_name,
            "success": self.success,
            "demangler_used": self.demangler_used,
            "error": self.error,
        }


@dataclass
class SwiftModel:
    """Complete Swift metadata for a binary."""
    artifact_path: str
    artifact_hash: str = ""
    file_size: int = 0

    # Primary collections
    modules: List[SwiftModule] = field(default_factory=list)
    types: List[SwiftType] = field(default_factory=list)
    protocols: List[SwiftProtocol] = field(default_factory=list)
    conformances: List[SwiftConformance] = field(default_factory=list)
    fields: List[SwiftField] = field(default_factory=list)
    functions: List[SwiftFunction] = field(default_factory=list)
    symbols: List[SwiftSymbol] = field(default_factory=list)
    references: List[SwiftMetadataReference] = field(default_factory=list)
    demangle_results: List[SwiftDemangleResult] = field(default_factory=list)

    # Demangling statistics
    demangling_attempted: int = 0
    demangling_succeeded: int = 0
    demangling_failed: int = 0

    # Metadata
    has_swift: bool = False
    swift_version: Optional[str] = None
    evidence_strength_distribution: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    sections_found: List[str] = field(default_factory=list)

    # Indexes for lookups
    _module_map: Dict[str, SwiftModule] = field(default_factory=dict, repr=False)
    _type_map: Dict[str, SwiftType] = field(default_factory=dict, repr=False)
    _protocol_map: Dict[str, SwiftProtocol] = field(default_factory=dict, repr=False)
    _symbol_map: Dict[str, SwiftSymbol] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._module_map = {m.id: m for m in self.modules}
        self._module_map.update({m.name: m for m in self.modules})
        self._type_map = {t.id: t for t in self.types}
        self._type_map.update({t.name: t for t in self.types})
        self._type_map.update({t.mangled_name: t for t in self.types if t.mangled_name})
        self._protocol_map = {p.id: p for p in self.protocols}
        self._protocol_map.update({p.name: p for p in self.protocols})
        self._symbol_map = {s.id: s for s in self.symbols}
        self._symbol_map.update({s.mangled_name: s for s in self.symbols if s.mangled_name})

        # Count evidence strength distribution
        self.evidence_strength_distribution = {
            "structural": 0,
            "symbol": 0,
            "mangled_symbol": 0,
            "string_hint": 0
        }
        for entity in self.types + self.protocols + self.functions + self.symbols:
            key = entity.evidence.value
            if key in self.evidence_strength_distribution:
                self.evidence_strength_distribution[key] += 1

    def get_type(self, identifier: str) -> Optional[SwiftType]:
        """Get type by ID, name, or mangled name."""
        return self._type_map.get(identifier)

    def get_module(self, identifier: str) -> Optional[SwiftModule]:
        """Get module by ID or name."""
        return self._module_map.get(identifier)

    def get_protocol(self, identifier: str) -> Optional[SwiftProtocol]:
        """Get protocol by ID or name."""
        return self._protocol_map.get(identifier)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "artifact_hash": self.artifact_hash,
            "file_size": self.file_size,
            "has_swift": self.has_swift,
            "swift_version": self.swift_version,
            "module_count": len(self.modules),
            "type_count": len(self.types),
            "protocol_count": len(self.protocols),
            "conformance_count": len(self.conformances),
            "field_count": len(self.fields),
            "function_count": len(self.functions),
            "symbol_count": len(self.symbols),
            "reference_count": len(self.references),
            "demangling_stats": {
                "attempted": self.demangling_attempted,
                "succeeded": self.demangling_succeeded,
                "failed": self.demangling_failed,
            },
            "sections_found": self.sections_found,
            "evidence_distribution": self.evidence_strength_distribution,
            "warnings": self.warnings,
        }
