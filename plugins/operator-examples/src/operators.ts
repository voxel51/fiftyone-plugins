import {
  Operator,
  OperatorConfig,
  registerOperator,
  useOperatorExecutor,
  types,
} from "@fiftyone/operators";

class OpenEmbeddingsPanel extends Operator {
  get config() {
    return new OperatorConfig({
      name: "example_open_embeddings_panel",
      label: "Example: open Embeddings panel",
    });
  }
  useHooks(): object {
    const openPanelOperator = useOperatorExecutor("open_panel");
    return { openPanelOperator };
  }
  async resolvePlacement() {
    return new types.Placement(
      types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
      new types.Button({
        label: "Open Embeddings Panel",
        icon: "/assets/embeddings.svg",
      })
    );
  }
  async execute({ hooks }) {
    const { openPanelOperator } = hooks;
    openPanelOperator.execute({
      name: "Embeddings",
      isActive: true,
      layout: "horizontal",
    });
  }
}

registerOperator(OpenEmbeddingsPanel, "@voxel51/operator-examples");
