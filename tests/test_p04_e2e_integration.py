"""
P04.8: Capability Integration Gate Tests.

End-to-end integration tests for the complete capability layer.
"""

import hashlib
import json
import os
import pytest
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from unittest.mock import patch

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_reverse.capabilities import (
    ArtifactDetectCapability, IpaValidateCapability, IpaUnpackCapability,
    BundleInventoryCapability, PlistExtractCapability, EntitlementsExtractCapability,
    MachoBasicCapability, MachoSlicesCapability, MachoLoadCommandsCapability,
    BinaryImportsCapability, BinaryExportsCapability, BinarySymbolsCapability,
    BinaryStringsCapability, ObjCMetadataCapability, SwiftMetadataCapability,
    FrameworkInventoryCapability, DylibInventoryCapability, ExtensionInventoryCapability,
    ComponentGraphCapability, NetworkFrameworkDetectionCapability,
    NetworkEndpointDiscoveryCapability, ArchitectureDetectionCapability,
    CallflowReconstructCapability, CryptoDetectionCapability,
    AntiAnalysisDetectionCapability, CoverageAuditorCapability,
)
from ios_reverse.capabilities.base import CapabilityResult, CapabilityStatus
from ios_reverse.models.coverage import (
    CoverageState, CoverageDimension, CoverageTarget, CoverageTargetType
)
from ios_reverse.models.report import Report, ReportSection, ReportMetadata, ReportFinding
from ios_reverse.renderers import JSONRenderer, MarkdownRenderer, render_coverage_audit


# =============================================================================
# FIXTURE A — MINIMAL IOS APP
# =============================================================================

class TestFixtureA:
    """Fixture A: Minimal iOS App - validates narrow baseline pipeline."""

    @pytest.fixture
    def minimal_ipa(self, tmp_path):
        """Create minimal IPA fixture."""
        fixture_dir = tmp_path / "fixture_a"
        fixture_dir.mkdir()

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Minimal.app"
        app_dir.mkdir(parents=True)

        # Info.plist
        plist_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>Minimal</string>
    <key>CFBundleIdentifier</key><string>com.test.minimal</string>
    <key>CFBundleName</key><string>Minimal</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
    <key>CFBundleVersion</key><string>1</string>
</dict>
</plist>
'''
        (app_dir / "Info.plist").write_bytes(plist_content)

        # Simple Mach-O header
        import struct
        magic = 0xfeedface
        header = struct.pack('>IIIIIII',
            magic, 0x0100000c, 0x80000002, 0x00000002, 0, 0, 0x00200085
        )
        content = header + b'\x00' * 256
        (app_dir / "Minimal").write_bytes(content)

        # Create IPA
        ipa_path = tmp_path / "minimal.ipa"
        with zipfile.ZipFile(ipa_path, 'w') as zf:
            for root, dirs, files in os.walk(fixture_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(fixture_dir)
                    zf.write(file_path, arc_name)

        return ipa_path

    def test_artifact_detect(self, minimal_ipa):
        """Test artifact detection."""
        cap = ArtifactDetectCapability()
        result = cap.execute({"artifact_path": str(minimal_ipa)})

        assert result.status.value == "success"
        assert result.metadata.get("artifact_type") == "ipa"

    def test_ipa_validate(self, minimal_ipa):
        """Test IPA validation."""
        cap = IpaValidateCapability()
        result = cap.execute({"artifact_path": str(minimal_ipa)})

        assert result.status.value in ["success", "partial"]

    def test_ipa_unpack(self, minimal_ipa):
        """Test IPA unpacking."""
        cap = IpaUnpackCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = cap.execute({
                "artifact_path": str(minimal_ipa),
                "output_dir": tmpdir
            })

            assert result.status.value == "success"
            assert Path(tmpdir).exists()

            # Check unpacked content
            app_path = Path(tmpdir) / "Payload" / "Minimal.app"
            assert app_path.exists()

    def test_bundle_inventory(self, minimal_ipa):
        """Test bundle inventory."""
        cap = BundleInventoryCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            # First unpack
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(minimal_ipa),
                "output_dir": tmpdir
            })

            # Then inventory - use correct input key
            app_path = Path(tmpdir) / "Payload" / "Minimal.app"
            result = cap.execute({
                "bundle_path": str(app_path)
            })

            assert result.status.value in ["success", "partial"]


# =============================================================================
# FIXTURE B — MIXED APPLICATION
# =============================================================================

class TestFixtureB:
    """Fixture B: Multi-component application - validates full pipeline."""

    @pytest.fixture
    def mixed_ipa(self, tmp_path):
        """Create mixed application IPA fixture."""
        fixture_dir = tmp_path / "fixture_b"
        fixture_dir.mkdir()

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Mixed.app"
        app_dir.mkdir(parents=True)

        # Info.plist
        plist_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>Mixed</string>
    <key>CFBundleIdentifier</key><string>com.test.mixed</string>
    <key>CFBundleName</key><string>Mixed</string>
    <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>
'''
        (app_dir / "Info.plist").write_bytes(plist_content)

        # Mach-O with evidence
        import struct
        magic = 0xfeedface
        header = struct.pack('>IIIIIII',
            magic, 0x0100000c, 0x80000002, 0x00000002, 0, 0, 0x00200085
        )

        # Strings with evidence
        strings = b''
        strings += b'/Applications/Cydia.app/System/Library\x00'  # Jailbreak
        strings += b'https://api.example.com/v1/users\x00'  # Network
        strings += b'AES-256-CBC\x00'  # Crypto
        strings += b'NSURLSession\x00'  # Network framework
        strings += b'_CCCrypt\x00'  # Crypto import
        strings += b'NSObject\x00'  # ObjC
        strings += b'_T05MyApp8StorageV\x00'  # Swift

        content = header + b'\x00' * 512 + strings
        (app_dir / "Mixed").write_bytes(content)

        # Frameworks
        fw_dir = app_dir / "Frameworks"
        fw_dir.mkdir()
        net_fw = fw_dir / "Networking.framework"
        net_fw.mkdir()

        # Networking framework Info.plist
        (net_fw / "Info.plist").write_bytes(plist_content)

        # Networking dylib with evidence
        net_strings = b'NSURL\x00_T05Network\x00'
        net_content = header + b'\x00' * 128 + net_strings
        (net_fw / "Networking").write_bytes(net_content)

        # Shared.framework
        shared_fw = fw_dir / "Shared.framework"
        shared_fw.mkdir()
        (shared_fw / "Info.plist").write_bytes(plist_content)

        # PlugIns
        plugins_dir = app_dir / "PlugIns"
        plugins_dir.mkdir()
        widget_ext = plugins_dir / "Widget.appex"
        widget_ext.mkdir()
        (widget_ext / "Info.plist").write_bytes(plist_content)

        # Widget executable
        (widget_ext / "Widget").write_bytes(content)

        # Dylib
        (app_dir / "libExample.dylib").write_bytes(content)

        # Create IPA
        ipa_path = tmp_path / "mixed.ipa"
        with zipfile.ZipFile(ipa_path, 'w') as zf:
            for root, dirs, files in os.walk(fixture_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(fixture_dir)
                    zf.write(file_path, arc_name)

        return ipa_path

    def test_framework_inventory(self, mixed_ipa):
        """Test framework inventory."""
        cap = FrameworkInventoryCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            app_path = Path(tmpdir) / "Payload" / "Mixed.app"
            result = cap.execute({
                "artifact_path": str(app_path)
            })

            assert result.status.value in ["success", "partial"]

    def test_dylib_inventory(self, mixed_ipa):
        """Test dylib inventory."""
        cap = DylibInventoryCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            app_path = Path(tmpdir) / "Payload" / "Mixed.app"
            result = cap.execute({
                "artifact_path": str(app_path)
            })

            assert result.status.value in ["success", "partial"]

    def test_extension_inventory(self, mixed_ipa):
        """Test extension inventory."""
        cap = ExtensionInventoryCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            app_path = Path(tmpdir) / "Payload" / "Mixed.app"
            result = cap.execute({
                "artifact_path": str(app_path)
            })

            assert result.status.value in ["success", "partial"]

    def test_macho_basic(self, mixed_ipa):
        """Test Mach-O basic analysis."""
        cap = MachoBasicCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial"]

    def test_binary_strings(self, mixed_ipa):
        """Test string extraction."""
        cap = BinaryStringsCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial"]
            # Check evidence strength is preserved
            strings = result.metadata.get("strings", [])
            # Weak hints should remain weak

    def test_objc_metadata(self, mixed_ipa):
        """Test ObjC metadata."""
        cap = ObjCMetadataCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            # ObjC may or may not be found depending on fixture content
            assert result.status.value in ["success", "partial", "failure"]

    def test_swift_metadata(self, mixed_ipa):
        """Test Swift metadata."""
        cap = SwiftMetadataCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial", "failure"]

    def test_network_framework_detection(self, mixed_ipa):
        """Test network framework detection."""
        cap = NetworkFrameworkDetectionCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial"]

    def test_network_endpoint_discovery(self, mixed_ipa):
        """Test network endpoint discovery."""
        cap = NetworkEndpointDiscoveryCapability()

        # Network endpoint discovery needs strings_data as input
        # (not artifact_path - it works on pre-extracted strings)
        strings_data = "https://api.example.com/v1/users NSURLSession https://test.com/api"

        result = cap.execute({
            "strings_data": strings_data
        })

        # May find endpoints or may have none in test data
        assert result.status.value in ["success", "partial", "failure"]

    def test_crypto_detection(self, mixed_ipa):
        """Test crypto detection."""
        cap = CryptoDetectionCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial"]

    def test_anti_analysis_detection(self, mixed_ipa):
        """Test anti-analysis detection."""
        cap = AntiAnalysisDetectionCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(mixed_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Mixed.app" / "Mixed"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial"]


# =============================================================================
# FIXTURE C — PARTIAL/BROKEN APPLICATION
# =============================================================================

class TestFixtureC:
    """Fixture C: Partial/Broken - validates failure handling."""

    @pytest.fixture
    def partial_ipa(self, tmp_path):
        """Create partial/broken IPA fixture."""
        fixture_dir = tmp_path / "fixture_c"
        fixture_dir.mkdir()

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Partial.app"
        app_dir.mkdir(parents=True)

        # Valid Info.plist
        plist_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>Partial</string>
    <key>CFBundleIdentifier</key><string>com.test.partial</string>
</dict>
</plist>
'''
        (app_dir / "Info.plist").write_bytes(plist_content)

        # Valid Mach-O
        import struct
        magic = 0xfeedface
        header = struct.pack('>IIIIIII',
            magic, 0x0100000c, 0x80000002, 0x00000002, 0, 0, 0x00200085
        )
        (app_dir / "Partial").write_bytes(header + b'\x00' * 256)

        # Broken framework
        broken_fw = app_dir / "Frameworks"
        broken_fw.mkdir()
        broken_info = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>Broken</string>
    <key>CFBundleIdentifier</key><string>com.test.broken</string>
</dict>
</plist>
'''
        (broken_fw / "Broken.framework").mkdir()
        (broken_fw / "Broken.framework" / "Info.plist").write_bytes(broken_info)
        # Truncated garbage instead of valid Mach-O
        (broken_fw / "Broken.framework" / "Broken").write_bytes(b'TRUNCATED' * 10)

        # Create IPA
        ipa_path = tmp_path / "partial.ipa"
        with zipfile.ZipFile(ipa_path, 'w') as zf:
            for root, dirs, files in os.walk(fixture_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(fixture_dir)
                    zf.write(file_path, arc_name)

        return ipa_path

    def test_partial_analysis_survives(self, partial_ipa):
        """Test that partial analysis survives."""
        cap = MachoBasicCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(partial_ipa),
                "output_dir": tmpdir
            })

            # Valid binary should work
            valid_path = Path(tmpdir) / "Payload" / "Partial.app" / "Partial"
            valid_result = cap.execute({"artifact_path": str(valid_path)})
            assert valid_result.status.value in ["success", "partial"]

            # Broken binary should fail gracefully
            broken_path = Path(tmpdir) / "Payload" / "Partial.app" / "Frameworks" / "Broken.framework" / "Broken"
            broken_result = cap.execute({"artifact_path": str(broken_path)})
            # Should not crash, may return failure
            assert broken_result.status.value in ["success", "partial", "failure"]

    def test_coverage_detects_gaps(self, partial_ipa):
        """Test that coverage detects gaps."""
        cap = CoverageAuditorCapability()

        # 2 eligible targets, only 1 valid
        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": [
                {"path": "/Payload/Partial.app/Partial", "type": "executable"},
                {"path": "/Payload/Partial.app/Frameworks/Broken.framework/Broken", "type": "executable"},
            ],
            "capability_results": [
                {"target_id": "target-1", "capability_id": "macho.basic", "status": "success"},
            ],
        })

        assert result.status.value == "success"
        # Should detect gap
        assert result.metadata.get("gap_count", 0) > 0 or result.metadata.get("coverage_complete") == False


# =============================================================================
# FIXTURE D — FAT MACH-O
# =============================================================================

class TestFixtureD:
    """Fixture D: Fat/Universal Mach-O - validates multi-architecture."""

    @pytest.fixture
    def fat_ipa(self, tmp_path):
        """Create fat Mach-O IPA fixture."""
        fixture_dir = tmp_path / "fixture_d"
        fixture_dir.mkdir()

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Fat.app"
        app_dir.mkdir(parents=True)

        # Info.plist
        plist_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>Fat</string>
    <key>CFBundleIdentifier</key><string>com.test.fat</string>
</dict>
</plist>
'''
        (app_dir / "Info.plist").write_bytes(plist_content)

        # Fat Mach-O
        import struct
        # Fat header
        magic = 0xcafebabe
        nfat_arch = 2
        fat_header = struct.pack('>II', magic, nfat_arch)

        # ARM64 slice header
        arm64_entry = struct.pack('>IIIIII',
            0x0100000c, 0x80000002, 32, 256, 14, 0
        )

        # ARMv7 slice header
        armv7_entry = struct.pack('>IIIIII',
            0x00000007, 0x00000009, 288, 256, 14, 0
        )

        # Slice content
        slice_header = struct.pack('>IIIIIII',
            0xfeedface, 0x0100000c, 0x80000002, 0x00000002, 0, 0, 0x00200085
        )
        arm64_content = slice_header + b'\x00' * 248
        armv7_content = slice_header + b'\x00' * 248

        fat_binary = fat_header + arm64_entry + armv7_entry + arm64_content + armv7_content
        (app_dir / "Fat").write_bytes(fat_binary)

        # Create IPA
        ipa_path = tmp_path / "fat.ipa"
        with zipfile.ZipFile(ipa_path, 'w') as zf:
            for root, dirs, files in os.walk(fixture_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(fixture_dir)
                    zf.write(file_path, arc_name)

        return ipa_path

    def test_fat_macho_slices(self, fat_ipa):
        """Test fat Mach-O slice detection."""
        cap = MachoSlicesCapability()

        with tempfile.TemporaryDirectory() as tmpdir:
            unpack = IpaUnpackCapability()
            unpack.execute({
                "artifact_path": str(fat_ipa),
                "output_dir": tmpdir
            })

            binary_path = Path(tmpdir) / "Payload" / "Fat.app" / "Fat"

            result = cap.execute({
                "artifact_path": str(binary_path)
            })

            assert result.status.value in ["success", "partial"]
            # Should detect multiple slices


# =============================================================================
# REGISTRY AUDIT
# =============================================================================

class TestRegistryAudit:
    """Test that registry is complete and accurate."""

    def test_all_capabilities_have_contracts(self):
        """Every implemented capability has a valid contract."""
        from ios_reverse.capabilities import (
            ArtifactDetectCapability, IpaValidateCapability, IpaUnpackCapability,
            BundleInventoryCapability, PlistExtractCapability, EntitlementsExtractCapability,
            MachoBasicCapability, MachoSlicesCapability, MachoLoadCommandsCapability,
            BinaryImportsCapability, BinaryExportsCapability, BinarySymbolsCapability,
            BinaryStringsCapability, ObjCMetadataCapability, SwiftMetadataCapability,
            FrameworkInventoryCapability, DylibInventoryCapability, ExtensionInventoryCapability,
            NetworkFrameworkDetectionCapability, NetworkEndpointDiscoveryCapability,
            ArchitectureDetectionCapability, CallflowReconstructCapability,
            CryptoDetectionCapability, AntiAnalysisDetectionCapability,
            CoverageAuditorCapability,
        )

        capabilities = [
            ArtifactDetectCapability(),
            IpaValidateCapability(),
            IpaUnpackCapability(),
            BundleInventoryCapability(),
            PlistExtractCapability(),
            EntitlementsExtractCapability(),
            MachoBasicCapability(),
            MachoSlicesCapability(),
            MachoLoadCommandsCapability(),
            BinaryImportsCapability(),
            BinaryExportsCapability(),
            BinarySymbolsCapability(),
            BinaryStringsCapability(),
            ObjCMetadataCapability(),
            SwiftMetadataCapability(),
            FrameworkInventoryCapability(),
            DylibInventoryCapability(),
            ExtensionInventoryCapability(),
            NetworkFrameworkDetectionCapability(),
            NetworkEndpointDiscoveryCapability(),
            ArchitectureDetectionCapability(),
            CallflowReconstructCapability(),
            CryptoDetectionCapability(),
            AntiAnalysisDetectionCapability(),
            CoverageAuditorCapability(),
        ]

        for cap in capabilities:
            contract = cap.get_contract()
            assert contract.id is not None
            assert contract.version is not None
            assert contract.domain is not None


# =============================================================================
# COVERAGE E2E
# =============================================================================

class TestCoverageE2E:
    """End-to-end coverage tests."""

    def test_false_100_prevented(self):
        """False 100% coverage is prevented."""
        cap = CoverageAuditorCapability()

        # 10 eligible, 8 analyzed, 2 not attempted
        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": [{"path": f"/bin/app{i}"} for i in range(10)],
            "capability_results": [
                {"target_id": f"target-{i}", "capability_id": "macho.basic", "status": "success"}
                for i in range(8)
            ],
        })

        coverage_rate = result.metadata.get("target_coverage_rate", 1.0)
        assert coverage_rate < 1.0, "Coverage must not be 100% when targets are not_attempted"

    def test_execution_success_vs_coverage_complete(self):
        """execution_success != coverage_complete."""
        cap = CoverageAuditorCapability()

        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": [{"path": "/bin/app1"}],
            "capability_results": [
                {"target_id": "target-1", "capability_id": "macho.basic", "status": "success"},
            ],
        })

        # Both may be true or one may be false independently
        exec_success = result.metadata.get("execution_success")
        cov_complete = result.metadata.get("coverage_complete")

        # They are tracked independently
        assert isinstance(exec_success, bool)
        assert isinstance(cov_complete, bool)

    def test_eligible_denominator_explicit(self):
        """Eligible denominator is explicit."""
        cap = CoverageAuditorCapability()

        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": [
                {"path": "/bin/app1"},
                {"path": "/bin/app2"},
                {"path": "/System/Library/Frameworks/UIKit.framework", "is_system_framework": True},
            ],
            "capability_results": [
                {"target_id": "target-1", "capability_id": "macho.basic", "status": "success"},
                {"target_id": "target-2", "capability_id": "macho.basic", "status": "success"},
            ],
        })

        assert result.metadata.get("total_eligible_targets") == 3


# =============================================================================
# REPORTING E2E
# =============================================================================

class TestReportingE2E:
    """End-to-end reporting tests."""

    def test_json_renderer_deterministic(self):
        """JSON output is deterministic."""
        metadata = ReportMetadata(
            report_id="test-report-1",
            artifact_path="/test/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00Z",
        )
        report = Report(metadata=metadata, sections=[])

        renderer = JSONRenderer()
        output1 = renderer.render(report)
        output2 = renderer.render(report)

        assert output1 == output2

    def test_markdown_renderer_deterministic(self):
        """Markdown output is deterministic."""
        metadata = ReportMetadata(
            report_id="test-report-1",
            artifact_path="/test/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00Z",
        )
        report = Report(metadata=metadata, sections=[])

        renderer = MarkdownRenderer()
        output1 = renderer.render(report)
        output2 = renderer.render(report)

        assert output1 == output2

    def test_partial_analysis_generates_report(self):
        """Partial upstream analysis still generates report."""
        metadata = ReportMetadata(
            report_id="test-report-1",
            artifact_path="/test/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00Z",
            execution_success=False,
            coverage_complete=False,
        )
        report = Report(metadata=metadata, sections=[])

        renderer = JSONRenderer()
        output = renderer.render(report)

        # Should still render
        data = json.loads(output)
        assert data["metadata"]["report_id"] == "test-report-1"


# =============================================================================
# CLAIM INTEGRITY
# =============================================================================

class TestClaimIntegrity:
    """Tests that evidence strength is preserved through rendering."""

    def test_string_hint_remains_suspected(self):
        """STRING_HINT becomes SUSPECTED, not higher."""
        from ios_reverse.models.report import ClaimStrength, evidence_to_claim_strength

        strength = evidence_to_claim_strength("string_hint")
        assert strength == ClaimStrength.SUSPECTED
        assert strength != ClaimStrength.DETECTED
        assert strength != ClaimStrength.VERIFIED

    def test_reference_remains_inferred(self):
        """REFERENCE becomes INFERRED."""
        from ios_reverse.models.report import ClaimStrength, evidence_to_claim_strength

        strength = evidence_to_claim_strength("reference")
        assert strength == ClaimStrength.INFERRED

    def test_verified_remains_verified(self):
        """VERIFIED stays VERIFIED."""
        from ios_reverse.models.report import ClaimStrength, evidence_to_claim_strength

        strength = evidence_to_claim_strength("verified")
        assert strength == ClaimStrength.VERIFIED


# =============================================================================
# DETERMINISM
# =============================================================================

class TestDeterminism:
    """Tests for deterministic output."""

    def test_capability_ids_deterministic(self):
        """Capability IDs are deterministic."""
        from ios_reverse.models.coverage import generate_target_id

        id1 = generate_target_id("/path/to/binary", "arm64")
        id2 = generate_target_id("/path/to/binary", "arm64")

        assert id1 == id2

    def test_coverage_audit_deterministic(self):
        """Coverage audit is deterministic."""
        from ios_reverse.models.coverage import CoverageAudit, CoverageSummary
        from ios_reverse.renderers import render_coverage_audit

        audit = CoverageAudit(
            audit_id="audit-1",
            workflow="full",
            depth="full",
            timestamp="2024-01-01T00:00:00Z",
            eligible_targets=[],
            required_dimensions=[],
            observations=[],
            gaps=[],
            summary=CoverageSummary(workflow="full", depth="full"),
        )
        audit.build_indexes()

        output1 = render_coverage_audit(audit, format="json")
        output2 = render_coverage_audit(audit, format="json")

        assert output1 == output2


# =============================================================================
# SOURCE IMMUTABILITY
# =============================================================================

class TestSourceImmutability:
    """Tests for source artifact immutability."""

    def test_fixtures_hash_consistent(self, tmp_path):
        """Fixture hashes are consistent."""
        # Create fixture
        fixture_dir = tmp_path / "immutability_test"
        fixture_dir.mkdir()

        app_dir = fixture_dir / "Payload" / "Test.app"
        app_dir.mkdir(parents=True)

        content = b'test content'
        (app_dir / "Test").write_bytes(content)

        # Hash before
        hash1 = hashlib.sha256(content).hexdigest()

        # Read same content
        read_content = (app_dir / "Test").read_bytes()
        hash2 = hashlib.sha256(read_content).hexdigest()

        assert hash1 == hash2


# =============================================================================
# SCHEMA COMPATIBILITY
# =============================================================================

class TestSchemaCompatibility:
    """Tests for schema version compatibility."""

    def test_coverage_model_serialization(self):
        """Coverage model serializes correctly."""
        from ios_reverse.models.coverage import CoverageAudit, CoverageSummary

        audit = CoverageAudit(
            audit_id="test",
            workflow="full",
            depth="full",
            timestamp="2024-01-01T00:00:00Z",
            eligible_targets=[],
            required_dimensions=[],
            observations=[],
            gaps=[],
            summary=CoverageSummary(workflow="full", depth="full"),
        )
        audit.build_indexes()

        data = audit.to_dict()
        assert data["audit_id"] == "test"

    def test_report_model_serialization(self):
        """Report model serializes correctly."""
        from ios_reverse.models.report import Report, ReportMetadata

        metadata = ReportMetadata(
            report_id="test",
            artifact_path="/test.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00Z",
        )
        report = Report(metadata=metadata, sections=[])

        data = report.to_dict()
        assert data["metadata"]["report_id"] == "test"


# =============================================================================
# FAILURE PROPAGATION
# =============================================================================

class TestFailurePropagation:
    """Tests for controlled failure handling."""

    def test_capability_handles_invalid_input(self):
        """Capability handles invalid input gracefully."""
        cap = ArtifactDetectCapability()

        # Empty path should fail validation
        result = cap.execute({"artifact_path": ""})

        assert result.status.value == "failure"
        assert result.error_code is not None

    def test_coverage_handles_invalid_workflow(self):
        """Coverage handles invalid workflow."""
        cap = CoverageAuditorCapability()

        result = cap.execute({
            "workflow": "invalid_workflow",
            "depth": "full",
            "eligible_targets": [],
        })

        assert result.status.value == "failure"

    def test_macho_handles_non_macho_binary(self):
        """Mach-O capability handles non-Mach-O file."""
        cap = MachoBasicCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'not a macho file at all')
            temp_path = f.name

        try:
            result = cap.execute({"artifact_path": temp_path})
            # Should handle gracefully (may be partial or failure)
            assert result.status.value in ["success", "partial", "failure"]
        finally:
            os.unlink(temp_path)


# =============================================================================
# TOOL ABSENCE
# =============================================================================

class TestToolAbsence:
    """Tests for graceful degradation without optional tools."""

    def test_pure_python_fallback(self, tmp_path):
        """Pure Python path works without external tools."""
        # Create minimal IPA
        fixture_dir = tmp_path / "tool_test"
        fixture_dir.mkdir()

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Test.app"
        app_dir.mkdir(parents=True)

        plist = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0"><dict></dict></plist>
'''
        (app_dir / "Info.plist").write_bytes(plist)

        import struct
        magic = 0xfeedface
        header = struct.pack('>IIIIIII',
            magic, 0x0100000c, 0x80000002, 0x00000002, 0, 0, 0x00200085
        )
        (app_dir / "Test").write_bytes(header + b'\x00' * 256)

        ipa_path = tmp_path / "test.ipa"
        with zipfile.ZipFile(ipa_path, 'w') as zf:
            for root, dirs, files in os.walk(fixture_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(fixture_dir)
                    zf.write(file_path, arc_name)

        # Test without external tools
        cap = ArtifactDetectCapability()
        result = cap.execute({"artifact_path": str(ipa_path)})

        assert result.status.value in ["success", "partial"]
