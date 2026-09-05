"""
IOS REVERSE KAISER
Production-quality iOS reverse-engineering framework.

This module provides:
- Command parsing and routing
- Workflow execution engine
- Capability registry
- Case workspace management
"""

__version__ = "0.2.0"
__author__ = "IOS REVERSE KAISER"

from .engine.intent import Intent, IntentResolver
from .engine.depth import Depth, DepthResolver
from .engine.complexity import ComplexityScorer, OrchestrationTier
from .engine.state import NodeState, WorkflowState
from .engine.workflow import WorkflowRegistry, Workflow
from .engine.executor import DAGExecutor

__all__ = [
    "Intent",
    "IntentResolver",
    "Depth",
    "DepthResolver",
    "ComplexityScorer",
    "OrchestrationTier",
    "NodeState",
    "WorkflowState",
    "WorkflowRegistry",
    "Workflow",
    "DAGExecutor",
]
