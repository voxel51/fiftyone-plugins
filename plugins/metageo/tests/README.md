# Metageo Plugin Tests

This directory contains tests for the metageo plugin, including the OSMClient class.

## Running the Tests

### Prerequisites

Install the required dependencies:

```bash
pip install pytest overpy
```

### Run All Tests

From the plugin root directory:
```bash
pytest tests/ -v
```

Or from the tests directory:
```bash
cd tests
pytest -v
```

### Run with Output

```bash
pytest tests/ -v -s
```

### Run Specific Test File

```bash
pytest tests/test_osm_client.py -v
```

### Run Specific Test

```bash
pytest tests/test_osm_client.py::TestOSMClient::test_query_bbox_highway_only -v
```

## Test Structure

### OSM Client Tests (`test_osm_client.py`)
All tests make real calls to the OpenStreetMap Overpass API:

- **test_osm_client_initialization**: Tests OSMClient initialization
- **test_query_bbox_highway_only**: Tests OSM API call for highway features only
- **test_query_bbox_multiple_features**: Tests API call with multiple feature types
- **test_query_bbox_default_features**: Tests query with default feature types
- **test_get_primary_tag**: Tests the `_get_primary_tag` method
- **test_get_feature_statistics**: Tests the `get_feature_statistics` method
- **test_bbox_normalization**: Tests bounding box coordinate normalization
- **test_real_osm_data_processing**: Tests actual retrieval and processing of real OSM data

### Operator Tests (`test_operators.py`)
Tests the plugin operators:

- **test_index_grid_operator_initialization**: Verifies IndexGridOperator configuration
- **test_watch_indexing_operator_initialization**: Tests WatchIndexingOperator setup

### Cell Data Tests (`test_cell_data.py`)
Tests the cell data retrieval functionality:

- **test_get_cell_data_missing_cell_id**: Tests error handling when cell_id is missing
- **test_get_cell_data_nonexistent_cell**: Tests graceful handling of cells that don't exist
- **test_get_cell_data_with_mock_data**: Tests correct data structure returned for valid cells
- **test_get_cell_data_with_error**: Tests handling of cells with errors (rate limited, failed)
- **test_get_cell_data_exception_handling**: Tests graceful error handling for store access issues

### Cancel Indexing Tests (`test_cancel_indexing.py`)
Tests the indexing cancellation functionality:

- **test_cancel_indexing_no_indexing_state**: Tests error handling when no indexing operation exists
- **test_cancel_indexing_success**: Tests successful cancellation of an indexing operation
- **test_cancel_indexing_with_empty_grid**: Tests cancellation when grid has no cells
- **test_cancel_indexing_exception_handling**: Tests graceful error handling for store access issues

## What the Tests Verify

### OSM Client Tests
1. **OSMClient Initialization**: Proper setup of the client with correct endpoint and rate limiting
2. **Real API Calls**: Actual calls to the OpenStreetMap Overpass API
3. **Data Processing**: Proper parsing and structuring of OSM data (nodes, ways, relations)
4. **Feature Filtering**: Correct querying of different OSM feature types (highway, amenity, building, etc.)
5. **Statistics Generation**: Correct feature counting and categorization
6. **Data Validation**: Verification that retrieved OSM data has the expected structure

### Operator Tests
7. **Operator Configuration**: Proper initialization and configuration of plugin operators
8. **Operator Properties**: Correct operator names, labels, and execution settings

### Cell Data Tests
9. **Parameter Validation**: Proper handling of missing or invalid parameters
10. **Data Retrieval**: Correct extraction of cell data from the execution store
11. **Error Handling**: Graceful handling of missing cells, errors, and exceptions
12. **Data Structure**: Verification that returned data has the expected format

### Cancel Indexing Tests
13. **Operation Cancellation**: Proper cancellation of ongoing indexing operations
14. **State Management**: Correct updating of indexing state to "cancelled" status
15. **Data Cleanup**: Proper clearing of cell data when indexing is cancelled
16. **Error Handling**: Graceful handling of missing indexing state and exceptions

## Test Data

The tests use a small bounding box around Central Park, NYC:
- Bounding box: `[-73.98, 40.77, -73.95, 40.79]` (minLon, minLat, maxLon, maxLat)
- This area is chosen because it has known OSM data and is small enough for fast testing

## Notes

- All tests require `overpy` to be installed - tests will be skipped if not available
- Tests make real API calls to the OpenStreetMap Overpass API
- Rate limiting is respected with a 0.1 second delay between requests
- The tests verify actual OSM data retrieval and processing
