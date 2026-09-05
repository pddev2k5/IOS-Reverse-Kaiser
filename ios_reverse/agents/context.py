"""
Agent Context Pack Generator for IOS REVERSE KAISER.

Generates minimal deterministic context packs for agent tasks.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

from .model import AgentTask, AgentRole, TaskStatus
from .registry import get_agent_by_role


@dataclass
class ContextPack:
    """Agent context pack."""
    task_id: str
    agent_role: AgentRole
    objective: str
    workflow_id: str
    node_id: str
    allowed_capabilities: List[str]
    allowed_tools: List[str]
    verified_facts: List[str]
    evidence_refs: List[str]
    artifact_refs: List[str]
    known_failures: List[str]
    expected_outputs: List[str]
    constraints: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_role": self.agent_role.value,
            "objective": self.objective,
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "allowed_capabilities": self.allowed_capabilities,
            "allowed_tools": self.allowed_tools,
            "verified_facts": self.verified_facts,
            "evidence_refs": self.evidence_refs,
            "artifact_refs": self.artifact_refs,
            "known_failures": self.known_failures,
            "expected_outputs": self.expected_outputs,
            "constraints": self.constraints,
        }

    def to_markdown(self) -> str:
        """Convert to markdown for agent consumption."""
        lines = [
            f"# Agent Context Pack: {self.task_id}",
            "",
            f"**Agent Role**: {self.agent_role.value}",
            f"**Workflow**: {self.workflow_id}",
            f"**Node**: {self.node_id}",
            "",
            "## Objective",
            self.objective,
            "",
            "## Allowed Capabilities",
        ]

        for cap in self.allowed_capabilities:
            lines.append(f"- {cap}")

        lines.extend([
            "",
            "## Allowed Tools",
        ])

        for tool in self.allowed_tools:
            lines.append(f"- {tool}")

        if self.verified_facts:
            lines.extend([
                "",
                "## Verified Facts",
            ])
            for fact in self.verified_facts:
                lines.append(f"- {fact}")

        if self.evidence_refs:
            lines.extend([
                "",
                "## Evidence References",
            ])
            for ref in self.evidence_refs:
                lines.append(f"- {ref}")

        if self.artifact_refs:
            lines.extend([
                "",
                "## Artifact References",
            ])
            for ref in self.artifact_refs:
                lines.append(f"- {ref}")

        if self.known_failures:
            lines.extend([
                "",
                "## Known Failures",
            ])
            for failure in self.known_failures:
                lines.append(f"- {failure}")

        if self.expected_outputs:
            lines.extend([
                "",
                "## Expected Outputs",
            ])
            for output in self.expected_outputs:
                lines.append(f"- {output}")

        if self.constraints:
            lines.extend([
                "",
                "## Constraints",
            ])
            for constraint in self.constraints:
                lines.append(f"- {constraint}")

        return "\n".join(lines)


def generate_context_pack(
    task: AgentTask,
    verified_facts: List[str] = None,
    evidence_refs: List[str] = None,
    artifact_refs: List[str] = None,
    known_failures: List[str] = None,
) -> ContextPack:
    """
    Generate context pack for an agent task.

    Args:
        task: Agent task
        verified_facts: Known verified facts
        evidence_refs: Evidence references
        artifact_refs: Artifact references
        known_failures: Known failures from previous runs

    Returns:
        ContextPack
    """
    # Get agent definition
    agent_def = get_agent_by_role(task.agent_role)

    # Get allowed tools from agent definition
    allowed_tools = agent_def.allowed_tools if agent_def else []

    # Build context pack
    return ContextPack(
        task_id=task.task_id,
        agent_role=task.agent_role,
        objective=task.objective,
        workflow_id=task.workflow_id,
        node_id=task.node_id,
        allowed_capabilities=task.allowed_capabilities,
        allowed_tools=allowed_tools,
        verified_facts=verified_facts or [],
        evidence_refs=evidence_refs or task.evidence_refs,
        artifact_refs=artifact_refs or task.input_artifacts,
        known_failures=known_failures or [],
        expected_outputs=task.expected_outputs,
        constraints=task.constraints,
    )


def save_context_pack(
    context_pack: ContextPack,
    workspace_path: str,
    case_id: str
) -> str:
    """
    Save context pack to workspace.

    Args:
        context_pack: Context pack to save
        workspace_path: Base workspace path
        case_id: Case ID

    Returns:
        Path to saved context pack
    """
    # Build path
    context_dir = Path(workspace_path) / "cases" / case_id / ".context" / "agents"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    json_path = context_dir / f"{context_pack.task_id}.json"
    with open(json_path, "w") as f:
        json.dump(context_pack.to_dict(), f, indent=2)

    # Save as Markdown
    md_path = context_dir / f"{context_pack.task_id}.md"
    with open(md_path, "w") as f:
        f.write(context_pack.to_markdown())

    return str(json_path)


def load_context_pack(context_path: str) -> ContextPack:
    """
    Load context pack from file.

    Args:
        context_path: Path to context pack JSON

    Returns:
        ContextPack
    """
    with open(context_path) as f:
        data = json.load(f)

    return ContextPack(
        task_id=data["task_id"],
        agent_role=AgentRole(data["agent_role"]),
        objective=data["objective"],
        workflow_id=data["workflow_id"],
        node_id=data["node_id"],
        allowed_capabilities=data["allowed_capabilities"],
        allowed_tools=data["allowed_tools"],
        verified_facts=data["verified_facts"],
        evidence_refs=data["evidence_refs"],
        artifact_refs=data["artifact_refs"],
        known_failures=data["known_failures"],
        expected_outputs=data["expected_outputs"],
        constraints=data["constraints"],
    )


def generate_agent_workspace(
    workspace_path: str,
    case_id: str,
    agent_role: AgentRole
) -> Dict[str, str]:
    """
    Generate agent workspace structure.

    Args:
        workspace_path: Base workspace path
        case_id: Case ID
        agent_role: Agent role

    Returns:
        Dict mapping subdirectory names to paths
    """
    base = Path(workspace_path) / "cases" / case_id / "agents" / agent_role.value
    paths = {
        "base": str(base),
        "tasks": str(base / "tasks"),
        "findings": str(base / "findings"),
        "handoffs": str(base / "handoffs"),
        "errors": str(base / "errors"),
        "status": str(base / "STATUS.md"),
    }

    # Create directories
    for name, path in paths.items():
        if name != "status":
            Path(path).mkdir(parents=True, exist_ok=True)

    return paths


def write_agent_status(
    workspace_path: str,
    case_id: str,
    agent_role: AgentRole,
    tasks: List[AgentTask]
):
    """Write agent status file."""
    base = Path(workspace_path) / "cases" / case_id / "agents" / agent_role.value

    lines = [
        f"# Agent Status: {agent_role.value}",
        f"",
        f"**Case**: {case_id}",
        f"**Updated**: (auto-generated)",
        f"",
        "## Tasks",
        "",
    ]

    for task in tasks:
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.READY: "✅",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.DONE: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.SKIPPED: "⏭️",
            TaskStatus.STALE: "⚠️",
        }.get(task.status, "❓")

        lines.append(f"{status_icon} {task.task_id}: {task.status.value}")
        lines.append(f"   - Node: {task.node_id}")
        lines.append(f"   - Objective: {task.objective[:50]}...")
        if task.errors:
            lines.append(f"   - Errors: {len(task.errors)}")
        lines.append("")

    # Write status
    status_path = base / "STATUS.md"
    with open(status_path, "w") as f:
        f.write("\n".join(lines))


def write_handoff(
    workspace_path: str,
    case_id: str,
    from_role: AgentRole,
    to_role: AgentRole,
    task_id: str,
    findings_summary: Dict[str, Any]
):
    """Write handoff artifact."""
    base = Path(workspace_path) / "cases" / case_id / "agents" / from_role.value / "handoffs"
    base.mkdir(parents=True, exist_ok=True)

    handoff = {
        "from": from_role.value,
        "to": to_role.value,
        "task_id": task_id,
        "findings": findings_summary,
        "timestamp": "2024-01-01T00:00:00Z",  # Would use datetime
    }

    handoff_path = base / f"handoff-{task_id}.json"
    with open(handoff_path, "w") as f:
        json.dump(handoff, f, indent=2)
