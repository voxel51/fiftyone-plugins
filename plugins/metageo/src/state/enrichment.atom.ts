import { atom } from "recoil";

export interface EnrichmentState {
  enrichmentId: string | null;
  status: "idle" | "running" | "completed" | "failed" | "cancelled";
  totalSamples: number;
  processedSamples: number;
  failedSamples: number;
  progress: number;
  startedAt: string | null;
  completedAt: string | null;
  error: string | null;
}

export const enrichmentStateAtom = atom<EnrichmentState>({
  key: "enrichmentState",
  default: {
    enrichmentId: null,
    status: "idle",
    totalSamples: 0,
    processedSamples: 0,
    failedSamples: 0,
    progress: 0,
    startedAt: null,
    completedAt: null,
    error: null,
  },
});
