"""
Capability Registry for IOS REVERSE KAISER.

This module defines the 31 capabilities across 12 domains.
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Any
from enum import Enum


class CapabilityDomain(Enum):
    """Capability domains."""
    FOUNDATION = "foundation"
    MACHO = "macho"
    BINARY = "binary"
    OBJC = "objc"
    SWIFT = "swift"
    FRAMEWORK = "framework"
    ARCHITECTURE = "architecture"
    NETWORK = "network"
    CALLFLOW = "callflow"
    CRYPTO = "crypto"
    ANTI_ANALYSIS = "anti-analysis"
    ABSTRACTION = "abstraction"
    REPORTING = "reporting"


@dataclass
class Capability:
    """An atomic capability."""
    id: str
    name: str
    description: str
    domain: CapabilityDomain
    version: str = "1.0.0"

    # Inputs
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)

    # Outputs
    output_types: List[str] = field(default_factory=list)
    output_artifacts: List[str] = field(default_factory=list)

    # Intent mapping
    intents: List[str] = field(default_factory=list)

    # Depth profiles
    depth_coverage: Dict[str, str] = field(default_factory=dict)

    # Dependencies
    dependencies: List[str] = field(default_factory=list)

    # Tool requirements
    required_tools: List[str] = field(default_factory=list)
    optional_tools: List[str] = field(default_factory=list)

    # Provenance
    provenance_required: bool = True

    def supports_depth(self, depth: str) -> bool:
        """Check if capability supports a depth."""
        return depth in self.depth_coverage

    def get_tool_tier(self, depth: str) -> int:
        """Get recommended tool tier for depth."""
        coverage = self.depth_coverage.get(depth, "minimal")
        tiers = {"minimal": 1, "normal": 1, "extended": 2, "complete": 3}
        return tiers.get(coverage, 1)


class CapabilityRegistry:
    """
    Registry of all 31 capabilities across 12 domains.

    Domains:
    1. Foundation (6) - IPA handling, bundle analysis
    2. Mach-O Analysis (3) - Binary structure
    3. Binary Analysis (4) - Imports, exports, symbols, strings
    4. Metadata ObjC (2) - Objective-C metadata
    5. Metadata Swift (2) - Swift metadata
    6. Framework/Dylib/Extension (3) - Component inventory
    7. Architecture (1) - Architecture discovery
    8. Network Analysis (3) - Network patterns
    9. Callflow (1) - Call flow reconstruction
    10. Crypto (1) - Crypto identification
    11. Anti-Analysis (1) - Anti-RE detection
    12. Abstraction (1) - Runtime abstraction
    13. Reporting (3) - Reporting and auditing

    Total: 31 capabilities
    """

    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}
        self._intent_map: Dict[str, List[str]] = {}
        self._domain_map: Dict[CapabilityDomain, List[str]] = {}
        self._register_all()

    def _register_all(self) -> None:
        """Register all 31 capabilities."""
        # Foundation (6)
        self._register_foundation()

        # Mach-O Analysis (3)
        self._register_macho()

        # Binary Analysis (4)
        self._register_binary()

        # Metadata ObjC/Swift (4)
        self._register_metadata()

        # Framework/Dylib/Extension (3)
        self._register_framework()

        # Architecture (1)
        self._register_architecture()

        # Network Analysis (3)
        self._register_network()

        # Callflow (1)
        self._register_callflow()

        # Crypto (1)
        self._register_crypto()

        # Anti-Analysis (1)
        self._register_anti_analysis()

        # Abstraction (1)
        self._register_abstraction()

        # Reporting (3)
        self._register_reporting()

    def _register(self, cap: Capability) -> None:
        """Register a capability."""
        self._capabilities[cap.id] = cap

        # Update intent map
        for intent in cap.intents:
            if intent not in self._intent_map:
                self._intent_map[intent] = []
            self._intent_map[intent].append(cap.id)

        # Update domain map
        if cap.domain not in self._domain_map:
            self._domain_map[cap.domain] = []
        self._domain_map[cap.domain].append(cap.id)

    def _register_foundation(self) -> None:
        """Register foundation capabilities."""
        caps = [
            Capability(
                id="foundation.artifact_detect",
                name="Artifact Detection",
                description="Detect and classify input artifacts",
                domain=CapabilityDomain.FOUNDATION,
                required_inputs=["artifact_path"],
                output_types=["artifact_type"],
                intents=["inspect", "dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["file"],
            ),
            Capability(
                id="ipa.validate",
                name="IPA Validation",
                description="Validate IPA archive integrity",
                domain=CapabilityDomain.FOUNDATION,
                required_inputs=["ipa_path"],
                output_types=["validation_result"],
                intents=["unpack", "dump"],
                depth_coverage={"quick": "minimal", "standard": "normal"},
                required_tools=["unzip"],
            ),
            Capability(
                id="ipa.unpack",
                name="IPA Unpacking",
                description="Extract IPA contents",
                domain=CapabilityDomain.FOUNDATION,
                required_inputs=["ipa_path", "output_dir"],
                output_artifacts=["extracted_payload"],
                intents=["unpack", "dump"],
                depth_coverage={"quick": "normal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["unzip"],
            ),
            Capability(
                id="bundle.inventory",
                name="Bundle Inventory",
                description="Inventory bundle contents",
                domain=CapabilityDomain.FOUNDATION,
                required_inputs=["bundle_path"],
                output_types=["bundle_contents"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["find"],
            ),
            Capability(
                id="plist.extract",
                name="Plist Extraction",
                description="Extract and parse Info.plist",
                domain=CapabilityDomain.FOUNDATION,
                required_inputs=["plist_path"],
                output_types=["plist_data"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["plutil"],
            ),
            Capability(
                id="entitlements.extract",
                name="Entitlements Extraction",
                description="Extract code signing entitlements",
                domain=CapabilityDomain.FOUNDATION,
                required_inputs=["artifact_path"],
                output_types=["entitlements_data"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["codesign", "plutil"],
            ),
        ]
        for cap in caps:
            self._register(cap)

    def _register_macho(self) -> None:
        """Register Mach-O capabilities."""
        caps = [
            Capability(
                id="macho.basic",
                name="Basic Mach-O Analysis",
                description="Basic Mach-O structure analysis",
                domain=CapabilityDomain.MACHO,
                required_inputs=["macho_path"],
                output_types=["macho_info"],
                intents=["macho", "dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["file"],
            ),
            Capability(
                id="macho.slices",
                name="Mach-O Slice Analysis",
                description="Analyze fat binary slices",
                domain=CapabilityDomain.MACHO,
                required_inputs=["macho_path"],
                output_types=["slices_info"],
                intents=["macho", "dump"],
                depth_coverage={"standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["lipo"],
            ),
            Capability(
                id="macho.load_commands",
                name="Load Commands Analysis",
                description="Analyze Mach-O load commands",
                domain=CapabilityDomain.MACHO,
                required_inputs=["macho_path"],
                output_types=["load_commands"],
                intents=["macho", "dump"],
                depth_coverage={"standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["otool"],
            ),
        ]
        for cap in caps:
            self._register(cap)

    def _register_binary(self) -> None:
        """Register binary analysis capabilities."""
        caps = [
            Capability(
                id="binary.imports",
                name="Import Extraction",
                description="Extract imported symbols",
                domain=CapabilityDomain.BINARY,
                required_inputs=["binary_path"],
                output_types=["imports_list"],
                intents=["dump", "decompile"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["nm", "otool"],
            ),
            Capability(
                id="binary.exports",
                name="Export Extraction",
                description="Extract exported symbols",
                domain=CapabilityDomain.BINARY,
                required_inputs=["binary_path"],
                output_types=["exports_list"],
                intents=["dump", "decompile"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["nm"],
            ),
            Capability(
                id="binary.symbols",
                name="Symbol Extraction",
                description="Extract all symbols",
                domain=CapabilityDomain.BINARY,
                required_inputs=["binary_path"],
                output_types=["symbols_list"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["nm", "strings"],
            ),
            Capability(
                id="binary.strings",
                name="String Extraction",
                description="Extract string constants",
                domain=CapabilityDomain.BINARY,
                required_inputs=["binary_path"],
                output_types=["strings_list"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["strings"],
            ),
        ]
        for cap in caps:
            self._register(cap)

    def _register_metadata(self) -> None:
        """Register ObjC/Swift metadata capabilities."""
        caps = [
            Capability(
                id="objc.metadata",
                name="ObjC Metadata Extraction",
                description="Extract Objective-C class and method metadata",
                domain=CapabilityDomain.OBJC,
                required_inputs=["binary_path"],
                output_types=["objc_classes", "objc_methods"],
                intents=["objc", "dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended"},
                required_tools=["ipsw", "nm"],
            ),
            Capability(
                id="objc.deep_metadata",
                name="Deep ObjC Metadata",
                description="Deep Objective-C metadata extraction with selectors",
                domain=CapabilityDomain.OBJC,
                required_inputs=["binary_path"],
                output_types=["objc_classes", "objc_selectors", "objc_message_graph"],
                intents=["objc"],
                depth_coverage={"deep": "extended", "full": "complete"},
                required_tools=["ipsw", "nm", "strings"],
            ),
            Capability(
                id="swift.metadata",
                name="Swift Metadata Extraction",
                description="Extract Swift type and method metadata",
                domain=CapabilityDomain.SWIFT,
                required_inputs=["binary_path"],
                output_types=["swift_types", "swift_methods"],
                intents=["swift", "dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended"},
                required_tools=["ipsw", "nm"],
            ),
            Capability(
                id="swift.demangle",
                name="Swift Demangling",
                description="Demangle Swift symbols",
                domain=CapabilityDomain.SWIFT,
                required_inputs=["mangled_symbols"],
                output_types=["demangled_symbols"],
                intents=["swift", "dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended"},
                required_tools=["swift-demangle"],
            ),
        ]
        for cap in caps:
            self._register(cap)

    def _register_framework(self) -> None:
        """Register framework/dylib/extension capabilities."""
        caps = [
            Capability(
                id="framework.inventory",
                name="Framework Inventory",
                description="Inventory embedded frameworks",
                domain=CapabilityDomain.FRAMEWORK,
                required_inputs=["bundle_path"],
                output_types=["framework_list"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["find"],
            ),
            Capability(
                id="dylib.inventory",
                name="Dylib Inventory",
                description="Inventory embedded dylibs",
                domain=CapabilityDomain.FRAMEWORK,
                required_inputs=["bundle_path"],
                output_types=["dylib_list"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["find"],
            ),
            Capability(
                id="extension.inventory",
                name="Extension Inventory",
                description="Inventory app extensions",
                domain=CapabilityDomain.FRAMEWORK,
                required_inputs=["bundle_path"],
                output_types=["extension_list"],
                intents=["dump"],
                depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["find"],
            ),
        ]
        for cap in caps:
            self._register(cap)

    def _register_architecture(self) -> None:
        """Register architecture discovery capability."""
        self._register(Capability(
            id="architecture.discovery",
            name="Architecture Discovery",
            description="Discover supported CPU architectures",
            domain=CapabilityDomain.ARCHITECTURE,
            required_inputs=["macho_path"],
            output_types=["architecture_list"],
            intents=["macho", "dump"],
            depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended", "full": "complete"},
            required_tools=["lipo", "file"],
        ))

    def _register_network(self) -> None:
        """Register network analysis capabilities."""
        caps = [
            Capability(
                id="network.discovery",
                name="Network Discovery",
                description="Discover network-related strings and patterns",
                domain=CapabilityDomain.NETWORK,
                required_inputs=["binary_path"],
                output_types=["network_strings"],
                intents=["network"],
                depth_coverage={"quick": "minimal", "standard": "normal"},
                required_tools=["strings"],
            ),
            Capability(
                id="network.framework_detect",
                name="Network Framework Detection",
                description="Detect network framework usage",
                domain=CapabilityDomain.NETWORK,
                required_inputs=["binary_path"],
                output_types=["network_frameworks"],
                intents=["network"],
                depth_coverage={"standard": "normal", "deep": "extended"},
                required_tools=["strings", "otool"],
            ),
            Capability(
                id="network.endpoint_extract",
                name="Network Endpoint Extraction",
                description="Extract API endpoints and URLs",
                domain=CapabilityDomain.NETWORK,
                required_inputs=["strings_path"],
                output_types=["endpoints_list", "urls_list"],
                intents=["network"],
                depth_coverage={"standard": "normal", "deep": "extended", "full": "complete"},
                required_tools=["strings", "ipsw"],
            ),
        ]
        for cap in caps:
            self._register(cap)

    def _register_callflow(self) -> None:
        """Register callflow reconstruction capability."""
        self._register(Capability(
            id="callflow.reconstruct",
            name="Call Flow Reconstruction",
            description="Reconstruct call flows from UI to network",
            domain=CapabilityDomain.CALLFLOW,
            required_inputs=["binary_path", "class_dump_path"],
            output_types=["callflow_graph"],
            intents=["login-flow", "runtime"],
            depth_coverage={"standard": "normal", "deep": "extended"},
            required_tools=["ipsw", "Ghidra"],
        ))

    def _register_crypto(self) -> None:
        """Register crypto identification capability."""
        self._register(Capability(
            id="crypto.identify",
            name="Crypto Identification",
            description="Identify crypto algorithms and key handling",
            domain=CapabilityDomain.CRYPTO,
            required_inputs=["binary_path"],
            output_types=["crypto_usage"],
            intents=["crypto"],
            depth_coverage={"quick": "minimal", "standard": "normal", "deep": "extended"},
            required_tools=["strings", "nm"],
        ))

    def _register_anti_analysis(self) -> None:
        """Register anti-analysis detection capability."""
        self._register(Capability(
            id="anti_analysis.scan",
            name="Anti-Analysis Detection",
            description="Detect anti-RE protections",
            domain=CapabilityDomain.ANTI_ANALYSIS,
            required_inputs=["binary_path"],
            output_types=["protections_found"],
            intents=["anti-analysis"],
            depth_coverage={"quick": "minimal", "standard": "normal"},
            required_tools=["strings"],
        ))

    def _register_abstraction(self) -> None:
        """Register runtime abstraction capability."""
        self._register(Capability(
            id="runtime.abstract",
            name="Runtime Abstraction",
            description="Generate runtime instrumentation scripts",
            domain=CapabilityDomain.ABSTRACTION,
            required_inputs=["target_info"],
            output_artifacts=["frida_scripts"],
            intents=["runtime"],
            depth_coverage={"deep": "extended", "full": "complete"},
            required_tools=["Frida"],
        ))

    def _register_reporting(self) -> None:
        """Register reporting capabilities."""
        caps = [
            Capability(
                id="report.generate",
                name="Report Generation",
                description="Generate structured analysis report",
                domain=CapabilityDomain.REPORTING,
                required_inputs=["analysis_results"],
                output_artifacts=["analysis_report.md"],
                intents=["report"],
                depth_coverage={"standard": "normal", "deep": "extended", "full": "complete"},
            ),
            Capability(
                id="coverage.audit",
                name="Coverage Audit",
                description="Audit analysis coverage",
                domain=CapabilityDomain.REPORTING,
                required_inputs=["workflow_results"],
                output_types=["coverage_report"],
                intents=["dump", "full"],
                depth_coverage={"full": "complete"},
            ),
            Capability(
                id="evidence.validate",
                name="Evidence Validation",
                description="Validate claims against evidence",
                domain=CapabilityDomain.REPORTING,
                required_inputs=["claims", "evidence"],
                output_types=["validation_results"],
                intents=["dump", "full"],
                depth_coverage={"standard": "normal", "deep": "extended", "full": "complete"},
            ),
        ]
        for cap in caps:
            self._register(cap)

    def get(self, capability_id: str) -> Optional[Capability]:
        """Get a capability by ID."""
        return self._capabilities.get(capability_id)

    def get_for_intent(self, intent: str) -> List[Capability]:
        """Get all capabilities for an intent."""
        cap_ids = self._intent_map.get(intent, [])
        return [self._capabilities[cid] for cid in cap_ids if cid in self._capabilities]

    def get_for_domain(self, domain: CapabilityDomain) -> List[Capability]:
        """Get all capabilities in a domain."""
        cap_ids = self._domain_map.get(domain, [])
        return [self._capabilities[cid] for cid in cap_ids if cid in self._capabilities]

    def list_all(self) -> List[Capability]:
        """List all capabilities."""
        return list(self._capabilities.values())

    def list_ids(self) -> List[str]:
        """List all capability IDs."""
        return list(self._capabilities.keys())

    def get_by_depth(self, intent: str, depth: str) -> List[Capability]:
        """Get capabilities supporting an intent at a specific depth."""
        caps = self.get_for_intent(intent)
        return [c for c in caps if c.supports_depth(depth)]
