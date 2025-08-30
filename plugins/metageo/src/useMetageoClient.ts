import { useCallback } from "react";
import { usePanelEvent } from "@fiftyone/operators";

export type MetageoClient = {
  define_area_auto: (params: { geo_field: string }) => Promise<any>;
  explore_tags: (params: { bbox: number[] }) => Promise<any>;
  get_sample_distribution: (params: {
    bbox: number[];
    grid_tiles: number;
    geo_field: string;
  }) => Promise<any>;
  start_indexing: (params: {
    bbox: number[];
    grid_tiles: number;
    geo_field: string;
    execution_mode: "immediate" | "delegated";
  }) => Promise<any>;
  get_indexing_state: () => Promise<any>;
  get_cell_statuses: () => Promise<any>;
  get_indexing_status: (params: {}) => Promise<any>;
  get_existing_index: () => Promise<any>;
  drop_index: () => Promise<any>;
  get_available_osm_tags: () => Promise<any>;
  cancel_indexing: (params: {}) => Promise<any>;
  enrich: (params: {
    geo_field: string;
    radius_m: number;
    prefetch_id: string;
  }) => Promise<any>;
  cleanup_index: (params: { prefetch_id?: string }) => Promise<any>;
  cleanup_enriched_data: (params?: any) => Promise<any>;
  create_filters: (params: {
    field: string;
    value: string;
    filter_type: string;
  }) => Promise<any>;
};

export function useMetageoClient(props: any): MetageoClient {
  const handleEvent = usePanelEvent();

  const client: MetageoClient = {
    define_area_auto: useCallback(
      async (params: { geo_field: string }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#define_area_auto",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    explore_tags: useCallback(
      async (params: { bbox: number[] }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#explore_tags",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    start_indexing: useCallback(
      async (params: {
        bbox: number[];
        grid_tiles: number;
        geo_field: string;
        execution_mode: "immediate" | "delegated";
      }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#start_indexing",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    get_indexing_state: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent(props.id, {
          operator: "@voxel51/metageo/metageo_panel#get_indexing_state",
          params: {},
          panelId: props.id,
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent, props.id]),
    get_cell_statuses: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent(props.id, {
          operator: "@voxel51/metageo/metageo_panel#get_cell_statuses",
          params: {},
          panelId: props.id,
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent, props.id]),

    get_sample_distribution: useCallback(
      async (params: {
        bbox: number[];
        grid_tiles: number;
        geo_field: string;
      }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#get_sample_distribution",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    get_indexing_status: useCallback(
      async (params: {}) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#get_indexing_status",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    get_existing_index: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent(props.id, {
          operator: "@voxel51/metageo/metageo_panel#get_existing_index",
          params: {},
          panelId: props.id,
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent, props.id]),

    drop_index: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent(props.id, {
          operator: "@voxel51/metageo/metageo_panel#drop_index",
          params: {},
          panelId: props.id,
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent, props.id]),

    cancel_indexing: useCallback(
      async (params: {}) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#cancel_indexing",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    enrich: useCallback(
      async (params: {
        geo_field: string;
        radius_m: number;
        prefetch_id: string;
      }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#enrich",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    cleanup_index: useCallback(
      async (params: { prefetch_id?: string }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#cleanup_index",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    cleanup_enriched_data: useCallback(
      async (params?: any) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#cleanup_enriched_data",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    create_filters: useCallback(
      async (params: { field: string; value: string; filter_type: string }) => {
        return new Promise<any>((resolve, reject) => {
          handleEvent(props.id, {
            operator: "@voxel51/metageo/metageo_panel#create_filters",
            params,
            panelId: props.id,
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
      [handleEvent, props.id]
    ),

    get_available_osm_tags: useCallback(async () => {
      return new Promise<any>((resolve, reject) => {
        handleEvent(props.id, {
          operator: "@voxel51/metageo/metageo_panel#get_available_osm_tags",
          params: {},
          panelId: props.id,
          callback: (result: any) => {
            if (result?.error) {
              reject(new Error(result.error));
            } else {
              resolve(result);
            }
          },
        });
      });
    }, [handleEvent, props.id]),
  };

  return client;
}
