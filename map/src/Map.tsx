import React from 'react'

import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";

// import FiftyOneLeaflet from './components/Leaflet/FiftyOneMap';
// import FiftyOneMapBox from './components/MapBox/FiftyOneMap';
import FiftyOnePlotly from './components/Plotly/FiftyOneMap';

import * as ReactDOMServer from 'react-dom/server';
import * as fop from '@fiftyone/plugins'

function useGeoLocations({ dataset, filters, view }) {
  console.log({ dataset, filters, view })
  const [aggregate, points, loading] = fop.useAggregation({ dataset, filters, view })

  React.useEffect(() => {
    aggregate([
      new fop.aggregations.Values({
        fieldOrExpr: 'id',
        // @ts-ignore
        _big_result: true
      }),
      new fop.aggregations.Values({
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