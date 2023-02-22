import * as fop from '@fiftyone/plugins'
import * as fos from '@fiftyone/state'
import {useRecoilValue as useVal} from 'recoil'
import * as foa  from '@fiftyone/aggregations'
import { useEffect } from 'react'
import {Button} from '@fiftyone/components'

export function HelloWorld() {
  const dataset = useVal(fos.dataset)

  const {fieldToCount} = fop.usePluginSettings('hello-world', {fieldToCount: 'filepath'})
  
  return (
    <h1>
      You are viewing the <strong>{dataset.name}</strong> dataset.
      It has <Count field={fieldToCount} /> samples. 
    </h1>
  )
}

function Count({field}) {
  const dataset = useVal(fos.dataset)
  const view = useVal(fos.view)
  const filters = useVal(fos.filters)
  const [aggregate, result, loading] = foa.useAggregation({view, filters, dataset})

  const load = () => {
    const aggregations = [
      new foa.aggregations.Count({fieldOrExpr: field})
    ]
    aggregate(aggregations, dataset.name)
  }
  
  if (!result) {
    return <Button onClick={load}>Click to Load</Button>
  }

  if (loading) return <Button disabled>Loading...</Button>

  return <strong>{result[0]}</strong>
}


