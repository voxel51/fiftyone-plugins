import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import ExampleCustomView from "./ExampleCustomView";

registerComponent({
  name: "ExampleCustomView",
  label: "ExampleCustomView",
  component: ExampleCustomView,
  type: PluginComponentType.Component,
  activator: () => true,
});
