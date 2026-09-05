"""
E2E Test Fixture Generator for P04.8 Integration Gate.

Creates deterministic synthetic IPA fixtures for integration testing.
"""

import hashlib
import json
import os
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class MachOHeader:
    """Simple Mach-O header for testing."""
    magic: int = 0xfeedface  # 32-bit Mach-O
    cputype: int = 0x0100000c  # ARM64
    cpusubtype: int = 0x80000002  # ARM64 all variants
    filetype: int = 0x00000002  # MH_EXECUTE
    ncmds: int = 0
    sizeofcmds: int = 0
    flags: int = 0


class FixtureGenerator:
    """Generate deterministic test fixtures."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_minimal_ipa(self) -> Path:
        """
        Fixture A: Minimal iOS App.

        Contains:
        - Minimal.app/Info.plist
        - Minimal.app/Minimal (simple Mach-O)
        """
        fixture_dir = self.output_dir / "fixture_a_minimal"
        fixture_dir.mkdir(exist_ok=True)

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Minimal.app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Create Info.plist
        plist = self._create_info_plist("Minimal", bundle_id="com.test.minimal")
        (app_dir / "Info.plist").write_bytes(plist)

        # Create executable Mach-O
        macho = self._create_simple_macho()
        (app_dir / "Minimal").write_bytes(macho)

        # Create ZIP (IPA)
        ipa_path = fixture_dir.with_suffix(".ipa")
        self._create_ipa(fixture_dir, ipa_path)

        return ipa_path

    def generate_mixed_ipa(self) -> Path:
        """
        Fixture B: Mixed Application with multiple components.

        Contains:
        - Mixed.app/
          - Info.plist
          - Mixed (main executable)
          - Frameworks/
            - Networking.framework/
            - Shared.framework/
          - PlugIns/
            - Widget.appex/
        - libExample.dylib
        """
        fixture_dir = self.output_dir / "fixture_b_mixed"
        fixture_dir.mkdir(exist_ok=True)

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Mixed.app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Main app Info.plist
        plist = self._create_info_plist("Mixed", bundle_id="com.test.mixed")
        (app_dir / "Info.plist").write_bytes(plist)

        # Main executable with evidence
        macho = self._create_macho_with_evidence()
        (app_dir / "Mixed").write_bytes(macho)

        # Frameworks
        fw_dir = app_dir / "Frameworks"
        fw_dir.mkdir(exist_ok=True)

        # Networking.framework
        net_fw = fw_dir / "Networking.framework"
        net_fw.mkdir(exist_ok=True)
        self._create_framework(net_fw, "Networking", "com.test.networking")
        # Networking dylib with evidence
        net_macho = self._create_framework_dylib("Networking")
        (net_fw / "Networking").write_bytes(net_macho)

        # Shared.framework
        shared_fw = fw_dir / "Shared.framework"
        shared_fw.mkdir(exist_ok=True)
        self._create_framework(shared_fw, "Shared", "com.test.shared")

        # PlugIns
        plugins_dir = app_dir / "PlugIns"
        plugins_dir.mkdir(exist_ok=True)

        # Widget extension
        widget_ext = plugins_dir / "Widget.appex"
        widget_ext.mkdir(exist_ok=True)
        self._create_extension(widget_ext, "Widget", "com.test.widget")

        # libExample.dylib
        dylib = self._create_dylib()
        (app_dir / "libExample.dylib").write_bytes(dylib)

        # Create ZIP (IPA)
        ipa_path = fixture_dir.with_suffix(".ipa")
        self._create_ipa(fixture_dir, ipa_path)

        return ipa_path

    def generate_partial_ipa(self) -> Path:
        """
        Fixture C: Partial/Broken Application.

        Contains:
        - Partial.app/ (valid)
        - Broken.framework/ (malformed)
        """
        fixture_dir = self.output_dir / "fixture_c_partial"
        fixture_dir.mkdir(exist_ok=True)

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Partial.app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Valid app
        plist = self._create_info_plist("Partial", bundle_id="com.test.partial")
        (app_dir / "Info.plist").write_bytes(plist)

        # Valid executable
        macho = self._create_simple_macho()
        (app_dir / "Partial").write_bytes(macho)

        # Broken framework (truncated)
        broken_fw = app_dir / "Frameworks"
        broken_fw.mkdir(exist_ok=True)
        (broken_fw / "Broken.framework").mkdir(exist_ok=True)
        # Write truncated/garbage instead of valid Mach-O
        (broken_fw / "Broken.framework" / "Broken").write_bytes(b"TRUNCATED" * 10)

        # Create ZIP (IPA)
        ipa_path = fixture_dir.with_suffix(".ipa")
        self._create_ipa(fixture_dir, ipa_path)

        return ipa_path

    def generate_fat_ipa(self) -> Path:
        """
        Fixture D: Fat/Universal Mach-O.

        Contains:
        - Fat.app/ with fat Mach-O containing arm64 and armv7 slices
        """
        fixture_dir = self.output_dir / "fixture_d_fat"
        fixture_dir.mkdir(exist_ok=True)

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "Fat.app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Info.plist
        plist = self._create_info_plist("Fat", bundle_id="com.test.fat")
        (app_dir / "Info.plist").write_bytes(plist)

        # Fat Mach-O (arm64 + armv7)
        fat_macho = self._create_fat_macho()
        (app_dir / "Fat").write_bytes(fat_macho)

        # Create ZIP (IPA)
        ipa_path = fixture_dir.with_suffix(".ipa")
        self._create_ipa(fixture_dir, ipa_path)

        return ipa_path

    def generate_pure_swift_ipa(self) -> Path:
        """
        Fixture E: Pure Swift Application.

        Contains only Swift symbols, no ObjC.
        """
        fixture_dir = self.output_dir / "fixture_e_swift"
        fixture_dir.mkdir(exist_ok=True)

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "SwiftApp.app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Info.plist
        plist = self._create_info_plist("SwiftApp", bundle_id="com.test.swift")
        (app_dir / "Info.plist").write_bytes(plist)

        # Swift-only executable
        macho = self._create_swift_only_macho()
        (app_dir / "SwiftApp").write_bytes(macho)

        # Create ZIP (IPA)
        ipa_path = fixture_dir.with_suffix(".ipa")
        self._create_ipa(fixture_dir, ipa_path)

        return ipa_path

    def generate_pure_objc_ipa(self) -> Path:
        """
        Fixture F: Pure Objective-C Application.

        Contains only ObjC symbols.
        """
        fixture_dir = self.output_dir / "fixture_f_objc"
        fixture_dir.mkdir(exist_ok=True)

        payload_dir = fixture_dir / "Payload"
        app_dir = payload_dir / "ObjCApp.app"
        app_dir.mkdir(parents=True, exist_ok=True)

        # Info.plist
        plist = self._create_info_plist("ObjCApp", bundle_id="com.test.objc")
        (app_dir / "Info.plist").write_bytes(plist)

        # ObjC-only executable
        macho = self._create_objc_only_macho()
        (app_dir / "ObjCApp").write_bytes(macho)

        # Create ZIP (IPA)
        ipa_path = fixture_dir.with_suffix(".ipa")
        self._create_ipa(fixture_dir, ipa_path)

        return ipa_path

    def _create_info_plist(self, name: str, bundle_id: str) -> bytes:
        """Create a minimal Info.plist."""
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{name}</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
</dict>
</plist>
'''
        return plist_content.encode('utf-8')

    def _create_simple_macho(self) -> bytes:
        """Create a simple valid Mach-O for minimal fixture."""
        # Mach-O header (32-bit)
        magic = 0xfeedface
        cputype = 0x0100000c  # ARM64
        cpusubtype = 0x80000002
        filetype = 0x00000002  # MH_EXECUTE
        ncmds = 0
        sizeofcmds = 0
        flags = 0x00200085  # MH_NO_HEAP_EXECUTE | MH_ALLOW_STACK_EXECUTION

        header = struct.pack('>IIIIIII',
            magic, cputype, cpusubtype, filetype,
            ncmds, sizeofcmds, flags
        )

        # Some padding to make it look like a binary
        content = b'\x00' * 256

        return header + content

    def _create_macho_with_evidence(self) -> bytes:
        """
        Create Mach-O with evidence for various detection types.
        Includes ObjC, Swift, network, crypto, and anti-analysis indicators.
        """
        # Mach-O header
        magic = 0xfeedface
        cputype = 0x0100000c  # ARM64
        cpusubtype = 0x80000002
        filetype = 0x00000002  # MH_EXECUTE
        ncmds = 0
        sizeofcmds = 0
        flags = 0x00200085

        header = struct.pack('>IIIIIII',
            magic, cputype, cpusubtype, filetype,
            ncmds, sizeofcmds, flags
        )

        # Embedded strings with evidence at different strengths
        # String hints (weak evidence)
        strings = b''
        strings += b'/Applications/Cydia.app/System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist\x00'  # Jailbreak indicator
        strings += b'https://api.example.com/v1/users\x00'  # Network endpoint hint
        strings += b'AES-256-CBC\x00'  # Crypto string hint
        strings += b'ptrace\x00'  # Debugger detection reference
        strings += b'_CCCrypt\x00'  # CommonCrypto import
        strings += b'_objc_msgSend\x00'  # ObjC reference
        strings += b'_T0Cs16SecureStorage\x00'  # Swift mangled name
        strings += b'NSURLSession\x00'  # Network framework reference
        strings += b'kSecAttrKeyTypeECSECPrimeRandom\x00'  # Crypto reference
        strings += b' SecItemAdd\x00'  # Keychain reference

        # Pad to reasonable size
        content = b'\x00' * 512 + strings

        return header + content

    def _create_framework(self, fw_dir: Path, name: str, bundle_id: str):
        """Create a framework directory structure."""
        plist = self._create_info_plist(name, bundle_id)
        (fw_dir / "Info.plist").write_bytes(plist)

    def _create_framework_dylib(self, name: str) -> bytes:
        """Create framework dylib with evidence."""
        # Similar to main executable but smaller
        magic = 0xfeedface
        cputype = 0x0100000c
        cpusubtype = 0x80000002
        filetype = 0x00000008  # MH_DYLIB
        ncmds = 0
        sizeofcmds = 0
        flags = 0

        header = struct.pack('>IIIIIII',
            magic, cputype, cpusubtype, filetype,
            ncmds, sizeofcmds, flags
        )

        strings = b''
        strings += b'NSURL\x00'
        strings += b'_T05Network\x00'

        content = b'\x00' * 128 + strings

        return header + content

    def _create_extension(self, ext_dir: Path, name: str, bundle_id: str):
        """Create an extension directory structure."""
        plist = self._create_info_plist(name, bundle_id)
        (ext_dir / "Info.plist").write_bytes(plist)

        # Extension executable
        macho = self._create_simple_macho()
        (ext_dir / name).write_bytes(macho)

    def _create_dylib(self) -> bytes:
        """Create a standalone dylib."""
        magic = 0xfeedface
        cputype = 0x0100000c
        cpusubtype = 0x80000002
        filetype = 0x00000006  # MH_DYLIB
        ncmds = 0
        sizeofcmds = 0
        flags = 0

        header = struct.pack('>IIIIIII',
            magic, cputype, cpusubtype, filetype,
            ncmds, sizeofcmds, flags
        )

        strings = b'libExample_dylib\x00'

        content = b'\x00' * 128 + strings

        return header + content

    def _create_fat_macho(self) -> bytes:
        """Create a fat/Universal Mach-O with arm64 and armv7."""
        # Fat header
        magic = 0xcafebabe
        nfat_arch = 2
        fat_header = struct.pack('>II', magic, nfat_arch)

        # ARM64 slice
        arm64_cpu_type = 0x0100000c
        arm64_cpu_sub = 0x80000002
        arm64_offset = 32  # Header + fat arch entries
        arm64_size = 256
        arm64_align = 14  # 2^14 = 16384

        arm64_entry = struct.pack('>IIIIII',
            arm64_cpu_type, arm64_cpu_sub, arm64_offset, arm64_size, arm64_align, 0
        )

        # ARMv7 slice
        armv7_cpu_type = 0x00000007
        armv7_cpu_sub = 0x00000009
        armv7_offset = arm64_offset + arm64_size
        armv7_size = 256
        armv7_align = 14

        armv7_entry = struct.pack('>IIIIII',
            armv7_cpu_type, armv7_cpu_sub, armv7_offset, armv7_size, armv7_align, 0
        )

        # Slice content (simple)
        arm64_content = self._create_simple_macho()
        armv7_content = self._create_simple_macho()

        return fat_header + arm64_entry + armv7_entry + arm64_content + armv7_content

    def _create_swift_only_macho(self) -> bytes:
        """Create Mach-O with only Swift evidence."""
        magic = 0xfeedface
        cputype = 0x0100000c
        cpusubtype = 0x80000002
        filetype = 0x00000002
        ncmds = 0
        sizeofcmds = 0
        flags = 0x00200085

        header = struct.pack('>IIIIIII',
            magic, cputype, cpusubtype, filetype,
            ncmds, sizeofcmds, flags
        )

        # Swift mangled names only
        strings = b''
        strings += b'_T05MyApp8StorageV\x00'
        strings += b'_T013SharedCode7StorageV\x00'
        strings += b'_swift_getGenericType\x00'
        strings += b'_T09Foundation8DataTypeVAC\x00'

        content = b'\x00' * 256 + strings

        return header + content

    def _create_objc_only_macho(self) -> bytes:
        """Create Mach-O with only ObjC evidence."""
        magic = 0xfeedface
        cputype = 0x0100000c
        cpusubtype = 0x80000002
        filetype = 0x00000002
        ncmds = 0
        sizeofcmds = 0
        flags = 0x00200085

        header = struct.pack('>IIIIIII',
            magic, cputype, cpusubtype, filetype,
            ncmds, sizeofcmds, flags
        )

        # ObjC selectors and class names
        strings = b''
        strings += b'NSObject\x00'
        strings += b'NSString\x00'
        strings += b'NSArray\x00'
        strings += b'NSDictionary\x00'
        strings += b'deleteRowAtIndexPath:\x00'
        strings += b'initWithFrame:\x00'
        strings += b'viewDidLoad\x00'
        strings += b'_objc_msgSend\x00'
        strings += b'_objc_retain\x00'
        strings += b'_objc_release\x00'

        content = b'\x00' * 256 + strings

        return header + content

    def _create_ipa(self, source_dir: Path, output_path: Path):
        """Create IPA (ZIP) from directory."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.endswith('.ipa'):
                        continue
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(source_dir)
                    zf.write(file_path, arc_name)


def generate_all_fixtures(output_dir: str) -> Dict[str, Path]:
    """Generate all E2E fixtures."""
    generator = FixtureGenerator(Path(output_dir))

    fixtures = {}
    fixtures['A_minimal'] = generator.generate_minimal_ipa()
    fixtures['B_mixed'] = generator.generate_mixed_ipa()
    fixtures['C_partial'] = generator.generate_partial_ipa()
    fixtures['D_fat'] = generator.generate_fat_ipa()
    fixtures['E_swift'] = generator.generate_pure_swift_ipa()
    fixtures['F_objc'] = generator.generate_pure_objc_ipa()

    return fixtures


if __name__ == '__main__':
    fixtures = generate_all_fixtures(__file__)
    for name, path in fixtures.items():
        print(f"Generated {name}: {path}")
