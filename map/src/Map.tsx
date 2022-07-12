import React from 'react'

import FiftyOnePlotly from './components/Plotly/FiftyOneMap';

import * as foa from '@fiftyone/aggregations'

function useGeoLocations({ dataset, filters, view }) {
  console.log({ dataset, filters, view })
  const [aggregate, points, loading] = foa.useAggregation({ dataset, filters, view })

  React.useEffect(() => {
    aggregate([
      new foa.aggregations.Values({
        fieldOrExpr: 'id'
      }),
      new foa.aggregations.Values({
        fieldOrExpr: 'location.point.coordinates'
      }),
    ], dataset.name)
  }, [dataset, filters, view])


  let data;
  if (points && points.length) {
    console.log({ points })
    let [sampleIDs, latLngs] = points
    data = { sampleIDs, latLngs }
  }

  return { loading, data }
}

function Map({ dataset, filters, view }) {
  const { loading, data } = useGeoLocations({ dataset, filters, view })

  if (loading) return <h3>Loading....</h3>

  return (
    <div>
      <FiftyOnePlotly sampleIDs={data.sampleIDs} latLngs={data.latLngs} />
    </div>
  );
}

export default Map;