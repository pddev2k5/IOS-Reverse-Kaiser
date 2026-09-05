"""
Objective-C Metadata Model for IOS REVERSE KAISER.

Provides normalized, address-aware Objective-C runtime metadata.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class EvidenceStrength(Enum):
    """Evidence strength for metadata extraction."""
    STRUCTURAL = "structural"  # Recovered from runtime structures
    SYMBOL = "symbol"          # Recovered from symbol table
    REFERENCE = "reference"    # From reference pointers
    STRING_HINT = "string_hint"  # From printable strings only


class AddressType(Enum):
    """Explicit address type to avoid mixing semantics."""
    FILE_OFFSET = "file_offset"
    VIRTUAL_ADDRESS = "virtual_address"
    VM_ADDRESS = "vm_address"
    RELATIVE_OFFSET = "relative_offset"
    SLICE_RELATIVE = "slice_relative"


@dataclass
class ObjCAddress:
    """Address with explicit type semantics."""
    value: int
    address_type: AddressType
    slice_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "type": self.address_type.value,
            "slice_index": self.slice_index,
            "hex": hex(self.value) if self.value >= 0 else f"unavailable"
        }


@dataclass
class ObjCSelector:
    """Objective-C selector (method name)."""
    id: str
    name: str
    address: Optional[ObjCAddress] = None
    references: List[str] = field(default_factory=list)
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address.to_dict() if self.address else None,
            "reference_count": len(self.references),
            "evidence": self.evidence.value,
            "source_artifact": self.source_artifact,
            "source_slice": self.source_slice,
        }


@dataclass
class ObjCMethod:
    """Objective-C method."""
    id: str
    name: str  # Selector name
    selector: str  # Raw selector string
    implementation_address: Optional[ObjCAddress] = None
    type_encoding: Optional[str] = None
    is_class_method: bool = False
    owning_class: Optional[str] = None  # Class name
    owning_category: Optional[str] = None  # Category name if from category
    owning_class_id: Optional[str] = None
    section: Optional[str] = None  # __objc_methname, etc.
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "selector": self.selector,
            "imp_address": self.implementation_address.to_dict() if self.implementation_address else None,
            "type_encoding": self.type_encoding,
            "is_class_method": self.is_class_method,
            "owning_class": self.owning_class,
            "owning_category": self.owning_category,
            "section": self.section,
            "evidence": self.evidence.value,
            "source_artifact": self.source_artifact,
            "source_slice": self.source_slice,
        }


@dataclass
class ObjCProperty:
    """Objective-C property."""
    id: str
    name: str
    owning_class: Optional[str] = None
    owning_class_id: Optional[str] = None
    attributes: Optional[str] = None  # Type encoding + attributes
    getter_selector: Optional[str] = None
    setter_selector: Optional[str] = None
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owning_class": self.owning_class,
            "attributes": self.attributes,
            "getter": self.getter_selector,
            "setter": self.setter_selector,
            "evidence": self.evidence.value,
            "source_artifact": self.source_artifact,
        }


@dataclass
class ObjCIvar:
    """Objective-C instance variable."""
    id: str
    name: str
    owning_class: Optional[str] = None
    owning_class_id: Optional[str] = None
    type_encoding: Optional[str] = None
    offset: Optional[int] = None
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owning_class": self.owning_class,
            "type_encoding": self.type_encoding,
            "offset": self.offset,
            "evidence": self.evidence.value,
        }


@dataclass
class ObjCProtocol:
    """Objective-C protocol."""
    id: str
    name: str
    address: Optional[ObjCAddress] = None
    methods: List[str] = field(default_factory=list)  # Method selector names
    adopted_protocols: List[str] = field(default_factory=list)  # Protocol names
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address.to_dict() if self.address else None,
            "method_count": len(self.methods),
            "method_selectors": self.methods[:20],  # Limit for output
            "adopted_protocols": self.adopted_protocols,
            "evidence": self.evidence.value,
            "source_artifact": self.source_artifact,
        }


@dataclass
class ObjCCategory:
    """Objective-C category."""
    id: str
    name: str  # Category name
    target_class: str  # Class being extended
    target_class_id: Optional[str] = None
    address: Optional[ObjCAddress] = None
    methods: List[str] = field(default_factory=list)  # Method IDs
    properties: List[str] = field(default_factory=list)  # Property names
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_class": self.target_class,
            "target_class_id": self.target_class_id,
            "address": self.address.to_dict() if self.address else None,
            "method_count": len(self.methods),
            "property_count": len(self.properties),
            "evidence": self.evidence.value,
            "source_artifact": self.source_artifact,
        }


@dataclass
class ObjCClass:
    """Objective-C class."""
    id: str
    name: str
    address: Optional[ObjCAddress] = None
    metaclass_address: Optional[ObjCAddress] = None
    superclass_name: Optional[str] = None
    superclass_id: Optional[str] = None
    protocols: List[str] = field(default_factory=list)  # Protocol names
    protocol_ids: List[str] = field(default_factory=list)
    instance_methods: List[str] = field(default_factory=list)  # Method IDs
    class_methods: List[str] = field(default_factory=list)  # Method IDs
    properties: List[str] = field(default_factory=list)  # Property IDs
    ivars: List[str] = field(default_factory=list)  # Ivar IDs
    is_meta: bool = False  # This is a metaclass
    evidence: EvidenceStrength = EvidenceStrength.STRING_HINT
    source_artifact: Optional[str] = None
    source_slice: int = 0
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address.to_dict() if self.address else None,
            "metaclass_address": self.metaclass_address.to_dict() if self.metaclass_address else None,
            "superclass": self.superclass_name,
            "superclass_id": self.superclass_id,
            "protocols": self.protocols,
            "instance_method_count": len(self.instance_methods),
            "class_method_count": len(self.class_methods),
            "property_count": len(self.properties),
            "ivar_count": len(self.ivars),
            "is_meta": self.is_meta,
            "evidence": self.evidence.value,
            "source_artifact": self.source_artifact,
            "source_slice": self.source_slice,
        }


@dataclass
class ObjCReference:
    """Reference relationship between ObjC entities."""
    id: str
    reference_type: str  # e.g., "selector_to_class", "class_to_protocol", "method_to_class"
    source_id: str  # ID of source entity
    target_id: str  # ID of target entity
    source_name: str  # Human-readable source
    target_name: str  # Human-readable target
    address: Optional[ObjCAddress] = None  # Address where reference found
    evidence: EvidenceStrength = EvidenceStrength.REFERENCE
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
class ObjCModel:
    """Complete Objective-C metadata for a binary."""
    artifact_path: str
    artifact_hash: str = ""
    file_size: int = 0

    # Primary collections
    classes: List[ObjCClass] = field(default_factory=list)
    protocols: List[ObjCProtocol] = field(default_factory=list)
    categories: List[ObjCCategory] = field(default_factory=list)
    methods: List[ObjCMethod] = field(default_factory=list)
    selectors: List[ObjCSelector] = field(default_factory=list)
    properties: List[ObjCProperty] = field(default_factory=list)
    ivars: List[ObjCIvar] = field(default_factory=list)
    references: List[ObjCReference] = field(default_factory=list)

    # Relationship maps for efficient lookup
    _class_map: Dict[str, ObjCClass] = field(default_factory=dict, repr=False)
    _protocol_map: Dict[str, ObjCProtocol] = field(default_factory=dict, repr=False)
    _category_map: Dict[str, ObjCCategory] = field(default_factory=dict, repr=False)
    _method_map: Dict[str, ObjCMethod] = field(default_factory=dict, repr=False)
    _selector_map: Dict[str, ObjCSelector] = field(default_factory=dict, repr=False)

    # Metadata
    has_objc: bool = False
    evidence_strength_distribution: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    sections_found: List[str] = field(default_factory=list)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._class_map = {c.id: c for c in self.classes}
        self._class_map.update({c.name: c for c in self.classes})
        self._protocol_map = {p.id: p for p in self.protocols}
        self._protocol_map.update({p.name: p for p in self.protocols}
                                )
        self._category_map = {cat.id: cat for cat in self.categories}
        self._method_map = {m.id: m for m in self.methods}
        self._selector_map = {s.name: s for s in self.selectors}

        # Count evidence strength distribution
        self.evidence_strength_distribution = {
            "structural": 0,
            "symbol": 0,
            "reference": 0,
            "string_hint": 0
        }
        for entity in self.classes + self.protocols + self.categories + self.methods:
            key = entity.evidence.value
            if key in self.evidence_strength_distribution:
                self.evidence_strength_distribution[key] += 1

    def get_class(self, identifier: str) -> Optional[ObjCClass]:
        """Get class by ID or name."""
        return self._class_map.get(identifier)

    def get_protocol(self, identifier: str) -> Optional[ObjCProtocol]:
        """Get protocol by ID or name."""
        return self._protocol_map.get(identifier)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "artifact_hash": self.artifact_hash,
            "file_size": self.file_size,
            "has_objc": self.has_objc,
            "class_count": len(self.classes),
            "protocol_count": len(self.protocols),
            "category_count": len(self.categories),
            "method_count": len(self.methods),
            "selector_count": len(self.selectors),
            "property_count": len(self.properties),
            "ivar_count": len(self.ivars),
            "reference_count": len(self.references),
            "sections_found": self.sections_found,
            "evidence_distribution": self.evidence_strength_distribution,
            "warnings": self.warnings,
        }
