import React, { useRef, useMemo, useCallback, useState } from "react";
import { Box, Typography, Alert } from "@mui/material";
import { usePluginSettings } from "@fiftyone/plugins";
import * as foc from "@fiftyone/components";
import { ExternalLink } from "@fiftyone/components";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import mapbox, { GeoJSONSource, LngLatBounds } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import Map, { Layer, MapRef, Source } from "react-map-gl";

const MAP_STYLES = {
  light: "light-v11",
  dark: "dark-v11",
  satellite: "satellite-v9",
  streets: "streets-v12",
  outdoors: "outdoors-v12",
};

const fitBoundsOptions = { animate: false, padding: 30 };

const computeBounds = (
  data: GeoJSON.FeatureCollection<GeoJSON.Point, { id: string }>
) => {
  return data.features.reduce(
    (bounds, { geometry: { coordinates } }) =>
      bounds.extend(coordinates as [number, number]),
    new LngLatBounds()
  );
};

const fitBounds = (
  map: MapRef,
  data: GeoJSON.FeatureCollection<GeoJSON.Point, { id: string }>
) => {
  map.fitBounds(computeBounds(data), fitBoundsOptions);
};

const createSourceData = (
  geoPoints: Array<[number, number]>
): GeoJSON.FeatureCollection<GeoJSON.Point, { id: string }> => {
  if (geoPoints.length === 0) return null;

  return {
    type: "FeatureCollection",
    features: geoPoints.map((coordinates, index) => ({
      type: "Feature",
      properties: { id: `point_${index}` },
      geometry: { type: "Point", coordinates },
    })),
  };
};

interface DatasetBoundsMapProps {
  geoPoints: Array<[number, number]>;
  bbox?: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  onBoundsChange?: (bounds: [number, number, number, number]) => void;
  height?: number;
}

export default function DatasetBoundsMap({
  geoPoints,
  bbox,
  onBoundsChange,
  height = 400,
}: DatasetBoundsMapProps) {
  const theme = foc.useTheme();
  const mapRef = useRef<MapRef>(null);
  const [mapError, setMapError] = useState(false);

  // Get Mapbox settings from FiftyOne
  const settings = usePluginSettings("map", {
    mapboxAccessToken: "",
    clustering: false,
    clusterMaxZoom: 14,
    clusters: {
      paint: {
        "circle-color": theme.primary.plainColor,
        "circle-opacity": 0.7,
      },
      textPaint: {
        "text-color": "#ffffff",
      },
    },
    pointPaint: {
      "circle-color": theme.primary.plainColor,
      "circle-opacity": 0.8,
      "circle-radius": 6,
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff",
    },
  });

  const data = useMemo(() => createSourceData(geoPoints), [geoPoints]);

  const bounds = useMemo(() => {
    if (bbox) {
      // Use provided bbox
      return new LngLatBounds([bbox[0], bbox[1]], [bbox[2], bbox[3]]);
    } else if (data) {
      // Compute bounds from geo points
      return computeBounds(data);
    }
    return null;
  }, [data, bbox]);

  const onLoad = useCallback(() => {
    const map = mapRef.current?.getMap();
    if (!map) return;

    // Set cursor styles
    const pointer = () => (map.getCanvas().style.cursor = "pointer");
    const crosshair = () => (map.getCanvas().style.cursor = "crosshair");
    const drag = () => (map.getCanvas().style.cursor = "all-scroll");

    map.on("mouseenter", "point", pointer);
    map.on("mouseleave", "point", crosshair);
    map.on("dragstart", drag);
    map.on("dragend", crosshair);

    // Fit bounds on load
    if (bounds && mapRef.current) {
      fitBounds(mapRef.current, data);
    }
  }, [bounds, data]);

  const handleMapMove = useCallback(() => {
    if (onBoundsChange && mapRef.current) {
      const map = mapRef.current.getMap();
      const bounds = map.getBounds();
      const newBounds: [number, number, number, number] = [
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth(),
      ];
      onBoundsChange(newBounds);
    }
  }, [onBoundsChange]);

  React.useEffect(() => {
    if (mapRef.current && data && bounds) {
      fitBounds(mapRef.current, data);
    }
  }, [data, bounds]);

  if (!settings.mapboxAccessToken) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        <Typography variant="body2">
          No Mapbox token provided.&nbsp;
          <ExternalLink
            style={{ color: theme.text.primary }}
            href={"https://docs.voxel51.com/user_guide/app.html#map-panel"}
          >
            Learn more
          </ExternalLink>
        </Typography>
      </Alert>
    );
  }

  const noData = !geoPoints.length || !data;

  if (noData) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2">
          No geographic data available to display on the map.
        </Typography>
      </Alert>
    );
  }

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Dataset Geographic Coverage
      </Typography>
      <Box
        sx={{
          height: height,
          borderRadius: 1,
          overflow: "hidden",
          border: `1px solid ${theme.palette.divider}`,
          position: "relative",
        }}
      >
        {mapError ? (
          <Alert
            severity="error"
            sx={{ height: "100%", display: "flex", alignItems: "center" }}
          >
            <Typography variant="body2">
              Map failed to load. Please check your&nbsp;
              <ExternalLink
                style={{ color: theme.text.primary }}
                href={"https://docs.voxel51.com/user_guide/app.html#map-panel"}
              >
                Mapbox token
              </ExternalLink>
              &nbsp;configuration.
            </Typography>
          </Alert>
        ) : (
          <Map
            ref={mapRef}
            mapLib={mapbox}
            mapStyle={`mapbox://styles/mapbox/${MAP_STYLES.light}`}
            initialViewState={{
              bounds,
              fitBoundsOptions,
            }}
            mapboxAccessToken={settings.mapboxAccessToken}
            onLoad={onLoad}
            onMoveEnd={handleMapMove}
            onError={({ error }) => {
              setMapError(true);
              console.error("Map error:", error);
            }}
            style={{ width: "100%", height: "100%" }}
          >
            <Source id="points" type="geojson" data={data} cluster={false}>
              <Layer id={"point"} paint={settings.pointPaint} type={"circle"} />
            </Source>
          </Map>
        )}
      </Box>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ mt: 1, display: "block" }}
      >
        Showing {geoPoints.length} geographic points from your dataset.
        {bbox && " Bounding box is highlighted."}
      </Typography>
    </Box>
  );
}
