import { atom } from "recoil";

export interface IndexingState {
  status:
    | "idle"
    | "running"
    | "completed"
    | "failed"
    | "cancelled"
    | "rate_limited";
  indexing_id?: string;
  total_cells?: number;
  active_cells?: number;
  completed_cells?: number;
  failed_cells?: number;
  rate_limited_cells?: number;
  total_features?: number;
  progress?: number;
  cells: { [cellId: string]: CellState };
  started_at?: string;
  completed_at?: string;
  last_updated?: string;
}

export interface CellState {
  id: string;
  status:
    | "idle"
    | "running"
    | "completed"
    | "failed"
    | "rate_limited"
    | "empty";
  progress: number;
  osm_features: number;
  error: string | null;
  updated_at: string;
}

export const metageoIndexingState = atom<IndexingState>({
  key: "metageoIndexingState",
  default: {
    status: "idle",
    cells: {},
  },
});
