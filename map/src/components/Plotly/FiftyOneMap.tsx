import './FiftyOneMap.css';

import mapboxgl from 'mapbox-gl';
import Plotly from 'plotly.js-dist';
import React from 'react';

const MAPBOX_ACCESS_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
const PLOTLY_CONTAINER_ID = "fiftyone-plotly-map";
const MAP_STYLES = {
    streets: "Streets",
    light: "Light",
    dark: "Dark",
    satellite: "Satellite",
    "satellite-streets": "Satellite Streets"
};

type FiftyOneMapProps = {
    sampleIDs: any,
    latLngs: any
};

type FiftyOneMapState = {
    selectedMapStyle: string
};

class FiftyOneMap extends React.Component<FiftyOneMapProps, FiftyOneMapState> {
    private sampleIDs: any[];
    private latLngs: number[];
    private markerColor: string;
    private markerSize: number;

    constructor(props) {
        super(props);

        this.sampleIDs = props.sampleIDs;
        this.latLngs = props.latLngs;
        this.markerColor = 'red';
        this.markerSize = 10;

        this.state = {
            selectedMapStyle: Object.keys(MAP_STYLES)[0]
        };
    }


    draw() {
        let bounds = this.latLngs.reduce(
            (bounds, latLng) => bounds.extend([latLng[1], latLng[0]]),
            new mapboxgl.LngLatBounds()
        );
        let center = bounds.getCenter();

        let data = [{
            type: "scattermapbox",
            lat: this.latLngs.map(latLng => latLng[0]),
            lon: this.latLngs.map(latLng => latLng[1]),
            marker: {
                color: this.markerColor,
                size: this.markerSize
            }
        }];

        let layout = {
            mapbox: {
                style: this.state.selectedMapStyle,
                center: {
                    lat: center.lat,
                    lon: center.lng
                }
            },
            margin: { r: 0, t: 0, b: 0, l: 0 }
        };

        var config = {
            mapboxAccessToken: MAPBOX_ACCESS_TOKEN
        };

        var that = this;
        Plotly
            .newPlot(PLOTLY_CONTAINER_ID, data, layout, config)
            .then(plot => {
                let map = plot._fullLayout.mapbox._subplot.map;

                map.once('zoomend', () => {
                    let zoom = map.getZoom();
                    plot._fullLayout.mapbox._subplot.viewInitial.zoom = zoom;
                    Plotly.relayout(PLOTLY_CONTAINER_ID, { "mapbox.zoom": zoom });
                });

                map.fitBounds([
                    bounds.getNorthEast(),
                    bounds.getSouthWest()
                ], { padding: 20 });

                /// TODO: Bubble event for clicking a single point
                plot.on('plotly_click', event => {
                    let sampleID = that.sampleIDs[event.points[0].pointIndex];
                    console.log(`Clicked sample: ${sampleID}`);
                });

                /// TODO: Bubble event for lassoing points
                plot.on('plotly_selected', event => {
                    let sampleIDs = event.points.map(point => that.sampleIDs[point.pointIndex]);
                    console.log(`Selected ${sampleIDs.length} samples: ${sampleIDs}`);
                });
            });
    }

    componentDidMount() {
        this.draw()
    }

    mapStyleChange(style: string) {
        Plotly.relayout(PLOTLY_CONTAINER_ID, { "mapbox.style": style });
        this.setState({
            selectedMapStyle: style
        });
    }

    render() {
        return (
            <div id="fiftyone-plotly-container">
                <div id="fiftyone-plotly-styles">
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
                <div id="fiftyone-plotly-map"></div>
            </div>
        )
    }
}

export default FiftyOneMap;
