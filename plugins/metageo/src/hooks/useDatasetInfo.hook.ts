import { useState, useEffect } from "react";
import { useMetageoClient } from "./useMetageoClient.hook";

export interface DatasetInfo {
  is_grouped: boolean;
  group_field: string | null;
  slices: string[];
  dataset_name: string;
  total_samples: number;
}

export function useDatasetInfo(forceRefresh?: boolean) {
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const client = useMetageoClient();

  const loadDatasetInfo = async () => {
    if (!client) {
      setError("Client not available");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const operatorResult = await client.get_dataset_info();
      const result = operatorResult.result;

      console.log("🔍 useDatasetInfo: Backend result =", result);

      if (result?.status === "success") {
        const datasetInfo = {
          is_grouped: result.is_grouped,
          group_field: result.group_field,
          slices: result.slices || [],
          dataset_name: result.dataset_name,
          total_samples: result.total_samples,
        };
        console.log("🔍 useDatasetInfo: Setting dataset info =", datasetInfo);
        setDatasetInfo(datasetInfo);
      } else {
        setError(result?.message || "Failed to load dataset info");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log(
      "🔍 useDatasetInfo: useEffect triggered, calling loadDatasetInfo"
    );
    loadDatasetInfo();
  }, [forceRefresh]);

  return {
    datasetInfo,
    loading,
    error,
    refetch: loadDatasetInfo,
  };
}
