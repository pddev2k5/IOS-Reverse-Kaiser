"""
Decompiler Provider Abstraction for IOS REVERSE KAISER.

Provides unified interface over IDA, Ghidra, and rizin for decompilation.

Maturity Level: L1 (Contract + Provider selection)
Target Level: L3 (Full provider integration)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from enum import Enum

from ios_reverse.adapters.contract import (
    ToolAvailability,
    FailureClassification,
    AdapterExecutionResult,
)


class DecompilerProvider(str, Enum):
    """Available decompiler providers."""
    IDA = "ida"
    GHIDRA = "ghidra"
    RIZIN = "rizin"
    NONE = "none"


@dataclass
class DecompiledFunction:
    """Normalized decompiled function."""
    address: int
    name: str
    signature: str
    pseudocode: str
    warnings: List[str] = field(default_factory=list)
    provider: DecompilerProvider = DecompilerProvider.NONE
    quality: str = "unknown"  # high, medium, low, unknown


@dataclass
class FunctionInfo:
    """Function metadata."""
    address: int
    name: str
    size: int
    cc: int = 0  # Cyclomatic complexity
    callers: List[int] = field(default_factory=list)
    callees: List[int] = field(default_factory=list)


@dataclass
class XrefInfo:
    """Cross-reference information."""
    from_addr: int
    to_addr: int
    type: str  # code, data, etc.


class DecompilerProviderContract(ABC):
    """
    Abstract decompiler provider contract.

    All decompiler providers must implement this interface.
    """

    @property
    @abstractmethod
    def provider_id(self) -> DecompilerProvider:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        pass

    @abstractmethod
    def availability(self) -> ToolAvailability:
        """Check provider availability."""
        pass

    @abstractmethod
    def supported_architectures(self) -> Set[str]:
        """Architectures this provider supports."""
        pass

    @abstractmethod
    def decompile_function(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """
        Decompile a single function.

        Args:
            binary_path: Path to binary
            address: Function address

        Returns:
            AdapterExecutionResult with DecompiledFunction in normalized_output
        """
        pass

    @abstractmethod
    def list_functions(
        self,
        binary_path: str
    ) -> AdapterExecutionResult:
        """
        List all functions.

        Returns:
            AdapterExecutionResult with list of FunctionInfo
        """
        pass

    @abstractmethod
    def get_function_info(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """
        Get function metadata.

        Returns:
            AdapterExecutionResult with FunctionInfo
        """
        pass

    @abstractmethod
    def get_xrefs(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """
        Get cross-references to/from address.

        Returns:
            AdapterExecutionResult with list of XrefInfo
        """
        pass

    @abstractmethod
    def get_callers(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """
        Get functions that call this function.

        Returns:
            AdapterExecutionResult with list of caller addresses
        """
        pass

    @abstractmethod
    def get_callees(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """
        Get functions called by this function.

        Returns:
            AdapterExecutionResult with list of callee addresses
        """
        pass

    @abstractmethod
    def get_strings(
        self,
        binary_path: str
    ) -> AdapterExecutionResult:
        """
        Get strings from binary.

        Returns:
            AdapterExecutionResult with list of strings
        """
        pass


class DecompilerManager:
    """
    Unified decompiler manager.

    Selects best available provider and delegates calls.
    """

    def __init__(self):
        self._providers: Dict[DecompilerProvider, DecompilerProviderContract] = {}
        self._selected_provider: Optional[DecompilerProvider] = None

    def register_provider(
        self,
        provider: DecompilerProvider,
        adapter: DecompilerProviderContract
    ):
        """Register a decompiler provider."""
        self._providers[provider] = adapter

    def select_best_provider(self) -> Optional[DecompilerProvider]:
        """
        Select best available provider.

        Priority: IDA > Ghidra > rizin
        """
        # Priority order
        priority = [
            DecompilerProvider.IDA,
            DecompilerProvider.GHIDRA,
            DecompilerProvider.RIZIN,
        ]

        for provider_id in priority:
            if provider_id in self._providers:
                adapter = self._providers[provider_id]
                if adapter.availability() == ToolAvailability.AVAILABLE:
                    self._selected_provider = provider_id
                    return provider_id

        return None

    def get_provider(self) -> Optional[DecompilerProvider]:
        """Get selected provider."""
        return self._selected_provider

    def decompile_function(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """Decompile via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.decompile_function(binary_path, address)

    def list_functions(self, binary_path: str) -> AdapterExecutionResult:
        """List functions via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.list_functions(binary_path)

    def get_function_info(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """Get function info via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.get_function_info(binary_path, address)

    def get_xrefs(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """Get xrefs via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.get_xrefs(binary_path, address)

    def get_callers(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """Get callers via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.get_callers(binary_path, address)

    def get_callees(
        self,
        binary_path: str,
        address: int
    ) -> AdapterExecutionResult:
        """Get callees via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.get_callees(binary_path, address)

    def get_strings(self, binary_path: str) -> AdapterExecutionResult:
        """Get strings via selected provider."""
        if not self._selected_provider:
            return AdapterExecutionResult(
                success=False,
                error="No decompiler provider available",
                failure_classification=FailureClassification.TOOL_NOT_FOUND,
            )

        adapter = self._providers[self._selected_provider]
        return adapter.get_strings(binary_path)

    def provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {}
        for provider_id, adapter in self._providers.items():
            status[provider_id.value] = {
                "available": adapter.availability() == ToolAvailability.AVAILABLE,
                "provider_name": adapter.provider_name,
            }
        status["selected"] = self._selected_provider.value if self._selected_provider else None
        return status
