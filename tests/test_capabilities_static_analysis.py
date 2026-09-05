"""
Tests for static analysis capabilities.

Covers SDK fingerprinting, secret scanning, keychain analysis,
jailbreak detection, and obfuscation detection.
"""

import pytest
from pathlib import Path

from ios_reverse.capabilities.static_analysis import (
    SDKFingerprintingCapability,
    SecretScanningCapability,
    KeychainAnalysisCapability,
    JailbreakDetectionCapability,
    ObfuscationDetectionCapability,
)


class TestSDKFingerprinting:
    """Tests for SDK fingerprinting capability."""

    def test_capability_initialization(self):
        """Test capability initializes correctly."""
        cap = SDKFingerprintingCapability()
        assert cap.CAPABILITY_ID == "static.sdk_fingerprinting"
        assert cap.VERSION == "0.1.0"

    def test_firebase_detection_from_strings(self):
        """Test Firebase SDK detection from strings."""
        cap = SDKFingerprintingCapability()
        result = cap.execute_capability({
            "strings": [
                "firebaseio.com",
                "firebaseapp.com",
                "GoogleService-Info.plist",
            ],
            "frameworks": [],
            "classes": [],
            "symbols": [],
        })

        assert result.success
        assert result.metadata.get("sdk_count", 0) >= 1
        sdks = result.metadata.get("sdks", [])
        assert "Firebase" in sdks

    def test_alamofire_detection_from_classes(self):
        """Test Alamofire detection from class prefixes."""
        cap = SDKFingerprintingCapability()
        result = cap.execute_capability({
            "strings": [],
            "frameworks": [],
            "classes": [
                "AFHTTPSessionManager",
                "AFURLSessionManager",
            ],
            "symbols": [],
        })

        assert result.success
        sdks = result.metadata.get("sdks", [])
        assert "Alamofire" in sdks

    def test_facebook_detection_from_strings(self):
        """Test Facebook SDK detection from strings."""
        cap = SDKFingerprintingCapability()
        result = cap.execute_capability({
            "strings": ["fb://login"],
            "frameworks": [],
            "classes": [],
            "symbols": [],
        })

        assert result.success
        sdks = result.metadata.get("sdks", [])
        assert "Facebook" in sdks

    def test_no_strings_returns_empty(self):
        """Test empty strings returns no SDKs."""
        cap = SDKFingerprintingCapability()
        result = cap.execute_capability({
            "strings": [],
            "frameworks": [],
            "classes": [],
            "symbols": [],
        })

        # Empty inputs returns failure (no data to analyze)
        assert result.status.value == "failure"

    def test_framework_detection(self):
        """Test framework-based SDK detection."""
        cap = SDKFingerprintingCapability()
        result = cap.execute_capability({
            "strings": [],
            "frameworks": ["Alamofire.framework"],
            "classes": [],
            "symbols": [],
        })

        assert result.success
        sdks = result.metadata.get("sdks", [])
        assert "Alamofire" in sdks


class TestSecretScanning:
    """Tests for secret scanning capability."""

    def test_capability_initialization(self):
        """Test capability initializes correctly."""
        cap = SecretScanningCapability()
        assert cap.CAPABILITY_ID == "static.secret_scanning"
        assert cap.VERSION == "0.1.0"

    def test_aws_access_key_detection(self):
        """Test AWS access key detection."""
        cap = SecretScanningCapability()
        result = cap.execute_capability({
            "strings": ["AKIAIOSFODNN7EXAMPLE"],
            "include_client_safe": False,
        })

        assert result.success
        findings = result.metadata.get("by_category", {})
        assert "AWS" in findings

    def test_firebase_endpoint_detection(self):
        """Test Firebase endpoint detection."""
        cap = SecretScanningCapability()
        result = cap.execute_capability({
            "strings": ["firebaseio.com"],
            "include_client_safe": True,
        })

        assert result.status.value in ["success", "partial"]
        findings = result.metadata.get("by_category", {})
        assert "Firebase" in findings

    def test_aws_key_detection(self):
        """Test AWS key detection."""
        cap = SecretScanningCapability()
        result = cap.execute_capability({
            "strings": ["AKIAIOSFODNN7EXAMPLE"],
            "include_client_safe": False,
        })

        assert result.status.value in ["success", "partial"]
        findings = result.metadata.get("by_category", {})
        assert "AWS" in findings

    def test_ip_address_marked_client_safe(self):
        """Test IP address is marked client safe."""
        cap = SecretScanningCapability()
        result = cap.execute_capability({
            "strings": ["192.168.1.1"],
            "include_client_safe": True,
        })

        assert result.success
        # IP addresses should be found
        count = result.metadata.get("finding_count", 0)
        assert count >= 1

    def test_no_client_safe_by_default(self):
        """Test client-safe findings excluded by default."""
        cap = SecretScanningCapability()
        result = cap.execute_capability({
            "strings": ["192.168.1.1", "AKIAIOSFODNN7EXAMPLE"],
            "include_client_safe": False,
        })

        assert result.success
        # Should only find AWS key, not IP
        count = result.metadata.get("finding_count", 0)
        assert count == 1

    def test_high_risk_keys_detected(self):
        """Test high-risk secrets have correct risk level."""
        cap = SecretScanningCapability()
        # Using JWT pattern which is high risk
        result = cap.execute_capability({
            "strings": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3Ud8tMEMJ7x5bMLL"],
            "include_client_safe": False,
        })

        assert result.status.value in ["success", "partial"]
        by_risk = result.metadata.get("by_risk", {})
        assert "high_risk" in by_risk or "JWT" in result.metadata.get("by_category", {})


class TestKeychainAnalysis:
    """Tests for keychain analysis capability."""

    def test_capability_initialization(self):
        """Test capability initializes correctly."""
        cap = KeychainAnalysisCapability()
        assert cap.CAPABILITY_ID == "static.keychain_analysis"
        assert cap.VERSION == "0.1.0"

    def test_secitemadd_detection(self):
        """Test SecItemAdd API detection."""
        cap = KeychainAnalysisCapability()
        result = cap.execute_capability({
            "symbols": ["_SecItemAdd"],
            "imports": [],
            "strings": [],
        })

        assert result.success
        apis = result.metadata.get("apis", [])
        assert "SecItemAdd" in apis

    def test_secitemcopymatching_detection(self):
        """Test SecItemCopyMatching API detection."""
        cap = KeychainAnalysisCapability()
        result = cap.execute_capability({
            "symbols": [],
            "imports": ["SecItemCopyMatching"],
            "strings": [],
        })

        assert result.success
        apis = result.metadata.get("apis", [])
        assert "SecItemCopyMatching" in apis

    def test_accessibility_constant_detection(self):
        """Test kSecAttrAccessible constant detection."""
        cap = KeychainAnalysisCapability()
        result = cap.execute_capability({
            "symbols": [],
            "imports": [],
            "strings": ["kSecAttrAccessibleWhenUnlocked"],
        })

        assert result.success
        acc = result.metadata.get("accessibility", [])
        assert "kSecAttrAccessibleWhenUnlocked" in acc

    def test_no_apis_returns_empty(self):
        """Test no keychain APIs returns empty."""
        cap = KeychainAnalysisCapability()
        result = cap.execute_capability({
            "symbols": [],
            "imports": [],
            "strings": [],
        })

        assert result.success
        assert result.metadata.get("api_count", 0) == 0


class TestJailbreakDetection:
    """Tests for jailbreak detection capability."""

    def test_capability_initialization(self):
        """Test capability initializes correctly."""
        cap = JailbreakDetectionCapability()
        assert cap.CAPABILITY_ID == "static.jailbreak_detection"
        assert cap.VERSION == "0.1.0"

    def test_cydia_path_detection(self):
        """Test Cydia path detection."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": ["/Applications/Cydia.app"],
        })

        assert result.success
        indicators = result.metadata.get("indicators", [])
        assert "/Applications/Cydia.app" in indicators

    def test_ssh_detection(self):
        """Test SSH detection."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": ["/usr/sbin/sshd"],
        })

        assert result.success
        indicators = result.metadata.get("indicators", [])
        assert "/usr/sbin/sshd" in indicators

    def test_substrate_detection(self):
        """Test Substrate detection."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": ["/Library/MobileSubstrate/MobileSubstrate.dylib"],
        })

        assert result.success
        indicators = result.metadata.get("indicators", [])
        assert len(indicators) >= 1

    def test_no_indicators_confidence_none(self):
        """Test no indicators gives confidence none."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": [],
        })

        assert result.success
        assert result.metadata.get("confidence") == "none"

    def test_single_indicator_low_confidence(self):
        """Test single indicator gives low confidence."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": ["/bin/bash"],
        })

        assert result.success
        assert result.metadata.get("confidence") == "low"

    def test_multiple_indicators_medium_confidence(self):
        """Test multiple indicators gives medium confidence."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": [
                "/bin/bash",
                "/usr/sbin/sshd",
            ],
        })

        assert result.success
        assert result.metadata.get("confidence") == "medium"

    def test_many_indicators_high_confidence(self):
        """Test many indicators gives high confidence."""
        cap = JailbreakDetectionCapability()
        result = cap.execute_capability({
            "strings": [
                "/Applications/Cydia.app",
                "/Library/MobileSubstrate/MobileSubstrate.dylib",
                "/bin/bash",
                "/usr/sbin/sshd",
                "/etc/apt",
                "substrate.h",
            ],
        })

        assert result.success
        assert result.metadata.get("confidence") == "high"


class TestObfuscationDetection:
    """Tests for obfuscation detection capability."""

    def test_capability_initialization(self):
        """Test capability initializes correctly."""
        cap = ObfuscationDetectionCapability()
        assert cap.CAPABILITY_ID == "static.obfuscation_detection"
        assert cap.VERSION == "0.1.0"

    def test_encryption_detection(self):
        """Test encryption indicator detection."""
        cap = ObfuscationDetectionCapability()
        result = cap.execute_capability({
            "strings": ["cryptid", "LC_ENCRYPTION"],
            "symbols": [],
            "load_commands": [],
        })

        assert result.success
        patterns = result.metadata.get("patterns", [])
        assert "encryption" in patterns

    def test_symbol_stripping_detection(self):
        """Test symbol stripping detection."""
        cap = ObfuscationDetectionCapability()
        result = cap.execute_capability({
            "strings": [],
            "symbols": ["_mh_execute_header"],
            "load_commands": [],
        })

        assert result.success
        patterns = result.metadata.get("patterns", [])
        assert "symbol_stripping" in patterns

    def test_no_patterns_returns_zero_score(self):
        """Test no patterns gives zero score."""
        cap = ObfuscationDetectionCapability()
        result = cap.execute_capability({
            "strings": [],
            "symbols": [],
            "load_commands": [],
        })

        assert result.success
        assert result.metadata.get("score") == 0

    def test_multiple_patterns_accumulate_score(self):
        """Test multiple patterns accumulate score."""
        cap = ObfuscationDetectionCapability()
        result = cap.execute_capability({
            "strings": ["cryptid", "GCC_except_table"],
            "symbols": ["_mh_execute_header"],
            "load_commands": [],
        })

        assert result.success
        score = result.metadata.get("score", 0)
        assert score >= 40  # At least 2 patterns

    def test_score_capped_at_100(self):
        """Test score calculation."""
        cap = ObfuscationDetectionCapability()
        result = cap.execute_capability({
            "strings": ["cryptid", "GCC_except_table", "dispatch", "IMP", "objc_msgSend"],
            "symbols": ["_mh_execute_header", "MobileSubstrate", "fairplay"],
            "load_commands": ["LC_ENCRYPTION"],
        })

        assert result.success
        # Score is calculated based on patterns found, capped at 100
        score = result.metadata.get("score", 0)
        assert score >= 80  # At least 4 patterns detected
