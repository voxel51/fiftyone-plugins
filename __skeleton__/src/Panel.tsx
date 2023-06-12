import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import * as fos from "@fiftyone/state";
import { useRecoilValue } from "recoil";

export function Panel() {
  const dataset = useRecoilValue(fos.dataset);
  return (
    <h1>
      You are viewing the <strong>{dataset.name}</strong> dataset.
    </h1>
  );
}

registerComponent({
  name: "{{PLUGIN_NAME}}",
  label: "{{PLUGIN_NAME}}",
  component: Panel,
  type: PluginComponentType.Panel,
  activator,
});

function activator({ dataset }) {
  return true;
}
