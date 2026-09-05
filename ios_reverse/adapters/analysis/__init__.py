"""
Analysis adapters for IOS REVERSE KAISER.

Provides adapters for network, architecture, callflow, crypto, and anti-analysis analysis.
"""

from .network_adapter import NetworkAnalysisAdapter
from .architecture_adapter import ArchitectureAnalysisAdapter
from .callflow_adapter import CallflowAnalysisAdapter
from .crypto_adapter import CryptoAnalysisAdapter
from .anti_analysis_adapter import AntiAnalysisAdapter

__all__ = [
    "NetworkAnalysisAdapter",
    "ArchitectureAnalysisAdapter",
    "CallflowAnalysisAdapter",
    "CryptoAnalysisAdapter",
    "AntiAnalysisAdapter",
]
