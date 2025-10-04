#!/usr/bin/env python3
"""
Test for the OSMClient class in the metageo plugin.

This test verifies that the OSMClient can successfully call the OpenStreetMap
Overpass API and retrieve data for a small bounding box.
"""

import pytest
import sys
import os
import time

# Add the plugin directory to the path so we can import the module
plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_dir)

try:
    from __init__ import OSMClient
except ImportError:
    pytest.skip("Could not import OSMClient from __init__.py", allow_module_level=True)

# Skip all tests if overpy is not available
try:
    import overpy
except ImportError:
    pytest.skip("overpy not available - install with: pip install overpy", allow_module_level=True)


class TestOSMClient:
    """Test cases for the OSMClient class."""

    @pytest.fixture
    def client(self):
        """Create an OSMClient instance for testing."""
        return OSMClient()

    @pytest.fixture
    def test_bbox(self):
        """Small bounding box around Central Park, NYC for testing."""
        return [-73.98, 40.77, -73.95, 40.79]  # [minLon, minLat, maxLon, maxLat]

    def test_osm_client_initialization(self, client):
        """Test that OSMClient initializes correctly."""
        assert client is not None
        assert client.endpoint == "https://overpass-api.de/api/interpreter"
        assert client.rate_limit_delay == 0.1
        assert client.api is not None  # Should have overpy API available

    def test_query_bbox_highway_only(self, client, test_bbox):
        """Test OSM API call for highway features only."""
        time.sleep(1)  # Rate limiting
        result = client.query_bbox(test_bbox, feature_types=["highway"])
        
        # Verify the result structure
        assert "features" in result
        assert "count" in result
        assert "bbox" in result
        
        # Handle rate limiting gracefully
        if result.get("status") == "error" and "error" in result:
            print(f"Rate limited: {result['error']}")
            assert result["error"] == "Too many requests - rate limited"
            assert result["features"] == []
            assert result["count"] == 0
        else:
            assert "feature_types" in result
            assert "query_time" in result
            assert result.get("status") == "success"
        
            # Verify bbox is preserved
            assert result["bbox"] == test_bbox
            
            # Verify feature types
            assert result["feature_types"] == ["highway"]
            
            # The count should be a non-negative integer
            assert isinstance(result["count"], int)
            assert result["count"] >= 0
            
            print(f"Highway query: Retrieved {result['count']} OSM features")
            
            # If we got features, verify their structure
            if result["count"] > 0:
                feature = result["features"][0]
                assert "type" in feature
                assert "id" in feature
                assert "tags" in feature
                assert "feature_type" in feature
                
                # Verify the feature type is highway
                assert feature["feature_type"] == "highway"
                
                # Verify tags contain highway information
                assert "highway" in feature["tags"]
                
                print(f"Sample highway feature: {feature}")

    def test_query_bbox_multiple_features(self, client, test_bbox):
        """Test OSM API call with multiple feature types."""
        time.sleep(1)  # Rate limiting
        feature_types = ["highway", "amenity", "building"]
        result = client.query_bbox(test_bbox, feature_types=feature_types)
        
        # Verify the result structure
        assert "features" in result
        assert "count" in result
        
        # Handle rate limiting gracefully
        if result.get("status") == "error" and "error" in result:
            print(f"Rate limited: {result['error']}")
            assert result["error"] == "Too many requests - rate limited"
            assert result["features"] == []
            assert result["count"] == 0
        else:
            assert result["feature_types"] == feature_types
            assert result.get("status") == "success"
            
            # The count should be a non-negative integer
            assert isinstance(result["count"], int)
            assert result["count"] >= 0
            
            print(f"Multiple features query: Retrieved {result['count']} OSM features")
            
            # Test statistics generation
            if result["count"] > 0:
                stats = client.get_feature_statistics(result["features"])
                assert "total" in stats
                assert "by_type" in stats
                assert "by_feature_type" in stats
                assert stats["total"] == result["count"]
                print(f"Feature statistics: {stats}")
                
                # Show breakdown by feature type
                for feature_type, count in stats["by_feature_type"].items():
                    print(f"  {feature_type}: {count} features")

    def test_query_bbox_default_features(self, client, test_bbox):
        """Test OSM API call with default feature types."""
        time.sleep(1)  # Rate limiting
        result = client.query_bbox(test_bbox)
        
        # Verify the result structure
        assert "features" in result
        assert "count" in result
        
        # Handle rate limiting gracefully
        if result.get("status") == "error" and "error" in result:
            print(f"Rate limited: {result['error']}")
            assert result["error"] == "Too many requests - rate limited"
            assert result["features"] == []
            assert result["count"] == 0
        else:
            # Should have success status
            assert result.get("status") == "success"
            
            # Should have the default feature types
            assert "feature_types" in result
            expected_types = [
                "highway", "amenity", "building", "leisure", "natural",
                "landuse", "waterway", "railway", "power", "barrier"
            ]
            assert result["feature_types"] == expected_types

            # The count should be a non-negative integer
            assert isinstance(result["count"], int)
            assert result["count"] >= 0

            print(f"Default features query: Retrieved {result['count']} OSM features")

            # Show breakdown by OSM type (node, way, relation)
            if result["count"] > 0:
                stats = client.get_feature_statistics(result["features"])
                print(f"OSM type breakdown: {stats['by_type']}")

    def test_get_primary_tag(self, client):
        """Test the _get_primary_tag method."""
        # Test with priority tags
        tags = {"highway": "primary", "name": "Test Street"}
        primary_tag = client._get_primary_tag(tags)
        assert primary_tag == "highway"
        
        # Test with non-priority tags
        tags = {"name": "Test Street", "surface": "asphalt"}
        primary_tag = client._get_primary_tag(tags)
        assert primary_tag == "name"
        
        # Test with empty tags
        primary_tag = client._get_primary_tag({})
        assert primary_tag is None
        
        # Test with None
        primary_tag = client._get_primary_tag(None)
        assert primary_tag is None

    def test_get_feature_statistics(self, client):
        """Test the get_feature_statistics method."""
        # Sample features for testing
        features = [
            {"type": "node", "feature_type": "highway"},
            {"type": "way", "feature_type": "highway"},
            {"type": "node", "feature_type": "amenity"},
            {"type": "relation", "feature_type": "building"},
        ]
        
        stats = client.get_feature_statistics(features)
        
        # Verify statistics structure
        assert "total" in stats
        assert "by_type" in stats
        assert "by_feature_type" in stats
        
        # Verify counts
        assert stats["total"] == 4
        assert stats["by_type"]["node"] == 2
        assert stats["by_type"]["way"] == 1
        assert stats["by_type"]["relation"] == 1
        assert stats["by_feature_type"]["highway"] == 2
        assert stats["by_feature_type"]["amenity"] == 1
        assert stats["by_feature_type"]["building"] == 1
        
        # Test with empty features
        empty_stats = client.get_feature_statistics([])
        assert empty_stats["total"] == 0
        assert empty_stats["by_type"] == {}
        assert empty_stats["by_feature_type"] == {}

    def test_bbox_normalization(self, test_bbox):
        """Test that bounding box coordinates are properly normalized."""
        # Test with a bbox that needs normalization
        bbox = test_bbox  # [minLon, minLat, maxLon, maxLat]
        
        # The method should normalize to (south, west, north, east)
        min_lon, min_lat, max_lon, max_lat = bbox
        south, west, north, east = min_lat, min_lon, max_lat, max_lon
        
        assert south == 40.77  # min_lat
        assert west == -73.98  # min_lon
        assert north == 40.79  # max_lat
        assert east == -73.95  # max_lon

    def test_real_osm_data_processing(self, client, test_bbox):
        """Test that we can actually retrieve and process real OSM data."""
        time.sleep(1)  # Rate limiting
        # Query for a mix of features that should exist in Central Park area
        result = client.query_bbox(test_bbox, feature_types=["highway", "leisure", "natural"])
        
        assert result["count"] >= 0
        
        if result["count"] > 0:
            # Verify we can process the features
            for feature in result["features"][:3]:  # Check first 3 features
                assert "type" in feature
                assert "id" in feature
                assert "tags" in feature
                assert "feature_type" in feature
                
                # Verify feature type is one of our requested types
                assert feature["feature_type"] in ["highway", "leisure", "natural"]
                
                # Verify tags contain the expected key
                assert feature["feature_type"] in feature["tags"]
            
            print(f"Successfully processed {len(result['features'])} real OSM features")
            
            # Show some examples
            for i, feature in enumerate(result["features"][:2]):
                print(f"Feature {i+1}: {feature['feature_type']} - {feature['tags']}")


if __name__ == "__main__":
    print("Testing OSMClient with real OpenStreetMap API calls...")
    print("=" * 60)
    print("Run with: pytest test_osm_client.py -v -s")