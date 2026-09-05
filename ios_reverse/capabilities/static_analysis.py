"""
Deep Static Analysis Capabilities for IOS REVERSE KAISER.

Provides SDK fingerprinting, secret scanning, keychain detection, and other
deep static analysis features.

Maturity Level: L1 (Pattern definitions)
Target Level: L2 (Implementation)
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from ios_reverse.capabilities.base import (
    CapabilityExecutor,
    CapabilityResult,
    Evidence,
    EvidenceType,
    EvidenceStrength,
)


class SecretRiskLevel(str, Enum):
    """Risk level for detected secrets."""
    CLIENT_SAFE = "client_safe"  # Public identifier, safe to use
    POTENTIALLY_SENSITIVE = "potentially_sensitive"  # Needs review
    UNKNOWN = "unknown"  # Cannot determine
    HIGH_RISK = "high_risk"  # Likely sensitive


@dataclass
class SDKFingerprint:
    """SDK fingerprint record."""
    name: str
    version: Optional[str]
    confidence: str  # high, medium, low
    indicators: List[str]


@dataclass
class SecretFinding:
    """Secret finding record."""
    category: str
    pattern: str
    value: str
    risk_level: SecretRiskLevel
    location: str
    context: Optional[str] = None


class SDKFingerprintingCapability(CapabilityExecutor):
    """
    SDK fingerprinting capability.

    Identifies third-party SDKs embedded in the application.
    """

    CAPABILITY_ID = "static.sdk_fingerprinting"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    def execute_capability(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """Execute SDK fingerprinting."""
        strings = inputs.get("strings", [])
        frameworks = inputs.get("frameworks", [])
        classes = inputs.get("classes", [])
        symbols = inputs.get("symbols", [])

        found_sdks: List[SDKFingerprint] = []

        for sdk_name, pattern in self.SDK_PATTERNS.items():
            score = 0
            indicators_found = []

            # Check framework
            if pattern.get("framework") and pattern["framework"] in frameworks:
                score += 4
                indicators_found.append(f"framework:{pattern['framework']}")

            # Check class prefixes
            for prefix in pattern.get("class_prefixes", []):
                for cls in classes:
                    if cls.startswith(prefix):
                        score += 2
                        indicators_found.append(f"class:{cls}")

            # Check strings
            for s in strings:
                for pattern_str in pattern.get("strings", []):
                    if pattern_str.lower() in s.lower():
                        score += 1
                        indicators_found.append(f"string:{s[:50]}")

            # Check symbols
            for sym in symbols:
                for pattern_sym in pattern.get("symbols", []):
                    if pattern_sym in sym:
                        score += 2
                        indicators_found.append(f"symbol:{sym}")

            if score >= 3:
                confidence = "high" if score >= 6 else "medium" if score >= 4 else "low"
                found_sdks.append(SDKFingerprint(
                    name=sdk_name,
                    version=None,
                    confidence=confidence,
                    indicators=indicators_found[:5],
                ))

        # Create evidence
        evidence_list = []
        for sdk in found_sdks:
            evidence_list.append(Evidence(
                evidence_id=f"sdk-{sdk.name.lower()}",
                evidence_type=EvidenceType.STRUCTURAL,
                strength=EvidenceStrength.CORRELATED,
                source_artifact="static_analysis",
                content={
                    "sdk_name": sdk.name,
                    "version": sdk.version,
                    "confidence": sdk.confidence,
                    "indicators": sdk.indicators,
                },
                capability_id=self.CAPABILITY_ID,
                metadata={"category": "sdk"},
            ))

        return CapabilityResult.from_evidence(
            evidence_list,
            metadata={
                "sdk_count": len(found_sdks),
                "sdks": [sdk.name for sdk in found_sdks],
            },
        )

    # Known SDK patterns
    SDK_PATTERNS = {
        "Alamofire": {
            "framework": "Alamofire.framework",
            "class_prefixes": ["AF", "Alamofire"],
            "strings": ["Alamofire", "alamofire"],
            "symbols": ["Alamofire", "_AF"],
        },
        "Firebase": {
            "framework": "Firebase.framework",
            "class_prefixes": ["FIR", "FIRO", "Firebase"],
            "strings": ["firebaseio.com", "firebaseapp.com", "GoogleService-Info"],
            "symbols": ["FIRApp", "FIRAuth"],
        },
        "GoogleSignIn": {
            "framework": "GoogleSignIn.framework",
            "class_prefixes": ["GID", "GoogleID"],
            "strings": ["googlesignin", "clientID"],
            "symbols": ["GIDSignIn", "GIDConfiguration"],
        },
        "GoogleMaps": {
            "framework": "GoogleMaps.framework",
            "class_prefixes": ["GMS", "GMSServices"],
            "strings": ["maps.googleapis.com", "GoogleMaps"],
            "symbols": ["GMSMapView", "GMSPlacesClient"],
        },
        "GoogleAnalytics": {
            "framework": None,
            "class_prefixes": ["GAITracker", "GAI"],
            "strings": ["google-analytics.com", "analytics"],
            "symbols": ["GAI", "GAITracker"],
        },
        "Facebook": {
            "framework": "FBSDK",
            "class_prefixes": ["FB", "FBSDK"],
            "strings": ["facebook", "fb://"],
            "symbols": ["FBSDK", "FBAppEvents"],
        },
        "Stripe": {
            "framework": "Stripe.framework",
            "class_prefixes": ["STP", "Stripe"],
            "strings": ["Stripe", "pk_live", "pk_test"],
            "symbols": ["STPPayment", "StripeAPI"],
        },
        "Braintree": {
            "framework": "Braintree",
            "class_prefixes": ["BT", "Braintree"],
            "strings": ["braintree", "Bt"],
            "symbols": ["BT", "Braintree"],
        },
        "Amplitude": {
            "framework": None,
            "class_prefixes": ["AMP", "Amplitude"],
            "strings": ["amplitude", "api.amplitude.com"],
            "symbols": ["Amplitude", "_AMP"],
        },
        "Mixpanel": {
            "framework": None,
            "class_prefixes": ["MXP", "Mixpanel"],
            "strings": ["mixpanel", "api.mixpanel.com"],
            "symbols": ["Mixpanel", "_MXP"],
        },
        "Segment": {
            "framework": None,
            "class_prefixes": ["SEG", "Segment"],
            "strings": ["segment", "api.segment.io"],
            "symbols": ["Segment", "Analytics"],
        },
        "Adjust": {
            "framework": None,
            "class_prefixes": ["ADJ", "Adjust"],
            "strings": ["adjust", "adj"],
            "symbols": ["Adjust", "_ADJ"],
        },
        "SDWebImage": {
            "framework": None,
            "class_prefixes": ["SD", "SDWebImage"],
            "strings": ["sdwebimage", "SDWebImage"],
            "symbols": ["SDWebImage", "_SD"],
        },
        "Kingfisher": {
            "framework": None,
            "class_prefixes": ["KF", "Kingfisher"],
            "strings": ["kingfisher"],
            "symbols": ["Kingfisher", "_KF"],
        },
        "Realm": {
            "framework": "Realm.framework",
            "class_prefixes": ["RLM", "Realm"],
            "strings": ["realm", "Realm"],
            "symbols": ["RLMObject", "Realm"],
        },
        "SQLCipher": {
            "framework": None,
            "class_prefixes": ["SQLite"],
            "strings": ["sqlcipher", "PRAGMA key"],
            "symbols": ["SQLite", "sqlcipher"],
        },
        "TrustKit": {
            "framework": None,
            "class_prefixes": ["TSK", "TrustKit"],
            "strings": ["trustkit", "TrustKit"],
            "symbols": ["TrustKit", "_TSK"],
        },
        "SAMKeychain": {
            "framework": None,
            "class_prefixes": ["SAM", "SAMKeychain"],
            "strings": ["SAMKeychain", "keychain"],
            "symbols": ["SAMKeychain", "_SAM"],
        },
        "PubNub": {
            "framework": None,
            "class_prefixes": ["PN", "PubNub"],
            "strings": ["pubnub", "pnconf"],
            "symbols": ["PubNub", "_PN"],
        },
        "Crashlytics": {
            "framework": None,
            "class_prefixes": ["CLS", "Crashlytics"],
            "strings": ["crashlytics", "fabric"],
            "symbols": ["Crashlytics", "CLS"],
        },
        "Bugly": {
            "framework": None,
            "class_prefixes": ["Bugly"],
            "strings": ["bugly", "bugly.qq.com"],
            "symbols": ["Bugly"],
        },
    }

    def __init__(self):
        super().__init__()

    def dependencies(self) -> List[str]:
        return ["bundle.inventory", "macho.strings", "macho.symbols"]

    def inputs(self) -> Dict[str, Any]:
        return {
            "strings_file": "Path to extracted strings",
            "classes_file": "Optional class dump",
            "framework_list": "List of embedded frameworks",
            "symbols_file": "Optional symbols file",
        }

    def outputs(self) -> Dict[str, Any]:
        return {
            "sdks": "List of SDKFingerprint records",
            "version_conflicts": "Potential version conflicts",
            "sdk_count": "Total SDK count",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Execute SDK fingerprinting."""
        strings = context.get("strings", [])
        frameworks = context.get("frameworks", [])
        classes = context.get("classes", [])
        symbols = context.get("symbols", [])

        if not strings and not frameworks and not classes and not symbols:
            return CapabilityResult.failure("exec-no-data", "NO_DATA", "No analysis data provided")

        found_sdks = []

        # Check each SDK pattern
        for sdk_name, patterns in self.SDK_PATTERNS.items():
            indicators = []
            confidence = "low"

            # Check framework presence
            if patterns.get("framework") and patterns["framework"] in frameworks:
                indicators.append(f"framework:{patterns['framework']}")
                confidence = "medium"

            # Check strings
            for pattern in patterns.get("strings", []):
                for s in strings:
                    if isinstance(s, dict):
                        s_value = s.get("value", "")
                    else:
                        s_value = str(s)
                    if pattern.lower() in s_value.lower():
                        indicators.append(f"string:{pattern}")
                        confidence = "medium"
                        break

            # Check class prefixes
            for prefix in patterns.get("class_prefixes", []):
                for cls in classes:
                    if isinstance(cls, str) and cls.startswith(prefix):
                        indicators.append(f"class:{prefix}")
                        if confidence == "medium":
                            confidence = "high"
                        break

            # Check symbols
            for pattern in patterns.get("symbols", []):
                for sym in symbols:
                    if isinstance(sym, dict):
                        sym_name = sym.get("name", "")
                    else:
                        sym_name = str(sym)
                    if pattern in sym_name:
                        indicators.append(f"symbol:{pattern}")
                        if confidence == "medium":
                            confidence = "high"
                        break

            # Extract version if present
            version = None
            version_pattern = r"(?:v|version)?[=:\s]*(\d+\.[\d.]+)"
            for indicator in indicators:
                if indicator.startswith("string:"):
                    match = re.search(version_pattern, indicator, re.IGNORECASE)
                    if match:
                        version = match.group(1)
                        break

            if indicators:
                found_sdks.append(SDKFingerprint(
                    name=sdk_name,
                    version=version,
                    confidence=confidence,
                    indicators=indicators,
                ))

        # Build evidence
        evidence_list = []
        for sdk in found_sdks:
            evidence_list.append(Evidence(
                evidence_id=f"sdk-{sdk.name.lower().replace(' ', '-')}",
                evidence_type=EvidenceType.STRING_HINT,
                strength=EvidenceStrength.STRING_HINT,
                source_artifact=context.get("artifact_path", "unknown"),
                content={
                    "type": "sdk_fingerprint",
                    "name": sdk.name,
                    "version": sdk.version,
                    "confidence": sdk.confidence,
                    "indicators": sdk.indicators,
                },
                capability_id=self.CAPABILITY_ID,
                metadata={"category": "sdk", "name": sdk.name},
            ))

        return CapabilityResult.from_evidence(
            evidence_list,
            metadata={
                "sdk_count": len(found_sdks),
                "sdks": [sdk.name for sdk in found_sdks],
            },
        )


class SecretScanningCapability(CapabilityExecutor):
    """
    Secret scanning capability.

    Detects potentially sensitive patterns in strings and binaries.
    """

    CAPABILITY_ID = "static.secret_scanning"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    # Secret patterns by category
    SECRET_PATTERNS = {
        "firebase_api_key": {
            "pattern": r"firebase.*\.com",
            "risk": SecretRiskLevel.POTENTIALLY_SENSITIVE,
            "category": "Firebase",
            "description": "Firebase/Google API endpoint",
        },
        "firebase_config": {
            "pattern": r"GoogleService-Info\.plist",
            "risk": SecretRiskLevel.POTENTIALLY_SENSITIVE,
            "category": "Firebase",
            "description": "Firebase configuration file reference",
        },
        "gcp_api_key": {
            "pattern": r"AIza[0-9A-Za-z_-]{35}",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "GCP",
            "description": "Google Cloud API key",
        },
        "gcp_oauth": {
            "pattern": r"[0-9]{12}-[a-z0-9]{32}\.apps\.googleusercontent\.com",
            "risk": SecretRiskLevel.POTENTIALLY_SENSITIVE,
            "category": "GCP",
            "description": "Google OAuth client ID",
        },
        "aws_access_key": {
            "pattern": r"(?i)(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "AWS",
            "description": "AWS access key ID",
        },
        "aws_secret_key": {
            "pattern": r"(?i)aws_secret_access_key",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "AWS",
            "description": "AWS secret key reference",
        },
        "stripe_key": {
            "pattern": r"sk_live_[0-9a-zA-Z]{24,}",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "Stripe",
            "description": "Stripe live secret key",
        },
        "stripe_test_key": {
            "pattern": r"sk_test_[0-9a-zA-Z]{24,}",
            "risk": SecretRiskLevel.POTENTIALLY_SENSITIVE,
            "category": "Stripe",
            "description": "Stripe test secret key",
        },
        "jwt_token": {
            "pattern": r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "JWT",
            "description": "JWT token pattern",
        },
        "private_key": {
            "pattern": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "PrivateKey",
            "description": "Private key header",
        },
        "generic_secret": {
            "pattern": r"(?i)(secret|password|passwd|pwd|apikey|api_key|auth_token|access_token)['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            "risk": SecretRiskLevel.UNKNOWN,
            "category": "Generic",
            "description": "Possible secret assignment",
        },
        "connection_string": {
            "pattern": r"(?i)(mongodb|mysql|postgres|redis|sqlserver):\/\/[^?\s]+",
            "risk": SecretRiskLevel.HIGH_RISK,
            "category": "ConnectionString",
            "description": "Database connection string",
        },
        "ip_address": {
            "pattern": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "risk": SecretRiskLevel.CLIENT_SAFE,
            "category": "Network",
            "description": "IP address",
        },
        "email": {
            "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "risk": SecretRiskLevel.CLIENT_SAFE,
            "category": "Contact",
            "description": "Email address",
        },
    }

    def __init__(self):
        super().__init__()

    def dependencies(self) -> List[str]:
        return ["macho.strings"]

    def inputs(self) -> Dict[str, Any]:
        return {
            "strings": "List of strings from binary",
            "strings_file": "Optional path to strings file",
            "include_client_safe": "Include client-safe findings (default: false)",
        }

    def outputs(self) -> Dict[str, Any]:
        return {
            "findings": "List of SecretFinding records",
            "by_category": "Findings grouped by category",
            "by_risk": "Findings grouped by risk level",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Execute secret scanning."""
        strings = context.get("strings", [])
        include_client_safe = context.get("include_client_safe", False)

        findings = []

        # Scan each string
        for s in strings:
            if isinstance(s, dict):
                value = s.get("value", "")
                address = s.get("address")
            else:
                value = str(s)
                address = None

            # Check against patterns
            for pattern_name, pattern_info in self.SECRET_PATTERNS.items():
                matches = re.findall(pattern_info["pattern"], value)
                if matches:
                    # Skip client-safe unless requested
                    if pattern_info["risk"] == SecretRiskLevel.CLIENT_SAFE and not include_client_safe:
                        continue

                    for match in matches:
                        findings.append(SecretFinding(
                            category=pattern_info["category"],
                            pattern=pattern_name,
                            value=value if len(value) <= 200 else value[:200] + "...",
                            risk_level=pattern_info["risk"],
                            location=f"address:{address}" if address else "unknown",
                            context=pattern_info.get("description", ""),
                        ))

        # Build evidence
        evidence_list = []
        for finding in findings:
            evidence_list.append(Evidence(
                evidence_id=f"secret-{finding.category.lower()}-{len(evidence_list)}",
                evidence_type=EvidenceType.STRING_HINT,
                strength=EvidenceStrength.STRING_HINT if finding.risk_level != SecretRiskLevel.HIGH_RISK else EvidenceStrength.VERIFIED,
                source_artifact=context.get("artifact_path", "unknown"),
                content={
                    "type": "secret_finding",
                    "category": finding.category,
                    "pattern": finding.pattern,
                    "value": finding.value,
                    "risk_level": finding.risk_level.value,
                    "location": finding.location,
                    "description": finding.context,
                },
                capability_id=self.CAPABILITY_ID,
                metadata={
                    "category": "secret",
                    "risk_level": finding.risk_level.value,
                },
            ))

        # Group by category
        by_category = {}
        for f in findings:
            if f.category not in by_category:
                by_category[f.category] = []
            by_category[f.category].append(f.pattern)

        # Group by risk
        by_risk = {}
        for f in findings:
            risk = f.risk_level.value
            if risk not in by_risk:
                by_risk[risk] = []
            by_risk[risk].append(f.pattern)

        return CapabilityResult.from_evidence(
            evidence_list,
            metadata={
                "finding_count": len(findings),
                "by_category": {k: list(set(v)) for k, v in by_category.items()},
                "by_risk": by_risk,
            },
        )


class KeychainAnalysisCapability(CapabilityExecutor):
    """
    Keychain analysis capability.

    Detects Keychain API usage patterns.
    """

    CAPABILITY_ID = "static.keychain_analysis"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    KEYCHAIN_APIS = [
        "SecItemAdd",
        "SecItemCopyMatching",
        "SecItemUpdate",
        "SecItemDelete",
        "kSecClass",
        "kSecAttrAccount",
        "kSecAttrService",
        "kSecAttrAccessGroup",
        "kSecAttrAccessible",
        "kSecAttrAccessibleWhenUnlocked",
        "kSecAttrAccessibleWhenUnlockedThisDeviceOnly",
        "kSecAttrAccessibleAfterFirstUnlock",
        "SAMKeychain",
        "KeychainAccess",
        "KeychainItem",
    ]

    def __init__(self):
        super().__init__()

    def dependencies(self) -> List[str]:
        return ["macho.symbols", "macho.imports"]

    def inputs(self) -> Dict[str, Any]:
        return {
            "symbols": "List of symbols",
            "imports": "List of imports",
            "strings": "Optional strings for context",
        }

    def outputs(self) -> Dict[str, Any]:
        return {
            "keychain_apis": "Detected Keychain API usage",
            "accessibility": "Detected accessibility settings",
            "patterns": "Keychain usage patterns",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Execute Keychain analysis."""
        symbols = context.get("symbols", [])
        imports = context.get("imports", [])
        strings = context.get("strings", [])

        found_apis = []
        found_accessibility = []

        # Check symbols
        for sym in symbols:
            if isinstance(sym, dict):
                name = sym.get("name", "")
            else:
                name = str(sym)

            for api in self.KEYCHAIN_APIS:
                if api in name:
                    found_apis.append(api)
                    break

        # Check imports
        for imp in imports:
            if isinstance(imp, dict):
                name = imp.get("name", "")
            else:
                name = str(imp)

            for api in self.KEYCHAIN_APIS:
                if api in name:
                    if api not in found_apis:
                        found_apis.append(api)
                    break

        # Check strings for accessibility
        for s in strings:
            if isinstance(s, dict):
                value = s.get("value", "")
            else:
                value = str(s)

            for api in self.KEYCHAIN_APIS:
                if api in value and api.startswith("kSecAttrAccessible"):
                    if api not in found_accessibility:
                        found_accessibility.append(api)

        # Build evidence
        evidence_list = []
        for api in found_apis:
            evidence_list.append(Evidence(
                evidence_id=f"keychain-api-{api}",
                evidence_type=EvidenceType.STRUCTURAL,
                strength=EvidenceStrength.STRING_HINT,
                source_artifact=context.get("artifact_path", "unknown"),
                content={
                    "type": "keychain_api",
                    "api": api,
                },
                capability_id=self.CAPABILITY_ID,
                metadata={"category": "keychain", "api": api},
            ))

        for acc in found_accessibility:
            evidence_list.append(Evidence(
                evidence_id=f"keychain-access-{acc}",
                evidence_type=EvidenceType.STRING_HINT,
                strength=EvidenceStrength.STRING_HINT,
                source_artifact=context.get("artifact_path", "unknown"),
                content={
                    "type": "keychain_accessibility",
                    "setting": acc,
                },
                capability_id=self.CAPABILITY_ID,
                metadata={"category": "keychain", "accessibility": acc},
            ))

        return CapabilityResult.from_evidence(
            evidence_list,
            metadata={
                "api_count": len(found_apis),
                "accessibility_count": len(found_accessibility),
                "apis": found_apis,
                "accessibility": found_accessibility,
            },
        )


class JailbreakDetectionCapability(CapabilityExecutor):
    """
    Jailbreak detection capability.

    Detects jailbreak indicators in the binary.
    """

    CAPABILITY_ID = "static.jailbreak_detection"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    JAILBREAK_PATTERNS = [
        "/Applications/Cydia.app",
        "/Library/MobileSubstrate/MobileSubstrate.dylib",
        "/bin/bash",
        "/usr/sbin/sshd",
        "/etc/apt",
        "/private/var/lib/apt/",
        "/private/var/lib/cydia",
        "/private/var/stash",
        "/private/var/mobile/Library/SBSettings/Themes",
        "/System/Library/LaunchDaemons/com.ikey.bbot.plist",
        "/System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist",
        "/usr/bin/cycript",
        "/usr/local/bin/cycript",
        "/usr/lib/libcycript",
        "cydia://package",
        "substrate.h",
        "SubstrateLoader",
        "MSHookFunction",
        "MobileSubstrate",
        "Telesphoreo",
        "electra",
        "checkra1n",
        "unc0ver",
        "jailbreak",
        "/jb/",
        "/.bootstrapped_electra",
        "/usr/lib/libjailbreak.dylib",
        "frida",
        "frida-server",
        "substrate",
        "/private/var/tmp/cydia.log",
        "cydia:",
    ]

    def __init__(self):
        super().__init__()

    def dependencies(self) -> List[str]:
        return ["macho.strings"]

    def inputs(self) -> Dict[str, Any]:
        return {
            "strings": "List of strings from binary",
        }

    def outputs(self) -> Dict[str, Any]:
        return {
            "indicators": "Detected jailbreak indicators",
            "confidence": "Confidence level (high, medium, low)",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Execute jailbreak detection."""
        strings = context.get("strings", [])

        found_indicators = []

        for s in strings:
            if isinstance(s, dict):
                value = s.get("value", "")
            else:
                value = str(s)

            for pattern in self.JAILBREAK_PATTERNS:
                if pattern.lower() in value.lower():
                    found_indicators.append(pattern)

        # Calculate confidence
        if len(found_indicators) >= 5:
            confidence = "high"
        elif len(found_indicators) >= 2:
            confidence = "medium"
        elif len(found_indicators) >= 1:
            confidence = "low"
        else:
            confidence = "none"

        # Build evidence
        evidence_list = []
        for indicator in found_indicators:
            evidence_list.append(Evidence(
                evidence_id=f"jailbreak-{indicator[:30].replace('/', '_')}",
                evidence_type=EvidenceType.STRING_HINT,
                strength=EvidenceStrength.STRING_HINT,
                source_artifact=context.get("artifact_path", "unknown"),
                content={
                    "type": "jailbreak_indicator",
                    "pattern": indicator,
                },
                capability_id=self.CAPABILITY_ID,
                metadata={"category": "jailbreak"},
            ))

        return CapabilityResult.from_evidence(
            evidence_list,
            metadata={
                "indicator_count": len(found_indicators),
                "indicators": found_indicators,
                "confidence": confidence,
            },
        )


class ObfuscationDetectionCapability(CapabilityExecutor):
    """
    Obfuscation detection capability.

    Detects code obfuscation indicators.
    """

    CAPABILITY_ID = "static.obfuscation_detection"
    VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def get_contract(self) -> Dict[str, Any]:
        return {
            "id": self.CAPABILITY_ID,
            "version": self.VERSION,
        }

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs."""
        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute capability."""
        return self.execute_capability(inputs)

    OBFUSCATION_PATTERNS = {
        "symbol_stripping": {
            "indicators": ["_mh_execute_header"],
            "description": "Symbols appear stripped",
        },
        "code_stripping": {
            "indicators": ["GCC_except_table", "__stub_helper", "__unwind_info"],
            "description": "Exception handling stripped",
        },
        "encryption": {
            "indicators": ["cryptid", "LC_ENCRYPTION", "fairplay"],
            "description": "Binary or code appears encrypted",
        },
        "junk_code": {
            "indicators": ["__text", "__stub_helper"],
            "description": "May contain junk/padding code",
        },
        "function_pointer_obfuscation": {
            "indicators": ["IMP", "objc_msgSend", "dispatch"],
            "description": "Uses function pointer obfuscation",
        },
    }

    def __init__(self):
        super().__init__()

    def dependencies(self) -> List[str]:
        return ["macho.strings", "macho.symbols", "macho.load_commands"]

    def inputs(self) -> Dict[str, Any]:
        return {
            "strings": "List of strings",
            "symbols": "List of symbols",
            "load_commands": "List of load commands",
        }

    def outputs(self) -> Dict[str, Any]:
        return {
            "patterns": "Detected obfuscation patterns",
            "score": "Obfuscation score (0-100)",
        }

    def execute_capability(self, context: Dict[str, Any]) -> CapabilityResult:
        """Execute obfuscation detection."""
        strings = context.get("strings", [])
        symbols = context.get("symbols", [])
        load_commands = context.get("load_commands", [])

        found_patterns = []
        score = 0

        # Check each obfuscation type
        for pattern_name, pattern_info in self.OBFUSCATION_PATTERNS.items():
            for indicator in pattern_info["indicators"]:
                found = False

                # Check strings
                for s in strings:
                    if isinstance(s, dict):
                        value = s.get("value", "")
                    else:
                        value = str(s)
                    if indicator in value:
                        found = True
                        break

                # Check symbols
                if not found:
                    for sym in symbols:
                        if isinstance(sym, dict):
                            name = sym.get("name", "")
                        else:
                            name = str(sym)
                        if indicator in name:
                            found = True
                            break

                # Check load commands
                if not found:
                    for cmd in load_commands:
                        if isinstance(cmd, dict):
                            cmd_str = str(cmd)
                        else:
                            cmd_str = str(cmd)
                        if indicator in cmd_str:
                            found = True
                            break

                if found:
                    found_patterns.append(pattern_name)
                    score += 20
                    break

        # Normalize score
        score = min(score, 100)

        # Build evidence
        evidence_list = []
        for pattern in found_patterns:
            pattern_info = self.OBFUSCATION_PATTERNS.get(pattern, {})
            evidence_list.append(Evidence(
                evidence_id=f"obfuscation-{pattern}",
                evidence_type=EvidenceType.STRING_HINT,
                strength=EvidenceStrength.STRING_HINT,
                source_artifact=context.get("artifact_path", "unknown"),
                content={
                    "type": "obfuscation_pattern",
                    "pattern": pattern,
                    "description": pattern_info.get("description", ""),
                },
                capability_id=self.CAPABILITY_ID,
                metadata={"category": "obfuscation"},
            ))

        return CapabilityResult.from_evidence(
            evidence_list,
            metadata={
                "pattern_count": len(found_patterns),
                "patterns": found_patterns,
                "score": score,
            },
        )
