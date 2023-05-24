import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import ExampleCustomView from "./ExampleCustomView";
import "./operators";

registerComponent({
  name: "ExampleCustomView",
  label: "ExampleCustomView",
  component: ExampleCustomView,
  type: PluginComponentType.Component,
  activator: () => true,
});
