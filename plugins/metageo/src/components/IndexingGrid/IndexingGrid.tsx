import React, { useMemo } from "react";
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  Chip,
  useTheme,
  alpha,
} from "@mui/material";
import type { CellStatus, GridCell, QuadtreeCell } from "../../types";

export interface IndexingGridProps {
  bbox: [number, number, number, number] | null;
  isLoading: boolean;
  realSampleCounts: { [cellId: string]: number };
  onCellStatusChange: (cellId: string, status: CellStatus) => void;
  quadtreeCells: QuadtreeCell[];
  useQuadtree: boolean;
  indexingStatus: string;
  gridCells: GridCell[];
}

export function IndexingGrid({
  bbox,
  isLoading,
  realSampleCounts,
  onCellStatusChange,
  quadtreeCells,
  useQuadtree,
  indexingStatus,
  gridCells,
}: IndexingGridProps) {
  const theme = useTheme();

  const progress = useMemo(() => {
    if (gridCells.length === 0) return 0;
    const completedCells = gridCells.filter(
      (cell) => cell.status === "completed"
    ).length;
    return completedCells / gridCells.length;
  }, [gridCells]);

  const statusCounts = useMemo(() => {
    const counts = {
      idle: 0,
      running: 0,
      completed: 0,
      failed: 0,
      rate_limited: 0,
      unknown: 0,
    };

    gridCells.forEach((cell) => {
      counts[cell.status] = (counts[cell.status] || 0) + 1;
    });

    return counts;
  }, [gridCells]);

  if (!bbox) {
    return null;
  }

  const [minLon, minLat, maxLon, maxLat] = bbox;
  const gridSize = useQuadtree
    ? Math.sqrt(quadtreeCells.length)
    : Math.sqrt(gridCells.length);

  return (
    <Paper
      elevation={1}
      sx={{
        p: 3,
        mb: 3,
        background: alpha(theme.palette.background.paper, 0.8),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        borderRadius: 2,
      }}
    >
      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 600,
          color: theme.palette.text.primary,
        }}
      >
        Geo Index Status
      </Typography>

      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 1,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Indexing Progress
          </Typography>
          <Typography variant="body2" fontWeight={600}>
            {Math.round(progress * 100)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={progress * 100}
          sx={{
            height: 8,
            borderRadius: 4,
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            "& .MuiLinearProgress-bar": {
              borderRadius: 4,
            },
          }}
        />
      </Box>

      {/* Status Chips */}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 3 }}>
        <Chip
          label={`Idle: ${statusCounts.idle}`}
          size="small"
          variant="outlined"
          sx={{ borderColor: theme.palette.grey[600] }}
        />
        <Chip
          label={`Running: ${statusCounts.running}`}
          size="small"
          variant="outlined"
          sx={{ borderColor: theme.palette.info.main }}
        />
        <Chip
          label={`Completed: ${statusCounts.completed}`}
          size="small"
          variant="outlined"
          sx={{ borderColor: theme.palette.success.main }}
        />
        <Chip
          label={`Failed: ${statusCounts.failed}`}
          size="small"
          variant="outlined"
          sx={{ borderColor: theme.palette.error.main }}
        />
        <Chip
          label={`Rate Limited: ${statusCounts.rate_limited}`}
          size="small"
          variant="outlined"
          sx={{ borderColor: theme.palette.warning.main }}
        />
      </Box>

      {/* Grid Visualization */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          gap: 1,
          maxWidth: "100%",
          overflow: "auto",
        }}
      >
        {Array.from({ length: gridSize * gridSize }, (_, index) => {
          const row = Math.floor(index / gridSize);
          const col = index % gridSize;
          const cellId = `${row}_${col}`;
          const cell = gridCells.find((c) => c.id === cellId);
          const sampleCount = realSampleCounts[cellId] || 0;
          const status = cell?.status || "unknown";

          const getStatusColor = (status: CellStatus) => {
            switch (status) {
              case "completed":
                return theme.palette.success.main;
              case "running":
                return theme.palette.info.main;
              case "failed":
                return theme.palette.error.main;
              case "rate_limited":
                return theme.palette.warning.main;
              case "idle":
                return theme.palette.grey[600];
              default:
                return theme.palette.grey[300];
            }
          };

          const getStatusLabel = (status: CellStatus) => {
            switch (status) {
              case "completed":
                return "✓";
              case "running":
                return "⟳";
              case "failed":
                return "✗";
              case "rate_limited":
                return "⏱";
              case "idle":
                return sampleCount > 0 ? "○" : "·";
              default:
                return "?";
            }
          };

          return (
            <Box
              key={cellId}
              sx={{
                width: 20,
                height: 20,
                backgroundColor: getStatusColor(status),
                borderRadius: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.75rem",
                color: "white",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s ease",
                "&:hover": {
                  transform: "scale(1.2)",
                  zIndex: 1,
                },
              }}
              title={`Cell ${cellId}: ${status} (${sampleCount} samples)`}
              onClick={() => onCellStatusChange(cellId, status)}
            >
              {getStatusLabel(status)}
            </Box>
          );
        })}
      </Box>

      {/* Grid Info */}
      <Box
        sx={{
          mt: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Grid: {gridSize}x{gridSize} ({gridSize * gridSize} cells)
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {useQuadtree ? "Adaptive Quadtree" : "Fixed Grid"}
        </Typography>
      </Box>
    </Paper>
  );
}
