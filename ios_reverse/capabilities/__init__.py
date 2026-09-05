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
# v0.2.0 Deep Analysis Capabilities
from .ida_analysis import IDAAnalysisCapability, IDATargetVerificationCapability
from .decompiler import DecompilerCapability, XrefAnalysisCapability
from .runtime import RuntimeAnalysisCapability, RuntimeSessionCapability
from .static_analysis import (
    SDKFingerprintingCapability,
    SecretScanningCapability,
    KeychainAnalysisCapability,
    JailbreakDetectionCapability,
    ObfuscationDetectionCapability,
)

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
    # v0.2.0 IDA/MCP capabilities (P14)
    "IDAAnalysisCapability",
    "IDATargetVerificationCapability",
    # v0.2.0 Decompiler capabilities (P15)
    "DecompilerCapability",
    "XrefAnalysisCapability",
    # v0.2.0 Runtime capabilities (P17)
    "RuntimeAnalysisCapability",
    "RuntimeSessionCapability",
    # v0.2.0 Static Analysis capabilities (P16)
    "SDKFingerprintingCapability",
    "SecretScanningCapability",
    "KeychainAnalysisCapability",
    "JailbreakDetectionCapability",
    "ObfuscationDetectionCapability",
]
