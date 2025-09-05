import { useCallback, useEffect, useState } from "react";
import { usePanelEvent } from "@fiftyone/operators";
import type { GeoFieldsData } from "../types";

export function useGeoFields() {
  const [geoFields, setGeoFields] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getGeoFields = usePanelEvent("get_geo_fields");

  const fetchGeoFields = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await getGeoFields();
      if (result?.result) {
        const data: GeoFieldsData = result.result;
        setGeoFields(data.geo_fields || []);
      } else {
        setGeoFields([]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch geographic fields"
      );
      setGeoFields([]);
    } finally {
      setLoading(false);
    }
  }, [getGeoFields]);

  useEffect(() => {
    fetchGeoFields();
  }, [fetchGeoFields]);

  return {
    geoFields,
    loading,
    error,
    refetch: fetchGeoFields,
  };
}
