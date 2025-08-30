import {
  Operator,
  OperatorConfig,
  ExecutionContext,
} from "@fiftyone/operators";
import { useRecoilState, useSetRecoilState } from "recoil";
import { metageoIndexingState } from "./state";

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
    const setIndexingState = useSetRecoilState(metageoIndexingState);
    return { setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const { indexing_id, total_cells, active_cells, status } = params;

    hooks.setIndexingState((prev) => ({
      ...prev,
      status: "running",
      indexing_id,
      total_cells,
      active_cells,
      started_at: new Date().toISOString(),
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
    const [indexingState, setIndexingState] =
      useRecoilState(metageoIndexingState);
    return { indexingState, setIndexingState };
  }

  async execute({ hooks, params }: ExecutionContext) {
    const { cell_id, status, progress, osm_features, error } = params;

    console.log(
      `CellStatusUpdateOperator: Updating cell ${cell_id} to status ${status} with ${osm_features} features`
    );

    hooks.setIndexingState((prev) => {
      const updatedCells = { ...prev.cells };

      updatedCells[cell_id] = {
        id: cell_id,
        status: status as
          | "idle"
          | "running"
          | "completed"
          | "failed"
          | "rate_limited"
          | "empty",
        progress: progress || 0,
        osm_features: osm_features || 0,
        error: error || null,
        updated_at: new Date().toISOString(),
      };

      return {
        ...prev,
        cells: updatedCells,
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
    const setIndexingState = useSetRecoilState(metageoIndexingState);
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

    hooks.setIndexingState((prev) => ({
      ...prev,
      progress: progress || 0,
      completed_cells: completed_cells || 0,
      failed_cells: failed_cells || 0,
      total_features: total_features || 0,
      last_updated: new Date().toISOString(),
    }));
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
    const setIndexingState = useSetRecoilState(metageoIndexingState);
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

    hooks.setIndexingState((prev) => ({
      ...prev,
      status: "completed",
      completed_cells: completed_cells || 0,
      failed_cells: failed_cells || 0,
      total_features: total_features || 0,
      completed_at: new Date().toISOString(),
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
    const setIndexingState = useSetRecoilState(metageoIndexingState);
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
      status: "completed",
      completed_cells: completed_cells || 0,
      failed_cells: failed_cells || 0,
      rate_limited_cells: rate_limited_cells || 0,
      total_features: total_features || 0,
      completed_at: new Date().toISOString(),
    }));
  }
}
