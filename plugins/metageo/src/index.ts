import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import { registerOperator } from "@fiftyone/operators";
import MetageoView from "./MetageoView";
import {
  IndexingStartedOperator,
  CellStatusUpdateOperator,
  IndexingProgressOperator,
  IndexingCompletedOperator,
  GridIndexingCompletedOperator,
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
