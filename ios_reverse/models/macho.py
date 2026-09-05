"""
Normalized Mach-O Model for IOS REVERSE KAISER.

This module defines a stable, tool-agnostic representation of Mach-O binaries.
Do not leak tool-specific formats into this model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime


class MachOType(Enum):
    """Mach-O binary type."""
    UNKNOWN = "unknown"
    THIN = "thin"
    FAT = "fat"
    FAT_MAGIC_32 = "fat.magic32"
    FAT_MAGIC_64 = "fat.magic64"


class FileType(Enum):
    """Mach-O file type."""
    UNKNOWN = "unknown"
    EXECUTABLE = "executable"
    OBJECT = "object"
    DYLIB = "dylib"
    DYLINKER = "dylinker"
    BUNDLE = "bundle"
    FRAMEWORK = "framework"
    PRELOAD = "preload"


class CPUType(Enum):
    """CPU architecture types."""
    UNKNOWN = "unknown"
    ANY = "any"
    VAX = "vax"
    MC680x0 = "mc680x0"
    I386 = "i386"
    X86_64 = "x86_64"
    X86_64_H = "x86_64h"
    MC98000 = "mc98000"
    HPPA = "hppa"
    ARM = "arm"
    ARM64 = "arm64"
    ARM64_32 = "arm64_32"
    SPARC = "sparc"
    MIPS = "mips"
    I860 = "i860"
    POWERPC = "powerpc"
    POWERPC64 = "powerpc64"


class Bitness(Enum):
    """Bitness indicator."""
    UNKNOWN = "unknown"
    BIT32 = "32"
    BIT64 = "64"


class Endianness(Enum):
    """Endianness."""
    UNKNOWN = "unknown"
    LITTLE = "little"
    BIG = "big"


class StripStatus(Enum):
    """Symbol stripping status."""
    UNKNOWN = "unknown"
    STRIPPED = "stripped"
    SYMBOLS_STripped = "symbols_stripped"
    SYMBOLS_PRESENT = "symbols_present"
    DY_SYMS_PRESENT = "dy_syms_present"
    DY_SYMS_STRIPPED = "dy_syms_stripped"


@dataclass
class CPUMetadata:
    """CPU type/subtype metadata."""
    cpu_type: str = "unknown"
    cpu_subtype: str = "unknown"
    cpu_type_hex: Optional[int] = None
    cpu_subtype_hex: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "cpu_type": self.cpu_type,
            "cpu_subtype": self.cpu_subtype,
            "cpu_type_hex": self.cpu_type_hex,
            "cpu_subtype_hex": self.cpu_subtype_hex,
        }


@dataclass
class UUIDInfo:
    """UUID information."""
    uuid: str = "unknown"
    source: str = "unknown"  # load_command, file_header, etc.

    def to_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "source": self.source,
        }


@dataclass
class SegmentInfo:
    """Segment information."""
    name: str = "unknown"
    vmaddr: int = 0
    vmsize: int = 0
    fileoff: int = 0
    filesize: int = 0
    maxprot: int = 0
    initprot: int = 0
    nsects: int = 0
    flags: int = 0
    sections: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "vmaddr": hex(self.vmaddr),
            "vmsize": hex(self.vmsize),
            "fileoff": hex(self.fileoff),
            "filesize": hex(self.filesize),
            "maxprot": self.maxprot,
            "initprot": self.initprot,
            "nsects": self.nsects,
            "flags": hex(self.flags),
            "sections": self.sections,
        }


@dataclass
class LibraryDependency:
    """Dynamic library dependency."""
    name: str = "unknown"
    install_name: str = "unknown"
    version: str = "unknown"
    weak: bool = False
    reexport: bool = False
    lazy: bool = False
    cmd_type: str = "unknown"  # LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, etc.

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "install_name": self.install_name,
            "version": self.version,
            "weak": self.weak,
            "reexport": self.reexport,
            "lazy": self.lazy,
            "cmd_type": self.cmd_type,
        }


@dataclass
class RPath:
    """Run path entry."""
    path: str = "unknown"
    cmd_type: str = "LC_RPATH"

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "cmd_type": self.cmd_type,
        }


@dataclass
class LoadCommand:
    """Generic load command."""
    cmd_type: str = "unknown"
    cmd_offset: int = 0
    cmd_size: int = 0
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "cmd_type": self.cmd_type,
            "cmd_offset": self.cmd_offset,
            "cmd_size": self.cmd_size,
            "data": self.data,
        }


@dataclass
class VersionInfo:
    """Minimum OS version information."""
    platform: str = "unknown"
    min_version: str = "unknown"
    sdk_version: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "min_version": self.min_version,
            "sdk_version": self.sdk_version,
        }


@dataclass
class EncryptionInfo:
    """Encryption information."""
    encrypted: bool = False
    crypt_id: int = 0
    cryptoff: int = 0
    cryptsize: int = 0
    crypttype: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "encrypted": self.encrypted,
            "crypt_id": self.crypt_id,
            "cryptoff": hex(self.cryptoff),
            "cryptsize": hex(self.cryptsize),
            "crypttype": self.crypttype,
        }


@dataclass
class CodeSignature:
    """Code signature information."""
    present: bool = False
    location: str = "unknown"
    offset: int = 0
    size: int = 0

    def to_dict(self) -> dict:
        return {
            "present": self.present,
            "location": self.location,
            "offset": hex(self.offset),
            "size": self.size,
        }


@dataclass
class BuildVersion:
    """Build version information."""
    platform: str = "unknown"
    minos: str = "unknown"
    sdk: str = "unknown"
    ntools: int = 0

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "minos": self.minos,
            "sdk": self.sdk,
            "ntools": self.ntools,
        }


@dataclass
class EntryPoint:
    """Entry point information."""
    present: bool = False
    address: str = "unknown"
    source: str = "unknown"  # LC_MAIN, computed, etc.

    def to_dict(self) -> dict:
        return {
            "present": self.present,
            "address": self.address,
            "source": self.source,
        }


@dataclass
class MachOSlice:
    """Single Mach-O slice (architecture in fat or standalone)."""
    architecture: str = "unknown"
    cpu_metadata: CPUMetadata = field(default_factory=CPUMetadata)
    bitness: Bitness = Bitness.UNKNOWN
    endianness: Endianness = Endianness.UNKNOWN
    file_offset: int = 0
    size: int = 0
    align: int = 0
    slice_hash: str = ""

    # Extracted slice data
    data_path: Optional[str] = None
    extracted: bool = False

    # Slice-level analysis
    uuid: Optional[UUIDInfo] = None
    entry_point: EntryPoint = field(default_factory=EntryPoint)
    segments: List[SegmentInfo] = field(default_factory=list)
    load_commands: List[LoadCommand] = field(default_factory=list)
    libraries: List[LibraryDependency] = field(default_factory=list)
    rpaths: List[RPath] = field(default_factory=list)
    version_info: Optional[VersionInfo] = None
    encryption: EncryptionInfo = field(default_factory=EncryptionInfo)
    code_signature: CodeSignature = field(default_factory=CodeSignature)
    build_version: Optional[BuildVersion] = None

    def to_dict(self) -> dict:
        return {
            "architecture": self.architecture,
            "cpu_metadata": self.cpu_metadata.to_dict(),
            "bitness": self.bitness.value,
            "endianness": self.endianness.value,
            "file_offset": hex(self.file_offset),
            "size": hex(self.size),
            "align": self.align,
            "slice_hash": self.slice_hash,
            "data_path": self.data_path,
            "extracted": self.extracted,
            "uuid": self.uuid.to_dict() if self.uuid else None,
            "entry_point": self.entry_point.to_dict(),
            "segments": [s.to_dict() for s in self.segments],
            "load_commands": [lc.to_dict() for lc in self.load_commands],
            "libraries": [lib.to_dict() for lib in self.libraries],
            "rpaths": [rp.to_dict() for rp in self.rpaths],
            "version_info": self.version_info.to_dict() if self.version_info else None,
            "encryption": self.encryption.to_dict(),
            "code_signature": self.code_signature.to_dict(),
            "build_version": self.build_version.to_dict() if self.build_version else None,
        }


@dataclass
class MachOModel:
    """
    Normalized Mach-O model.

    This is the canonical representation used by all capabilities.
    Tool-specific formats are normalized to this model.
    """
    # Artifact identity
    artifact_path: str = ""
    artifact_hash: str = ""

    # Binary type
    macho_type: MachOType = MachOType.UNKNOWN
    file_type: FileType = FileType.UNKNOWN

    # Fat binary info
    is_fat: bool = False
    slice_count: int = 0
    slices: List[MachOSlice] = field(default_factory=list)

    # Stripping status
    strip_status: StripStatus = StripStatus.UNKNOWN

    # Raw size
    file_size: int = 0

    # Warnings/limitations
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # Metadata from primary slice (for thin binaries)
    primary: Optional[MachOSlice] = None

    def to_dict(self) -> dict:
        return {
            "artifact_path": self.artifact_path,
            "artifact_hash": self.artifact_hash,
            "macho_type": self.macho_type.value,
            "file_type": self.file_type.value,
            "is_fat": self.is_fat,
            "slice_count": self.slice_count,
            "slices": [s.to_dict() for s in self.slices],
            "strip_status": self.strip_status.value,
            "file_size": self.file_size,
            "warnings": self.warnings,
            "limitations": self.limitations,
            "primary": self.primary.to_dict() if self.primary else None,
        }

    @classmethod
    def from_macho(cls, path: str, data: bytes) -> "MachOModel":
        """Create model from raw Mach-O data."""
        model = cls(artifact_path=path, file_size=len(data))
        return model


# Mach-O magic numbers for detection
MAGIC_VALUES = {
    0xfeedface: {"name": "MH_MAGIC", "bitness": "32", "endian": "little"},
    0xcefaedfe: {"name": "MH_CIGAM", "bitness": "32", "endian": "big"},
    0xfeedfacf: {"name": "MH_MAGIC_64", "bitness": "64", "endian": "little"},
    0xcffaedfe: {"name": "MH_CIGAM_64", "bitness": "64", "endian": "big"},
    0xcafebabe: {"name": "FAT_MAGIC", "bitness": "32", "endian": "big"},
    0xbebafeca: {"name": "FAT_CIGAM", "bitness": "32", "endian": "little"},
    0xcafedbad: {"name": "FAT_MAGIC_64", "bitness": "64", "endian": "big"},
    0xaddabadc: {"name": "FAT_CIGAM_64", "bitness": "64", "endian": "little"},
}

# CPU type mappings
CPU_TYPES = {
    0x01: "CPU_TYPE_ANY",
    0x06: "CPU_TYPE_VAX",
    0x07: "CPU_TYPE_MC680x0",
    0x07 << 24: "CPU_TYPE_MC680x0",  # Actual value
    0x0c: "CPU_TYPE_I386",
    0x01000007: "CPU_TYPE_MC680x0",
    0x10000007: "CPU_TYPE_MC680x0",
    0x1000000c: "CPU_TYPE_X86",
    0x0100000c: "CPU_TYPE_X86",
    0x0100007b: "CPU_TYPE_X86_64",
    0x0100007c: "CPU_TYPE_X86_64H",
    0x0100000d: "CPU_TYPE_X86_64",
    0x0000000d: "CPU_TYPE_X86_64",
    0x01000014: "CPU_TYPE_MC98000",
    0x00000014: "CPU_TYPE_MC98000",
    0x00000015: "CPU_TYPE_HPPA",
    0x00000018: "CPU_TYPE_SPARC",
    0x0000001a: "CPU_TYPE_I860",
    0x0000001b: "CPU_TYPE_MIPS",
    0x00000012: "CPU_TYPE_MIPS",
    0x00000020: "CPU_TYPE_POWERPC",
    0x01000020: "CPU_TYPE_POWERPC64",
    0x00000006: "CPU_TYPE_ARM",
    0x0000000c: "CPU_TYPE_ARM",
    0x00000012: "CPU_TYPE_ARM",
    0x0000000a: "CPU_TYPE_ARM",
    0x0100000c: "CPU_TYPE_ARM",
    0x0100000a: "CPU_TYPE_ARM64",
    0x0000000a: "CPU_TYPE_ARM64",
    0x0000001c: "CPU_TYPE_ARM64",
    0x0100001c: "CPU_TYPE_ARM64",
    0x0000001d: "CPU_TYPE_ARM64_32",
    0x0100001d: "CPU_TYPE_ARM64_32",
}

# Load command types
LC_TYPES = {
    0x01: "LC_SEGMENT",
    0x02: "LC_SYMTAB",
    0x03: "LC_SYMSEG",
    0x04: "LC_THREAD",
    0x05: "LC_UNIXTHREAD",
    0x06: "LC_LOADFVMLIB",
    0x07: "LC_IDFVMLIB",
    0x08: "LC_IDENT",
    0x09: "LC_FVMFILE",
    0x0a: "LC_PREPAGE",
    0x0b: "LC_DYSYMTAB",
    0x0c: "LC_LOAD_DYLIB",
    0x0d: "LC_ID_DYLIB",
    0x0e: "LC_LOAD_DYLINKER",
    0x0f: "LC_ID_DYLINKER",
    0x10: "LC_PREBOUND_DYLIB",
    0x11: "LC_ROUTINES",
    0x12: "LC_SUB_FRAMEWORK",
    0x13: "LC_SUB_UMBRELLA",
    0x14: "LC_SUB_CLIENT",
    0x15: "LC_SUB_LIBRARY",
    0x16: "LC_TWOLEVEL_HINTS",
    0x17: "LC_PREBIND_CKSUM",
    0x18: "LC_LOAD_WEAK_DYLIB",
    0x19: "LC_SEGMENT_64",
    0x1a: "LC_ROUTINES_64",
    0x1b: "LC_UUID",
    0x1c: "LC_RPATH",
    0x1d: "LC_CODE_SIGNATURE",
    0x1e: "LC_SEGMENT_SPLIT_INFO",
    0x1f: "LC_REEXPORT_DYLIB",
    0x20: "LC_LAZY_LOAD_DYLIB",
    0x21: "LC_ENCRYPTION_INFO",
    0x22: "LC_TOPLEVEL_APIS",
    0x23: "LC_FILESET_ENTRY",
    0x24: "LC_BUILD_VERSION",
    0x80000018: "LC_RPATH",  # 64-bit variant
    0x8000001c: "LC_CODE_SIGNATURE",  # 64-bit variant
    0x80000021: "LC_ENCRYPTION_INFO_64",
    0x80000022: "LC_LINKER_OPTION",
    0x80000023: "LC_LINKER_OPTIMIZATION_HINT",
    0x80000024: "LC_TWOLEVEL_HINTS_64",
    0x80000025: "LC_MAIN",
    0x80000026: "LC_DATA_IN_CODE",
    0x80000027: "LC_SOURCE_VERSION",
    0x80000028: "LC_DYLIB_CODE_SIGN_DRS",
    0x80000029: "LC_ENCRYPTION_INFO_64",
    0x8000002a: "LC_LINKER",
    0x8000002b: "LC_VERSION_MIN_MACOSX",
    0x8000002c: "LC_VERSION_MIN_IPHONEOS",
    0x80000030: "LC_VERSION_MIN_TVOS",
    0x80000031: "LC_VERSION_MIN_WATCHOS",
}

# File type mappings
MH_FILE_TYPES = {
    0x01: "MH_OBJECT",
    0x02: "MH_EXECUTE",
    0x03: "MH_FVMLIB",
    0x04: "MH_CORE",
    0x05: "MH_PRELOAD",
    0x06: "MH_DYLIB",
    0x07: "MH_DYLINKER",
    0x08: "MH_BUNDLE",
    0x09: "MH_DYLIB_STUB",
    0x0a: "MH_DSYM",
    0x0b: "MH_KEXT_BUNDLE",
}

# Platform mappings
PLATFORM_NAMES = {
    0x01: "PLATFORM_MACOS",
    0x02: "PLATFORM_IOS",
    0x03: "PLATFORM_TVOS",
    0x04: "PLATFORM_WATCHOS",
    0x05: "PLATFORM_BRIDGEOS",
    0x06: "PLATFORM_MACCATALYST",
    0x07: "PLATFORM_IOSSIMULATOR",
    0x08: "PLATFORM_TVOSSIMULATOR",
    0x09: "PLATFORM_WATCHOSSIMULATOR",
    0x0a: "PLATFORM_DRIVERKIT",
}
