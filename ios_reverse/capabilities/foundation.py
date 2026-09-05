"""
Foundation Capabilities for IOS REVERSE KAISER.

These capabilities handle IPA/bundle operations.
"""

from typing import Dict, Any, Tuple, Optional, List
import os
import shutil
import zipfile
from datetime import datetime

from .base import (
    CapabilityExecutor,
    CapabilityContract,
    CapabilityResult,
    CapabilityStatus,
    EvidenceRecord,
    ProvenanceRecord,
)


# =============================================================================
# CAP-001: foundation.artifact_detect
# =============================================================================

class ArtifactDetectCapability(CapabilityExecutor):
    """
    Detect and classify input artifacts.

    Contract: foundation.artifact_detect v1.0.0
    Domain: foundation
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="foundation.artifact_detect",
            version="1.0.0",
            domain="foundation",
            name="Artifact Detection",
            description="Detect and classify input artifacts as IPA, app_bundle, macho, etc.",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to artifact"},
            ],
            optional_inputs=[
                {"name": "compute_hash", "type": "boolean", "default": False},
            ],

            supported_input_types=["*"],
            output_types=["artifact_type"],

            required_adapters=["file_adapter"],
            optional_adapters=[],

            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "EMPTY_FILE", "message": "File is empty"},
                "E003": {"name": "UNREADABLE", "message": "Cannot read artifact"},
            },
            warning_codes={},

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

        if os.path.getsize(artifact_path) == 0:
            return False, f"File is empty: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute artifact detection."""
        from ..adapters.core.file_adapter import FileAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        compute_hash = inputs.get("compute_hash", False)

        # Get adapter
        adapter = FileAdapter()

        # Detect type
        result = adapter.detect_type(artifact_path)

        if not result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E003",
                error_message=result.error or "Detection failed",
            )

        # Build metadata
        metadata = {
            "artifact_type": result.metadata.get("artifact_type", "unknown"),
            "mime_type": result.metadata.get("mime_type", ""),
            "description": result.metadata.get("description", ""),
            "size_bytes": result.metadata.get("size_bytes", 0),
            "path": artifact_path,
        }

        if compute_hash:
            import hashlib
            sha256_hash = hashlib.sha256()
            with open(artifact_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            metadata["sha256"] = sha256_hash.hexdigest()

        # Create evidence
        evidence: List[EvidenceRecord] = []
        evidence.append(EvidenceRecord(
            id=self._next_evidence_id(),
            type="raw",
            capability_id=self.id,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            file_path=artifact_path,
            sha256=metadata.get("sha256", ""),
            size=metadata.get("size_bytes", 0),
        ))

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={"artifact_path": artifact_path},
            adapter_id=adapter.id,
            working_directory=os.getcwd(),
        )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            evidence=evidence,
            provenance=provenance,
        )


# =============================================================================
# CAP-002: ipa.validate
# =============================================================================

class IpaValidateCapability(CapabilityExecutor):
    """
    Validate IPA archive integrity.

    Contract: ipa.validate v1.0.0
    Domain: foundation
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="ipa.validate",
            version="1.0.0",
            domain="foundation",
            name="IPA Validation",
            description="Validate that a file is a valid IPA archive",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to IPA file"},
            ],
            optional_inputs=[],

            supported_input_types=["ipa", "zip_archive"],
            output_types=["validation_result"],

            required_adapters=["unzip_adapter"],
            optional_adapters=["python_zipfile"],

            error_codes={
                "E001": {"name": "INVALID_FORMAT", "message": "Not a valid IPA/ZIP archive"},
                "E002": {"name": "CORRUPT_ARCHIVE", "message": "Archive is corrupt"},
                "E003": {"name": "NO_PAYLOAD", "message": "Archive does not contain Payload directory"},
                "E004": {"name": "NOT_FOUND", "message": "File not found"},
            },
            warning_codes={
                "W001": {"name": "SYMLINKS_IGNORED", "message": "Archive contains symbolic links"},
                "W002": {"name": "DUPLICATES", "message": "Archive contains duplicate entries"},
            },

            stop_on=["E001", "E002", "E004"],
            abort_workflow_on=["E001", "E004"],
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
            return False, f"IPA not found: {artifact_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute IPA validation."""
        from ..adapters.core.unzip_adapter import UnzipAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]

        # Get adapter
        adapter = UnzipAdapter()

        # Validate
        result = adapter.validate_ipa(artifact_path)

        warnings = []
        is_valid = result.metadata.get("is_valid", False)
        errors = result.metadata.get("errors", [])

        # Add warnings
        for w in result.metadata.get("warnings", []):
            warnings.append({"code": "W001", "message": w})

        # Determine status
        if result.success and is_valid:
            # Check for Payload directory
            if "Payload/" not in result.stdout and "Payload\\" not in result.stdout:
                warnings.append({"code": "W003", "message": "Payload directory not confirmed"})

            return CapabilityResult.success(
                execution_id=execution_id,
                metadata={
                    "is_valid": True,
                    "has_payload": True,
                    "validation_errors": errors,
                    "warnings": warnings,
                },
                provenance=ProvenanceRecord(
                    capability_id=self.id,
                    capability_version=self.version,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow(),
                    inputs={"artifact_path": artifact_path},
                    adapter_id=adapter.id,
                    working_directory=os.getcwd(),
                ),
                warnings=warnings,
            )
        else:
            # Determine error code
            if errors:
                error_code = "E001"
                error_message = errors[0]
            else:
                error_code = "E001"
                error_message = "Validation failed"

            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code=error_code,
                error_message=error_message,
                provenance=ProvenanceRecord(
                    capability_id=self.id,
                    capability_version=self.version,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow(),
                    inputs={"artifact_path": artifact_path},
                    adapter_id=adapter.id,
                    working_directory=os.getcwd(),
                    error_code=error_code,
                    error_message=error_message,
                ),
            )


# =============================================================================
# CAP-003: ipa.unpack
# =============================================================================

class IpaUnpackCapability(CapabilityExecutor):
    """
    Extract IPA contents.

    Contract: ipa.unpack v1.0.0
    Domain: foundation
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="ipa.unpack",
            version="1.0.0",
            domain="foundation",
            name="IPA Unpacking",
            description="Extract IPA archive contents to a directory",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to IPA file"},
                {"name": "output_dir", "type": "path", "description": "Output directory"},
            ],
            optional_inputs=[
                {"name": "overwrite", "type": "boolean", "default": False},
                {"name": "flatten", "type": "boolean", "default": False},
            ],

            supported_input_types=["ipa"],
            output_types=["extracted_payload", "extraction_log"],

            required_adapters=["unzip_adapter"],
            optional_adapters=["sevenzip_adapter", "python_zipfile"],

            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "IPA not found"},
                "E002": {"name": "NOT_WRITABLE", "message": "Output directory is not writable"},
                "E003": {"name": "EXTRACTION_FAILED", "message": "Extraction failed"},
            },
            warning_codes={
                "W001": {"name": "SKIPPED_FILES", "message": "Some files were skipped"},
                "W002": {"name": "PERMISSION_DENIED", "message": "Some files could not be extracted"},
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
        output_dir = inputs.get("output_dir")

        if not artifact_path:
            return False, "artifact_path is required"

        if not output_dir:
            return False, "output_dir is required"

        if not os.path.exists(artifact_path):
            return False, f"IPA not found: {artifact_path}"

        # Check if output dir is writable
        try:
            os.makedirs(output_dir, exist_ok=True)
            test_file = os.path.join(output_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            return False, f"Output directory is not writable: {e}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute IPA unpacking."""
        from ..adapters.core.unzip_adapter import UnzipAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        output_dir = inputs["output_dir"]
        overwrite = inputs.get("overwrite", False)

        # Clean output if overwriting
        if overwrite and os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        # Get adapter
        adapter = UnzipAdapter()

        # Unpack
        result = adapter.unpack(artifact_path, output_dir, overwrite)

        warnings = []
        evidence: List[EvidenceRecord] = []
        partial = False

        if result.success:
            # Check for partial success
            if result.metadata.get("partial"):
                partial = True
                warnings.append({
                    "code": "W001",
                    "message": f"Some files were skipped: {result.error}"
                })

            # Count extracted files
            files_extracted = result.metadata.get("files_extracted", 0)

            # Create evidence
            if os.path.exists(output_dir):
                evidence.append(EvidenceRecord(
                    id=self._next_evidence_id(),
                    type="derived",
                    capability_id=self.id,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow(),
                    file_path=output_dir,
                    sha256="",
                    size=result.metadata.get("total_size_bytes", 0),
                ))

            # Create provenance
            provenance = ProvenanceRecord(
                capability_id=self.id,
                capability_version=self.version,
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                inputs={
                    "artifact_path": artifact_path,
                    "output_dir": output_dir,
                    "overwrite": overwrite,
                },
                adapter_id=adapter.id,
                working_directory=os.getcwd(),
                output_artifacts=[{"path": output_dir}],
            )

            return CapabilityResult(
                status=CapabilityStatus.PARTIAL if partial else CapabilityStatus.SUCCESS,
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                metadata={
                    "files_extracted": files_extracted,
                    "output_dir": output_dir,
                    "total_size_bytes": result.metadata.get("total_size_bytes", 0),
                    "partial": partial,
                },
                artifacts=[output_dir],
                evidence=evidence,
                provenance=provenance,
                warnings=warnings,
            )
        else:
            # Check for partial extraction
            if os.path.exists(output_dir):
                files = list(os.walk(output_dir))
                if files:
                    partial = True
                    warnings.append({
                        "code": "W001",
                        "message": "Partial extraction occurred"
                    })

                    return CapabilityResult.partial(
                        execution_id=execution_id,
                        metadata={
                            "output_dir": output_dir,
                            "partial": True,
                            "error": result.error,
                        },
                        artifacts=[output_dir],
                        provenance=ProvenanceRecord(
                            capability_id=self.id,
                            capability_version=self.version,
                            execution_id=execution_id,
                            timestamp=datetime.utcnow(),
                            inputs=inputs,
                            adapter_id=adapter.id,
                            working_directory=os.getcwd(),
                            error_code="E003",
                            error_message=result.error,
                        ),
                        warnings=warnings,
                    )

            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E003",
                error_message=result.error or "Extraction failed",
                provenance=ProvenanceRecord(
                    capability_id=self.id,
                    capability_version=self.version,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow(),
                    inputs=inputs,
                    adapter_id=adapter.id,
                    working_directory=os.getcwd(),
                    error_code="E003",
                    error_message=result.error,
                ),
            )


# =============================================================================
# CAP-004: bundle.inventory
# =============================================================================

class BundleInventoryCapability(CapabilityExecutor):
    """
    Inventory bundle contents.

    Contract: bundle.inventory v1.0.0
    Domain: foundation
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="bundle.inventory",
            version="1.0.0",
            domain="foundation",
            name="Bundle Inventory",
            description="Inventory contents of an app bundle, framework, or extension",

            required_inputs=[
                {"name": "bundle_path", "type": "path", "description": "Path to bundle"},
            ],
            optional_inputs=[
                {"name": "max_depth", "type": "integer", "default": None},
                {"name": "include_hidden", "type": "boolean", "default": False},
            ],

            supported_input_types=["app_bundle", "framework", "extension"],
            output_types=["bundle_contents"],

            required_adapters=["find_adapter"],
            optional_adapters=[],

            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Bundle not found"},
                "E002": {"name": "NOT_A_DIRECTORY", "message": "Bundle path is not a directory"},
            },
            warning_codes={},

            stop_on=["E001", "E002"],
            abort_workflow_on=["E001"],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        bundle_path = inputs.get("bundle_path")

        if not bundle_path:
            return False, "bundle_path is required"

        if not os.path.exists(bundle_path):
            return False, f"Bundle not found: {bundle_path}"

        if not os.path.isdir(bundle_path):
            return False, f"Not a directory: {bundle_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute bundle inventory."""
        from ..adapters.core.find_adapter import FindAdapter

        execution_id = self._generate_execution_id()
        bundle_path = inputs["bundle_path"]
        max_depth = inputs.get("max_depth")
        include_hidden = inputs.get("include_hidden", False)

        # Get adapter
        adapter = FindAdapter()

        # Inventory
        result = adapter.inventory_directory(
            bundle_path,
            max_depth=max_depth if not include_hidden else None
        )

        if not result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E999",
                error_message=result.error or "Inventory failed",
            )

        # Build metadata
        metadata = {
            "bundle_path": bundle_path,
            "file_count": result.metadata.get("file_count", 0),
            "directory_count": result.metadata.get("directory_count", 0),
            "total_size_bytes": result.metadata.get("total_size_bytes", 0),
            "file_types": result.metadata.get("file_types", {}),
            "files": result.metadata.get("files", [])[:100],  # Limit for output
        }

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id=adapter.id,
            working_directory=os.getcwd(),
        )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata=metadata,
            evidence=[],
            provenance=provenance,
        )


# =============================================================================
# CAP-005: plist.extract
# =============================================================================

class PlistExtractCapability(CapabilityExecutor):
    """
    Extract and parse plist files.

    Contract: plist.extract v1.0.0
    Domain: foundation
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="plist.extract",
            version="1.0.0",
            domain="foundation",
            name="Plist Extraction",
            description="Extract and parse Info.plist and entitlements files",

            required_inputs=[
                {"name": "plist_path", "type": "path", "description": "Path to plist file"},
            ],
            optional_inputs=[
                {"name": "extract_keys", "type": "array", "default": None},
            ],

            supported_input_types=["plist", "entitlements"],
            output_types=["plist_data"],

            required_adapters=["plutil_adapter"],
            optional_adapters=["python_plistlib"],

            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Plist not found"},
                "E002": {"name": "PARSE_FAILED", "message": "Failed to parse plist"},
            },
            warning_codes={},

            stop_on=["E001", "E002"],
            abort_workflow_on=["E002"],
        )

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        plist_path = inputs.get("plist_path")

        if not plist_path:
            return False, "plist_path is required"

        if not os.path.exists(plist_path):
            return False, f"Plist not found: {plist_path}"

        return True, None

    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """Execute plist extraction."""
        from ..adapters.core.plutil_adapter import PlutilAdapter

        execution_id = self._generate_execution_id()
        plist_path = inputs["plist_path"]
        extract_keys = inputs.get("extract_keys")

        # Get adapter
        adapter = PlutilAdapter()

        # Check if plutil is available
        if not adapter.is_available():
            # Fallback to Python
            return self._parse_with_python(execution_id, plist_path, extract_keys)

        # Parse
        result = adapter.parse_plist(plist_path)

        if not result.success:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E002",
                error_message=result.error or "Parse failed",
            )

        plist_data = result.metadata.get("plist_data", {})

        # Filter keys if requested
        if extract_keys:
            filtered = {k: plist_data.get(k) for k in extract_keys if k in plist_data}
            plist_data = filtered

        # Create provenance
        provenance = ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs={"plist_path": plist_path, "extract_keys": extract_keys},
            adapter_id=adapter.id,
            working_directory=os.getcwd(),
        )

        return CapabilityResult.success(
            execution_id=execution_id,
            metadata={
                "plist_data": plist_data,
                "format": result.metadata.get("format", "unknown"),
                "plist_path": plist_path,
                "key_count": len(plist_data),
            },
            provenance=provenance,
        )

    def _parse_with_python(
        self,
        execution_id: str,
        plist_path: str,
        extract_keys: Optional[List[str]]
    ) -> CapabilityResult:
        """Fallback to Python plistlib."""
        try:
            import plistlib
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)

            if extract_keys:
                plist_data = {k: plist_data.get(k) for k in extract_keys if k in plist_data}

            return CapabilityResult.success(
                execution_id=execution_id,
                metadata={
                    "plist_data": plist_data,
                    "format": "binary",
                    "plist_path": plist_path,
                    "key_count": len(plist_data),
                    "parsed_with": "python_plistlib",
                },
                provenance=ProvenanceRecord(
                    capability_id=self.id,
                    capability_version=self.version,
                    execution_id=execution_id,
                    timestamp=datetime.utcnow(),
                    inputs={"plist_path": plist_path},
                    adapter_id="python_plistlib",
                    working_directory=os.getcwd(),
                ),
            )
        except Exception as e:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E002",
                error_message=f"Parse failed: {e}",
            )


# =============================================================================
# CAP-006: entitlements.extract
# =============================================================================

class EntitlementsExtractCapability(CapabilityExecutor):
    """
    Extract code signing entitlements.

    Contract: entitlements.extract v1.0.0
    Domain: foundation
    """

    def get_contract(self) -> CapabilityContract:
        return CapabilityContract(
            id="entitlements.extract",
            version="1.0.0",
            domain="foundation",
            name="Entitlements Extraction",
            description="Extract code signing entitlements from a binary or bundle",

            required_inputs=[
                {"name": "artifact_path", "type": "path", "description": "Path to binary or bundle"},
            ],
            optional_inputs=[
                {"name": "output_path", "type": "path", "description": "Output path for entitlements file"},
            ],

            supported_input_types=["macho", "macho_executable", "app_bundle"],
            output_types=["entitlements_data"],

            required_adapters=["codesign_adapter", "plutil_adapter"],
            optional_adapters=[],

            error_codes={
                "E001": {"name": "NOT_FOUND", "message": "Artifact not found"},
                "E002": {"name": "NO_ENTITLEMENTS", "message": "No entitlements found"},
                "E003": {"name": "EXTRACTION_FAILED", "message": "Failed to extract entitlements"},
            },
            warning_codes={},

            stop_on=["E001", "E003"],
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
        """Execute entitlements extraction."""
        from ..adapters.core.codesign_adapter import CodesignAdapter
        from ..adapters.core.plutil_adapter import PlutilAdapter

        execution_id = self._generate_execution_id()
        artifact_path = inputs["artifact_path"]
        output_path = inputs.get("output_path")

        # Try codesign first
        codesign_adapter = CodesignAdapter()

        if codesign_adapter.is_available():
            result = codesign_adapter.extract_entitlements(artifact_path)

            if result.success:
                entitlements = result.metadata.get("entitlements", {})

                # Save to file if requested
                if output_path:
                    try:
                        import plistlib
                        with open(output_path, 'wb') as f:
                            plistlib.dump(entitlements, f)
                    except Exception:
                        pass

                return CapabilityResult.success(
                    execution_id=execution_id,
                    metadata={
                        "entitlements": entitlements,
                        "entitlement_keys": result.metadata.get("entitlement_keys", []),
                        "has_keychain_access": result.metadata.get("has_keychain_access", False),
                        "has_network_access": result.metadata.get("has_network_access", False),
                        "has_app_groups": result.metadata.get("has_app_groups", False),
                        "artifact_path": artifact_path,
                    },
                    artifacts=[output_path] if output_path else [],
                    provenance=ProvenanceRecord(
                        capability_id=self.id,
                        capability_version=self.version,
                        execution_id=execution_id,
                        timestamp=datetime.utcnow(),
                        inputs=inputs,
                        adapter_id=codesign_adapter.id,
                        working_directory=os.getcwd(),
                    ),
                )
            else:
                return CapabilityResult.failure(
                    execution_id=execution_id,
                    error_code="E003",
                    error_message=result.error or "Extraction failed",
                )

        # Fallback: try to find embedded entitlements
        plist_adapter = PlutilAdapter()
        entitlements_path = None

        # Check common locations
        if artifact_path.endswith('.app'):
            base = artifact_path
            candidates = [
                os.path.join(base, "embedded.mobileprovision"),
                os.path.join(base, "Entitlements.plist"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    entitlements_path = candidate
                    break

        if entitlements_path and plist_adapter.is_available():
            result = plist_adapter.parse_plist(entitlements_path)
            if result.success:
                return CapabilityResult.success(
                    execution_id=execution_id,
                    metadata={
                        "entitlements": result.metadata.get("plist_data", {}),
                        "source": "embedded_file",
                        "artifact_path": entitlements_path,
                    },
                    provenance=ProvenanceRecord(
                        capability_id=self.id,
                        capability_version=self.version,
                        execution_id=execution_id,
                        timestamp=datetime.utcnow(),
                        inputs=inputs,
                        adapter_id="embedded_file",
                        working_directory=os.getcwd(),
                    ),
                )

        return CapabilityResult.failure(
            execution_id=execution_id,
            error_code="E003",
            error_message="No entitlements found and no tools available",
        )
