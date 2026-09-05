"""
Complexity Scoring for IOS REVERSE KAISER.

This module handles:
- Complexity factor calculation
- Orchestration tier determination
- Agent selection
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Set, Optional


class OrchestrationTier(Enum):
    """Orchestration tiers based on complexity."""
    SIMPLE = "simple"      # Single executor
    MODERATE = "moderate"  # Executor + validator
    COMPLEX = "complex"    # Planner + specialists + validator
    FULL = "full"          # Planner + specialists + validator + auditor + reporter


# Tier boundaries
TIER_BOUNDARIES = {
    OrchestrationTier.SIMPLE: (0, 10),
    OrchestrationTier.MODERATE: (11, 25),
    OrchestrationTier.COMPLEX: (26, 50),
    OrchestrationTier.FULL: (51, float('inf')),
}


# Agent roles per tier
TIER_AGENTS = {
    OrchestrationTier.SIMPLE: ["executor"],
    OrchestrationTier.MODERATE: ["executor", "evidence-validator"],
    OrchestrationTier.COMPLEX: ["planner", "artifact-analyst", "binary-analyst",
                                "network-analyst", "objc-swift-analyst", "evidence-validator"],
    OrchestrationTier.FULL: ["planner", "artifact-analyst", "binary-analyst",
                            "network-analyst", "objc-swift-analyst", "crypto-analyst",
                            "evidence-validator", "coverage-auditor", "reporter"],
}


@dataclass
class ComplexityFactors:
    """Complexity factors for scoring."""
    artifact_count: int = 0
    depth_multiplier: float = 1.0
    domains: List[str] = field(default_factory=list)
    binary_count: int = 0
    decompilation_needed: bool = False
    xref_analysis: bool = False
    callflow_needed: bool = False
    runtime_needed: bool = False
    coverage_audit: bool = False


@dataclass
class ComplexityScore:
    """Result of complexity scoring."""
    total: float
    tier: OrchestrationTier
    agents: List[str]
    factors: ComplexityFactors
    breakdown: dict = field(default_factory=dict)


class ComplexityScorer:
    """
    Calculates workflow complexity and determines orchestration tier.

    Complexity factors:
    - artifact_count: Number of artifacts to analyze (1.0 each)
    - depth_multiplier: 1.0 (quick), 2.0 (standard), 3.0 (deep), 5.0 (full)
    - domains: Number of analysis domains (1.5 each)
    - binary_count: Number of embedded binaries (1.0 each)
    - decompilation_needed: Requires decompilation (+3.0)
    - xref_analysis: Requires cross-reference analysis (+2.0)
    - callflow_needed: Requires call flow reconstruction (+2.5)
    - runtime_needed: Requires runtime instrumentation (+3.0)
    - coverage_audit: Requires full coverage audit (+2.0)
    """

    # Factor weights
    WEIGHTS = {
        "artifact_count": 1.0,
        "domains": 1.5,
        "binary_count": 1.0,
        "decompilation_needed": 3.0,
        "xref_analysis": 2.0,
        "callflow_needed": 2.5,
        "runtime_needed": 3.0,
        "coverage_audit": 2.0,
    }

    def __init__(self):
        self._tier_boundaries = TIER_BOUNDARIES
        self._tier_agents = TIER_AGENTS

    def calculate(self, factors: ComplexityFactors) -> ComplexityScore:
        """
        Calculate complexity score from factors.

        Args:
            factors: Complexity factors

        Returns:
            ComplexityScore with total, tier, and agents
        """
        breakdown = {}

        # Artifact count
        artifact_score = factors.artifact_count * self.WEIGHTS["artifact_count"]
        breakdown["artifact_count"] = artifact_score

        # Depth multiplier
        depth_score = factors.depth_multiplier - 1.0  # Base is 1.0
        breakdown["depth"] = depth_score * 10  # Scale up

        # Domains
        domain_score = len(factors.domains) * self.WEIGHTS["domains"]
        breakdown["domains"] = domain_score

        # Binary count
        binary_score = factors.binary_count * self.WEIGHTS["binary_count"]
        breakdown["binary_count"] = binary_score

        # Boolean factors
        if factors.decompilation_needed:
            breakdown["decompilation"] = self.WEIGHTS["decompilation_needed"]
        else:
            breakdown["decompilation"] = 0

        if factors.xref_analysis:
            breakdown["xref_analysis"] = self.WEIGHTS["xref_analysis"]
        else:
            breakdown["xref_analysis"] = 0

        if factors.callflow_needed:
            breakdown["callflow"] = self.WEIGHTS["callflow_needed"]
        else:
            breakdown["callflow"] = 0

        if factors.runtime_needed:
            breakdown["runtime"] = self.WEIGHTS["runtime_needed"]
        else:
            breakdown["runtime"] = 0

        if factors.coverage_audit:
            breakdown["coverage_audit"] = self.WEIGHTS["coverage_audit"]
        else:
            breakdown["coverage_audit"] = 0

        # Total
        total = sum(breakdown.values())

        # Determine tier
        tier = self._determine_tier(total)

        # Get agents for tier
        agents = self._tier_agents.get(tier, ["executor"])

        return ComplexityScore(
            total=total,
            tier=tier,
            agents=agents,
            factors=factors,
            breakdown=breakdown
        )

    def calculate_from_params(
        self,
        artifact_count: int = 0,
        depth_multiplier: float = 1.0,
        domains: List[str] = None,
        binary_count: int = 0,
        decompilation_needed: bool = False,
        xref_analysis: bool = False,
        callflow_needed: bool = False,
        runtime_needed: bool = False,
        coverage_audit: bool = False
    ) -> ComplexityScore:
        """Convenience method to calculate from parameters."""
        factors = ComplexityFactors(
            artifact_count=artifact_count,
            depth_multiplier=depth_multiplier,
            domains=domains or [],
            binary_count=binary_count,
            decompilation_needed=decompilation_needed,
            xref_analysis=xref_analysis,
            callflow_needed=callflow_needed,
            runtime_needed=runtime_needed,
            coverage_audit=coverage_audit
        )
        return self.calculate(factors)

    def _determine_tier(self, score: float) -> OrchestrationTier:
        """Determine orchestration tier from score."""
        for tier, (min_score, max_score) in self._tier_boundaries.items():
            if min_score <= score <= max_score:
                return tier
        return OrchestrationTier.FULL

    def get_tier_description(self, tier: OrchestrationTier) -> str:
        """Get human-readable description of tier."""
        descriptions = {
            OrchestrationTier.SIMPLE: "Single executor - minimal overhead",
            OrchestrationTier.MODERATE: "Executor + validator - basic validation",
            OrchestrationTier.COMPLEX: "Planner + specialists + validator - deep analysis",
            OrchestrationTier.FULL: "Full team - complete coverage and reporting",
        }
        return descriptions.get(tier, "Unknown")

    def estimate_agents(self, tier: OrchestrationTier) -> List[str]:
        """Get list of agent roles for a tier."""
        return self._tier_agents.get(tier, ["executor"])
