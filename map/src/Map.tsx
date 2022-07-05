import React from 'react'

import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";

import FiftyOneLeaflet from './components/Leaflet/FiftyOneMap';
import FiftyOneMapBox from './components/MapBox/FiftyOneMap';

import * as ReactDOMServer from 'react-dom/server';


function useGeoLocations() {
  const [loading, setLoading] = React.useState(true)
  const [data, setData] = React.useState(null)

  const jsonBody = {
    "filters": null,
    "dataset": "quickstart-geo",
    "sample_ids": null,
    "aggregations": [{
        "_cls": "fiftyone.core.aggregations.Values",
        "kwargs": [
            ["field_or_expr", "id"],
            ["expr", null],
            ["missing_value", null],
            ["unwind", false],
            ["_allow_missing", false],
            ["_big_result", true],
            ["_raw", false]
        ]
    },
    {
        "_cls": "fiftyone.core.aggregations.Values",
        "kwargs": [
            ["field_or_expr", "location.point.coordinates"],
            ["expr", null],
            ["missing_value", null],
            ["unwind", false],
            ["_allow_missing", false],
            ["_big_result", true],
            ["_raw", false]
        ]
    }]
  }

  React.useEffect(() => {
    fetch('http://localhost:5151/aggregate', {
      method: 'POST',
      body: JSON.stringify(jsonBody)
    })
    .then(resp => resp.json())
    .then(json => {
      console.log(json)
      const {aggregate} = json
      const [ids, locations] = aggregate
      const data = []
      for (let i = 0; i < ids.length; i++) {
        const location = locations[i]
        data.push({
          id: ids[0],
          location: {
            lat: location[0],
            lng: location[1]
          }
        })
      }
      setLoading(false)
      setData(data)
    })
  }, [])

  return {loading, data}
}

function Map() {
  const {loading, data} = useGeoLocations()

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