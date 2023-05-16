import * as fos from '@fiftyone/state'
import {useRecoilValue} from 'recoil'
import {useCallback} from 'react'
import {Button} from '@fiftyone/components'
import {types, useOperatorExecutor, Operator, OperatorConfig, registerOperator, executeOperator} from '@fiftyone/operators'

export function HelloWorld() {
  const executor = useOperatorExecutor('@fiftyone/hello-world-plugin/count')
  const onClickAlert = useCallback(executeOperator);
  const dataset = useRecoilValue(fos.dataset);

  if (executor.isLoading) return <h3>loading...</h3>
  if (executor.result) return <h3>Count: {executor.result.count}</h3>

  return <>
      <h1>Hello, world!</h1>
      <h2>You are viewing the <strong>{dataset.name}</strong> dataset!</h2>
      <Button onClick={() => executor.execute()}>Count</Button>
      <Button onClick={onClickAlert}>Alert</Button>
    </>
}

class MyAlertOperator extends Operator {
  get config() {
    return new OperatorConfig({
      name: 'alert',
      label: 'My Alert Operator',
    })
  }
  async execute() {
    alert("Hello, world... plugin:" + this.pluginName)
  }
}

registerOperator(MyAlertOperator, "@fiftyone/hello-world-plugin")
