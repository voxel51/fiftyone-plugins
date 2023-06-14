import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import { Plugin } from "./Plugin";

registerComponent({
  name: "{{PLUGIN_NAME}}",
  label: "{{PLUGIN_NAME}}",
  component: Plugin,
  type: PluginComponentType.Panel,
  activator,
});

function activator({ dataset }) {
  return true;
}
