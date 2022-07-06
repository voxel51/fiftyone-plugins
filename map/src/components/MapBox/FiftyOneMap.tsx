import './FiftyOneMap.css';

import React from 'react';
import mapboxgl from 'mapbox-gl';

const MAPBOX_ACCESS_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
const circleColor = "#FF0000"

const styles = [{
    id: "satellite-v9",
    name: "Satellite"
}, {
    id: "streets-v11",
    name: "Streets"
}, {
    id: "outdoors-v11",
    name: "Outdoors"
}, {
    id: "light-v10",
    name: "Light"
}, {
    id: "dark-v10",
    name: "Dark"
}];


class MapboxGLButtonControl {
    private _iconClass: any;
    private _title: any;
    private _eventHandler: any;
    private _btn: HTMLButtonElement;
    private _icon: HTMLElement;
    private _container: HTMLElement;
    private _map: any;
    constructor({
        iconClass = "",
        title = "",
        eventHandler
    }) {
        this._iconClass = iconClass;
        this._title = title;
        this._eventHandler = eventHandler;
    }

    onAdd(map) {
        this._btn = document.createElement("button");
        this._btn.className = "mapboxgl-ctrl-icon";
        this._btn.type = "button";
        this._btn.title = this._title;
        this._btn.onclick = this._eventHandler;

        this._icon = document.createElement("i");
        this._icon.className = this._iconClass
        this._btn.appendChild(this._icon)


        this._container = document.createElement("div");
        this._container.className = "mapboxgl-ctrl-group mapboxgl-ctrl";
        this._container.appendChild(this._btn);

        return this._container;
    }

    onRemove() {
        this._container.parentNode.removeChild(this._container);
        this._map = undefined;
    }
}

type FiftyOneMapProps = {
    data: any, onClick: Function, onGroup: Function, tooltip: any
}

class FiftyOneMap extends React.Component<FiftyOneMapProps> {
    private data: any;
    private points: any;
    private bounds: any;
    private onClick: Function;
    private onGroup: Function;
    private tooltip: any;
    private map: any;
    private style: any;
    constructor(props) {
        const { data, onClick, onGroup, tooltip } = props
        super(props);

        mapboxgl.accessToken = MAPBOX_ACCESS_TOKEN

        this.data = data;
        this.points = {
            'type': 'FeatureCollection',
            'features': data.map(datum => ({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [datum.location.lng, datum.location.lat]
                },
                'properties': datum
            }))
        };
        this.bounds = new mapboxgl.LngLatBounds();
        this.points.features.forEach(feature => {
            this.bounds.extend(feature.geometry.coordinates);
        });

        this.onClick = onClick;
        this.onGroup = onGroup;
        this.tooltip = tooltip;
    }

    componentDidMount() {
        this.style = styles[styles.length - 1].id;
        this.load_map();
    }

    load_map() {
        var that = this;

        var bounds = this.bounds;
        if (that.map) {
            bounds = that.map.getBounds()
            that.map.remove();
        }

        that.map = new mapboxgl.Map({
            container: 'fiftyone-map-container-mapbox',
            style: `mapbox://styles/mapbox/${that.style}`,
            bounds: bounds,
            fitBoundsOptions: {
                padding: 25
            }
        });

        that.map.addControl(new mapboxgl.NavigationControl());
        that.map.addControl(new MapboxGLButtonControl({
            iconClass: 'fa-solid fa-crosshairs',
            title: "Recenter",
            eventHandler: () => that.centerMap()
        }), "top-right");

        that.map.on('load', () => {
            that.map.addSource('points', {
                'type': 'geojson',
                'data': that.points,
                cluster: true,
                clusterMaxZoom: 12
            });

            that.map.addLayer({
                id: 'clusters',
                type: 'circle',
                source: 'points',
                filter: ['has', 'point_count'],
                paint: {
                    // Use step expressions (https://docs.mapbox.com/mapbox-gl-js/style-spec/#expressions-step)
                    // with three steps to implement three types of circles:
                    //   * Blue, 20px circles when point count is less than 100
                    //   * Yellow, 30px circles when point count is between 100 and 750
                    //   * Pink, 40px circles when point count is greater than or equal to 750
                    'circle-color': circleColor,
                    'circle-radius': [
                        'step',
                        ['get', 'point_count'],
                        20,
                        10,
                        30,
                        25,
                        40
                    ]
                }
            });

            that.map.addLayer({
                id: 'cluster-count',
                type: 'symbol',
                source: 'points',
                filter: ['has', 'point_count'],
                layout: {
                    'text-field': '{point_count_abbreviated}',
                    'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
                    'text-size': 12
                }
            });


            that.map.addLayer({
                id: 'unclustered-point',
                type: 'circle',
                source: 'points',
                filter: ['!', ['has', 'point_count']],
                paint: {
                    'circle-color': circleColor,
                    'circle-radius': 5,

                }
            });

            // inspect a cluster on click
            that.map.on('click', 'clusters', (e) => {
                const features = that.map.queryRenderedFeatures(e.point, {
                    layers: ['clusters']
                });

                const clusterId = features[0].properties.cluster_id;
                that.map.getSource('points').getClusterExpansionZoom(
                    clusterId,
                    (err, zoom) => {
                        if (err) return;

                        that.map.easeTo({
                            center: features[0].geometry.coordinates,
                            zoom: zoom
                        });
                    }
                );
            });

            // When a click event occurs on a feature in
            // the unclustered-point layer, open a popup at
            // the location of the feature, with
            // description HTML from its properties.
            that.map.on('click', 'unclustered-point', (e) => {
                that.onClick(e.features[0].properties)
            });

            that.map.on('mouseenter', 'clusters', () => {
                that.map.getCanvas().style.cursor = 'pointer';
            });
            that.map.on('mouseleave', 'clusters', () => {
                that.map.getCanvas().style.cursor = '';
            });

            that.map.on('mouseenter', 'unclustered-point', () => {
                that.map.getCanvas().style.cursor = 'pointer';
            });
            that.map.on('mouseleave', 'unclustered-point', () => {
                that.map.getCanvas().style.cursor = '';
            });

        });


    }


    centerMap() {
        this.map.fitBounds(this.bounds, {
            padding: 25
        });
    }

    setStyle(style) {
        this.style = style
        this.load_map()
    }
    render() {
        return (
            <div>
                <div id="menu">
                    <Choices parent={this} styles={styles} />;
                </div>
                <div id="fiftyone-map-container-mapbox"></div>
            </div>
        )
    }
}

function Choices({ parent, styles }) {
    return styles.map((style, idx) => {
        return <Choice parent={parent} style={style} idx={idx} />
    })
}

function Choice({ idx, style, parent }) {
    return (
        <span key={idx} >
            <input id={style.id} type="radio" name="rtoggle" checked onClick={() => parent.setStyle(style.id)} />
            <label>{style.name}</label>
        </span>
    )
}

export default FiftyOneMap;
