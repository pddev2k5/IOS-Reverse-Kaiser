"""
Callflow Model for IOS REVERSE KAISER.

Provides normalized models for call-flow reconstruction.

IMPORTANT: This represents evidenced call relationships derived from metadata,
NOT speculative call graphs. Unresolved targets must remain explicit.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set


class EdgeType(Enum):
    """Type of call/reference edge."""
    CONFIRMED_CALL = "confirmed_call"         # Proven call
    REFERENCE = "reference"                   # Selector/symbol reference
    METADATA_RELATIONSHIP = "metadata"        # From metadata relationships
    POSSIBLE_CALL = "possible_call"           # Possible but not confirmed
    UNRESOLVED = "unresolved"                 # Target could not be resolved


class EvidenceLevel(Enum):
    """Evidence level for callflow edges."""
    WEAK = "weak"             # Single string match
    REFERENCE = "reference"   # Symbol/selector reference
    STRUCTURAL = "structural" # From call graph/parsing
    CORRELATED = "correlated" # Multiple correlated evidence
    STRONG = "strong"        # Strong evidence of call


class AnchorType(Enum):
    """Type of analysis anchor."""
    ENDPOINT = "endpoint"             # Network endpoint string
    SELECTOR = "selector"           # ObjC selector
    CLASS = "class"                 # Class name
    FUNCTION = "function"           # Function name
    SYMBOL = "symbol"              # Symbol
    HEADER = "header"              # HTTP header
    CRYPTO = "crypto"              # Crypto primitive
    ARCHITECTURE = "architecture"  # Architecture component


@dataclass
class FlowAnchor:
    """
    Anchor for callflow analysis.

    An anchor is a starting point for callflow reconstruction.
    """
    anchor_id: str
    anchor_type: AnchorType
    value: str                         # The anchor value
    component_id: Optional[str] = None    # Which component
    artifact_id: Optional[str] = None     # Which artifact
    offset: Optional[int] = None         # Offset if from binary
    evidence_strength: EvidenceLevel = EvidenceLevel.REFERENCE

    # References from this anchor
    referencing_nodes: List[str] = field(default_factory=list)  # Node IDs that reference this anchor
    referenced_by: List[str] = field(default_factory=list)      # Nodes that this anchor references

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "anchor_type": self.anchor_type.value,
            "value": self.value,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "offset": self.offset,
            "evidence_strength": self.evidence_strength.value,
            "referencing_node_count": len(self.referencing_nodes),
            "referenced_by_count": len(self.referenced_by),
        }


@dataclass
class FunctionNode:
    """
    Function or method in the call graph.
    """
    node_id: str                       # Stable deterministic ID
    name: str                        # Function/method name
    demangled_name: Optional[str] = None  # If Swift

    # Type
    is_method: bool = False          # ObjC method or Swift func
    is_init: bool = False            # Initializer
    is_class_method: bool = False     # Class method vs instance

    # Location
    component_id: Optional[str] = None    # From P04.4
    artifact_id: Optional[str] = None     # Which binary
    address: Optional[int] = None         # Virtual address

    # Classification
    selector: Optional[str] = None       # ObjC selector
    swift_type: Optional[str] = None     # Swift type if method

    # Relationships
    anchors: List[str] = field(default_factory=list)       # Anchor IDs referencing this
    inbound_calls: List[str] = field(default_factory=list)  # Nodes calling this
    outbound_calls: List[str] = field(default_factory=list)  # Nodes this calls

    # Evidence
    evidence_level: EvidenceLevel = EvidenceLevel.REFERENCE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "demangled_name": self.demangled_name,
            "is_method": self.is_method,
            "is_init": self.is_init,
            "is_class_method": self.is_class_method,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "address": self.address,
            "selector": self.selector,
            "swift_type": self.swift_type,
            "anchor_count": len(self.anchors),
            "inbound_call_count": len(self.inbound_calls),
            "outbound_call_count": len(self.outbound_calls),
            "evidence_level": self.evidence_level.value,
        }


@dataclass
class CallEdge:
    """
    Edge representing a call relationship.
    """
    edge_id: str                       # Stable deterministic ID
    source_id: str                    # Source node ID
    target_id: str                    # Target node ID
    edge_type: EdgeType

    # Evidence
    evidence_level: EvidenceLevel = EvidenceLevel.REFERENCE
    evidence_sources: List[str] = field(default_factory=list)

    # Details
    context: Optional[str] = None       # Where call occurs (method name, etc.)
    offset: Optional[int] = None        # Offset in source binary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "evidence_level": self.evidence_level.value,
            "evidence_sources": self.evidence_sources,
            "context": self.context,
            "offset": self.offset,
        }


@dataclass
class UnresolvedTarget:
    """
    Call target that could not be resolved.

    Critical: Unresolved targets must remain explicit, not invented.
    """
    unresolved_id: str
    name: str                         # The unresolved name
    source_id: str                    # Node that references this
    reason: str                       # Why unresolved (no_symbol, ambiguous, etc.)

    # Evidence
    evidence_level: EvidenceLevel = EvidenceLevel.WEAK
    evidence_sources: List[str] = field(default_factory=list)

    # Possible targets (if ambiguous)
    possible_targets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unresolved_id": self.unresolved_id,
            "name": self.name,
            "source_id": self.source_id,
            "reason": self.reason,
            "evidence_level": self.evidence_level.value,
            "evidence_sources": self.evidence_sources,
            "possible_target_count": len(self.possible_targets),
        }


@dataclass
class CallFlow:
    """
    Complete call flow model for an application.
    """
    artifact_path: str

    # Core elements
    anchors: List[FlowAnchor] = field(default_factory=list)
    nodes: List[FunctionNode] = field(default_factory=list)
    edges: List[CallEdge] = field(default_factory=list)
    unresolved: List[UnresolvedTarget] = field(default_factory=list)

    # Statistics
    confirmed_call_count: int = 0
    reference_count: int = 0
    unresolved_count: int = 0

    # Indexes
    _node_by_id: Dict[str, FunctionNode] = field(default_factory=dict, repr=False)
    _node_by_name: Dict[str, List[FunctionNode]] = field(default_factory=dict, repr=False)
    _anchor_by_id: Dict[str, FlowAnchor] = field(default_factory=dict, repr=False)
    _anchor_by_value: Dict[str, List[FlowAnchor]] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._node_by_id = {n.node_id: n for n in self.nodes}
        self._node_by_name = {}
        for node in self.nodes:
            if node.name not in self._node_by_name:
                self._node_by_name[node.name] = []
            self._node_by_name[node.name].append(node)

        self._anchor_by_id = {a.anchor_id: a for a in self.anchors}
        self._anchor_by_value = {}
        for anchor in self.anchors:
            if anchor.value not in self._anchor_by_value:
                self._anchor_by_value[anchor.value] = []
            self._anchor_by_value[anchor.value].append(anchor)

    def get_node(self, node_id: str) -> Optional[FunctionNode]:
        """Get node by ID."""
        return self._node_by_id.get(node_id)

    def get_nodes_by_name(self, name: str) -> List[FunctionNode]:
        """Get nodes by name."""
        return self._node_by_name.get(name, [])

    def get_anchor(self, anchor_id: str) -> Optional[FlowAnchor]:
        """Get anchor by ID."""
        return self._anchor_by_id.get(anchor_id)

    def get_anchors_by_value(self, value: str) -> List[FlowAnchor]:
        """Get anchors by value."""
        return self._anchor_by_value.get(value, [])

    def compute_statistics(self):
        """Compute edge type statistics."""
        self.confirmed_call_count = sum(1 for e in self.edges if e.edge_type == EdgeType.CONFIRMED_CALL)
        self.reference_count = sum(1 for e in self.edges if e.edge_type == EdgeType.REFERENCE)
        self.unresolved_count = len(self.unresolved)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "anchor_count": len(self.anchors),
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "unresolved_count": self.unresolved_count,
            "confirmed_call_count": self.confirmed_call_count,
            "reference_count": self.reference_count,
            "anchors": [a.to_dict() for a in self.anchors],
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "unresolved": [u.to_dict() for u in self.unresolved],
        }


def generate_node_id(name: str, artifact_id: str, address: Optional[int] = None) -> str:
    """Generate deterministic node ID."""
    import hashlib
    content = f"{name}:{artifact_id}:{address}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"cfn-{hash_val}"


def generate_edge_id(source_id: str, target_id: str, context: Optional[str] = None) -> str:
    """Generate deterministic edge ID."""
    import hashlib
    content = f"{source_id}:{target_id}:{context}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"cfe-{hash_val}"


def generate_anchor_id(anchor_type: str, value: str) -> str:
    """Generate deterministic anchor ID."""
    import hashlib
    content = f"{anchor_type}:{value}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"cfa-{hash_val}"
