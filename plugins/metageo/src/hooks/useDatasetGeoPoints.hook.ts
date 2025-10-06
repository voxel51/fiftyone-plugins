import { useState, useEffect } from "react";
import { useMetageoClient } from "./useMetageoClient.hook";

export interface GeoPoint {
  longitude: number;
  latitude: number;
}

export function useDatasetGeoPoints(geoField: string | null) {
  const [geoPoints, setGeoPoints] = useState<Array<[number, number]>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const client = useMetageoClient();

  const loadGeoPoints = async () => {
    if (!client || !geoField) {
      setGeoPoints([]);
      setError(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await client.get_sample_geo_points({
        geo_field: geoField,
      });

      if (result?.status === "success" && result.geo_points) {
        setGeoPoints(result.geo_points);
      } else {
        setError(result?.message || "Failed to load geographic points");
        setGeoPoints([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setGeoPoints([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGeoPoints();
  }, [geoField]);

  return {
    geoPoints,
    loading,
    error,
    refetch: loadGeoPoints,
  };
}
