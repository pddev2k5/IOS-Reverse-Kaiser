"""
Workflow Registry for IOS REVERSE KAISER.

Provides access to all canonical workflow definitions.
"""

from .schema import WorkflowRegistry, Intent, Depth
from .definitions import create_all_workflows

# Create global registry
_registry: WorkflowRegistry = None


def get_registry() -> WorkflowRegistry:
    """Get or create the workflow registry."""
    global _registry
    if _registry is None:
        _registry = WorkflowRegistry()
        workflows = create_all_workflows()
        for workflow_id, workflow in workflows.items():
            _registry.register(workflow)
    return _registry


def get_workflow(workflow_id: str):
    """Get a workflow by ID."""
    return get_registry().get(workflow_id)


def get_workflow_by_intent(intent: str):
    """Get a workflow by intent."""
    return get_registry().get_by_intent(intent)


def list_workflows():
    """List all workflow IDs."""
    return get_registry().list_workflows()


def list_intents():
    """List all supported intents."""
    return get_registry().list_intents()


def normalize_intent(intent_str: str) -> str:
    """
    Normalize intent string to canonical form.

    Handles aliases and depth modifiers.

    Examples:
        "dump-full" -> ("dump", "full")
        "unpack" -> ("unpack", "standard")
        "inspect-quick" -> ("inspect", "quick")
    """
    # Split by '-' to handle depth modifier
    parts = intent_str.lower().strip().split('-')

    # Single word intent
    if len(parts) == 1:
        return parts[0]

    # Check if last part is a depth
    depth_str = parts[-1]
    intent_parts = parts[:-1]

    # Determine depth
    depth = Depth.STANDARD.value
    if depth_str in [d.value for d in Depth]:
        depth = depth_str
        intent_str = '-'.join(intent_parts)
    else:
        # No depth modifier, use default
        intent_str = '-'.join(parts)

    return intent_str


def parse_intent_with_depth(intent_str: str) -> tuple:
    """
    Parse intent string into (intent, depth) tuple.

    Examples:
        "dump-full" -> ("dump", "full")
        "unpack" -> ("unpack", "standard")
        "inspect-quick" -> ("inspect", "quick")
    """
    parts = intent_str.lower().strip().split('-')

    # Check if last part is a depth
    if len(parts) >= 2:
        depth_str = parts[-1]
        if depth_str in [d.value for d in Depth]:
            return ('-'.join(parts[:-1]), depth_str)

    # Default depth
    return (intent_str.lower().strip(), Depth.STANDARD.value)


def get_capabilities_for_workflow(workflow_id: str, depth: str = None):
    """
    Get list of capabilities required for a workflow at given depth.

    Returns list of capability IDs.
    """
    workflow = get_workflow(workflow_id)
    if not workflow:
        return []

    # Use default depth if not specified
    if depth is None:
        depth = workflow.default_depth

    if isinstance(depth, str):
        depth = Depth(depth)

    return workflow.get_capabilities_for_depth(depth)


def validate_workflow(workflow_id: str) -> dict:
    """
    Validate a workflow definition.

    Returns dict with validation results:
        - valid: bool
        - errors: list of error messages
        - warnings: list of warning messages
    """
    workflow = get_workflow(workflow_id)
    if not workflow:
        return {
            "valid": False,
            "errors": [f"Workflow {workflow_id} not found"],
            "warnings": []
        }

    errors = []
    warnings = []

    # Check entry node exists
    if not workflow.get_entry_node():
        errors.append("Missing entry node")

    # Check terminal nodes exist
    for terminal in workflow.terminal_nodes:
        if not workflow.get_node(terminal):
            errors.append(f"Terminal node {terminal} not found")

    # Check dependencies exist
    for node in workflow.nodes:
        for dep in node.dependencies:
            if not workflow.get_node(dep):
                errors.append(f"Node {node.node_id} has missing dependency {dep}")

    # Check for cycles (simple check)
    visited = set()
    path = set()

    def has_cycle(node_id: str) -> bool:
        if node_id in path:
            return True
        if node_id in visited:
            return False
        visited.add(node_id)
        path.add(node_id)
        node = workflow.get_node(node_id)
        if node:
            for dep in node.dependencies:
                if has_cycle(dep):
                    return True
        path.remove(node_id)
        return False

    for node in workflow.nodes:
        if has_cycle(node.node_id):
            errors.append(f"Cycle detected involving node {node.node_id}")

    # Check capabilities exist in registry
    # (This would require importing the capability registry)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
