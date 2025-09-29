import { useCallback, useMemo } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { indexingStateAtom } from "../state/indexing.atom";
import { useMetageoClient } from "./useMetageoClient.hook";
import { useMappingConfig } from "./useMappingConfig.hook";
import type { IndexingState, BoundingBox } from "../types";

export function useIndexingState() {
  console.log("🔍 useIndexingState: Hook starting...");

  let indexingState, setIndexingState;
  try {
    [indexingState, setIndexingState] = useRecoilState(indexingStateAtom);
  } catch (error) {
    console.error("🔍 useIndexingState: Error accessing atom:", error);
    // Return default state if atom access fails
    const defaultState = {
      bbox: null,
      gridTiles: 16,
      location: "",
      gridCells: [],
      executionMode: "immediate" as const,
      indexingStatus: "idle" as const,
      quadtreeCells: [],
      realSampleDistribution: {},
    };
    
    return {
      state: defaultState,
      actions: {
        setBbox: () => {},
        setLocation: () => {},
        setGridTiles: () => {},
        setGridCells: () => {},
        setIndexingStatus: () => {},
        setQuadtreeCells: () => {},
        setRealSampleDistribution: () => {},
        updateCellStatus: () => {},
        resetIndexing: () => {},
        clearDistribution: () => {},
      },
      derived: {
        hasBbox: false,
        hasGridCells: false,
        hasQuadtreeCells: false,
        isIndexing: false,
        isCompleted: false,
        isFailed: false,
        canStartIndexing: false,
        canCalculateDistribution: false,
        progress: 0,
      },
    };
  }
  
  console.log("🔍 useIndexingState: indexingState =", indexingState);
  console.log(
    "🔍 useIndexingState: indexingState.gridCells =",
    indexingState?.gridCells
  );
  console.log(
    "🔍 useIndexingState: indexingState.gridCells?.length =",
    indexingState?.gridCells?.length
  );

  const client = useMetageoClient();
  console.log("🔍 useIndexingState: client =", client);
  
  const { state: mappingConfig } = useMappingConfig();

  const actions = useMemo(
    () => ({
      setBbox: (bbox: BoundingBox | null) => {
        setIndexingState((prev) => ({ ...prev, bbox }));
      },

      setLocation: (location: string) => {
        setIndexingState((prev) => ({ ...prev, location }));
      },

      setGridTiles: (gridTiles: number) => {
        setIndexingState((prev) => ({ ...prev, gridTiles }));
      },

      setGridCells: (gridCells: IndexingState["gridCells"]) => {
        setIndexingState((prev) => ({ ...prev, gridCells }));
      },

      setIndexingStatus: (status: IndexingState["indexingStatus"]) => {
        setIndexingState((prev) => ({ ...prev, indexingStatus: status }));
      },

      setQuadtreeCells: (cells: IndexingState["quadtreeCells"]) => {
        setIndexingState((prev) => ({ ...prev, quadtreeCells: cells }));
      },

      setRealSampleDistribution: (distribution: { [cellId: string]: number }) => {
        setIndexingState((prev) => ({
          ...prev,
          realSampleDistribution: distribution,
        }));
      },

      updateCellStatus: (
        cellId: string,
        status: IndexingState["gridCells"][0]["status"],
        progress?: number,
        error?: string
      ) => {
        setIndexingState((prev) => ({
          ...prev,
          gridCells: prev.gridCells.map((cell) =>
            cell.id === cellId
              ? {
                  ...cell,
                  status,
                  progress: progress ?? cell.progress,
                  error,
                }
              : cell
          ),
        }));
      },

      resetIndexing: () => {
        setIndexingState((prev) => ({
          ...prev,
          gridCells: [],
          indexingStatus: "idle",
          quadtreeCells: [],
          realSampleDistribution: {},
        }));
      },

      clearDistribution: () => {
        setIndexingState((prev) => ({
          ...prev,
          gridCells: [],
          realSampleDistribution: {},
        }));
      },
    }),
    [setIndexingState]
  );

  const derived = useMemo(
    () => ({
      hasBbox: Boolean(indexingState.bbox),
      hasGridCells: Boolean(
        indexingState.gridCells && indexingState.gridCells.length > 0
      ),
      hasQuadtreeCells: Boolean(
        indexingState.quadtreeCells && indexingState.quadtreeCells.length > 0
      ),
      isIndexing: indexingState.indexingStatus === "running",
      isCompleted: indexingState.indexingStatus === "completed",
      isFailed: indexingState.indexingStatus === "failed",
      canStartIndexing: Boolean(
        indexingState.bbox &&
          mappingConfig.geoField &&
          indexingState.gridTiles > 0
      ),
      canCalculateDistribution: Boolean(
        indexingState.bbox &&
          mappingConfig.geoField &&
          indexingState.gridTiles > 0
      ),
      progress:
        indexingState.gridCells && indexingState.gridCells.length > 0
          ? indexingState.gridCells.filter(
              (cell) => cell.status === "completed"
            ).length / indexingState.gridCells.length
          : 0,
    }),
    [indexingState]
  );

  return {
    state: indexingState,
    actions,
    derived,
  };
}
