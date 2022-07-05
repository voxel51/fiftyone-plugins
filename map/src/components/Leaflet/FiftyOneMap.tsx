
import './FiftyOneMap.css';

import React from 'react';
import L from 'leaflet';
import 'leaflet.markercluster';
import "leaflet-lasso";

type FiftyOneMapProps = {
  data: any, onClick: Function, onGroup: Function, tooltip: any
}

class FiftyOneMap extends React.Component<FiftyOneMapProps> {
  data: any
  onClick: Function
  onGroup: Function
  tooltip: any
  map: any
  bounds: any
  path: any
  cluster: any
  markers: any
  _isClustering: boolean
  _showPath: boolean
  constructor(props: FiftyOneMapProps) {
    super(props)
    const { data, onClick, onGroup, tooltip } = props
    this.data = data
    this.onClick = onClick
    this.onGroup = onGroup
    this.tooltip = tooltip
  }

  componentDidMount() {
    var that = this;

    this.map = L.map('fiftyone-map-container-leaflet', {
      preferCanvas: true,
      maxZoom: 20,
      layers: [
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 20,
          attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a>'
        })
      ]
    });

    L.Control.Button = L.Control.extend({
      options: {
        position: 'topright'
      },
      initialize: function (onClick, faClass, options) {
        this.onClick = onClick
        this.faClass = faClass
        L.setOptions(this, options);
      },
      onAdd: function (map) {
        var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
        var button = L.DomUtil.create('a', 'leaflet-control-button', container);
        L.DomUtil.create('i', this.faClass, button);
        L.DomEvent.disableClickPropagation(button);
        L.DomEvent.on(button, 'click', this.onClick);
        container.title = "Title";
        return container;
      },
      onRemove: function (map) { },
    });

    new L.Control.Button(() => that.centerMap(), 'fa-solid fa-crosshairs').addTo(this.map);


    L.control.lasso({
      position: 'topright'
    }).addTo(this.map);

    this.map.on('lasso.finished', function (event) {
      var latlon = [];
      var data = [];

      event.layers.forEach(layer => {
        if (layer instanceof L.Marker && !(layer instanceof L.MarkerCluster)) {
          latlon.push(layer._latlng)
          console.log(layer)
          data.push(that.data[layer.options.idx])
        }
      });

      that.map.fitBounds(new L.LatLngBounds(latlon), {
        padding: [20, 20]
      });

      if (!that.onGroup)
        return

      that.onGroup(data)

    });

    this.bounds = new L.LatLngBounds(this.data);
    this.path = L.polyline(this.data);

    this.cluster = L.markerClusterGroup({
      disableClusteringAtZoom: 15,
      spiderfyOnMaxZoom: false
    });
    this.markers = L.layerGroup();


    this.data.forEach((datum, idx) => {
      var marker = L.marker(datum, { idx: idx });

      function get_tooltip() {
        return that.tooltip(that.data[idx])
      }

      marker.bindTooltip(get_tooltip, {
        direction: 'right'
      });

      marker.on('click', evt => {
        if (!that.onClick)
          return
        that.onClick(that.data[evt.sourceTarget.options.idx])
      });

      this.cluster.addLayer(marker);
      marker.addTo(this.markers);
    });

    this.centerMap()
    this.isClustering = true
  }

  get isClustering() {
    return !!this._isClustering
  }

  set isClustering(value) {
    this._isClustering = value
    this.setState({ _isClustering: value });

    if (this._isClustering) {
      this.map.removeLayer(this.markers);
      this.map.addLayer(this.cluster);
    } else {
      this.map.removeLayer(this.cluster);
      this.map.addLayer(this.markers);
    }
  }

  get showPath() {
    return !!this._showPath
  }

  set showPath(value) {
    this._showPath = value
    this.setState({ _showPath: value });

    if (this._showPath)
      this.path.addTo(this.map);
    else
      this.path.remove(this.map);
  }

  centerMap() {
    this.map.fitBounds(this.bounds, {
      padding: [20, 20]
    });
  }

  render() {
    return <div id="fiftyone-map-container-leaflet"></div>
  }
}

export default FiftyOneMap;
