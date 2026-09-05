"""
Canonical Provenance Model for IOS REVERSE KAISER.

Provides unified provenance tracking across all analytical entities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import hashlib


class ProvenanceNodeType(str, Enum):
    """Types of provenance nodes."""
    CASE = "case"
    WORKFLOW_RUN = "workflow_run"
    WORKFLOW_NODE = "workflow_node"
    AGENT_TASK = "agent_task"
    CAPABILITY_EXECUTION = "capability_execution"
    ADAPTER_EXECUTION = "adapter_execution"
    ARTIFACT = "artifact"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    FUNCTION = "function"
    ENDPOINT = "endpoint"
    CALLFLOW = "callflow"
    COVERAGE = "coverage"
    REPORT_FINDING = "report_finding"


class ProvenanceEdgeType(str, Enum):
    """Types of provenance edges."""
    DERIVED_FROM = "derived_from"
    PRODUCED_BY = "produced_by"
    CONSUMED_BY = "consumed_by"
    SUPPORTED_BY = "supported_by"
    VALIDATED_BY = "validated_by"
    REFERENCES = "references"
    BELONGS_TO = "belongs_to"
    OBSERVED_IN = "observed_in"
    REPORTED_AS = "reported_as"
    INVALIDATED_BY = "invalidated_by"
    CONFLICTS_WITH = "conflicts_with"
    RESOLVED_AS = "resolved_as"


class ExecutionStatus(str, Enum):
    """Execution status for provenance nodes."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    STALE = "stale"


@dataclass
class ProvenanceNode:
    """
    A node in the provenance graph.

    Represents any entity that can be traced through the analytical pipeline.
    """
    node_id: str
    node_type: ProvenanceNodeType
    case_id: str
    created_at: str
    label: str = ""
    parent_refs: List[str] = field(default_factory=list)  # Direct parents
    child_refs: List[str] = field(default_factory=list)   # Direct children
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_status: Optional[ExecutionStatus] = None
    schema_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "case_id": self.case_id,
            "created_at": self.created_at,
            "label": self.label,
            "parent_refs": self.parent_refs,
            "child_refs": self.child_refs,
            "metadata": self.metadata,
            "execution_status": self.execution_status.value if self.execution_status else None,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProvenanceNode':
        return cls(
            node_id=data["node_id"],
            node_type=ProvenanceNodeType(data["node_type"]),
            case_id=data["case_id"],
            created_at=data["created_at"],
            label=data.get("label", ""),
            parent_refs=data.get("parent_refs", []),
            child_refs=data.get("child_refs", []),
            metadata=data.get("metadata", {}),
            execution_status=ExecutionStatus(data["execution_status"]) if data.get("execution_status") else None,
            schema_version=data.get("schema_version", "1.0.0"),
        )


@dataclass
class ProvenanceEdge:
    """
    An edge in the provenance graph.

    Represents relationships between provenance nodes.
    """
    edge_id: str
    source_id: str
    target_id: str
    edge_type: ProvenanceEdgeType
    case_id: str
    created_at: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "case_id": self.case_id,
            "created_at": self.created_at,
            "weight": self.weight,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProvenanceEdge':
        return cls(
            edge_id=data["edge_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=ProvenanceEdgeType(data["edge_type"]),
            case_id=data["case_id"],
            created_at=data["created_at"],
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProvenanceEvent:
    """
    A provenance event (edge with context).

    Records significant analytical events.
    """
    event_id: str
    event_type: str
    case_id: str
    source_node_id: str
    target_node_id: str
    edge_type: ProvenanceEdgeType
    timestamp: str
    actor: str = ""  # agent role, capability, etc.
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "case_id": self.case_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_type": self.edge_type.value,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "reason": self.reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProvenanceEvent':
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            case_id=data["case_id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            edge_type=ProvenanceEdgeType(data["edge_type"]),
            timestamp=data["timestamp"],
            actor=data.get("actor", ""),
            reason=data.get("reason", ""),
            metadata=data.get("metadata", {}),
        )


class ProvenanceGraph:
    """
    In-memory provenance graph.

    Provides efficient traversal and querying.
    """

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.nodes: Dict[str, ProvenanceNode] = {}
        self.edges: Dict[str, ProvenanceEdge] = {}
        self._adjacency: Dict[str, Set[str]] = {}  # node_id -> child node_ids
        self._reverse_adjacency: Dict[str, Set[str]] = {}  # node_id -> parent node_ids

    def add_node(self, node: ProvenanceNode) -> bool:
        """Add a node to the graph."""
        if node.node_id in self.nodes:
            return False
        self.nodes[node.node_id] = node
        self._adjacency[node.node_id] = set()
        self._reverse_adjacency[node.node_id] = set()
        return True

    def add_edge(self, edge: ProvenanceEdge) -> bool:
        """Add an edge to the graph."""
        if edge.edge_id in self.edges:
            return False

        # Ensure nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            return False

        self.edges[edge.edge_id] = edge

        # Update adjacency lists
        self._adjacency[edge.source_id].add(edge.target_id)
        self._reverse_adjacency[edge.target_id].add(edge.source_id)

        # Update node parent/child refs
        self.nodes[edge.source_id].child_refs.append(edge.target_id)
        self.nodes[edge.target_id].parent_refs.append(edge.source_id)

        return True

    def get_node(self, node_id: str) -> Optional[ProvenanceNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_ancestors(self, node_id: str, max_depth: int = None) -> List[str]:
        """Get all ancestor node IDs (reverse traversal)."""
        ancestors = []
        visited = set()
        to_visit = list(self._reverse_adjacency.get(node_id, set()))
        depth = 0

        while to_visit and (max_depth is None or depth < max_depth):
            next_level = []
            for parent_id in to_visit:
                if parent_id not in visited:
                    visited.add(parent_id)
                    ancestors.append(parent_id)
                    next_level.extend(self._reverse_adjacency.get(parent_id, []))
            to_visit = next_level
            depth += 1

        return ancestors

    def get_descendants(self, node_id: str, max_depth: int = None) -> List[str]:
        """Get all descendant node IDs (forward traversal)."""
        descendants = []
        visited = set()
        to_visit = list(self._adjacency.get(node_id, set()))
        depth = 0

        while to_visit and (max_depth is None or depth < max_depth):
            next_level = []
            for child_id in to_visit:
                if child_id not in visited:
                    visited.add(child_id)
                    descendants.append(child_id)
                    next_level.extend(self._adjacency.get(child_id, []))
            to_visit = next_level
            depth += 1

        return descendants

    def get_ancestor_nodes(self, node_id: str, max_depth: int = None) -> List[ProvenanceNode]:
        """Get ancestor nodes."""
        ancestor_ids = self.get_ancestors(node_id, max_depth)
        return [self.nodes[nid] for nid in ancestor_ids if nid in self.nodes]

    def get_descendant_nodes(self, node_id: str, max_depth: int = None) -> List[ProvenanceNode]:
        """Get descendant nodes."""
        descendant_ids = self.get_descendants(node_id, max_depth)
        return [self.nodes[nid] for nid in descendant_ids if nid in self.nodes]

    def find_nodes_by_type(self, node_type: ProvenanceNodeType) -> List[ProvenanceNode]:
        """Find all nodes of a specific type."""
        return [n for n in self.nodes.values() if n.node_type == node_type]

    def find_nodes_by_metadata(self, key: str, value: Any) -> List[ProvenanceNode]:
        """Find nodes with specific metadata."""
        return [n for n in self.nodes.values() if n.metadata.get(key) == value]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "case_id": self.case_id,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProvenanceGraph':
        """Deserialize from dictionary."""
        graph = cls(case_id=data["case_id"])

        # Load nodes
        for nid, node_data in data.get("nodes", {}).items():
            graph.add_node(ProvenanceNode.from_dict(node_data))

        # Load edges
        for eid, edge_data in data.get("edges", {}).items():
            graph.add_edge(ProvenanceEdge.from_dict(edge_data))

        return graph

    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: List[str]):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for child_id in self._adjacency.get(node_id, set()):
                if child_id not in visited:
                    dfs(child_id, path.copy())
                elif child_id in rec_stack:
                    # Found cycle
                    cycle_start = path.index(child_id)
                    cycles.append(path[cycle_start:] + [child_id])

            rec_stack.remove(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles


def generate_provenance_id(prefix: str, *parts: str) -> str:
    """Generate a deterministic provenance ID."""
    combined = "|".join([prefix] + list(parts))
    hash_digest = hashlib.sha256(combined.encode()).hexdigest()[:12]
    return f"prv-{prefix}-{hash_digest}"


def generate_event_id(event_type: str, case_id: str) -> str:
    """Generate an event ID."""
    timestamp = datetime.utcnow().isoformat()
    combined = f"{event_type}|{case_id}|{timestamp}"
    hash_digest = hashlib.sha256(combined.encode()).hexdigest()[:12]
    return f"evt-{hash_digest}"
