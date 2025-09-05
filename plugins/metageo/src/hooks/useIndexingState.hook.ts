import { useCallback, useMemo } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { indexingStateAtom } from "../state/indexing.atom";
import { useMetageoClient } from "./useMetageoClient.hook";
import type { IndexingState, BoundingBox } from "../types";

export function useIndexingState() {
  console.log("🔍 useIndexingState: Hook starting...");

  const [indexingState, setIndexingState] = useRecoilState(indexingStateAtom);
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

  const actions = useMemo(
    () => ({
      setBbox: useCallback(
        (bbox: BoundingBox | null) => {
          setIndexingState((prev) => ({ ...prev, bbox }));
        },
        [setIndexingState]
      ),

      setLocation: useCallback(
        (location: string) => {
          setIndexingState((prev) => ({ ...prev, location }));
        },
        [setIndexingState]
      ),

      setGridTiles: useCallback(
        (gridTiles: number) => {
          setIndexingState((prev) => ({ ...prev, gridTiles }));
        },
        [setIndexingState]
      ),

      setGridCells: useCallback(
        (gridCells: IndexingState["gridCells"]) => {
          setIndexingState((prev) => ({ ...prev, gridCells }));
        },
        [setIndexingState]
      ),

      setIndexingStatus: useCallback(
        (status: IndexingState["indexingStatus"]) => {
          setIndexingState((prev) => ({ ...prev, indexingStatus: status }));
        },
        [setIndexingState]
      ),

      setQuadtreeCells: useCallback(
        (cells: IndexingState["quadtreeCells"]) => {
          setIndexingState((prev) => ({ ...prev, quadtreeCells: cells }));
        },
        [setIndexingState]
      ),

      setRealSampleDistribution: useCallback(
        (distribution: { [cellId: string]: number }) => {
          setIndexingState((prev) => ({
            ...prev,
            realSampleDistribution: distribution,
          }));
        },
        [setIndexingState]
      ),

      updateCellStatus: useCallback(
        (
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
        [setIndexingState]
      ),

      resetIndexing: useCallback(() => {
        setIndexingState((prev) => ({
          ...prev,
          gridCells: [],
          indexingStatus: "idle",
          quadtreeCells: [],
          realSampleDistribution: {},
        }));
      }, [setIndexingState]),

      clearDistribution: useCallback(() => {
        setIndexingState((prev) => ({
          ...prev,
          gridCells: [],
          realSampleDistribution: {},
        }));
      }, [setIndexingState]),
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
          indexingState.location &&
          indexingState.gridTiles > 0
      ),
      canCalculateDistribution: Boolean(
        indexingState.bbox &&
          indexingState.location &&
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
