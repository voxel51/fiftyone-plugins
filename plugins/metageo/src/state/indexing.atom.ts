import { atom } from "recoil";
import type { IndexingState } from "../types";
import { getStoredIndexingState } from "../utils/persistence";

const defaultIndexingState: IndexingState = {
  bbox: null,
  gridTiles: 16,
  location: "",
  gridCells: [],
  executionMode: "immediate",
  indexingStatus: "idle",
  quadtreeCells: [],
  realSampleDistribution: {},
};

export const indexingStateAtom = atom<IndexingState>({
  key: "metageo/indexing",
  default: getStoredIndexingState() || defaultIndexingState,
});
