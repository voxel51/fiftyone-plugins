# OSM Client Implementation

## Overview

The Metageo plugin now includes a real OpenStreetMap (OSM) client that queries
the Overpass API to retrieve geographic data for enriching your datasets.

## Features

### 🗺️ **OSMClient Class**

-   **Overpass API Integration**: Uses the official Overpass API for querying
    OSM data
-   **Rate Limiting**: Built-in rate limiting to respect OSM server limits
-   **Bounding Box Queries**: Efficient spatial queries within geographic
    boundaries
-   **Feature Type Filtering**: Query specific OSM feature types (highways,
    amenities, buildings, etc.)
-   **Error Handling**: Robust error handling and retry logic
-   **Statistics Generation**: Automatic feature statistics and categorization

### 📊 **Supported OSM Feature Types**

-   **highway**: Roads, streets, paths
-   **amenity**: Restaurants, shops, services
-   **building**: Buildings and structures
-   **leisure**: Parks, sports facilities
-   **natural**: Natural features (trees, water, etc.)
-   **landuse**: Land use classifications
-   **waterway**: Rivers, streams, canals
-   **railway**: Train tracks and stations
-   **power**: Power lines and infrastructure
-   **barrier**: Walls, fences, barriers

## Installation

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install overpy requests geopy
```

## Usage

### Basic Query Example

```python
from metageo import OSMClient

# Initialize client
osm_client = OSMClient()

# Query OSM data for a bounding box
bbox = [-74.0, 40.7, -73.9, 40.8]  # [minLon, minLat, maxLon, maxLat]
result = osm_client.query_bbox(bbox)

print(f"Retrieved {result['count']} OSM features")
```

### Custom Feature Types

```python
# Query specific feature types
feature_types = ["highway", "amenity", "building"]
result = osm_client.query_bbox(bbox, feature_types=feature_types)
```

### Get Statistics

```python
# Generate statistics from query results
stats = osm_client.get_feature_statistics(result["features"])
print(f"Feature breakdown: {stats['by_feature_type']}")
```

## API Reference

### OSMClient Methods

#### `query_bbox(bbox, feature_types=None)`

Query OSM data within a bounding box.

**Parameters:**

-   `bbox`: List of [minLon, minLat, maxLon, maxLat]
-   `feature_types`: Optional list of OSM feature types to query

**Returns:**

-   Dictionary with features, count, metadata, and query information

#### `get_feature_statistics(features)`

Generate statistics from OSM features.

**Parameters:**

-   `features`: List of OSM feature dictionaries

**Returns:**

-   Dictionary with total count and breakdowns by type and feature type

## Integration with Metageo Panel

The OSM client is automatically used during the indexing process:

1. **Grid Cell Processing**: Each geographic cell is queried for OSM data
2. **Feature Storage**: OSM features are stored with each cell
3. **Statistics Tracking**: Feature counts and types are tracked per cell
4. **Error Handling**: Failed queries are logged and retried

## Rate Limiting

The client includes built-in rate limiting:

-   **Default Delay**: 1 second between requests
-   **Configurable**: Adjust `rate_limit_delay` in OSMClient constructor
-   **Respectful**: Follows Overpass API usage guidelines

## Error Handling

The client handles various error scenarios:

-   **Network Errors**: Connection timeouts and failures
-   **API Errors**: Overpass API error responses
-   **Data Errors**: Malformed or missing data
-   **Rate Limit Errors**: Automatic retry with backoff

## Performance Considerations

-   **Query Optimization**: Efficient Overpass QL queries
-   **Batch Processing**: Process multiple cells in sequence
-   **Caching**: Results can be cached for repeated queries
-   **Memory Management**: Large result sets are processed incrementally

## Testing

Use the test method in the Metageo panel:

```python
# Test OSM client with a small query
result = panel.test_osm_client({"bbox": [-74.0, 40.7, -73.9, 40.8]})
print(result)
```

## Troubleshooting

### Common Issues

1. **Import Error**: Install overpy with `pip install overpy`
2. **Rate Limiting**: Increase delay between requests
3. **Large Queries**: Break large areas into smaller cells
4. **Network Issues**: Check internet connection and firewall settings

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

-   **Caching Layer**: Redis or file-based caching
-   **Parallel Processing**: Multi-threaded queries
-   **Advanced Filtering**: More sophisticated feature filtering
-   **Data Validation**: Enhanced data quality checks
-   **Performance Metrics**: Query timing and performance tracking
