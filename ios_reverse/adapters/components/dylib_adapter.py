"""
Dylib inventory adapter for IOS REVERSE KAISER.

Discovers and normalizes embedded dynamic libraries.
"""

import os
import hashlib
from typing import Dict, Any, Optional, List, Set, Tuple

from ios_reverse.models.components import (
    ComponentType, DylibComponent, ExecutableIdentity, ArchitectureInfo,
    ComponentGraph, DependencyEdge, generate_component_id, generate_edge_id,
    EdgeType, DependencyState
)
from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class DylibAdapter(ToolAdapter):
    """
    Adapter for discovering embedded dylibs.

    Distinguishes between:
    - Embedded dylibs (physically inside the application)
    - External/system dependencies (referenced but not embedded)
    """

    def __init__(self):
        super().__init__("dylib_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="dylib_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def discover_dylibs(
        self,
        base_path: str,
        context: Optional[TraversalContext] = None,
        parent_id: Optional[str] = None
    ) -> List[DylibComponent]:
        """
        Discover embedded dylibs in a path.

        Args:
            base_path: Path to search for dylibs
            context: Optional traversal context
            parent_id: Parent component ID

        Returns:
            List of DylibComponent
        """
        if context is None:
            context = TraversalContext(
                root_path=base_path,
                visited_paths=set(),
                visited_artifacts=set()
            )

        dylibs = []

        # Common locations for embedded dylibs
        search_locations = [
            ("", base_path),  # Root directory
            ("Frameworks", os.path.join(base_path, "Frameworks")),
            ("PlugIns", os.path.join(base_path, "PlugIns")),
        ]

        for location_name, search_dir in search_locations:
            if not os.path.isdir(search_dir):
                continue

            try:
                for entry in os.listdir(search_dir):
                    # Skip frameworks and extensions (handled by other adapters)
                    if entry.endswith(('.framework', '.appex', '.app')):
                        continue

                    if entry.endswith(('.dylib', '.so')) or '.' not in entry:
                        dylib_path = os.path.join(search_dir, entry)

                        if not os.path.isfile(dylib_path):
                            continue

                        if not context.mark_visited(dylib_path):
                            continue

                        if location_name:
                            rel_path = os.path.join(location_name, entry)
                        else:
                            rel_path = entry

                        dylib = self._parse_dylib(
                            dylib_path, rel_path, context, parent_id
                        )
                        if dylib:
                            dylibs.append(dylib)
            except PermissionError:
                pass

        return dylibs

    def _parse_dylib(
        self,
        dylib_path: str,
        bundle_path: str,
        context: TraversalContext,
        parent_id: Optional[str]
    ) -> Optional[DylibComponent]:
        """
        Parse a dylib file into a DylibComponent.
        """
        try:
            with open(dylib_path, 'rb') as f:
                data = f.read()
        except Exception:
            return None

        # Compute artifact ID
        artifact_id = hashlib.sha256(data).hexdigest()

        if not context.mark_artifact_visited(artifact_id):
            return None

        # Check if it's a Mach-O file
        if len(data) < 4 or data[:4] not in (b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe'):
            # Not a Mach-O file
            return None

        dylib_name = os.path.basename(dylib_path)

        # Generate component ID
        component_id = generate_component_id(dylib_name, artifact_id, bundle_path)

        # Parse dylib identity from Mach-O
        install_name, version = self._parse_dylib_identity(data)

        # Parse architectures
        archs = self._detect_architectures(data)

        executable = ExecutableIdentity(
            path=bundle_path,
            artifact_id=artifact_id,
            sha256=artifact_id,
            size=len(data),
            architectures=archs,
            is_fat=len(archs) > 1,
            slice_count=len(archs)
        )

        return DylibComponent(
            component_id=component_id,
            component_type=ComponentType.DYLIB,
            name=dylib_name,
            bundle_path=bundle_path,
            artifact_id=artifact_id,
            install_name=install_name,
            version=version,
            executable=executable,
            provenance=["filesystem_discovery"],
            parent_id=parent_id
        )

    def _parse_dylib_identity(self, data: bytes) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse dylib identity from Mach-O.
        """
        import struct

        if len(data) < 32:
            return None, None

        magic = struct.unpack('<I', data[:4])[0]
        is_64bit = magic in (0xfeedfacf, 0xcffaedfe)

        offset = 32 if is_64bit else 28
        ncmds = struct.unpack('<I', data[16:20])[0]

        install_name = None
        version = None

        for _ in range(ncmds):
            if offset + 8 > len(data):
                break

            cmd, size = struct.unpack('<II', data[offset:offset+8])

            # LC_ID_DYLIB = 0x0d
            if cmd == 0x0d:
                try:
                    timestamp, version_num, compatibility = struct.unpack('<III', data[offset+8:offset+20])
                    # Parse version
                    v1 = (version_num >> 16) & 0xff
                    v2 = (version_num >> 8) & 0xff
                    v3 = version_num & 0xff
                    version = f"{v1}.{v2}.{v3}"

                    # Parse install name
                    str_offset = struct.unpack('<I', data[offset+12:offset+16])[0]
                    str_start = offset + str_offset
                    str_end = data.find(b'\x00', str_start)
                    if str_end > str_start:
                        install_name = data[str_start:str_end].decode('utf-8', errors='replace')
                except Exception:
                    pass
            elif cmd == 0x0c:  # LC_LOAD_DYLIB
                pass  # Not the dylib's own identity

            offset += size

        return install_name, version

    def _detect_architectures(self, data: bytes) -> List[ArchitectureInfo]:
        """Detect Mach-O architectures in binary data."""
        import struct

        archs = []
        if len(data) < 32:
            return archs

        magic = struct.unpack('<I', data[:4])[0]

        if magic == 0xfeedfacf:  # 64-bit little endian
            cputype = struct.unpack('<I', data[4:8])[0]
            if cputype == 0x0100000c:
                archs.append(ArchitectureInfo(0x0100000c, 0, "arm64", True))
            elif cputype == 0x01000007:
                archs.append(ArchitectureInfo(0x01000007, 0, "x86_64", True))

        return archs

    def extract_dylib_dependencies(
        self,
        dylib_path: str,
        component_id: str,
        rpath_resolvers: Optional[List[str]] = None
    ) -> List[DependencyEdge]:
        """
        Extract dependencies from dylib.
        """
        edges = []

        try:
            with open(dylib_path, 'rb') as f:
                data = f.read()
        except Exception:
            return edges

        deps = self._parse_load_commands(data)
        for install_name, edge_type, is_weak in deps:
            state = DependencyState.UNRESOLVED

            # Try to resolve
            if not ComponentTraversal.is_system_framework(install_name):
                resolved_path = self._resolve_dependency(
                    install_name, dylib_path, rpath_resolvers or []
                )
                if resolved_path and os.path.exists(resolved_path):
                    state = DependencyState.RESOLVED_EMBEDDED

            edge = DependencyEdge(
                edge_id=generate_edge_id(component_id, None, install_name),
                source_id=component_id,
                target_id=None,
                edge_type=edge_type,
                install_name=install_name,
                resolved_path=resolved_path if state == DependencyState.RESOLVED_EMBEDDED else None,
                state=state,
                evidence=["load_command_analysis"],
                is_weak=is_weak
            )
            edges.append(edge)

        return edges

    def _parse_load_commands(self, data: bytes) -> List[Tuple[str, EdgeType, bool]]:
        """Parse LC_LOAD_DYLIB commands from Mach-O data."""
        import struct

        deps = []
        if len(data) < 32:
            return deps

        magic = struct.unpack('<I', data[:4])[0]
        is_64bit = magic in (0xfeedfacf, 0xcffaedfe)

        offset = 32 if is_64bit else 28
        ncmds = struct.unpack('<I', data[16:20])[0]

        for _ in range(ncmds):
            if offset + 8 > len(data):
                break

            cmd, size = struct.unpack('<II', data[offset:offset+8])

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
        dylib_path: str,
        rpath_resolvers: List[str]
    ) -> Optional[str]:
        """Resolve a dependency path."""
        if install_name.startswith("@rpath/"):
            rpath_name = install_name[7:]
            for rpath in rpath_resolvers:
                candidate = os.path.join(rpath, rpath_name)
                if os.path.exists(candidate):
                    return candidate
        elif install_name.startswith("@loader_path/"):
            base_dir = os.path.dirname(dylib_path)
            rel_path = install_name[13:]
            return os.path.join(base_dir, rel_path)

        return None
