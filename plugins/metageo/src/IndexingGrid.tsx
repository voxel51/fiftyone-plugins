import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Typography,
  useTheme,
  alpha,
  Tooltip,
  IconButton,
  Chip,
  LinearProgress,
} from "@mui/material";
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
} from "@mui/icons-material";
import { CircularProgress } from "@mui/material";
// Removed direct Recoil usage - this component should receive data via props

export type CellStatus =
  | "idle"
  | "running"
  | "success"
  | "completed"
  | "failed"
  | "empty"
  | "unknown"
  | "rate_limited";

export interface GridCell {
  id: string;
  status: CellStatus;
  progress: number;
  error?: string;
  coordinates: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  sample_count: number;
  osm_features?: number; // OSM features count
  osm_data?: any; // OSM data
  depth?: number; // For quadtree cells
  children?: GridCell[]; // For quadtree cells
}

// Import QuadtreeCell type from MetageoView
interface QuadtreeCell {
  id: string;
  bbox: [number, number, number, number];
  sampleCount: number;
  children?: QuadtreeCell[];
  depth: number;
  maxDepth: number;
  minSize: number;
}

export interface IndexingGridProps {
  bbox: number[] | null;
  onCellStatusChange?: (cellId: string, status: CellStatus) => void;
  realSampleCounts?: { [cellId: string]: number };
  isLoading?: boolean;
  quadtreeCells?: QuadtreeCell[]; // New prop for quadtree cells
  useQuadtree?: boolean; // Flag to use quadtree instead of fixed grid
  indexingStatus?:
    | "idle"
    | "running"
    | "completed"
    | "failed"
    | "cancelled"
    | "paused";
  gridCells?: Array<{
    id: string;
    status: CellStatus;
    progress: number;
    error?: string;
    coordinates: [number, number, number, number];
    sample_count: number;
    osm_data?: any;
    osm_feature_count?: number;
    osm_statistics?: any;
  }>;
}

export default function IndexingGrid({
  bbox,
  onCellStatusChange,
  realSampleCounts,
  isLoading = false,
  quadtreeCells = [],
  useQuadtree = false,
  indexingStatus,
  gridCells = [],
}: IndexingGridProps) {
  console.log("🔍 IndexingGrid: realSampleCounts =", realSampleCounts);
  console.log("🔍 IndexingGrid: gridCells =", gridCells);
  const theme = useTheme();
  const [cells, setCells] = useState<GridCell[]>([]);

  // Real-time indexing state is now passed via props

  // Generate quadtree cells for display
  const generateQuadtreeDisplayCells = useCallback(() => {
    if (!bbox || !quadtreeCells.length) return [];

    return quadtreeCells.map((cell, index) => ({
      id: cell.id,
      status: (cell.sampleCount === 0 ? "empty" : "idle") as CellStatus,
      progress: 0,
      coordinates: cell.bbox,
      sample_count: cell.sampleCount,
      depth: cell.depth || 0,
    }));
  }, [bbox, quadtreeCells]);

  // Generate fixed grid cells (legacy) - now cropped to data extents
  const generateFixedGridCells = useCallback(() => {
    console.log("generateFixedGridCells called");
    console.log("bbox:", bbox);
    console.log("realSampleCounts:", realSampleCounts);
    console.log("isLoading:", isLoading);

    if (!bbox) return [];

    const [minLon, minLat, maxLon, maxLat] = bbox;

    // Calculate data extents from sample distribution
    const calculateDataExtents = () => {
      if (!realSampleCounts || Object.keys(realSampleCounts).length === 0) {
        return {
          dataMinLon: minLon,
          dataMaxLon: maxLon,
          dataMinLat: minLat,
          dataMaxLat: maxLat,
          gridSize: 16,
        };
      }

      const gridSize = Math.sqrt(Object.keys(realSampleCounts).length);
      const lonStep = (maxLon - minLon) / gridSize;
      const latStep = (maxLat - minLat) / gridSize;

      let dataMinLon = maxLon,
        dataMaxLon = minLon;
      let dataMinLat = maxLat,
        dataMaxLat = minLat;

      Object.entries(realSampleCounts).forEach(([cellId, count]) => {
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
      return {
        dataMinLon: Math.max(minLon, dataMinLon - buffer),
        dataMaxLon: Math.min(maxLon, dataMaxLon + buffer),
        dataMinLat: Math.max(minLat, dataMinLat - buffer),
        dataMaxLat: Math.min(maxLat, dataMaxLat + buffer),
        gridSize: Math.max(8, Math.min(50, gridSize)), // Reasonable grid size
      };
    };

    const { dataMinLon, dataMaxLon, dataMinLat, dataMaxLat, gridSize } =
      calculateDataExtents();

    const cells: GridCell[] = [];
    const lonStep = (dataMaxLon - dataMinLon) / gridSize;
    const latStep = (dataMaxLat - dataMinLat) / gridSize;

    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        const cellId = `${row}_${col}`;
        const cellMinLon = dataMinLon + col * lonStep;
        const cellMaxLon = cellMinLon + lonStep;
        const cellMinLat = dataMinLat + row * latStep;
        const cellMaxLat = cellMinLat + latStep;

        let sample_count: number;
        let status: CellStatus;

        if (isLoading) {
          status = "unknown";
          sample_count = -1;
        } else if (
          realSampleCounts &&
          Object.keys(realSampleCounts).length > 0
        ) {
          // Map the cropped grid coordinates back to the original sample distribution
          const originalGridSize = Math.sqrt(
            Object.keys(realSampleCounts).length
          );
          const originalLonStep = (maxLon - minLon) / originalGridSize;
          const originalLatStep = (maxLat - minLat) / originalGridSize;

          // Find which original cells overlap with this cropped cell
          let totalSamples = 0;
          for (let origRow = 0; origRow < originalGridSize; origRow++) {
            for (let origCol = 0; origCol < originalGridSize; origCol++) {
              const origCellId = `${origRow}_${origCol}`;
              const origCellMinLon = minLon + origCol * originalLonStep;
              const origCellMaxLon = origCellMinLon + originalLonStep;
              const origCellMinLat = minLat + origRow * originalLatStep;
              const origCellMaxLat = origCellMinLat + originalLatStep;

              // Check if original cell overlaps with cropped cell
              if (
                origCellMaxLon > cellMinLon &&
                origCellMinLon < cellMaxLon &&
                origCellMaxLat > cellMinLat &&
                origCellMinLat < cellMaxLat
              ) {
                totalSamples += realSampleCounts[origCellId] || 0;
              }
            }
          }

          sample_count = totalSamples;
          status = sample_count === 0 ? "empty" : "idle";
          console.log(
            `Cell ${cellId}: sample_count=${sample_count}, status=${status}`
          );
        } else {
          // No real data yet - show as unknown
          status = "unknown";
          sample_count = -1; // -1 indicates unknown/loading
        }

        cells.push({
          id: cellId,
          status,
          progress: 0,
          coordinates: [cellMinLon, cellMinLat, cellMaxLon, cellMaxLat],
          sample_count,
        });
      }
    }

    return cells;
  }, [bbox, realSampleCounts, isLoading]);

  // Update cells when props change
  useEffect(() => {
    console.log("🔍 IndexingGrid useEffect triggered - regenerating cells");
    console.log("🔍 realSampleCounts:", realSampleCounts);
    console.log("🔍 isLoading:", isLoading);
    console.log("🔍 useQuadtree:", useQuadtree);
    console.log("🔍 quadtreeCells:", quadtreeCells);
    console.log("🔍 gridCells from backend:", gridCells);
    console.log("🔍 indexingStatus:", indexingStatus);

    if (gridCells && gridCells.length > 0) {
      console.log(
        "🔍 Using gridCells from backend - sample counts:",
        gridCells.map((c) => ({ id: c.id, sample_count: c.sample_count }))
      );
      setCells(gridCells);
    } else if (useQuadtree && quadtreeCells.length > 0) {
      console.log("🔍 Using quadtree cells");
      setCells(generateQuadtreeDisplayCells());
    } else {
      console.log("🔍 Using generated fixed grid cells");
      setCells(generateFixedGridCells());
    }
  }, [
    generateFixedGridCells,
    generateQuadtreeDisplayCells,
    realSampleCounts,
    isLoading,
    useQuadtree,
    quadtreeCells,
    gridCells,
    indexingStatus,
  ]);

  const getStatusColor = (status: CellStatus) => {
    switch (status) {
      case "idle":
        return alpha(theme.palette.primary.main, 0.3);
      case "running":
        return alpha(theme.palette.warning.main, 0.6);
      case "success":
      case "completed":
        return alpha(theme.palette.success.main, 0.4);
      case "failed":
        return alpha(theme.palette.error.main, 0.4);
      case "rate_limited":
        return alpha(theme.palette.warning.main, 0.4);
      case "empty":
        return alpha(theme.palette.grey[600], 0.3);
      case "unknown":
        return alpha(theme.palette.info.main, 0.3);
      default:
        return alpha(theme.palette.grey[400], 0.2);
    }
  };

  const getStatusIcon = (status: CellStatus) => {
    const iconSize = useQuadtree ? 14 : 12; // Smaller icons for better fit

    switch (status) {
      case "idle":
        return <PlayIcon sx={{ fontSize: iconSize }} />;
      case "running":
        return <CircularProgress size={iconSize} />;
      case "success":
      case "completed":
        return <CheckCircleIcon sx={{ fontSize: iconSize }} />;
      case "failed":
        return <ErrorIcon sx={{ fontSize: iconSize }} />;
      case "rate_limited":
        return (
          <ErrorIcon
            sx={{ fontSize: iconSize, color: theme.palette.warning.main }}
          />
        );
      case "empty":
        return null;
      case "unknown":
        return <CircularProgress size={iconSize} />;
      default:
        return null;
    }
  };

  const getStatusText = (status: CellStatus) => {
    switch (status) {
      case "idle":
        return "Ready";
      case "running":
        return "Processing...";
      case "success":
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      case "rate_limited":
        return "Rate Limited";
      case "empty":
        return "No samples";
      case "unknown":
        return "Calculating...";
      default:
        return "Unknown";
    }
  };

  const handleCellClick = (cellId: string, currentStatus: CellStatus) => {
    if (currentStatus === "failed" && onCellStatusChange) {
      onCellStatusChange(cellId, "idle");
    }
  };

  if (!bbox) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: 200,
          border: `2px dashed ${theme.palette.divider}`,
          borderRadius: 2,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Define geographic boundaries to view the indexing grid
        </Typography>
      </Box>
    );
  }

  // Calculate grid dimensions for quadtree cells
  const getQuadtreeGridDimensions = () => {
    if (!quadtreeCells.length) return { cols: 0, rows: 0 };

    // For quadtree, we'll arrange cells in a roughly square layout
    const totalCells = quadtreeCells.length;
    const cols = Math.ceil(Math.sqrt(totalCells));
    const rows = Math.ceil(totalCells / cols);

    return { cols, rows };
  };

  // Calculate grid dimensions for fixed grid based on actual data
  const getFixedGridDimensions = () => {
    if (
      !bbox ||
      !realSampleCounts ||
      Object.keys(realSampleCounts).length === 0
    ) {
      return { cols: 16, rows: 16 };
    }

    const gridSize = Math.sqrt(Object.keys(realSampleCounts).length);
    const dynamicGridSize = Math.max(8, Math.min(50, gridSize));
    return { cols: dynamicGridSize, rows: dynamicGridSize };
  };

  const { cols, rows } = useQuadtree
    ? getQuadtreeGridDimensions()
    : getFixedGridDimensions();

  // Calculate progress information from real-time cell data
  const calculateProgress = () => {
    if (
      !indexingStatus ||
      indexingStatus !== "running" ||
      !gridCells ||
      gridCells.length === 0
    ) {
      return {
        progress: 0,
        completed: 0,
        total: 0,
        features: 0,
        processed: 0,
        failed: 0,
        rateLimited: 0,
      };
    }

    // Count cells by status from the real-time grid data
    const total = gridCells.length;
    const completed = gridCells.filter(
      (cell) => cell.status === "completed"
    ).length;
    const failed = gridCells.filter((cell) => cell.status === "failed").length;
    const rateLimited = gridCells.filter(
      (cell) => cell.status === "rate_limited"
    ).length;
    const processed = completed + failed + rateLimited;
    const progress = total > 0 ? (processed / total) * 100 : 0;

    // Calculate total samples from completed cells
    const features = gridCells
      .filter((cell) => cell.status === "completed")
      .reduce((sum, cell) => sum + (cell.sample_count || 0), 0);

    return {
      progress,
      completed,
      total,
      features,
      processed,
      failed,
      rateLimited,
    };
  };

  const progressInfo = calculateProgress();
  const isIndexing = indexingStatus === "running";

  // Debug: Log the final cells state
  console.log(
    "🔍 IndexingGrid render - final cells state:",
    cells.map((c) => ({
      id: c.id,
      sample_count: c.sample_count,
      status: c.status,
    }))
  );

  // Calculate time estimate
  const calculateTimeEstimate = () => {
    if (!isIndexing || !progressInfo.processed || progressInfo.processed === 0)
      return null;

    const elapsed = Date.now() - new Date(Date.now()).getTime();
    const rate = progressInfo.processed / (elapsed / 1000); // cells per second
    const remaining = progressInfo.total - progressInfo.processed;
    const estimatedSeconds = rate > 0 ? remaining / rate : 0;

    if (estimatedSeconds < 60) {
      return `${Math.ceil(estimatedSeconds)}s`;
    } else if (estimatedSeconds < 3600) {
      return `${Math.ceil(estimatedSeconds / 60)}m`;
    } else {
      return `${Math.ceil(estimatedSeconds / 3600)}h ${Math.ceil(
        (estimatedSeconds % 3600) / 60
      )}m`;
    }
  };

  const timeEstimate = calculateTimeEstimate();

  return (
    <Box>
      {/* Progress Bar Section */}
      {isIndexing && (
        <Box
          sx={{
            mb: 3,
            p: 3,
            bgcolor: alpha(theme.palette.primary.main, 0.05),
            borderRadius: 2,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2,
            }}
          >
            <Typography
              variant="h6"
              sx={{ fontWeight: 600, color: theme.palette.primary.main }}
            >
              Indexing Progress
            </Typography>
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              <Chip
                label={`${progressInfo.completed} completed`}
                size="small"
                color="success"
                variant="outlined"
              />
              <Chip
                label={`${progressInfo.failed} failed`}
                size="small"
                color="error"
                variant="outlined"
              />
              <Chip
                label={`${progressInfo.rateLimited} rate limited`}
                size="small"
                color="warning"
                variant="outlined"
              />
              {timeEstimate && (
                <Chip
                  label={`~${timeEstimate} remaining`}
                  size="small"
                  color="info"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}
            >
              <Typography variant="body2" color="text.secondary">
                Processing cells...
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ fontWeight: 600 }}
              >
                {progressInfo.processed}/{progressInfo.total} (
                {progressInfo.progress.toFixed(1)}%)
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressInfo.progress}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                "& .MuiLinearProgress-bar": {
                  borderRadius: 4,
                },
              }}
            />
          </Box>

          {progressInfo.features > 0 && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <CheckCircleIcon fontSize="small" color="success" />
              <strong>{progressInfo.features.toLocaleString()}</strong> samples
              processed so far
            </Typography>
          )}
        </Box>
      )}

      {/* Header Section */}
      <Box sx={{ mb: 2, display: "flex", alignItems: "center", gap: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Geo Index Status
        </Typography>
        <Chip
          label={`${cells.length} cells`}
          size="small"
          color="primary"
          variant="outlined"
        />
        {useQuadtree && (
          <Chip
            label={`${cells.filter((c) => c.sample_count > 0).length} active`}
            size="small"
            color="success"
            variant="outlined"
          />
        )}
        {progressInfo.features > 0 && (
          <Chip
            label={`${progressInfo.features.toLocaleString()} samples`}
            size="small"
            color="success"
            variant="outlined"
          />
        )}
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gap: 1,
          height: "60vh", // Use viewport height instead of fixed height
          maxHeight: "500px", // Cap the maximum height
          minHeight: "200px", // Ensure minimum height
          overflow: "hidden", // Remove scrolling
          p: 1,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 1,
          background: theme.palette.background.paper,
          // Make cells fit the available space
          "& > *": {
            minWidth: 0,
            minHeight: 0,
          },
        }}
      >
        {cells.map((cell) => (
          <Tooltip
            key={cell.id}
            title={
              <Box>
                <Typography variant="caption" display="block">
                  <strong>Cell:</strong> {cell.id}
                </Typography>
                <Typography variant="caption" display="block">
                  <strong>Samples:</strong>{" "}
                  {cell.sample_count === -1
                    ? "Calculating..."
                    : cell.sample_count}
                </Typography>
                <Typography variant="caption" display="block">
                  <strong>Status:</strong> {getStatusText(cell.status)}
                </Typography>
                {useQuadtree && cell.depth !== undefined && (
                  <Typography variant="caption" display="block">
                    <strong>Depth:</strong> {cell.depth}
                  </Typography>
                )}
                <Typography variant="caption" display="block">
                  <strong>Bounds:</strong> [{cell.coordinates[0].toFixed(4)},{" "}
                  {cell.coordinates[1].toFixed(4)}] to [
                  {cell.coordinates[2].toFixed(4)},{" "}
                  {cell.coordinates[3].toFixed(4)}]
                </Typography>
              </Box>
            }
            arrow
          >
            <Box
              onClick={() => handleCellClick(cell.id, cell.status)}
              sx={{
                aspectRatio: "1",
                backgroundColor: getStatusColor(cell.status),
                border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                borderRadius: 0.5,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: cell.status === "failed" ? "pointer" : "default",
                position: "relative",
                // Remove fixed min dimensions to allow scaling
                width: "100%",
                height: "100%",
                fontSize: "0.7rem", // Smaller font for better fit
                "&:hover": {
                  backgroundColor: alpha(getStatusColor(cell.status), 0.8),
                  transform: cell.status === "failed" ? "scale(1.05)" : "none",
                  transition: "all 0.2s ease-in-out",
                },
              }}
            >
              {/* Show sample count if available, otherwise show status icon */}
              {cell.sample_count >= 0 ? (
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: "0.7rem",
                    fontWeight: 600,
                    color: theme.palette.text.primary,
                    textAlign: "center",
                    lineHeight: 1,
                    textShadow: "0 0 2px white",
                  }}
                >
                  {cell.sample_count}
                </Typography>
              ) : (
                getStatusIcon(cell.status)
              )}

              {/* Show sample count for completed cells */}
              {cell.status === "completed" &&
                cell.sample_count &&
                cell.sample_count > 0 && (
                  <Typography
                    variant="caption"
                    sx={{
                      position: "absolute",
                      bottom: 1,
                      right: 1,
                      fontSize: "0.5rem",
                      fontWeight: 600,
                      color: theme.palette.success.main,
                      textShadow: "0 0 2px white",
                      lineHeight: 1,
                    }}
                  >
                    {cell.sample_count} samples
                  </Typography>
                )}
            </Box>
          </Tooltip>
        ))}
      </Box>

      <Box sx={{ mt: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
        <Chip
          icon={<PlayIcon />}
          label="Ready"
          size="small"
          sx={{ backgroundColor: alpha(theme.palette.primary.main, 0.3) }}
        />
        <Chip
          icon={<CircularProgress size={16} />}
          label="Processing"
          size="small"
          sx={{ backgroundColor: alpha(theme.palette.warning.main, 0.6) }}
        />
        <Chip
          icon={<CheckCircleIcon />}
          label="Completed"
          size="small"
          sx={{ backgroundColor: alpha(theme.palette.success.main, 0.4) }}
        />
        <Chip
          icon={<ErrorIcon />}
          label="Failed"
          size="small"
          sx={{ backgroundColor: alpha(theme.palette.error.main, 0.4) }}
        />
        <Chip
          label="Empty"
          size="small"
          sx={{ backgroundColor: alpha(theme.palette.grey[600], 0.3) }}
        />
      </Box>
    </Box>
  );
}
