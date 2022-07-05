import React from 'react'

import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";

import FiftyOnePlotly from './components/Plotly/FiftyOneMap';

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
        const { aggregate } = json
        const [sampleIDs, latLngs] = aggregate
        const data = { sampleIDs, latLngs }
        setLoading(false)
        setData(data)
      })
  }, [])

  return { loading, data }
}

function Map() {
  const { loading, data } = useGeoLocations()

  if (loading) return <h3>Loading....</h3>

  return (
    <div>
      <FiftyOnePlotly sampleIDs={data.sampleIDs} latLngs={data.latLngs} />
    </div>
  );
}

export default Map;