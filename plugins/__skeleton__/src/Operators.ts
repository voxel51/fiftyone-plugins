import {
  Operator,
  OperatorConfig,
  registerOperator,
  types,
} from "@fiftyone/operators";
import fos from "@fiftyone/state";
import { useRecoilValue } from "recoil";

class Greet extends Operator {
  get config() {
    return new OperatorConfig({
      name: "{{PLUGIN_NAME}}_greet_js",
      label: "{{PLUGIN_NAME}}: Greet from JS",
    });
  }
  async execute({ hooks, params }) {
    const greetName = params.name;
    const datasetName = hooks.dataset.name;
    return {
      greeting: `Hi ${greetName}! You are viewing "${datasetName}" dataset`,
    };
  }
  async resolveInput() {
    const inputs = new types.Object();
    inputs.str("name");
    return new types.Property(inputs);
  }
  async resolveOutput() {
    const outputs = new types.Object();
    outputs.str("greeting");
    return new types.Property(outputs);
  }
  //  Uncomment class method below to add a placement for this operator
  // async resolvePlacement() {
  //   return new types.Placement(
  //     types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
  //     new types.Button({
  //       label: "{{PLUGIN_NAME}}: Greet from JS",
  //       icon: "/assets/icon.svg",
  //     })
  //   );
  // }
  useHooks(): object {
    const dataset = useRecoilValue(fos.dataset);
    return { dataset };
  }
}

registerOperator(Greet, "{{PLUGIN_NAME}}");
