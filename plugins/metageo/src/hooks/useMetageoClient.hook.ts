import { useMemo } from "react";
import { usePanelEvent } from "@fiftyone/operators";
import type { MetageoClient } from "../types/index";

// Utility function to create operator calls with consistent error handling
function createOperatorCall(
  handleEvent: any,
  eventName: string,
  operator: string
) {
  return async (params: any = {}) => {
    return new Promise<any>((resolve, reject) => {
      handleEvent(eventName, {
        operator,
        params,
        callback: (result: any) => {
          if (result?.error) {
            reject(new Error(result.error));
          } else {
            resolve(result);
          }
        },
      });
    });
  };
}

export function useMetageoClient(): MetageoClient {
  console.log("🔍 useMetageoClient: Hook starting...");

  const handleEvent = usePanelEvent();
  console.log("🔍 useMetageoClient: handleEvent =", handleEvent);

  const client: MetageoClient = useMemo(
    () => ({
      define_area_auto: createOperatorCall(
        handleEvent,
        "define_area_auto",
        "@voxel51/metageo/metageo_panel#define_area_auto"
      ),

      calculate_sample_distribution: createOperatorCall(
        handleEvent,
        "calculate_sample_distribution",
        "@voxel51/metageo/metageo_panel#get_sample_distribution"
      ),

      index_grid: createOperatorCall(
        handleEvent,
        "index_grid",
        "@voxel51/metageo/index_grid"
      ),

      start_indexing: createOperatorCall(
        handleEvent,
        "start_indexing",
        "@voxel51/metageo/metageo_panel#start_indexing"
      ),

      watch_indexing: createOperatorCall(
        handleEvent,
        "watch_indexing",
        "@voxel51/metageo/watch_indexing"
      ),

      get_current_indexing_state: createOperatorCall(
        handleEvent,
        "get_current_indexing_state",
        "@voxel51/metageo/metageo_panel#get_current_indexing_state"
      ),

      drop_index: createOperatorCall(
        handleEvent,
        "drop_index",
        "@voxel51/metageo/metageo_panel#drop_index"
      ),

      get_available_osm_tags: createOperatorCall(
        handleEvent,
        "get_available_osm_tags",
        "@voxel51/metageo/metageo_panel#get_available_osm_tags"
      ),

      get_field_mappings: createOperatorCall(
        handleEvent,
        "get_field_mappings",
        "@voxel51/metageo/metageo_panel#get_field_mappings"
      ),

      save_mapping_config: createOperatorCall(
        handleEvent,
        "save_mapping_config",
        "@voxel51/metageo/metageo_panel#save_mapping_config"
      ),

      get_mapping_config: createOperatorCall(
        handleEvent,
        "get_mapping_config",
        "@voxel51/metageo/metageo_panel#get_mapping_config"
      ),

      clear_mapping_config: createOperatorCall(
        handleEvent,
        "clear_mapping_config",
        "@voxel51/metageo/metageo_panel#clear_mapping_config"
      ),

      clear_enrichment_data: createOperatorCall(
        handleEvent,
        "clear_enrichment_data",
        "@voxel51/metageo/metageo_panel#clear_enrichment_data"
      ),

      enrich_dataset_async: createOperatorCall(
        handleEvent,
        "enrich_dataset_async",
        "@voxel51/metageo/metageo_panel#enrich_dataset_async"
      ),

      get_enrichment_status: createOperatorCall(
        handleEvent,
        "get_enrichment_status",
        "@voxel51/metageo/metageo_panel#get_enrichment_status"
      ),

      get_geo_fields: createOperatorCall(
        handleEvent,
        "get_geo_fields",
        "@voxel51/metageo/metageo_panel#get_geo_fields"
      ),

      get_dataset_info: createOperatorCall(
        handleEvent,
        "get_dataset_info",
        "@voxel51/metageo/metageo_panel#get_dataset_info"
      ),

      get_sample_geo_points: createOperatorCall(
        handleEvent,
        "get_sample_geo_points",
        "@voxel51/metageo/metageo_panel#get_sample_geo_points"
      ),

      get_cell_data: createOperatorCall(
        handleEvent,
        "get_cell_data",
        "@voxel51/metageo/metageo_panel#get_cell_data"
      ),

      cancel_indexing: createOperatorCall(
        handleEvent,
        "cancel_indexing",
        "@voxel51/metageo/metageo_panel#cancel_indexing"
      ),

      reset_metageo: createOperatorCall(
        handleEvent,
        "reset_metageo",
        "@voxel51/metageo/metageo_panel#reset_metageo"
      ),

      // Enrichment progress tracking
      watch_enrichment: createOperatorCall(
        handleEvent,
        "watch_enrichment",
        "@voxel51/metageo/watch_enrichment_progress"
      ),

      cancel_enrichment: createOperatorCall(
        handleEvent,
        "cancel_enrichment",
        "@voxel51/metageo/metageo_panel#cancel_enrichment"
      ),
    }),
    [handleEvent]
  );

  return client;
}
