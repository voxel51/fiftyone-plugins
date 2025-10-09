import { useCallback, useMemo, useState, useEffect } from "react";
import { useRecoilState } from "recoil";
import { activeStepAtom, hasStartedAtom } from "../state/flow.atom";
import { useIndexingState } from "./useIndexingState.hook";
import { useMappingConfig } from "./useMappingConfig.hook";
import { useMetageoClient } from "./useMetageoClient.hook";
import { hasStoredState, getStoredFlowState, setStoredFlowState, clearStoredFlowState } from "../utils/persistence";
import type { BoundingBox } from "../types/index";

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
  const [isLoadingState, setIsLoadingState] = useState(true);
  
  // Add a timeout to prevent infinite loading
  useEffect(() => {
    const timeout = setTimeout(() => {
      console.log("🔍 useMetageoFlow: Loading timeout reached, setting isLoadingState to false");
      setIsLoadingState(false);
    }, 5000); // 5 second timeout
    
    return () => clearTimeout(timeout);
  }, []);

  // Save flow state to localStorage whenever it changes
  useEffect(() => {
    if (hasStarted) {
      console.log("🔍 useMetageoFlow: Saving flow state to localStorage:", { activeStep, hasStarted });
      setStoredFlowState({ activeStep, hasStarted });
    }
  }, [activeStep, hasStarted]);
  
  try {
    [activeStep, setActiveStep] = useRecoilState(activeStepAtom);
    [hasStarted, setHasStarted] = useRecoilState(hasStartedAtom);
  } catch (error) {
    console.error("🔍 useMetageoFlow: Error accessing atoms:", error);
    // Return default state if atom access fails
    return {
      state: { activeStep: 0, hasStarted: false, isLoadingState: true },
      actions: {
        start: () => {},
        next: () => {},
        back: () => {},
        goToStep: () => {},
        autoDetectBbox: async () => ({ success: false, error: "Client not available" }),
        calculateSampleDistribution: async () => ({ success: false, error: "Client not available" }),
        startIndexing: async () => ({ success: false, error: "Client not available" }),
        dropIndex: async () => ({ success: false, error: "Client not available" }),
        cancelIndexing: async () => ({ success: false, error: "Client not available" }),
        loadCurrentIndexingState: async () => ({ success: false, error: "Client not available" }),
        resetMetageo: async () => ({ success: false, error: "Client not available" }),
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
      console.log("🔍 next() called: activeStep =", activeStep, "STEPS.SEARCH_CLEANUP =", STEPS.SEARCH_CLEANUP);
      if (activeStep < STEPS.SEARCH_CLEANUP) {
        const newStep = activeStep + 1;
        console.log("🔍 next() setting activeStep from", activeStep, "to", newStep);
        setActiveStep(newStep);
      } else {
        console.log("🔍 next() blocked: already at last step");
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
    async (executionMode: "immediate" | "delegated" = "immediate") => {
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
          execution_mode: executionMode,
        });

        if (result?.result?.status === "error") {
          return { success: false, error: result.result.message };
        }

        if (result?.result?.indexing_id) {
          // Start watching the indexing progress (works for both immediate and delegated)
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
        // Reset to configuration step when index is dropped
        setActiveStep(STEPS.INDEX_CONFIGURATION);
        setHasStarted(false);
        // Clear stored flow state
        clearStoredFlowState();
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [client, indexingActions, setActiveStep, setHasStarted]
  );

  const cancelIndexing = useCallback(async () => {
    if (!client) {
      return { success: false, error: "Client not available" };
    }
    try {
      console.log("🔍 cancelIndexing: Starting cancellation...");
      const result = await client.cancel_indexing({});
      console.log("🔍 cancelIndexing: Backend result:", result);
      
        if (result?.result?.status === "cancelled") {
          console.log("🔍 cancelIndexing: Cancellation successful, resetting local state...");
          // Reset the local indexing state to clear all data with cancelled status
          indexingActions.resetIndexing("cancelled");
          
          // Reset to configuration step when indexing is cancelled
          setActiveStep(STEPS.INDEX_CONFIGURATION);
          setHasStarted(false);
          // Clear stored flow state
          clearStoredFlowState();
          
          console.log("🔍 cancelIndexing: Reloading indexing state from backend...");
          // Reload the current indexing state to reflect the cleared data
          try {
            const loadResult = await client.get_current_indexing_state();
            console.log("🔍 cancelIndexing: Load result:", loadResult);
            
            if (loadResult?.result) {
              const data = loadResult.result;
              if (data.indexing_state) {
                const state = data.indexing_state;
                if (state.bbox) {
                  indexingActions.setBbox({
                    minLon: state.bbox[0],
                    minLat: state.bbox[1],
                    maxLon: state.bbox[2],
                    maxLat: state.bbox[3],
                  });
                }
                if (state.grid_cells) indexingActions.setGridCells(state.grid_cells);
                if (state.quadtree_cells) indexingActions.setQuadtreeCells(state.quadtree_cells);
                if (state.real_sample_distribution) indexingActions.setRealSampleDistribution(state.real_sample_distribution);
                if (state.indexing_status) indexingActions.setIndexingStatus(state.indexing_status);
                if (state.location) indexingActions.setLocation(state.location);
                if (state.grid_tiles) indexingActions.setGridTiles(state.grid_tiles);
                console.log("🔍 cancelIndexing: Indexing state reloaded after cancellation");
              }
            }
          } catch (loadError) {
            console.warn("🔍 cancelIndexing: Failed to reload indexing state:", loadError);
          }
          
          return { success: true, message: result.result.message };
        }
      
      console.error("🔍 cancelIndexing: Backend did not return cancelled status:", result);
      return { success: false, error: result?.result?.message || "Failed to cancel indexing" };
    } catch (error) {
      console.error("🔍 cancelIndexing: Exception occurred:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }, [client, indexingActions, setActiveStep, setHasStarted]);

  const loadCurrentIndexingState = useMemo(() => 
    async () => {
      console.log("🔍 loadCurrentIndexingState: Function called");
      console.log("🔍 loadCurrentIndexingState: Client available:", !!client);
      setIsLoadingState(true);
      if (!client) {
        console.warn("🔍 loadCurrentIndexingState: Client not available");
        setIsLoadingState(false);
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
          
          // Check if we have the data directly (new format)
          if (data.bbox || data.grid_cells || data.indexing_status) {
            console.log("🔍 loadCurrentIndexingState: Found data directly in result");
            if (data.bbox) {
              indexingActions.setBbox({
                minLon: data.bbox[0],
                minLat: data.bbox[1],
                maxLon: data.bbox[2],
                maxLat: data.bbox[3],
              });
            }
            if (data.grid_cells) indexingActions.setGridCells(data.grid_cells);
            if (data.quadtree_cells)
              indexingActions.setQuadtreeCells(data.quadtree_cells);
            if (data.real_sample_distribution)
              indexingActions.setRealSampleDistribution(
                data.real_sample_distribution
              );
            if (data.indexing_status)
              indexingActions.setIndexingStatus(data.indexing_status);
            if (data.geo_field) indexingActions.setLocation(data.geo_field);
            if (data.grid_tiles) indexingActions.setGridTiles(data.grid_tiles);

            setHasStarted(true);
            
            // Check for saved flow state first
            const savedFlowState = getStoredFlowState();
            console.log("🔍 loadCurrentIndexingState: Saved flow state:", savedFlowState);
            
            // Check if there's a mapping configuration saved
            let hasMappingConfig = false;
            try {
              const mappingResult = await client.get_mapping_config();
              hasMappingConfig = mappingResult?.result?.status === "success" && mappingResult.result.mapping_config;
              console.log("🔍 loadCurrentIndexingState: Has mapping config:", hasMappingConfig);
            } catch (error) {
              console.log("🔍 loadCurrentIndexingState: Error checking mapping config:", error);
            }
            
            // Determine the appropriate step
            let targetStep = STEPS.INDEXING; // Default to indexing step
            
            if (savedFlowState && savedFlowState.hasStarted) {
              // Use saved step if it's valid
              targetStep = savedFlowState.activeStep;
              console.log("🔍 loadCurrentIndexingState: Using saved step:", targetStep);
            } else if (data.indexing_status === "completed" && hasMappingConfig) {
              // If indexing is completed and there's a mapping config, go to mapping step
              targetStep = STEPS.MAPPING;
              console.log("🔍 loadCurrentIndexingState: Indexing completed with mapping config, going to mapping step");
            } else if (data.indexing_status === "completed") {
              // If indexing is completed but no mapping config, go to mapping step to create one
              targetStep = STEPS.MAPPING;
              console.log("🔍 loadCurrentIndexingState: Indexing completed, going to mapping step");
            }
            
            setActiveStep(targetStep);
            console.log("🔍 loadCurrentIndexingState: Set hasStarted=true and activeStep=", targetStep);
            setIsLoadingState(false);
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
            
            // Check for saved flow state first
            const savedFlowState = getStoredFlowState();
            console.log("🔍 loadCurrentIndexingState: Saved flow state (old format):", savedFlowState);
            
            // Check if there's a mapping configuration saved
            let hasMappingConfig = false;
            try {
              const mappingResult = await client.get_mapping_config();
              hasMappingConfig = mappingResult?.result?.status === "success" && mappingResult.result.mapping_config;
              console.log("🔍 loadCurrentIndexingState: Has mapping config (old format):", hasMappingConfig);
            } catch (error) {
              console.log("🔍 loadCurrentIndexingState: Error checking mapping config (old format):", error);
            }
            
            // Determine the appropriate step
            let targetStep = STEPS.INDEXING; // Default to indexing step
            
            if (savedFlowState && savedFlowState.hasStarted) {
              // Use saved step if it's valid
              targetStep = savedFlowState.activeStep;
              console.log("🔍 loadCurrentIndexingState: Using saved step (old format):", targetStep);
            } else if (hasMappingConfig) {
              // If there's a mapping config, go to mapping step
              targetStep = STEPS.MAPPING;
              console.log("🔍 loadCurrentIndexingState: Has mapping config, going to mapping step (old format)");
            }
            
            setActiveStep(targetStep);
            console.log("🔍 loadCurrentIndexingState: Set hasStarted=true and activeStep=", targetStep, "(old format)");
            setIsLoadingState(false);
            return { success: true, hasExistingIndex: true };
          }
        }
        setIsLoadingState(false);
        return { success: true, hasExistingIndex: false };
      } catch (error) {
        setIsLoadingState(false);
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
    },
    [client, indexingActions, setHasStarted, setActiveStep]
  );

  const resetMetageo = useMemo(() => 
    async () => {
      if (!client) {
        console.error("🔍 resetMetageo: Client not available");
        return { success: false, error: "Client not available" };
      }
      try {
        console.log("🔍 resetMetageo: Starting complete reset...");
        console.log("🔍 resetMetageo: Client available:", !!client);
        console.log("🔍 resetMetageo: reset_metageo method available:", !!client.reset_metageo);
        
        // Call the reset operator
        const result = await client.reset_metageo();
        console.log("🔍 resetMetageo: Result from client.reset_metageo():", result);
        console.log("🔍 resetMetageo: Result.result:", result?.result);
        console.log("🔍 resetMetageo: Result.result.status:", result?.result?.status);
        
        if (result?.result?.status === "success") {
          // Reset all local state
          indexingActions.resetIndexing();
          setActiveStep(STEPS.INDEX_CONFIGURATION);
          setHasStarted(false);
          // Clear stored flow state
          clearStoredFlowState();
          
          console.log("🔍 resetMetageo: Successfully reset all metageo state");
          return { success: true, message: result.result.message };
        } else {
          console.error("🔍 resetMetageo: Reset failed:", result);
          return { success: false, error: result?.result?.message || "Reset failed" };
        }
      } catch (error) {
        console.error("🔍 resetMetageo: Error during reset:", error);
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error during reset",
        };
      }
    },
    [client, indexingActions, setActiveStep, setHasStarted]
  );

  const startOver = useMemo(() => 
    async () => {
      console.log("🔍 startOver: Calling resetMetageo...");
      return await resetMetageo();
    },
    [resetMetageo]
  );

  const actions = useMemo(() => ({
    start,
    next,
    back,
    goToStep,
    autoDetectBbox,
    calculateSampleDistribution,
    startIndexing,
    dropIndex,
    cancelIndexing,
    loadCurrentIndexingState,
    resetMetageo,
    startOver,
  }), [
    start,
    next,
    back,
    goToStep,
    autoDetectBbox,
    calculateSampleDistribution,
    startIndexing,
    dropIndex,
    cancelIndexing,
    loadCurrentIndexingState,
    resetMetageo,
    startOver,
  ]);

  const derived = useMemo(
    () => {
      const hasExistingIndex = 
        (indexingState.gridCells && indexingState.gridCells.length > 0) ||
        (indexingState.indexingStatus !== "idle" && indexingState.indexingStatus !== "cancelled");
      
      console.log("🔍 useMetageoFlow derived: hasExistingIndex =", hasExistingIndex);
      console.log("🔍 useMetageoFlow derived: indexingState.gridCells =", indexingState.gridCells);
      console.log("🔍 useMetageoFlow derived: indexingState.indexingStatus =", indexingState.indexingStatus);
      console.log("🔍 useMetageoFlow derived: indexingState.bbox =", indexingState.bbox);
      console.log("🔍 useMetageoFlow derived: activeStep =", activeStep);
      console.log("🔍 useMetageoFlow derived: hasStarted =", hasStarted);
      
      // Determine the effective step based on the current state
      let effectiveStep = activeStep;
      
      // If there's an existing index but we're on the configuration step, go to indexing
      if (hasExistingIndex && activeStep === STEPS.INDEX_CONFIGURATION) {
        effectiveStep = STEPS.INDEXING;
      }
      // If indexing is completed, allow progression to mapping step
      else if (indexingState.indexingStatus === "completed" && activeStep >= STEPS.INDEXING) {
        // Allow the user to progress to the next step (mapping)
        effectiveStep = activeStep;
      }
      
      const canGoNext = effectiveStep < STEPS.SEARCH_CLEANUP;
      console.log("🔍 useMetageoFlow derived: canGoNext =", canGoNext, "(effectiveStep =", effectiveStep, "<", STEPS.SEARCH_CLEANUP, ")");
      
      return {
        canGoNext,
        canGoBack: effectiveStep > STEPS.INDEX_CONFIGURATION,
        isFirstStep: effectiveStep === STEPS.INDEX_CONFIGURATION,
        isLastStep: effectiveStep === STEPS.SEARCH_CLEANUP,
        stepName:
          Object.keys(STEPS).find(
            (key) => STEPS[key as keyof typeof STEPS] === effectiveStep
          ) || "Unknown",
        hasExistingIndex,
        effectiveStep, // Add this to track the effective step
      };
    },
    [activeStep, indexingState]
  );

  return {
    state: { activeStep, hasStarted, isLoadingState },
    actions,
    derived,
  };
}
