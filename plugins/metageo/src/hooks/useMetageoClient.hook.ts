import { useCallback } from "react";
import { usePanelEvent } from "@fiftyone/operators";
import type { MetageoClient } from "../types";

export function useMetageoClient(): MetageoClient {
  console.log("🔍 useMetageoClient: Hook starting...");

  const handleEvent = usePanelEvent();
  console.log("🔍 useMetageoClient: handleEvent =", handleEvent);

  const client: MetageoClient = {
    define_area_auto: useCallback(
      async (params: { geo_field: string }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent("define_area_auto", {
            operator: "@voxel51/metageo/metageo_panel#define_area_auto",
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
      },
      [handleEvent]
    ),

    calculate_sample_distribution: useCallback(
      async (params: { bbox: number[]; grid_tiles: number }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent("calculate_sample_distribution", {
            operator: "@voxel51/metageo/metageo_panel#get_sample_distribution",
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
      },
      [handleEvent]
    ),

    index_grid: useCallback(
      async (params: {
        bbox: number[];
        grid_tiles: number;
        location: string;
      }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent("index_grid", {
            operator: "@voxel51/metageo/index_grid",
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
      },
      [handleEvent]
    ),

    start_indexing: useCallback(
      async (params: {
        bbox: number[];
        grid_tiles: number;
        location: string;
        execution_mode: "immediate" | "delegated";
      }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent("start_indexing", {
            operator: "@voxel51/metageo/metageo_panel#start_indexing",
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
      },
      [handleEvent]
    ),

    watch_indexing: useCallback(
      async (params: { indexing_id: string }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent("watch_indexing", {
            operator: "@voxel51/metageo/watch_indexing",
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
      },
      [handleEvent]
    ),

    get_current_indexing_state: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent("get_current_indexing_state", {
          operator: "@voxel51/metageo/metageo_panel#get_current_indexing_state",
          params: {},
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent]),

    drop_index: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent("drop_index", {
          operator: "@voxel51/metageo/metageo_panel#drop_index",
          params: {},
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent]),

    get_available_osm_tags: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent("get_available_osm_tags", {
          operator: "@voxel51/metageo/metageo_panel#get_available_osm_tags",
          params: {},
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent]),
  };

  return client;
}
