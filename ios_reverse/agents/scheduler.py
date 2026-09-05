"""
Task Scheduler for IOS REVERSE KAISER.

Provides deterministic task scheduling based on dependencies.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

from .model import AgentTask, TaskStatus, AgentRole


@dataclass
class TaskSchedule:
    """Task schedule with execution order."""
    ready_tasks: List[AgentTask] = field(default_factory=list)
    blocked_tasks: List[AgentTask] = field(default_factory=list)
    completed_tasks: List[AgentTask] = field(default_factory=list)
    failed_tasks: List[AgentTask] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Dependency graph for tasks."""
    tasks: Dict[str, AgentTask] = field(default_factory=dict)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)  # task_id -> depends_on
    dependents: Dict[str, Set[str]] = field(default_factory=dict)  # task_id -> blocked_by

    def add_task(self, task: AgentTask):
        """Add task to graph."""
        self.tasks[task.task_id] = task
        if task.task_id not in self.dependencies:
            self.dependencies[task.task_id] = set()
        if task.task_id not in self.dependents:
            self.dependents[task.task_id] = set()

    def add_dependency(self, task_id: str, depends_on: str):
        """Add dependency: task_id depends on depends_on."""
        if task_id not in self.dependencies:
            self.dependencies[task_id] = set()
        self.dependencies[task_id].add(depends_on)

        if depends_on not in self.dependents:
            self.dependents[depends_on] = set()
        self.dependents[depends_on].add(task_id)

    def get_dependencies(self, task_id: str) -> Set[str]:
        """Get dependencies for task."""
        return self.dependencies.get(task_id, set())

    def get_dependents(self, task_id: str) -> Set[str]:
        """Get tasks that depend on this task."""
        return self.dependents.get(task_id, set())

    def is_ready(self, task_id: str) -> bool:
        """Check if task is ready to run (all dependencies complete)."""
        deps = self.get_dependencies(task_id)
        for dep_id in deps:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or not dep_task.is_complete():
                return False
        return True


class TaskScheduler:
    """
    Deterministic task scheduler.

    Schedules tasks based on dependencies and priority.
    """

    def __init__(self):
        self.graph = DependencyGraph()
        self._execution_order: List[str] = []

    def add_task(self, task: AgentTask) -> bool:
        """
        Add task to scheduler.

        Returns True if task was added, False if already exists.
        """
        if task.task_id in self.graph.tasks:
            return False

        self.graph.add_task(task)
        return True

    def add_dependency(self, task_id: str, depends_on: str):
        """Add dependency between tasks."""
        self.graph.add_dependency(task_id, depends_on)

    def get_ready_tasks(self) -> List[AgentTask]:
        """Get all tasks that are ready to execute."""
        ready = []
        for task_id, task in self.graph.tasks.items():
            if task.status == TaskStatus.PENDING and self.graph.is_ready(task_id):
                task.status = TaskStatus.READY
                ready.append(task)
        return ready

    def mark_task_done(self, task_id: str, findings: Dict = None):
        """Mark task as done."""
        task = self.graph.tasks.get(task_id)
        if task:
            task.mark_done(findings)
            # Update dependents
            for dep_id in self.graph.get_dependents(task_id):
                dep_task = self.graph.tasks.get(dep_id)
                if dep_task and dep_task.status == TaskStatus.PENDING:
                    if self.graph.is_ready(dep_id):
                        dep_task.status = TaskStatus.READY

    def mark_task_failed(self, task_id: str, error: str):
        """Mark task as failed."""
        task = self.graph.tasks.get(task_id)
        if task:
            task.mark_failed(error)
            # Mark dependents as blocked
            for dep_id in self.graph.get_dependents(task_id):
                dep_task = self.graph.tasks.get(dep_id)
                if dep_task and dep_task.status in (TaskStatus.PENDING, TaskStatus.READY):
                    dep_task.status = TaskStatus.BLOCKED
                    dep_task.errors.append(f"Blocked by failed task: {task_id}")

    def mark_task_blocked(self, task_id: str, reason: str):
        """Mark task as blocked."""
        task = self.graph.tasks.get(task_id)
        if task:
            task.mark_blocked(reason)

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get task by ID."""
        return self.graph.tasks.get(task_id)

    def get_task_schedule(self) -> TaskSchedule:
        """Get current task schedule."""
        ready = []
        blocked = []
        completed = []
        failed = []

        for task in self.graph.tasks.values():
            if task.status == TaskStatus.READY:
                ready.append(task)
            elif task.status == TaskStatus.BLOCKED:
                blocked.append(task)
            elif task.status == TaskStatus.DONE:
                completed.append(task)
            elif task.status == TaskStatus.FAILED:
                failed.append(task)

        return TaskSchedule(
            ready_tasks=ready,
            blocked_tasks=blocked,
            completed_tasks=completed,
            failed_tasks=failed
        )

    def is_complete(self) -> bool:
        """Check if all tasks are complete or blocked."""
        for task in self.graph.tasks.values():
            if task.status in (TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RUNNING):
                return False
        return True

    def has_failures(self) -> bool:
        """Check if any tasks failed."""
        for task in self.graph.tasks.values():
            if task.status == TaskStatus.FAILED:
                return True
        return False

    def get_blocked_count(self) -> int:
        """Get count of blocked tasks."""
        return sum(1 for t in self.graph.tasks.values() if t.status == TaskStatus.BLOCKED)

    def get_failed_count(self) -> int:
        """Get count of failed tasks."""
        return sum(1 for t in self.graph.tasks.values() if t.status == TaskStatus.FAILED)

    def get_completed_count(self) -> int:
        """Get count of completed tasks."""
        return sum(1 for t in self.graph.tasks.values() if t.status == TaskStatus.DONE)

    def get_next_task(self) -> Optional[AgentTask]:
        """Get next task to execute (deterministic)."""
        ready = self.get_ready_tasks()
        if ready:
            # Sort by task_id for deterministic ordering
            ready.sort(key=lambda t: t.task_id)
            return ready[0]
        return None

    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task if allowed."""
        task = self.graph.tasks.get(task_id)
        if not task:
            return False

        if task.status != TaskStatus.FAILED:
            return False

        if task.retry_count >= task.retry_policy.max_retries if hasattr(task, 'retry_policy') else task.retry_count >= 3:
            return False

        # Check if dependencies are now complete
        if self.graph.is_ready(task_id):
            task.status = TaskStatus.READY
            task.errors.clear()
            return True

        return False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "task_count": len(self.graph.tasks),
            "ready": len([t for t in self.graph.tasks.values() if t.status == TaskStatus.READY]),
            "completed": self.get_completed_count(),
            "failed": self.get_failed_count(),
            "blocked": self.get_blocked_count(),
            "is_complete": self.is_complete(),
            "has_failures": self.has_failures(),
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self.graph.tasks.items()
            }
        }


def create_task_from_workflow_node(
    task_id: str,
    case_id: str,
    workflow_id: str,
    node_id: str,
    agent_role: AgentRole,
    objective: str,
    allowed_capabilities: List[str] = None,
    input_artifacts: List[str] = None,
    dependencies: List[str] = None
) -> AgentTask:
    """Create an agent task from workflow node."""
    task = AgentTask(
        task_id=task_id,
        case_id=case_id,
        workflow_id=workflow_id,
        node_id=node_id,
        agent_role=agent_role,
        objective=objective,
        allowed_capabilities=allowed_capabilities or [],
        input_artifacts=input_artifacts or [],
        created_at=datetime.utcnow().isoformat(),
    )

    if dependencies:
        # Dependencies are handled by scheduler, not stored in task
        pass

    return task


def generate_deterministic_id(*parts: str) -> str:
    """Generate deterministic ID from parts."""
    combined = "|".join(parts)
    hash_digest = hashlib.sha256(combined.encode()).hexdigest()[:12]
    return f"{parts[0]}-{hash_digest}"
