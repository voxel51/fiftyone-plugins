import * as fos from "@fiftyone/state";
import { useRecoilValue } from "recoil";
import { useCallback } from "react";
import { Button } from "@fiftyone/components";
import {
  types,
  useOperatorExecutor,
  Operator,
  OperatorConfig,
  registerOperator,
  executeOperator,
} from "@fiftyone/operators";

export function HelloWorld() {
  const executor = useOperatorExecutor("@voxel51/hello-world/count_samples");
  const onClickAlert = useCallback(() =>
    executeOperator("@voxel51/hello-world/show_alert")
  );
  const dataset = useRecoilValue(fos.dataset);

  if (executor.isLoading) return <h3>Loading...</h3>;
  if (executor.result) return <h3>Dataset size: {executor.result.count}</h3>;

  return (
    <>
      <h1>Hello, world!</h1>
      <h2>
        You are viewing the <strong>{dataset.name}</strong> dataset
      </h2>
      <Button onClick={() => executor.execute()}>Count samples</Button>
      <Button onClick={onClickAlert}>Show alert</Button>
    </>
  );
}

class AlertOperator extends Operator {
  get config() {
    return new OperatorConfig({
      name: "show_alert",
      label: "Show alert",
      unlisted: true,
    });
  }
  async execute() {
    alert(`Hello from plugin ${this.pluginName}`);
  }
}

registerOperator(AlertOperator, "@voxel51/hello-world");
