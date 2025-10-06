import {
  Operator,
  OperatorConfig,
  ExecutionContext,
} from "@fiftyone/operators";
import { useRecoilState, useSetRecoilState } from "recoil";
import { indexingStateAtom } from "./state/indexing.atom";
import { enrichmentStateAtom } from "./state/enrichment.atom";
import type { CellStatus } from "./types";

// Operator to handle indexing started event
export class IndexingStartedOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "indexing_started",
      label: "Indexing Started",
      unlisted: true,
    });
  }

  useHooks() {
    const setIndexingState = useSetRecoilState(indexingStateAtom);
    return { setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const { indexing_id, total_cells, active_cells, status } = params;

    console.log("IndexingStartedOperator: Indexing started", {
      indexing_id,
      total_cells,
      active_cells,
    });

    hooks.setIndexingState((prev) => ({
      ...prev,
      indexingStatus: "running",
    }));
  }
}

// Operator to handle cell status updates
export class CellStatusUpdateOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "cell_status_update",
      label: "Cell Status Update",
      unlisted: true,
    });
  }

  useHooks() {
    const [indexingState, setIndexingState] = useRecoilState(indexingStateAtom);
    return { indexingState, setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const { cell_id, status, progress, osm_features, error } = params;

    console.log(
      `CellStatusUpdateOperator: Updating cell ${cell_id} to status ${status} with ${osm_features} features`
    );

    hooks.setIndexingState((prev) => {
      const updatedGridCells = prev.gridCells.map((cell) => {
        if (cell.id === cell_id) {
          return {
            ...cell,
            status: status as CellStatus,
            progress: progress || 0,
            error: error || undefined,
            osm_features: osm_features ? [osm_features] : undefined,
          };
        }
        return cell;
      });

      return {
        ...prev,
        gridCells: updatedGridCells,
      };
    });
  }
}

// Operator to handle indexing progress updates
export class IndexingProgressOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "indexing_progress",
      label: "Indexing Progress",
      unlisted: true,
    });
  }

  useHooks() {
    const setIndexingState = useSetRecoilState(indexingStateAtom);
    return { setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const {
      indexing_id,
      completed_cells,
      failed_cells,
      total_cells,
      total_features,
      progress,
    } = params;

    console.log("IndexingProgressOperator: Progress update", {
      indexing_id,
      completed_cells,
      failed_cells,
      total_cells,
      total_features,
      progress,
    });

    // For now, just log the progress since the IndexingState doesn't have these fields
    // The UI can calculate progress from the gridCells array
  }
}

// Operator to handle indexing completed event
export class IndexingCompletedOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "indexing_completed",
      label: "Indexing Completed",
      unlisted: true,
    });
  }

  useHooks() {
    const setIndexingState = useSetRecoilState(indexingStateAtom);
    return { setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const {
      indexing_id,
      completed_cells,
      failed_cells,
      total_cells,
      total_features,
      status,
    } = params;

    console.log("IndexingCompletedOperator: Indexing completed", {
      indexing_id,
      completed_cells,
      failed_cells,
      total_cells,
      total_features,
      status,
    });

    hooks.setIndexingState((prev) => ({
      ...prev,
      indexingStatus: "completed",
    }));
  }
}

// Operator to handle grid indexing completion
export class GridIndexingCompletedOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "grid_indexing_completed",
      label: "Grid Indexing Completed",
      unlisted: true,
    });
  }

  useHooks() {
    const setIndexingState = useSetRecoilState(indexingStateAtom);
    return { setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const {
      indexing_id,
      completed_cells,
      failed_cells,
      rate_limited_cells,
      total_features,
      status,
    } = params;

    console.log("GridIndexingCompletedOperator: Grid indexing completed!");
    console.log("Completed cells:", completed_cells);
    console.log("Failed cells:", failed_cells);
    console.log("Rate limited cells:", rate_limited_cells);
    console.log("Total features:", total_features);

    hooks.setIndexingState((prev) => ({
      ...prev,
      indexingStatus: "completed",
    }));
  }
}

// Browser operator to update enrichment state - called by Python WatchEnrichmentOperator
export class UpdateEnrichmentStateOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "update_enrichment_state",
      label: "Update Enrichment State",
      unlisted: true,
    });
  }

  useHooks() {
    const setEnrichmentState = useSetRecoilState(enrichmentStateAtom);
    return { setEnrichmentState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const {
      enrichment_id,
      status,
      total_samples,
      processed_samples,
      failed_samples,
      progress,
      error,
    } = params;

    console.log("🔍 UpdateEnrichmentStateOperator: Updating enrichment state", {
      enrichment_id,
      status,
      total_samples,
      processed_samples,
      failed_samples,
      progress,
      error,
    });

    hooks.setEnrichmentState((prev) => ({
      ...prev,
      enrichmentId: enrichment_id || prev.enrichmentId,
      status: status || prev.status,
      totalSamples:
        total_samples !== undefined ? total_samples : prev.totalSamples,
      processedSamples:
        processed_samples !== undefined
          ? processed_samples
          : prev.processedSamples,
      failedSamples:
        failed_samples !== undefined ? failed_samples : prev.failedSamples,
      progress: progress !== undefined ? progress : prev.progress,
      startedAt:
        status === "running" && !prev.startedAt
          ? new Date().toISOString()
          : prev.startedAt,
      completedAt:
        status === "completed" || status === "failed" || status === "cancelled"
          ? new Date().toISOString()
          : prev.completedAt,
      error: error || null,
    }));
  }
}

// Operator to handle enrichment started event
export class EnrichmentStartedOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "enrichment_started",
      label: "Enrichment Started",
      unlisted: true,
    });
  }

  useHooks() {
    const setEnrichmentState = useSetRecoilState(enrichmentStateAtom);
    return { setEnrichmentState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const { enrichment_id, total_samples, status } = params;

    console.log("🔍 EnrichmentStartedOperator: Enrichment started", {
      enrichment_id,
      total_samples,
    });

    hooks.setEnrichmentState((prev) => ({
      ...prev,
      enrichmentId: enrichment_id,
      status: "running",
      totalSamples: total_samples,
      processedSamples: 0,
      failedSamples: 0,
      progress: 0,
      startedAt: new Date().toISOString(),
      completedAt: null,
      error: null,
    }));
  }
}

// Operator to handle enrichment progress updates
export class EnrichmentProgressOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "enrichment_progress",
      label: "Enrichment Progress",
      unlisted: true,
    });
  }

  useHooks() {
    const setEnrichmentState = useSetRecoilState(enrichmentStateAtom);
    return { setEnrichmentState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const {
      enrichment_id,
      processed_samples,
      failed_samples,
      total_samples,
      progress,
    } = params;

    console.log("🔍 EnrichmentProgressOperator: Progress update", {
      enrichment_id,
      processed_samples,
      failed_samples,
      total_samples,
      progress,
    });

    hooks.setEnrichmentState((prev) => ({
      ...prev,
      processedSamples:
        processed_samples !== undefined
          ? processed_samples
          : prev.processedSamples,
      failedSamples:
        failed_samples !== undefined ? failed_samples : prev.failedSamples,
      totalSamples:
        total_samples !== undefined ? total_samples : prev.totalSamples,
      progress: progress !== undefined ? progress : prev.progress,
    }));
  }
}

// Operator to handle enrichment completed event
export class EnrichmentCompletedOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "enrichment_completed",
      label: "Enrichment Completed",
      unlisted: true,
    });
  }

  useHooks() {
    const setEnrichmentState = useSetRecoilState(enrichmentStateAtom);
    return { setEnrichmentState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const {
      enrichment_id,
      processed_samples,
      failed_samples,
      total_samples,
      status,
      error,
    } = params;

    console.log("🔍 EnrichmentCompletedOperator: Enrichment completed", {
      enrichment_id,
      processed_samples,
      failed_samples,
      total_samples,
      status,
      error,
    });

    hooks.setEnrichmentState((prev) => ({
      ...prev,
      status: status,
      processedSamples:
        processed_samples !== undefined
          ? processed_samples
          : prev.processedSamples,
      failedSamples:
        failed_samples !== undefined ? failed_samples : prev.failedSamples,
      totalSamples:
        total_samples !== undefined ? total_samples : prev.totalSamples,
      progress: status === "completed" ? 100 : prev.progress,
      completedAt: new Date().toISOString(),
      error: error || null,
    }));
  }
}
