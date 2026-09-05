"""
State Machine for IOS REVERSE KAISER.

This module handles:
- Node state definitions
- State transition rules
- Workflow state tracking
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


class NodeState(Enum):
    """Node execution states."""
    PENDING = "PENDING"     # Not yet ready
    READY = "READY"          # Dependencies satisfied
    RUNNING = "RUNNING"      # Currently executing
    DONE = "DONE"            # Successfully completed
    SKIPPED = "SKIPPED"      # Intentionally skipped
    BLOCKED = "BLOCKED"      # Dependency failed
    FAILED = "FAILED"        # Execution failed
    STALE = "STALE"          # Outputs invalidated


# Valid state transitions
VALID_TRANSITIONS = {
    NodeState.PENDING: {NodeState.READY, NodeState.SKIPPED},
    NodeState.READY: {NodeState.RUNNING, NodeState.SKIPPED},
    NodeState.RUNNING: {NodeState.DONE, NodeState.SKIPPED, NodeState.FAILED},
    NodeState.DONE: {NodeState.STALE},
    NodeState.SKIPPED: set(),
    NodeState.BLOCKED: {NodeState.SKIPPED, NodeState.PENDING},
    NodeState.FAILED: set(),
    NodeState.STALE: {NodeState.PENDING, NodeState.SKIPPED},
}


@dataclass
class NodeStatus:
    """Status of a workflow node."""
    state: NodeState
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    output_path: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateMachine:
    """
    Manages workflow node states.

    Enforces valid state transitions and tracks history.
    """

    def __init__(self):
        self._nodes: Dict[str, NodeStatus] = {}

    def add_node(self, node_id: str) -> None:
        """Add a node with PENDING state."""
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id} already exists")
        self._nodes[node_id] = NodeStatus(state=NodeState.PENDING)

    def get_state(self, node_id: str) -> NodeState:
        """Get current state of a node."""
        if node_id not in self._nodes:
            raise ValueError(f"Node {node_id} not found")
        return self._nodes[node_id].state

    def get_status(self, node_id: str) -> NodeStatus:
        """Get full status of a node."""
        if node_id not in self._nodes:
            raise ValueError(f"Node {node_id} not found")
        return self._nodes[node_id]

    def transition(self, node_id: str, new_state: NodeState, error: Optional[str] = None) -> None:
        """
        Transition a node to a new state.

        Args:
            node_id: Node identifier
            new_state: Target state
            error: Error message if transitioning to FAILED

        Raises:
            StateTransitionError: If transition is invalid
        """
        if node_id not in self._nodes:
            raise ValueError(f"Node {node_id} not found")

        current = self._nodes[node_id].state

        # Check if transition is valid
        valid = VALID_TRANSITIONS.get(current, set())
        if new_state not in valid:
            raise StateTransitionError(
                f"Invalid transition: {current.value} -> {new_state.value} "
                f"for node {node_id}"
            )

        # Update state
        self._nodes[node_id].state = new_state

        # Set timestamps
        now = datetime.utcnow()
        if new_state == NodeState.RUNNING:
            self._nodes[node_id].started_at = now
        elif new_state in {NodeState.DONE, NodeState.SKIPPED, NodeState.FAILED}:
            self._nodes[node_id].completed_at = now

        # Set error if failing
        if new_state == NodeState.FAILED and error:
            self._nodes[node_id].error = error

    def mark_ready(self, node_id: str) -> None:
        """Mark a node as READY (dependencies satisfied)."""
        self.transition(node_id, NodeState.READY)

    def mark_running(self, node_id: str) -> None:
        """Mark a node as RUNNING."""
        self.transition(node_id, NodeState.RUNNING)

    def mark_done(self, node_id: str, output_path: Optional[str] = None) -> None:
        """Mark a node as DONE."""
        self._nodes[node_id].output_path = output_path
        self.transition(node_id, NodeState.DONE)

    def mark_skipped(self, node_id: str) -> None:
        """Mark a node as SKIPPED."""
        self.transition(node_id, NodeState.SKIPPED)

    def mark_failed(self, node_id: str, error: str) -> None:
        """Mark a node as FAILED."""
        self.transition(node_id, NodeState.FAILED, error=error)

    def mark_stale(self, node_id: str) -> None:
        """Mark a node as STALE (outputs invalidated)."""
        self.transition(node_id, NodeState.STALE)

    def reset(self, node_id: str) -> None:
        """Reset a STALE node to PENDING."""
        self.transition(node_id, NodeState.PENDING)

    def can_run(self, node_id: str) -> bool:
        """Check if a node can be executed (READY state)."""
        return self.get_state(node_id) == NodeState.READY

    def is_complete(self, node_id: str) -> bool:
        """Check if a node is in a terminal state."""
        return self.get_state(node_id) in {NodeState.DONE, NodeState.SKIPPED}

    def is_failed(self, node_id: str) -> bool:
        """Check if a node has failed."""
        return self.get_state(node_id) == NodeState.FAILED

    def get_pending_nodes(self) -> List[str]:
        """Get list of nodes in PENDING state."""
        return [n for n, s in self._nodes.items() if s.state == NodeState.PENDING]

    def get_ready_nodes(self) -> List[str]:
        """Get list of nodes in READY state."""
        return [n for n, s in self._nodes.items() if s.state == NodeState.READY]

    def get_running_nodes(self) -> List[str]:
        """Get list of nodes in RUNNING state."""
        return [n for n, s in self._nodes.items() if s.state == NodeState.RUNNING]

    def get_done_nodes(self) -> List[str]:
        """Get list of nodes in DONE state."""
        return [n for n, s in self._nodes.items() if s.state == NodeState.DONE]

    def get_failed_nodes(self) -> List[str]:
        """Get list of nodes in FAILED state."""
        return [n for n, s in self._nodes.items() if s.state == NodeState.FAILED]

    def get_summary(self) -> dict:
        """Get summary of all node states."""
        states = {}
        for node_id, status in self._nodes.items():
            states[node_id] = status.state.value
        return {
            "total": len(self._nodes),
            "pending": len(self.get_pending_nodes()),
            "ready": len(self.get_ready_nodes()),
            "running": len(self.get_running_nodes()),
            "done": len(self.get_done_nodes()),
            "failed": len(self.get_failed_nodes()),
            "states": states,
        }

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "nodes": {
                node_id: {
                    "state": status.state.value,
                    "started_at": status.started_at.isoformat() if status.started_at else None,
                    "completed_at": status.completed_at.isoformat() if status.completed_at else None,
                    "error": status.error,
                    "retry_count": status.retry_count,
                    "output_path": status.output_path,
                    "evidence_ids": status.evidence_ids,
                }
                for node_id, status in self._nodes.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StateMachine":
        """Deserialize from dictionary."""
        machine = cls()
        for node_id, status_data in data.get("nodes", {}).items():
            machine._nodes[node_id] = NodeStatus(
                state=NodeState(status_data["state"]),
                started_at=datetime.fromisoformat(status_data["started_at"]) if status_data.get("started_at") else None,
                completed_at=datetime.fromisoformat(status_data["completed_at"]) if status_data.get("completed_at") else None,
                error=status_data.get("error"),
                retry_count=status_data.get("retry_count", 0),
                output_path=status_data.get("output_path"),
                evidence_ids=status_data.get("evidence_ids", []),
            )
        return machine


@dataclass
class WorkflowState:
    """Overall workflow state."""
    workflow_id: str
    workflow_version: str
    status: str = "PENDING"  # PENDING, RUNNING, DONE, FAILED, ABORTED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    state_machine: Optional[StateMachine] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "state": self.state_machine.to_dict() if self.state_machine else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowState":
        """Deserialize from dictionary."""
        state = cls(
            workflow_id=data["workflow_id"],
            workflow_version=data["workflow_version"],
            status=data.get("status", "PENDING"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
        )
        if data.get("state"):
            state.state_machine = StateMachine.from_dict(data["state"])
        return state
