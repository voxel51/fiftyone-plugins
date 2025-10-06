import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import { registerOperator } from "@fiftyone/operators";
import MetageoView from "./MetageoView";
import {
  IndexingStartedOperator,
  CellStatusUpdateOperator,
  IndexingProgressOperator,
  IndexingCompletedOperator,
  GridIndexingCompletedOperator,
  UpdateEnrichmentStateOperator,
  EnrichmentStartedOperator,
  EnrichmentProgressOperator,
  EnrichmentCompletedOperator,
} from "./operators";

// Function to register operators
function registerMetageoOperators() {
  try {
    // Register the operators
    registerOperator(IndexingStartedOperator, "@voxel51/metageo");
    registerOperator(CellStatusUpdateOperator, "@voxel51/metageo");
    registerOperator(IndexingProgressOperator, "@voxel51/metageo");
    registerOperator(IndexingCompletedOperator, "@voxel51/metageo");
    registerOperator(GridIndexingCompletedOperator, "@voxel51/metageo");
    registerOperator(UpdateEnrichmentStateOperator, "@voxel51/metageo");
    registerOperator(EnrichmentStartedOperator, "@voxel51/metageo");
    registerOperator(EnrichmentProgressOperator, "@voxel51/metageo");
    registerOperator(EnrichmentCompletedOperator, "@voxel51/metageo");
    console.log("Metageo operators registered successfully");
  } catch (e) {
    console.error("Error registering Metageo operators:", e);
  }
}

// Register operators
registerMetageoOperators();

registerComponent({
  name: "MetageoView",
  label: "Metageo",
  component: MetageoView as any,
  type: PluginComponentType.Component,
  activator: () => true,
});
