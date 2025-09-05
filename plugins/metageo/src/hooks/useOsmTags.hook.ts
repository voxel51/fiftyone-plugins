import { useCallback, useState } from "react";
import { useMetageoClient } from "./useMetageoClient.hook";
import type { OsmTag } from "../types";

export function useOsmTags() {
  const [osmTags, setOsmTags] = useState<OsmTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const client = useMetageoClient();

  const loadOsmTags = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await client.get_available_osm_tags();
      if (result?.result?.status === "success" && result.result.tags) {
        setOsmTags(result.result.tags);
      } else if (result?.result?.status === "no_index") {
        setError(
          "No completed index found. Please complete the indexing step first."
        );
        setOsmTags([]);
      } else {
        setError(result?.result?.message || "Failed to load OSM tags");
        setOsmTags([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load OSM tags");
      setOsmTags([]);
    } finally {
      setLoading(false);
    }
  }, [client]);

  return {
    osmTags,
    loading,
    error,
    refetch: loadOsmTags,
  };
}
