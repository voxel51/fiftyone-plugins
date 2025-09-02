import React, { useState, useCallback, useEffect } from "react";
import * as fos from "@fiftyone/state";
import { useRecoilValue, useRecoilState } from "recoil";
import { Button as FiftyOneButton } from "@fiftyone/components";
import { useOperatorExecutor, abortOperationsByURI } from "@fiftyone/operators";

import IndexingGrid from "./IndexingGrid";
import type { CellStatus } from "./IndexingGrid";
import { useMetageoClient } from "./useMetageoClient";
import { metageoIndexingState } from "./state";
import IndexConfigurationStep from "./steps/IndexConfigurationStep";
import IndexingStep from "./steps/IndexingStep";
import MappingStep from "./steps/MappingStep";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  AlertTitle,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Divider,
  Paper,
  Grid,
  Stack,
  useTheme,
  alpha,
  Button,
  CircularProgress,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from "@mui/material";
import {
  Map as MapIcon,
  LocationOn as LocationIcon,
  Explore as ExploreIcon,
  CloudDownload as DownloadIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  PlayArrow as PlayIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Analytics as DataUsageIcon,
  Refresh as RefreshIcon,
  Pause as PauseIcon,
  Code as CodeIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Replay as ReplayIcon,
} from "@mui/icons-material";

type PanelMethod = (args?: any) => Promise<any>;

interface GeoFieldsData {
  geo_fields: string[];
  has_geo_fields: boolean;
  dataset_name: string;
  total_fields: number;
  can_proceed: boolean;
}

interface StepData {
  index: {
    bbox: number[] | null;
    gridTiles: number;
    location: string;
    gridCells: Array<{
      id: string;
      status: CellStatus;
      progress: number;
      error?: string;
      coordinates: [number, number, number, number];
      sample_count: number;
    }>;
    executionMode: "immediate" | "delegated";
    indexingStatus?:
      | "idle"
      | "running"
      | "completed"
      | "failed"
      | "cancelled"
      | "paused";
  };
  mapping: {
    // Basic configuration
    radius: number;
    geoField: string;

    // 3D Detections configuration
    enable3DDetections: boolean;
    threeDSlice: string;
    detectionFieldName: string;
    detectionLabelTag: string;

    // Sample tagging configuration
    enableSampleTagging: boolean;
    tagSlice: string;
    tagMappings: Array<{
      osmKey: string;
      fieldName: string;
      fieldType: "string" | "int" | "float" | "bool";
      boolTrueValue?: string;
      boolFalseValue?: string;
    }>;
    tagRadius: number;
    renderOn3D: boolean;
    renderOn2D: boolean;

    // Field mapping configuration
    enableFieldMapping: boolean;
    fieldMappings: Array<{
      osmKey: string;
      fieldName: string;
      fieldType: "string" | "int" | "float" | "bool";
      boolTrueValue?: string;
      boolFalseValue?: string;
    }>;

    // YAML configuration
    useYamlConfig: boolean;
    yamlConfig: string;
  };
  enrich: {
    prefetchId: string | null;
    enrichedCount: number;
  };
  search: {
    filters: Array<{ key: string; value: string; type: string }>;
  };
  cleanup: {
    removeIndex: boolean;
    removeEnrichedData: boolean;
  };
}

interface QuadtreeCell {
  id: string;
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  sampleCount: number;
  children?: QuadtreeCell[];
  depth: number;
  maxDepth: number;
  minSize: number; // minimum bbox size in degrees
}

interface QuadtreeConfig {
  maxDepth: number;
  minSize: number;
  threshold: number; // max samples per cell before splitting
  maxSamplesPerCell: number;
}

// Quadtree implementation
const buildQuadtree = (
  sampleDistribution: { [cellId: string]: number },
  bbox: [number, number, number, number],
  config: QuadtreeConfig
): QuadtreeCell[] => {
  // Calculate the actual data extents from sample distribution
  const calculateDataExtents = () => {
    if (Object.keys(sampleDistribution).length === 0) return bbox;

    const [minLon, minLat, maxLon, maxLat] = bbox;
    const gridSize = Math.sqrt(Object.keys(sampleDistribution).length);
    const lonStep = (maxLon - minLon) / gridSize;
    const latStep = (maxLat - minLat) / gridSize;

    let dataMinLon = maxLon,
      dataMaxLon = minLon;
    let dataMinLat = maxLat,
      dataMaxLat = minLat;

    Object.entries(sampleDistribution).forEach(([cellId, count]) => {
      if (count > 0) {
        const [row, col] = cellId.split("_").map(Number);
        const cellMinLon = minLon + col * lonStep;
        const cellMaxLon = cellMinLon + lonStep;
        const cellMinLat = minLat + row * latStep;
        const cellMaxLat = cellMinLat + latStep;

        dataMinLon = Math.min(dataMinLon, cellMinLon);
        dataMaxLon = Math.max(dataMaxLon, cellMaxLon);
        dataMinLat = Math.min(dataMinLat, cellMinLat);
        dataMaxLat = Math.max(dataMaxLat, cellMaxLat);
      }
    });

    // Add a small buffer around the data
    const buffer = 0.001; // ~100m buffer
    return [
      Math.max(minLon, dataMinLon - buffer),
      Math.max(minLat, dataMinLat - buffer),
      Math.min(maxLon, dataMaxLon + buffer),
      Math.min(maxLat, dataMaxLat + buffer),
    ] as [number, number, number, number];
  };

  const dataExtents = calculateDataExtents();
  const totalSamples = Object.values(sampleDistribution).reduce(
    (sum, count) => sum + count,
    0
  );

  // Start with the data extents as root cell
  const rootCell: QuadtreeCell = {
    id: "root",
    bbox: dataExtents,
    sampleCount: totalSamples,
    depth: 0,
    maxDepth: config.maxDepth,
    minSize: config.minSize,
  };

  const processCell = (cell: QuadtreeCell): QuadtreeCell => {
    const [minLon, minLat, maxLon, maxLat] = cell.bbox;
    const cellWidth = maxLon - minLon;
    const cellHeight = maxLat - minLat;

    // Check if we should split this cell
    const shouldSplit =
      cell.depth < config.maxDepth &&
      cell.sampleCount > config.threshold &&
      cellWidth > config.minSize &&
      cellHeight > config.minSize;

    if (shouldSplit) {
      // Split into 4 quadrants
      const midLon = (minLon + maxLon) / 2;
      const midLat = (minLat + maxLat) / 2;

      const quadrants = [
        { id: `${cell.id}_NW`, bbox: [minLon, midLat, midLon, maxLat] },
        { id: `${cell.id}_NE`, bbox: [midLon, midLat, maxLon, maxLat] },
        { id: `${cell.id}_SW`, bbox: [minLon, minLat, midLon, midLat] },
        { id: `${cell.id}_SE`, bbox: [midLon, minLat, maxLon, midLat] },
      ];

      cell.children = quadrants.map((quad) => {
        // Count samples in this quadrant by checking which samples fall within the quadrant
        let quadrantSampleCount = 0;
        const [quadMinLon, quadMinLat, quadMaxLon, quadMaxLat] = quad.bbox;

        Object.entries(sampleDistribution).forEach(([cellId, count]) => {
          if (count > 0) {
            const [row, col] = cellId.split("_").map(Number);
            const [origMinLon, origMinLat, origMaxLon, origMaxLat] = bbox;
            const gridSize = Math.sqrt(Object.keys(sampleDistribution).length);
            const lonStep = (origMaxLon - origMinLon) / gridSize;
            const latStep = (origMaxLat - origMinLat) / gridSize;

            const cellMinLon = origMinLon + col * lonStep;
            const cellMaxLon = cellMinLon + lonStep;
            const cellMinLat = origMinLat + row * latStep;
            const cellMaxLat = cellMinLat + latStep;

            // Check if this sample cell overlaps with the quadrant
            if (
              cellMaxLon > quadMinLon &&
              cellMinLon < quadMaxLon &&
              cellMaxLat > quadMinLat &&
              cellMinLat < quadMaxLat
            ) {
              quadrantSampleCount += count;
            }
          }
        });

        return processCell({
          id: quad.id,
          bbox: quad.bbox,
          sampleCount: quadrantSampleCount,
          depth: cell.depth + 1,
          maxDepth: config.maxDepth,
          minSize: config.minSize,
        });
      });
    }

    return cell;
  };

  const processedRoot = processCell(rootCell);

  // Flatten the tree into a list of leaf cells
  const flattenCells = (cell: QuadtreeCell): QuadtreeCell[] => {
    if (cell.children && cell.children.length > 0) {
      return cell.children.flatMap(flattenCells);
    }
    return [cell];
  };

  return flattenCells(processedRoot);
};

// Add quadtree configuration component
const QuadtreeConfiguration = ({
  sampleDistribution,
  bbox,
  onQuadtreeCellsChange,
}: {
  sampleDistribution: { [cellId: string]: number };
  bbox: [number, number, number, number] | null;
  onQuadtreeCellsChange: (cells: QuadtreeCell[]) => void;
}) => {
  const theme = useTheme();
  const [config, setConfig] = useState<QuadtreeConfig>({
    maxDepth: 4,
    minSize: 0.01, // ~1km at equator
    threshold: 50,
    maxSamplesPerCell: 100,
  });

  const [quadtreeCells, setQuadtreeCells] = useState<QuadtreeCell[]>([]);
  const [showQuadtree, setShowQuadtree] = useState(false);

  const generateQuadtree = useCallback(() => {
    if (!bbox) return;

    const cells = buildQuadtree(
      sampleDistribution,
      bbox as [number, number, number, number],
      config
    );
    setQuadtreeCells(cells);
    onQuadtreeCellsChange(cells);
    setShowQuadtree(true);
  }, [sampleDistribution, bbox, config, onQuadtreeCellsChange]);

  const totalSamples = Object.values(sampleDistribution).reduce(
    (sum, count) => sum + count,
    0
  );
  const estimatedCost = quadtreeCells.length * 0.5 + totalSamples * 0.001;

  return (
    <Paper
      elevation={1}
      sx={{
        p: 3,
        mb: 3,
        background: alpha(theme.palette.info.main, 0.05),
        border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
        borderRadius: 2,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
        <DataUsageIcon sx={{ mr: 1, color: theme.palette.info.main }} />
        <Typography
          variant="h6"
          sx={{ fontWeight: 600, color: theme.palette.text.primary }}
        >
          Adaptive Quadtree Grid
        </Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Automatically split cells based on sample density for optimal OSM data
        retrieval. Dense areas get finer resolution, sparse areas stay coarse.
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Max Depth</InputLabel>
            <Select
              value={config.maxDepth}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  maxDepth: e.target.value as number,
                }))
              }
              label="Max Depth"
            >
              <MenuItem value={2}>2 levels (4 cells)</MenuItem>
              <MenuItem value={3}>3 levels (16 cells)</MenuItem>
              <MenuItem value={4}>4 levels (64 cells)</MenuItem>
              <MenuItem value={5}>5 levels (256 cells)</MenuItem>
              <MenuItem value={6}>6 levels (1,024 cells)</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Split Threshold</InputLabel>
            <Select
              value={config.threshold}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  threshold: e.target.value as number,
                }))
              }
              label="Split Threshold"
            >
              <MenuItem value={10}>10 samples</MenuItem>
              <MenuItem value={25}>25 samples</MenuItem>
              <MenuItem value={50}>50 samples</MenuItem>
              <MenuItem value={100}>100 samples</MenuItem>
              <MenuItem value={200}>200 samples</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Min Cell Size</InputLabel>
            <Select
              value={config.minSize}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  minSize: e.target.value as number,
                }))
              }
              label="Min Cell Size"
            >
              <MenuItem value={0.001}>~100m</MenuItem>
              <MenuItem value={0.005}>~500m</MenuItem>
              <MenuItem value={0.01}>~1km</MenuItem>
              <MenuItem value={0.05}>~5km</MenuItem>
              <MenuItem value={0.1}>~10km</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Button
            onClick={generateQuadtree}
            disabled={!bbox || Object.keys(sampleDistribution).length === 0}
            variant="contained"
            startIcon={<DataUsageIcon />}
            sx={{ height: 40 }}
          >
            Generate Quadtree
          </Button>
        </Grid>
      </Grid>

      {showQuadtree && quadtreeCells.length > 0 && (
        <Box>
          <Alert severity="success" sx={{ mb: 2 }}>
            <AlertTitle>Quadtree Generated</AlertTitle>
            Created {quadtreeCells.length} adaptive cells with estimated{" "}
            {estimatedCost.toFixed(1)}s processing time.
            {quadtreeCells.length < 50 &&
              " This is much more efficient than a fixed grid!"}
          </Alert>

          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
            {quadtreeCells.slice(0, 20).map((cell, index) => (
              <Chip
                key={cell.id}
                label={`${cell.sampleCount} samples`}
                size="small"
                color={
                  cell.sampleCount > config.threshold ? "warning" : "default"
                }
                variant={
                  cell.sampleCount > config.threshold ? "filled" : "outlined"
                }
              />
            ))}
            {quadtreeCells.length > 20 && (
              <Chip
                label={`+${quadtreeCells.length - 20} more`}
                size="small"
                variant="outlined"
              />
            )}
          </Box>

          <Typography variant="body2" color="text.secondary">
            <strong>Distribution:</strong>{" "}
            {quadtreeCells.filter((c) => c.sampleCount > 0).length} active
            cells,
            {
              quadtreeCells.filter((c) => c.sampleCount > config.threshold)
                .length
            }{" "}
            dense cells that were split, average{" "}
            {(totalSamples / quadtreeCells.length).toFixed(1)} samples per cell.
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default function MetageoView(props: any) {
  const { data } = props as {
    data: any;
  };

  const client = useMetageoClient(props);

  const theme = useTheme();
  const dataset = useRecoilValue(fos.dataset);
  const [indexingState, setIndexingState] =
    useRecoilState(metageoIndexingState);
  const [hasStarted, setHasStarted] = useState(false);
  // Step constants for clarity
  const STEPS = {
    INDEX_CONFIGURATION: 0,
    INDEXING: 1,
    MAPPING: 2,
    ENRICH: 3,
    SEARCH_CLEANUP: 4
  } as const;

  const [activeStep, setActiveStep] = useState<number>(STEPS.INDEX_CONFIGURATION);
  const [loading, setLoading] = useState(false);
  const [geoFieldsData, setGeoFieldsData] = useState<GeoFieldsData | null>(
    null
  );
  const [geoFieldsLoading, setGeoFieldsLoading] = useState(true);
  const [osmTags, setOsmTags] = useState<
    Array<{ key: string; count: number; examples: string[] }>
  >([]);
  const [osmTagsLoading, setOsmTagsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Use data from on_load instead of calling method
  React.useEffect(() => {
    if (data) {
      const geoFields = data.geo_fields || [];
      const geoFieldsData: GeoFieldsData = {
        geo_fields: geoFields,
        has_geo_fields: geoFields.length > 0,
        dataset_name: data.dataset_name || "Unknown",
        total_fields: data.total_fields || 0,
        can_proceed: geoFields.length > 0,
      };
      setGeoFieldsData(geoFieldsData);
      setGeoFieldsLoading(false);
    }
  }, [data]);

  const [stepData, setStepData] = useState<StepData>({
    index: {
      bbox: null,
      gridTiles: 16,
      location: "",
      gridCells: [],
      executionMode: "immediate",
      indexingStatus: "idle",
    },
    mapping: {
      // Basic configuration
      radius: 100,
      geoField: data?.default_geo_field || "",

      // 3D Detections configuration
      enable3DDetections: false,
      threeDSlice: "",
      detectionFieldName: "my_detections",
      detectionLabelTag: "type",

      // Sample tagging configuration
      enableSampleTagging: false,
      tagSlice: "",
      tagMappings: [],
      tagRadius: 100,
      renderOn3D: true,
      renderOn2D: true,

      // Field mapping configuration
      enableFieldMapping: false,
      fieldMappings: [],

      // YAML configuration
      useYamlConfig: false,
      yamlConfig: "",
    },
    enrich: {
      prefetchId: null,
      enrichedCount: 0,
    },
    search: {
      filters: [],
    },
    cleanup: {
      removeIndex: false,
      removeEnrichedData: false,
    },
  });

  const [availableTags, setAvailableTags] = useState<
    Array<{ key: string; count: number; sampleValues: string[] }>
  >([]);
  const [sampleDistributionLoading, setSampleDistributionLoading] =
    useState(false);
  const [dropIndexDialogOpen, setDropIndexDialogOpen] = useState(false);
  const [realSampleDistribution, setRealSampleDistribution] = useState<{
    [cellId: string]: number;
  }>({});
  const [quadtreeCells, setQuadtreeCells] = useState<QuadtreeCell[]>([]);
  const [hasExistingIndex, setHasExistingIndex] = useState(false);
  const [existingIndexData, setExistingIndexData] = useState<any>(null);

  // Watch operator executor for real-time updates (not needed - operators are triggered from backend)
  // const watchExecutor = useOperatorExecutor("@voxel51/metageo/watch_indexing");

  const handleGetStarted = useCallback(() => {
    setHasStarted(true);
  }, []);

  // Load current indexing state from backend (single source of truth)
  const loadCurrentIndexingState = useCallback(async () => {
    console.log("🔄 loadCurrentIndexingState: Starting...");
    try {
      const result = await client.get_current_indexing_state();
      console.log("🔄 loadCurrentIndexingState: Backend result:", result);
      console.log("🔄 loadCurrentIndexingState: Result status:", result?.status);
      console.log("🔄 loadCurrentIndexingState: Has grid cells:", result?.grid_cells?.length);

      // Handle FiftyOne OperatorResult wrapper
      const data = result?.result || result;
      
      if (data?.status === "found") {
        // We have an indexing state - update all UI state from it
        console.log("🔄 loadCurrentIndexingState: Found existing state, updating UI...");
        setHasExistingIndex(true);
        setExistingIndexData(data);
        setHasStarted(true); // Skip intro screen, show current state
        console.log("🔄 loadCurrentIndexingState: Set hasStarted = true");

        // Load the grid data into Recoil state
        const gridCells = data.grid_cells || [];
        const cells: { [cellId: string]: any } = {};

        gridCells.forEach((cell: any) => {
          if (cell?.id) {
            cells[cell.id] = {
              id: cell.id,
              status: cell.status || "idle",
              progress: 0,
              osm_features: cell.osm_features || 0,
              error: cell.error || null,
              updated_at: new Date().toISOString(),
            };
          }
        });

        // Update Recoil state with current indexing data
        setIndexingState((prev) => ({
          ...prev,
          status: result.status || "idle",
          cells: cells,
          total_cells: result.total_cells || 0,
          active_cells: result.active_cells || 0,
          completed_cells: result.completed_cells || 0,
          failed_cells: result.failed_cells || 0,
          rate_limited_cells: result.rate_limited_cells || 0,
          total_features: result.total_features || 0,
          progress: result.progress || 0,
          started_at: result.started_at,
          last_updated: new Date().toISOString(),
        }));

        // Set the bounding box, grid tiles, and geo field from current state
        if (
          result.bbox &&
          Array.isArray(result.bbox) &&
          result.bbox.length === 4
        ) {
          setStepData((prev) => ({
            ...prev,
            index: {
              ...prev.index,
              bbox: result.bbox,
              gridTiles: result.grid_tiles || 16,
              indexingStatus: result.status || "idle",
            },
            mapping: {
              ...prev.mapping,
              geoField: result.geo_field || prev.mapping.geoField,
            },
          }));
        }

        // Update grid cells for display
        setStepData((prev) => ({
          ...prev,
          index: {
            ...prev.index,
            gridCells: gridCells,
          },
        }));

        // Determine which step to show based on indexing status
        if (result.indexing_status === "completed") {
            setActiveStep(STEPS.MAPPING); // Show Mapping step for completed index
        } else if (result.indexing_status === "running" || result.indexing_status === "paused" || result.indexing_status === "failed") {
                      setActiveStep(STEPS.INDEXING); // Show Index step for active/incomplete indexing
          } else {
            setActiveStep(STEPS.INDEX_CONFIGURATION); // Show Index Configuration step for new/unknown status
          }

        console.log("✅ Current indexing state loaded from backend");
      } else {
        // No indexing state found - clear everything
        setHasExistingIndex(false);
        setExistingIndexData(null);
        setIndexingState((prev) => ({
          ...prev,
          status: "idle",
          cells: {},
          total_cells: 0,
          active_cells: 0,
          completed_cells: 0,
          failed_cells: 0,
          rate_limited_cells: 0,
          total_features: 0,
          progress: 0,
        }));
        console.log("ℹ️ No indexing state found - starting fresh");
      }
    } catch (err) {
      console.error("Error loading current indexing state:", err);
      // Don't show error - it's normal to not have an existing index
    }
  }, [client, setIndexingState]);

  // Load current indexing state on mount - single source of truth
  useEffect(() => {
    console.log("🔄 useEffect: Loading current indexing state on mount...");
    loadCurrentIndexingState();
  }, []); // Empty dependency array - only run once on mount

  const handleBack = useCallback(() => {
    setActiveStep((prev) => Math.max(prev - 1, 0));
  }, []);

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccess(null);
  }, []);



  // Step 1: Index
  const handleAutoBbox = useCallback(async () => {
    if (!stepData.mapping.geoField) {
      setError("Please select a geo field first");
      return;
    }

    setLoading(true);
    clearMessages();

    try {
      // Use the client to call the method
      const result = await client.define_area_auto({
        geo_field: stepData.mapping.geoField,
      });
      console.log("Auto-detect result:", result);
      console.log("Result type:", typeof result);
      console.log("Result keys:", result ? Object.keys(result) : "null");

      // Extract the actual result data from the OperatorResult wrapper
      const actualResult = result?.result;
      console.log("Actual result:", actualResult);
      console.log("Bbox from actual result:", actualResult?.bbox);
      console.log(
        "Sample count from actual result:",
        actualResult?.sample_count
      );

      setStepData((prev) => {
        console.log("Previous state bbox:", prev.index.bbox);
        const newState = {
          ...prev,
          index: {
            ...prev.index,
            bbox: actualResult?.bbox,
          },
        };
        console.log("New state bbox:", newState.index.bbox);
        console.log("Setting bbox to:", actualResult?.bbox);
        return newState;
      });
      // Auto-detection completed successfully
    } catch (err) {
      console.error("Auto-detect error:", err);
      setError(`Failed to auto-detect bounding box: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [stepData.mapping.geoField, client, clearMessages]);

  // Step 2: Mapping
  const handleExploreTags = useCallback(async () => {
    if (!stepData.index.bbox) {
      setError("Please complete the indexing step first");
      return;
    }

    setLoading(true);
    clearMessages();

    try {
      const result = await client.explore_tags({ bbox: stepData.index.bbox });
      setAvailableTags(result?.keys || []);
              // Tags loaded successfully
    } catch (err) {
      setError(`Failed to explore tags: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [stepData.index.bbox, client, clearMessages]);

  const handleLoadOsmTags = useCallback(async () => {
    setOsmTagsLoading(true);
    clearMessages();

    try {
      const result = await client.get_available_osm_tags();
      const actualResult = result?.result;

      if (actualResult?.status === "success" && actualResult?.tags) {
        setOsmTags(actualResult.tags);
        // OSM tags loaded successfully
      } else if (actualResult?.status === "no_index") {
        setError(
          "No completed index found. Please complete the indexing step first."
        );
      } else {
        setError(actualResult?.message || "Failed to load OSM tags");
      }
    } catch (err) {
      setError(`Failed to load OSM tags: ${err}`);
    } finally {
      setOsmTagsLoading(false);
    }
  }, [client, clearMessages]);

  // Load OSM tags when mapping step is active and we have an index
  useEffect(() => {
    if (
      activeStep === 1 &&
      data?.has_existing_index &&
      osmTags.length === 0 &&
      !osmTagsLoading
    ) {
      handleLoadOsmTags();
    }
  }, [
    activeStep,
    data?.has_existing_index,
    osmTags.length,
    osmTagsLoading,
    handleLoadOsmTags,
  ]);

  // Step 3: Enrich
  const handleCalculateSampleDistribution = useCallback(async () => {
    if (!stepData.index.bbox || !stepData.mapping.geoField) {
      setError("Please complete previous steps first");
      return;
    }

    setSampleDistributionLoading(true);
    clearMessages();

    try {
      const result = await client.get_sample_distribution({
        bbox: stepData.index.bbox,
        grid_tiles: stepData.index.gridTiles,
        geo_field: stepData.mapping.geoField,
      });

      const actualResult = result?.result;

      // Store the real sample distribution data
      const sampleDistribution: { [cellId: string]: number } = {};
      if (actualResult?.grid_cells) {
        actualResult.grid_cells.forEach((cell: any) => {
          sampleDistribution[cell.id] = cell.sample_count;
        });
      }
      console.log("Sample distribution calculated:", sampleDistribution);
      console.log("Sample distribution keys:", Object.keys(sampleDistribution));
      console.log(
        "Sample distribution values:",
        Object.values(sampleDistribution)
      );
      setRealSampleDistribution(sampleDistribution);

      // Build the grid in Recoil state
      const gridCells = actualResult?.grid_cells || [];
      const cells: { [cellId: string]: any } = {};

      gridCells.forEach((cell: any) => {
        cells[cell.id] = {
          id: cell.id,
          status: cell.sample_count === 0 ? "empty" : "idle",
          progress: 0,
          osm_features: 0,
          error: null,
          updated_at: new Date().toISOString(),
        };
      });

      // Update Recoil state with the grid
      setIndexingState((prev) => ({
        ...prev,
        status: "idle",
        cells: cells,
        total_cells: gridCells.length,
        active_cells: gridCells.filter((cell: any) => cell.sample_count > 0)
          .length,
        completed_cells: 0,
        failed_cells: 0,
        rate_limited_cells: 0,
        total_features: 0,
        progress: 0,
      }));

      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          gridCells: gridCells,
        },
      }));

      // Sample distribution calculated successfully
    } catch (err) {
      setError(`Failed to calculate sample distribution: ${err}`);
    } finally {
      setSampleDistributionLoading(false);
    }
  }, [
    stepData.index.bbox,
    stepData.index.gridTiles,
    stepData.mapping.geoField,
    client,
    clearMessages,
    setIndexingState,
  ]);

  const handleStartIndexing = useCallback(async () => {
    if (!stepData.index.bbox || !stepData.mapping.geoField) {
      setError("Please complete previous steps first");
      return;
    }

    // Check if we have a grid in Recoil state - if not, we'll create a uniform grid
    const hasSampleDistribution =
      indexingState.cells && Object.keys(indexingState.cells).length > 0;

    if (!hasSampleDistribution) {
      // Create a uniform grid for indexing without sample distribution
      const gridTiles = stepData.index.gridTiles;
      const totalCells = gridTiles * gridTiles;
      const cells: { [cellId: string]: any } = {};

      for (let row = 0; row < gridTiles; row++) {
        for (let col = 0; col < gridTiles; col++) {
          const cellId = `${row}_${col}`;
          cells[cellId] = {
            id: cellId,
            status: "idle",
            progress: 0,
            osm_features: 0,
            error: null,
            updated_at: new Date().toISOString(),
          };
        }
      }

      // Update Recoil state with uniform grid
      setIndexingState((prev) => ({
        ...prev,
        status: "idle",
        cells: cells,
        total_cells: totalCells,
        active_cells: totalCells, // All cells are active in uniform grid
        completed_cells: 0,
        failed_cells: 0,
        rate_limited_cells: 0,
        total_features: 0,
        progress: 0,
      }));

      // Uniform grid created successfully
    }

    setLoading(true);
    clearMessages();

    try {
      // Update Recoil state to show indexing is starting
      setIndexingState((prev) => ({
        ...prev,
        status: "running",
        started_at: new Date().toISOString(),
        last_updated: new Date().toISOString(),
      }));

      const result = await client.start_indexing({
        bbox: stepData.index.bbox,
        grid_tiles: stepData.index.gridTiles,
        geo_field: stepData.mapping.geoField,
        execution_mode: stepData.index.executionMode,
      });

      console.log("Start indexing result:", result);
      console.log("Result type:", typeof result);
      console.log("Result result property:", result?.result);

      // Extract the actual result from the OperatorResult
      const actualResult = result?.result;
      console.log("Actual result:", actualResult);
      console.log("Actual result status:", actualResult?.status);
      console.log("Actual result error:", actualResult?.error);
      console.log("Actual result message:", actualResult?.message);

      if (actualResult?.status === "started") {
        // Indexing started successfully
        console.log("✅ Indexing started successfully!");
        console.log(
          "Active cells to process:",
          indexingState.active_cells || 0
        );
        console.log("Indexing ID:", actualResult?.indexing_id);

        setStepData((prev) => ({
          ...prev,
          index: {
            ...prev.index,
            indexingStatus: "running",
          },
        }));
        
        // Start polling for progress updates
        startPollingCellStatuses();
        
        // Indexing started successfully
      } else {
        // Error starting indexing
        setIndexingState((prev) => ({
          ...prev,
          status: "failed",
        }));
        setError(
          `Failed to start indexing: ${actualResult?.error || "Unknown error"}`
        );
      }
    } catch (err: any) {
      console.error("Start indexing error details:", err);
      console.error("Error type:", typeof err);
      console.error("Error message:", err?.message);
      console.error("Error stack:", err?.stack);

      setIndexingState((prev) => ({
        ...prev,
        status: "failed",
      }));

      const errorMessage = err?.message || err?.error || String(err);
      setError(`Failed to start indexing: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [
    stepData.index.bbox,
    stepData.index.gridTiles,
    stepData.mapping.geoField,
    stepData.index.executionMode,
    client,
    clearMessages,
    indexingState.cells,
    indexingState.active_cells,
    setIndexingState,
  ]);

  const startPollingCellStatuses = useCallback(() => {
    const pollInterval = setInterval(async () => {
      try {
        const result = await client.get_cell_statuses();
        if (result?.status === "found" && result?.cell_statuses) {
          console.log("Polled cell statuses:", result.cell_statuses);

          // Update grid cells with statuses
          setStepData((prev) => ({
            ...prev,
            index: {
              ...prev.index,
              gridCells: result.cell_statuses,
            },
          }));

          // Check if all cells are completed
          const allCompleted = result.cell_statuses.every(
            (cell: any) =>
              cell.status === "completed" || cell.status === "failed"
          );

          if (allCompleted) {
            clearInterval(pollInterval);
            setStepData((prev) => ({
              ...prev,
              index: {
                ...prev.index,
                indexingStatus: "completed",
              },
            }));
            // Indexing completed successfully
          }
        }
      } catch (err) {
        console.error("Error polling cell statuses:", err);
      }
    }, 2000); // Poll every 2 seconds

    // Store interval ID for cleanup
    return () => clearInterval(pollInterval);
  }, [client]);

  // Watch operator event handlers for real-time updates
  useEffect(() => {
    const handleIndexingStarted = (data: any) => {
      console.log("Indexing started event:", data);
      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          indexingStatus: "running",
        },
      }));
    };

    const handleCellStatusUpdate = (data: any) => {
      console.log("Cell status update:", data);
      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          gridCells: prev.index.gridCells.map((cell) =>
            cell.id === data.cell_id
              ? { ...cell, status: data.status, progress: data.progress || 0 }
              : cell
          ),
        },
      }));
    };

    const handleIndexingProgress = (data: any) => {
      console.log("Indexing progress:", data);
      
      // Update the Recoil state with progress information
      setIndexingState((prev) => ({
        ...prev,
        completed_cells: data.completed_cells || 0,
        failed_cells: data.failed_cells || 0,
        rate_limited_cells: data.rate_limited_cells || 0,
        total_features: data.total_features || 0,
        progress: data.progress || 0,
        last_updated: new Date().toISOString(),
      }));
    };

    const handleIndexingCompleted = (data: any) => {
      console.log("Indexing completed:", data);
      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          indexingStatus: "completed",
        },
      }));
      // Indexing completed successfully
    };

    // Note: In a real implementation, you would register these event listeners
    // with the watchExecutor. For now, we'll rely on the watch operator's
    // ctx.trigger() events being handled by the FiftyOne framework.
  }, []);

  const handleNext = useCallback(async () => {
    if (activeStep === 0) {
      // On Index Configuration step, start indexing when Next is clicked
      try {
        setLoading(true);
        clearMessages();
        
        // Start the indexing operation
        await handleStartIndexing();
        
        // If successful, move to next step
        setActiveStep(1);
      } catch (error) {
        console.error("Failed to start indexing:", error);
        setError("Failed to start indexing. Please check your configuration.");
      } finally {
        setLoading(false);
      }
    } else {
      // For other steps, just move to next step
      setActiveStep((prev) => Math.min(prev + 1, 2));
    }
  }, [activeStep, handleStartIndexing, clearMessages, setLoading, setError]);

  const handlePauseIndexing = useCallback(async () => {
    setLoading(true);
    clearMessages();

    try {
      // TODO: Implement pause functionality in Python backend
      console.log("Pausing indexing...");
      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          indexingStatus: "paused",
        },
      }));
      // Indexing paused successfully
    } catch (err) {
      setError(`Failed to pause indexing: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [clearMessages]);

  const handleRetryIndexing = useCallback(async () => {
    if (!stepData.index.bbox || !stepData.mapping.geoField) {
      setError("Please complete previous steps first");
      return;
    }

    // Check if we have a grid in Recoil state
    if (!indexingState.cells || Object.keys(indexingState.cells).length === 0) {
      setError(
        "Please calculate sample distribution first to build the indexing grid"
      );
      return;
    }

    setLoading(true);
    clearMessages();

    try {
      // Reset all cells to idle status for retry
      const resetCells: { [cellId: string]: any } = {};
      Object.keys(indexingState.cells).forEach((cellId) => {
        const cell = indexingState.cells[cellId];
        resetCells[cellId] = {
          ...cell,
          status: (cell.status === "empty" ? "empty" : "idle") as any,
          progress: 0,
          error: null,
          updated_at: new Date().toISOString(),
        };
      });

      // Update Recoil state for retry
      setIndexingState((prev) => ({
        ...prev,
        status: "running",
        cells: resetCells,
        completed_cells: 0,
        failed_cells: 0,
        rate_limited_cells: 0,
        total_features: 0,
        progress: 0,
        started_at: new Date().toISOString(),
        last_updated: new Date().toISOString(),
      }));

      const result = await client.start_indexing({
        bbox: stepData.index.bbox,
        grid_tiles: stepData.index.gridTiles,
        geo_field: stepData.mapping.geoField,
        execution_mode: stepData.index.executionMode,
      });

      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          indexingStatus: "running",
        },
      }));

      if (result?.status === "started") {
        // Indexing retry started successfully
      } else {
        setIndexingState((prev) => ({
          ...prev,
          status: "failed",
        }));
        setError(
          `Failed to retry indexing: ${result?.error || "Unknown error"}`
        );
      }
    } catch (err) {
      setIndexingState((prev) => ({
        ...prev,
        status: "failed",
      }));
      setError(`Failed to retry indexing: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [
    stepData.index.bbox,
    stepData.index.gridTiles,
    stepData.index.executionMode,
    stepData.mapping.geoField,
    client,
    clearMessages,
    indexingState.cells,
    indexingState.active_cells,
    setIndexingState,
  ]);

  const handleCancelIndexing = useCallback(async () => {
    setLoading(true);
    clearMessages();

    try {
      // Abort the running operators
      abortOperationsByURI("@voxel51/metageo/index_grid");
      abortOperationsByURI("@voxel51/metageo/watch_indexing");

      // Also call the backend cancel method to clean up state
      await client.cancel_indexing();
      console.log("Indexing cancelled - operators aborted");

      // Clear Recoil state
      setIndexingState({
        status: "idle",
        cells: {},
        total_cells: 0,
        active_cells: 0,
        completed_cells: 0,
        failed_cells: 0,
        rate_limited_cells: 0,
        total_features: 0,
        progress: 0,
      });

      setStepData((prev) => ({
        ...prev,
        index: {
          ...prev.index,
          indexingStatus: "idle",
        },
      }));
      // Indexing cancelled successfully
    } catch (err) {
      setError(`Failed to cancel indexing: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [client, clearMessages, setIndexingState]);

  const handleEnrich = useCallback(async () => {
    if (!stepData.enrich.prefetchId || !stepData.mapping.geoField) {
      setError("Please complete prefetch and select geo field");
      return;
    }

    setLoading(true);
    clearMessages();

    try {
      const result = await client.enrich({
        geo_field: stepData.mapping.geoField,
        radius_m: stepData.mapping.radius,
        prefetch_id: stepData.enrich.prefetchId,
      });
      setStepData((prev) => ({
        ...prev,
        enrich: {
          ...prev.enrich,
          enrichedCount: result?.samples_enriched || 0,
        },
      }));
      // Sample enrichment completed successfully
    } catch (err) {
      setError(`Failed to enrich samples: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [
    stepData.enrich.prefetchId,
    stepData.mapping.geoField,
    stepData.mapping.radius,
    client,
    clearMessages,
  ]);

  // Step 5: Cleanup
  const handleCleanupIndex = useCallback(async () => {
    setLoading(true);
    clearMessages();

    try {
      const result = await client.cleanup_index({
        prefetch_id: stepData.enrich.prefetchId || undefined,
      });
      // Index cleanup completed successfully
    } catch (err) {
      setError(`Failed to cleanup index: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [stepData.enrich.prefetchId, client, clearMessages]);

  const handleCleanupEnrichedData = useCallback(async () => {
    setLoading(true);
    clearMessages();

    try {
      const result = await client.cleanup_enriched_data();
      // Enriched data cleanup completed successfully
    } catch (err) {
      setError(`Failed to cleanup enriched data: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [client, clearMessages]);

  // Drop Index handler
  const handleDropIndex = useCallback(async () => {
    setLoading(true);
    clearMessages();

    try {
      await client.drop_index();
      setHasExistingIndex(false);
      setExistingIndexData(null);
      setIndexingState((prev) => ({
        ...prev,
        status: "idle",
        cells: {},
        total_cells: 0,
        active_cells: 0,
        completed_cells: 0,
        failed_cells: 0,
        rate_limited_cells: 0,
        total_features: 0,
        progress: 0,
      }));
      setDropIndexDialogOpen(false);
      // Index dropped successfully
    } catch (err) {
      setError(`Failed to drop index: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [client, clearMessages, setIndexingState]);

  const steps = [
    {
      label: "Index Configuration", // STEPS.INDEX_CONFIGURATION
      description: "Set location field, bounds, and sample distribution",
      icon: <SettingsIcon />,
    },
    {
      label: "Indexing", // STEPS.INDEXING
      description: "Run indexing operation and monitor progress",
      icon: <LocationIcon />,
    },
    {
      label: "Mapping", // STEPS.MAPPING
      description: "Configure tag mapping",
      icon: <SettingsIcon />,
    },
    {
      label: "Enrich", // STEPS.ENRICH
      description: "Fetch and apply data",
      icon: <DownloadIcon />,
    },
    {
      label: "Search & Cleanup", // STEPS.SEARCH_CLEANUP
      description: "Create filters and cleanup",
      icon: <SearchIcon />,
    },
  ];

  // Show loading state while fetching geo fields
  if (geoFieldsLoading) {
    return (
      <Box
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          p: 3,
          background: `linear-gradient(135deg, ${alpha(
            theme.palette.primary.main,
            0.05
          )} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
        }}
      >
        <Card
          elevation={3}
          sx={{
            maxWidth: 500,
            width: "100%",
            background: theme.palette.background.paper,
            borderRadius: 3,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mb: 3,
              }}
            >
              <MapIcon
                sx={{
                  fontSize: 64,
                  color: theme.palette.primary.main,
                  mr: 2,
                }}
              />
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  color: theme.palette.text.primary,
                }}
              >
                Metageo
              </Typography>
            </Box>

            <Typography
              variant="h6"
              sx={{
                mb: 2,
                color: theme.palette.text.secondary,
                fontWeight: 500,
              }}
            >
              Analyzing Your Dataset
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: theme.palette.text.secondary,
                lineHeight: 1.6,
              }}
            >
              Checking for geographic fields in your dataset...
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Show warning if no geo fields available
  if (geoFieldsData && !geoFieldsData.can_proceed) {
    return (
      <Box
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          p: 3,
          background: `linear-gradient(135deg, ${alpha(
            theme.palette.warning.main,
            0.08
          )} 0%, ${alpha(theme.palette.error.main, 0.06)} 50%, ${alpha(
            theme.palette.info.main,
            0.04
          )} 100%)`,
        }}
      >
        <Card
          elevation={3}
          sx={{
            maxWidth: 800,
            width: "100%",
            background: theme.palette.background.paper,
            borderRadius: 3,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mb: 3,
              }}
            >
              <WarningIcon
                sx={{
                  fontSize: 64,
                  color: theme.palette.warning.main,
                  mr: 2,
                }}
              />
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  color: theme.palette.text.primary,
                }}
              >
                No Geographic Data Found
              </Typography>
            </Box>

            <Alert
              severity="warning"
              sx={{ mb: 3 }}
              icon={<WarningIcon sx={{ fontSize: 32 }} />}
            >
              <AlertTitle sx={{ fontSize: "1.2rem", fontWeight: 600 }}>
                Cannot Proceed
              </AlertTitle>
              <Typography variant="body1" sx={{ mt: 1 }}>
                The Metageo panel requires geographic data to function, but no
                geographic fields were found in your dataset.
              </Typography>
            </Alert>

            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Dataset Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Dataset:</strong> {geoFieldsData.dataset_name}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Total Fields:</strong> {geoFieldsData.total_fields}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Geographic Fields:</strong>{" "}
                    {geoFieldsData.geo_fields.length}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>All Fields:</strong>{" "}
                    {data?.all_fields?.join(", ") || "None"}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Geo Fields Found:</strong>{" "}
                    {geoFieldsData.geo_fields.join(", ") || "None"}
                  </Typography>
                </Grid>
              </Grid>
            </Box>

            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                How to Add Geographic Data
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                To use the Metageo panel, your dataset must contain geographic
                fields. You can:
              </Typography>
              <Box component="ul" sx={{ pl: 2 }}>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  Import data with latitude/longitude coordinates
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  Add geographic fields manually to your samples
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  Use FiftyOne's geospatial importers for supported formats
                </Typography>
              </Box>
            </Box>

            <Box sx={{ mt: 4, textAlign: "center" }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => window.location.reload()}
              >
                Refresh Dataset
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Intro Screen
  if (!hasStarted) {
    return (
      <Box
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          p: 3,
          background: `linear-gradient(135deg, ${alpha(
            theme.palette.primary.main,
            0.05
          )} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
        }}
      >
        <Card
          elevation={3}
          sx={{
            maxWidth: 500,
            width: "100%",
            background: theme.palette.background.paper,
            borderRadius: 3,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mb: 3,
              }}
            >
              <MapIcon
                sx={{
                  fontSize: 64,
                  color: theme.palette.primary.main,
                  mr: 2,
                }}
              />
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  color: theme.palette.text.primary,
                }}
              >
                Metageo
              </Typography>
            </Box>

            <Typography
              variant="h6"
              sx={{
                mb: 2,
                color: theme.palette.text.secondary,
                fontWeight: 500,
              }}
            >
              Enrich Your Dataset with OpenStreetMap Data
            </Typography>

            <Typography
              variant="body1"
              sx={{
                mb: 4,
                color: theme.palette.text.secondary,
                lineHeight: 1.6,
              }}
            >
              Transform your geospatial dataset by automatically adding rich
              metadata from OpenStreetMap. Discover nearby amenities, road
              networks, land use patterns, and more to enhance your analysis.
            </Typography>

            {geoFieldsData && geoFieldsData.has_geo_fields && (
              <Alert severity="info" sx={{ mb: 4 }}>
                <Typography variant="body2">
                  <strong>Available geographic fields:</strong>{" "}
                  {geoFieldsData.geo_fields.join(", ")}
                </Typography>
              </Alert>
            )}

            <Stack spacing={2} sx={{ mb: 4 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="body2">
                  Automatically detect geographic boundaries
                </Typography>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="body2">
                  Map OSM tags to your dataset schema
                </Typography>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="body2">
                  Enrich samples with contextual data
                </Typography>
              </Box>
            </Stack>

            <Button
              onClick={handleGetStarted}
              size="large"
              sx={{
                width: "100%",
                py: 1.5,
                fontSize: "1.1rem",
                fontWeight: 600,
                borderRadius: 2,
              }}
            >
              <PlayIcon sx={{ mr: 1 }} />
              Get Started
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: theme.palette.background.default,
      }}
    >
      {/* Pinned Header */}
      <Paper
        elevation={1}
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          borderRadius: 0,
          borderBottom: `1px solid ${theme.palette.divider}`,
          background: theme.palette.background.paper,
        }}
      >
        <Box sx={{ p: 2, pb: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", mb: 1.5 }}>
            <MapIcon
              sx={{
                fontSize: 22,
                color: theme.palette.primary.main,
                mr: 1,
              }}
            />
            <Typography
              variant="h6"
              component="h1"
              sx={{
                fontWeight: 600,
                color: theme.palette.text.primary,
                mr: 2,
                minWidth: "fit-content",
              }}
            >
              Metageo
            </Typography>

            {/* Progress Stepper */}
            <Stepper
              activeStep={activeStep}
              alternativeLabel
              sx={{
                flex: 1,
                "& .MuiStepLabel-root": {
                  "& .MuiStepLabel-label": {
                    fontSize: "0.7rem",
                    fontWeight: 500,
                    lineHeight: 1.2,
                    marginTop: 0,
                  },
                },
                "& .MuiStepLabel-iconContainer": {
                  padding: 0.5,
                  marginBottom: 0,
                },
              }}
            >
              {steps.map((step, index) => (
                <Step key={index}>
                  <StepLabel
                    icon={step.icon}
                    sx={{
                      "& .MuiStepLabel-iconContainer": {
                        color:
                          index <= activeStep
                            ? theme.palette.primary.main
                            : theme.palette.grey[400],
                      },
                    }}
                  >
                    {step.label}
                  </StepLabel>
                </Step>
              ))}
            </Stepper>
          </Box>
        </Box>
      </Paper>

      {/* Messages */}
      {(error || success) && (
        <Box sx={{ p: 2 }}>
          {error && (
            <Alert severity="error" onClose={clearMessages} sx={{ mb: 1 }}>
              <AlertTitle>Error</AlertTitle>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" onClose={clearMessages} sx={{ mb: 1 }}>
              <AlertTitle>Success</AlertTitle>
              {success}
            </Alert>
          )}
        </Box>
      )}

      {/* Content Area */}
      <Box sx={{ flex: 1, overflow: "auto", p: 2 }}>
        <Card
          elevation={2}
          sx={{
            minHeight: "100%",
            background: theme.palette.background.paper,
            borderRadius: 2,
          }}
        >
          <CardContent sx={{ p: 3 }}>
            {/* Step Content */}
            {activeStep === STEPS.INDEX_CONFIGURATION && (
              <IndexConfigurationStep
                stepData={stepData}
                setStepData={setStepData}
                loading={loading}
                sampleDistributionLoading={sampleDistributionLoading}
                realSampleDistribution={realSampleDistribution}
                quadtreeCells={quadtreeCells}
                hasExistingIndex={hasExistingIndex}
                existingIndexData={existingIndexData}
                onAutoBbox={handleAutoBbox}
                onCalculateSampleDistribution={handleCalculateSampleDistribution}
                onStartIndexing={handleStartIndexing}
                onPauseIndexing={handlePauseIndexing}
                onRetryIndexing={handleRetryIndexing}
                onCancelIndexing={handleCancelIndexing}
                onDropIndex={handleDropIndex}
                onQuadtreeCellsChange={setQuadtreeCells}
                geoFields={data?.geo_fields || []}
              />
            )}

            {activeStep === STEPS.INDEXING && (
              <IndexingStep
                stepData={stepData}
                onStartIndexing={handleStartIndexing}
                onPauseIndexing={handlePauseIndexing}
                onRetryIndexing={handleRetryIndexing}
                onCancelIndexing={handleCancelIndexing}
                onDropIndex={handleDropIndex}
                hasExistingIndex={hasExistingIndex}
                existingIndexData={existingIndexData}
                loading={loading}
              />
            )}

            {activeStep === STEPS.MAPPING && (
              <MappingStep
                stepData={stepData}
                setStepData={setStepData}
                osmTags={osmTags}
                osmTagsLoading={osmTagsLoading}
                onLoadOsmTags={handleLoadOsmTags}
              />
            )}

            {activeStep === STEPS.ENRICH && (
              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    mb: 3,
                    fontWeight: 600,
                    color: theme.palette.text.primary,
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                  }}
                >
                  <SearchIcon color="primary" />
                  Step 4: Create Search Filters
                </Typography>

                <Typography
                  variant="body2"
                  sx={{
                    mb: 3,
                    color: theme.palette.text.secondary,
                    lineHeight: 1.6,
                  }}
                >
                  Your samples have been enriched! You can now create filters in
                  the sidebar to search through the new OSM data.
                </Typography>

                <Alert severity="info" icon={<InfoIcon />}>
                  <AlertTitle>Ready for Filtering</AlertTitle>
                  Use the sidebar filters to search by the newly added OSM tags
                  and properties. The enriched data is now available as regular
                  FiftyOne fields.
                </Alert>
              </Box>
            )}

            {activeStep === STEPS.SEARCH_CLEANUP && (
              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    mb: 3,
                    fontWeight: 600,
                    color: theme.palette.text.primary,
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                  }}
                >
                  <ClearIcon color="primary" />
                  Step 5: Cleanup
                </Typography>

                <Typography
                  variant="body2"
                  sx={{
                    mb: 3,
                    color: theme.palette.text.secondary,
                    lineHeight: 1.6,
                  }}
                >
                  Optionally remove the indexed OSM data and enriched fields
                  from your dataset to free up space.
                </Typography>

                <Stack spacing={2}>
                  <Button
                    onClick={handleCleanupIndex}
                    disabled={loading}
                    startIcon={<ClearIcon />}
                    variant="outlined"
                    color="warning"
                    size="large"
                  >
                    Remove Indexed OSM Data
                  </Button>
                  <Button
                    onClick={handleCleanupEnrichedData}
                    disabled={loading}
                    startIcon={<ClearIcon />}
                    variant="outlined"
                    color="error"
                    size="large"
                  >
                    Remove Enriched Fields
                  </Button>
                </Stack>

                <Alert severity="warning" icon={<WarningIcon />} sx={{ mt: 2 }}>
                  <AlertTitle>Warning</AlertTitle>
                  These actions will permanently remove data. Make sure you have
                  backups if needed.
                </Alert>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Navigation Footer */}
      <Paper
        elevation={1}
        sx={{
          borderTop: `1px solid ${theme.palette.divider}`,
          background: theme.palette.background.paper,
        }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Button
            onClick={handleBack}
            disabled={activeStep === 0}
            startIcon={<ArrowBackIcon />}
            variant="outlined"
          >
            Back
          </Button>
          <Button
            onClick={handleNext}
            disabled={
              activeStep === steps.length - 1 || 
              (activeStep === 0 && (!stepData.index.bbox || !stepData.mapping.geoField))
            }
            endIcon={<ArrowForwardIcon />}
            variant="contained"
          >
            {activeStep === steps.length - 1 ? "Finish" : activeStep === 0 ? "Start Indexing" : "Next"}
          </Button>
        </Box>
      </Paper>

      {/* Drop Index Confirmation Dialog */}
      <Dialog
        open={dropIndexDialogOpen}
        onClose={() => setDropIndexDialogOpen(false)}
        aria-labelledby="drop-index-dialog-title"
        aria-describedby="drop-index-dialog-description"
      >
        <DialogTitle id="drop-index-dialog-title">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <ClearIcon color="error" />
            Drop Index
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="drop-index-dialog-description">
            Are you sure you want to permanently delete all indexed OSM data? This action cannot be undone and will:
          </DialogContentText>
          <Box sx={{ mt: 2, pl: 2 }}>
            <Typography variant="body2" component="div" sx={{ mb: 1 }}>
              • Remove all OSM feature data from the index
            </Typography>
            <Typography variant="body2" component="div" sx={{ mb: 1 }}>
              • Clear all cell statuses and progress
            </Typography>
            <Typography variant="body2" component="div" sx={{ mb: 1 }}>
              • Reset the indexing state to idle
            </Typography>
            <Typography variant="body2" component="div" sx={{ mb: 1 }}>
              • Require re-indexing to use OSM data again
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setDropIndexDialogOpen(false)}
            color="primary"
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleDropIndex}
            color="error"
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <ClearIcon />}
          >
            {loading ? "Dropping..." : "Drop Index"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
