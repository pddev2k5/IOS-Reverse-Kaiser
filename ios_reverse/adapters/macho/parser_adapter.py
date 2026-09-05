"""
Mach-O Parser Adapter for IOS REVERSE KAISER.

Pure Python Mach-O parser - works on all platforms.
This is the preferred adapter for Mach-O analysis.
"""

from typing import Tuple, Optional, Dict, Any, List
import struct
import hashlib
import os

from ..base import AdapterResult
from ...models.macho import (
    MachOModel, MachOType, FileType, Bitness, Endianness,
    CPUMetadata, UUIDInfo, MachOSlice, SegmentInfo, LibraryDependency,
    RPath, LoadCommand, VersionInfo, EncryptionInfo, CodeSignature,
    BuildVersion, EntryPoint, StripStatus,
    MAGIC_VALUES, CPU_TYPES, LC_TYPES, MH_FILE_TYPES, PLATFORM_NAMES,
)


class MachOParserAdapter:
    """
    Pure Python Mach-O parser adapter.

    This adapter does not depend on any external tools.
    Works on all platforms.
    """

    def __init__(self):
        pass

    @property
    def id(self) -> str:
        return "mach_o_parser"

    def is_available(self) -> bool:
        """Parser is always available."""
        return True

    def parse(
        self,
        path: str,
        compute_hashes: bool = True,
        extract_slices: bool = False
    ) -> AdapterResult:
        """
        Parse a Mach-O file.

        Args:
            path: Path to Mach-O file
            compute_hashes: Compute SHA-256 hashes
            extract_slices: Extract slices as separate files (not implemented)

        Returns:
            AdapterResult with parsed Mach-O model
        """
        if not os.path.exists(path):
            return AdapterResult(
                success=False,
                error=f"File not found: {path}"
            )

        try:
            with open(path, 'rb') as f:
                data = f.read()

            file_size = len(data)

            # Compute artifact hash
            artifact_hash = ""
            if compute_hashes:
                artifact_hash = hashlib.sha256(data).hexdigest()

            # Detect Mach-O type from magic
            magic_bytes = data[:4]
            if len(magic_bytes) < 4:
                return AdapterResult(
                    success=False,
                    error="File too small to contain Mach-O header"
                )

            magic_int = struct.unpack('>I', magic_bytes)[0]
            magic_info = MAGIC_VALUES.get(magic_int)

            if magic_info is None:
                return AdapterResult(
                    success=False,
                    error=f"Not a valid Mach-O file (magic: {hex(magic_int)})",
                    metadata={"magic": hex(magic_int), "is_macho": False}
                )

            model = MachOModel(
                artifact_path=path,
                artifact_hash=artifact_hash,
                file_size=file_size
            )

            # Parse based on magic type
            if magic_info.get("name") in ("FAT_MAGIC", "FAT_CIGAM", "FAT_MAGIC_64", "FAT_CIGAM_64"):
                return self._parse_fat(path, data, model, magic_info, compute_hashes)
            else:
                return self._parse_thin(path, data, model, magic_info, compute_hashes)

        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Parse error: {str(e)}",
                metadata={"exception": type(e).__name__}
            )

    def _parse_fat(
        self,
        path: str,
        data: bytes,
        model: MachOModel,
        magic_info: Dict,
        compute_hashes: bool
    ) -> AdapterResult:
        """Parse fat/universal Mach-O."""
        model.macho_type = MachOType.FAT if magic_info.get("name") == "FAT_MAGIC" else MachOType.FAT
        model.is_fat = True

        # Parse fat header
        # Convert endian string to struct format character
        endian_str = magic_info.get("endian", "little")
        endian_fmt = '>' if endian_str == "big" else '<'  # '>' for big endian, '<' for little endian

        if magic_info.get("name") in ("FAT_MAGIC_64", "FAT_CIGAM_64"):
            # 64-bit fat header
            nfat_arch = struct.unpack(endian_fmt + 'I', data[4:8])[0]
            offset = 8
            arch_fmt = endian_fmt + 'IIIIII'  # cputype, cpusubtype, offset, size, align, reserved
        else:
            # 32-bit fat header
            nfat_arch = struct.unpack(endian_fmt + 'I', data[4:8])[0]
            offset = 8
            arch_fmt = endian_fmt + 'IIII'  # cputype, cpusubtype, offset, size

        slices = []
        for i in range(nfat_arch):
            try:
                arch_data = struct.unpack(arch_fmt, data[offset:offset + struct.calcsize(arch_fmt)])

                cpu_type = arch_data[0]
                cpu_subtype = arch_data[1]
                slice_offset = arch_data[2]
                slice_size = arch_data[3]

                # Determine architecture
                arch = self._get_architecture_name(cpu_type, cpu_subtype)

                # Compute slice hash
                slice_hash = ""
                if compute_hashes and slice_offset + slice_size <= len(data):
                    slice_data = data[slice_offset:slice_offset + slice_size]
                    slice_hash = hashlib.sha256(slice_data).hexdigest()

                # Parse thin header within slice
                if slice_offset + 4 <= len(data):
                    slice_magic = struct.unpack(endian_fmt + 'I', data[slice_offset:slice_offset + 4])[0]
                    slice_magic_info = MAGIC_VALUES.get(slice_magic, {})

                    cpu_meta = CPUMetadata(
                        cpu_type=self._map_cpu_type(cpu_type),
                        cpu_type_hex=cpu_type,
                        cpu_subtype=hex(cpu_subtype),
                        cpu_subtype_hex=cpu_subtype
                    )

                    mach_slice = MachOSlice(
                        architecture=arch,
                        cpu_metadata=cpu_meta,
                        bitness=Bitness.BIT64 if "64" in slice_magic_info.get("name", "") else Bitness.BIT32,
                        endianness=Endianness.LITTLE if slice_magic_info.get("endian") == "little" else Endianness.BIG,
                        file_offset=slice_offset,
                        size=slice_size,
                        slice_hash=slice_hash
                    )

                    # Parse thin Mach-O inside fat
                    self._parse_slice_header(data, slice_offset, mach_slice)

                    slices.append(mach_slice)

                offset += struct.calcsize(arch_fmt)
            except Exception as e:
                model.warnings.append(f"Failed to parse slice {i}: {str(e)}")

        model.slice_count = len(slices)
        model.slices = slices
        model.primary = slices[0] if slices else None

        return AdapterResult(
            success=True,
            artifacts=[path],
            metadata={
                "model": model.to_dict(),
                "is_fat": True,
                "slice_count": len(slices),
                "architectures": [s.architecture for s in slices]
            }
        )

    def _parse_thin(
        self,
        path: str,
        data: bytes,
        model: MachOModel,
        magic_info: Dict,
        compute_hashes: bool
    ) -> AdapterResult:
        """Parse thin Mach-O."""
        model.macho_type = MachOType.THIN

        endian_fmt = '<' if magic_info.get("endian") == "little" else '>'

        # Parse Mach-O header
        # mach_header (32-bit): magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags = 7 * 4 = 28 bytes
        # mach_header_64 (64-bit): adds reserved = 8 * 4 = 32 bytes
        if magic_info.get("bitness") == "64":
            header_fmt = endian_fmt + 'IIIIIIII'  # 8 unsigned ints = 32 bytes
            header_size = 32
        else:
            header_fmt = endian_fmt + 'IIIIIII'  # 7 unsigned ints = 28 bytes
            header_size = 28

        if len(data) < header_size:
            return AdapterResult(
                success=False,
                error="File too small for Mach-O header"
            )

        header = struct.unpack(header_fmt, data[:header_size])

        cpu_type = header[0]
        cpu_subtype = header[1]
        filetype = header[2]
        ncmds = header[3]
        sizeofcmds = header[4]
        flags = header[5]

        # Determine architecture
        arch = self._get_architecture_name(cpu_type, cpu_subtype)

        # Compute slice hash
        slice_hash = ""
        if compute_hashes:
            slice_hash = hashlib.sha256(data).hexdigest()

        # Create slice
        cpu_meta = CPUMetadata(
            cpu_type=self._map_cpu_type(cpu_type),
            cpu_type_hex=cpu_type,
            cpu_subtype=hex(cpu_subtype),
            cpu_subtype_hex=cpu_subtype
        )

        mach_slice = MachOSlice(
            architecture=arch,
            cpu_metadata=cpu_meta,
            bitness=Bitness.BIT64 if magic_info.get("bitness") == "64" else Bitness.BIT32,
            endianness=Endianness.LITTLE if magic_info.get("endian") == "little" else Endianness.BIG,
            file_offset=0,
            size=len(data),
            slice_hash=slice_hash
        )

        # Map file type
        model.file_type = self._map_file_type(filetype)

        # Check stripping
        model.strip_status = self._check_strip_status(flags, ncmds)

        # Parse load commands
        self._parse_load_commands(data, header_size, sizeofcmds, endian_fmt, mach_slice, model)

        model.slice_count = 1
        model.slices = [mach_slice]
        model.primary = mach_slice

        return AdapterResult(
            success=True,
            artifacts=[path],
            metadata={
                "model": model.to_dict(),
                "is_fat": False,
                "slice_count": 1,
                "architecture": arch,
                "file_type": model.file_type.value
            }
        )

    def _parse_slice_header(
        self,
        data: bytes,
        offset: int,
        mach_slice: MachOSlice
    ):
        """Parse thin Mach-O header within a fat slice."""
        if offset + 4 > len(data):
            return

        magic_int = struct.unpack('<I', data[offset:offset + 4])[0]
        magic_info = MAGIC_VALUES.get(magic_int, {})

        endian = 'little' if magic_info.get("endian") == "little" else 'big'

        if magic_info.get("bitness") == "64":
            header_fmt = endian + 'IIIIIIII'  # 8 unsigned ints = 32 bytes
            header_size = 32
        else:
            header_fmt = endian + 'IIIIIII'  # 7 unsigned ints = 28 bytes
            header_size = 28

        if offset + header_size > len(data):
            return

        header = struct.unpack(header_fmt, data[offset:offset + header_size])

        cpu_type = header[0]
        cpu_subtype = header[1]
        filetype = header[2]
        ncmds = header[3]
        sizeofcmds = header[4]
        flags = header[5]

        # Update slice
        mach_slice.cpu_metadata.cpu_type = self._map_cpu_type(cpu_type)
        mach_slice.cpu_metadata.cpu_type_hex = cpu_type
        mach_slice.cpu_metadata.cpu_subtype = hex(cpu_subtype)
        mach_slice.cpu_metadata.cpu_subtype_hex = cpu_subtype

        mach_slice.bitness = Bitness.BIT64 if magic_info.get("bitness") == "64" else Bitness.BIT32
        mach_slice.endianness = Endianness.LITTLE if magic_info.get("endian") == "little" else Endianness.BIG

    def _parse_load_commands(
        self,
        data: bytes,
        offset: int,
        sizeofcmds: int,
        endian_fmt: str,
        mach_slice: MachOSlice,
        model: MachOModel
    ):
        """Parse Mach-O load commands."""
        end_offset = offset + sizeofcmds

        while offset < end_offset and offset + 8 <= len(data):
            try:
                cmd_data = data[offset:]

                # Read command header
                cmd_fmt = endian_fmt + 'II'
                cmd_type, cmd_size = struct.unpack(cmd_fmt, cmd_data[:8])

                cmd_name = LC_TYPES.get(cmd_type, f"LC_UNKNOWN_{cmd_type}")

                # Create load command record
                lc = LoadCommand(
                    cmd_type=cmd_name,
                    cmd_offset=offset,
                    cmd_size=cmd_size,
                    data={}
                )

                # Parse specific command types
                if cmd_name == "LC_UUID":
                    if len(cmd_data) >= 24:
                        uuid_bytes = cmd_data[8:24]
                        uuid_str = '-'.join([
                            uuid_bytes[i*4:(i+1)*4].hex()
                            for i in range(4)
                        ])
                        lc.data = {"uuid": uuid_str}
                        mach_slice.uuid = UUIDInfo(uuid=uuid_str, source="LC_UUID")

                elif cmd_name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB"):
                    lib_info = self._parse_dylib_command(cmd_data, endian)
                    lc.data = lib_info
                    mach_slice.libraries.append(LibraryDependency(
                        name=lib_info.get("name", "unknown"),
                        install_name=lib_info.get("install_name", ""),
                        version=lib_info.get("version", "unknown"),
                        weak=(cmd_name == "LC_LOAD_WEAK_DYLIB"),
                        reexport=(cmd_name == "LC_REEXPORT_DYLIB"),
                        cmd_type=cmd_name
                    ))

                elif cmd_name == "LC_RPATH":
                    if len(cmd_data) >= cmd_size:
                        path_data = cmd_data[8:cmd_size]
                        try:
                            path = path_data.split(b'\x00')[0].decode('utf-8')
                        except:
                            path = "unknown"
                        lc.data = {"path": path}
                        mach_slice.rpaths.append(RPath(path=path))

                elif cmd_name in ("LC_SEGMENT", "LC_SEGMENT_64"):
                    seg_info = self._parse_segment_command(cmd_data, endian_fmt, cmd_name, offset, data)
                    lc.data = seg_info
                    mach_slice.segments.append(SegmentInfo(
                        name=seg_info.get("name", "unknown"),
                        vmaddr=seg_info.get("vmaddr", 0),
                        vmsize=seg_info.get("vmsize", 0),
                        fileoff=seg_info.get("fileoff", 0),
                        filesize=seg_info.get("filesize", 0),
                        maxprot=seg_info.get("maxprot", 0),
                        initprot=seg_info.get("initprot", 0),
                        nsects=seg_info.get("nsects", 0),
                        flags=seg_info.get("flags", 0)
                    ))

                elif cmd_name == "LC_MAIN":
                    if len(cmd_data) >= 24:
                        entryoff, stacksize = struct.unpack(endian_fmt + 'QQ', cmd_data[8:24])
                        lc.data = {"entryoff": hex(entryoff), "stacksize": hex(stacksize)}
                        mach_slice.entry_point = EntryPoint(
                            present=True,
                            address=hex(entryoff),
                            source="LC_MAIN"
                        )

                elif cmd_name in ("LC_ENCRYPTION_INFO", "LC_ENCRYPTION_INFO_64"):
                    if cmd_name == "LC_ENCRYPTION_INFO_64" and len(cmd_data) >= 32:
                        cryptoff, cryptsize, cryptid, pad = struct.unpack(endian_fmt + 'IIII', cmd_data[8:24])
                    elif len(cmd_data) >= 20:
                        cryptoff, cryptsize, cryptid = struct.unpack(endian_fmt + 'III', cmd_data[8:20])
                        pad = 0
                    else:
                        cryptoff = cryptsize = cryptid = 0
                        pad = 0

                    lc.data = {
                        "cryptoff": hex(cryptoff),
                        "cryptsize": hex(cryptsize),
                        "cryptid": cryptid
                    }
                    mach_slice.encryption = EncryptionInfo(
                        encrypted=cryptid != 0,
                        crypt_id=cryptid,
                        cryptoff=cryptoff,
                        cryptsize=cryptsize,
                        crypttype="FairPlay" if cryptid == 1 else "Unknown"
                    )

                elif cmd_name == "LC_CODE_SIGNATURE":
                    if len(cmd_data) >= 16:
                        data_off, data_size = struct.unpack(endian_fmt + 'II', cmd_data[8:16])
                        lc.data = {"offset": hex(data_off), "size": data_size}
                        mach_slice.code_signature = CodeSignature(
                            present=True,
                            location="LC_CODE_SIGNATURE",
                            offset=data_off,
                            size=data_size
                        )

                elif cmd_name in ("LC_VERSION_MIN_MACOSX", "LC_VERSION_MIN_IPHONEOS",
                                  "LC_VERSION_MIN_TVOS", "LC_VERSION_MIN_WATCHOS"):
                    if len(cmd_data) >= 16:
                        version, sdk = struct.unpack(endian_fmt + 'II', cmd_data[8:16])
                        lc.data = {
                            "version": self._format_version(version),
                            "sdk": self._format_version(sdk),
                            "platform": cmd_name.split("_")[-1]
                        }
                        mach_slice.version_info = VersionInfo(
                            platform=cmd_name.split("_")[-1],
                            min_version=self._format_version(version),
                            sdk_version=self._format_version(sdk)
                        )

                elif cmd_name == "LC_BUILD_VERSION":
                    if len(cmd_data) >= 20:
                        platform, minos, sdk, ntools = struct.unpack(endian_fmt + 'IIII', cmd_data[8:24])
                        lc.data = {
                            "platform": PLATFORM_NAMES.get(platform, f"PLATFORM_{platform}"),
                            "minos": self._format_version(minos),
                            "sdk": self._format_version(sdk),
                            "ntools": ntools
                        }
                        mach_slice.build_version = BuildVersion(
                            platform=PLATFORM_NAMES.get(platform, f"PLATFORM_{platform}"),
                            minos=self._format_version(minos),
                            sdk=self._format_version(sdk),
                            ntools=ntools
                        )

                mach_slice.load_commands.append(lc)
                offset += cmd_size

            except Exception as e:
                model.warnings.append(f"Failed to parse load command at offset {offset}: {str(e)}")
                break

    def _parse_dylib_command(self, data: bytes, endian_fmt: str) -> Dict:
        """Parse dylib load command."""
        try:
            if len(data) >= 16:
                offset, timestamp, current_version, compatibility_version = struct.unpack(
                    endian_fmt + 'IIII', data[8:24]
                )
                name_data = data[offset:]
                name = name_data.split(b'\x00')[0].decode('utf-8', errors='replace')
                return {
                    "name": os.path.basename(name),
                    "install_name": name,
                    "version": self._format_version(current_version),
                    "timestamp": timestamp,
                    "compatibility_version": self._format_version(compatibility_version)
                }
        except:
            pass
        return {"name": "unknown", "install_name": "unknown", "version": "unknown"}

    def _parse_segment_command(
        self,
        data: bytes,
        endian_fmt: str,
        cmd_name: str,
        offset: int,
        full_data: bytes
    ) -> Dict:
        """Parse segment load command."""
        result = {}

        try:
            if cmd_name == "LC_SEGMENT_64":
                if len(data) >= 72:
                    segname = data[8:24].rstrip(b'\x00').decode('utf-8', errors='replace')
                    vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, flags = struct.unpack(
                        endian_fmt + 'IIIIIIII', data[24:56]
                    )
                    result = {
                        "name": segname,
                        "vmaddr": hex(vmaddr),
                        "vmsize": hex(vmsize),
                        "fileoff": hex(fileoff),
                        "filesize": hex(filesize),
                        "maxprot": maxprot,
                        "initprot": initprot,
                        "nsects": nsects,
                        "flags": hex(flags)
                    }
            else:
                if len(data) >= 56:
                    segname = data[8:24].rstrip(b'\x00').decode('utf-8', errors='replace')
                    vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, flags = struct.unpack(
                        endian_fmt + 'IIIIIIII', data[24:56]
                    )
                    result = {
                        "name": segname,
                        "vmaddr": hex(vmaddr),
                        "vmsize": hex(vmsize),
                        "fileoff": hex(fileoff),
                        "filesize": hex(filesize),
                        "maxprot": maxprot,
                        "initprot": initprot,
                        "nsects": nsects,
                        "flags": hex(flags)
                    }
        except:
            result = {"name": "unknown"}

        return result

    def _get_architecture_name(self, cpu_type: int, cpu_subtype: int) -> str:
        """Get human-readable architecture name."""
        # ARM variants
        if cpu_type == 12:  # CPU_TYPE_ARM
            if cpu_subtype & 0xFF == 6:
                return "armv6"
            elif cpu_subtype & 0xFF == 7:
                return "armv7"
            elif cpu_subtype & 0xFF == 9:
                return "armv7s"
            elif cpu_subtype & 0xFF == 11:
                return "armv8"  # 32-bit ARM64 variant
            return f"arm_{hex(cpu_subtype)}"

        # ARM64 variants
        if cpu_type == 16777228 or cpu_type == 16777226:  # CPU_TYPE_ARM64
            if cpu_subtype == 0:
                return "arm64"
            elif cpu_subtype == 1:
                return "arm64e"  # Apple Silicon
            elif cpu_subtype == 2:
                return "arm64_32"
            return f"arm64_{hex(cpu_subtype)}"

        # x86 variants
        if cpu_type == 7 or cpu_type == 0x01000007:  # CPU_TYPE_I386
            return "i386"

        # x86_64 variants
        if cpu_type == 0x0100000c or cpu_type == 16777228:  # CPU_TYPE_X86_64
            if cpu_subtype == 8:  # CPU_SUBTYPE_X86_64_Haswell
                return "x86_64h"
            return "x86_64"

        # PowerPC
        if cpu_type == 18 or cpu_type == 0x01000012:  # CPU_TYPE_POWERPC
            return "ppc"

        if cpu_type == 0x01000020:  # CPU_TYPE_POWERPC64
            return "ppc64"

        # Unknown
        return f"cpu_{hex(cpu_type)}_{hex(cpu_subtype)}"

    def _map_cpu_type(self, cpu_type: int) -> str:
        """Map CPU type constant to name."""
        return CPU_TYPES.get(cpu_type, f"CPU_TYPE_{cpu_type}")

    def _map_file_type(self, filetype: int) -> FileType:
        """Map file type constant to FileType enum."""
        name = MH_FILE_TYPES.get(filetype, f"unknown_{filetype}")
        try:
            return FileType[name.replace("MH_", "").lower()]
        except:
            return FileType.UNKNOWN

    def _check_strip_status(self, flags: int, ncmds: int) -> StripStatus:
        """Check symbol stripping status from flags."""
        if flags & 0x200:  # MH_STRIP_STABS
            return StripStatus.STRIPPED
        if flags & 0x1000:  # MH_DYLDLINK
            if ncmds == 0:
                return StripStatus.SYMBOLS_STRIPPED
            return StripStatus.DY_SYMS_STRIPPED
        return StripStatus.SYMBOLS_PRESENT

    def _format_version(self, version: int) -> str:
        """Format packed version integer to string."""
        major = (version >> 16) & 0xFFFF
        minor = (version >> 8) & 0xFF
        patch = version & 0xFF
        return f"{major}.{minor}.{patch}"

    def validate_macho(self, path: str) -> AdapterResult:
        """Check if file is a valid Mach-O."""
        if not os.path.exists(path):
            return AdapterResult(success=False, error="File not found")

        try:
            with open(path, 'rb') as f:
                magic_bytes = f.read(4)

            if len(magic_bytes) < 4:
                return AdapterResult(
                    success=False,
                    error="File too small",
                    metadata={"is_macho": False}
                )

            magic_int = struct.unpack('>I', magic_bytes)[0]
            magic_info = MAGIC_VALUES.get(magic_int)

            is_macho = magic_info is not None

            return AdapterResult(
                success=True,
                metadata={
                    "is_macho": is_macho,
                    "magic": hex(magic_int) if magic_bytes else "unknown",
                    "type": magic_info.get("name", "unknown") if magic_info else "not_macho"
                }
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))
