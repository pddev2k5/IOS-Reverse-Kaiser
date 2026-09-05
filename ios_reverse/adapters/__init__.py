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

# Deep analysis adapters
from .ida import (
    IDAMCPAdapter,
    IDATargetInfo,
    IDAFunction,
    IDAXref,
    IDAString,
    IDAImport,
    IDAExport,
    IDAConnectionState,
)

from .ghidra import (
    GhidraHeadlessAdapter,
    GhidraFunction,
    GhidraXref,
    GhidraDecompileResult,
)

from .rizin import (
    RizinAdapter,
    RizinFunction,
    RizinXref,
    RizinImport,
    RizinExport,
)

from .runtime import (
    RuntimeProviderAdapter,
    RuntimeProvider,
    SessionState,
    RuntimeDevice,
    RuntimeProcess,
    RuntimeModule,
    RuntimeClass,
    RuntimeObservation,
)

from .decompiler import (
    DecompilerProvider,
    DecompilerProviderContract,
    DecompilerManager,
    DecompiledFunction,
    FunctionInfo,
    XrefInfo,
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

    # IDA adapter
    "IDAMCPAdapter",
    "IDATargetInfo",
    "IDAFunction",
    "IDAXref",
    "IDAString",
    "IDAImport",
    "IDAExport",
    "IDAConnectionState",

    # Ghidra adapter
    "GhidraHeadlessAdapter",
    "GhidraFunction",
    "GhidraXref",
    "GhidraDecompileResult",

    # Rizin adapter
    "RizinAdapter",
    "RizinFunction",
    "RizinXref",
    "RizinImport",
    "RizinExport",

    # Runtime adapter
    "RuntimeProviderAdapter",
    "RuntimeProvider",
    "SessionState",
    "RuntimeDevice",
    "RuntimeProcess",
    "RuntimeModule",
    "RuntimeClass",
    "RuntimeObservation",

    # Decompiler
    "DecompilerProvider",
    "DecompilerProviderContract",
    "DecompilerManager",
    "DecompiledFunction",
    "FunctionInfo",
    "XrefInfo",
]
