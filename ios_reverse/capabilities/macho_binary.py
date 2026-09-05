"""
Mach-O and Binary Capabilities for IOS REVERSE KAISER.

These capabilities provide normalized Mach-O and binary analysis.
"""

from typing import Dict, Any, Tuple, Optional, List
import os
import hashlib
import struct
from datetime import datetime

from .base import (
    CapabilityExecutor,
    CapabilityContract,
    CapabilityResult,
    CapabilityStatus,
    EvidenceRecord,
    ProvenanceRecord,
)
from ..models.macho import (
    MachOModel, MachOType, FileType, Bitness, Endianness,
    CPUMetadata, UUIDInfo, MachOSlice, SegmentInfo,
    LibraryDependency, RPath, LoadCommand, VersionInfo,
    EncryptionInfo, CodeSignature, BuildVersion, EntryPoint, StripStatus,
    MAGIC_VALUES, CPU_TYPES, LC_TYPES, MH_FILE_TYPES, PLATFORM_NAMES,
)


# =============================================================================
# CAP-007: macho.basic
# =============================================================================

class MachoBasicCapability(CapabilityExecutor):
    """
    Create normalized basic Mach-O metadata.

    Contract: macho.basic v1.0.0
    Domain: mach_o
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="macho.basic",
            version="1.0.0",
            domain="mach_o",
            name="Mach-O Basic Analysis",
            description="Create normalized basic Mach-O metadata including architecture, file type, and structural information",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to Mach-O file"},
            ],
            optional_inputs=[
                {"name": "compute_hash", "type": "boolean", "default": True},
            ],

            supported_input_types=["macho", "thin_macho", "fat_macho", "app_bundle", "dylib"],
            output_types=["macho_metadata"],

            required_adapters=["macho_parser"],
            optional_adapters=["otool"],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NOT_MACHO", "message": "File is not a valid Mach-O"},
                "E003": {"name": "PARSE_ERROR", "message": "Failed to parse Mach-O header"},
            },
            warning_codes={
                "W001": {"name": "TOOL_UNAVAILABLE", "message": "External tool not available, using fallback"},
                "W002": {"name": "TRUNCATED", "message": "Output was truncated"},
            },
            stop_on=["E001", "E002"],
            abort_workflow_on=["E001"],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        # Check if it's a Mach-O file
        try:
            with open(artifact_path, 'rb') as f:
                magic_bytes = f.read(4)
            if len(magic_bytes) < 4:
                return False, "File too small to be Mach-O"

            magic_int = struct.unpack('>I', magic_bytes)[0]
            if magic_int not in MAGIC_VALUES:
                return False, f"Not a valid Mach-O file (magic: {hex(magic_int)})"
        except Exception as e:
            return False, f"Cannot read file: {e}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute Mach-O basic analysis."""
        from ..adapters.macho.parser_adapter import MachOParserAdapter
        from ..adapters.macho.otool_adapter import OtoolAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        compute_hash = inputs.get("compute_hash", True)

        warnings = []

        # Get parser adapter (preferred - works on all platforms)
        parser_adapter = MachOParserAdapter()

        # Try parser first
        if parser_adapter.is_available():
            parse_result = parser_adapter.parse(
                artifact_path,
                compute_hashes=compute_hash
            )

            if parse_result.success:
                model_data = parse_result.metadata.get("model", {})
                macho_type = model_data.get("macho_type", "unknown")
                is_fat = model_data.get("is_fat", False)
                slices = model_data.get("slices", [])
                primary = model_data.get("primary")

                # Build metadata
                metadata = {
                    "artifact_path": artifact_path,
                    "artifact_hash": model_data.get("artifact_hash", ""),
                    "file_size": model_data.get("file_size", 0),
                    "macho_type": macho_type,
                    "is_fat": is_fat,
                    "file_type": model_data.get("file_type", "unknown"),
                    "strip_status": model_data.get("strip_status", "unknown"),
                    "slice_count": model_data.get("slice_count", 0),
                    "warnings": model_data.get("warnings", []),
                }

                # Add primary slice info if available
                if primary:
                    metadata["architecture"] = primary.get("architecture", "unknown")
                    metadata["cpu_type"] = primary.get("cpu_metadata", {}).get("cpu_type", "unknown")
                    metadata["bitness"] = primary.get("bitness", "unknown")
                    metadata["endianness"] = primary.get("endianness", "unknown")

                    # UUID
                    uuid_info = primary.get("uuid")
                    if uuid_info:
                        metadata["uuid"] = uuid_info.get("uuid", "unknown")

                    # Entry point
                    ep = primary.get("entry_point", {})
                    metadata["entry_point"] = ep.get("address", "unknown") if ep.get("present") else None

                    # Encryption
                    enc = primary.get("encryption", {})
                    metadata["encrypted"] = enc.get("encrypted", False)
                    if enc.get("encrypted"):
                        metadata["encryption_type"] = enc.get("crypttype", "unknown")

                    # Code signature
                    cs = primary.get("code_signature", {})
                    metadata["code_signed"] = cs.get("present", False)

                    # Libraries
                    libs = primary.get("libraries", [])
                    metadata["linked_library_count"] = len(libs)

                    # Version info
                    ver = primary.get("version_info")
                    if ver:
                        metadata["min_os_version"] = ver.get("min_version", "unknown")
                        metadata["platform"] = ver.get("platform", "unknown")

                # Add slice summaries for fat binaries
                if is_fat:
                    metadata["architectures"] = [s.get("architecture", "unknown") for s in slices]

                # Create evidence
                evidence = [
                    EvidenceRecord(
                        id=self._next_evidence_id(),
                        type="raw",
                        capability_id=self.id,
                        execution_id=execution_id,
                        timestamp=datetime.utcnow(),
                        file_path=artifact_path,
                        sha256=model_data.get("artifact_hash", ""),
                        size=model_data.get("file_size", 0),
                    )
                ]

                # Create provenance
                provenance = ProvenanceRecord(
                    capability_id=self.id,
                    capability_version=self.version,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow(),
                    inputs={"artifact_path": artifact_path, "compute_hash": compute_hash},
                    adapter_id=parser_adapter.id,
                    working_directory=os.getcwd(),
                    output_artifacts=[{"path": artifact_path, "type": "macho_metadata"}],
                )

                return CapabilityResult.success(
                    execution_id=execution_id,
                    metadata=metadata,
                    evidence=evidence,
                    provenance=provenance,
                    warnings=warnings,
                )
            else:
                # Parser failed
                return CapabilityResult.failure(
                    execution_id=execution_id,
                    error_code="E003",
                    error_message=parse_result.error or "Parse failed",
                    provenance=ProvenanceRecord(
                        capability_id=self.id,
                        capability_version=self.version,
                        execution_id=execution_id,
                        timestamp=datetime.utcnow(),
                        inputs={"artifact_path": artifact_path},
                        adapter_id=parser_adapter.id,
                        working_directory=os.getcwd(),
                        error_code="E003",
                        error_message=parse_result.error,
                    ),
                )
        else:
            # No parser available (shouldn't happen)
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E003",
                error_message="No Mach-O parser available",
            )


# =============================================================================
# CAP-008: macho.slices
# =============================================================================

class MachoSlicesCapability(CapabilityExecutor):
    """
    Enumerate all architecture slices.

    Contract: macho.slices v1.0.0
    Domain: mach_o
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="macho.slices",
            version="1.0.0",
            domain="mach_o",
            name="Mach-O Slice Enumeration",
            description="Enumerate all architecture slices in fat/universal binaries or confirm single slice",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to Mach-O file"},
            ],
            optional_inputs=[
                {"name": "extract_slices", "type": "boolean", "default": False},
                {"name": "output_dir", "type": "path", "description": "Directory for extracted slices"},
            ],

            supported_input_types=["macho", "fat_macho", "thin_macho"],
            output_types=["slice_list"],

            required_adapters=["macho_parser"],
            optional_adapters=[],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NOT_MACHO", "message": "File is not a valid Mach-O"},
                "E003": {"name": "EXTRACTION_FAILED", "message": "Failed to extract slice"},
            },
            warning_codes={
                "W001": {"name": "SLICE_LIMIT", "message": "Slice count exceeds limit"},
            },
            stop_on=["E001", "E002", "E003"],
            abort_workflow_on=["E001"],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute slice enumeration."""
        from ..adapters.macho.parser_adapter import MachOParserAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        extract_slices = inputs.get("extract_slices", False)
        output_dir = inputs.get("output_dir")

        warnings = []
        artifacts = []

        # Parse Mach-O
        parser_adapter = MachOParserAdapter()
        parse_result = parser_adapter.parse(artifact_path, compute_hashes=True)

        if not parse_result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E002",
                error_message=parse_result.error or "Not a valid Mach-O",
            )

        model_data = parse_result.metadata.get("model", {})
        slices_data = model_data.get("slices", [])
        is_fat = model_data.get("is_fat", False)

        # Build slice list
        slices = []
        for i, slice_data in enumerate(slices_data):
            slice_info = {
                "index": i,
                "architecture": slice_data.get("architecture", "unknown"),
                "offset": slice_data.get("file_offset", "0x0"),
                "size": slice_data.get("size", "0x0"),
                "hash": slice_data.get("slice_hash", ""),
                "cpu_type": slice_data.get("cpu_metadata", {}).get("cpu_type", "unknown"),
                "cpu_subtype": slice_data.get("cpu_metadata", {}).get("cpu_subtype", "unknown"),
                "bitness": slice_data.get("bitness", "unknown"),
                "endianness": slice_data.get("endianness", "unknown"),
                "extracted": False,
                "extraction_path": None,
            }

            # Extract slice if requested
            if extract_slices and output_dir:
                slice_path = os.path.join(output_dir, f"slice_{i}_{slice_info['architecture']}")
                try:
                    with open(artifact_path, 'rb') as f:
                        f.seek(int(slice_data.get("file_offset", 0), 16) if isinstance(slice_data.get("file_offset"), str) else slice_data.get("file_offset", 0))
                        slice_data_bytes = f.read(int(slice_data.get("size", 0), 16) if isinstance(slice_data.get("size"), str) else slice_data.get("size", 0))

                    with open(slice_path, 'wb') as sf:
                        sf.write(slice_data_bytes)

                    slice_info["extracted"] = True
                    slice_info["extraction_path"] = slice_path
                    artifacts.append(slice_path)
                except Exception as e:
                    warnings.append({"code": "W002", "message": f"Failed to extract slice {i}: {str(e)}"})

            slices.append(slice_info)

        # Create metadata
        metadata = {
            "artifact_path": artifact_path,
            "artifact_hash": model_data.get("artifact_hash", ""),
            "is_fat": is_fat,
            "slice_count": len(slices),
            "architectures": [s["architecture"] for s in slices],
            "slices": slices,
        }

        # Add warning if many slices
        if len(slices) > 10:
            warnings.append({"code": "W001", "message": f"Slice count ({len(slices)}) exceeds typical range"})

        # Create evidence
        evidence = [
            EvidenceRecord(
                id=self._next_evidence_id(),
                type="raw",
                capability_id=self.id,
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                file_path=artifact_path,
                sha256=model_data.get("artifact_hash", ""),
                size=model_data.get("file_size", 0),
            )
        ]

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={
                "artifact_path": artifact_path,
                "extract_slices": extract_slices,
                "output_dir": output_dir,
            },
            adapter_id=parser_adapter.id,
            working_directory=os.getcwd(),
            output_artifacts=[{"path": artifact_path}, *({"path": a} for a in artifacts)],
        )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            artifacts=artifacts if artifacts else [artifact_path],
            evidence=evidence,
            provenance=provenance,
            warnings=warnings,
        )


# =============================================================================
# CAP-009: macho.load_commands
# =============================================================================

class MachoLoadCommandsCapability(CapabilityExecutor):
    """
    Normalize load commands.

    Contract: macho.load_commands v1.0.0
    Domain: mach_o
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="macho.load_commands",
            version="1.0.0",
            domain="mach_o",
            name="Mach-O Load Commands",
            description="Extract and normalize Mach-O load commands including libraries, rpaths, segments, and version info",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to Mach-O file"},
            ],
            optional_inputs=[
                {"name": "slice_index", "type": "integer", "description": "Slice index for fat binaries (default: 0)"},
                {"name": "command_types", "type": "array", "description": "Filter to specific command types"},
            ],

            supported_input_types=["macho", "fat_macho", "thin_macho"],
            output_types=["load_commands"],

            required_adapters=["macho_parser"],
            optional_adapters=["otool"],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NOT_MACHO", "message": "File is not a valid Mach-O"},
                "E003": {"name": "PARSE_ERROR", "message": "Failed to parse load commands"},
                "E004": {"name": "SLICE_NOT_FOUND", "message": "Specified slice not found"},
            },
            warning_codes={
                "W001": {"name": "UNKNOWN_COMMAND", "message": "Unknown load command type encountered"},
                "W002": {"name": "COMMAND_LIMIT", "message": "Command count exceeds limit"},
            },
            stop_on=["E001", "E002"],
            abort_workflow_on=["E001"],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute load command extraction."""
        from ..adapters.macho.parser_adapter import MachOParserAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        slice_index = inputs.get("slice_index", 0)
        command_types = inputs.get("command_types")

        warnings = []

        # Parse Mach-O
        parser_adapter = MachOParserAdapter()
        parse_result = parser_adapter.parse(artifact_path, compute_hashes=False)

        if not parse_result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E002",
                error_message=parse_result.error or "Not a valid Mach-O",
            )

        model_data = parse_result.metadata.get("model", {})
        slices_data = model_data.get("slices", [])

        # Get specified slice
        if slice_index >= len(slices_data):
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E004",
                error_message=f"Slice {slice_index} not found (only {len(slices_data)} slices)",
            )

        slice_data = slices_data[slice_index]
        load_commands_data = slice_data.get("load_commands", [])

        # Filter by command type if specified
        if command_types:
            load_commands_data = [
                lc for lc in load_commands_data
                if lc.get("cmd_type") in command_types
            ]

        # Build normalized load commands
        load_commands = []
        dylibs = []
        rpaths = []
        segments = []
        command_types_found = set()

        for lc in load_commands_data:
            cmd_type = lc.get("cmd_type", "unknown")
            command_types_found.add(cmd_type)

            normalized_lc = {
                "cmd_type": cmd_type,
                "cmd_offset": lc.get("cmd_offset", 0),
                "cmd_size": lc.get("cmd_size", 0),
            }

            # Add command-specific data
            data = lc.get("data", {})
            normalized_lc.update(data)

            load_commands.append(normalized_lc)

            # Categorize
            if cmd_type in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB"):
                dylibs.append({
                    "name": data.get("name", "unknown"),
                    "install_name": data.get("install_name", ""),
                    "version": data.get("version", "unknown"),
                    "cmd_type": cmd_type,
                    "weak": cmd_type == "LC_LOAD_WEAK_DYLIB",
                    "reexport": cmd_type == "LC_REEXPORT_DYLIB",
                })
            elif cmd_type == "LC_RPATH":
                rpaths.append({
                    "path": data.get("path", "unknown"),
                })
            elif cmd_type in ("LC_SEGMENT", "LC_SEGMENT_64"):
                segments.append({
                    "name": data.get("name", "unknown"),
                    "vmaddr": data.get("vmaddr", "0x0"),
                    "vmsize": data.get("vmsize", "0x0"),
                    "fileoff": data.get("fileoff", "0x0"),
                    "filesize": data.get("filesize", "0x0"),
                    "nsects": data.get("nsects", 0),
                })

        # Build metadata
        metadata = {
            "artifact_path": artifact_path,
            "slice_index": slice_index,
            "architecture": slice_data.get("architecture", "unknown"),
            "command_count": len(load_commands),
            "command_types": list(command_types_found),
            "load_commands": load_commands,
            "dylibs": dylibs,
            "rpaths": rpaths,
            "segments": segments,
            "libraries": dylibs,  # Alias for consistency
            "dylib_count": len(dylibs),
            "rpath_count": len(rpaths),
            "segment_count": len(segments),
        }

        # Add command-specific metadata
        uuid = slice_data.get("uuid")
        if uuid:
            metadata["uuid"] = uuid.get("uuid", "unknown")

        entry_point = slice_data.get("entry_point", {})
        if entry_point.get("present"):
            metadata["entry_point"] = entry_point.get("address", "unknown")

        version_info = slice_data.get("version_info")
        if version_info:
            metadata["min_os_version"] = version_info.get("min_version", "unknown")
            metadata["platform"] = version_info.get("platform", "unknown")

        encryption = slice_data.get("encryption", {})
        if encryption.get("encrypted"):
            metadata["encrypted"] = True
            metadata["encryption_type"] = encryption.get("crypttype", "unknown")

        build_version = slice_data.get("build_version")
        if build_version:
            metadata["build_platform"] = build_version.get("platform", "unknown")
            metadata["build_minos"] = build_version.get("minos", "unknown")
            metadata["build_sdk"] = build_version.get("sdk", "unknown")

        code_sig = slice_data.get("code_signature", {})
        metadata["code_signature_present"] = code_sig.get("present", False)

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={
                "artifact_path": artifact_path,
                "slice_index": slice_index,
                "command_types": command_types,
            },
            adapter_id=parser_adapter.id,
            working_directory=os.getcwd(),
        )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            evidence=[],
            provenance=provenance,
            warnings=warnings,
        )


# =============================================================================
# CAP-010: binary.imports
# =============================================================================

class BinaryImportsCapability(CapabilityExecutor):
    """
    Extract imported symbols and dependencies.

    Contract: binary.imports v1.0.0
    Domain: binary
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="binary.imports",
            version="1.0.0",
            domain="binary",
            name="Import Analysis",
            description="Extract imported symbols and dynamic library dependencies from binary",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to binary"},
            ],
            optional_inputs=[
                {"name": "slice_index", "type": "integer", "description": "Slice index for fat binaries"},
            ],

            supported_input_types=["macho", "dylib", "executable"],
            output_types=["imports"],

            required_adapters=["macho_parser"],
            optional_adapters=["nm"],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NO_IMPORTS", "message": "No imports found (may be stripped)"},
                "E003": {"name": "PARSE_ERROR", "message": "Failed to parse imports"},
            },
            warning_codes={
                "W001": {"name": "STRIPPED", "message": "Binary may be stripped, imports unavailable"},
                "W002": {"name": "TOOL_FALLBACK", "message": "Using fallback parser"},
            },
            stop_on=["E001"],
            abort_workflow_on=[],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute import extraction."""
        from ..adapters.macho.parser_adapter import MachOParserAdapter
        from ..adapters.macho.nm_adapter import NmAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        slice_index = inputs.get("slice_index", 0)

        warnings = []
        partial = False

        # Parse Mach-O
        parser_adapter = MachOParserAdapter()
        parse_result = parser_adapter.parse(artifact_path, compute_hashes=False)

        if not parse_result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E003",
                error_message=parse_result.error or "Failed to parse",
            )

        model_data = parse_result.metadata.get("model", {})
        slices_data = model_data.get("slices", [])

        # Get specified slice
        if slice_index >= len(slices_data):
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E003",
                error_message=f"Slice {slice_index} not found",
            )

        slice_data = slices_data[slice_index]
        libraries = slice_data.get("libraries", [])

        # Get symbol imports using nm if available
        nm_adapter = NmAdapter()
        symbol_imports = []

        if nm_adapter.is_available():
            nm_result = nm_adapter.get_imports(artifact_path)
            if nm_result.success:
                symbol_imports = nm_result.metadata.get("imports", [])
        else:
            warnings.append({"code": "W002", "message": "nm not available, using parser data only"})

        # Build import records
        imports = []
        for lib in libraries:
            import_record = {
                "type": "library",
                "name": lib.get("name", "unknown"),
                "install_name": lib.get("install_name", ""),
                "version": lib.get("version", "unknown"),
                "weak": lib.get("weak", False),
                "reexport": lib.get("reexport", False),
                "cmd_type": lib.get("cmd_type", "LC_LOAD_DYLIB"),
            }
            imports.append(import_record)

        # Add symbol imports
        for sym in symbol_imports:
            imports.append({
                "type": "symbol",
                "name": sym,
                "source": "nm",
            })

        # Check for stripping
        strip_status = model_data.get("strip_status", "unknown")
        if strip_status in ("stripped", "symbols_stripped", "dy_syms_stripped"):
            if not libraries:
                warnings.append({"code": "W001", "message": f"Binary is {strip_status}, imports may be unavailable"})
                partial = True

        # Build metadata
        metadata = {
            "artifact_path": artifact_path,
            "architecture": slice_data.get("architecture", "unknown"),
            "slice_index": slice_index,
            "import_count": len(imports),
            "library_count": len(libraries),
            "symbol_import_count": len(symbol_imports),
            "libraries": libraries,
            "symbol_imports": symbol_imports[:100],  # Limit for output
            "strip_status": strip_status,
        }

        # Check for empty imports
        if len(imports) == 0:
            partial = True
            warnings.append({"code": "W001", "message": "No imports found"})

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={"artifact_path": artifact_path, "slice_index": slice_index},
            adapter_id=parser_adapter.id,
            working_directory=os.getcwd(),
        )

        if partial:
            return CapabilityResult.partial(
                execution_id=execution_id,
                metadata=metadata,
                evidence=[],
                provenance=provenance,
                warnings=warnings,
            )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            evidence=[],
            provenance=provenance,
            warnings=warnings,
        )


# =============================================================================
# CAP-011: binary.exports
# =============================================================================

class BinaryExportsCapability(CapabilityExecutor):
    """
    Extract exported symbols.

    Contract: binary.exports v1.0.0
    Domain: binary
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="binary.exports",
            version="1.0.0",
            domain="binary",
            name="Export Analysis",
            description="Extract exported symbols from binary",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to binary"},
            ],
            optional_inputs=[
                {"name": "slice_index", "type": "integer", "description": "Slice index for fat binaries"},
            ],

            supported_input_types=["macho", "dylib", "executable"],
            output_types=["exports"],

            required_adapters=["macho_parser"],
            optional_adapters=["nm"],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NO_EXPORTS", "message": "No exports found"},
                "E003": {"name": "PARSE_ERROR", "message": "Failed to parse exports"},
            },
            warning_codes={
                "W001": {"name": "STRIPPED", "message": "Binary is stripped, exports unavailable"},
                "W002": {"name": "TOOL_FALLBACK", "message": "Using fallback method"},
            },
            stop_on=["E001"],
            abort_workflow_on=[],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute export extraction."""
        from ..adapters.macho.nm_adapter import NmAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        slice_index = inputs.get("slice_index", 0)

        warnings = []
        partial = False

        # Try nm first
        nm_adapter = NmAdapter()
        exports = []

        if nm_adapter.is_available():
            nm_result = nm_adapter.get_exports(artifact_path)
            if nm_result.success:
                # Parse nm output
                for line in nm_result.stdout.split('\n'):
                    line = line.strip()
                    if line:
                        exports.append(line)
        else:
            warnings.append({"code": "W002", "message": "nm not available, exports may be incomplete"})

        # Build metadata
        metadata = {
            "artifact_path": artifact_path,
            "slice_index": slice_index,
            "export_count": len(exports),
            "exports": exports[:100],  # Limit for output
        }

        # Empty exports is valid for some binaries (stubs, etc.)
        if len(exports) == 0:
            # This is a valid state, not necessarily an error
            metadata["note"] = "No exports found - binary may be stripped or have no public symbols"
            partial = True

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={"artifact_path": artifact_path, "slice_index": slice_index},
            adapter_id=nm_adapter.id if nm_adapter.is_available() else "none",
            working_directory=os.getcwd(),
        )

        if partial:
            return CapabilityResult.partial(
                execution_id=execution_id,
                metadata=metadata,
                evidence=[],
                provenance=provenance,
                warnings=warnings,
            )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            evidence=[],
            provenance=provenance,
            warnings=warnings,
        )


# =============================================================================
# CAP-012: binary.symbols
# =============================================================================

class BinarySymbolsCapability(CapabilityExecutor):
    """
    Collect symbol information.

    Contract: binary.symbols v1.0.0
    Domain: binary
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="binary.symbols",
            version="1.0.0",
            domain=" binary",
            name="Symbol Table Analysis",
            description="Collect and classify symbol information from binary",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to binary"},
            ],
            optional_inputs=[
                {"name": "slice_index", "type": "integer", "description": "Slice index for fat binaries"},
                {"name": "symbol_types", "type": "array", "description": "Filter by symbol type (defined, undefined, etc.)"},
            ],

            supported_input_types=["macho", "dylib", "executable", "object"],
            output_types=["symbols"],

            required_adapters=["macho_parser"],
            optional_adapters=["nm"],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NO_SYMBOLS", "message": "No symbols found"},
                "E003": {"name": "PARSE_ERROR", "message": "Failed to parse symbols"},
            },
            warning_codes={
                "W001": {"name": "STRIPPED", "message": "Binary is stripped, symbols unavailable"},
                "W002": {"name": "LIMIT_EXCEEDED", "message": "Symbol count exceeds limit"},
            },
            stop_on=["E001"],
            abort_workflow_on=[],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute symbol extraction."""
        from ..adapters.macho.nm_adapter import NmAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        slice_index = inputs.get("slice_index", 0)
        symbol_types = inputs.get("symbol_types")

        warnings = []
        partial = False

        nm_adapter = NmAdapter()

        symbols = []
        defined_count = 0
        undefined_count = 0
        objc_count = 0
        swift_count = 0

        if nm_adapter.is_available():
            # Get all symbols
            nm_result = nm_adapter.get_symbols(artifact_path)
            if nm_result.success:
                # Classify symbols
                for line in nm_result.stdout.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # Classify symbol
                    symbol_info = self._classify_symbol(line)
                    symbols.append(symbol_info)

                    if symbol_info.get("type") == "undefined":
                        undefined_count += 1
                    else:
                        defined_count += 1

                    if symbol_info.get("type_detail") == "objc":
                        objc_count += 1
                    elif symbol_info.get("type_detail") == "swift":
                        swift_count += 1
        else:
            warnings.append({"code": "W001", "message": "nm not available"})

        # Filter by type if specified
        if symbol_types:
            symbols = [s for s in symbols if s.get("type") in symbol_types]

        # Check limits
        if len(symbols) > 1000:
            warnings.append({"code": "W002", "message": f"Symbol count ({len(symbols)}) exceeds limit, truncating"})
            symbols = symbols[:1000]
            partial = True

        # Build metadata
        metadata = {
            "artifact_path": artifact_path,
            "slice_index": slice_index,
            "total_symbols": len(symbols),
            "defined_count": defined_count,
            "undefined_count": undefined_count,
            "objc_count": objc_count,
            "swift_count": swift_count,
            "symbols": symbols,
        }

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={"artifact_path": artifact_path, "slice_index": slice_index},
            adapter_id=nm_adapter.id if nm_adapter.is_available() else "none",
            working_directory=os.getcwd(),
        )

        if partial or len(symbols) == 0:
            return CapabilityResult.partial(
                execution_id=execution_id,
                metadata=metadata,
                evidence=[],
                provenance=provenance,
                warnings=warnings,
            )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            evidence=[],
            provenance=provenance,
            warnings=warnings,
        )

    def _classify_symbol(self, line: str) -> Dict[str, Any]:
        """Classify a symbol."""
        symbol = {
            "raw": line,
            "type": "unknown",
            "type_detail": "unknown",
            "name": "",
            "address": "",
        }

        # Parse nm output format
        parts = line.split()
        if len(parts) >= 2:
            # Try to extract type
            for part in parts:
                if part.startswith('_'):
                    symbol["name"] = part
                    break

            # Symbol type character
            for part in parts:
                if len(part) == 1 and part in 'TBEFGIWSDVUbvd':
                    symbol["type"] = self._symbol_type_to_category(part)
                    break

        # Check for Objective-C
        if '_OBJC_' in line or line.startswith('+[') or line.startswith('-['):
            symbol["type_detail"] = "objc"

        # Check for Swift
        if '_T' in line and '_' in line and not symbol["type_detail"]:
            # Swift mangled symbols typically start with _T and contain underscores
            symbol["type_detail"] = "swift"

        return symbol

    def _symbol_type_to_category(self, type_char: str) -> str:
        """Convert nm symbol type to category."""
        categories = {
            'T': 'global',  # Text (code)
            'B': 'global',  # BSS (uninitialized data)
            'D': 'global',  # Data
            'I': 'global',  # Indirect
            'W': 'global',  # Weak
            'S': 'global',  # Section
            'V': 'global',  # Weak object
            'U': 'undefined',
            't': 'local',  # Local text
            'b': 'local',  # Local BSS
            'd': 'local',  # Local data
            'i': 'local',  # Local indirect
            'w': 'local',  # Local weak
            's': 'local',  # Local section
            'v': 'local',  # Weak object
            'f': 'local',  # Function
            'F': 'file',
            'G': 'small',  # Small global
            'C': 'small',  # Small BSS
        }
        return categories.get(type_char, 'unknown')


# =============================================================================
# CAP-013: binary.strings
# =============================================================================

class BinaryStringsCapability(CapabilityExecutor):
    """
    Extract binary strings.

    Contract: binary.strings v1.0.0
    Domain: binary
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="binary.strings",
            version="1.0.0",
            domain="binary",
            name="String Extraction",
            description="Extract strings from binary with normalized records",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to binary"},
            ],
            optional_inputs=[
                {"name": "min_length", "type": "integer", "default": 4, "description": "Minimum string length"},
                {"name": "max_strings", "type": "integer", "default": 1000, "description": "Maximum strings to return"},
                {"name": "include_offsets", "type": "boolean", "default": True, "description": "Include file offsets"},
            ],

            supported_input_types=["*"],
            output_types=["strings"],

            required_adapters=["strings_adapter"],
            optional_adapters=["strings"],
            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "EXTRACTION_FAILED", "message": "String extraction failed"},
            },
            warning_codes={
                "W001": {"name": "LIMIT_EXCEEDED", "message": "String count exceeds limit"},
                "W002": {"name": "TRUNCATED", "message": "Output was truncated"},
            },
            stop_on=["E001"],
            abort_workflow_on=["E001"],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute string extraction."""
        from ..adapters.macho.strings_adapter import StringsAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        min_length = inputs.get("min_length", 4)
        max_strings = inputs.get("max_strings", 1000)
        include_offsets = inputs.get("include_offsets", True)

        warnings = []
        truncated = False

        # Extract strings
        strings_adapter = StringsAdapter()
        result = strings_adapter.extract_strings(
            artifact_path,
            min_length=min_length,
            include_offsets=include_offsets
        )

        if not result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E002",
                error_message=result.error or "Extraction failed",
            )

        strings_data = result.metadata.get("strings", [])

        # Check limits
        total_strings = len(strings_data)
        if total_strings > max_strings:
            warnings.append({
                "code": "W001",
                "message": f"String count ({total_strings}) exceeds limit ({max_strings}), truncating"
            })
            strings_data = strings_data[:max_strings]
            truncated = True

        # Build metadata
        metadata = {
            "artifact_path": artifact_path,
            "min_length": min_length,
            "total_strings_found": total_strings,
            "strings_returned": len(strings_data),
            "truncated": truncated,
            "strings": strings_data,
            "method": result.metadata.get("method", "unknown"),
        }

        # Create evidence
        evidence = [
            EvidenceRecord(
                id=self._next_evidence_id(),
                type="derived",
                capability_id=self.id,
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                file_path=artifact_path,
                size=os.path.getsize(artifact_path),
            )
        ]

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={
                "artifact_path": artifact_path,
                "min_length": min_length,
                "max_strings": max_strings,
            },
            adapter_id=strings_adapter.id,
            working_directory=os.getcwd(),
        )

        return CapabilityResult(
            status=CapabilityStatus.SUCCESS if not truncated else CapabilityStatus.PARTIAL,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            metadata=metadata,
            evidence=evidence,
            provenance=provenance,
            warnings=warnings,
        )
