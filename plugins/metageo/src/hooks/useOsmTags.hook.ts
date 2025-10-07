import { useCallback, useState, useEffect } from "react";
import { useMetageoClient } from "./useMetageoClient.hook";
import type { OsmTag } from "../types";

export function useOsmTags() {
  const [osmTags, setOsmTags] = useState<OsmTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);
  const client = useMetageoClient();

  const loadOsmTags = useCallback(async () => {
    console.log("🔍 useOsmTags: loadOsmTags called");
    if (!client) {
      console.log("🔍 useOsmTags: Client not available");
      setError("Client not available");
      setLoading(false);
      return;
    }

    try {
      console.log("🔍 useOsmTags: Setting loading to true");
      setLoading(true);
      setError(null);

      console.log("🔍 useOsmTags: Calling client.get_available_osm_tags()");
      const result = await client.get_available_osm_tags();
      console.log("🔍 useOsmTags: Result received:", result);
      console.log("🔍 useOsmTags: result.result:", result?.result);
      console.log("🔍 useOsmTags: result.result.status:", result?.result?.status);
      console.log("🔍 useOsmTags: result.result.tags:", result?.result?.tags);
      
      if (result?.result?.status === "success" && result.result.tags) {
        console.log("🔍 useOsmTags: Success - setting tags:", result.result.tags);
        setOsmTags(result.result.tags);
        setHasLoaded(true);
      } else if (result?.result?.status === "no_index") {
        console.log("🔍 useOsmTags: No index found");
        setError(
          result?.result?.message || "No completed index found. Please complete the indexing step first."
        );
        setOsmTags([]);
        setHasLoaded(true);
      } else if (result?.result?.status === "error") {
        console.log("🔍 useOsmTags: Backend error");
        setError(result?.result?.message || "Failed to load OSM tags");
        setOsmTags([]);
        setHasLoaded(true);
      } else {
        console.log("🔍 useOsmTags: Unknown status - result:", result);
        console.log("🔍 useOsmTags: Unknown status - result.result:", result?.result);
        setError(result?.result?.message || "Failed to load OSM tags");
        setOsmTags([]);
        setHasLoaded(true);
      }
    } catch (err) {
      console.error("🔍 useOsmTags: Exception:", err);
      setError(err instanceof Error ? err.message : "Failed to load OSM tags");
      setOsmTags([]);
      setHasLoaded(true);
    } finally {
      console.log("🔍 useOsmTags: Setting loading to false");
      setLoading(false);
    }
  }, [client]);

  // Auto-load OSM tags when component mounts and client is available
  useEffect(() => {
    if (client && !hasLoaded && !loading) {
      console.log("🔍 useOsmTags: Auto-loading OSM tags on mount");
      loadOsmTags();
    }
  }, [client, hasLoaded, loading]); // Remove loadOsmTags dependency to prevent infinite loop

  return {
    osmTags,
    loading,
    error,
    hasLoaded,
    refetch: loadOsmTags,
  };
}
