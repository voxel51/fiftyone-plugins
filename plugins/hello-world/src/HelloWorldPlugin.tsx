import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import { HelloWorld } from "./HelloWorld";

registerComponent({
  name: "HelloWorld",
  label: "Hello World",
  component: HelloWorld,
  type: PluginComponentType.Plot,
  activator: myActivator,
});

function myActivator({ dataset }) {
  // return dataset.name === 'quickstart'
  return true;
}
