import { atom } from "recoil";
import type { IndexingState } from "../types";

export const indexingStateAtom = atom<IndexingState>({
  key: "metageo/indexing",
  default: {
    bbox: null,
    gridTiles: 16,
    location: "",
    gridCells: [],
    executionMode: "immediate",
    indexingStatus: "idle",
    quadtreeCells: [],
    realSampleDistribution: {},
  },
});
