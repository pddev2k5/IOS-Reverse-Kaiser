"""
Application Component Model for IOS REVERSE KAISER.

Provides normalized component identity and relationships for application analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set, Tuple
import hashlib
import os


class ComponentType(Enum):
    """Component type classification."""
    APPLICATION = "application"
    FRAMEWORK = "framework"
    DYLIB = "dylib"
    EXTENSION = "extension"
    BUNDLE = "bundle"
    UNKNOWN = "unknown"


class DependencyState(Enum):
    """Dependency resolution state."""
    RESOLVED_EMBEDDED = "resolved_embedded"
    EXTERNAL_SYSTEM = "external_system"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


class Classification(Enum):
    """Framework ownership classification."""
    EMBEDDED = "embedded"
    SYSTEM_EXTERNAL = "system_external"
    UNKNOWN = "unknown"


class OwnershipHint(Enum):
    """Framework ownership hint."""
    FIRST_PARTY = "first_party"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class EdgeType(Enum):
    """Graph edge types."""
    CONTAINS = "contains"
    LOADS = "loads"
    WEAK_LOADS = "weak_loads"
    REEXPORTS = "reexports"
    DEPENDS_ON = "depends_on"  # Generic fallback


@dataclass
class ComponentAddress:
    """Address with explicit semantics."""
    path_type: str  # relative, absolute, rpath, loader_path, executable_path
    value: str
    resolved_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_type": self.path_type,
            "value": self.value,
            "resolved_path": self.resolved_path,
        }


@dataclass
class ArchitectureInfo:
    """Architecture information for a component."""
    cpusubtype: int
    cpu_type: int
    name: str  # arm64, x86_64, etc.
    is_64bit: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpusubtype": self.cpusubtype,
            "cpu_type": self.cpu_type,
            "name": self.name,
            "is_64bit": self.is_64bit,
        }


@dataclass
class ExecutableIdentity:
    """Executable Mach-O identity."""
    path: str  # Relative path within component
    artifact_id: str  # Stable artifact ID (SHA-256 of content)
    sha256: str  # File hash
    size: int  # File size
    architectures: List[ArchitectureInfo] = field(default_factory=list)
    is_fat: bool = False
    slice_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "artifact_id": self.artifact_id,
            "sha256": self.sha256,
            "size": self.size,
            "architectures": [a.to_dict() for a in self.architectures],
            "is_fat": self.is_fat,
            "slice_count": self.slice_count,
        }


@dataclass
class ComponentReference:
    """Reference to another component."""
    target_id: str  # Component ID of target
    target_name: str  # Human-readable name
    target_type: ComponentType
    install_name: Optional[str] = None  # Original LC_LOAD_DYLIB name
    resolved_path: Optional[str] = None  # Resolved embedded path if applicable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_name": self.target_name,
            "target_type": self.target_type.value,
            "install_name": self.install_name,
            "resolved_path": self.resolved_path,
        }


@dataclass
class BaseComponent:
    """Base component with identity."""
    component_id: str  # Stable deterministic ID
    component_type: ComponentType
    name: str  # Bundle/executable name
    bundle_path: str  # Relative path within containing bundle
    artifact_id: str  # SHA-256 of the artifact
    parent_id: Optional[str] = None  # Parent component ID
    containing_app_id: Optional[str] = None  # Top-level app component ID
    provenance: List[str] = field(default_factory=list)  # Evidence sources

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_type": self.component_type.value,
            "name": self.name,
            "bundle_path": self.bundle_path,
            "artifact_id": self.artifact_id,
            "parent_id": self.parent_id,
            "containing_app_id": self.containing_app_id,
            "provenance": self.provenance,
        }


@dataclass
class AppComponent(BaseComponent):
    """Application component (the main .app bundle)."""
    bundle_identifier: Optional[str] = None
    version: Optional[str] = None
    min_os_version: Optional[str] = None
    info_plist_path: Optional[str] = None
    entitlements_path: Optional[str] = None
    main_executable: Optional[ExecutableIdentity] = None
    embedded_components: List[str] = field(default_factory=list)  # Child component IDs

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "bundle_identifier": self.bundle_identifier,
            "version": self.version,
            "min_os_version": self.min_os_version,
            "info_plist_path": self.info_plist_path,
            "entitlements_path": self.entitlements_path,
            "main_executable": self.main_executable.to_dict() if self.main_executable else None,
            "embedded_component_count": len(self.embedded_components),
        })
        return base


@dataclass
class FrameworkComponent(BaseComponent):
    """Framework component."""
    bundle_identifier: Optional[str] = None
    version: Optional[str] = None
    executable: Optional[ExecutableIdentity] = None
    info_plist_path: Optional[str] = None
    classification: Classification = Classification.UNKNOWN
    ownership_hint: OwnershipHint = OwnershipHint.UNKNOWN
    dependencies: List[ComponentReference] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "bundle_identifier": self.bundle_identifier,
            "version": self.version,
            "executable": self.executable.to_dict() if self.executable else None,
            "info_plist_path": self.info_plist_path,
            "classification": self.classification.value,
            "ownership_hint": self.ownership_hint.value,
            "dependency_count": len(self.dependencies),
        })
        return base


@dataclass
class DylibComponent(BaseComponent):
    """Dynamic library component."""
    install_name: Optional[str] = None  # LC_ID_DYLIB or LC_LOAD_DYLIB
    version: Optional[str] = None
    executable: Optional[ExecutableIdentity] = None
    dependencies: List[ComponentReference] = field(default_factory=list)
    is_weak: bool = False  # LC_LOAD_WEAK_DYLIB

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "install_name": self.install_name,
            "version": self.version,
            "executable": self.executable.to_dict() if self.executable else None,
            "dependency_count": len(self.dependencies),
            "is_weak": self.is_weak,
        })
        return base


@dataclass
class ExtensionComponent(BaseComponent):
    """Extension component (.appex)."""
    bundle_identifier: Optional[str] = None
    extension_point: Optional[str] = None  # NSExtensionPointIdentifier
    version: Optional[str] = None
    executable: Optional[ExecutableIdentity] = None
    info_plist_path: Optional[str] = None
    entitlements_path: Optional[str] = None
    parent_component_id: Optional[str] = None  # Parent app/framework
    embedded_components: List[str] = field(default_factory=list)  # Child component IDs

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "bundle_identifier": self.bundle_identifier,
            "extension_point": self.extension_point,
            "version": self.version,
            "executable": self.executable.to_dict() if self.executable else None,
            "info_plist_path": self.info_plist_path,
            "entitlements_path": self.entitlements_path,
            "parent_component_id": self.parent_component_id,
            "embedded_component_count": len(self.embedded_components),
        })
        return base


@dataclass
class BundleComponent(BaseComponent):
    """Generic bundle component."""
    bundle_identifier: Optional[str] = None
    version: Optional[str] = None
    info_plist_path: Optional[str] = None
    executable: Optional[ExecutableIdentity] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "bundle_identifier": self.bundle_identifier,
            "version": self.version,
            "info_plist_path": self.info_plist_path,
            "executable": self.executable.to_dict() if self.executable else None,
        })
        return base


@dataclass
class DependencyEdge:
    """Dependency graph edge."""
    edge_id: str
    source_id: str  # Component ID of source
    target_id: Optional[str]  # Component ID of target (None if unresolved)
    edge_type: EdgeType
    install_name: str  # Original dependency name
    resolved_path: Optional[str] = None  # Resolved path if embedded
    state: DependencyState = DependencyState.UNRESOLVED
    evidence: List[str] = field(default_factory=list)  # Provenance
    is_weak: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "install_name": self.install_name,
            "resolved_path": self.resolved_path,
            "state": self.state.value,
            "evidence": self.evidence,
            "is_weak": self.is_weak,
        }


@dataclass
class ComponentGraph:
    """Complete component graph for an application."""
    root_component_id: str  # Main application component ID
    components: Dict[str, BaseComponent] = field(default_factory=dict)
    edges: List[DependencyEdge] = field(default_factory=list)
    eligible_executables: List[str] = field(default_factory=list)  # Component IDs
    system_dependencies: Set[str] = field(default_factory=set)  # System dylib names
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Indexes for efficient lookup
    _artifact_to_component: Dict[str, str] = field(default_factory=dict, repr=False)
    _name_to_component: Dict[str, List[str]] = field(default_factory=dict, repr=False)
    _install_name_to_component: Dict[str, str] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._artifact_to_component = {}
        self._name_to_component = {}
        self._install_name_to_component = {}

        for comp_id, comp in self.components.items():
            # Artifact to component
            self._artifact_to_component[comp.artifact_id] = comp_id

            # Name to component(s)
            if comp.name not in self._name_to_component:
                self._name_to_component[comp.name] = []
            self._name_to_component[comp.name].append(comp_id)

            # Framework/Dylib install names
            if isinstance(comp, FrameworkComponent) and comp.bundle_identifier:
                self._install_name_to_component[comp.bundle_identifier] = comp_id
            if isinstance(comp, DylibComponent) and comp.install_name:
                self._install_name_to_component[comp.install_name] = comp_id

    def add_component(self, component: BaseComponent):
        """Add a component to the graph."""
        self.components[component.component_id] = component
        self._artifact_to_component[component.artifact_id] = component.component_id
        if component.name not in self._name_to_component:
            self._name_to_component[component.name] = []
        self._name_to_component[component.name].append(component.component_id)

    def add_edge(self, edge: DependencyEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)

    def get_by_artifact_id(self, artifact_id: str) -> Optional[BaseComponent]:
        """Get component by artifact ID."""
        comp_id = self._artifact_to_component.get(artifact_id)
        return self.components.get(comp_id) if comp_id else None

    def get_by_name(self, name: str) -> List[BaseComponent]:
        """Get components by name."""
        comp_ids = self._name_to_component.get(name, [])
        return [self.components[cid] for cid in comp_ids if cid in self.components]

    def get_by_install_name(self, install_name: str) -> Optional[BaseComponent]:
        """Get component by install name."""
        comp_id = self._install_name_to_component.get(install_name)
        return self.components.get(comp_id) if comp_id else None

    def get_containing_components(self, parent_id: str) -> List[BaseComponent]:
        """Get all components contained by a parent."""
        return [c for c in self.components.values() if c.parent_id == parent_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_component_id": self.root_component_id,
            "component_count": len(self.components),
            "edge_count": len(self.edges),
            "eligible_executable_count": len(self.eligible_executables),
            "system_dependency_count": len(self.system_dependencies),
            "warnings": self.warnings,
            "components": {cid: c.to_dict() for cid, c in self.components.items()},
            "edges": [e.to_dict() for e in self.edges],
            "eligible_executables": self.eligible_executables,
            "system_dependencies": list(self.system_dependencies),
        }


def generate_component_id(name: str, artifact_id: str, bundle_path: str) -> str:
    """
    Generate a deterministic component ID.

    Component IDs are based on content (artifact_id) not paths,
    ensuring stability across renames.
    """
    # Create deterministic ID from content
    data = f"{name}:{artifact_id}:{bundle_path}".encode()
    hash_val = hashlib.sha256(data).hexdigest()[:16]
    return f"comp-{hash_val}"


def generate_edge_id(source_id: str, target_id: str, install_name: str) -> str:
    """Generate a deterministic edge ID."""
    data = f"{source_id}:{target_id or 'unresolved'}:{install_name}".encode()
    hash_val = hashlib.sha256(data).hexdigest()[:12]
    return f"edge-{hash_val}"
