"""
Capabilities module for IOS REVERSE KAISER.
"""

from .base import CapabilityExecutor, CapabilityResult, CapabilityError
from .foundation import (
    ArtifactDetectCapability,
    IpaValidateCapability,
    IpaUnpackCapability,
    BundleInventoryCapability,
    PlistExtractCapability,
    EntitlementsExtractCapability,
)
from .macho_binary import (
    MachoBasicCapability,
    MachoSlicesCapability,
    MachoLoadCommandsCapability,
    BinaryImportsCapability,
    BinaryExportsCapability,
    BinarySymbolsCapability,
    BinaryStringsCapability,
)
from .objc_metadata import (
    ObjCMetadataCapability,
    ObjCDeepMetadataCapability,
)
from .swift_metadata import (
    SwiftMetadataCapability,
    SwiftDemangleCapability,
)
from .framework_inventory import FrameworkInventoryCapability
from .dylib_inventory import DylibInventoryCapability
from .extension_inventory import ExtensionInventoryCapability
from .component_graph import ComponentGraphCapability
from .network_framework_detection import NetworkFrameworkDetectionCapability
from .network_endpoint_discovery import NetworkEndpointDiscoveryCapability
from .architecture_detection import ArchitectureDetectionCapability
from .callflow_reconstruction import CallflowReconstructCapability
from .crypto_detection import CryptoDetectionCapability
from .anti_analysis_detection import AntiAnalysisDetectionCapability
from .coverage_auditor import CoverageAuditorCapability

__all__ = [
    "CapabilityExecutor",
    "CapabilityResult",
    "CapabilityError",
    # Foundation capabilities (P04.1)
    "ArtifactDetectCapability",
    "IpaValidateCapability",
    "IpaUnpackCapability",
    "BundleInventoryCapability",
    "PlistExtractCapability",
    "EntitlementsExtractCapability",
    # Mach-O/Binary capabilities (P04.2)
    "MachoBasicCapability",
    "MachoSlicesCapability",
    "MachoLoadCommandsCapability",
    "BinaryImportsCapability",
    "BinaryExportsCapability",
    "BinarySymbolsCapability",
    "BinaryStringsCapability",
    # Objective-C capabilities (P04.3)
    "ObjCMetadataCapability",
    "ObjCDeepMetadataCapability",
    # Swift capabilities (P04.3)
    "SwiftMetadataCapability",
    "SwiftDemangleCapability",
    # Component inventory capabilities (P04.4)
    "FrameworkInventoryCapability",
    "DylibInventoryCapability",
    "ExtensionInventoryCapability",
    "ComponentGraphCapability",
    # Network capabilities (P04.5)
    "NetworkFrameworkDetectionCapability",
    "NetworkEndpointDiscoveryCapability",
    # Architecture capabilities (P04.5)
    "ArchitectureDetectionCapability",
    # Callflow capabilities (P04.5)
    "CallflowReconstructCapability",
    # Crypto capabilities (P04.6)
    "CryptoDetectionCapability",
    # Anti-analysis capabilities (P04.6)
    "AntiAnalysisDetectionCapability",
    # Coverage capabilities (P04.7)
    "CoverageAuditorCapability",
]
