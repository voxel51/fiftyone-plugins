import React from 'react'

import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";

import FiftyOneLeaflet from './components/Leaflet/FiftyOneMap';
import FiftyOneMapBox from './components/MapBox/FiftyOneMap';

import * as ReactDOMServer from 'react-dom/server';
import * as fop from '@fiftyone/plugins'
import * as foa from '@fiftyone/aggregations'

function useGeoLocations({dataset, filters, view}) {
  const [aggregate, points, loading] = foa.useAggregation({dataset, filters, view})

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

  const data = []
  if (points && points.length) {
    const [ids, locations] = points
    for (let i = 0; i < ids.length; i++) {
      const location = locations[i]
      data.push({
        id: ids[i],
        location: {
          lat: location[1],
          lng: location[0]
        }
      })
    }
  }

  return {loading, data}
}

function Map({dataset, filters, view}) {
  const {loading, data} = useGeoLocations({dataset, filters, view})

  if (loading) return <h3>Loading....</h3>

  function sampleClick(properties) {
    let msg = `Clicked ID: ${properties.id}:`;
    console.log(properties)
    alert(msg)
  }

  function sampleGroup(samples) {
    samples.forEach(sample => {
      console.log(
        `Selected:\n - Sample ID: ${sample.sampleID}\n - Date${sample.date}:`
      )
    });
    alert(`Selected ${samples.length} samples`)
  }


  const sampleTooltip = datum => {
    return ReactDOMServer.renderToStaticMarkup((
      <div>
        <div>
          Sample ID: {datum.sampleID}
        </div>
        <div>
          Date: {datum.date.toString()}
        </div>
      </div>
    ))
  }


  return (
    <div>
      <FiftyOneMapBox data={data} onClick={sampleClick} onGroup={sampleGroup} tooltip={sampleTooltip} />
    </div>
  );
}

export default Map;