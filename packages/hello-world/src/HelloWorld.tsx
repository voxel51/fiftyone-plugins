import * as fop from '@fiftyone/plugins'
import * as fos from '@fiftyone/state'
import {useRecoilValue} from 'recoil'
import * as foa  from '@fiftyone/aggregations'
import { useEffect } from 'react'
import {Button} from '@fiftyone/components'
import {useOperatorExecutor} from '@fiftyone/operators'

import foo from '@fiftyone/operators'

export function HelloWorld() {
  const executor = foo.useOperatorExecutor('count')

  if (executor.isLoading) return <h4>Loading...</h4>
  if (executor.result) return <h4>Result: {executor.result.count}</h4>

  return (
    <div>
      <Button onClick={() => executor.execute()}>Execute</Button>
    </div>
  )
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


