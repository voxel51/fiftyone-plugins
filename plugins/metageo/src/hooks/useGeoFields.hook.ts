import { useCallback, useEffect, useState } from "react";
import { useMetageoClient } from "./useMetageoClient.hook";
import type { GeoFieldsData } from "../types";

export function useGeoFields() {
  const [geoFields, setGeoFields] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const client = useMetageoClient();

  const fetchGeoFields = useCallback(async () => {
    if (!client) {
      setError("Client not available");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log("🔍 useGeoFields: Calling client.get_geo_fields()");
      const result = await client.get_geo_fields();
      console.log("🔍 useGeoFields: Raw result =", result);
      console.log("🔍 useGeoFields: result type =", typeof result);
      console.log("🔍 useGeoFields: result keys =", result ? Object.keys(result) : "null/undefined");

      if (result?.result) {
        const data: GeoFieldsData = result.result;
        console.log("🔍 useGeoFields: Extracted data =", data);
        setGeoFields(data.geo_fields || []);
      } else if (result?.geo_fields) {
        // Handle case where result is not wrapped in a result property
        console.log("🔍 useGeoFields: Direct geo_fields access =", result.geo_fields);
        setGeoFields(result.geo_fields || []);
      } else {
        console.log("🔍 useGeoFields: No geo_fields found, setting empty array");
        setGeoFields([]);
      }
    } catch (err) {
      console.error("🔍 useGeoFields: Error fetching geo fields:", err);
      setError(
        err instanceof Error ? err.message : "Failed to fetch geographic fields"
      );
      setGeoFields([]);
    } finally {
      setLoading(false);
    }
  }, [client]);

  useEffect(() => {
    if (client) {
      fetchGeoFields();
    }
  }, [client]); // Remove fetchGeoFields dependency to prevent infinite loop

  return {
    geoFields,
    loading,
    error,
    refetch: fetchGeoFields,
  };
}
