from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import time
import requests
import fiftyone.operators.types as fo_types
from fiftyone.operators.categories import Categories
from fiftyone.operators.executor import ExecutionContext
from fiftyone.operators.panel import Panel, PanelConfig
from fiftyone.operators.types import Property
import fiftyone.operators as foo

# Try to import overpy, install if not available
try:
    import overpy
except ImportError:
    print("overpy not found. Please install with: pip install overpy")
    overpy = None

BBox = Tuple[float, float, float, float]  # minLon, minLat, maxLon, maxLat


class OSMClient:
    """Client for querying OpenStreetMap data via Overpass API"""

    def __init__(
        self, endpoint: str = "https://overpass-api.de/api/interpreter"
    ):
        self.endpoint = endpoint
        self.api = overpy.Overpass(url=endpoint) if overpy else None
        self.rate_limit_delay = 0.1  # seconds between requests

    def query_bbox(
        self, bbox: BBox, feature_types: List[str] = None, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0
    ) -> Dict[str, Any]:
        """
        Query OSM data within a bounding box with retry logic for rate limiting

        Args:
            bbox: [minLon, minLat, maxLon, maxLat] - will be normalized to (south, west, north, east)
            feature_types: List of OSM feature types to query
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds

        Returns:
            Dict containing query results and metadata
        """
        if not overpy:
            return {
                "error": "overpy not available",
                "features": [],
                "count": 0,
            }

        if not feature_types:
            feature_types = [
                "highway",
                "amenity",
                "building",
                "leisure",
                "natural",
                "landuse",
                "waterway",
                "railway",
                "power",
                "barrier",
            ]

        # Normalize bbox to (south, west, north, east) format
        min_lon, min_lat, max_lon, max_lat = bbox
        south, west, north, east = min_lat, min_lon, max_lat, max_lon

        # Build Overpass QL query with proper syntax
        # Start with just nodes to avoid API limits, then add ways and relations if needed
        # We'll filter by feature types in Python code for better reliability
        query = f"node({south},{west},{north},{east});out body;"
        
        print(f"DEBUG: Using simple query to get nodes in bounding box")
        print(f"DEBUG: Query length: {len(query)} characters")

        # Retry logic with exponential backoff
        for attempt in range(max_retries + 1):
            try:
                print(f"OVERPASS QUERY (attempt {attempt + 1}/{max_retries + 1}): {query}")
                print(
                    f"BBOX: {bbox} -> (south={south}, west={west}, north={north}, east={east})"
                )
                print(f"FEATURE TYPES: {feature_types}")
                print(f"COORDINATE DEBUG: min_lon={min_lon}, min_lat={min_lat}, max_lon={max_lon}, max_lat={max_lat}")
                print(f"COORDINATE DEBUG: south={south}, west={west}, north={north}, east={east}")

                # Execute query with rate limiting
                time.sleep(self.rate_limit_delay)
                
                # Test with a simple query first to debug coordinate issues
                test_query = f"node({south},{west},{north},{east});out body;"
                print(f"TEST QUERY: {test_query}")
                test_result = self.api.query(test_query)
                print(f"TEST RESULT: nodes={len(test_result.nodes)}")
                
                result = self.api.query(query)

                print(
                    f"RAW RESULT: nodes={len(result.nodes)}, ways={len(result.ways)}, relations={len(result.relations)}"
                )
                
                # Debug: Check if we have any results at all
                if len(result.nodes) == 0 and len(result.ways) == 0 and len(result.relations) == 0:
                    print("WARNING: No results returned from Overpass API")
                    print(f"Query was: {query}")
                    print(f"Bounding box: south={south}, west={west}, north={north}, east={east}")
                else:
                    print(f"SUCCESS: Found {len(result.nodes)} nodes, {len(result.ways)} ways, {len(result.relations)} relations")
                    
                # Debug: Check if the query is too broad and being limited
                if len(result.nodes) == 0 and len(result.ways) == 0:
                    print("WARNING: Query returned 0 nodes and 0 ways - this might indicate the query is too broad")
                    print("The Overpass API might be limiting results due to query complexity or size")

                # Process results
                features = []

                # Process nodes
                for node in result.nodes:
                    try:
                        feature_type = self._get_primary_tag(node.tags) if node.tags else None
                        feature = {
                            "type": "node",
                            "id": node.id,
                            "lat": float(node.lat),
                            "lon": float(node.lon),
                            "tags": dict(node.tags) if node.tags else {},
                            "feature_type": feature_type,
                        }
                        features.append(feature)
                        
                        # Debug: Log first few features
                        if len(features) <= 3:
                            print(f"DEBUG: Node {node.id} - tags: {dict(node.tags) if node.tags else {}}, feature_type: {feature_type}")
                    except Exception as e:
                        print(f"Error processing node {node.id}: {e}")
                        continue

                # Process ways (if any)
                for way in result.ways:
                    try:
                        feature_type = self._get_primary_tag(way.tags) if way.tags else None
                        feature = {
                            "type": "way",
                            "id": way.id,
                            "nodes": [node.id for node in way.nodes],
                            "tags": dict(way.tags) if way.tags else {},
                            "feature_type": feature_type,
                        }
                        features.append(feature)
                        
                        # Debug: Log first few features
                        if len(features) <= 6:  # 3 nodes + 3 ways
                            print(f"DEBUG: Way {way.id} - tags: {dict(way.tags) if way.tags else {}}, feature_type: {feature_type}")
                    except Exception as e:
                        print(f"Error processing way {way.id}: {e}")
                        continue

                # Process relations (if any)
                for relation in result.relations:
                    try:
                        feature_type = self._get_primary_tag(relation.tags) if relation.tags else None
                        feature = {
                            "type": "relation",
                            "id": relation.id,
                            "members": [
                                {"type": type(m).__name__, "ref": m.ref, "role": m.role}
                                for m in relation.members
                            ],
                            "tags": dict(relation.tags) if relation.tags else {},
                            "feature_type": feature_type,
                        }
                        features.append(feature)
                        
                        # Debug: Log first few features
                        if len(features) <= 9:  # 3 nodes + 3 ways + 3 relations
                            print(f"DEBUG: Relation {relation.id} - tags: {dict(relation.tags) if relation.tags else {}}, feature_type: {feature_type}")
                    except Exception as e:
                        print(f"Error processing relation {relation.id}: {e}")
                        continue

                result_data = {
                    "status": "success",
                    "features": features,
                    "count": len(features),
                    "bbox": bbox,
                    "feature_types": feature_types,
                    "query_time": datetime.now().isoformat(),
                    "attempts": attempt + 1,
                }

                # Filter features to only include those with our target feature types
                filtered_features = []
                feature_type_counts = {}
                for feature in features:
                    feature_type = feature.get("feature_type")
                    if feature_type:
                        feature_type_counts[feature_type] = feature_type_counts.get(feature_type, 0) + 1
                    
                    # Check if this feature matches any of our target feature types
                    # Either through the primary tag or by checking all tags
                    tags = feature.get("tags", {})
                    matches_target = False
                    
                    if feature_type in feature_types:
                        matches_target = True
                    else:
                        # Check if any of the target feature types are in the tags
                        for target_type in feature_types:
                            if target_type in tags:
                                matches_target = True
                                break
                    
                    if matches_target:
                        filtered_features.append(feature)
                
                print(f"FEATURE TYPE COUNTS: {feature_type_counts}")
                print(f"TARGET FEATURE TYPES: {feature_types}")
                
                print(f"FINAL RESULT: {len(features)} total features, {len(filtered_features)} matching target types")
                if len(filtered_features) > 0:
                    print(f"Sample filtered feature: {filtered_features[0]}")
                else:
                    print("No features found matching target types - this might indicate a filtering issue")
                    if len(features) > 0:
                        print(f"Sample unfiltered feature: {features[0]}")

                # Update result data with filtered features
                result_data["features"] = filtered_features
                result_data["count"] = len(filtered_features)

                return result_data

            except overpy.exception.OverpassTooManyRequests:
                error_msg = "Too many requests - rate limited"
                print(f"Rate limited on attempt {attempt + 1}: {error_msg}")
                
                if attempt < max_retries:
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        "status": "error",
                        "error": f"{error_msg} (after {max_retries + 1} attempts)",
                        "features": [],
                        "count": 0,
                        "bbox": bbox,
                        "attempts": max_retries + 1,
                    }
                    
            except overpy.exception.OverpassBadRequest as e:
                # Bad requests shouldn't be retried
                return {
                    "status": "error",
                    "error": f"Bad request: {str(e)}",
                    "features": [],
                    "count": 0,
                    "bbox": bbox,
                    "attempts": attempt + 1,
                }
                
            except Exception as e:
                error_msg = str(e)
                if (
                    "rate limit" in error_msg.lower()
                    or "too many requests" in error_msg.lower()
                    or "server load too high" in error_msg.lower()
                ):
                    print(f"Rate limited on attempt {attempt + 1}: {error_msg}")
                    
                    if attempt < max_retries:
                        # Calculate exponential backoff delay
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        print(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        return {
                            "status": "error",
                            "error": f"Rate limited by OSM API (after {max_retries + 1} attempts)",
                            "features": [],
                            "count": 0,
                            "bbox": bbox,
                            "attempts": max_retries + 1,
                        }
                else:
                    # Other errors shouldn't be retried
                    return {
                        "status": "error",
                        "error": f"OSM query error: {error_msg}",
                        "features": [],
                        "count": 0,
                        "bbox": bbox,
                        "attempts": attempt + 1,
                    }

    def _get_primary_tag(self, tags: Dict[str, str]) -> str:
        """Extract the primary feature type from tags"""
        if not tags:
            return None

        try:
            # Priority order for feature types
            priority_types = [
                "highway",
                "amenity",
                "building",
                "leisure",
                "natural",
                "landuse",
                "waterway",
                "railway",
                "power",
                "barrier",
            ]

            for tag_type in priority_types:
                if tag_type in tags:
                    return tag_type

            # Return first tag if no priority type found
            return next(iter(tags.keys())) if tags else None
        except Exception as e:
            print(f"Error extracting primary tag from {tags}: {e}")
            return None

    def get_feature_statistics(self, features: List[Dict]) -> Dict[str, Any]:
        """Generate statistics from OSM features"""
        if not features:
            return {"total": 0, "by_type": {}, "by_feature_type": {}}

        stats = {"total": len(features), "by_type": {}, "by_feature_type": {}}

        for feature in features:
            # Count by OSM type (node, way, relation)
            osm_type = feature.get("type", "unknown")
            stats["by_type"][osm_type] = stats["by_type"].get(osm_type, 0) + 1

            # Count by feature type (highway, amenity, etc.)
            feature_type = feature.get("feature_type", "unknown")
            stats["by_feature_type"][feature_type] = (
                stats["by_feature_type"].get(feature_type, 0) + 1
            )

        return stats


class IndexGridOperator(foo.Operator):
    """Operator for indexing the entire grid efficiently"""

    @property
    def config(self):
        print("IndexGridOperator.config() called")
        return foo.OperatorConfig(
            name="index_grid",
            label="Index Entire Grid",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
        )

    def execute(self, ctx: ExecutionContext):
        """Execute indexing for the entire grid"""
        print("IndexGridOperator.execute() called!")
        print(f"IndexGridOperator params: {ctx.params}")

        indexing_id = ctx.params.get("indexing_id")

        if not indexing_id:
            raise ValueError("'indexing_id' is required")

        print(f"Starting grid indexing for {indexing_id}")

        # Get the grid from the execution store
        indexing_state = ctx.store("metageo").get("indexing_state")
        if not indexing_state or not indexing_state.get("grid_cells"):
            raise RuntimeError("No grid found in execution store")

        grid_cells = indexing_state["grid_cells"]
        print(f"IndexGridOperator: Retrieved {len(grid_cells)} grid cells from store")
        print(f"IndexGridOperator: First few cells: {grid_cells[:3]}")
        
        active_cells = [
            cell for cell in grid_cells if cell.get("sample_count", 0) > 0
        ]
        print(f"IndexGridOperator: Filtered to {len(active_cells)} active cells")

        print(
            f"IndexGridOperator: Found {len(grid_cells)} total cells, {len(active_cells)} active cells"
        )

        # Mark empty cells as "empty" in the store
        print(f"IndexGridOperator: Checking {len(grid_cells)} cells for empty status...")
        for cell in grid_cells:
            cell_id = cell["id"]
            sample_count = cell.get("sample_count", 0)
            print(f"IndexGridOperator: Cell {cell_id} has sample_count: {sample_count} (type: {type(sample_count)})")
            if sample_count == 0:
                ctx.store("metageo").set(f"cell_{cell_id}_status", "empty")
                print(
                    f"IndexGridOperator: Marked cell {cell_id} as empty (0 samples)"
                )
            else:
                print(f"IndexGridOperator: Cell {cell_id} has {sample_count} samples, will process")

        # Initialize OSM client
        osm_client = OSMClient()
        if not osm_client.api:
            raise RuntimeError(
                "OSM client not available - please install overpy: pip install overpy"
            )

        print(f"IndexGridOperator: OSM client initialized successfully")

        # Process all active cells
        completed_cells = 0
        failed_cells = 0
        rate_limited_cells = 0
        total_features = 0

        print(
            f"IndexGridOperator: Starting to process {len(active_cells)} active cells"
        )

        for i, cell in enumerate(active_cells):
            # Check if indexing has been cancelled
            current_state = ctx.store("metageo").get("indexing_state")
            if current_state and current_state.get("status") == "cancelled":
                print(
                    f"IndexGridOperator: Indexing cancelled, stopping processing at cell {i+1}"
                )
                return {
                    "status": "cancelled",
                    "indexing_id": indexing_id,
                    "message": "Indexing operation was cancelled",
                }

            cell_id = cell["id"]
            coordinates = cell["coordinates"]
            sample_count = cell.get("sample_count", 0)

            print(
                f"IndexGridOperator: Processing cell {i+1}/{len(active_cells)}: {cell_id} (samples: {sample_count})"
            )

            try:
                # Query OSM data for this cell
                print(f"API CALL: Cell {cell_id} - coordinates: {coordinates}")
                osm_result = osm_client.query_bbox(coordinates)
                print(
                    f"API RESULT: Cell {cell_id} - count: {osm_result.get('count', 0)}, error: {osm_result.get('error', 'None')}"
                )

                if "error" in osm_result:
                    # Check if it's a rate limit error
                    error_msg = osm_result["error"]
                    if (
                        "rate limit" in error_msg.lower()
                        or "server load too high" in error_msg.lower()
                        or "too many requests" in error_msg.lower()
                    ):
                        status = "rate_limited"
                        rate_limited_cells += 1
                        # print(f"IndexGridOperator: Cell {cell_id} rate limited - {error_msg}")
                    else:
                        status = "failed"
                        failed_cells += 1
                        # print(f"IndexGridOperator: Cell {cell_id} failed - {error_msg}")

                    # Store status in execution store
                    ctx.store("metageo").set(f"cell_{cell_id}_status", status)
                    ctx.store("metageo").set(
                        f"cell_{cell_id}_error", error_msg
                    )

                else:
                    # Store successful data in execution store
                    feature_count = osm_result["count"]
                    status = "completed"
                    completed_cells += 1
                    total_features += feature_count

                    # Store the actual OSM data
                    osm_data = osm_result.get("features", [])

                    ctx.store("metageo").set(f"cell_{cell_id}_status", status)
                    ctx.store("metageo").set(
                        f"cell_{cell_id}_osm_features", feature_count
                    )
                    ctx.store("metageo").set(
                        f"cell_{cell_id}_osm_data", osm_data
                    )

                    # print(f"IndexGridOperator: Cell {cell_id} completed - {feature_count} OSM features")
                    if feature_count > 0:
                        print(
                            f"OSM DATA: Cell {cell_id} - {feature_count} features: {osm_data[:2]}"
                        )
                    # else:
                    #     print(f"  - No OSM features found in this cell")

                # Add a small delay to avoid overwhelming the OSM API
                import time

                time.sleep(0.1)  # 100ms delay between requests

            except Exception as e:
                # Store failed status in execution store
                failed_cells += 1
                ctx.store("metageo").set(f"cell_{cell_id}_status", "failed")
                ctx.store("metageo").set(f"cell_{cell_id}_error", str(e))
                # print(f"IndexGridOperator: Cell {cell_id} error - {e}")

        # Update the indexing state with final results
        final_state = {
            **indexing_state,
            "status": "completed",
            "completed_cells": completed_cells,
            "failed_cells": failed_cells,
            "rate_limited_cells": rate_limited_cells,
            "total_features": total_features,
            "completed_at": datetime.now().isoformat(),
        }

        ctx.store("metageo").set("indexing_state", final_state)

        # print(f"IndexGridOperator: Grid indexing completed!")
        # print(f"  - Completed cells: {completed_cells}")
        # print(f"  - Failed cells: {failed_cells}")
        # print(f"  - Rate limited cells: {rate_limited_cells}")
        # print(f"  - Total OSM features: {total_features}")

        # Trigger React operator to update the UI
        try:
            ctx.trigger(
                "@voxel51/metageo/grid_indexing_completed",
                {
                    "indexing_id": indexing_id,
                    "completed_cells": completed_cells,
                    "failed_cells": failed_cells,
                    "rate_limited_cells": rate_limited_cells,
                    "total_features": total_features,
                    "status": "completed",
                },
            )
            # print("IndexGridOperator: Successfully triggered grid_indexing_completed operator")
        except Exception as e:
            # print(f"IndexGridOperator: Error triggering grid_indexing_completed operator: {e}")
            pass

        return {
            "status": "completed",
            "indexing_id": indexing_id,
            "completed_cells": completed_cells,
            "failed_cells": failed_cells,
            "rate_limited_cells": rate_limited_cells,
            "total_features": total_features,
            "message": f"Grid indexing completed: {completed_cells} cells processed, {total_features} features found",
        }


class WatchIndexingOperator(foo.Operator):
    """Operator for watching indexing progress and reporting via ctx.trigger()"""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="watch_indexing",
            label="Watch Indexing Progress",
            execute_as_generator=True,
            allow_delegated_execution=True,
            allow_immediate_execution=True,
        )

    def execute(self, ctx: ExecutionContext):
        """Watch indexing progress and report updates"""
        # print("WatchIndexingOperator.execute() called!")
        # print(f"WatchIndexingOperator params: {ctx.params}")

        indexing_id = ctx.params.get("indexing_id")
        total_cells = ctx.params.get("total_cells", 0)
        active_cells = ctx.params.get("active_cells", 0)

        if not indexing_id:
            raise ValueError("'indexing_id' is required")

        # print(f"Watching indexing progress for {indexing_id}")

        # Trigger initial state
        yield ctx.trigger(
            "@voxel51/metageo/indexing_started",
            {
                "indexing_id": indexing_id,
                "total_cells": total_cells,
                "active_cells": active_cells,
                "status": "watching",
            },
        )

        # Get the grid cells from the execution store
        indexing_state = ctx.store("metageo").get("indexing_state")
        # print(f"Watch operator: Retrieved indexing_state: {indexing_state is not None}")

        if not indexing_state:
            # print("Watch operator: No indexing_state found in execution store")
            return

        if "grid_cells" not in indexing_state:
            # print(f"Watch operator: No grid_cells in indexing_state. Keys: {list(indexing_state.keys())}")
            return

        grid_cells = indexing_state["grid_cells"]
        total_cells = len(grid_cells)
        active_cells = len(
            [cell for cell in grid_cells if cell.get("sample_count", 0) > 0]
        )

        # print(f"Watch operator: Found {total_cells} total cells, {active_cells} active cells")

        # Wait for the IndexGridOperator to complete by monitoring the indexing state
        while True:
            # Check if indexing has been cancelled
            current_state = ctx.store("metageo").get("indexing_state")
            if current_state and current_state.get("status") == "cancelled":
                # print("WatchIndexingOperator: Indexing cancelled, stopping monitoring")
                yield ctx.trigger(
                    "@voxel51/metageo/indexing_completed",
                    {
                        "indexing_id": indexing_id,
                        "status": "cancelled",
                        "message": "Indexing operation was cancelled",
                    },
                )
                return

            # Check if IndexGridOperator has completed
            if current_state and current_state.get("status") == "completed":
                # print("WatchIndexingOperator: IndexGridOperator completed, collecting final results")
                break

            # Check for individual cell updates and send them to React
            completed_cells = 0
            failed_cells = 0
            rate_limited_cells = 0
            total_features = 0

            # Check each cell status and send individual updates
            for cell in grid_cells:
                cell_id = cell["id"]
                try:
                    status = ctx.store("metageo").get(f"cell_{cell_id}_status")

                    # Only process cells that have a status (not None/empty)
                    if status and status in [
                        "completed",
                        "failed",
                        "rate_limited",
                        "empty",
                    ]:
                        if status == "completed":
                            completed_cells += 1
                            osm_features = ctx.store("metageo").get(
                                f"cell_{cell_id}_osm_features"
                            )
                            if osm_features is not None:
                                total_features += osm_features

                            # Send individual cell update
                            yield ctx.trigger(
                                "@voxel51/metageo/cell_status_update",
                                {
                                    "cell_id": cell_id,
                                    "status": "completed",
                                    "osm_features": osm_features or 0,
                                    "error": None,
                                },
                            )

                        elif status == "failed":
                            failed_cells += 1
                            error_msg = ctx.store("metageo").get(
                                f"cell_{cell_id}_error"
                            )

                            # Send individual cell update
                            yield ctx.trigger(
                                "@voxel51/metageo/cell_status_update",
                                {
                                    "cell_id": cell_id,
                                    "status": "failed",
                                    "osm_features": 0,
                                    "error": error_msg,
                                },
                            )

                        elif status == "rate_limited":
                            rate_limited_cells += 1
                            error_msg = ctx.store("metageo").get(
                                f"cell_{cell_id}_error"
                            )

                            # Send individual cell update
                            yield ctx.trigger(
                                "@voxel51/metageo/cell_status_update",
                                {
                                    "cell_id": cell_id,
                                    "status": "rate_limited",
                                    "osm_features": 0,
                                    "error": error_msg,
                                },
                            )

                        elif status == "empty":
                            # Send individual cell update for empty cells
                            yield ctx.trigger(
                                "@voxel51/metageo/cell_status_update",
                                {
                                    "cell_id": cell_id,
                                    "status": "empty",
                                    "osm_features": 0,
                                    "error": None,
                                },
                            )

                        # print(f"Watch operator: Sent update for cell {cell_id} - status: {status}")
                    else:
                        # Cell hasn't been processed yet
                        # print(f"Watch operator: Cell {cell_id} not yet processed (status: {status})")
                        pass

                except Exception as e:
                    # print(f"Watch operator: Error reading cell {cell_id} status: {e}")
                    continue

            # Report overall progress
            processed_cells = (
                completed_cells + failed_cells + rate_limited_cells
            )
            progress = (
                (processed_cells / active_cells * 100)
                if active_cells > 0
                else 0
            )

            # print(f"Watch operator: Progress update - {processed_cells}/{active_cells} cells processed ({progress:.1f}%)")
            # print(f"  - Completed: {completed_cells}")
            # print(f"  - Failed: {failed_cells}")
            # print(f"  - Rate limited: {rate_limited_cells}")
            # print(f"  - Total features: {total_features}")

            yield ctx.trigger(
                "@voxel51/metageo/indexing_progress",
                {
                    "indexing_id": indexing_id,
                    "completed_cells": completed_cells,
                    "failed_cells": failed_cells,
                    "rate_limited_cells": rate_limited_cells,
                    "total_cells": active_cells,
                    "total_features": total_features,
                    "progress": progress,
                },
            )

            # Wait before next check
            import time

            time.sleep(1)  # Check every second for real-time updates

        # Get final results from the completed IndexGridOperator
        final_state = ctx.store("metageo").get("indexing_state")
        if final_state and final_state.get("status") == "completed":
            final_completed = final_state.get("completed_cells", 0)
            final_failed = final_state.get("failed_cells", 0)
            final_rate_limited = final_state.get("rate_limited_cells", 0)
            final_features = final_state.get("total_features", 0)

            # print(f"WatchIndexingOperator: Final results from IndexGridOperator:")
            # print(f"  - Completed cells: {final_completed}")
            # print(f"  - Failed cells: {final_failed}")
            # print(f"  - Rate limited cells: {final_rate_limited}")
            # print(f"  - Total features: {final_features}")

            yield ctx.trigger(
                "@voxel51/metageo/indexing_completed",
                {
                    "indexing_id": indexing_id,
                    "completed_cells": final_completed,
                    "failed_cells": final_failed,
                    "rate_limited_cells": final_rate_limited,
                    "total_cells": active_cells,
                    "total_features": final_features,
                    "status": "completed",
                },
            )
        else:
            # Fallback to our own count if final state not available
            yield ctx.trigger(
                "@voxel51/metageo/indexing_completed",
                {
                    "indexing_id": indexing_id,
                    "completed_cells": completed_cells,
                    "failed_cells": failed_cells,
                    "rate_limited_cells": rate_limited_cells,
                    "total_cells": active_cells,
                    "total_features": total_features,
                    "status": "completed",
                },
            )


class ResetMetageoOperator(foo.Operator):
    """Operator for completely resetting all metageo state and configuration"""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="reset_metageo",
            label="Reset Metageo",
            allow_delegated_execution=False,
            allow_immediate_execution=True,
        )

    def execute(self, ctx: ExecutionContext):
        """Reset all metageo state and configuration"""
        print("ResetMetageoOperator.execute() called!")
        
        try:
            # Clear all metageo-related data from the execution store
            store = ctx.store("metageo")
            
            # Get all keys in the store to clear them
            all_keys = []
            
            # Clear indexing state
            indexing_state = store.get("indexing_state")
            if indexing_state:
                # Clear individual cell data
                grid_cells = indexing_state.get("grid_cells", [])
                for cell in grid_cells:
                    cell_id = cell["id"]
                    all_keys.extend([
                        f"cell_{cell_id}_status",
                        f"cell_{cell_id}_error", 
                        f"cell_{cell_id}_osm_features",
                        f"cell_{cell_id}_osm_data"
                    ])
            
            # Clear main state keys
            main_keys = [
                "indexing_state",
                "mapping_config", 
                "sample_distribution",
                "bbox",
                "grid_tiles",
                "geo_field",
                "location"
            ]
            all_keys.extend(main_keys)
            
            # Delete all keys
            for key in all_keys:
                try:
                    store.delete(key)
                    print(f"ResetMetageoOperator: Deleted key '{key}'")
                except Exception as e:
                    print(f"ResetMetageoOperator: Error deleting key '{key}': {e}")
            
            # Clear panel data
            ctx.panel.clear_data()
            
            print("ResetMetageoOperator: Successfully reset all metageo state")
            
            return {
                "status": "success",
                "message": "All metageo state and configuration has been reset",
                "cleared_keys": len(all_keys)
            }
            
        except Exception as e:
            print(f"ResetMetageoOperator: Error during reset: {e}")
            return {
                "status": "error", 
                "message": f"Error resetting metageo state: {str(e)}"
            }


class MetageoPanel(Panel):
    @property
    def config(self) -> PanelConfig:
        return PanelConfig(
            name="metageo_panel",
            label="Metageo",
            icon="map",
            category=Categories.ANALYZE,
            alpha=True,
        )

    def on_load(self, ctx: ExecutionContext) -> None:
        can_edit = (
            True
            if (ctx.user is None)
            else ctx.user.dataset_permission in ["EDIT", "MANAGE"]
        )
        geo_fields = self._get_geo_fields(ctx.dataset)
        default_field = (
            "location"
            if "location" in ctx.dataset.get_field_schema()
            else (geo_fields[0] if geo_fields else None)
        )

        # Debug information
        field_schema = ctx.dataset.get_field_schema()
        all_fields = list(field_schema.keys())

        print(f"Dataset: {ctx.dataset.name}")
        print(f"All fields: {all_fields}")
        print(f"Geo fields found: {geo_fields}")
        print(f"Default field: {default_field}")

        # Check for existing index
        existing_index = self.get_existing_index(ctx)
        has_existing_index = existing_index.get("status") == "found"

        print(f"Existing index found: {has_existing_index}")
        if has_existing_index:
            print(f"  - Index ID: {existing_index.get('indexing_id')}")
            print(
                f"  - Completed cells: {existing_index.get('completed_cells')}"
            )
            print(
                f"  - Total features: {existing_index.get('total_features')}"
            )

        ctx.panel.set_data("can_edit", can_edit)
        ctx.panel.set_data("geo_fields", geo_fields)
        ctx.panel.set_data("default_geo_field", default_field)
        ctx.panel.set_data("dataset_name", ctx.dataset.name)
        ctx.panel.set_data("total_fields", len(ctx.dataset.get_field_schema()))
        ctx.panel.set_data("all_fields", all_fields)  # For debugging
        ctx.panel.set_data("has_existing_index", has_existing_index)
        ctx.panel.set_data(
            "existing_index", existing_index if has_existing_index else None
        )

    def _get_geo_fields(self, dataset) -> list[str]:
        """Get all geographic fields from the dataset."""
        geo_fields = []
        field_schema = dataset.get_field_schema()

        for path, f in field_schema.items():
            try:
                # Check for explicit geo flag
                if getattr(f, "geo", False):
                    geo_fields.append(path)
                    continue

                # Check for GeoPointField type
                if getattr(f, "ftype", "") == "GeoPointField":
                    geo_fields.append(path)
                    continue

                # Check for common geo field names
                if any(
                    geo_name in path.lower()
                    for geo_name in [
                        "location",
                        "geo",
                        "lat",
                        "lon",
                        "coordinates",
                        "point",
                    ]
                ):
                    geo_fields.append(path)
                    continue

                # Check if field has coordinates subfield (common pattern)
                if f"{path}.coordinates" in field_schema:
                    geo_fields.append(path)
                    continue

                # Check for embedded geo fields
                if hasattr(f, "embedded_document_type"):
                    embedded_fields = getattr(
                        f, "embedded_document_type", {}
                    ).get("fields", {})
                    if any(
                        "coordinates" in str(field)
                        for field in embedded_fields.values()
                    ):
                        geo_fields.append(path)
                        continue

            except Exception as e:
                # Log the error but continue checking other fields
                print(f"Error checking field {path}: {e}")
                pass

        # If no geo fields found, try to find any field with coordinates
        if not geo_fields:
            for path, f in field_schema.items():
                try:
                    # Check if this field has a coordinates subfield
                    if f"{path}.coordinates" in field_schema:
                        geo_fields.append(path)
                except Exception:
                    pass

        return geo_fields

    def get_geo_fields(self, ctx: ExecutionContext) -> dict[str, any]:
        """Get available geo fields and validation info."""
        print(f"🔍 get_geo_fields: Method called for dataset: {ctx.dataset.name}")
        
        geo_fields = self._get_geo_fields(ctx.dataset)
        print(f"🔍 get_geo_fields: Found geo fields: {geo_fields}")

        result = {
            "geo_fields": geo_fields,
            "has_geo_fields": len(geo_fields) > 0,
            "dataset_name": ctx.dataset.name,
            "total_fields": len(ctx.dataset.get_field_schema()),
            "can_proceed": len(geo_fields) > 0,
        }
        
        print(f"🔍 get_geo_fields: Returning result: {result}")
        return result

    def get_available_osm_tags(self, ctx: ExecutionContext) -> dict[str, any]:
        """Get available OSM tags from the existing index."""
        try:
            # Get the existing index
            indexing_state = ctx.store("metageo").get("indexing_state")
            print(f"get_available_osm_tags: indexing_state = {indexing_state}")
            print(f"get_available_osm_tags: status = {indexing_state.get('status') if indexing_state else 'None'}")
            
            if not indexing_state:
                return {
                    "status": "no_index",
                    "message": "No indexing state found. Please complete the indexing step first.",
                    "tags": [],
                }
            
            # Check if indexing is completed - be more flexible with status checking
            status = indexing_state.get("status", "idle")
            if status not in ["completed", "running"]:
                return {
                    "status": "no_index",
                    "message": f"Indexing not completed. Current status: {status}. Please complete the indexing step first.",
                    "tags": [],
                }

            # Collect all unique OSM tags from the index
            all_tags = set()
            tag_counts = {}
            tag_examples = {}  # Store example values for each tag

            # Get all cell data from the store
            store = ctx.store("metageo")
            
            # Get all cell data from the grid cells in indexing state
            grid_cells = indexing_state.get("grid_cells", [])
            print(f"get_available_osm_tags: Processing {len(grid_cells)} grid cells")
            
            for cell in grid_cells:
                cell_id = cell["id"]
                print(f"get_available_osm_tags: Processing cell {cell_id}")
                
                osm_data = store.get(f"cell_{cell_id}_osm_data")
                print(f"get_available_osm_tags: Cell {cell_id} OSM data: {osm_data}")
                
                if osm_data:
                    for feature in osm_data:
                        if isinstance(feature, dict) and "tags" in feature:
                                print(f"get_available_osm_tags: Feature tags: {feature['tags']}")
                                for tag_key, tag_value in feature["tags"].items():
                                    all_tags.add(tag_key)
                                    tag_counts[tag_key] = tag_counts.get(tag_key, 0) + 1
                                    
                                    # Collect example values (limit to 5 per tag)
                                    if tag_key not in tag_examples:
                                        tag_examples[tag_key] = set()
                                    if len(tag_examples[tag_key]) < 5 and tag_value:
                                        tag_examples[tag_key].add(tag_value)

            # Convert to list format for frontend
            tags_list = [
                {
                    "key": tag, 
                    "count": count, 
                    "examples": list(tag_examples.get(tag, []))[:5]  # Limit to 5 examples
                }
                for tag, count in tag_counts.items()
            ]

            # Sort by count (most common first)
            tags_list.sort(key=lambda x: x["count"], reverse=True)

            return {
                "status": "success",
                "tags": tags_list,
                "total_tags": len(tags_list),
                "total_features": indexing_state.get("total_features", 0),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving OSM tags: {str(e)}",
                "tags": [],
            }

    def enrich_dataset_async(self, ctx: ExecutionContext) -> dict[str, any]:
        """Enrich dataset with OSM data asynchronously for multi-dashboard support."""
        try:
            # Get the mapping configuration
            mapping_config = ctx.store("metageo").get("mapping_config")
            print(f"🔍 enrich_dataset_async: Retrieved mapping config from store: {mapping_config}")
            
            if not mapping_config:
                print(f"🔍 enrich_dataset_async: No mapping configuration found in store")
                return {
                    "status": "error",
                    "message": "No mapping configuration found. Please complete the mapping step first.",
                }

            # Get the indexing state
            indexing_state = ctx.store("metageo").get("indexing_state")
            if not indexing_state:
                return {
                    "status": "error", 
                    "message": "No indexing state found. Please complete the indexing step first.",
                }

            # Get dataset info
            dataset = ctx.dataset
            if not dataset:
                return {
                    "status": "error",
                    "message": "No dataset found in context.",
                }

            # Store enrichment job info
            enrichment_job = {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "dataset_name": dataset.name,
                "total_samples": len(dataset),
                "processed_samples": 0,
                "mapping_config": mapping_config,
                "indexing_state": indexing_state,
            }
            
            ctx.store("metageo").set("enrichment_job", enrichment_job)
            
            # Start the enrichment process asynchronously
            # Use FiftyOne's built-in async execution
            import threading
            
            def run_enrichment():
                try:
                    self._start_enrichment_process(ctx, dataset, mapping_config, indexing_state)
                except Exception as e:
                    print(f"🔍 enrich_dataset_async: Background enrichment failed: {e}")
                    # Update job with error status
                    enrichment_job = ctx.store("metageo").get("enrichment_job")
                    if enrichment_job:
                        enrichment_job["status"] = "failed"
                        enrichment_job["error"] = str(e)
                        enrichment_job["failed_at"] = datetime.now().isoformat()
                        ctx.store("metageo").set("enrichment_job", enrichment_job)
            
            # Start enrichment in background thread
            enrichment_thread = threading.Thread(target=run_enrichment, daemon=True)
            enrichment_thread.start()
            
            return {
                "status": "success",
                "message": "Enrichment process started successfully",
                "job_id": "enrichment_job",
                "total_samples": len(dataset),
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error starting enrichment process: {str(e)}",
            }

    def _start_enrichment_process(self, ctx: ExecutionContext, dataset, mapping_config: dict, indexing_state: dict):
        """Start the actual enrichment process."""
        try:
            print(f"🔍 _start_enrichment_process: Starting enrichment for {len(dataset)} samples")
            print(f"🔍 _start_enrichment_process: Mapping config keys: {list(mapping_config.keys()) if mapping_config else 'None'}")
            print(f"🔍 _start_enrichment_process: Mapping config geoField: '{mapping_config.get('geoField', 'NOT_FOUND')}'")
            print(f"🔍 _start_enrichment_process: Mapping config enableSampleTagging: {mapping_config.get('enableSampleTagging', 'NOT_FOUND')}")
            print(f"🔍 _start_enrichment_process: Mapping config enableFieldMapping: {mapping_config.get('enableFieldMapping', 'NOT_FOUND')}")
            print(f"🔍 _start_enrichment_process: Mapping config includeAllTagsAsMetadata: {mapping_config.get('includeAllTagsAsMetadata', 'NOT_FOUND')}")
            print(f"🔍 _start_enrichment_process: Indexing state keys: {list(indexing_state.keys())}")
            
            # Get the geo field from mapping config
            geo_field = mapping_config.get("geoField", "location")
            print(f"🔍 _start_enrichment_process: Using geo field: '{geo_field}'")
            print(f"🔍 _start_enrichment_process: geo_field is empty: {not geo_field}")
            
            # If geo_field is empty, try to use "location" as default
            if not geo_field:
                geo_field = "location"
                print(f"🔍 _start_enrichment_process: geo_field was empty, using default: '{geo_field}'")
            
            # First, define new fields in the dataset schema
            print(f"🔍 _start_enrichment_process: Defining dataset fields...")
            self._define_dataset_fields(dataset, mapping_config)
            
            # Get all OSM data from the index
            store = ctx.store("metageo")
            all_osm_data = {}
            
            # Collect all OSM data from grid cells
            grid_cells = indexing_state.get("grid_cells", [])
            print(f"🔍 _start_enrichment_process: Found {len(grid_cells)} grid cells")
            
            # Debug: Show what's in the first grid cell
            if grid_cells:
                print(f"🔍 _start_enrichment_process: First grid cell structure: {grid_cells[0]}")
                print(f"🔍 _start_enrichment_process: First grid cell keys: {list(grid_cells[0].keys()) if grid_cells[0] else 'None'}")
            
            for cell in grid_cells:
                cell_id = cell["id"]
                print(f"🔍 _start_enrichment_process: Processing cell {cell_id}")
                print(f"🔍 _start_enrichment_process: Cell {cell_id} structure: {cell}")
                osm_data = store.get(f"cell_{cell_id}_osm_data")
                print(f"🔍 _start_enrichment_process: Cell {cell_id} OSM data: {type(osm_data)}, length: {len(osm_data) if osm_data else 0}")
                
                if osm_data:
                    # Store OSM data by cell for spatial lookup
                    all_osm_data[cell_id] = osm_data
                    print(f"🔍 _start_enrichment_process: Loaded {len(osm_data)} OSM features for cell {cell_id}")
                    # Log first few features for debugging
                    if len(osm_data) > 0:
                        print(f"🔍 _start_enrichment_process: First feature in cell {cell_id}: {osm_data[0]}")
                else:
                    print(f"🔍 _start_enrichment_process: No OSM data found for cell {cell_id}")
            
            print(f"🔍 _start_enrichment_process: Total OSM data loaded from {len(all_osm_data)} cells")
            
            # Process samples by iterating through grid cells (more efficient)
            processed_count = 0
            total_samples = len(dataset)
            print(f"🔍 _start_enrichment_process: Processing {total_samples} samples across {len(grid_cells)} grid cells")
            
            # Process each grid cell
            for cell in grid_cells:
                cell_id = cell["id"]
                cell_coordinates = cell.get("coordinates")
                sample_count = cell.get("sample_count", 0)
                
                print(f"🔍 _start_enrichment_process: Processing cell {cell_id} with {sample_count} samples")
                
                if not cell_coordinates or len(cell_coordinates) != 4:
                    print(f"🔍 _start_enrichment_process: Cell {cell_id} has invalid coordinates: {cell_coordinates}")
                    continue
                
                if sample_count == 0:
                    print(f"🔍 _start_enrichment_process: Cell {cell_id} has no samples, skipping")
                    continue
                
                # Get OSM data for this cell
                cell_osm_data = all_osm_data.get(cell_id, [])
                print(f"🔍 _start_enrichment_process: Cell {cell_id} has {len(cell_osm_data)} OSM features")
                
                if not cell_osm_data:
                    print(f"🔍 _start_enrichment_process: Cell {cell_id} has no OSM data, skipping")
                    continue
                
                # Extract cell boundaries
                min_lon, min_lat, max_lon, max_lat = cell_coordinates
                print(f"🔍 _start_enrichment_process: Cell {cell_id} bounds: [{min_lon}, {min_lat}, {max_lon}, {max_lat}]")
                
                # Find samples that fall within this cell's boundaries
                cell_samples = []
                for sample in dataset:
                    try:
                        # Get sample's geographic location
                        if geo_field not in sample:
                            continue
                        
                        geo_location = sample[geo_field]
                        if not geo_location:
                            continue
                        
                        # Convert to lat/lon
                        lon, lat = self._extract_coordinates(geo_location)
                        if lon is None or lat is None:
                            continue
                        
                        # Check if sample falls within this cell
                        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                            cell_samples.append((sample, lon, lat))
                            print(f"🔍 _start_enrichment_process: Sample {sample.id} belongs to cell {cell_id}")
                    
                    except Exception as e:
                        print(f"🔍 _start_enrichment_process: Error checking sample {sample.id} for cell {cell_id}: {e}")
                        continue
                
                print(f"🔍 _start_enrichment_process: Found {len(cell_samples)} samples in cell {cell_id}")
                
                # Process samples in this cell
                for sample, lon, lat in cell_samples:
                    try:
                        print(f"🔍 _start_enrichment_process: Applying mappings to sample {sample.id} in cell {cell_id}")
                        self._apply_mapping_to_sample(sample, cell_osm_data, mapping_config, lon, lat)
                        processed_count += 1
                        
                        # Update progress every 100 samples
                        if processed_count % 100 == 0:
                            self._update_enrichment_progress(ctx, processed_count, total_samples)
                            print(f"🔍 _start_enrichment_process: Processed {processed_count}/{total_samples} samples")
                    
                    except Exception as e:
                        print(f"🔍 _start_enrichment_process: Error processing sample {sample.id} in cell {cell_id}: {e}")
                        continue
            
            # Mark as completed
            enrichment_job = ctx.store("metageo").get("enrichment_job")
            if enrichment_job:
                enrichment_job["status"] = "completed"
                enrichment_job["completed_at"] = datetime.now().isoformat()
                enrichment_job["processed_samples"] = processed_count
                enrichment_job["total_samples"] = total_samples
                ctx.store("metageo").set("enrichment_job", enrichment_job)
            
            print(f"🔍 _start_enrichment_process: Enrichment completed. Processed {processed_count}/{total_samples} samples")
                
        except Exception as e:
            print(f"🔍 _start_enrichment_process: Enrichment failed: {e}")
            # Update job with error status
            enrichment_job = ctx.store("metageo").get("enrichment_job")
            if enrichment_job:
                enrichment_job["status"] = "failed"
                enrichment_job["error"] = str(e)
                enrichment_job["failed_at"] = datetime.now().isoformat()
                ctx.store("metageo").set("enrichment_job", enrichment_job)

    def _define_dataset_fields(self, dataset, mapping_config: dict):
        """Define new fields in the dataset schema based on mapping configuration."""
        try:
            print(f"🔍 _define_dataset_fields: Defining new fields in dataset schema")
            print(f"🔍 _define_dataset_fields: Dataset name: {dataset.name}")
            print(f"🔍 _define_dataset_fields: Current field names: {list(dataset.get_field_schema().keys())}")
            
            # Define fields for sample tagging
            if mapping_config.get("enableSampleTagging", False):
                tag_mappings = mapping_config.get("tagMappings", [])
                print(f"🔍 _define_dataset_fields: Sample tagging enabled, {len(tag_mappings)} tag mappings")
                
                for i, tag_mapping in enumerate(tag_mappings):
                    field_name = tag_mapping.get("fieldName")
                    field_type = tag_mapping.get("fieldType", "string")
                    
                    print(f"🔍 _define_dataset_fields: Tag mapping {i+1}: {field_name} ({field_type})")
                    
                    if field_name:
                        # Define the field in the dataset schema
                        if field_type == "bool":
                            dataset.add_sample_field(field_name, fo.BooleanField)
                        elif field_type == "int":
                            dataset.add_sample_field(field_name, fo.IntField)
                        elif field_type == "float":
                            dataset.add_sample_field(field_name, fo.FloatField)
                        else:  # string
                            dataset.add_sample_field(field_name, fo.StringField)
                        
                        print(f"🔍 _define_dataset_fields: Added field '{field_name}' of type '{field_type}'")
                    else:
                        print(f"🔍 _define_dataset_fields: Skipping tag mapping {i+1} - no field name")
            else:
                print(f"🔍 _define_dataset_fields: Sample tagging disabled")
            
            # Define fields for field mapping
            if mapping_config.get("enableFieldMapping", False):
                field_mappings = mapping_config.get("fieldMappings", [])
                for field_mapping in field_mappings:
                    field_name = field_mapping.get("fieldName")
                    field_type = field_mapping.get("fieldType", "string")
                    
                    if field_name:
                        # Define the field in the dataset schema
                        if field_type == "bool":
                            dataset.add_sample_field(field_name, fo.BooleanField)
                        elif field_type == "int":
                            dataset.add_sample_field(field_name, fo.IntField)
                        elif field_type == "float":
                            dataset.add_sample_field(field_name, fo.FloatField)
                        else:  # string
                            dataset.add_sample_field(field_name, fo.StringField)
                        
                        print(f"🔍 _define_dataset_fields: Added field '{field_name}' of type '{field_type}'")
            
            # Define metadata field if enabled
            if mapping_config.get("includeAllTagsAsMetadata", False):
                metadata_field = mapping_config.get("metadataFieldName", "osm_metadata")
                dataset.add_sample_field(metadata_field, fo.ListField)
                print(f"🔍 _define_dataset_fields: Added metadata field '{metadata_field}' as ListField")
            
            # Define detection field if 3D detections are enabled
            if mapping_config.get("enable3DDetections", False):
                detection_field = mapping_config.get("detectionFieldName", "detections")
                dataset.add_sample_field(detection_field, fo.ListField)
                print(f"🔍 _define_dataset_fields: Added detection field '{detection_field}'")
                
        except Exception as e:
            print(f"🔍 _define_dataset_fields: Error defining fields: {e}")

    def _extract_coordinates(self, geo_location) -> tuple:
        """Extract longitude and latitude from various geo location formats."""
        try:
            if hasattr(geo_location, 'point') and geo_location.point is not None:
                # FiftyOne GeoLocation object with point
                point = geo_location.point
                if hasattr(point, 'coordinates'):
                    # Point geometry
                    return point.coordinates
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    # [lon, lat] format
                    return point[0], point[1]
            elif hasattr(geo_location, 'coordinates'):
                # Point geometry
                return geo_location.coordinates
            elif isinstance(geo_location, (list, tuple)) and len(geo_location) >= 2:
                # [lon, lat] or [lat, lon] format
                if len(geo_location) == 2:
                    # Assume [lon, lat] format
                    return geo_location[0], geo_location[1]
            
            return None, None
        except Exception as e:
            print(f"🔍 _extract_coordinates: Error extracting coordinates: {e}")
            return None, None

    def _find_cell_for_location(self, lon: float, lat: float, grid_cells: list) -> str:
        """Find which grid cell contains the given location."""
        print(f"🔍 _find_cell_for_location: Looking for cell containing lon={lon}, lat={lat}")
        print(f"🔍 _find_cell_for_location: Checking {len(grid_cells)} grid cells")
        
        for i, cell in enumerate(grid_cells):
            cell_id = cell.get("id", f"cell_{i}")
            bbox = cell.get("bbox")
            print(f"🔍 _find_cell_for_location: Cell {cell_id} bbox: {bbox}")
            
            if bbox and len(bbox) == 4:
                min_lon, min_lat, max_lon, max_lat = bbox
                print(f"🔍 _find_cell_for_location: Cell {cell_id} bounds: min_lon={min_lon}, min_lat={min_lat}, max_lon={max_lon}, max_lat={max_lat}")
                print(f"🔍 _find_cell_for_location: Checking if {lon} in [{min_lon}, {max_lon}] and {lat} in [{min_lat}, {max_lat}]")
                
                if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                    print(f"🔍 _find_cell_for_location: Found match in cell {cell_id}")
                    return cell["id"]
                else:
                    print(f"🔍 _find_cell_for_location: No match in cell {cell_id}")
            else:
                print(f"🔍 _find_cell_for_location: Cell {cell_id} has invalid bbox: {bbox}")
        
        print(f"🔍 _find_cell_for_location: No cell found for lon={lon}, lat={lat}")
        return None

    def _apply_mapping_to_sample(self, sample, osm_data: list, mapping_config: dict, lon: float, lat: float):
        """Apply the mapping configuration to a sample using nearby OSM data."""
        try:
            print(f"🔍 _apply_mapping_to_sample: Applying mappings to sample {sample.id}")
            print(f"🔍 _apply_mapping_to_sample: OSM data count: {len(osm_data)}")
            print(f"🔍 _apply_mapping_to_sample: Mapping config enabled features:")
            print(f"  - 3D Detections: {mapping_config.get('enable3DDetections', False)}")
            print(f"  - Sample Tagging: {mapping_config.get('enableSampleTagging', False)}")
            print(f"  - Field Mapping: {mapping_config.get('enableFieldMapping', False)}")
            print(f"  - Metadata: {mapping_config.get('includeAllTagsAsMetadata', False)}")
            
            # 3D Detections
            if mapping_config.get("enable3DDetections", False):
                print(f"🔍 _apply_mapping_to_sample: Applying 3D detections to sample {sample.id}")
                self._apply_3d_detections(sample, osm_data, mapping_config, lon, lat)
            
            # Sample Tagging
            if mapping_config.get("enableSampleTagging", False):
                print(f"🔍 _apply_mapping_to_sample: Applying sample tagging to sample {sample.id}")
                self._apply_sample_tagging(sample, osm_data, mapping_config, lon, lat)
            
            # Field Mapping
            if mapping_config.get("enableFieldMapping", False):
                print(f"🔍 _apply_mapping_to_sample: Applying field mapping to sample {sample.id}")
                self._apply_field_mapping(sample, osm_data, mapping_config, lon, lat)
            
            # Metadata
            if mapping_config.get("includeAllTagsAsMetadata", False):
                print(f"🔍 _apply_mapping_to_sample: Applying metadata to sample {sample.id}")
                self._apply_metadata(sample, osm_data, mapping_config, lon, lat)
                
        except Exception as e:
            print(f"🔍 _apply_mapping_to_sample: Error applying mappings to sample {sample.id}: {e}")
            import traceback
            traceback.print_exc()

    def _apply_3d_detections(self, sample, osm_data: list, mapping_config: dict, lon: float, lat: float):
        """Apply 3D detections mapping."""
        detection_field = mapping_config.get("detectionFieldName", "detections")
        label_tag = mapping_config.get("detectionLabelTag", "type")
        radius = mapping_config.get("detectionRadius", 100)
        
        # Find nearby OSM features
        nearby_features = self._find_nearby_features(osm_data, lon, lat, radius)
        
        detections = []
        for feature in nearby_features:
            if "tags" in feature and label_tag in feature["tags"]:
                label = feature["tags"][label_tag]
                # Create a detection object (simplified)
                detection = {
                    "label": label,
                    "location": [lon, lat],  # Simplified location
                    "confidence": 1.0,
                    "osm_id": feature.get("id"),
                    "osm_type": feature.get("type")
                }
                detections.append(detection)
        
        if detections:
            sample[detection_field] = detections
            sample.save()

    def _apply_sample_tagging(self, sample, osm_data: list, mapping_config: dict, lon: float, lat: float):
        """Apply sample tagging mapping."""
        tag_slice = mapping_config.get("tagSlice", "default")
        radius = mapping_config.get("tagRadius", 100)
        tag_mappings = mapping_config.get("tagMappings", [])
        
        print(f"🔍 _apply_sample_tagging: Sample {sample.id}, tag_mappings: {len(tag_mappings)}")
        
        if not tag_mappings:
            print(f"🔍 _apply_sample_tagging: No tag mappings configured")
            return
        
        # Find nearby OSM features
        nearby_features = self._find_nearby_features(osm_data, lon, lat, radius)
        print(f"🔍 _apply_sample_tagging: Found {len(nearby_features)} nearby features within {radius}m")
        
        # Apply each tag mapping
        for i, tag_mapping in enumerate(tag_mappings):
            osm_key = tag_mapping.get("osmKey")
            field_name = tag_mapping.get("fieldName")
            field_type = tag_mapping.get("fieldType", "string")
            
            print(f"🔍 _apply_sample_tagging: Mapping {i+1}: {osm_key} -> {field_name} ({field_type})")
            
            if not osm_key or not field_name:
                print(f"🔍 _apply_sample_tagging: Skipping mapping {i+1} - missing osm_key or field_name")
                continue
            
            # Find the best matching feature for this tag
            best_value = None
            for feature in nearby_features:
                if "tags" in feature and osm_key in feature["tags"]:
                    best_value = feature["tags"][osm_key]
                    print(f"🔍 _apply_sample_tagging: Found value '{best_value}' for key '{osm_key}'")
                    break
            
            if best_value is not None:
                # Convert value based on field type
                converted_value = self._convert_value(best_value, field_type, tag_mapping)
                print(f"🔍 _apply_sample_tagging: Setting {field_name} = {converted_value} (type: {type(converted_value)})")
                sample[field_name] = converted_value
            else:
                print(f"🔍 _apply_sample_tagging: No value found for key '{osm_key}'")
        
        print(f"🔍 _apply_sample_tagging: Saving sample {sample.id}")
        sample.save()

    def _apply_field_mapping(self, sample, osm_data: list, mapping_config: dict, lon: float, lat: float):
        """Apply field mapping."""
        field_mappings = mapping_config.get("fieldMappings", [])
        
        print(f"🔍 _apply_field_mapping: Sample {sample.id}, field_mappings: {len(field_mappings)}")
        
        if not field_mappings:
            print(f"🔍 _apply_field_mapping: No field mappings configured")
            return
        
        # Find nearby OSM features
        nearby_features = self._find_nearby_features(osm_data, lon, lat, 100)  # Default radius
        print(f"🔍 _apply_field_mapping: Found {len(nearby_features)} nearby features within 100m")
        
        # Apply each field mapping
        for i, field_mapping in enumerate(field_mappings):
            osm_key = field_mapping.get("osmKey")
            field_name = field_mapping.get("fieldName")
            field_type = field_mapping.get("fieldType", "string")
            
            print(f"🔍 _apply_field_mapping: Mapping {i+1}: {osm_key} -> {field_name} ({field_type})")
            
            if not osm_key or not field_name:
                print(f"🔍 _apply_field_mapping: Skipping mapping {i+1} - missing osm_key or field_name")
                continue
            
            # Find the best matching feature for this tag
            best_value = None
            for feature in nearby_features:
                if "tags" in feature and osm_key in feature["tags"]:
                    best_value = feature["tags"][osm_key]
                    print(f"🔍 _apply_field_mapping: Found value '{best_value}' for key '{osm_key}'")
                    break
            
            if best_value is not None:
                # Convert value based on field type
                converted_value = self._convert_value(best_value, field_type, field_mapping)
                print(f"🔍 _apply_field_mapping: Setting {field_name} = {converted_value} (type: {type(converted_value)})")
                sample[field_name] = converted_value
            else:
                print(f"🔍 _apply_field_mapping: No value found for key '{osm_key}'")
        
        print(f"🔍 _apply_field_mapping: Saving sample {sample.id}")
        sample.save()

    def _apply_metadata(self, sample, osm_data: list, mapping_config: dict, lon: float, lat: float):
        """Apply metadata mapping - store ALL OSM features from the cell as metadata."""
        metadata_field = mapping_config.get("metadataFieldName", "osm_metadata")
        
        print(f"🔍 _apply_metadata: Sample {sample.id}, metadata_field: {metadata_field}")
        print(f"🔍 _apply_metadata: OSM data count: {len(osm_data)}")
        
        # For metadata, we want ALL OSM features from the entire cell, not just nearby ones
        # Store the entire osm_data as metadata
        if osm_data:
            print(f"🔍 _apply_metadata: Storing {len(osm_data)} OSM features as metadata for sample {sample.id}")
            sample[metadata_field] = osm_data
            print(f"🔍 _apply_metadata: Saving sample {sample.id}")
            sample.save()
            print(f"🔍 _apply_metadata: Successfully stored metadata for sample {sample.id}")
        else:
            print(f"🔍 _apply_metadata: No OSM data to store for sample {sample.id}")

    def _find_nearby_features(self, osm_data: list, lon: float, lat: float, radius: float) -> list:
        """Find OSM features within the specified radius of the location."""
        nearby_features = []
        
        for feature in osm_data:
            feature_lon, feature_lat = self._get_feature_location(feature)
            if feature_lon is not None and feature_lat is not None:
                # Calculate distance (simplified - assumes small distances)
                distance = ((lon - feature_lon) ** 2 + (lat - feature_lat) ** 2) ** 0.5
                # Convert to meters (rough approximation)
                distance_meters = distance * 111000  # Rough conversion
                
                if distance_meters <= radius:
                    nearby_features.append(feature)
        
        return nearby_features

    def _get_feature_location(self, feature: dict) -> tuple:
        """Extract longitude and latitude from an OSM feature."""
        if "lat" in feature and "lon" in feature:
            return feature["lon"], feature["lat"]
        elif "geometry" in feature:
            geometry = feature["geometry"]
            if geometry.get("type") == "Point" and "coordinates" in geometry:
                coords = geometry["coordinates"]
                if len(coords) >= 2:
                    return coords[0], coords[1]  # [lon, lat]
        return None, None

    def _convert_value(self, value: str, field_type: str, mapping_config: dict):
        """Convert a string value to the specified field type."""
        print(f"🔍 _convert_value: Converting '{value}' to type '{field_type}'")
        
        if field_type == "string":
            result = str(value)
            print(f"🔍 _convert_value: String conversion: '{value}' -> '{result}'")
            return result
        elif field_type == "int":
            try:
                result = int(float(value))
                print(f"🔍 _convert_value: Int conversion: '{value}' -> {result}")
                return result
            except (ValueError, TypeError) as e:
                print(f"🔍 _convert_value: Int conversion failed for '{value}': {e}, returning 0")
                return 0
        elif field_type == "float":
            try:
                result = float(value)
                print(f"🔍 _convert_value: Float conversion: '{value}' -> {result}")
                return result
            except (ValueError, TypeError) as e:
                print(f"🔍 _convert_value: Float conversion failed for '{value}': {e}, returning 0.0")
                return 0.0
        elif field_type == "bool":
            bool_true = mapping_config.get("boolTrueValue", "yes")
            bool_false = mapping_config.get("boolFalseValue", "no")
            print(f"🔍 _convert_value: Bool conversion - true='{bool_true}', false='{bool_false}'")
            
            if str(value).lower() == str(bool_true).lower():
                print(f"🔍 _convert_value: Bool conversion: '{value}' -> True (matches true value)")
                return True
            elif str(value).lower() == str(bool_false).lower():
                print(f"🔍 _convert_value: Bool conversion: '{value}' -> False (matches false value)")
                return False
            else:
                result = bool(value)  # Fallback
                print(f"🔍 _convert_value: Bool conversion: '{value}' -> {result} (fallback)")
                return result
        else:
            result = str(value)
            print(f"🔍 _convert_value: Unknown type '{field_type}', returning as string: '{result}'")
            return result

    def _update_enrichment_progress(self, ctx: ExecutionContext, processed: int, total: int):
        """Update the enrichment progress in the store."""
        enrichment_job = ctx.store("metageo").get("enrichment_job")
        if enrichment_job:
            enrichment_job["processed_samples"] = processed
            enrichment_job["total_samples"] = total
            enrichment_job["progress_percent"] = (processed / total) * 100 if total > 0 else 0
            ctx.store("metageo").set("enrichment_job", enrichment_job)

    def get_enrichment_status(self, ctx: ExecutionContext) -> dict[str, any]:
        """Get the status of the enrichment process."""
        try:
            enrichment_job = ctx.store("metageo").get("enrichment_job")
            if not enrichment_job:
                return {
                    "status": "success",
                    "enrichment_status": "not_started",
                    "message": "No enrichment job found",
                }
            
            return {
                "status": "success",
                "enrichment_status": enrichment_job.get("status", "unknown"),
                "job_info": enrichment_job,
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting enrichment status: {str(e)}",
            }

    def get_field_mappings(self, ctx: ExecutionContext) -> dict[str, any]:
        """Get current field mappings for validation"""
        try:
            # Get current mapping configuration from the store
            mapping_config = ctx.store("metageo").get("mapping_config")
            if not mapping_config:
                return {
                    "status": "success",
                    "field_mappings": [],
                    "used_field_names": [],
                }
            
            field_mappings = mapping_config.get("fieldMappings", [])
            used_field_names = [mapping.get("fieldName") for mapping in field_mappings if mapping.get("fieldName")]
            
            return {
                "status": "success",
                "field_mappings": field_mappings,
                "used_field_names": used_field_names,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving field mappings: {str(e)}",
                "field_mappings": [],
                "used_field_names": [],
            }

    def save_mapping_config(self, ctx: ExecutionContext) -> dict[str, any]:
        """Save the mapping configuration to the execution store."""
        try:
            mapping_config = ctx.params.get("mapping_config")
            if not mapping_config:
                return {
                    "status": "error",
                    "message": "No mapping configuration provided",
                }
            
            # Save to execution store
            ctx.store("metageo").set("mapping_config", mapping_config)
            
            return {
                "status": "success",
                "message": "Mapping configuration saved successfully",
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error saving mapping configuration: {str(e)}",
            }

    def get_mapping_config(self, ctx: ExecutionContext) -> dict[str, any]:
        """Get the mapping configuration from the execution store."""
        try:
            mapping_config = ctx.store("metageo").get("mapping_config")
            
            return {
                "status": "success",
                "mapping_config": mapping_config,
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting mapping configuration: {str(e)}",
            }

    def clear_mapping_config(self, ctx: ExecutionContext) -> dict[str, any]:
        """Clear the mapping configuration from the execution store."""
        try:
            # Remove mapping configuration from store
            ctx.store("metageo").delete("mapping_config")
            
            return {
                "status": "success",
                "message": "Mapping configuration cleared successfully",
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error clearing mapping configuration: {str(e)}",
            }

    def clear_enrichment_data(self, ctx: ExecutionContext) -> dict[str, any]:
        """Clear enrichment data from samples while keeping the mapping configuration."""
        try:
            # Get the mapping configuration to know which fields to clear
            mapping_config = ctx.store("metageo").get("mapping_config")
            if not mapping_config:
                return {
                    "status": "error",
                    "message": "No mapping configuration found. Nothing to clear.",
                }
            
            # Get the dataset
            dataset = ctx.dataset
            if not dataset:
                return {
                    "status": "error",
                    "message": "No dataset found in context.",
                }
            
            print(f"🔍 clear_enrichment_data: Starting to clear enrichment data from {len(dataset)} samples")
            
            # Collect all field names that need to be cleared
            fields_to_clear = set()
            
            # Sample tagging fields
            if mapping_config.get("enableSampleTagging", False):
                tag_mappings = mapping_config.get("tagMappings", [])
                for tag_mapping in tag_mappings:
                    field_name = tag_mapping.get("fieldName")
                    if field_name:
                        fields_to_clear.add(field_name)
                        print(f"🔍 clear_enrichment_data: Will clear sample tagging field: {field_name}")
            
            # Field mapping fields
            if mapping_config.get("enableFieldMapping", False):
                field_mappings = mapping_config.get("fieldMappings", [])
                for field_mapping in field_mappings:
                    field_name = field_mapping.get("fieldName")
                    if field_name:
                        fields_to_clear.add(field_name)
                        print(f"🔍 clear_enrichment_data: Will clear field mapping field: {field_name}")
            
            # Metadata field
            if mapping_config.get("includeAllTagsAsMetadata", False):
                metadata_field = mapping_config.get("metadataFieldName", "osm_metadata")
                fields_to_clear.add(metadata_field)
                print(f"🔍 clear_enrichment_data: Will clear metadata field: {metadata_field}")
            
            # Detection field
            if mapping_config.get("enable3DDetections", False):
                detection_field = mapping_config.get("detectionFieldName", "detections")
                fields_to_clear.add(detection_field)
                print(f"🔍 clear_enrichment_data: Will clear detection field: {detection_field}")
            
            print(f"🔍 clear_enrichment_data: Total fields to clear: {len(fields_to_clear)}")
            
            # Delete the fields from the dataset schema
            deleted_fields = []
            for field_name in fields_to_clear:
                try:
                    # Check if the field exists in the dataset schema
                    if field_name in dataset.get_field_schema():
                        # Delete the field from the dataset schema
                        dataset.delete_sample_field(field_name)
                        deleted_fields.append(field_name)
                        print(f"🔍 clear_enrichment_data: Deleted field '{field_name}' from dataset schema")
                    else:
                        print(f"🔍 clear_enrichment_data: Field '{field_name}' not found in dataset schema")
                except Exception as e:
                    print(f"🔍 clear_enrichment_data: Error deleting field '{field_name}': {e}")
            
            print(f"🔍 clear_enrichment_data: Successfully deleted {len(deleted_fields)} fields from dataset schema")
            
            return {
                "status": "success",
                "message": f"Enrichment fields deleted successfully from dataset schema",
                "deleted_fields": deleted_fields,
                "total_fields_attempted": len(fields_to_clear),
                "total_samples": len(dataset),
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error clearing enrichment data: {str(e)}",
            }

    def get_cell_data(self, ctx: ExecutionContext) -> dict[str, any]:
        """Get detailed data for a specific grid cell."""
        cell_id = ctx.params.get("cell_id")
        if not cell_id:
            return {
                "status": "error",
                "message": "cell_id parameter is required",
            }

        try:
            store = ctx.store("metageo")
            
            # Get cell status
            status = store.get(f"cell_{cell_id}_status")
            error = store.get(f"cell_{cell_id}_error")
            osm_features = store.get(f"cell_{cell_id}_osm_features")
            osm_data = store.get(f"cell_{cell_id}_osm_data")
            
            # Get cell coordinates from indexing state
            indexing_state = store.get("indexing_state")
            cell_info = None
            if indexing_state and indexing_state.get("grid_cells"):
                cell_info = next(
                    (cell for cell in indexing_state["grid_cells"] if cell["id"] == cell_id),
                    None
                )
            
            return {
                "status": "success",
                "cell_id": cell_id,
                "cell_status": status,
                "error": error,
                "osm_features_count": osm_features,
                "osm_data": osm_data or [],
                "cell_info": cell_info,
                "coordinates": cell_info.get("coordinates") if cell_info else None,
                "sample_count": cell_info.get("sample_count", 0) if cell_info else 0,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving cell data: {str(e)}",
            }

    def on_unload(self, ctx: ExecutionContext) -> None:
        pass

    def define_area_auto(self, ctx: ExecutionContext) -> Dict[str, Any]:
        geo_field = ctx.params.get("geo_field")
        if not geo_field:
            raise ValueError("'geo_field' is required")

        # Get real coordinates from the dataset
        coords = []
        try:
            coords = ctx.view.values(geo_field)
        except:
            try:
                coords = ctx.view.values(f"{geo_field}.coordinates")
            except:
                try:
                    coords = ctx.view.values(f"{geo_field}.point")
                except:
                    try:
                        coords = ctx.view.values(f"{geo_field}.location")
                    except:
                        raise ValueError(
                            f"Could not access coordinates from field '{geo_field}'"
                        )

        # Extract coordinates from various formats
        lons, lats = [], []
        for c in coords:
            if c is None:
                continue
            if isinstance(c, (list, tuple)) and len(c) == 2:
                lons.append(float(c[0]))
                lats.append(float(c[1]))
            elif (
                hasattr(c, "coordinates")
                and isinstance(c.coordinates, (list, tuple))
                and len(c.coordinates) == 2
            ):
                lons.append(float(c.coordinates[0]))
                lats.append(float(c.coordinates[1]))
            elif (
                hasattr(c, "point")
                and isinstance(c.point, (list, tuple))
                and len(c.point) == 2
            ):
                lons.append(float(c.point[0]))
                lats.append(float(c.point[1]))

        if not lons:
            raise ValueError(
                f"No coordinates found for field '{geo_field}' in current view"
            )

        # Calculate real bounding box from actual data
        bbox: BBox = (min(lons), min(lats), max(lons), max(lats))
        sample_count = len(lons)

        print(f"Real dataset analysis:")
        print(f"  - Field: {geo_field}")
        print(f"  - Samples: {sample_count}")
        print(f"  - Bounding box: {bbox}")
        print(
            f"  - Coverage: {bbox[2] - bbox[0]:.4f}° lon × {bbox[3] - bbox[1]:.4f}° lat"
        )

        return {"bbox": bbox, "sample_count": sample_count}

    def explore_tags(self, ctx: ExecutionContext) -> Dict[str, Any]:
        bbox = ctx.params.get("bbox")
        if not bbox:
            raise ValueError("'bbox' is required")

        # Mock OSM API call - simulate real OSM data exploration
        print(f"Mock OSM API: Exploring tags in bbox {bbox}")

        # Calculate area to determine realistic tag counts
        area_km2 = (
            (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) * 111 * 111
        )  # Rough km² calculation
        density_factor = min(area_km2 / 100, 10)  # Scale with area, cap at 10x

        # Simulate realistic OSM tag distribution based on area
        keys = [
            {
                "key": "highway",
                "count": int(500 * density_factor),
                "sampleValues": [
                    "residential",
                    "primary",
                    "service",
                    "motorway",
                    "trunk",
                    "secondary",
                    "tertiary",
                ],
            },
            {
                "key": "amenity",
                "count": int(200 * density_factor),
                "sampleValues": [
                    "fuel",
                    "cafe",
                    "parking",
                    "restaurant",
                    "school",
                    "hospital",
                    "bank",
                    "post_office",
                ],
            },
            {
                "key": "building",
                "count": int(1000 * density_factor),
                "sampleValues": [
                    "residential",
                    "commercial",
                    "industrial",
                    "school",
                    "house",
                    "apartments",
                ],
            },
            {
                "key": "landuse",
                "count": int(150 * density_factor),
                "sampleValues": [
                    "residential",
                    "commercial",
                    "industrial",
                    "agricultural",
                    "forest",
                    "park",
                ],
            },
            {
                "key": "natural",
                "count": int(80 * density_factor),
                "sampleValues": [
                    "water",
                    "wood",
                    "grassland",
                    "beach",
                    "tree",
                    "scrub",
                ],
            },
            {
                "key": "leisure",
                "count": int(60 * density_factor),
                "sampleValues": [
                    "park",
                    "playground",
                    "sports_centre",
                    "swimming_pool",
                    "garden",
                ],
            },
            {
                "key": "shop",
                "count": int(120 * density_factor),
                "sampleValues": [
                    "supermarket",
                    "convenience",
                    "bakery",
                    "pharmacy",
                    "clothes",
                    "electronics",
                ],
            },
            {
                "key": "tourism",
                "count": int(40 * density_factor),
                "sampleValues": [
                    "hotel",
                    "museum",
                    "attraction",
                    "viewpoint",
                    "information",
                ],
            },
        ]

        print(
            f"Mock OSM API: Found {sum(k['count'] for k in keys)} total features across {len(keys)} tag types"
        )
        return {"keys": keys}

    def start_indexing(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Start indexing OSM data for the defined geographic area"""
        bbox = ctx.params.get("bbox")
        grid_tiles = ctx.params.get("grid_tiles", 10)
        geo_field = ctx.params.get("geo_field")
        execution_mode = ctx.params.get("execution_mode", "immediate")

        if not bbox:
            raise ValueError("'bbox' is required")
        if not geo_field:
            raise ValueError("'geo_field' is required")

        # Test OSM client availability
        test_client = OSMClient()
        if not test_client.api:
            raise RuntimeError(
                "OSM API client not available. Please install 'overpy' package."
            )

        # Get existing indexing state from store (should be populated by calculate distribution)
        existing_state = ctx.store("metageo").get("indexing_state")
        print(
            f"start_indexing: Retrieved existing state: {existing_state is not None}"
        )
        if existing_state:
            print(
                f"start_indexing: Existing state keys: {list(existing_state.keys())}"
            )
            print(
                f"start_indexing: Has grid_cells: {existing_state.get('grid_cells') is not None}"
            )
            print(
                f"start_indexing: Grid cells count: {len(existing_state.get('grid_cells', []))}"
            )

        if not existing_state or not existing_state.get("grid_cells"):
            raise RuntimeError(
                "No grid found. Please calculate sample distribution first."
            )

        grid_cells = existing_state["grid_cells"]
        active_cells = existing_state["active_cells"]
        total_cells = existing_state["total_cells"]

        print(f"Starting indexing with existing grid:")
        print(f"  - Total cells: {total_cells}")
        print(f"  - Active cells: {active_cells}")

        # Generate unique indexing ID
        indexing_id = f"indexing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Update indexing state
        indexing_state = {
            **existing_state,
            "indexing_id": indexing_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "execution_mode": execution_mode,
        }

        # Store updated state
        ctx.store("metageo").set("indexing_state", indexing_state)

        # Launch the index grid operator to process all cells
        print("Starting indexing with grid operator...")
        print(f"Total grid cells: {len(grid_cells)}")
        print(f"Active cells (with samples): {active_cells}")

        # Launch the index grid operator
        print(
            f"start_indexing: Launching index grid operator with params: indexing_id={indexing_id}"
        )

        try:
            # Launch the index grid operator to process all cells
            ctx.trigger(
                "@voxel51/metageo/index_grid", {"indexing_id": indexing_id}
            )
            print("start_indexing: Successfully triggered index grid operator")

            # Launch the watch operator to monitor progress
            ctx.trigger(
                "@voxel51/metageo/watch_indexing",
                {
                    "indexing_id": indexing_id,
                    "total_cells": total_cells,
                    "active_cells": active_cells,
                },
            )
            print("start_indexing: Successfully triggered watch operator")
        except Exception as e:
            print(f"start_indexing: Error triggering operators: {e}")
            raise

        return {
            "status": "started",
            "execution_mode": "immediate",
            "indexing_id": indexing_id,
            "total_cells": total_cells,
            "active_cells": active_cells,
            "message": f"Started indexing with watch operator monitoring {active_cells} active cells.",
        }

    def get_sample_distribution(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Get sample distribution across grid cells without starting indexing"""
        bbox = ctx.params.get("bbox")
        grid_tiles = ctx.params.get("grid_tiles", 10)
        geo_field = ctx.params.get("geo_field")

        if not bbox:
            raise ValueError("'bbox' is required")
        if not geo_field:
            raise ValueError("'geo_field' is required")

        # Calculate sample distribution
        sample_distribution = self._calculate_sample_distribution(
            ctx, geo_field, bbox, grid_tiles
        )

        # Generate grid cells with sample counts
        min_lon, min_lat, max_lon, max_lat = bbox
        lon_step = (max_lon - min_lon) / grid_tiles
        lat_step = (max_lat - min_lat) / grid_tiles

        grid_cells = []
        total_samples = 0
        active_cells = 0

        for row in range(grid_tiles):
            for col in range(grid_tiles):
                cell_id = f"{row}_{col}"
                cell_min_lon = min_lon + (col * lon_step)
                cell_max_lon = cell_min_lon + lon_step
                cell_min_lat = min_lat + (row * lat_step)
                cell_max_lat = cell_min_lat + lat_step

                sample_count = sample_distribution.get(cell_id, 0)
                total_samples += sample_count
                if sample_count > 0:
                    active_cells += 1

                cell_data = {
                    "id": cell_id,
                    "coordinates": [
                        cell_min_lon,
                        cell_min_lat,
                        cell_max_lon,
                        cell_max_lat,
                    ],
                    "sample_count": sample_count,
                    "status": "idle" if sample_count > 0 else "empty",
                    "progress": 0,
                    "error": None,
                }
                grid_cells.append(cell_data)
                print(f"get_sample_distribution: Created cell {cell_id} with sample_count: {sample_count} (type: {type(sample_count)})")

        # Store the grid in the execution store for later use by start_indexing
        indexing_state = {
            "grid_cells": grid_cells,
            "total_cells": len(grid_cells),
            "active_cells": active_cells,
            "total_samples": total_samples,
            "sample_distribution": sample_distribution,
            "status": "idle",
            "execution_mode": "immediate",
            # Store essential configuration for persistence
            "bbox": bbox,
            "geo_field": geo_field,
            "grid_tiles": grid_tiles,
        }

        # Store in dataset-linked store for MongoDB persistence
        ctx.store("metageo").set("indexing_state", indexing_state)

        print(f"Sample distribution calculated and stored:")
        print(f"  - Total cells: {len(grid_cells)}")
        print(f"  - Active cells: {active_cells}")
        print(f"  - Total samples: {total_samples}")

        return {
            "grid_cells": grid_cells,
            "total_cells": len(grid_cells),
            "active_cells": active_cells,
            "total_samples": total_samples,
            "sample_distribution": sample_distribution,
        }

    def get_indexing_status(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Get current indexing status and progress"""
        indexing_state = ctx.panel.get_state("metageo_indexing_state")
        if not indexing_state:
            return {
                "status": "not_started",
                "message": "No indexing operation found",
            }

        return {
            "status": indexing_state["status"],
            "total_cells": indexing_state["total_cells"],
            "active_cells": indexing_state["active_cells"],
            "completed_cells": indexing_state["completed_cells"],
            "failed_cells": indexing_state["failed_cells"],
            "execution_mode": indexing_state["execution_mode"],
            "start_time": indexing_state["start_time"],
            "total_samples": indexing_state.get("total_samples", 0),
            "grid_cells": indexing_state["grid_cells"],
        }

    def get_indexing_state(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Get the current indexing state from dataset-linked store"""
        indexing_state = ctx.store("metageo").get("indexing_state")
        if not indexing_state:
            return {
                "status": "not_found",
                "message": "No indexing state found",
            }

        return {"status": "found", "indexing_state": indexing_state}

    def cancel_indexing(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Cancel the current indexing operation"""
        try:
            indexing_state = ctx.store("metageo").get("indexing_state")
            if not indexing_state:
                return {
                    "status": "not_found",
                    "message": "No indexing operation to cancel",
                }

            # Set cancellation flag in the store so operators can check it
            indexing_state["status"] = "cancelled"
            indexing_state["cancelled_at"] = datetime.now().isoformat()
            
            # Clear all cell statuses to reset the grid
            grid_cells = indexing_state.get("grid_cells", [])
            for cell in grid_cells:
                cell_id = cell["id"]
                ctx.store("metageo").delete(f"cell_{cell_id}_status")
                ctx.store("metageo").delete(f"cell_{cell_id}_error")
                ctx.store("metageo").delete(f"cell_{cell_id}_osm_features")
                ctx.store("metageo").delete(f"cell_{cell_id}_osm_data")
            
            # Clear the grid cells array to reset the grid
            indexing_state["grid_cells"] = []
            indexing_state["completed_cells"] = 0
            indexing_state["failed_cells"] = 0
            indexing_state["rate_limited_cells"] = 0
            indexing_state["total_cells"] = 0
            indexing_state["progress"] = 0
            
            # Save the updated state
            ctx.store("metageo").set("indexing_state", indexing_state)

            print("Indexing operation cancelled - all cell data cleared")
            return {
                "status": "cancelled",
                "message": "Indexing operation cancelled and grid reset",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error cancelling indexing: {str(e)}",
            }

    def debug_state(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Debug method to check current state"""
        indexing_state = ctx.store("metageo").get("indexing_state")
        return {
            "status": "debug",
            "indexing_state": indexing_state,
            "has_state": indexing_state is not None,
        }

    def get_cell_statuses(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Get status of all cells from execution store"""
        indexing_state = ctx.store("metageo").get("indexing_state")
        if not indexing_state:
            return {
                "status": "not_found",
                "message": "No indexing state found",
            }

        grid_cells = indexing_state.get("grid_cells", [])
        cell_statuses = []

        for cell in grid_cells:
            cell_id = cell["id"]
            status = ctx.store("metageo").get(f"cell_{cell_id}_status")
            error = ctx.store("metageo").get(f"cell_{cell_id}_error")
            osm_features = ctx.store("metageo").get(
                f"cell_{cell_id}_osm_features"
            )

            cell_statuses.append(
                {
                    "id": cell_id,
                    "status": status or "pending",
                    "error": error,
                    "osm_features": osm_features,
                    "sample_count": cell.get("sample_count", 0),
                    "coordinates": cell.get("coordinates"),
                }
            )

        return {
            "status": "found",
            "cell_statuses": cell_statuses,
            "indexing_state": indexing_state,
        }

    def get_current_indexing_state(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Get current indexing state regardless of completion status"""
        print(f"🔍 get_current_indexing_state: Checking store...")
        
        # Debug: List all keys in the store
        store = ctx.store("metageo")
        all_keys = []
        try:
            # Try to get all keys (this might not work in all versions)
            for key in store.list_keys():
                all_keys.append(key)
        except:
            # Fallback: try to get common keys
            common_keys = ["indexing_state", "grid_cells", "bbox", "geo_field"]
            for key in common_keys:
                if store.get(key) is not None:
                    all_keys.append(key)
        
        print(f"🔍 get_current_indexing_state: Store keys: {all_keys}")
        
        # Debug: Try to get each key individually to see what's actually stored
        for key in all_keys:
            value = store.get(key)
            print(f"🔍 get_current_indexing_state: Key '{key}' = {type(value).__name__}: {str(value)[:200]}...")
        
        # Try to get indexing state - it might be stored in different ways
        indexing_state = store.get("indexing_state")
        print(f"🔍 get_current_indexing_state: indexing_state: {indexing_state}")
        
        # If no indexing_state, check if we have individual pieces
        if not indexing_state:
            # Check for old-style data structure
            bbox = store.get("bbox")
            grid_cells = store.get("grid_cells")
            geo_field = store.get("geo_field")
            
            print(f"🔍 get_current_indexing_state: Old structure check - bbox: {bbox}, grid_cells: {grid_cells}, geo_field: {geo_field}")
            
            if bbox and grid_cells and geo_field:
                # We have old-style data, create a compatible structure
                print(f"🔍 get_current_indexing_state: Found old-style data, creating compatible structure")
                indexing_state = {
                    "bbox": bbox,
                    "grid_cells": grid_cells,
                    "geo_field": geo_field,
                    "status": "completed",  # Assume completed if we have this data
                    "total_cells": len(grid_cells) if grid_cells else 0,
                    "active_cells": len([c for c in grid_cells if c.get("sample_count", 0) > 0]) if grid_cells else 0,
                    "completed_cells": len([c for c in grid_cells if c.get("status") == "completed"]) if grid_cells else 0,
                    "failed_cells": len([c for c in grid_cells if c.get("status") == "failed"]) if grid_cells else 0,
                    "rate_limited_cells": len([c for c in grid_cells if c.get("status") == "rate_limited"]) if grid_cells else 0,
                    "total_features": sum([c.get("osm_features", 0) for c in grid_cells if c.get("osm_features")]) if grid_cells else 0,
                    "progress": 100 if grid_cells else 0,
                }
                print(f"🔍 get_current_indexing_state: Created compatible structure: {indexing_state}")
            else:
                return {
                    "status": "not_found",
                    "message": "No indexing state found",
                }

        # Get all cell data with current statuses
        grid_cells = indexing_state.get("grid_cells", [])
        print(f"🔍 get_current_indexing_state: grid_cells from indexing_state: {grid_cells}")
        
        cell_data = []

        for cell in grid_cells:
            cell_id = cell["id"]
            print(f"🔍 get_current_indexing_state: Processing cell {cell_id}")
            
            status = ctx.store("metageo").get(f"cell_{cell_id}_status")
            error = ctx.store("metageo").get(f"cell_{cell_id}_error")
            osm_features = ctx.store("metageo").get(
                f"cell_{cell_id}_osm_features"
            )
            osm_data = ctx.store("metageo").get(f"cell_{cell_id}_osm_data")
            
            print(f"🔍 get_current_indexing_state: Cell {cell_id} - status: {status}, error: {error}, osm_features: {osm_features}")

            cell_data.append(
                {
                    "id": cell_id,
                    "coordinates": cell.get("coordinates"),
                    "sample_count": cell.get("sample_count", 0),
                    "status": status or "idle",
                    "error": error,
                    "osm_features": osm_features or 0,
                    "osm_data": osm_data,
                }
            )

        return {
            "status": "found",
            "indexing_id": indexing_state.get("indexing_id"),
            "total_cells": indexing_state.get("total_cells", 0),
            "active_cells": indexing_state.get("active_cells", 0),
            "completed_cells": indexing_state.get("completed_cells", 0),
            "failed_cells": indexing_state.get("failed_cells", 0),
            "rate_limited_cells": indexing_state.get("rate_limited_cells", 0),
            "total_features": indexing_state.get("total_features", 0),
            "progress": indexing_state.get("progress", 0),
            "indexing_status": indexing_state.get("status", "idle"),  # Use different key to avoid conflict
            "started_at": indexing_state.get("started_at"),
            "completed_at": indexing_state.get("completed_at"),
            "grid_cells": cell_data,
            "bbox": indexing_state.get("bbox"),
            "grid_tiles": indexing_state.get("grid_tiles"),
            "geo_field": indexing_state.get("geo_field"),
        }

    def get_existing_index(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Get existing index data if available"""
        indexing_state = ctx.store("metageo").get("indexing_state")
        if not indexing_state:
            return {
                "status": "not_found",
                "message": "No existing index found",
            }

        # Check if we have a completed index
        if indexing_state.get("status") != "completed":
            return {"status": "incomplete", "message": "Index is not complete"}

        # Get all cell data
        grid_cells = indexing_state.get("grid_cells", [])
        cell_data = []

        for cell in grid_cells:
            cell_id = cell["id"]
            status = ctx.store("metageo").get(f"cell_{cell_id}_status")
            error = ctx.store("metageo").get(f"cell_{cell_id}_error")
            osm_features = ctx.store("metageo").get(
                f"cell_{cell_id}_osm_features"
            )
            osm_data = ctx.store("metageo").get(f"cell_{cell_id}_osm_data")

            cell_data.append(
                {
                    "id": cell_id,
                    "coordinates": cell.get("coordinates"),
                    "sample_count": cell.get("sample_count", 0),
                    "status": status,
                    "error": error,
                    "osm_features": osm_features,
                    "osm_data": osm_data,
                }
            )

        return {
            "status": "found",
            "indexing_id": indexing_state.get("indexing_id"),
            "total_cells": indexing_state.get("total_cells", 0),
            "active_cells": indexing_state.get("active_cells", 0),
            "completed_cells": indexing_state.get("completed_cells", 0),
            "failed_cells": indexing_state.get("failed_cells", 0),
            "rate_limited_cells": indexing_state.get("rate_limited_cells", 0),
            "total_features": indexing_state.get("total_features", 0),
            "grid_cells": cell_data,
            "bbox": indexing_state.get("bbox"),
            "grid_tiles": indexing_state.get("grid_tiles"),
            "geo_field": indexing_state.get("geo_field"),
            "completed_at": indexing_state.get("completed_at"),
        }

    def drop_index(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Drop/clear the existing index"""
        indexing_state = ctx.store("metageo").get("indexing_state")
        if not indexing_state:
            return {"status": "not_found", "message": "No index to drop"}

        # Clear all cell data
        grid_cells = indexing_state.get("grid_cells", [])
        cleared_cells = 0

        for cell in grid_cells:
            cell_id = cell["id"]
            ctx.store("metageo").delete(f"cell_{cell_id}_status")
            ctx.store("metageo").delete(f"cell_{cell_id}_error")
            ctx.store("metageo").delete(f"cell_{cell_id}_osm_features")
            ctx.store("metageo").delete(f"cell_{cell_id}_osm_data")
            cleared_cells += 1

        # Clear the indexing state
        ctx.store("metageo").delete("indexing_state")

        print(f"Index dropped: cleared {cleared_cells} cells")
        return {
            "status": "dropped",
            "message": f"Index dropped successfully. Cleared {cleared_cells} cells.",
            "cleared_cells": cleared_cells,
        }

    def _calculate_sample_distribution(
        self,
        ctx: ExecutionContext,
        geo_field: str,
        bbox: BBox,
        grid_tiles: int,
    ) -> Dict[str, int]:
        """Efficiently calculate sample distribution across all grid cells in one pass"""
        try:
            print(
                f"Calculating sample distribution for {grid_tiles}x{grid_tiles} grid..."
            )
            print(f"Bounding box: {bbox}")
            print(f"Geo field: {geo_field}")

            # Get all coordinates from the dataset in one query
            coords = []
            try:
                coords = ctx.view.values(geo_field)
                print(f"Direct field access successful: {len(coords)} values")
                print(f"First 3 values: {coords[:3]}")
            except Exception as e:
                print(f"Direct field access failed: {e}")
                try:
                    coords = ctx.view.values(f"{geo_field}.coordinates")
                    print(
                        f"Coordinates subfield access successful: {len(coords)} values"
                    )
                    print(f"First 3 values: {coords[:3]}")
                except Exception as e:
                    print(f"Coordinates subfield access failed: {e}")
                    try:
                        coords = ctx.view.values(f"{geo_field}.point")
                        print(
                            f"Point subfield access successful: {len(coords)} values"
                        )
                        print(f"First 3 values: {coords[:3]}")
                    except Exception as e:
                        print(f"Point subfield access failed: {e}")
                        try:
                            coords = ctx.view.values(f"{geo_field}.location")
                            print(
                                f"Location subfield access successful: {len(coords)} values"
                            )
                            print(f"First 3 values: {coords[:3]}")
                        except Exception as e:
                            print(f"Location subfield access failed: {e}")
                            print(
                                f"Could not access coordinates from field '{geo_field}'"
                            )
                            return {}

            if not coords:
                print("No coordinates found in dataset")
                return {}

            # Calculate grid cell dimensions
            min_lon, min_lat, max_lon, max_lat = bbox
            lon_step = (max_lon - min_lon) / grid_tiles
            lat_step = (max_lat - min_lat) / grid_tiles

            print(
                f"Grid dimensions: lon_step={lon_step:.6f}, lat_step={lat_step:.6f}"
            )

            # Initialize sample count dictionary
            sample_distribution = {}

            # Process all coordinates in one pass
            valid_coords = 0
            bbox_coords = 0
            for i, c in enumerate(coords):
                if c is None:
                    continue

                # Extract coordinates
                lon, lat = None, None
                if isinstance(c, (list, tuple)) and len(c) == 2:
                    lon, lat = float(c[0]), float(c[1])
                elif (
                    hasattr(c, "coordinates")
                    and isinstance(c.coordinates, (list, tuple))
                    and len(c.coordinates) == 2
                ):
                    lon, lat = float(c.coordinates[0]), float(c.coordinates[1])
                elif (
                    hasattr(c, "point")
                    and isinstance(c.point, (list, tuple))
                    and len(c.point) == 2
                ):
                    lon, lat = float(c.point[0]), float(c.point[1])

                if lon is not None and lat is not None:
                    valid_coords += 1

                    # Calculate which grid cell this coordinate belongs to
                    if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                        bbox_coords += 1
                        col = int((lon - min_lon) / lon_step)
                        row = int((lat - min_lat) / lat_step)

                        # Ensure we're within grid bounds
                        col = max(0, min(col, grid_tiles - 1))
                        row = max(0, min(row, grid_tiles - 1))

                        cell_id = f"{row}_{col}"
                        sample_distribution[cell_id] = (
                            sample_distribution.get(cell_id, 0) + 1
                        )

                        # Debug first few coordinates
                        if valid_coords <= 5:
                            print(
                                f"  Coord {i}: ({lon:.6f}, {lat:.6f}) -> cell {cell_id}"
                            )
                    else:
                        # Debug coordinates outside bbox
                        if valid_coords <= 5:
                            print(
                                f"  Coord {i}: ({lon:.6f}, {lat:.6f}) -> OUTSIDE bbox"
                            )

            print(f"Total coordinates processed: {len(coords)}")
            print(f"Valid coordinates: {valid_coords}")
            print(f"Coordinates within bbox: {bbox_coords}")
            print(
                f"Sample distribution calculated for {len(sample_distribution)} cells"
            )

            if sample_distribution:
                print(
                    f"Sample distribution sample: {dict(list(sample_distribution.items())[:5])}"
                )

            return sample_distribution

        except Exception as e:
            print(f"Error calculating sample distribution: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def _execute_indexing_immediate(
        self, ctx: ExecutionContext, indexing_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute indexing synchronously (for immediate mode)"""
        print("Executing indexing in immediate mode...")

        # Initialize OSM client
        osm_client = OSMClient()

        # Retry loop: continue until all cells are processed or exhausted retries
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"Indexing iteration {iteration}/{max_iterations}")
            
            # Check if we have any cells that need processing
            cells_to_process = [
                cell for cell in indexing_state["grid_cells"] 
                if cell["sample_count"] > 0 and cell.get("status") in ["idle", "retrying"]
            ]
            
            if not cells_to_process:
                print("No more cells to process, breaking retry loop")
                break
                
            print(f"Processing {len(cells_to_process)} cells in iteration {iteration}")

            for cell in cells_to_process:
                if cell["sample_count"] == 0:
                    # Ensure empty cells are marked as "empty"
                    cell["status"] = "empty"
                    print(f"Cell {cell['id']}: Marked as empty (0 samples)")
                    continue

                if indexing_state["status"] == "cancelled":
                    print(f"Cell {cell['id']}: Skipped due to cancellation")
                    break

                # Initialize retry tracking for this cell
                if "retry_count" not in cell:
                    cell["retry_count"] = 0
                if "max_retries" not in cell:
                    cell["max_retries"] = 3  # Default max retries per cell

                # Query OSM data for this cell
                print(f"Cell {cell['id']}: Starting processing (samples: {cell['sample_count']}, retry: {cell['retry_count']}/{cell['max_retries']})")
                
                # Set status based on retry count
                if cell["retry_count"] > 0:
                    cell["status"] = "retrying"
                    cell["progress"] = 25
                    print(f"Cell {cell['id']}: Retrying (attempt {cell['retry_count'] + 1})")
                else:
                    cell["status"] = "running"
                    cell["progress"] = 25

                try:
                    # Query OSM data for this cell's bounding box with retry logic
                    osm_result = osm_client.query_bbox(
                        cell["coordinates"], 
                        max_retries=cell["max_retries"] - cell["retry_count"],
                        base_delay=2.0,  # Start with 2 second delay
                        max_delay=30.0   # Max 30 second delay
                    )

                    if "error" in osm_result:
                        error_msg = osm_result["error"]
                        attempts = osm_result.get("attempts", 1)
                        
                        # Check if this was a rate limiting error that exhausted retries
                        if (
                            "rate limit" in error_msg.lower()
                            or "server load too high" in error_msg.lower()
                            or "too many requests" in error_msg.lower()
                        ):
                            # Update retry count
                            cell["retry_count"] += attempts
                            
                            if cell["retry_count"] >= cell["max_retries"]:
                                # Exhausted all retries, mark as rate_limited
                                cell["status"] = "rate_limited"
                                cell["error"] = f"{error_msg} (exhausted {cell['retry_count']} retries)"
                                cell["progress"] = 0
                                indexing_state["rate_limited_cells"] = indexing_state.get("rate_limited_cells", 0) + 1
                                
                                # Save cell status to store for frontend synchronization
                                ctx.store("metageo").set(f"cell_{cell['id']}_status", "rate_limited")
                                ctx.store("metageo").set(f"cell_{cell['id']}_error", cell["error"])
                                
                                print(f"Cell {cell['id']}: Rate limited after {cell['retry_count']} retries")
                            else:
                                # Still have retries left, mark as retrying and continue to next cell
                                cell["status"] = "retrying"
                                cell["error"] = f"{error_msg} (retry {cell['retry_count']}/{cell['max_retries']})"
                                cell["progress"] = 0
                                
                                # Save cell status to store for frontend synchronization
                                ctx.store("metageo").set(f"cell_{cell['id']}_status", "retrying")
                                ctx.store("metageo").set(f"cell_{cell['id']}_error", cell["error"])
                                
                                print(f"Cell {cell['id']}: Rate limited, will retry later (attempt {cell['retry_count']}/{cell['max_retries']})")
                                continue  # Skip to next cell, this one will be retried later
                        else:
                            # Non-rate-limiting error, mark as failed
                            cell["status"] = "failed"
                            cell["error"] = error_msg
                            cell["progress"] = 0
                            indexing_state["failed_cells"] += 1
                            
                            # Save cell status to store for frontend synchronization
                            ctx.store("metageo").set(f"cell_{cell['id']}_status", "failed")
                            ctx.store("metageo").set(f"cell_{cell['id']}_error", error_msg)
                            
                            print(f"Cell {cell['id']}: Failed with error: {error_msg}")
                    else:
                        # Success! Store OSM data in cell
                        cell["osm_data"] = osm_result
                        cell["osm_feature_count"] = osm_result["count"]
                        cell["osm_statistics"] = osm_client.get_feature_statistics(
                            osm_result["features"]
                        )

                        cell["status"] = "completed"
                        cell["progress"] = 100
                        cell["retry_count"] = 0  # Reset retry count on success
                        indexing_state["completed_cells"] += 1
                        
                        # Save cell status to store for frontend synchronization
                        ctx.store("metageo").set(f"cell_{cell['id']}_status", "completed")
                        ctx.store("metageo").set(f"cell_{cell['id']}_osm_features", osm_result["count"])

                        print(
                            f"Cell {cell['id']}: Retrieved {osm_result['count']} OSM features (after {osm_result.get('attempts', 1)} attempts)"
                        )

                except Exception as e:
                    cell["status"] = "failed"
                    cell["error"] = str(e)
                    cell["progress"] = 0
                    indexing_state["failed_cells"] += 1
                    
                    # Save cell status to store for frontend synchronization
                    ctx.store("metageo").set(f"cell_{cell['id']}_status", "failed")
                    ctx.store("metageo").set(f"cell_{cell['id']}_error", str(e))
                    
                    print(f"Error processing cell {cell['id']}: {e}")
            
            # Add a small delay between iterations to be respectful to the API
            if iteration < max_iterations:
                print("Waiting 5 seconds before next iteration...")
                time.sleep(5)

        # Check if all active cells have been processed
        # Only count active cells (exclude empty cells from total)
        active_cells = [c for c in indexing_state["grid_cells"] if c.get("status") != "empty"]
        total_active_cells = len(active_cells)
        
        # Processed cells includes only completed, failed, rate_limited (not empty, not retrying)
        # Retrying cells are still being worked on, so they don't count as processed
        processed_cells = len([
            c for c in active_cells 
            if c.get("status") in ["completed", "failed", "rate_limited"]
        ])
        
        # Count retrying cells for debugging
        retrying_cells = len([
            c for c in active_cells 
            if c.get("status") == "retrying"
        ])
        
        # Debug: Print cell statuses
        print(f"COMPLETION CHECK: total_active_cells={total_active_cells}, processed_cells={processed_cells}, retrying_cells={retrying_cells}")
        for cell in indexing_state["grid_cells"]:
            print(f"  Cell {cell['id']}: status={cell.get('status')}, sample_count={cell.get('sample_count')}, retry_count={cell.get('retry_count', 0)}")
        
        if total_active_cells == 0 or processed_cells == total_active_cells:
            indexing_state["status"] = "completed"
            print("Indexing marked as COMPLETED")
        else:
            indexing_state["status"] = "running"  # Still processing
            print(f"Indexing still RUNNING - {total_active_cells - processed_cells} active cells remaining ({retrying_cells} retrying)")
            
        ctx.store("metageo").set("indexing_state", indexing_state)

        # Calculate final statistics
        total_features = sum(
            cell.get("osm_feature_count", 0)
            for cell in indexing_state["grid_cells"]
            if cell.get("status") == "completed"
        )

        return {
            "status": "completed",
            "total_cells": indexing_state["total_cells"],
            "completed_cells": indexing_state["completed_cells"],
            "failed_cells": indexing_state["failed_cells"],
            "total_osm_features": total_features,
            "message": f"Indexing completed successfully. Retrieved {total_features} OSM features.",
        }

    def enrich(self, ctx: ExecutionContext) -> Dict[str, Any]:
        geo_field = ctx.params.get("geo_field")
        radius_m = ctx.params.get("radius_m")
        prefetch_id = ctx.params.get("prefetch_id")

        if not geo_field or not prefetch_id:
            raise ValueError("'geo_field' and 'prefetch_id' are required")

        # Mock OSM API: Simulate real enrichment process
        print(f"Mock OSM API: Enriching {geo_field} with radius {radius_m}m")
        print(f"Mock OSM API: Using prefetch ID: {prefetch_id}")

        # Get real sample count from dataset
        sample_count = ctx.view.count()

        # Simulate realistic enrichment results
        # Some samples might be outside the indexed area or have no nearby OSM features
        enrichment_rate = 0.85  # 85% of samples get enriched
        enriched_count = int(sample_count * enrichment_rate)

        # Simulate cache performance
        cache_hit_rate = 0.92  # 92% cache hit rate
        cache_hits = int(enriched_count * cache_hit_rate)
        cache_misses = enriched_count - cache_hits

        # Simulate realistic timing based on sample count and radius
        base_time = 50  # ms base time
        time_per_sample = 0.1  # ms per sample
        radius_factor = radius_m / 100  # Larger radius = more time

        total_time = base_time + (
            sample_count * time_per_sample * radius_factor
        )

        print(
            f"Mock OSM API: Enriched {enriched_count:,}/{sample_count:,} samples"
        )
        print(
            f"Mock OSM API: Cache hits: {cache_hits:,}, misses: {cache_misses:,}"
        )
        print(f"Mock OSM API: Total time: {total_time:.0f}ms")

        return {
            "samples_enriched": enriched_count,
            "total_samples": sample_count,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "ms_by_phase": {
                "location_lookup": int(total_time * 0.3),
                "osm_query": int(total_time * 0.4),
                "data_mapping": int(total_time * 0.2),
                "sample_update": int(total_time * 0.1),
            },
            "radius_m": radius_m,
            "geo_field": geo_field,
            "enrichment_rate": round(enrichment_rate * 100, 1),
            "cache_hit_rate": round(cache_hit_rate * 100, 1),
        }

    def cleanup_index(self, ctx: ExecutionContext) -> Dict[str, Any]:
        prefetch_id = ctx.params.get("prefetch_id")

        # This would typically remove indexed OSM data
        # For now, returning mock cleanup results
        removed_count = 1 if prefetch_id else 0
        return {
            "removed_indexes": removed_count,
            "freed_space_mb": 150.5,
            "prefetch_id": prefetch_id,
        }

    def cleanup_enriched_data(self, ctx: ExecutionContext) -> Dict[str, Any]:
        fields = ctx.params.get("fields")

        # This would typically remove enriched fields from samples
        # For now, returning mock cleanup results
        if not fields:
            # Mock: remove common OSM field prefixes
            fields = [
                "osm_highway",
                "osm_amenity",
                "osm_building",
                "osm_landuse",
            ]

        sample_count = ctx.view.count()
        return {
            "removed_fields": len(fields),
            "fields_removed": fields,
            "samples_affected": sample_count,
            "freed_space_mb": 25.3,
        }

    def create_filters(self, ctx: ExecutionContext) -> Dict[str, Any]:
        field = ctx.params.get("field")
        value = ctx.params.get("value")
        filter_type = ctx.params.get("filter_type", "equals")

        if not field or not value:
            raise ValueError("'field' and 'value' are required")

        # This would typically create FiftyOne filters for the enriched data
        # For now, returning mock filter creation results
        return {
            "filter_created": True,
            "field": field,
            "value": value,
            "type": filter_type,
            "filter_id": f"filter_{field}_{value}_{hash(str(ctx.dataset.name))}",
        }

    def test_osm_client(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Test the OSM client with a small query"""
        bbox = ctx.params.get("bbox")
        if not bbox:
            return {"error": "bbox parameter required"}

        try:
            osm_client = OSMClient()
            result = osm_client.query_bbox(
                bbox, feature_types=["highway", "amenity"]
            )

            return {
                "success": True,
                "result": result,
                "message": f"Test query completed. Retrieved {result.get('count', 0)} features.",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Test query failed",
            }

    def render(self, ctx: ExecutionContext) -> Property:
        panel = fo_types.Object()
        return fo_types.Property(
            panel,
            view=fo_types.View(
                component="MetageoView",
                composite_view=True,
                define_area_auto=self.define_area_auto,
                explore_tags=self.explore_tags,
                get_sample_distribution=self.get_sample_distribution,
                start_indexing=self.start_indexing,
                get_indexing_status=self.get_indexing_status,
                get_current_indexing_state=self.get_current_indexing_state,
                get_existing_index=self.get_existing_index,
                drop_index=self.drop_index,
                cancel_indexing=self.cancel_indexing,
                test_osm_client=self.test_osm_client,
                get_available_osm_tags=self.get_available_osm_tags,
                get_field_mappings=self.get_field_mappings,
                save_mapping_config=self.save_mapping_config,
                get_mapping_config=self.get_mapping_config,
                clear_mapping_config=self.clear_mapping_config,
                clear_enrichment_data=self.clear_enrichment_data,
                enrich_dataset_async=self.enrich_dataset_async,
                get_enrichment_status=self.get_enrichment_status,
                get_geo_fields=self.get_geo_fields,
                enrich=self.enrich,
                cleanup_index=self.cleanup_index,
                cleanup_enriched_data=self.cleanup_enriched_data,
                create_filters=self.create_filters,
            ),
        )


def register(p):
    p.register(MetageoPanel)
    p.register(IndexGridOperator)
    p.register(WatchIndexingOperator)
 