#!/usr/bin/env python3
"""
Test for the get_cell_data method in the metageo plugin.

This test verifies that the get_cell_data method can retrieve detailed
information about a specific grid cell from the execution store.
"""

import pytest
import sys
import os

# Add the plugin directory to the path so we can import the module
plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_dir)

try:
    from __init__ import MetageoPanel
except ImportError:
    pytest.skip("Could not import MetageoPanel from __init__.py", allow_module_level=True)


class TestCellData:
    """Test cases for the get_cell_data method."""

    def test_get_cell_data_missing_cell_id(self):
        """Test that get_cell_data returns an error when cell_id is missing."""
        panel = MetageoPanel()
        
        # Mock execution context
        class MockContext:
            @property
            def params(self):
                return {}
        
        ctx = MockContext()
        result = panel.get_cell_data(ctx)
        
        assert result["status"] == "error"
        assert "cell_id parameter is required" in result["message"]

    def test_get_cell_data_nonexistent_cell(self):
        """Test that get_cell_data handles nonexistent cells gracefully."""
        panel = MetageoPanel()
        
        # Mock execution context
        class MockContext:
            @property
            def params(self):
                return {"cell_id": "nonexistent_cell"}
            
            def store(self, name):
                return MockStore()
        
        class MockStore:
            def get(self, key):
                return None
        
        ctx = MockContext()
        result = panel.get_cell_data(ctx)
        
        assert result["status"] == "success"
        assert result["cell_id"] == "nonexistent_cell"
        assert result["cell_status"] is None
        assert result["osm_features_count"] is None
        assert result["osm_data"] == []
        assert result["cell_info"] is None
        assert result["coordinates"] is None
        assert result["sample_count"] == 0

    def test_get_cell_data_with_mock_data(self):
        """Test that get_cell_data returns correct data structure."""
        panel = MetageoPanel()
        
        # Mock execution context
        class MockContext:
            @property
            def params(self):
                return {"cell_id": "0_0"}
            
            def store(self, name):
                return MockStore()
        
        class MockStore:
            def get(self, key):
                if key == "cell_0_0_status":
                    return "completed"
                elif key == "cell_0_0_error":
                    return None
                elif key == "cell_0_0_osm_features":
                    return 5
                elif key == "cell_0_0_osm_data":
                    return [
                        {
                            "type": "node",
                            "id": 12345,
                            "feature_type": "highway",
                            "tags": {"highway": "primary", "name": "Test Street"}
                        },
                        {
                            "type": "way",
                            "id": 67890,
                            "feature_type": "building",
                            "tags": {"building": "residential"}
                        }
                    ]
                elif key == "indexing_state":
                    return {
                        "grid_cells": [
                            {
                                "id": "0_0",
                                "coordinates": [-73.98, 40.77, -73.95, 40.79],
                                "sample_count": 10
                            }
                        ]
                    }
                return None
        
        ctx = MockContext()
        result = panel.get_cell_data(ctx)
        
        assert result["status"] == "success"
        assert result["cell_id"] == "0_0"
        assert result["cell_status"] == "completed"
        assert result["error"] is None
        assert result["osm_features_count"] == 5
        assert len(result["osm_data"]) == 2
        assert result["cell_info"]["id"] == "0_0"
        assert result["coordinates"] == [-73.98, 40.77, -73.95, 40.79]
        assert result["sample_count"] == 10

    def test_get_cell_data_with_error(self):
        """Test that get_cell_data handles cells with errors."""
        panel = MetageoPanel()
        
        # Mock execution context
        class MockContext:
            @property
            def params(self):
                return {"cell_id": "1_1"}
            
            def store(self, name):
                return MockStore()
        
        class MockStore:
            def get(self, key):
                if key == "cell_1_1_status":
                    return "failed"
                elif key == "cell_1_1_error":
                    return "Rate limited by OSM API"
                elif key == "cell_1_1_osm_features":
                    return None
                elif key == "cell_1_1_osm_data":
                    return None
                elif key == "indexing_state":
                    return {
                        "grid_cells": [
                            {
                                "id": "1_1",
                                "coordinates": [-73.95, 40.77, -73.92, 40.79],
                                "sample_count": 0
                            }
                        ]
                    }
                return None
        
        ctx = MockContext()
        result = panel.get_cell_data(ctx)
        
        assert result["status"] == "success"
        assert result["cell_id"] == "1_1"
        assert result["cell_status"] == "failed"
        assert result["error"] == "Rate limited by OSM API"
        assert result["osm_features_count"] is None
        assert result["osm_data"] == []
        assert result["sample_count"] == 0

    def test_get_cell_data_exception_handling(self):
        """Test that get_cell_data handles exceptions gracefully."""
        panel = MetageoPanel()
        
        # Mock execution context that raises an exception
        class MockContext:
            @property
            def params(self):
                return {"cell_id": "0_0"}
            
            def store(self, name):
                raise Exception("Store access error")
        
        ctx = MockContext()
        result = panel.get_cell_data(ctx)
        
        assert result["status"] == "error"
        assert "Error retrieving cell data" in result["message"]
        assert "Store access error" in result["message"]


if __name__ == "__main__":
    print("Testing get_cell_data method from metageo plugin...")
    print("=" * 60)
    print("Run with: pytest tests/test_cell_data.py -v")
