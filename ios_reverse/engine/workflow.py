"""
Workflow Management for IOS REVERSE KAISER.

This module handles:
- Workflow loading
- Workflow registry
- Workflow validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import yaml


class WorkflowError(Exception):
    """Raised when workflow operations fail."""
    pass


@dataclass
class WorkflowNode:
    """A node in a workflow DAG."""
    id: str
    name: str
    capability: str
    depends_on: List[str] = field(default_factory=list)
    conditions: Dict = field(default_factory=dict)
    allowed_agents: List[str] = field(default_factory=list)
    tool_override: Optional[str] = None
    timeout_ms: int = 60000
    max_retries: int = 0
    on_failure: str = "abort"  # abort, continue, skip_dependents


@dataclass
class WorkflowEdge:
    """An edge in a workflow DAG."""
    from_node: str
    to_node: str
    edge_type: str = "success"  # success, always


@dataclass
class Workflow:
    """A declarative workflow definition."""
    id: str
    version: str
    name: str
    description: str
    intent: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    capabilities_used: List[str] = field(default_factory=list)
    allowed_agents: List[str] = field(default_factory=list)
    coverage_dimensions: List[str] = field(default_factory=list)

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_dependencies(self, node_id: str) -> Set[str]:
        """Get direct dependencies of a node."""
        node = self.get_node(node_id)
        if node:
            return set(node.depends_on)
        return set()

    def get_dependents(self, node_id: str) -> Set[str]:
        """Get nodes that depend on this node."""
        dependents = set()
        for node in self.nodes:
            if node_id in node.depends_on:
                dependents.add(node.id)
        return dependents

    def topological_sort(self) -> List[str]:
        """Return nodes in topological order."""
        # Build adjacency list (node -> nodes that depend on it)
        adj = {n.id: [] for n in self.nodes}
        in_degree = {n.id: 0 for n in self.nodes}

        for node in self.nodes:
            for dep in node.depends_on:
                if dep in adj:
                    adj[dep].append(node.id)
                    in_degree[node.id] += 1

        # Kahn's algorithm
        queue = [n.id for n in self.nodes if in_degree[n.id] == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for dependent in adj[node_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self.nodes):
            raise WorkflowError("Workflow contains cycles")

        return result

    def validate(self) -> List[str]:
        """Validate workflow and return list of errors."""
        errors = []

        # Check node IDs are unique
        node_ids = [n.id for n in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node IDs found")

        # Check all dependencies exist
        for node in self.nodes:
            for dep in node.depends_on:
                if dep not in node_ids:
                    errors.append(f"Node {node.id} depends on non-existent node {dep}")

        # Check for cycles
        try:
            self.topological_sort()
        except WorkflowError as e:
            errors.append(str(e))

        return errors

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "intent": self.intent,
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "capability": n.capability,
                    "depends_on": n.depends_on,
                    "conditions": n.conditions,
                    "allowed_agents": n.allowed_agents,
                    "tool_override": n.tool_override,
                    "timeout_ms": n.timeout_ms,
                    "max_retries": n.max_retries,
                    "on_failure": n.on_failure,
                }
                for n in self.nodes
            ],
            "edges": [
                {"from": e.from_node, "to": e.to_node, "type": e.edge_type}
                for e in self.edges
            ],
            "capabilities_used": self.capabilities_used,
            "allowed_agents": self.allowed_agents,
            "coverage_dimensions": self.coverage_dimensions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        """Deserialize from dictionary."""
        nodes = [
            WorkflowNode(
                id=n["id"],
                name=n["name"],
                capability=n["capability"],
                depends_on=n.get("depends_on", []),
                conditions=n.get("conditions", {}),
                allowed_agents=n.get("allowed_agents", []),
                tool_override=n.get("tool_override"),
                timeout_ms=n.get("timeout_ms", 60000),
                max_retries=n.get("max_retries", 0),
                on_failure=n.get("on_failure", "abort"),
            )
            for n in data.get("nodes", [])
        ]

        edges = [
            WorkflowEdge(from_node=e["from"], to_node=e["to"], edge_type=e.get("type", "success"))
            for e in data.get("edges", [])
        ]

        return cls(
            id=data["id"],
            version=data.get("version", "1.0.0"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            intent=data["intent"],
            nodes=nodes,
            edges=edges,
            capabilities_used=data.get("capabilities_used", []),
            allowed_agents=data.get("allowed_agents", []),
            coverage_dimensions=data.get("coverage_dimensions", []),
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Workflow":
        """Load workflow from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class WorkflowRegistry:
    """
    Registry of available workflows.

    Manages workflow loading, lookup, and validation.
    """

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._intent_map: Dict[str, List[str]] = {}  # intent -> [workflow_ids]

    def register(self, workflow: Workflow) -> None:
        """Register a workflow."""
        # Validate
        errors = workflow.validate()
        if errors:
            raise WorkflowError(f"Invalid workflow {workflow.id}: {errors}")

        self._workflows[workflow.id] = workflow

        # Update intent map
        if workflow.intent not in self._intent_map:
            self._intent_map[workflow.intent] = []
        self._intent_map[workflow.intent].append(workflow.id)

    def get(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)

    def get_for_intent(self, intent: str) -> List[Workflow]:
        """Get all workflows for an intent."""
        workflow_ids = self._intent_map.get(intent, [])
        return [self._workflows[wid] for wid in workflow_ids if wid in self._workflows]

    def list_all(self) -> List[Workflow]:
        """List all registered workflows."""
        return list(self._workflows.values())

    def list_ids(self) -> List[str]:
        """List all workflow IDs."""
        return list(self._workflows.keys())

    def unregister(self, workflow_id: str) -> None:
        """Unregister a workflow."""
        if workflow_id in self._workflows:
            workflow = self._workflows.pop(workflow_id)
            # Update intent map
            if workflow.intent in self._intent_map:
                if workflow_id in self._intent_map[workflow.intent]:
                    self._intent_map[workflow.intent].remove(workflow_id)
