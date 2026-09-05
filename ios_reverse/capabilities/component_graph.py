"""
Component Graph Capability for IOS REVERSE KAISER.

EP-04.4E: Component graph and eligible executable set.
Combines all inventory capabilities into a unified component graph.
"""

import os
import plistlib
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.models.components import (
    ComponentType, Classification, DependencyState, EdgeType,
    AppComponent, FrameworkComponent, DylibComponent, ExtensionComponent,
    ExecutableIdentity, DependencyEdge, ComponentGraph,
    generate_component_id, generate_edge_id
)
from ios_reverse.adapters.components.framework_adapter import FrameworkAdapter
from ios_reverse.adapters.components.dylib_adapter import DylibAdapter
from ios_reverse.adapters.components.extension_adapter import ExtensionAdapter
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class ComponentGraphContract(CapabilityContract):
    """Contract for component graph capability."""

    def __init__(self):
        super().__init__(
            id="component.graph",
            version="1.0.0",
            domain="components",
            name="Component Graph",
            description="Build unified component graph and eligible executable set"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "build_dependencies", "type": "boolean", "default": True},
        ]
        self.supported_input_types = ["app_bundle"]
        self.output_types = ["component_graph", "eligible_executables"]
        self.required_adapters = []
        self.optional_adapters = ["framework_adapter", "dylib_adapter", "extension_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "GRAPH_BUILD_FAILED", "description": "Component graph build failed"},
        }
        self.warning_codes = {
            "W001": {"name": "CYCLE_DETECTED", "description": "Dependency cycle detected"},
            "W002": {"name": "UNRESOLVED_DEPS", "description": "Some dependencies could not be resolved"},
        }


class ComponentGraphCapability(CapabilityExecutor):
    """
    EP-04.4E: Build unified component graph and eligible executable set.

    This capability combines:
    - Framework discovery
    - Dylib discovery
    - Extension discovery
    - Dependency resolution
    - Eligible executable set

    The eligible_executables[] becomes the canonical input for later
    dump-full/deep analysis workflows.
    """

    def __init__(self):
        super().__init__()
        self._framework_adapter = FrameworkAdapter()
        self._dylib_adapter = DylibAdapter()
        self._extension_adapter = ExtensionAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return ComponentGraphContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"comp-graph-{self._id_counter:04d}"

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

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """
        Build component graph and eligible executable set.

        Args:
            inputs: Must contain artifact_path

        Returns:
            CapabilityResult with component graph
        """
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        valid, error = self.validate_preconditions(inputs)
        if not valid:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E001",
                error_message=error
            )

        artifact_path = inputs["artifact_path"]
        build_dependencies = inputs.get("build_dependencies", True)

        try:
            # Create traversal context
            context = TraversalContext(
                root_path=artifact_path,
                visited_paths=set(),
                visited_artifacts=set()
            )

            # Build component graph
            graph = self._build_graph(artifact_path, context, build_dependencies)

            # Build result metadata
            metadata = {
                "artifact_path": artifact_path,
                "component_count": len(graph.components),
                "edge_count": len(graph.edges),
                "eligible_executable_count": len(graph.eligible_executables),
                "system_dependency_count": len(graph.system_dependencies),
                "component_types": self._summarize_component_types(graph),
                "eligible_executables": graph.eligible_executables,
                "warnings": graph.warnings,
            }

            status = CapabilityStatus.SUCCESS
            if graph.warnings:
                status = CapabilityStatus.PARTIAL

            return CapabilityResult(
                status=status,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata=metadata,
                provenance=self._build_provenance(execution_id, inputs),
                warnings=graph.warnings
            )

        except Exception as e:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E002",
                error_message=str(e)
            )

    def _build_graph(
        self,
        app_path: str,
        context: TraversalContext,
        build_dependencies: bool
    ) -> ComponentGraph:
        """Build the complete component graph."""
        graph = ComponentGraph(root_component_id="")

        # Step 1: Create the root application component
        app_component = self._create_app_component(app_path)
        if not app_component:
            graph.warnings.append("Could not parse application component")
            return graph

        graph.root_component_id = app_component.component_id
        graph.add_component(app_component)
        context.mark_artifact_visited(app_component.artifact_id)

        # Step 2: Discover embedded frameworks
        frameworks = self._framework_adapter.discover_frameworks(app_path, context)
        for fw in frameworks:
            graph.add_component(fw)
            app_component.embedded_components.append(fw.component_id)

        # Step 3: Discover embedded dylibs
        dylibs = self._dylib_adapter.discover_dylibs(app_path, context, app_component.component_id)
        for dylib in dylibs:
            graph.add_component(dylib)
            app_component.embedded_components.append(dylib.component_id)

        # Step 4: Discover extensions
        extensions = self._extension_adapter.discover_extensions(
            app_path, context, app_component.component_id
        )
        for ext in extensions:
            graph.add_component(ext)
            app_component.embedded_components.append(ext.component_id)
            # Discover nested frameworks within extensions
            ext_path = os.path.join(app_path, ext.bundle_path)
            nested_fws = self._framework_adapter.discover_frameworks(ext_path, context)
            for nfw in nested_fws:
                if nfw.component_id not in graph.components:
                    graph.add_component(nfw)
                    ext.embedded_components.append(nfw.component_id)

        # Update app component
        graph.components[app_component.component_id] = app_component

        # Step 5: Build dependency edges
        if build_dependencies:
            self._build_dependency_edges(graph, app_path, context)

        # Step 6: Build eligible executable set
        self._build_eligible_executables(graph)

        # Build indexes
        graph.build_indexes()

        return graph

    def _create_app_component(self, app_path: str) -> Optional[AppComponent]:
        """Create the root application component."""
        if not app_path.endswith('.app'):
            return None

        app_name = os.path.basename(app_path).replace('.app', '')

        # Compute artifact ID
        artifact_id = self._compute_bundle_artifact_id(app_path)
        if not artifact_id:
            return None

        # Generate component ID
        component_id = generate_component_id(app_name, artifact_id, os.path.basename(app_path))

        # Parse Info.plist
        info_plist_path = os.path.join(app_path, "Info.plist")
        bundle_identifier = None
        version = None
        min_os_version = None

        if os.path.exists(info_plist_path):
            try:
                with open(info_plist_path, 'rb') as f:
                    plist = plistlib.load(f)
                    bundle_identifier = plist.get("CFBundleIdentifier")
                    version = plist.get("CFBundleVersion")
                    min_os_version = plist.get("MinimumOSVersion")
            except Exception:
                pass

        # Find main executable
        executable = self._find_main_executable(app_path, artifact_id)

        return AppComponent(
            component_id=component_id,
            component_type=ComponentType.APPLICATION,
            name=app_name,
            bundle_path=os.path.basename(app_path),
            artifact_id=artifact_id,
            bundle_identifier=bundle_identifier,
            version=version,
            min_os_version=min_os_version,
            info_plist_path="Info.plist",
            main_executable=executable,
            embedded_components=[],
            provenance=["filesystem_discovery", "info_plist"]
        )

    def _compute_bundle_artifact_id(self, bundle_path: str) -> Optional[str]:
        """Compute artifact ID for a bundle."""
        hasher = hashlib.sha256()
        hasher.update(bundle_path.encode())

        info_path = os.path.join(bundle_path, "Info.plist")
        if os.path.exists(info_path):
            try:
                with open(info_path, 'rb') as f:
                    hasher.update(f.read())
            except Exception:
                pass

        return hasher.hexdigest()

    def _find_main_executable(
        self,
        app_path: str,
        bundle_artifact_id: str
    ) -> Optional[ExecutableIdentity]:
        """Find the main executable in an app bundle."""
        app_name = os.path.basename(app_path).replace('.app', '')
        executable_path = os.path.join(app_path, app_name)

        if os.path.exists(executable_path):
            try:
                with open(executable_path, 'rb') as f:
                    data = f.read()
                    sha256 = hashlib.sha256(data).hexdigest()

                # Detect architectures
                archs = self._detect_architectures(data)

                return ExecutableIdentity(
                    path=app_name,
                    artifact_id=sha256,
                    sha256=sha256,
                    size=len(data),
                    architectures=archs,
                    is_fat=len(archs) > 1,
                    slice_count=len(archs)
                )
            except Exception:
                pass

        return None

    def _detect_architectures(self, data: bytes) -> List:
        """Detect Mach-O architectures."""
        import struct
        from ios_reverse.models.components import ArchitectureInfo

        archs = []
        if len(data) < 32:
            return archs

        magic = struct.unpack('<I', data[:4])[0]

        if magic == 0xfeedfacf:
            cputype = struct.unpack('<I', data[4:8])[0]
            if cputype == 0x0100000c:
                archs.append(ArchitectureInfo(0x0100000c, 0, "arm64", True))
            elif cputype == 0x01000007:
                archs.append(ArchitectureInfo(0x01000007, 0, "x86_64", True))

        return archs

    def _build_dependency_edges(
        self,
        graph: ComponentGraph,
        app_path: str,
        context: TraversalContext
    ):
        """Build dependency edges from Mach-O load commands."""
        # Collect rpath resolvers
        rpath_resolvers = []
        for comp_id, comp in graph.components.items():
            if hasattr(comp, 'bundle_path'):
                rpath_resolvers.append(os.path.join(app_path, os.path.dirname(comp.bundle_path)))

        # Build edges for each component with an executable
        for comp_id, comp in graph.components.items():
            if not hasattr(comp, 'executable') or not comp.executable:
                continue

            # Get the executable path
            if isinstance(comp, AppComponent) and comp.main_executable:
                exec_path = os.path.join(app_path, comp.main_executable.path)
            elif hasattr(comp, 'bundle_path'):
                exec_path = self._get_component_executable_path(app_path, comp)
            else:
                continue

            if not exec_path or not os.path.exists(exec_path):
                continue

            # Parse load commands
            edges = self._extract_load_commands(exec_path, comp_id, rpath_resolvers)

            for edge in edges:
                # Track system dependencies
                if ComponentTraversal.is_system_framework(edge.install_name):
                    graph.system_dependencies.add(edge.install_name)
                else:
                    graph.add_edge(edge)

    def _get_component_executable_path(
        self,
        app_path: str,
        comp
    ) -> Optional[str]:
        """Get the executable path for a component."""
        base_dir = os.path.join(app_path, os.path.dirname(comp.bundle_path))

        if isinstance(comp, FrameworkComponent) and comp.executable:
            return os.path.join(base_dir, comp.executable.path)
        elif isinstance(comp, DylibComponent) and comp.executable:
            return os.path.join(base_dir, comp.executable.path)
        elif isinstance(comp, ExtensionComponent) and comp.executable:
            return os.path.join(base_dir, comp.executable.path)

        return None

    def _extract_load_commands(
        self,
        executable_path: str,
        source_id: str,
        rpath_resolvers: List[str]
    ) -> List[DependencyEdge]:
        """Extract load command dependencies from executable."""
        edges = []

        try:
            with open(executable_path, 'rb') as f:
                data = f.read()
        except Exception:
            return edges

        import struct

        if len(data) < 32:
            return edges

        magic = struct.unpack('<I', data[:4])[0]
        is_64bit = magic in (0xfeedfacf, 0xcffaedfe)

        offset = 32 if is_64bit else 28
        ncmds = struct.unpack('<I', data[16:20])[0]

        for _ in range(ncmds):
            if offset + 8 > len(data):
                break

            cmd, size = struct.unpack('<II', data[offset:offset+8])

            if cmd in (0x0c, 0x18, 0x8000001f):  # LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB
                try:
                    str_offset = struct.unpack('<I', data[offset+8:offset+12])[0]
                    str_start = offset + str_offset
                    str_end = data.find(b'\x00', str_start)
                    if str_end > str_start:
                        install_name = data[str_start:str_end].decode('utf-8', errors='replace')

                        if cmd == 0x18:
                            edge_type = EdgeType.WEAK_LOADS
                            is_weak = True
                        elif cmd == 0x8000001f:
                            edge_type = EdgeType.REEXPORTS
                            is_weak = False
                        else:
                            edge_type = EdgeType.LOADS
                            is_weak = False

                        # Try to resolve
                        state = DependencyState.UNRESOLVED
                        resolved_path = None

                        if not ComponentTraversal.is_system_framework(install_name):
                            resolved_path = self._resolve_dependency(
                                install_name, executable_path, rpath_resolvers
                            )
                            if resolved_path:
                                state = DependencyState.RESOLVED_EMBEDDED

                        edge = DependencyEdge(
                            edge_id=generate_edge_id(source_id, None, install_name),
                            source_id=source_id,
                            target_id=None,
                            edge_type=edge_type,
                            install_name=install_name,
                            resolved_path=resolved_path,
                            state=state,
                            evidence=["load_command_analysis"],
                            is_weak=is_weak
                        )
                        edges.append(edge)
                except Exception:
                    pass

            offset += size

        return edges

    def _resolve_dependency(
        self,
        install_name: str,
        executable_path: str,
        rpath_resolvers: List[str]
    ) -> Optional[str]:
        """Resolve a dependency path."""
        if install_name.startswith("@rpath/"):
            name = install_name[7:]
            for rpath in rpath_resolvers:
                candidate = os.path.join(rpath, name)
                if os.path.exists(candidate):
                    return candidate
        elif install_name.startswith("@loader_path/"):
            base_dir = os.path.dirname(executable_path)
            rel_path = install_name[13:]
            candidate = os.path.join(base_dir, rel_path)
            if os.path.exists(candidate):
                return candidate

        return None

    def _build_eligible_executables(self, graph: ComponentGraph):
        """
        Build the canonical eligible_executables set.

        This is the deterministic set of executable components that
        should be analyzed by dump-full later.
        """
        eligible = []

        for comp_id, comp in graph.components.items():
            # Skip system dependencies
            if comp.component_id in graph.system_dependencies:
                continue

            # Check if this component has an executable
            has_executable = False

            if isinstance(comp, AppComponent) and comp.main_executable:
                has_executable = True
            elif isinstance(comp, FrameworkComponent) and comp.executable:
                has_executable = True
            elif isinstance(comp, DylibComponent) and comp.executable:
                has_executable = True
            elif isinstance(comp, ExtensionComponent) and comp.executable:
                has_executable = True

            if has_executable:
                eligible.append(comp_id)

        # Sort for determinism
        graph.eligible_executables = sorted(set(eligible))

    def _summarize_component_types(self, graph: ComponentGraph) -> Dict[str, int]:
        """Summarize component types in the graph."""
        summary = {}
        for comp in graph.components.values():
            type_name = comp.component_type.value
            summary[type_name] = summary.get(type_name, 0) + 1
        return summary

    def _build_provenance(
        self,
        execution_id: str,
        inputs: Dict
    ) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="component.graph",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            working_directory=os.getcwd(),
        )
