"""
Checkpoint Management for IOS REVERSE KAISER.

This module handles:
- Checkpoint creation
- Checkpoint storage
- Checkpoint restoration
- Context pack generation
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class CheckpointError(Exception):
    """Raised when checkpoint operations fail."""
    pass


@dataclass
class Checkpoint:
    """A checkpoint of workflow state."""
    id: str
    build: str
    phase: str
    endpoint: str
    status: str
    created: datetime
    updated: datetime
    version: str

    # Execution state
    completed_nodes: List[str] = field(default_factory=list)
    current_node: str = ""
    next_actions: List[str] = field(default_factory=list)

    # Workflow state
    workflow_id: Optional[str] = None
    workflow_state: Optional[Dict] = None

    # Metrics
    metrics: Dict = field(default_factory=dict)
    tests: Dict = field(default_factory=dict)
    known_failures: List[str] = field(default_factory=list)

    # File references
    important_files: List[str] = field(default_factory=list)

    # Resume
    resume_instructions: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "build": self.build,
            "phase": self.phase,
            "endpoint": self.endpoint,
            "status": self.status,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "version": self.version,
            "completed_nodes": self.completed_nodes,
            "current_node": self.current_node,
            "next_actions": self.next_actions,
            "workflow_id": self.workflow_id,
            "workflow_state": self.workflow_state,
            "metrics": self.metrics,
            "tests": self.tests,
            "known_failures": self.known_failures,
            "important_files": self.important_files,
            "resume_instructions": self.resume_instructions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            build=data["build"],
            phase=data["phase"],
            endpoint=data["endpoint"],
            status=data["status"],
            created=datetime.fromisoformat(data["created"]),
            updated=datetime.fromisoformat(data["updated"]),
            version=data.get("version", "1.0.0"),
            completed_nodes=data.get("completed_nodes", []),
            current_node=data.get("current_node", ""),
            next_actions=data.get("next_actions", []),
            workflow_id=data.get("workflow_id"),
            workflow_state=data.get("workflow_state"),
            metrics=data.get("metrics", {}),
            tests=data.get("tests", {}),
            known_failures=data.get("known_failures", []),
            important_files=data.get("important_files", []),
            resume_instructions=data.get("resume_instructions", ""),
        )

    def save(self, path: Path) -> None:
        """Save checkpoint to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> "Checkpoint":
        """Load checkpoint from file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


class CheckpointManager:
    """
    Manages checkpoint creation and restoration.

    Features:
    - Sequential checkpoint IDs
    - Latest pointer tracking
    - Workflow state snapshots
    - Context pack generation
    """

    def __init__(
        self,
        checkpoint_dir: Path,
        build_name: str = "ios-reverse-kaiser"
    ):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
            build_name: Name of the build
        """
        self._checkpoint_dir = Path(checkpoint_dir)
        self._build_name = build_name
        self._counter = 0

        # Ensure directory exists
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Load latest checkpoint
        self._latest = self._load_latest()

    def _load_latest(self) -> Optional[Checkpoint]:
        """Load the latest checkpoint."""
        latest_path = self._checkpoint_dir / "latest.json"
        if latest_path.exists():
            with open(latest_path, encoding="utf-8") as f:
                data = json.load(f)
            cp_path = self._checkpoint_dir / f"{data.get('checkpoint_file', 'latest.json')}"
            if cp_path.exists():
                return Checkpoint.load(cp_path)
        return None

    def _get_next_id(self) -> str:
        """Get next checkpoint ID."""
        self._counter += 1
        return f"CP-{self._counter:03d}"

    def create(
        self,
        phase: str,
        endpoint: str,
        status: str,
        current_node: str = "",
        next_actions: Optional[List[str]] = None,
        workflow_id: Optional[str] = None,
        workflow_state: Optional[Dict] = None,
        metrics: Optional[Dict] = None,
        tests: Optional[Dict] = None,
        known_failures: Optional[List[str]] = None,
        important_files: Optional[List[str]] = None,
        resume_instructions: str = "",
    ) -> Checkpoint:
        """
        Create a new checkpoint.

        Args:
            phase: Current phase
            endpoint: Current endpoint
            status: Checkpoint status
            current_node: Current node being executed
            next_actions: List of next actions
            workflow_id: Workflow being executed
            workflow_state: Current workflow state
            metrics: Execution metrics
            tests: Test results
            known_failures: Known failures
            important_files: Important files to preserve
            resume_instructions: Instructions for resuming

        Returns:
            Created Checkpoint
        """
        now = datetime.utcnow()
        cp_id = self._get_next_id()

        checkpoint = Checkpoint(
            id=cp_id,
            build=self._build_name,
            phase=phase,
            endpoint=endpoint,
            status=status,
            created=now,
            updated=now,
            version="1.0.0",
            current_node=current_node,
            next_actions=next_actions or [],
            workflow_id=workflow_id,
            workflow_state=workflow_state,
            metrics=metrics or {},
            tests=tests or {},
            known_failures=known_failures or [],
            important_files=important_files or [],
            resume_instructions=resume_instructions,
        )

        # Save checkpoint
        cp_path = self._checkpoint_dir / f"{cp_id}.json"
        checkpoint.save(cp_path)

        # Update latest pointer
        latest_path = self._checkpoint_dir / "latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump({
                "latest": cp_id,
                "build": self._build_name,
                "phase": phase,
                "endpoint": endpoint,
                "status": status,
                "timestamp": now.isoformat(),
                "checkpoint_file": f"{cp_id}.json",
                "resume_instructions": resume_instructions,
            }, f, indent=2)

        self._latest = checkpoint
        return checkpoint

    def get_latest(self) -> Optional[Checkpoint]:
        """Get the latest checkpoint."""
        return self._latest

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint."""
        path = self._checkpoint_dir / f"{checkpoint_id}.json"
        if path.exists():
            return Checkpoint.load(path)
        return None

    def list_all(self) -> List[Checkpoint]:
        """List all checkpoints."""
        checkpoints = []
        for path in self._checkpoint_dir.glob("CP-*.json"):
            checkpoints.append(Checkpoint.load(path))
        return sorted(checkpoints, key=lambda c: c.created)

    def generate_context_pack(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """
        Generate a context pack from a checkpoint.

        Context packs are used for resuming without conversation history.

        Args:
            checkpoint: Checkpoint to generate from

        Returns:
            Context pack dictionary
        """
        return {
            "phase": checkpoint.phase,
            "status": checkpoint.status,
            "current_objective": checkpoint.current_node,
            "completed_nodes": checkpoint.completed_nodes,
            "next_actions": checkpoint.next_actions,
            "workflow_id": checkpoint.workflow_id,
            "metrics": checkpoint.metrics,
            "tests": checkpoint.tests,
            "known_failures": checkpoint.known_failures,
            "important_files": checkpoint.important_files,
            "resume_instructions": checkpoint.resume_instructions,
            "generated_at": datetime.utcnow().isoformat(),
        }
