import {
  Operator,
  OperatorConfig,
  registerOperator,
  ExecutionContext,
  types,
} from "@fiftyone/operators";
import fos from "@fiftyone/state";

class SkipSamples extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "example_skip_samples",
      label: "Example: skip samples",
    });
  }
  async resolveInput(): Promise<types.Property> {
    const inputs = new types.Object();
    inputs.str("count", { label: "Skip samples count", required: true });
    return new types.Property(inputs);
  }
  useHooks(): {} {
    return {
      setView: fos.useSetView(),
    };
  }
  async execute({ state, params, hooks }: ExecutionContext) {
    const view = await state.snapshot.getPromise(fos.view);
    const { count: countStr } = params;
    const count = Number(countStr);
    const newView = [
      ...view,
      {
        _cls: "fiftyone.core.stages.Skip",
        kwargs: [["skip", count]],
        _uuid: "skip_samples",
      },
    ];
    hooks.setView(newView);
  }
}

registerOperator(SkipSamples, "@voxel51/examples");
