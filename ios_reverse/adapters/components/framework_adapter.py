"""
Framework inventory adapter for IOS REVERSE KAISER.

Discovers and normalizes embedded frameworks.
"""

import os
import plistlib
import hashlib
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass

from ios_reverse.models.components import (
    ComponentType, Classification, OwnershipHint,
    FrameworkComponent, ExecutableIdentity, ArchitectureInfo,
    ComponentReference, ComponentGraph, DependencyEdge,
    generate_component_id, generate_edge_id, EdgeType, DependencyState
)
from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class FrameworkAdapter(ToolAdapter):
    """
    Adapter for discovering embedded frameworks.

    Distinguishes between:
    - Embedded frameworks (physically inside the application)
    - System/external dependencies (referenced but not embedded)
    """

    def __init__(self):
        super().__init__("framework_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="framework_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def discover_frameworks(
        self,
        app_bundle_path: str,
        context: Optional[TraversalContext] = None
    ) -> List[FrameworkComponent]:
        """
        Discover embedded frameworks in an application bundle.

        Args:
            app_bundle_path: Path to the .app bundle
            context: Optional traversal context for bounded traversal

        Returns:
            List of FrameworkComponent
        """
        if context is None:
            context = TraversalContext(
                root_path=app_bundle_path,
                visited_paths=set(),
                visited_artifacts=set()
            )

        frameworks = []

        # Find all frameworks in standard locations
        frameworks_dir = os.path.join(app_bundle_path, "Frameworks")
        if os.path.isdir(frameworks_dir):
            for entry in os.listdir(frameworks_dir):
                if entry.endswith(".framework"):
                    fw_path = os.path.join(frameworks_dir, entry)
                    if context.mark_visited(fw_path):
                        framework = self._parse_framework(
                            fw_path,
                            os.path.join("Frameworks", entry),
                            context,
                            app_bundle_path
                        )
                        if framework:
                            frameworks.append(framework)

        # Also check PlugIns for frameworks inside extensions
        plugins_dir = os.path.join(app_bundle_path, "PlugIns")
        if os.path.isdir(plugins_dir):
            for entry in os.listdir(plugins_dir):
                if entry.endswith(".appex"):
                    ext_path = os.path.join(plugins_dir, entry)
                    ext_frameworks_dir = os.path.join(ext_path, "Frameworks")
                    if os.path.isdir(ext_frameworks_dir):
                        for fw_entry in os.listdir(ext_frameworks_dir):
                            if fw_entry.endswith(".framework"):
                                fw_full_path = os.path.join(ext_frameworks_dir, fw_entry)
                                if context.mark_visited(fw_full_path):
                                    rel_path = os.path.join("PlugIns", entry, "Frameworks", fw_entry)
                                    framework = self._parse_framework(
                                        fw_full_path, rel_path, context, app_bundle_path
                                    )
                                    if framework:
                                        frameworks.append(framework)

        return frameworks

    def _parse_framework(
        self,
        framework_path: str,
        bundle_path: str,
        context: TraversalContext,
        app_bundle_path: str
    ) -> Optional[FrameworkComponent]:
        """
        Parse a framework bundle into a FrameworkComponent.

        Args:
            framework_path: Absolute path to the framework
            bundle_path: Relative path within the app
            context: Traversal context
            app_bundle_path: Path to the containing app

        Returns:
            FrameworkComponent or None if parsing fails
        """
        if not os.path.isdir(framework_path):
            return None

        framework_name = os.path.basename(framework_path).replace('.framework', '')

        # Compute artifact ID
        # For frameworks, use the directory hash (less precise but consistent)
        artifact_id = self._compute_bundle_artifact_id(framework_path)
        if not artifact_id:
            return None

        # Generate component ID
        component_id = generate_component_id(framework_name, artifact_id, bundle_path)

        # Check if we've already processed this artifact
        if not context.mark_artifact_visited(artifact_id):
            # Already processed - return None to avoid duplicates
            return None

        # Parse Info.plist if present
        info_plist_path = os.path.join(framework_path, "Versions", "Current", "Info.plist")
        if not os.path.exists(info_plist_path):
            # Try root level
            info_plist_path = os.path.join(framework_path, "Info.plist")

        bundle_identifier = None
        version = None

        if os.path.exists(info_plist_path):
            try:
                with open(info_plist_path, 'rb') as f:
                    plist = plistlib.load(f)
                    bundle_identifier = plist.get("CFBundleIdentifier")
                    version = plist.get("CFBundleVersion")
            except Exception:
                pass

        # Find executable
        executable = self._find_framework_executable(framework_path, artifact_id)

        # Classify framework
        classification = self._classify_framework(framework_name, bundle_identifier)

        # Create component
        framework = FrameworkComponent(
            component_id=component_id,
            component_type=ComponentType.FRAMEWORK,
            name=framework_name,
            bundle_path=bundle_path,
            artifact_id=artifact_id,
            bundle_identifier=bundle_identifier,
            version=version,
            executable=executable,
            info_plist_path=os.path.relpath(info_plist_path, framework_path) if os.path.exists(info_plist_path) else None,
            classification=classification,
            ownership_hint=OwnershipHint.UNKNOWN,  # Requires additional evidence
            provenance=["filesystem_discovery"],
        )

        return framework

    def _find_framework_executable(
        self,
        framework_path: str,
        bundle_artifact_id: str
    ) -> Optional[ExecutableIdentity]:
        """
        Find the executable within a framework bundle.
        """
        # Framework executables typically have the framework name
        framework_name = os.path.basename(framework_path).replace('.framework', '')

        # Common executable locations
        candidates = [
            os.path.join(framework_path, framework_name),
            os.path.join(framework_path, "Versions", "Current", framework_name),
            os.path.join(framework_path, "A", framework_name),  # Version A
        ]

        for candidate in candidates:
            if os.path.isfile(candidate):
                try:
                    with open(candidate, 'rb') as f:
                        content = f.read()
                        sha256 = hashlib.sha256(content).hexdigest()
                        artifact_id = sha256  # Use file hash as artifact ID

                        # Parse architectures
                        archs = self._detect_architectures(content)

                        return ExecutableIdentity(
                            path=os.path.relpath(candidate, framework_path),
                            artifact_id=artifact_id,
                            sha256=sha256,
                            size=len(content),
                            architectures=archs,
                            is_fat=len(archs) > 1,
                            slice_count=len(archs)
                        )
                except Exception:
                    pass

        return None

    def _detect_architectures(self, data: bytes) -> List[ArchitectureInfo]:
        """Detect Mach-O architectures in binary data."""
        archs = []

        # Check for Mach-O magic
        if len(data) < 4:
            return archs

        import struct

        # Check little-endian 64-bit
        if data[:4] in (b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe'):
            is_64bit = True
            # Simple architecture detection
            if b'ARM' in data[:1024] or self._contains_arm_magic(data):
                archs.append(ArchitectureInfo(
                    cpusubtype=0, cpu_type=0x0100000c,
                    name="arm64", is_64bit=True
                ))
            elif self._contains_x86_64_magic(data):
                archs.append(ArchitectureInfo(
                    cpusubtype=0, cpu_type=0x01000007,
                    name="x86_64", is_64bit=True
                ))

        return archs

    def _contains_arm_magic(self, data: bytes) -> bool:
        """Check for ARM64 magic in Mach-O header."""
        import struct
        # Look for CPU type for ARM64
        for i in range(min(256, len(data) - 8)):
            try:
                val = struct.unpack('<I', data[i:i+4])[0]
                if val == 0x0100000c:  # ARM64
                    return True
            except:
                pass
        return False

    def _contains_x86_64_magic(self, data: bytes) -> bool:
        """Check for x86_64 magic in Mach-O header."""
        import struct
        for i in range(min(256, len(data) - 8)):
            try:
                val = struct.unpack('<I', data[i:i+4])[0]
                if val == 0x01000007:  # x86_64
                    return True
            except:
                pass
        return False

    def _compute_bundle_artifact_id(self, bundle_path: str) -> Optional[str]:
        """
        Compute artifact ID for a bundle directory.

        Uses a composite of the bundle's Info.plist and executable if available.
        """
        import hashlib

        hasher = hashlib.sha256()

        # Include bundle structure indicator
        hasher.update(bundle_path.encode())

        # Try to include Info.plist
        info_paths = [
            os.path.join(bundle_path, "Info.plist"),
            os.path.join(bundle_path, "Versions", "Current", "Info.plist"),
        ]

        for info_path in info_paths:
            if os.path.exists(info_path):
                try:
                    with open(info_path, 'rb') as f:
                        hasher.update(f.read())
                except Exception:
                    pass
                break

        return hasher.hexdigest()

    def _classify_framework(
        self,
        framework_name: str,
        bundle_identifier: Optional[str]
    ) -> Classification:
        """
        Classify framework as embedded, system, or unknown.
        """
        # If it's a known system framework, mark as external
        if ComponentTraversal.is_system_framework(framework_name):
            return Classification.SYSTEM_EXTERNAL

        if ComponentTraversal.is_system_framework(f"{framework_name}.framework"):
            return Classification.SYSTEM_EXTERNAL

        # Otherwise, it's embedded within the app
        return Classification.EMBEDDED

    def extract_framework_dependencies(
        self,
        framework_path: str,
        component_id: str,
        rpath_resolvers: Optional[List[str]] = None
    ) -> List[DependencyEdge]:
        """
        Extract framework dependencies from Mach-O load commands.

        Args:
            framework_path: Path to the framework
            component_id: Component ID of this framework
            rpath_resolvers: Paths to resolve @rpath

        Returns:
            List of DependencyEdge
        """
        edges = []

        executable_path = self._find_framework_executable_path(framework_path)
        if not executable_path:
            return edges

        try:
            with open(executable_path, 'rb') as f:
                data = f.read()

            # Parse load commands to find dependencies
            deps = self._parse_load_commands(data)
            for install_name, edge_type, is_weak in deps:
                state = DependencyState.UNRESOLVED

                # Try to resolve the dependency
                if not ComponentTraversal.is_system_framework(install_name):
                    resolved_path = self._resolve_dependency(
                        install_name, executable_path, rpath_resolvers or []
                    )
                    if resolved_path and os.path.exists(resolved_path):
                        state = DependencyState.RESOLVED_EMBEDDED

                edge = DependencyEdge(
                    edge_id=generate_edge_id(component_id, None, install_name),
                    source_id=component_id,
                    target_id=None,  # Will be resolved later
                    edge_type=edge_type,
                    install_name=install_name,
                    resolved_path=resolved_path if state == DependencyState.RESOLVED_EMBEDDED else None,
                    state=state,
                    evidence=["load_command_analysis"],
                    is_weak=is_weak
                )
                edges.append(edge)

        except Exception:
            pass

        return edges

    def _find_framework_executable_path(self, framework_path: str) -> Optional[str]:
        """Find the framework's executable path."""
        framework_name = os.path.basename(framework_path).replace('.framework', '')

        candidates = [
            os.path.join(framework_path, framework_name),
            os.path.join(framework_path, "Versions", "Current", framework_name),
        ]

        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        return None

    def _parse_load_commands(self, data: bytes) -> List[Tuple[str, EdgeType, bool]]:
        """Parse LC_LOAD_DYLIB commands from Mach-O data."""
        deps = []

        import struct

        if len(data) < 32:
            return deps

        # Check magic
        magic = struct.unpack('<I', data[:4])[0]
        is_64bit = magic in (0xfeedfacf, 0xcffaedfe)

        if not is_64bit:
            return deps

        # Parse header
        if magic == 0xfeedfacf:  # Little endian
            header = struct.unpack('<IIIIIIII', data[:32])
        else:  # Big endian
            header = struct.unpack('>IIIIIIII', data[:32])

        ncmds = header[6]
        cmds_size = header[7]
        offset = 32 if is_64bit else 28

        for _ in range(ncmds):
            if offset + 8 > len(data):
                break

            cmd, size = struct.unpack('<II', data[offset:offset+8])

            # LC_LOAD_DYLIB = 0x0c
            # LC_LOAD_WEAK_DYLIB = 0x18
            # LC_REEXPORT_DYLIB = 0x8000001f
            if cmd in (0x0c, 0x18, 0x8000001f):
                try:
                    str_offset = struct.unpack('<I', data[offset+8:offset+12])[0]
                    str_start = offset + str_offset
                    str_end = data.find(b'\x00', str_start)
                    if str_end > str_start:
                        name = data[str_start:str_end].decode('utf-8', errors='replace')

                        if cmd == 0x18:
                            edge_type = EdgeType.WEAK_LOADS
                            is_weak = True
                        elif cmd == 0x8000001f:
                            edge_type = EdgeType.REEXPORTS
                            is_weak = False
                        else:
                            edge_type = EdgeType.LOADS
                            is_weak = False

                        deps.append((name, edge_type, is_weak))
                except Exception:
                    pass

            offset += size

        return deps

    def _resolve_dependency(
        self,
        install_name: str,
        executable_path: str,
        rpath_resolvers: List[str]
    ) -> Optional[str]:
        """
        Resolve a dependency path.

        Handles @rpath, @loader_path, @executable_path prefixes.
        """
        if install_name.startswith("@rpath/"):
            rpath_name = install_name[7:]
            for rpath in rpath_resolvers:
                candidate = os.path.join(rpath, rpath_name)
                if os.path.exists(candidate):
                    return candidate
        elif install_name.startswith("@loader_path/"):
            base_dir = os.path.dirname(executable_path)
            rel_path = install_name[13:]
            candidate = os.path.join(base_dir, rel_path)
            if os.path.exists(candidate):
                return candidate
        elif install_name.startswith("@executable_path/"):
            # Would need the app's executable path
            pass

        return None
