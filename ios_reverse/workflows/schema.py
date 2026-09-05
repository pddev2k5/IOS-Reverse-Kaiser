"""
Workflow Schema and Models for IOS REVERSE KAISER.

Defines the canonical workflow structure used across all workflows.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime


class Intent(str, Enum):
    """Canonical user-facing intents."""
    UNPACK = "unpack"
    INSPECT = "inspect"
    DUMP = "dump"
    DECOMPILE = "decompile"
    MACHO = "macho"
    OBJC = "objc"
    SWIFT = "swift"
    NETWORK = "network"
    LOGIN_FLOW = "login-flow"
    CRYPTO = "crypto"
    ANTI_ANALYSIS = "anti-analysis"
    IDA = "ida"
    RUNTIME = "runtime"
    REPORT = "report"
    FULL = "full"


class Depth(str, Enum):
    """Depth profiles for workflows."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    FULL = "full"


class WorkflowStatus(str, Enum):
    """Workflow implementation status."""
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"  # Implementation exists, requires external tools/device
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    PLANNED = "planned"


class NodeStatus(str, Enum):
    """Workflow node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class Complexity(str, Enum):
    """Workflow complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ToolEscalationPolicy:
    """Tool escalation policy for a workflow."""
    tool_name: str
    condition: str  # e.g., "static_evidence_insufficient", "depth_requires_decompiler"
    fallback: Optional[str] = None
    block_on_unavailable: bool = False


@dataclass
class AgentPolicy:
    """Agent policy for a workflow."""
    allowed_agents: List[str]
    required_agents: List[str] = field(default_factory=list)
    max_agents: int = 1


@dataclass
class WorkflowCondition:
    """Condition for workflow branching."""
    expression: str  # e.g., "coverage.complete", "tool.available('ida')"
    true_branch: str  # node ID
    false_branch: Optional[str] = None


@dataclass
class WorkflowNode:
    """A node in the workflow DAG."""
    node_id: str
    capability_id: Optional[str] = None  # e.g., "macho.basic"
    sub_workflow: Optional[str] = None  # e.g., "ios.unpack"
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    conditions: List[WorkflowCondition] = field(default_factory=list)
    depth_profiles: Dict[Depth, bool] = field(default_factory=dict)
    tool_requirements: List[str] = field(default_factory=list)
    optional: bool = False
    block_on_failure: bool = True

    def __post_init__(self):
        # Convert depth_profiles from strings if needed
        if self.depth_profiles:
            converted = {}
            for k, v in self.depth_profiles.items():
                if isinstance(k, str):
                    k = Depth(k)
                converted[k] = v
            self.depth_profiles = converted


@dataclass
class WorkflowEdge:
    """An edge in the workflow DAG."""
    from_node: str
    to_node: str
    condition: Optional[str] = None  # Optional condition for conditional edges


@dataclass
class CoveragePolicy:
    """Coverage policy for a workflow."""
    policy_id: str
    workflow: str
    depth: str
    required_dimensions: List[str] = field(default_factory=list)
    blocking_gaps_fail_workflow: bool = True


@dataclass
class OutputArtifact:
    """Expected output artifact from workflow."""
    artifact_type: str
    path_pattern: str  # e.g., "outputs/{workflow}/{artifact}/"
    required: bool = True


@dataclass
class StopCondition:
    """Stop condition for workflow."""
    condition: str  # e.g., "all_nodes_complete", "coverage_complete"
    description: str = ""


@dataclass
class SuccessCondition:
    """Success condition for workflow."""
    condition: str
    description: str = ""


@dataclass
class WorkflowDefinition:
    """
    Complete workflow definition.

    Represents a declarative DAG for workflow execution.
    """
    # Core identity
    workflow_id: str
    version: str = "1.0.0"
    schema_version: str = "1.0.0"

    # Intent
    intent: str = ""
    aliases: List[str] = field(default_factory=list)

    # Status
    status: WorkflowStatus = WorkflowStatus.IMPLEMENTED

    # Artifact support
    accepted_artifacts: List[str] = field(default_factory=list)

    # Depth profiles
    default_depth: Depth = Depth.STANDARD
    supported_depths: List[Depth] = field(default_factory=list)

    # DAG
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)

    # Entry/exit
    entry_node: str = ""
    terminal_nodes: List[str] = field(default_factory=list)

    # Conditions
    conditions: List[WorkflowCondition] = field(default_factory=list)

    # Policies
    coverage_policy: Optional[CoveragePolicy] = None
    tool_policy: List[ToolEscalationPolicy] = field(default_factory=list)
    agent_policy: Optional[AgentPolicy] = None
    complexity: Complexity = Complexity.MEDIUM

    # Stop/success conditions
    stop_conditions: List[StopCondition] = field(default_factory=list)
    success_conditions: List[SuccessCondition] = field(default_factory=list)

    # Outputs
    outputs: List[OutputArtifact] = field(default_factory=list)

    # Resume
    resume_enabled: bool = True

    def __post_init__(self):
        # Convert status if string
        if isinstance(self.status, str):
            self.status = WorkflowStatus(self.status)

        # Convert depth if string
        if isinstance(self.default_depth, str):
            self.default_depth = Depth(self.default_depth)

        # Convert node depth_profiles
        for node in self.nodes:
            if node.depth_profiles:
                converted = {}
                for k, v in node.depth_profiles.items():
                    if isinstance(k, str):
                        k = Depth(k)
                    converted[k] = v
                node.depth_profiles = converted

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get node by ID."""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_entry_node(self) -> Optional[WorkflowNode]:
        """Get entry node."""
        return self.get_node(self.entry_node)

    def get_terminal_nodes(self) -> List[WorkflowNode]:
        """Get terminal nodes."""
        return [n for n in self.nodes if n.node_id in self.terminal_nodes]

    def get_node_dependencies(self, node_id: str) -> List[str]:
        """Get direct dependencies of a node."""
        node = self.get_node(node_id)
        if node:
            return node.dependencies
        return []

    def get_dependents(self, node_id: str) -> List[str]:
        """Get nodes that depend on this node."""
        dependents = []
        for edge in self.edges:
            if edge.from_node == node_id:
                dependents.append(edge.to_node)
        return dependents

    def is_terminal(self, node_id: str) -> bool:
        """Check if node is terminal."""
        return node_id in self.terminal_nodes

    def get_capabilities_for_depth(self, depth: Depth) -> List[str]:
        """Get list of capability IDs for given depth."""
        caps = []
        for node in self.nodes:
            if node.capability_id:
                if not node.depth_profiles:
                    # No depth restriction, include always
                    caps.append(node.capability_id)
                elif node.depth_profiles.get(depth, False):
                    # Explicitly enabled for this depth
                    caps.append(node.capability_id)
                elif depth not in node.depth_profiles:
                    # No explicit restriction, include
                    caps.append(node.capability_id)
        return caps

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "intent": self.intent,
            "aliases": self.aliases,
            "status": self.status.value,
            "accepted_artifacts": self.accepted_artifacts,
            "default_depth": self.default_depth.value,
            "supported_depths": [d.value for d in self.supported_depths],
            "nodes": [
                {
                    "node_id": n.node_id,
                    "capability_id": n.capability_id,
                    "sub_workflow": n.sub_workflow,
                    "description": n.description,
                    "dependencies": n.dependencies,
                    "conditions": [
                        {"expression": c.expression, "true_branch": c.true_branch, "false_branch": c.false_branch}
                        for c in n.conditions
                    ],
                    "depth_profiles": {k.value: v for k, v in n.depth_profiles.items()},
                    "tool_requirements": n.tool_requirements,
                    "optional": n.optional,
                    "block_on_failure": n.block_on_failure,
                }
                for n in self.nodes
            ],
            "edges": [
                {"from": e.from_node, "to": e.to_node, "condition": e.condition}
                for e in self.edges
            ],
            "entry_node": self.entry_node,
            "terminal_nodes": self.terminal_nodes,
            "complexity": self.complexity.value,
            "resume_enabled": self.resume_enabled,
        }


@dataclass
class WorkflowExecutionState:
    """Runtime state for workflow execution."""
    workflow_id: str
    depth: Depth
    started_at: str = ""
    completed_at: Optional[str] = None

    # Node states
    node_states: Dict[str, NodeStatus] = field(default_factory=dict)

    # Artifact references
    artifact_inputs: Dict[str, str] = field(default_factory=dict)  # name -> path
    artifact_outputs: Dict[str, str] = field(default_factory=dict)  # name -> path

    # Coverage
    coverage_audit_id: Optional[str] = None
    coverage_complete: bool = False

    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Resume
    current_node: Optional[str] = None
    next_nodes: List[str] = field(default_factory=list)

    def get_status(self, node_id: str) -> NodeStatus:
        """Get status of a node."""
        return self.node_states.get(node_id, NodeStatus.PENDING)

    def is_node_complete(self, node_id: str) -> bool:
        """Check if node is complete (done or skipped)."""
        status = self.get_status(node_id)
        return status in (NodeStatus.DONE, NodeStatus.SKIPPED)

    def get_incomplete_nodes(self) -> List[str]:
        """Get list of incomplete nodes."""
        return [n for n, s in self.node_states.items()
                if s not in (NodeStatus.DONE, NodeStatus.SKIPPED)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "depth": self.depth.value if isinstance(self.depth, Depth) else self.depth,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "node_states": {k: v.value for k, v in self.node_states.items()},
            "artifact_inputs": self.artifact_inputs,
            "artifact_outputs": self.artifact_outputs,
            "coverage_audit_id": self.coverage_audit_id,
            "coverage_complete": self.coverage_complete,
            "errors": self.errors,
            "warnings": self.warnings,
            "current_node": self.current_node,
            "next_nodes": self.next_nodes,
        }


@dataclass
class WorkflowRegistry:
    """Registry of all workflows."""
    version: str = "1.0.0"
    workflows: Dict[str, WorkflowDefinition] = field(default_factory=dict)

    def register(self, workflow: WorkflowDefinition):
        """Register a workflow."""
        self.workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_by_intent(self, intent: str) -> Optional[WorkflowDefinition]:
        """Get workflow by intent."""
        for wf in self.workflows.values():
            if wf.intent == intent:
                return wf
            if intent in wf.aliases:
                return wf
        return None

    def list_intents(self) -> List[str]:
        """List all supported intents."""
        intents = []
        for wf in self.workflows.values():
            intents.append(wf.intent)
            intents.extend(wf.aliases)
        return sorted(set(intents))

    def list_workflows(self) -> List[str]:
        """List all workflow IDs."""
        return sorted(self.workflows.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "workflows": {
                wf_id: wf.to_dict()
                for wf_id, wf in self.workflows.items()
            }
        }
