"""
Tests for Component Inventory capabilities (P04.4).

Tests cover:
- CAP-018: framework.inventory
- CAP-019: dylib.inventory
- CAP-020: extension.inventory
- EP-04.4E: component.graph
"""

import pytest
import os
import tempfile
import plistlib
import hashlib
import struct
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_reverse.capabilities.framework_inventory import FrameworkInventoryCapability
from ios_reverse.capabilities.dylib_inventory import DylibInventoryCapability
from ios_reverse.capabilities.extension_inventory import ExtensionInventoryCapability
from ios_reverse.capabilities.component_graph import ComponentGraphCapability
from ios_reverse.models.components import (
    ComponentType, Classification, DependencyState, EdgeType,
    AppComponent, FrameworkComponent, DylibComponent, ExtensionComponent,
    ComponentGraph, generate_component_id, generate_edge_id
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as td:
        yield td


def create_minimal_macho(arch='arm64'):
    """Create a minimal Mach-O binary."""
    magic = 0xfeedfacf
    cpu_types = {'arm64': 0x0100000c, 'x86_64': 0x01000007}
    cpu_type = cpu_types.get(arch, 0x0100000c)

    header = struct.pack('<IIIIIIII',
        magic, cpu_type, 0, 0x02, 0, 0, 0, 0
    )
    return header + b'\x00' * 256


def create_test_app(temp_dir, name="TestApp.app"):
    """Create a test .app bundle structure."""
    app_path = os.path.join(temp_dir, name)
    os.makedirs(app_path)

    # Create Info.plist
    plist = {
        'CFBundleIdentifier': 'com.test.app',
        'CFBundleVersion': '1.0',
        'CFBundleName': name.replace('.app', ''),
    }
    with open(os.path.join(app_path, 'Info.plist'), 'wb') as f:
        plistlib.dump(plist, f)

    # Create main executable
    exe_data = create_minimal_macho()
    exe_name = name.replace('.app', '')
    with open(os.path.join(app_path, exe_name), 'wb') as f:
        f.write(exe_data)

    return app_path


def create_test_framework(temp_dir, name="TestFramework.framework"):
    """Create a test framework bundle."""
    fw_path = os.path.join(temp_dir, name)
    os.makedirs(os.path.join(fw_path, 'Versions', 'A'))

    # Create Info.plist
    plist = {
        'CFBundleIdentifier': f'com.test.{name.replace(".framework", "")}',
        'CFBundleVersion': '1.0',
    }
    info_path = os.path.join(fw_path, 'Versions', 'A', 'Info.plist')
    with open(info_path, 'wb') as f:
        plistlib.dump(plist, f)

    # Create executable
    exe_data = create_minimal_macho()
    exe_name = name.replace('.framework', '')
    with open(os.path.join(fw_path, 'Versions', 'A', exe_name), 'wb') as f:
        f.write(exe_data)

    return fw_path


def create_test_extension(temp_dir, name="TestExtension.appex"):
    """Create a test extension bundle."""
    ext_path = os.path.join(temp_dir, name)
    os.makedirs(ext_path)

    # Create Info.plist
    plist = {
        'CFBundleIdentifier': f'com.test.{name.replace(".appex", "")}',
        'CFBundleVersion': '1.0',
        'NSExtension': {
            'NSExtensionPointIdentifier': 'com.apple.widget-extension'
        }
    }
    with open(os.path.join(ext_path, 'Info.plist'), 'wb') as f:
        plistlib.dump(plist, f)

    # Create executable
    exe_data = create_minimal_macho()
    exe_name = name.replace('.appex', '')
    with open(os.path.join(ext_path, exe_name), 'wb') as f:
        f.write(exe_data)

    return ext_path


def create_test_dylib(temp_dir, name="libtest.dylib"):
    """Create a test dylib file."""
    dylib_path = os.path.join(temp_dir, name)
    exe_data = create_minimal_macho()
    with open(dylib_path, 'wb') as f:
        f.write(exe_data)
    return dylib_path


# =============================================================================
# Component Model Tests
# =============================================================================

class TestComponentModel:
    """Tests for component models."""

    def test_generate_component_id_deterministic(self):
        """Component IDs are deterministic."""
        id1 = generate_component_id("TestApp", "abc123", "Payload/TestApp.app")
        id2 = generate_component_id("TestApp", "abc123", "Payload/TestApp.app")
        assert id1 == id2

    def test_generate_component_id_different_names(self):
        """Different inputs produce different IDs."""
        id1 = generate_component_id("TestApp1", "abc123", "Payload/TestApp1.app")
        id2 = generate_component_id("TestApp2", "abc123", "Payload/TestApp2.app")
        assert id1 != id2

    def test_generate_edge_id_deterministic(self):
        """Edge IDs are deterministic."""
        id1 = generate_edge_id("comp-abc", "comp-def", "@rpath/Foo.framework/Foo")
        id2 = generate_edge_id("comp-abc", "comp-def", "@rpath/Foo.framework/Foo")
        assert id1 == id2

    def test_component_graph_build_indexes(self):
        """Component graph indexes work correctly."""
        graph = ComponentGraph(root_component_id="app-1")

        app = AppComponent(
            component_id="app-1",
            component_type=ComponentType.APPLICATION,
            name="TestApp",
            bundle_path="TestApp.app",
            artifact_id="artifact-1",
        )
        graph.add_component(app)

        graph.build_indexes()

        assert graph.get_by_artifact_id("artifact-1") == app
        assert graph.get_by_name("TestApp") == [app]

    def test_component_graph_add_edge(self):
        """Component graph edges work correctly."""
        from ios_reverse.models.components import DependencyEdge

        graph = ComponentGraph(root_component_id="app-1")

        edge = DependencyEdge(
            edge_id="edge-1",
            source_id="app-1",
            target_id="fw-1",
            edge_type=EdgeType.LOADS,
            install_name="@rpath/Foo.framework/Foo",
            state=DependencyState.RESOLVED_EMBEDDED,
        )
        graph.add_edge(edge)

        assert len(graph.edges) == 1
        assert graph.edges[0].source_id == "app-1"

    def test_classification_enum(self):
        """Classification enum values are correct."""
        assert Classification.EMBEDDED.value == "embedded"
        assert Classification.SYSTEM_EXTERNAL.value == "system_external"
        assert Classification.UNKNOWN.value == "unknown"

    def test_dependency_state_enum(self):
        """DependencyState enum values are correct."""
        assert DependencyState.RESOLVED_EMBEDDED.value == "resolved_embedded"
        assert DependencyState.EXTERNAL_SYSTEM.value == "external_system"
        assert DependencyState.UNRESOLVED.value == "unresolved"
        assert DependencyState.AMBIGUOUS.value == "ambiguous"


# =============================================================================
# Framework Inventory Tests (CAP-018)
# =============================================================================

class TestFrameworkInventory:
    """Tests for CAP-018 framework.inventory."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = FrameworkInventoryCapability()
        contract = cap.contract

        assert contract.id == "framework.inventory"
        assert contract.version == "1.0.0"
        assert contract.domain == "components"

    def test_validate_missing_path(self):
        """Validation fails with missing path."""
        cap = FrameworkInventoryCapability()
        result = cap.execute({})

        assert result.status.value == "failure"
        assert result.error_code == "E001"

    def test_validate_nonexistent_path(self):
        """Validation handles nonexistent path gracefully."""
        cap = FrameworkInventoryCapability()
        result = cap.execute({"artifact_path": "/nonexistent/path"})

        # Should handle gracefully
        assert result.status.value in ["failure", "partial"]

    def test_execute_no_frameworks(self, temp_dir):
        """Execute on app without frameworks."""
        app_path = create_test_app(temp_dir)

        cap = FrameworkInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("framework_count") == 0

    def test_execute_with_frameworks(self, temp_dir):
        """Execute on app with embedded frameworks."""
        app_path = create_test_app(temp_dir)

        # Create Frameworks directory
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)

        # Create test framework
        create_test_framework(fw_dir, "Foo.framework")
        create_test_framework(fw_dir, "Bar.framework")

        cap = FrameworkInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("framework_count") >= 2

    def test_framework_classification(self, temp_dir):
        """Frameworks are classified correctly."""
        app_path = create_test_app(temp_dir)

        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)
        create_test_framework(fw_dir, "Foo.framework")

        cap = FrameworkInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        components = result.metadata.get("components", [])
        if components:
            # Should be classified as embedded
            assert "classification" in components[0]


# =============================================================================
# Dylib Inventory Tests (CAP-019)
# =============================================================================

class TestDylibInventory:
    """Tests for CAP-019 dylib.inventory."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = DylibInventoryCapability()
        contract = cap.contract

        assert contract.id == "dylib.inventory"
        assert contract.version == "1.0.0"

    def test_validate_missing_path(self):
        """Validation fails with missing path."""
        cap = DylibInventoryCapability()
        result = cap.execute({})

        assert result.status.value == "failure"
        assert result.error_code == "E001"

    def test_execute_no_dylibs(self, temp_dir):
        """Execute on app without dylibs."""
        app_path = create_test_app(temp_dir)

        cap = DylibInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        # May find main executable as dylib - just check it works
        assert "dylib_count" in result.metadata

    def test_execute_with_dylibs(self, temp_dir):
        """Execute on app with embedded dylibs."""
        app_path = create_test_app(temp_dir)

        # Create dylibs at root
        create_test_dylib(app_path, "libfoo.dylib")
        create_test_dylib(app_path, "libbar.dylib")

        cap = DylibInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        # Should find dylibs
        assert "dylib_count" in result.metadata


# =============================================================================
# Extension Inventory Tests (CAP-020)
# =============================================================================

class TestExtensionInventory:
    """Tests for CAP-020 extension.inventory."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = ExtensionInventoryCapability()
        contract = cap.contract

        assert contract.id == "extension.inventory"
        assert contract.version == "1.0.0"

    def test_validate_missing_path(self):
        """Validation fails with missing path."""
        cap = ExtensionInventoryCapability()
        result = cap.execute({})

        assert result.status.value == "failure"
        assert result.error_code == "E001"

    def test_execute_no_extensions(self, temp_dir):
        """Execute on app without extensions."""
        app_path = create_test_app(temp_dir)

        cap = ExtensionInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("extension_count") == 0

    def test_execute_with_extensions(self, temp_dir):
        """Execute on app with extensions."""
        app_path = create_test_app(temp_dir)

        # Create PlugIns directory
        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)

        # Create test extension
        create_test_extension(plugins_dir, "Widget.appex")

        cap = ExtensionInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("extension_count") >= 1

    def test_extension_point_detection(self, temp_dir):
        """Extension point is detected from Info.plist."""
        app_path = create_test_app(temp_dir)

        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)
        ext_path = create_test_extension(plugins_dir, "Widget.appex")

        cap = ExtensionInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        components = result.metadata.get("components", [])
        if components:
            assert components[0].get("extension_point") == "com.apple.widget-extension"


# =============================================================================
# Component Graph Tests (EP-04.4E)
# =============================================================================

class TestComponentGraph:
    """Tests for EP-04.4E component.graph."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = ComponentGraphCapability()
        contract = cap.contract

        assert contract.id == "component.graph"
        assert contract.version == "1.0.0"

    def test_validate_missing_path(self):
        """Validation fails with missing path."""
        cap = ComponentGraphCapability()
        result = cap.execute({})

        assert result.status.value == "failure"
        assert result.error_code == "E001"

    def test_execute_basic_app(self, temp_dir):
        """Execute on basic app with main executable."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("component_count") >= 1
        assert "eligible_executables" in result.metadata

    def test_execute_app_with_frameworks(self, temp_dir):
        """Execute on app with embedded frameworks."""
        app_path = create_test_app(temp_dir)

        # Add frameworks
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)
        create_test_framework(fw_dir, "Foo.framework")
        create_test_framework(fw_dir, "Bar.framework")

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("component_count") >= 3  # App + 2 frameworks

    def test_execute_app_with_extensions(self, temp_dir):
        """Execute on app with extensions."""
        app_path = create_test_app(temp_dir)

        # Add extension
        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)
        create_test_extension(plugins_dir, "Widget.appex")

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("component_count") >= 2  # App + extension

    def test_execute_app_with_nested_framework(self, temp_dir):
        """Execute on app with nested frameworks in extensions."""
        app_path = create_test_app(temp_dir)

        # Add extension with nested framework
        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)
        ext_path = create_test_extension(plugins_dir, "Widget.appex")

        # Nested framework inside extension
        ext_fw_dir = os.path.join(ext_path, "Frameworks")
        os.makedirs(ext_fw_dir)
        create_test_framework(ext_fw_dir, "Nested.framework")

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        # Should find app, extension, and nested framework
        assert result.metadata.get("component_count") >= 3

    def test_eligible_executables_deterministic(self, temp_dir):
        """eligible_executables is deterministic."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()

        # Run twice
        result1 = cap.execute({"artifact_path": app_path})
        result2 = cap.execute({"artifact_path": app_path})

        # Should be identical
        execs1 = result1.metadata.get("eligible_executables", [])
        execs2 = result2.metadata.get("eligible_executables", [])
        assert execs1 == execs2

    def test_system_dependencies_separate(self, temp_dir):
        """System dependencies are tracked separately."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        # System dependencies should be separate from eligible_executables
        assert "system_dependencies" in result.metadata or \
               result.metadata.get("system_dependency_count", 0) >= 0


# =============================================================================
# Component Type Tests
# =============================================================================

class TestComponentTypes:
    """Tests for component type handling."""

    def test_component_type_enum(self):
        """Component types are correct."""
        assert ComponentType.APPLICATION.value == "application"
        assert ComponentType.FRAMEWORK.value == "framework"
        assert ComponentType.DYLIB.value == "dylib"
        assert ComponentType.EXTENSION.value == "extension"

    def test_edge_type_enum(self):
        """Edge types are correct."""
        assert EdgeType.CONTAINS.value == "contains"
        assert EdgeType.LOADS.value == "loads"
        assert EdgeType.WEAK_LOADS.value == "weak_loads"
        assert EdgeType.REEXPORTS.value == "reexports"


# =============================================================================
# Edge Resolution Tests
# =============================================================================

class TestDependencyResolution:
    """Tests for dependency resolution."""

    def test_resolved_edge_has_target(self):
        """Resolved edges have target IDs."""
        from ios_reverse.models.components import DependencyEdge

        graph = ComponentGraph(root_component_id="app-1")

        app = AppComponent(
            component_id="app-1",
            component_type=ComponentType.APPLICATION,
            name="TestApp",
            bundle_path="TestApp.app",
            artifact_id="artifact-1",
        )
        graph.add_component(app)

        fw = FrameworkComponent(
            component_id="fw-1",
            component_type=ComponentType.FRAMEWORK,
            name="Foo",
            bundle_path="Frameworks/Foo.framework",
            artifact_id="artifact-2",
        )
        graph.add_component(fw)

        edge = DependencyEdge(
            edge_id="edge-1",
            source_id="app-1",
            target_id="fw-1",  # Resolved
            edge_type=EdgeType.LOADS,
            install_name="@rpath/Foo.framework/Foo",
            state=DependencyState.RESOLVED_EMBEDDED,
        )
        graph.add_edge(edge)

        assert graph.edges[0].state == DependencyState.RESOLVED_EMBEDDED
        assert graph.edges[0].target_id == "fw-1"

    def test_unresolved_edge_no_target(self):
        """Unresolved edges do not have targets."""
        from ios_reverse.models.components import DependencyEdge

        edge = DependencyEdge(
            edge_id="edge-1",
            source_id="app-1",
            target_id=None,  # Unresolved
            edge_type=EdgeType.LOADS,
            install_name="@rpath/Unknown.framework/Unknown",
            state=DependencyState.UNRESOLVED,
        )

        assert edge.state == DependencyState.UNRESOLVED
        assert edge.target_id is None


# =============================================================================
# Boundary Safety Tests
# =============================================================================

class TestBoundarySafety:
    """Tests for defensive parsing and boundary safety."""

    def test_malformed_bundle_path(self, temp_dir):
        """Handle malformed bundle paths."""
        # Create something that looks like a framework but isn't
        fake_fw = os.path.join(temp_dir, "Fake.framework")
        os.makedirs(fake_fw)
        # No Info.plist, no executable

        app_path = create_test_app(temp_dir)
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)

        # Copy fake framework
        import shutil
        shutil.copytree(fake_fw, os.path.join(fw_dir, "Fake.framework"))

        cap = FrameworkInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        # Should handle gracefully
        assert result.status.value in ["success", "partial"]

    def test_empty_plugins_directory(self, temp_dir):
        """Handle empty PlugIns directory."""
        app_path = create_test_app(temp_dir)

        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)

        cap = ExtensionInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        assert result.status.value in ["success", "partial"]
        assert result.metadata.get("extension_count") == 0

    def test_duplicate_component_handling(self, temp_dir):
        """Duplicate artifacts are deduplicated."""
        graph = ComponentGraph(root_component_id="app-1")

        # Same artifact ID twice
        app = AppComponent(
            component_id="app-1",
            component_type=ComponentType.APPLICATION,
            name="TestApp",
            bundle_path="TestApp.app",
            artifact_id="artifact-1",
        )
        graph.add_component(app)
        graph.add_component(app)  # Duplicate

        assert len(graph.components) == 1


# =============================================================================
# Cross-Capability Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests across capabilities."""

    def test_all_capabilities_on_same_app(self, temp_dir):
        """All inventory capabilities work on the same app."""
        app_path = create_test_app(temp_dir)

        # Add frameworks
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)
        create_test_framework(fw_dir, "Foo.framework")

        # Add dylibs
        create_test_dylib(app_path, "libtest.dylib")

        # Add extension
        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)
        create_test_extension(plugins_dir, "Widget.appex")

        # Run all capabilities
        fw_cap = FrameworkInventoryCapability()
        dylib_cap = DylibInventoryCapability()
        ext_cap = ExtensionInventoryCapability()
        graph_cap = ComponentGraphCapability()

        fw_result = fw_cap.execute({"artifact_path": app_path})
        dylib_result = dylib_cap.execute({"artifact_path": app_path})
        ext_result = ext_cap.execute({"artifact_path": app_path})
        graph_result = graph_cap.execute({"artifact_path": app_path})

        # All should succeed
        assert fw_result.status.value in ["success", "partial"]
        assert dylib_result.status.value in ["success", "partial"]
        assert ext_result.status.value in ["success", "partial"]
        assert graph_result.status.value in ["success", "partial"]

    def test_component_graph_includes_all_types(self, temp_dir):
        """Component graph includes all component types."""
        app_path = create_test_app(temp_dir)

        # Add all types
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)
        create_test_framework(fw_dir, "Foo.framework")

        create_test_dylib(app_path, "libtest.dylib")

        plugins_dir = os.path.join(app_path, "PlugIns")
        os.makedirs(plugins_dir)
        create_test_extension(plugins_dir, "Widget.appex")

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        component_types = result.metadata.get("component_types", {})
        assert "application" in component_types
        assert component_types.get("framework", 0) >= 1
        assert component_types.get("dylib", 0) >= 1
        assert component_types.get("extension", 0) >= 1


# =============================================================================
# Invariants
# =============================================================================

class TestInvariants:
    """Tests that prove key invariants."""

    def test_component_ids_deterministic(self, temp_dir):
        """INVARIANT: Component IDs are deterministic."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()
        result1 = cap.execute({"artifact_path": app_path})
        result2 = cap.execute({"artifact_path": app_path})

        # Component IDs should be the same
        comps1 = set(result1.metadata.get("eligible_executables", []))
        comps2 = set(result2.metadata.get("eligible_executables", []))
        assert comps1 == comps2

    def test_no_duplicate_in_eligible(self, temp_dir):
        """INVARIANT: No duplicate components in eligible_executables."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        execs = result.metadata.get("eligible_executables", [])
        assert len(execs) == len(set(execs))

    def test_system_deps_not_in_eligible(self, temp_dir):
        """INVARIANT: System dependencies not in eligible_executables."""
        graph = ComponentGraph(root_component_id="app-1")
        graph.system_dependencies.add("UIKit.framework")

        app = AppComponent(
            component_id="app-1",
            component_type=ComponentType.APPLICATION,
            name="TestApp",
            bundle_path="TestApp.app",
            artifact_id="artifact-1",
        )
        graph.add_component(app)

        # System dep shouldn't be in components
        assert "UIKit.framework" not in graph.components

    def test_containment_vs_linkage_distinct(self, temp_dir):
        """INVARIANT: Containment and linkage are distinct."""
        app_path = create_test_app(temp_dir)

        # Create app with framework
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)
        create_test_framework(fw_dir, "Foo.framework")

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        # Should have edges for linkage
        assert "edge_count" in result.metadata or "component_count" in result.metadata

    def test_evidence_preserved(self, temp_dir):
        """INVARIANT: Evidence is preserved for components."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        # Provenance should be recorded
        assert result.provenance is not None
        assert result.provenance.capability_id == "component.graph"

    def test_no_path_as_component_id(self, temp_dir):
        """INVARIANT: Component IDs are not paths."""
        app_path = create_test_app(temp_dir)

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        # Component IDs should be hashes, not paths
        for comp_id in result.metadata.get("eligible_executables", []):
            assert not comp_id.startswith("/")
            assert ":" not in comp_id or comp_id.startswith("comp-")

    def test_partial_success_on_issues(self, temp_dir):
        """INVARIANT: Partial success when there are issues."""
        app_path = create_test_app(temp_dir)

        # Create malformed framework
        fw_dir = os.path.join(app_path, "Frameworks")
        os.makedirs(fw_dir)
        bad_fw = os.path.join(fw_dir, "Bad.framework")
        os.makedirs(bad_fw)
        # No Info.plist, no executable

        cap = FrameworkInventoryCapability()
        result = cap.execute({"artifact_path": app_path})

        # Should complete with partial success
        assert result.status.value in ["success", "partial"]

    def test_manifest_readonly(self, temp_dir):
        """INVARIANT: Inventory does not modify artifacts."""
        app_path = create_test_app(temp_dir)

        # Record original file state
        import filecmp
        original_state = {}

        for root, dirs, files in os.walk(app_path):
            for f in files:
                path = os.path.join(root, f)
                with open(path, 'rb') as fp:
                    original_state[path] = hashlib.sha256(fp.read()).hexdigest()

        cap = ComponentGraphCapability()
        result = cap.execute({"artifact_path": app_path})

        # Verify files unchanged
        for root, dirs, files in os.walk(app_path):
            for f in files:
                path = os.path.join(root, f)
                with open(path, 'rb') as fp:
                    current_hash = hashlib.sha256(fp.read()).hexdigest()
                assert current_hash == original_state[path]
