"""
DAG Executor for IOS REVERSE KAISER.

This module handles:
- Workflow execution
- Node execution
- Dependency resolution
- State management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

from .state import StateMachine, NodeState, WorkflowState
from .workflow import Workflow, WorkflowNode


class ExecutorError(Exception):
    """Raised when executor operations fail."""
    pass


@dataclass
class ExecutionContext:
    """Context for a single execution."""
    case_id: str
    workflow_id: str
    target: str
    output_dir: str
    depth: str
    options: Dict = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of a node execution."""
    node_id: str
    status: str  # success, failure, skipped
    output: Any = None
    error: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    duration_ms: int = 0


class DAGExecutor:
    """
    Executes workflows as directed acyclic graphs.

    Features:
    - Topological execution order
    - Dependency resolution
    - State machine integration
    - Checkpoint support
    - Retry logic
    """

    def __init__(
        self,
        state_machine: Optional[StateMachine] = None,
        on_node_start: Optional[Callable] = None,
        on_node_complete: Optional[Callable] = None,
        on_node_failure: Optional[Callable] = None,
        on_checkpoint: Optional[Callable] = None,
    ):
        """
        Initialize executor.

        Args:
            state_machine: Optional state machine for tracking
            on_node_start: Callback when node starts
            on_node_complete: Callback when node completes
            on_node_failure: Callback when node fails
            on_checkpoint: Callback when checkpoint is created
        """
        self._state_machine = state_machine or StateMachine()
        self._on_node_start = on_node_start
        self._on_node_complete = on_node_complete
        self._on_node_failure = on_node_failure
        self._on_checkpoint = on_checkpoint

    @property
    def state_machine(self) -> StateMachine:
        """Get the state machine."""
        return self._state_machine

    def execute(
        self,
        workflow: Workflow,
        context: ExecutionContext,
        node_executor: Callable[[WorkflowNode, ExecutionContext], ExecutionResult],
    ) -> Dict[str, ExecutionResult]:
        """
        Execute a workflow.

        Args:
            workflow: Workflow to execute
            context: Execution context
            node_executor: Function to execute a single node

        Returns:
            Dict of node_id -> ExecutionResult

        Raises:
            ExecutorError: If execution fails
        """
        # Initialize state machine with nodes
        self._init_nodes(workflow)

        # Get execution order
        try:
            execution_order = workflow.topological_sort()
        except Exception as e:
            raise ExecutorError(f"Workflow has cycles: {e}")

        # Mark nodes with no dependencies as ready
        for node_id in execution_order:
            node = workflow.get_node(node_id)
            if not node.depends_on:
                self._state_machine.mark_ready(node_id)

        results = {}
        workflow_failed = False

        for node_id in execution_order:
            # Check if workflow has failed and node should abort
            if workflow_failed:
                status = self._state_machine.get_state(node_id)
                if status in {NodeState.PENDING, NodeState.READY}:
                    self._state_machine.mark_skipped(node_id)
                    results[node_id] = ExecutionResult(
                        node_id=node_id,
                        status="skipped",
                        error="Workflow aborted due to earlier failure"
                    )
                continue

            # Check if node should run
            status = self._state_machine.get_state(node_id)
            if status in {NodeState.SKIPPED, NodeState.BLOCKED}:
                continue

            # Wait for dependencies
            node = workflow.get_node(node_id)
            for dep_id in node.depends_on:
                dep_status = self._state_machine.get_state(dep_id)
                if dep_status == NodeState.FAILED:
                    # Check if we should skip dependents
                    dep_node = workflow.get_node(dep_id)
                    if dep_node.on_failure == "skip_dependents":
                        self._state_machine.mark_skipped(node_id)
                        results[node_id] = ExecutionResult(
                            node_id=node_id,
                            status="skipped",
                            error=f"Dependency {dep_id} failed"
                        )
                        continue
                    else:
                        self._state_machine.mark_blocked(node_id)
                        workflow_failed = True
                        break
                elif dep_status == NodeState.SKIPPED:
                    # Dependency was skipped, check conditions
                    pass

            if workflow_failed:
                continue

            # Mark as running
            self._state_machine.mark_running(node_id)

            # Notify start
            if self._on_node_start:
                self._on_node_start(node_id, context)

            # Execute node
            try:
                result = node_executor(node, context)
                results[node_id] = result

                if result.status == "success":
                    self._state_machine.mark_done(node_id)
                elif result.status == "skipped":
                    self._state_machine.mark_skipped(node_id)
                else:
                    # Failure
                    self._state_machine.mark_failed(node_id, result.error)

                    # Check if we should abort
                    if node.on_failure == "abort":
                        workflow_failed = True

                    # Notify failure
                    if self._on_node_failure:
                        self._on_node_failure(node_id, result.error)

            except Exception as e:
                error_msg = str(e)
                results[node_id] = ExecutionResult(
                    node_id=node_id,
                    status="failure",
                    error=error_msg
                )
                self._state_machine.mark_failed(node_id, error_msg)

                if self._on_node_failure:
                    self._on_node_failure(node_id, error_msg)

                if node.on_failure == "abort":
                    workflow_failed = True

            # Notify completion
            if self._on_node_complete:
                self._on_node_complete(node_id, results[node_id])

            # Create checkpoint
            if self._on_checkpoint:
                self._on_checkpoint(node_id, results[node_id])

        return results

    def _init_nodes(self, workflow: Workflow) -> None:
        """Initialize state machine with workflow nodes."""
        for node in workflow.nodes:
            if node.id not in self._state_machine._nodes:
                self._state_machine.add_node(node.id)

    def can_resume(self, workflow: Workflow) -> bool:
        """Check if workflow can be resumed."""
        for node in workflow.nodes:
            status = self._state_machine.get_state(node.id)
            if status in {NodeState.PENDING, NodeState.READY}:
                return True
            if status == NodeState.FAILED:
                node = workflow.get_node(node.id)
                if node.max_retries > 0:
                    current_retries = self._state_machine.get_status(node.id).retry_count
                    if current_retries < node.max_retries:
                        return True
        return False

    def get_execution_summary(self, workflow: Workflow) -> Dict[str, Any]:
        """Get summary of workflow execution."""
        summary = self._state_machine.get_summary()

        # Add workflow-specific info
        summary["workflow_id"] = workflow.id
        summary["can_resume"] = self.can_resume(workflow)

        # Count by status
        done = summary.get("done", 0)
        total = summary.get("total", 0)
        summary["progress_percent"] = (done / total * 100) if total > 0 else 0

        return summary
