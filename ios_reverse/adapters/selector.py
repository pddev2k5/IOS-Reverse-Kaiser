"""
Tool Selector and Health Service for IOS REVERSE KAISER.

Provides centralized tool selection and health monitoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
import platform
import time
from pathlib import Path

from .contract import (
    ToolAdapterContract, ToolAvailability, ToolRole,
    AdapterHealth, DependencyInfo, FallbackChain,
    FailureClassification
)


@dataclass
class SelectionReason:
    """Explanation of tool selection."""
    selected_adapter: str
    fallback_chain: List[str]
    reason: str
    policy_used: str


@dataclass
class SelectionResult:
    """Result of tool selection."""
    adapter: Optional[ToolAdapterContract]
    fallback_chain: FallbackChain
    reason: SelectionReason
    available: bool


class ToolSelector:
    """
    Tool selector with explicit fallback chains.

    Given a capability, selects the best available adapter.
    """

    def __init__(self):
        self._chains: Dict[str, FallbackChain] = {}
        self._adapters: Dict[str, ToolAdapterContract] = {}

    def register(self, capability_id: str, adapter: ToolAdapterContract, role: ToolRole = ToolRole.OPTIONAL):
        """Register an adapter for a capability."""
        if capability_id not in self._chains:
            self._chains[capability_id] = FallbackChain()
        self._chains[capability_id].add(adapter, role)
        self._adapters[adapter.adapter_id] = adapter

    def select(
        self,
        capability_id: str,
        workflow_depth: str = "standard",
        platform_override: str = None,
        prior_failures: List[str] = None
    ) -> SelectionResult:
        """
        Select best available adapter for capability.

        Args:
            capability_id: Capability to select for
            workflow_depth: Workflow depth (basic, standard, deep)
            platform_override: Override platform detection
            prior_failures: Adapter IDs that recently failed

        Returns:
            SelectionResult with selected adapter and reasoning
        """
        if capability_id not in self._chains:
            return SelectionResult(
                adapter=None,
                fallback_chain=FallbackChain(),
                reason=SelectionReason(
                    selected_adapter="",
                    fallback_chain=[],
                    reason=f"No adapters registered for {capability_id}",
                    policy_used="none"
                ),
                available=False
            )

        chain = self._chains[capability_id]
        prior_failures = prior_failures or []

        # Apply prior failure filter
        if prior_failures:
            # Filter out recently failed adapters
            available_adapters = [
                (a, r) for a, r in chain.get_available()
                if a.adapter_id not in prior_failures
            ]
        else:
            available_adapters = chain.get_available()

        # Select based on role priority
        selected = None
        selected_role = None

        for role in [ToolRole.REQUIRED, ToolRole.OPTIONAL, ToolRole.FALLBACK]:
            for adapter, r in available_adapters:
                if r == role:
                    selected = adapter
                    selected_role = r
                    break
            if selected:
                break

        # Build reason
        all_adapters = [a.adapter_id for a, _ in chain._adapters]
        available_ids = [a.adapter_id for a, _ in available_adapters]

        if selected:
            reason = SelectionReason(
                selected_adapter=selected.adapter_id,
                fallback_chain=available_ids,
                reason=f"Selected {selected_role.value} adapter: {selected.adapter_id}",
                policy_used="role_priority_with_failure_filter"
            )
        else:
            reason = SelectionReason(
                selected_adapter="",
                fallback_chain=all_adapters,
                reason="No available adapters after failure filtering",
                policy_used="role_priority_with_failure_filter"
            )

        return SelectionResult(
            adapter=selected,
            fallback_chain=chain,
            reason=reason,
            available=selected is not None
        )

    def get_chain(self, capability_id: str) -> Optional[FallbackChain]:
        """Get fallback chain for capability."""
        return self._chains.get(capability_id)

    def explain(self, capability_id: str) -> Dict[str, Any]:
        """Explain selection for a capability."""
        if capability_id not in self._chains:
            return {"error": f"Unknown capability: {capability_id}"}

        chain = self._chains[capability_id]
        result = chain.explain()
        result["selection"] = self.select(capability_id).reason.__dict__
        return result


class ToolHealthService:
    """
    Centralized tool health monitoring.

    Caches health checks and provides unified reporting.
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        self._adapters: Dict[str, ToolAdapterContract] = {}
        self._health_cache: Dict[str, Tuple[AdapterHealth, float]] = {}
        self._cache_ttl = cache_ttl_seconds
        self._host_platform = platform.system().lower()

    def register(self, adapter: ToolAdapterContract):
        """Register an adapter for health monitoring."""
        self._adapters[adapter.adapter_id] = adapter

    def check_health(
        self,
        adapter_id: str,
        force: bool = False
    ) -> Optional[AdapterHealth]:
        """Check health of a specific adapter."""
        if adapter_id not in self._adapters:
            return None

        # Check cache
        if not force and adapter_id in self._health_cache:
            cached_health, cached_time = self._health_cache[adapter_id]
            if time.time() - cached_time < self._cache_ttl:
                return cached_health

        # Perform health check
        adapter = self._adapters[adapter_id]
        health = adapter.health_check()
        health.platform = self._host_platform

        # Cache result
        self._health_cache[adapter_id] = (health, time.time())

        return health

    def check_all(self, force: bool = False) -> List[AdapterHealth]:
        """Check health of all registered adapters."""
        results = []
        for adapter_id in self._adapters:
            health = self.check_health(adapter_id, force)
            if health:
                results.append(health)
        return results

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        health_list = self.check_all()

        by_availability = {
            "available": [],
            "unavailable": [],
            "degraded": [],
            "session_required": [],
            "other": []
        }

        for health in health_list:
            avail = health.availability.value
            if avail == "available":
                by_availability["available"].append(health)
            elif avail == "unavailable":
                by_availability["unavailable"].append(health)
            elif avail == "degraded":
                by_availability["degraded"].append(health)
            elif avail == "session_required":
                by_availability["session_required"].append(health)
            else:
                by_availability["other"].append(health)

        return {
            "platform": self._host_platform,
            "total_adapters": len(self._adapters),
            "health": health_list,
            "summary": {
                "available_count": len(by_availability["available"]),
                "unavailable_count": len(by_availability["unavailable"]),
                "degraded_count": len(by_availability["degraded"]),
                "session_required_count": len(by_availability["session_required"]),
            },
            "by_availability": {
                k: [
                    {"id": h.adapter_id, "tool": h.tool_name, "version": h.tool_version, "reason": h.reason}
                    for h in v
                ]
                for k, v in by_availability.items()
            },
            "capabilities": self._get_capability_matrix(health_list)
        }

    def _get_capability_matrix(self, health_list: List[AdapterHealth]) -> Dict[str, Any]:
        """Build capability availability matrix."""
        matrix = {}
        for health in health_list:
            for cap in health.capabilities:
                if cap not in matrix:
                    matrix[cap] = []
                matrix[cap].append({
                    "adapter_id": health.adapter_id,
                    "available": health.availability == ToolAvailability.AVAILABLE
                })
        return matrix

    def get_capability_status(
        self,
        capability_id: str,
        selector: ToolSelector
    ) -> Dict[str, Any]:
        """Get status for a specific capability."""
        chain = selector.get_chain(capability_id)
        if not chain:
            return {
                "capability": capability_id,
                "status": "no_adapters",
                "adapters": []
            }

        status = {
            "capability": capability_id,
            "status": "unavailable",
            "adapters": []
        }

        for adapter, role in chain._adapters:
            health = self.check_health(adapter.adapter_id)
            if health:
                status["adapters"].append({
                    "adapter_id": adapter.adapter_id,
                    "role": role.value,
                    "availability": health.availability.value,
                    "version": health.tool_version,
                    "reason": health.reason
                })
                if health.availability == ToolAvailability.AVAILABLE:
                    status["status"] = "available"

        return status

    def invalidate_cache(self, adapter_id: str = None):
        """Invalidate health cache."""
        if adapter_id:
            self._health_cache.pop(adapter_id, None)
        else:
            self._health_cache.clear()


# Global instances
_global_selector: Optional[ToolSelector] = None
_global_health_service: Optional[ToolHealthService] = None


def get_tool_selector() -> ToolSelector:
    """Get global tool selector."""
    global _global_selector
    if _global_selector is None:
        _global_selector = ToolSelector()
    return _global_selector


def get_health_service() -> ToolHealthService:
    """Get global health service."""
    global _global_health_service
    if _global_health_service is None:
        _global_health_service = ToolHealthService()
    return _global_health_service


def configure_tool_system(adapters: List[Tuple[str, ToolAdapterContract, ToolRole]]):
    """
    Configure global tool system.

    Args:
        adapters: List of (capability_id, adapter, role) tuples
    """
    selector = get_tool_selector()
    health = get_health_service()

    for capability_id, adapter, role in adapters:
        selector.register(capability_id, adapter, role)
        health.register(adapter)
