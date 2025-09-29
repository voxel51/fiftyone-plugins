import { useEffect } from "react";
import { useRecoilValue } from "recoil";
import { indexingStateAtom } from "../state/indexing.atom";
import { activeStepAtom, hasStartedAtom } from "../state/flow.atom";
import { mappingConfigAtom } from "../state/mapping.atom";
import {
  setStoredIndexingState,
  setStoredFlowState,
  setStoredMappingConfig,
  type FlowState,
} from "../utils/persistence";

/**
 * Hook that automatically persists state changes to localStorage
 * This ensures that state is preserved across browser sessions
 */
export function usePersistence() {
  const indexingState = useRecoilValue(indexingStateAtom);
  const activeStep = useRecoilValue(activeStepAtom);
  const hasStarted = useRecoilValue(hasStartedAtom);
  const mappingConfig = useRecoilValue(mappingConfigAtom);

  // Persist indexing state changes
  useEffect(() => {
    // Only persist if we have meaningful state (not just defaults)
    if (indexingState.bbox || indexingState.gridCells.length > 0 || indexingState.indexingStatus !== "idle") {
      setStoredIndexingState(indexingState);
    }
  }, [indexingState]);

  // Persist flow state changes
  useEffect(() => {
    // Only persist if we've started or are not on the first step
    if (hasStarted || activeStep > 0) {
      const flowState: FlowState = {
        activeStep,
        hasStarted,
      };
      setStoredFlowState(flowState);
    }
  }, [activeStep, hasStarted]);

  // Persist mapping config changes
  useEffect(() => {
    // Only persist if we have meaningful config (not just defaults)
    if (mappingConfig.geoField || mappingConfig.tagMappings.length > 0 || mappingConfig.fieldMappings.length > 0) {
      setStoredMappingConfig(mappingConfig);
    }
  }, [mappingConfig]);
}


