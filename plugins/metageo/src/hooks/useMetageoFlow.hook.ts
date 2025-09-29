import { useCallback, useMemo } from "react";
import { useRecoilState } from "recoil";
import { activeStepAtom, hasStartedAtom } from "../state/flow.atom";
import { useIndexingState } from "./useIndexingState.hook";
import { useMappingConfig } from "./useMappingConfig.hook";
import { useMetageoClient } from "./useMetageoClient.hook";
import { hasStoredState } from "../utils/persistence";
import type { BoundingBox } from "../types";

export const STEPS = {
  INDEX_CONFIGURATION: 0,
  INDEXING: 1,
  MAPPING: 2,
  ENRICH: 3,
  SEARCH_CLEANUP: 4,
} as const;

export type Step = typeof STEPS[keyof typeof STEPS];

export function useMetageoFlow() {
  console.log("🔍 useMetageoFlow: Hook starting...");

  let activeStep, setActiveStep, hasStarted, setHasStarted;
  try {
    [activeStep, setActiveStep] = useRecoilState(activeStepAtom);
    [hasStarted, setHasStarted] = useRecoilState(hasStartedAtom);
  } catch (error) {
    console.error("🔍 useMetageoFlow: Error accessing atoms:", error);
    // Return default state if atom access fails
    return {
      state: { activeStep: 0, hasStarted: false },
      actions: {
        start: () => {},
        next: () => {},
        back: () => {},
        goToStep: () => {},
        autoDetectBbox: async () => ({ success: false, error: "Client not available" }),
        calculateSampleDistribution: async () => ({ success: false, error: "Client not available" }),
        startIndexing: async () => ({ success: false, error: "Client not available" }),
        dropIndex: async () => ({ success: false, error: "Client not available" }),
        loadCurrentIndexingState: async () => ({ success: false, error: "Client not available" }),
      },
      derived: {
        canGoNext: false,
        canGoBack: false,
        isFirstStep: true,
        isLastStep: false,
        stepName: "Unknown",
        hasExistingIndex: false,
      },
    };
  }
  
  console.log("🔍 useMetageoFlow: activeStep =", activeStep);
  console.log("🔍 useMetageoFlow: hasStarted =", hasStarted);

  const { state: indexingState, actions: indexingActions } = useIndexingState();
  console.log("🔍 useMetageoFlow: indexingState =", indexingState);
  console.log(
    "🔍 useMetageoFlow: indexingState.gridCells =",
    indexingState?.gridCells
  );
  console.log(
    "🔍 useMetageoFlow: indexingState.gridCells?.length =",
    indexingState?.gridCells?.length
  );

  const { state: mappingConfig } = useMappingConfig();
  console.log("🔍 useMetageoFlow: mappingConfig =", mappingConfig);

  const client = useMetageoClient();
  console.log("🔍 useMetageoFlow: client =", client);

  const start = useMemo(() => 
    () => {
      setHasStarted(true);
      setActiveStep(STEPS.INDEX_CONFIGURATION);
    },
    [setHasStarted, setActiveStep]
  );

  const next = useMemo(() => 
    () => {
      if (activeStep < STEPS.SEARCH_CLEANUP) {
        setActiveStep(activeStep + 1);
      }
    },
    [activeStep, setActiveStep]
  );

  const back = useMemo(() => 
    () => {
      if (activeStep > STEPS.INDEX_CONFIGURATION) {
        setActiveStep(activeStep - 1);
      }
    },
    [activeStep, setActiveStep]
  );

  const goToStep = useMemo(() => 
    (step: Step) => {
      setActiveStep(step);
    },
    [setActiveStep]
  );

  const autoDetectBbox = useMemo(() => 
    async (geoField: string) => {
      if (!client) {
        return { success: false, error: "Client not available" };
      }
      try {
        const result = await client.define_area_auto({ geo_field: geoField });
        if (result?.result?.bbox) {
          const bbox: BoundingBox = {
            minLon: result.result.bbox[0],
            minLat: result.result.bbox[1],
            maxLon: result.result.bbox[2],
            maxLat: result.result.bbox[3],
          };
          indexingActions.setBbox(bbox);
          indexingActions.setLocation(geoField);
          return { success: true, bbox };
        }
        return { success: false, error: "No bounding box data received" };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [client, indexingActions]
  );

  const calculateSampleDistribution = useMemo(() => 
    async () => {
      if (!client) {
        return { success: false, error: "Client not available" };
      }
      if (
        !indexingState.bbox ||
        !mappingConfig.geoField ||
        !indexingState.gridTiles
      ) {
        return { success: false, error: "Missing required configuration" };
      }

      try {
        const bboxArray = [
          indexingState.bbox.minLon,
          indexingState.bbox.minLat,
          indexingState.bbox.maxLon,
          indexingState.bbox.maxLat,
        ];

        const result = await client.calculate_sample_distribution({
          bbox: bboxArray,
          grid_tiles: indexingState.gridTiles,
          geo_field: mappingConfig.geoField,
        });

        if (result?.result?.grid_cells) {
          indexingActions.setGridCells(result.result.grid_cells);
          indexingActions.setRealSampleDistribution(
            result.result.sample_distribution || {}
          );
          return { success: true, data: result.result };
        }
        return { success: false, error: "No grid cells data received" };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [
      indexingState.bbox,
      mappingConfig.geoField,
      indexingState.gridTiles,
      client,
      indexingActions,
    ]
  );

  const startIndexing = useMemo(() => 
    async () => {
      if (!client) {
        return { success: false, error: "Client not available" };
      }
      if (
        !indexingState.bbox ||
        !mappingConfig.geoField ||
        !indexingState.gridTiles
      ) {
        return { success: false, error: "Missing required configuration" };
      }

      try {
        const bboxArray = [
          indexingState.bbox.minLon,
          indexingState.bbox.minLat,
          indexingState.bbox.maxLon,
          indexingState.bbox.maxLat,
        ];

        indexingActions.setIndexingStatus("running");

        const result = await client.start_indexing({
          bbox: bboxArray,
          grid_tiles: indexingState.gridTiles,
          geo_field: mappingConfig.geoField,
          execution_mode: "immediate",
        });

        if (result?.result?.indexing_id) {
          // Start watching the indexing progress
          client.watch_indexing({ indexing_id: result.result.indexing_id });
          return { success: true, indexingId: result.result.indexing_id };
        }
        return { success: false, error: "No indexing ID received" };
      } catch (error) {
        indexingActions.setIndexingStatus("failed");
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [
      indexingState.bbox,
      mappingConfig.geoField,
      indexingState.gridTiles,
      client,
      indexingActions,
    ]
  );

  const dropIndex = useMemo(() => 
    async () => {
      if (!client) {
        return { success: false, error: "Client not available" };
      }
      try {
        await client.drop_index();
        indexingActions.resetIndexing();
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [client, indexingActions]
  );

  const loadCurrentIndexingState = useMemo(() => 
    async () => {
      console.log("🔍 loadCurrentIndexingState: Function called");
      if (!client) {
        console.warn("🔍 loadCurrentIndexingState: Client not available");
        return { success: false, error: "Client not available" };
      }
      try {
        console.log(
          "🔍 loadCurrentIndexingState: Calling client.get_current_indexing_state()"
        );
        const result = await client.get_current_indexing_state();
        console.log("🔍 loadCurrentIndexingState: Result received:", result);
        if (result?.result) {
          const data = result.result;
          console.log("🔍 loadCurrentIndexingState: Data extracted:", data);
          console.log(
            "🔍 loadCurrentIndexingState: Data keys:",
            Object.keys(data)
          );
          if (data.indexing_state) {
            // New format
            const state = data.indexing_state;
            console.log("🔍 loadCurrentIndexingState: New format state:", state);
            if (state.bbox) {
              indexingActions.setBbox({
                minLon: state.bbox[0],
                minLat: state.bbox[1],
                maxLon: state.bbox[2],
                maxLat: state.bbox[3],
              });
            }
            if (state.grid_cells) indexingActions.setGridCells(state.grid_cells);
            if (state.quadtree_cells)
              indexingActions.setQuadtreeCells(state.quadtree_cells);
            if (state.real_sample_distribution)
              indexingActions.setRealSampleDistribution(
                state.real_sample_distribution
              );
            if (state.indexing_status)
              indexingActions.setIndexingStatus(state.indexing_status);
            if (state.location) indexingActions.setLocation(state.location);
            if (state.grid_tiles) indexingActions.setGridTiles(state.grid_tiles);

            setHasStarted(true);
            return { success: true, hasExistingIndex: true };
          } else if (data.bbox || data.grid_cells) {
            // Old format - construct compatible state
            if (data.bbox) {
              indexingActions.setBbox({
                minLon: data.bbox[0],
                minLat: data.bbox[1],
                maxLon: data.bbox[2],
                maxLat: data.bbox[3],
              });
            }
            if (data.grid_cells) indexingActions.setGridCells(data.grid_cells);
            if (data.geo_field) indexingActions.setLocation(data.geo_field);

            setHasStarted(true);
            return { success: true, hasExistingIndex: true };
          }
        }
        return { success: true, hasExistingIndex: false };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [client, indexingActions, setHasStarted]
  );

  const actions = {
    start,
    next,
    back,
    goToStep,
    autoDetectBbox,
    calculateSampleDistribution,
    startIndexing,
    dropIndex,
    loadCurrentIndexingState,
  };

  const derived = useMemo(
    () => ({
      canGoNext: activeStep < STEPS.SEARCH_CLEANUP,
      canGoBack: activeStep > STEPS.INDEX_CONFIGURATION,
      isFirstStep: activeStep === STEPS.INDEX_CONFIGURATION,
      isLastStep: activeStep === STEPS.SEARCH_CLEANUP,
      stepName:
        Object.keys(STEPS).find(
          (key) => STEPS[key as keyof typeof STEPS] === activeStep
        ) || "Unknown",
      hasExistingIndex:
        (indexingState.gridCells && indexingState.gridCells.length > 0) ||
        indexingState.indexingStatus !== "idle",
    }),
    [activeStep, indexingState]
  );

  return {
    state: { activeStep, hasStarted },
    actions,
    derived,
  };
}
