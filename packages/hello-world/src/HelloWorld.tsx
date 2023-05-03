import * as fop from '@fiftyone/plugins'
import * as fos from '@fiftyone/state'
import {useRecoilValue} from 'recoil'
import * as foa  from '@fiftyone/aggregations'
import { useEffect } from 'react'
import {Button} from '@fiftyone/components'
import {useOperatorExecutor, Operator, registerOperator} from '@fiftyone/operators'

export function HelloWorld() {
  const executor = useOperatorExecutor('@fiftyone/hello-world-plugin/count')

  if (executor.isLoading) return <h3>loading...</h3>

  if (executor.result) return <h3>Count: {executor.result.count}</h3>

  return <>
      <h1>Hello</h1>
      <Button onClick={() => executor.execute()}>Count</Button>
    </>
}

function Count({field}) {
  const dataset = useVal(fos.dataset)
  const view = useVal(fos.view)
  const filters = useVal(fos.filters)
  const [aggregate, result, loading] = foa.useAggregation({view, filters, dataset})

  useEffect(() => {
    const aggregations = [
      new foa.aggregations.Count({fieldOrExpr: field})
    ]
    aggregate(aggregations, dataset.name)
  }, [dataset])
  
  if (loading) return '...'

  return <strong>{result[0]}</strong>
}

class MyAlertOperator extends Operator {
  constructor() {
    super(
      'my-alert-operator',
      'My Alert Operator'
    )
    this.pluginName = name
  }
  async execute() {
    alert("hello world! from, " + this.pluginName)
  }
}

registerOperator(new MyAlertOperator())

