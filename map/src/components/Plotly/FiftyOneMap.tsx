
import './FiftyOneMap.css';

import React from 'react';
import Plotly from 'plotly.js-dist';
import mapboxgl from 'mapbox-gl';

const MAPBOX_ACCESS_TOKEN; // Add access token here;
const PLOTLY_CONTAINER_ID = "fiftyone-map-plotly-container";
const MAP_STYLES = {
    streets: "Streets",
    light: "Light",
    dark: "Dark",
    satellite: "Satellite",
    "satellite-streets": "Satellite Streets"
};

type FiftyOneMapProps = {
    sampleIDs: any, latLngs: any
};

type FiftyOneMapState = {
    selectedMapStyle: string
};

class FiftyOneMap extends React.Component<FiftyOneMapProps, FiftyOneMapState> {
    private sampleIDs: any[];
    private latLngs: number[];
    private markerColor: string;
    private markerSize: number;

    constructor({ sampleIDs, latLngs }) {
        super({ sampleIDs, latLngs });

        this.sampleIDs = sampleIDs;
        this.latLngs = latLngs;
        this.markerColor = 'red';
        this.markerSize = 10;

        this.state = {
            selectedMapStyle: Object.keys(MAP_STYLES)[0]
        };
    }

    componentDidMount() {
        let that = this;

        let data = [{
            type: "scattermapbox",
            lat: this.latLngs.map(latLng => latLng[0]),
            lon: this.latLngs.map(latLng => latLng[1]),
            marker: {
                color: that.markerColor,
                size: that.markerSize
            }
        }];

        let bounds = that.latLngs.reduce(
            (bounds, latLng) => bounds.extend([latLng[1], latLng[0]]),
            new mapboxgl.LngLatBounds()
        );
        let center = bounds.getCenter();

        let layout = {
            mapbox: {
                style: this.state.selectedMapStyle,
                center: {
                    lat: center.lat,
                    lon: center.lng
                },
                zoom: 2
            },
            margin: { r: 0, t: 0, b: 0, l: 0 }
        };


        Plotly.newPlot(PLOTLY_CONTAINER_ID, data, layout, {
            mapboxAccessToken: MAPBOX_ACCESS_TOKEN
        }).then(plot => {
            let map = plot._fullLayout.mapbox._subplot.map;

            map.once('zoomend', () => {
                let zoom = map.getZoom();
                plot._fullLayout.mapbox._subplot.viewInitial.zoom = zoom;
                Plotly.relayout(PLOTLY_CONTAINER_ID, { "mapbox.zoom": zoom });
            });

            map.fitBounds([
                bounds.getSouthWest(),
                bounds.getNorthEast()
            ], { padding: 15 });

            /// TODO: Bubble event for clicking a single point
            plot.on('plotly_click', data => {
                let sampleID = that.sampleIDs[data.points[0].pointIndex];
                console.log(`Clicked sample: ${sampleID}`);
            });

            /// TODO: Bubble event for lassoing points
            plot.on('plotly_selected', data => {
                let sampleIDs = data.points.map(pt => that.sampleIDs[pt.pointIndex]);
                console.log(`Selected ${sampleIDs.length} samples: ${sampleIDs}`);
            });
        });
    }

    mapStyleChange(style) {
        Plotly.relayout(PLOTLY_CONTAINER_ID, { "mapbox.style": style });
        this.setState({
            selectedMapStyle: style
        });
    }

    render() {
        return (
            <div>
                <div id="fiftyone-map-plotly-container"></div>
                <div>
                    {Object.keys(MAP_STYLES).map(key =>
                        <span key={key}>
                            <input
                                type="radio"
                                value={key}
                                checked={this.state.selectedMapStyle === key}
                                onChange={evt => this.mapStyleChange(evt.target.value)} />
                            {MAP_STYLES[key]}
                        </span>
                    )}
                </div>
            </div>
        )
    }
}

export default FiftyOneMap;
