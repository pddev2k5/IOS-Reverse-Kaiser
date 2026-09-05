"""
Architecture Model for IOS REVERSE KAISER.

Provides normalized models for logical/software architecture detection
separate from the physical ComponentGraph (P04.4).

IMPORTANT: This represents LOGICAL architecture (ViewControllers, Services, etc.),
NOT physical (Frameworks, Dylibs). Keep these concepts separate.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set


class ArchitectureRole(Enum):
    """Architecture role classification."""
    VIEW_CONTROLLER = "view_controller"       # UI controller
    VIEW_MODEL = "view_model"               # MVVM view model
    MODEL = "model"                          # Data model
    SERVICE = "service"                       # Business logic service
    REPOSITORY = "repository"                # Data access layer
    MANAGER = "manager"                       # Manager class
    CLIENT = "client"                         # API/client class
    ROUTER = "router"                        # Navigation router
    COORDINATOR = "coordinator"              # Flow coordinator
    DELEGATE = "delegate"                    # Delegate pattern
    HANDLER = "handler"                      # Event/data handler
    PROVIDER = "provider"                    # Provider pattern
    INTERACTOR = "interactor"                # Clean architecture interactor
    PRESENTER = "presenter"                  # Presenter
    WORKER = "worker"                        # Background worker
    UNKNOWN = "unknown"


class EvidenceLevel(Enum):
    """Evidence level for architecture classifications."""
    HEURISTIC = "heuristic"          # Name-based only
    REFERENCE = "reference"           # References to/from other components
    STRUCTURAL = "structural"        # Inheritance, protocols
    CORRELATED = "correlated"        # Multiple evidence types
    VERIFIED = "verified"            # Confirmed by analysis


@dataclass
class ArchitectureComponent:
    """
    Logical architecture component.

    Represents a software component (class, struct, etc.) identified through evidence.
    """
    component_id: str                     # Stable deterministic ID
    name: str                            # Component name
    role: ArchitectureRole
    evidence_level: EvidenceLevel
    role_evidence: List[str] = field(default_factory=list)  # Why this role?

    # Provenance - links to P04.3/P04.4
    objc_class_id: Optional[str] = None      # From ObjC metadata
    swift_type_id: Optional[str] = None      # From Swift metadata
    component_id_p04: Optional[str] = None   # From P04.4 ComponentGraph
    artifact_id: Optional[str] = None        # Which binary

    # Structural evidence
    superclass: Optional[str] = None         # Parent class
    protocols: List[str] = field(default_factory=list)  # Adopted protocols
    methods: List[str] = field(default_factory=list)    # Significant methods
    properties: List[str] = field(default_factory=list) # Significant properties

    # Relationships
    inbound_references: List[str] = field(default_factory=list)  # Components referencing this
    outbound_references: List[str] = field(default_factory=list) # Components this references

    # Notes
    role_confidence_notes: List[str] = field(default_factory=list)
    alternative_roles: List[str] = field(default_factory=list)  # Other possible roles

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "role": self.role.value,
            "evidence_level": self.evidence_level.value,
            "role_evidence": self.role_evidence,
            "objc_class_id": self.objc_class_id,
            "swift_type_id": self.swift_type_id,
            "component_id_p04": self.component_id_p04,
            "artifact_id": self.artifact_id,
            "superclass": self.superclass,
            "protocols": self.protocols,
            "method_count": len(self.methods),
            "property_count": len(self.properties),
            "inbound_reference_count": len(self.inbound_references),
            "outbound_reference_count": len(self.outbound_references),
            "role_confidence_notes": self.role_confidence_notes,
            "alternative_roles": self.alternative_roles,
        }


@dataclass
class ArchitectureRelationship:
    """
    Relationship between architecture components.

    Represents logical relationships, NOT physical containment.
    """
    relationship_id: str
    source_id: str                       # Source component ID
    target_id: str                       # Target component ID
    relationship_type: str               # e.g., "delegates_to", "uses", "creates"

    # Evidence
    evidence_level: EvidenceLevel = EvidenceLevel.HEURISTIC
    evidence_sources: List[str] = field(default_factory=list)

    # Details
    context: Optional[str] = None         # Method/context where relationship exists

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "evidence_level": self.evidence_level.value,
            "evidence_sources": self.evidence_sources,
            "context": self.context,
        }


@dataclass
class ArchitectureEvidence:
    """
    Individual piece of architecture evidence.
    """
    evidence_id: str
    evidence_type: str                  # e.g., "naming", "inheritance", "protocol", "reference"
    target_component_id: str             # Which component this evidence points to
    content: str                        # What the evidence says
    source_artifact_id: Optional[str] = None
    source_address: Optional[int] = None
    raw_value: Optional[str] = None     # Original value before interpretation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "target_component_id": self.target_component_id,
            "content": self.content,
            "source_artifact_id": self.source_artifact_id,
            "source_address": self.source_address,
            "raw_value": self.raw_value,
        }


@dataclass
class ArchitectureModel:
    """
    Complete architecture model for an application.
    """
    artifact_path: str
    components: List[ArchitectureComponent] = field(default_factory=list)
    relationships: List[ArchitectureRelationship] = field(default_factory=list)
    evidence_records: List[ArchitectureEvidence] = field(default_factory=list)

    # Statistics
    role_distribution: Dict[str, int] = field(default_factory=dict)
    evidence_level_distribution: Dict[str, int] = field(default_factory=dict)

    # Indexes
    _component_by_id: Dict[str, ArchitectureComponent] = field(default_factory=dict, repr=False)
    _components_by_role: Dict[str, List[ArchitectureComponent]] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._component_by_id = {c.component_id: c for c in self.components}
        self._components_by_role = {}
        for comp in self.components:
            if comp.role.value not in self._components_by_role:
                self._components_by_role[comp.role.value] = []
            self._components_by_role[comp.role.value].append(comp)

    def get_component(self, component_id: str) -> Optional[ArchitectureComponent]:
        """Get component by ID."""
        return self._component_by_id.get(component_id)

    def get_by_role(self, role: ArchitectureRole) -> List[ArchitectureComponent]:
        """Get components by role."""
        return self._components_by_role.get(role.value, [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "component_count": len(self.components),
            "relationship_count": len(self.relationships),
            "evidence_count": len(self.evidence_records),
            "role_distribution": self.role_distribution,
            "evidence_level_distribution": self.evidence_level_distribution,
            "components": [c.to_dict() for c in self.components],
            "relationships": [r.to_dict() for r in self.relationships],
        }


def generate_architecture_id(name: str, artifact_id: str) -> str:
    """Generate deterministic architecture component ID."""
    import hashlib
    content = f"{name}:{artifact_id}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"arch-{hash_val}"


def classify_by_naming(name: str) -> List[tuple]:
    """
    Classify component role by name heuristics.

    Returns list of (role, confidence_note) sorted by confidence.
    Lower confidence = more tentative.

    IMPORTANT: This is HEURISTIC only, not confirmed classification.
    """
    candidates = []
    lower_name = name.lower()

    # Strong indicators
    if "viewcontroller" in lower_name or "viewcontroller" == lower_name:
        candidates.append((ArchitectureRole.VIEW_CONTROLLER, EvidenceLevel.HEURISTIC, "Name ends with 'ViewController'"))
    if "viewmodel" in lower_name:
        candidates.append((ArchitectureRole.VIEW_MODEL, EvidenceLevel.HEURISTIC, "Name contains 'ViewModel'"))
    if "service" in lower_name:
        candidates.append((ArchitectureRole.SERVICE, EvidenceLevel.HEURISTIC, "Name contains 'Service'"))
    if "repository" in lower_name:
        candidates.append((ArchitectureRole.REPOSITORY, EvidenceLevel.HEURISTIC, "Name contains 'Repository'"))
    if "manager" in lower_name:
        candidates.append((ArchitectureRole.MANAGER, EvidenceLevel.HEURISTIC, "Name contains 'Manager'"))
    if "client" in lower_name:
        candidates.append((ArchitectureRole.CLIENT, EvidenceLevel.HEURISTIC, "Name contains 'Client'"))
    if "router" in lower_name:
        candidates.append((ArchitectureRole.ROUTER, EvidenceLevel.HEURISTIC, "Name contains 'Router'"))
    if "coordinator" in lower_name:
        candidates.append((ArchitectureRole.COORDINATOR, EvidenceLevel.HEURISTIC, "Name contains 'Coordinator'"))
    if "delegate" in lower_name and not lower_name.endswith("delegateprotocol"):
        candidates.append((ArchitectureRole.DELEGATE, EvidenceLevel.HEURISTIC, "Name contains 'Delegate'"))
    if "handler" in lower_name:
        candidates.append((ArchitectureRole.HANDLER, EvidenceLevel.HEURISTIC, "Name contains 'Handler'"))
    if "provider" in lower_name:
        candidates.append((ArchitectureRole.PROVIDER, EvidenceLevel.HEURISTIC, "Name contains 'Provider'"))
    if "interactor" in lower_name:
        candidates.append((ArchitectureRole.INTERACTOR, EvidenceLevel.HEURISTIC, "Name contains 'Interactor'"))
    if "presenter" in lower_name:
        candidates.append((ArchitectureRole.PRESENTER, EvidenceLevel.HEURISTIC, "Name contains 'Presenter'"))
    if "worker" in lower_name:
        candidates.append((ArchitectureRole.WORKER, EvidenceLevel.HEURISTIC, "Name contains 'Worker'"))
    if "model" in lower_name or "entity" in lower_name:
        candidates.append((ArchitectureRole.MODEL, EvidenceLevel.HEURISTIC, "Name contains 'Model' or 'Entity'"))

    # Sort by confidence (keep as tuple for now)
    if not candidates:
        candidates.append((ArchitectureRole.UNKNOWN, EvidenceLevel.HEURISTIC, "No naming indicators"))

    return candidates
