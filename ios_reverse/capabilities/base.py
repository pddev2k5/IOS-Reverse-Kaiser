"""
Capability Base Classes for IOS REVERSE KAISER.

Capabilities expose stable platform-level contracts.
Adapters are replaceable implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from enum import Enum
from datetime import datetime
import uuid
import hashlib
import os


class CapabilityError(Exception):
    """Base exception for capability errors."""
    pass


class PreconditionError(CapabilityError):
    """Raised when a precondition check fails."""
    pass


class AdapterUnavailableError(CapabilityError):
    """Raised when a required adapter is unavailable."""
    pass


class CapabilityExecutionError(CapabilityError):
    """Raised when capability execution fails."""
    pass


class PartialSuccessError(CapabilityError):
    """Raised when capability partially succeeds."""
    pass


class CapabilityStatus(Enum):
    """Capability execution status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class CapabilityContract:
    """Contract defining a capability's interface."""
    id: str
    version: str
    domain: str
    name: str
    description: str

    # Inputs
    required_inputs: List[Dict[str, Any]] = field(default_factory=list)
    optional_inputs: List[Dict[str, Any]] = field(default_factory=list)

    # Artifacts
    supported_input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)

    # Adapters
    required_adapters: List[str] = field(default_factory=list)
    optional_adapters: List[str] = field(default_factory=list)

    # Error codes
    error_codes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    warning_codes: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Stop conditions
    stop_on: List[str] = field(default_factory=list)
    abort_workflow_on: List[str] = field(default_factory=list)


@dataclass
class ProvenanceRecord:
    """Provenance record for capability execution."""
    capability_id: str
    capability_version: str
    execution_id: str
    timestamp: datetime

    # Inputs
    inputs: Dict[str, Any] = field(default_factory=dict)

    # Adapter
    adapter_id: Optional[str] = None
    adapter_version: Optional[str] = None

    # Environment
    working_directory: Optional[str] = None

    # Outputs
    output_artifacts: List[Dict[str, Any]] = field(default_factory=list)

    # Errors
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "inputs": self.inputs,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "working_directory": self.working_directory,
            "output_artifacts": self.output_artifacts,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass
class EvidenceRecord:
    """Evidence record for capability output."""
    id: str
    type: str  # raw, derived
    capability_id: str
    execution_id: str
    timestamp: datetime

    # Optional file info - may not be available for all evidence types
    file_path: Optional[str] = None
    sha256: Optional[str] = None
    size: Optional[int] = None

    # For derived evidence
    derived_from: List[str] = field(default_factory=list)
    references: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "capability_id": self.capability_id,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "file_path": self.file_path,
            "sha256": self.sha256,
            "size": self.size,
            "derived_from": self.derived_from,
            "references": self.references,
        }


@dataclass
class CapabilityResult:
    """Result from capability execution."""
    status: CapabilityStatus
    execution_id: str
    timestamp: datetime

    # Output data
    metadata: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

    # Evidence
    evidence: List[EvidenceRecord] = field(default_factory=list)

    # Provenance
    provenance: Optional[ProvenanceRecord] = None

    # Errors/Warnings
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[Dict[str, str]] = field(default_factory=list)

    # Schema version
    schema_version: str = "1.0"

    def to_dict(self) -> dict:
        """Serialize to normalized output format."""
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "artifacts": self.artifacts,
            "evidence": [e.to_dict() for e in self.evidence],
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "error": {
                "code": self.error_code,
                "message": self.error_message,
            } if self.error_code else None,
            "warnings": self.warnings,
        }

    @classmethod
    def success(
        cls,
        execution_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[str]] = None,
        evidence: Optional[List[EvidenceRecord]] = None,
        provenance: Optional[ProvenanceRecord] = None,
        warnings: Optional[List[Dict[str, str]]] = None,
    ) -> "CapabilityResult":
        """Create a success result."""
        return cls(
            status=CapabilityStatus.SUCCESS,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            artifacts=artifacts or [],
            evidence=evidence or [],
            provenance=provenance,
            warnings=warnings or [],
        )

    @classmethod
    def partial(
        cls,
        execution_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[str]] = None,
        evidence: Optional[List[EvidenceRecord]] = None,
        provenance: Optional[ProvenanceRecord] = None,
        warnings: Optional[List[Dict[str, str]]] = None,
    ) -> "CapabilityResult":
        """Create a partial success result."""
        return cls(
            status=CapabilityStatus.PARTIAL,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            artifacts=artifacts or [],
            evidence=evidence or [],
            provenance=provenance,
            warnings=warnings or [],
        )

    @classmethod
    def failure(
        cls,
        execution_id: str,
        error_code: str,
        error_message: str,
        provenance: Optional[ProvenanceRecord] = None,
    ) -> "CapabilityResult":
        """Create a failure result."""
        return cls(
            status=CapabilityStatus.FAILURE,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            error_code=error_code,
            error_message=error_message,
            provenance=provenance,
        )


class CapabilityExecutor(ABC):
    """
    Base class for capability executors.

    Capabilities expose stable platform-level contracts.
    Adapters are replaceable implementations.

    Subclasses must implement:
    - get_contract()
    - validate_preconditions()
    - execute_capability()
    """

    def __init__(self):
        self._contract: Optional[CapabilityContract] = None
        self._evidence_counter = 0

    @property
    def contract(self) -> CapabilityContract:
        """Get the capability contract."""
        if self._contract is None:
            self._contract = self.get_contract()
        return self._contract

    @property
    def id(self) -> str:
        """Get capability ID."""
        return self.contract.id

    @property
    def version(self) -> str:
        """Get capability version."""
        return self.contract.version

    @abstractmethod
    def get_contract(self) -> CapabilityContract:
        """Get the capability contract."""
        pass

    @abstractmethod
    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that preconditions are met.

        Args:
            inputs: Capability inputs

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def execute(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """
        Execute the capability.

        Args:
            inputs: Capability inputs
            context: Execution context

        Returns:
            CapabilityResult with normalized output
        """
        pass

    def _generate_execution_id(self) -> str:
        """Generate a unique execution ID."""
        return f"{self.id}-{uuid.uuid4().hex[:8]}"

    def _next_evidence_id(self) -> str:
        """Generate next evidence ID."""
        self._evidence_counter += 1
        return f"E-{self._evidence_counter:04d}"

    def _compute_sha256(self, file_path: str) -> str:
        """Compute SHA-256 of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def _create_evidence(
        self,
        file_path: str,
        evidence_type: str,
        execution_id: str,
        derived_from: Optional[List[str]] = None,
    ) -> EvidenceRecord:
        """Create an evidence record."""
        return EvidenceRecord(
            id=self._next_evidence_id(),
            type=evidence_type,
            capability_id=self.id,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            file_path=file_path,
            sha256=self._compute_sha256(file_path) if os.path.exists(file_path) else "",
            size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            derived_from=derived_from or [],
        )

    def _create_provenance(
        self,
        execution_id: str,
        inputs: Dict[str, Any],
        adapter_id: Optional[str] = None,
        adapter_version: Optional[str] = None,
        artifacts: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ProvenanceRecord:
        """Create a provenance record."""
        return ProvenanceRecord(
            capability_id=self.id,
            capability_version=self.version,
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id=adapter_id,
            adapter_version=adapter_version,
            working_directory=os.getcwd(),
            output_artifacts=[
                {"path": a, "size": os.path.getsize(a) if os.path.exists(a) else 0}
                for a in (artifacts or [])
            ],
            error_code=error_code,
            error_message=error_message,
        )

    def run(
        self,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CapabilityResult:
        """
        Run the capability with full lifecycle.

        This includes:
        - Precondition validation
        - Execution
        - Provenance recording
        - Error handling

        Args:
            inputs: Capability inputs
            context: Execution context

        Returns:
            CapabilityResult with normalized output
        """
        execution_id = self._generate_execution_id()

        # Validate preconditions
        valid, error = self.validate_preconditions(inputs)
        if not valid:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E001",
                error_message=error or "Precondition validation failed",
            )

        # Execute
        try:
            return self.execute(inputs, context)
        except Exception as e:
            return CapabilityResult.failure(
                execution_id=execution_id,
                error_code="E999",
                error_message=str(e),
            )
