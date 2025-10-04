# Metageo Plugin

A powerful FiftyOne plugin for enriching geospatial datasets with OpenStreetMap
(OSM) data through an intuitive 5-step workflow.

![Metageo Workflow](https://img.shields.io/badge/Status-Alpha-orange)
![FiftyOne Version](https://img.shields.io/badge/FiftyOne-%3E%3D0.22.2-blue)

## Overview

The Metageo plugin allows you to automatically enrich your geospatial datasets
with rich contextual information from OpenStreetMap. Whether you're working
with drone imagery, satellite data, or any geospatial dataset, this plugin
helps you add valuable metadata like road types, building classifications,
amenities, and more.

## Features

-   **🗺️ Geographic Indexing**: Automatically detect or manually define
    geographic areas for OSM data extraction
-   **🔧 Flexible Mapping**: Configure how OSM tags map to your dataset schema
    (as tags or detections)
-   **⚡ Efficient Enrichment**: Batch process samples with configurable search
    radius
-   **🔍 Smart Filtering**: Create FiftyOne filters for the enriched data
-   **🧹 Cleanup Tools**: Remove indexed data and enriched fields when no
    longer needed

## Installation

```bash
# Clone the repository
git clone https://github.com/voxel51/fiftyone-plugins.git
cd fiftyone-plugins

# Install the plugin
pip install -e plugins/metageo
```

## Usage

### 1. Launch FiftyOne with the Plugin

```python
import fiftyone as fo
import fiftyone.zoo as foz

# Load a dataset with geospatial data
dataset = foz.load_zoo_dataset("quickstart-geo")  # or your own dataset
session = fo.launch_app(dataset)
```

### 2. Access the Metageo Panel

1. Open the FiftyOne App
2. Navigate to the "Metageo" panel in the sidebar
3. Follow the 5-step workflow below

## 5-Step Workflow

### Step 1: Index Geographic Area

**Purpose**: Define the geographic area and create an OSM data grid for
efficient access.

**Actions**:

-   Select a geo field from your dataset (e.g., `location`, `coordinates`)
-   Choose the number of grid tiles for data partitioning
-   Auto-detect bounding box from your data or set manually
-   The system creates an efficient spatial index for OSM data

**Example**:

```python
# Your dataset should have a geo field like:
sample.location = [longitude, latitude]  # GeoPointField
```

### Step 2: Configure Tag Mapping

**Purpose**: Define how OSM tags should be mapped to your dataset schema.

**Actions**:

-   Explore available OSM tags in your geographic area
-   Configure mappings for each tag:
    -   **OSM Key**: The OpenStreetMap tag key (e.g., `highway`, `amenity`)
    -   **Target Field**: Where to store the data in your dataset
    -   **Type**: Store as `tag` or `detection`
-   Set search radius for finding nearby OSM features

**Example Mappings**:

```python
# OSM highway tag → dataset field
"highway" → "road_type" (as tag)

# OSM amenity tag → dataset field
"amenity" → "nearby_amenities" (as detection)

# OSM building tag → dataset field
"building" → "building_type" (as tag)
```

### Step 3: Enrich Samples

**Purpose**: Fetch OSM data and apply it to your samples based on their
locations.

**Actions**:

-   Prefetch OSM data for the defined area and selected tags
-   Enrich samples by finding nearby OSM features within the specified radius
-   Monitor progress and results

**What happens**:

-   For each sample, the system finds OSM features within the search radius
-   Data is added to samples according to the mapping configuration
-   Progress is tracked and reported

### Step 4: Create Search Filters

**Purpose**: Leverage the enriched data for filtering and analysis.

**Actions**:

-   Use FiftyOne's sidebar filters to search by the new OSM data
-   Create complex queries combining geographic and semantic information
-   Export filtered views for further analysis

**Example Filters**:

```python
# Find samples near highways
dataset.match(F("road_type") == "highway")

# Find samples near restaurants
dataset.match(F("nearby_amenities") == "restaurant")

# Find samples in residential areas
dataset.match(F("building_type") == "residential")
```

### Step 5: Cleanup (Optional)

**Purpose**: Remove indexed data and enriched fields when no longer needed.

**Actions**:

-   Remove indexed OSM data to free up storage
-   Remove enriched fields from samples
-   Clean up temporary files and caches

## Example Use Cases

### Drone Imagery Analysis

```python
# Enrich drone images with road and building information
# Step 1: Index the flight area
# Step 2: Map highway, building, and landuse tags
# Step 3: Enrich with 50m radius
# Step 4: Filter for images containing roads or buildings
```

### Satellite Image Classification

```python
# Add urban/rural context to satellite imagery
# Step 1: Index the satellite coverage area
# Step 2: Map landuse, natural, and leisure tags
# Step 3: Enrich with 100m radius
# Step 4: Create filters for urban vs rural areas
```

### Autonomous Vehicle Data

```python
# Enhance driving scene data with road context
# Step 1: Index the driving route
# Step 2: Map highway, traffic_calming, and amenity tags
# Step 3: Enrich with 25m radius
# Step 4: Filter for different road types and conditions
```

## Configuration Options

### Search Radius

-   **Range**: 10-1000 meters
-   **Default**: 100 meters
-   **Recommendation**:
    -   25-50m for high-resolution imagery
    -   100-200m for satellite imagery
    -   50-100m for general use

### Grid Tiles

-   **Range**: 1-100 tiles
-   **Default**: 16 tiles
-   **Purpose**: Controls data partitioning for efficient processing

### Tag Types

-   **Tag**: Simple key-value pairs (e.g., `road_type: "highway"`)
-   **Detection**: Complex objects with bounding boxes and properties

## Data Sources

The plugin uses OpenStreetMap data, which provides:

-   **Road networks**: Highway types, traffic calming, etc.
-   **Buildings**: Residential, commercial, industrial, etc.
-   **Amenities**: Restaurants, schools, hospitals, etc.
-   **Land use**: Urban, agricultural, natural areas, etc.
-   **Natural features**: Water bodies, forests, parks, etc.

## Performance Considerations

-   **Indexing**: One-time operation, scales with geographic area size
-   **Enrichment**: Scales with number of samples and search radius
-   **Storage**: Enriched data adds minimal overhead to your dataset
-   **Caching**: OSM data is cached for efficient repeated access

## Troubleshooting

### Common Issues

1. **No geo fields found**

    - Ensure your dataset has GeoPointField or geo-enabled fields
    - Check field names like `location`, `coordinates`, `geo`

2. **No OSM data in area**

    - Verify the bounding box covers populated areas
    - Try increasing the search radius
    - Check if the area has OpenStreetMap coverage

3. **Slow enrichment**
    - Reduce the search radius
    - Limit the number of tag mappings
    - Use a smaller geographic area

### Error Messages

-   **"No coordinates found"**: Check your geo field contains valid coordinates
-   **"Failed to explore tags"**: Verify internet connection and OSM API access
-   **"Prefetch failed"**: Check geographic area size and available OSM data

## Development

### Building the Plugin

```bash
cd plugins/metageo
yarn install
yarn build
```

### Running Tests

The plugin includes comprehensive tests for the OSM API integration:

```bash
# Install test dependencies
pip install pytest overpy

# Run all tests
pytest tests/ -v

# Run with output
pytest tests/ -v -s
```

See `tests/README.md` for detailed testing instructions.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run the test suite: `pytest tests/ -v`
6. Submit a pull request

## License

Apache 2.0 - see [LICENSE](../../LICENSE) for details.

## Support

-   **Documentation**: [FiftyOne Docs](https://docs.voxel51.com)
-   **Issues**:
    [GitHub Issues](https://github.com/voxel51/fiftyone-plugins/issues)
-   **Discussions**:
    [GitHub Discussions](https://github.com/voxel51/fiftyone-plugins/discussions)

---

**Note**: This plugin is currently in alpha. The API and functionality may
change in future releases.
