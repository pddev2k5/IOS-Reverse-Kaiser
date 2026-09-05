"""
Tool Adapters module for IOS REVERSE KAISER.
"""

from .base import (
    AdapterError,
    ToolUnavailableError,
    ToolExecutionError,
    VersionError,
    AdapterResult,
    ToolInfo,
    ToolAdapter,
    SubprocessAdapter,
    FallbackAdapter,
)

from .contract import (
    ToolAvailability,
    ToolRole,
    FailureClassification,
    ExecutionMode,
    ToolMetadata,
    DependencyInfo,
    AdapterHealth,
    AdapterExecutionResult,
    ToolAdapterContract,
    SubprocessAdapterContract,
    FallbackChain,
    is_retryable_failure,
)

from .selector import (
    ToolSelector,
    ToolHealthService,
    SelectionReason,
    SelectionResult,
    get_tool_selector,
    get_health_service,
    configure_tool_system,
)

__all__ = [
    # Base
    "AdapterError",
    "ToolUnavailableError",
    "ToolExecutionError",
    "VersionError",
    "AdapterResult",
    "ToolInfo",
    "ToolAdapter",
    "SubprocessAdapter",
    "FallbackAdapter",

    # Contract
    "ToolAvailability",
    "ToolRole",
    "FailureClassification",
    "ExecutionMode",
    "ToolMetadata",
    "DependencyInfo",
    "AdapterHealth",
    "AdapterExecutionResult",
    "ToolAdapterContract",
    "SubprocessAdapterContract",
    "FallbackChain",
    "is_retryable_failure",

    # Selector
    "ToolSelector",
    "ToolHealthService",
    "SelectionReason",
    "SelectionResult",
    "get_tool_selector",
    "get_health_service",
    "configure_tool_system",
]
