import { useCallback, useMemo, useEffect } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { enrichmentStateAtom } from "../state/enrichment.atom";
import { useMetageoClient } from "./useMetageoClient.hook";
import type { EnrichmentState } from "../state/enrichment.atom";

export function useEnrichmentState() {
  console.log("🔍 useEnrichmentState: Hook starting...");

  let enrichmentState, setEnrichmentState;
  try {
    [enrichmentState, setEnrichmentState] = useRecoilState(enrichmentStateAtom);
  } catch (error) {
    console.error("🔍 useEnrichmentState: Error accessing atom:", error);
    // Return default state if atom access fails
    const defaultState = {
      enrichmentId: null,
      status: "idle" as const,
      totalSamples: 0,
      processedSamples: 0,
      failedSamples: 0,
      progress: 0,
      startedAt: null,
      completedAt: null,
      error: null,
    };

    return {
      state: defaultState,
      actions: {
        startEnrichment: () => {},
        cancelEnrichment: () => {},
        resetEnrichment: () => {},
        loadCurrentEnrichmentState: () => {},
      },
    };
  }

  console.log("🔍 useEnrichmentState: enrichmentState =", enrichmentState);

  const client = useMetageoClient();
  console.log("🔍 useEnrichmentState: client =", client);

  const actions = useMemo(
    () => ({
      startEnrichment: async (enrichmentId: string, totalSamples: number) => {
        console.log(
          "🔍 useEnrichmentState: Starting enrichment",
          enrichmentId,
          totalSamples
        );

        if (!client) {
          console.error("🔍 useEnrichmentState: No client available");
          return;
        }

        try {
          // Start the watch enrichment operator
          await client.watch_enrichment({
            enrichment_id: enrichmentId,
            total_samples: totalSamples,
          });

          // Note: Don't update local state here - let the UpdateEnrichmentStateOperator handle it
          // This prevents race conditions where local state overwrites the correct values from Python

          console.log("🔍 useEnrichmentState: Enrichment started successfully");
        } catch (error) {
          console.error(
            "🔍 useEnrichmentState: Error starting enrichment:",
            error
          );
          setEnrichmentState((prev) => ({
            ...prev,
            status: "failed",
            error: error instanceof Error ? error.message : String(error),
          }));
        }
      },

      cancelEnrichment: async () => {
        console.log("🔍 useEnrichmentState: Cancelling enrichment");

        if (!client) {
          console.error("🔍 useEnrichmentState: No client available");
          return;
        }

        try {
          await client.cancel_enrichment();

          setEnrichmentState((prev) => ({
            ...prev,
            status: "cancelled",
            completedAt: new Date().toISOString(),
          }));

          console.log(
            "🔍 useEnrichmentState: Enrichment cancelled successfully"
          );
        } catch (error) {
          console.error(
            "🔍 useEnrichmentState: Error cancelling enrichment:",
            error
          );
        }
      },

      resetEnrichment: () => {
        console.log("🔍 useEnrichmentState: Resetting enrichment state");
        setEnrichmentState({
          enrichmentId: null,
          status: "idle",
          totalSamples: 0,
          processedSamples: 0,
          failedSamples: 0,
          progress: 0,
          startedAt: null,
          completedAt: null,
          error: null,
        });
      },

      loadCurrentEnrichmentState: async () => {
        console.log("🔍 useEnrichmentState: Loading current enrichment state");

        if (!client) {
          console.error("🔍 useEnrichmentState: No client available");
          return;
        }

        try {
          const result = await client.get_enrichment_status();
          console.log(
            "🔍 useEnrichmentState: Backend enrichment status:",
            result
          );

          if (
            result?.result?.status === "success" &&
            result.result.enrichment_job
          ) {
            const job = result.result.enrichment_job;
            setEnrichmentState((prev) => ({
              ...prev,
              enrichmentId: job.get("enrichment_id") || null,
              status: job.get("status") || "idle",
              totalSamples: job.get("total_samples") || 0,
              processedSamples: job.get("processed_samples") || 0,
              failedSamples: job.get("failed_samples") || 0,
              progress: job.get("progress_percent") || 0,
              startedAt: job.get("started_at") || null,
              completedAt: job.get("completed_at") || null,
              error: job.get("error") || null,
            }));
          }
        } catch (error) {
          console.error(
            "🔍 useEnrichmentState: Error loading enrichment state:",
            error
          );
        }
      },

      updateEnrichmentProgress: (progress: Partial<EnrichmentState>) => {
        console.log(
          "🔍 useEnrichmentState: Updating enrichment progress:",
          progress
        );
        setEnrichmentState((prev) => ({
          ...prev,
          ...progress,
        }));
      },
    }),
    [client, setEnrichmentState]
  );

  // Load current enrichment state on mount
  useEffect(() => {
    console.log(
      "🔍 useEnrichmentState: useEffect triggered, loading current state"
    );
    actions.loadCurrentEnrichmentState();
  }, []); // Remove dependency to prevent infinite loop

  // Note: Polling removed - now using direct browser operator calls from Python WatchEnrichmentOperator

  return {
    state: enrichmentState,
    actions,
  };
}
