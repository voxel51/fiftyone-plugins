import React, { useState, useCallback, useMemo } from "react";
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  TextField,
  Stack,
  Grid,
  useTheme,
  alpha,
  CircularProgress,
} from "@mui/material";
import {
  GridOn as GridOnIcon,
  Analytics as DataUsageIcon,
} from "@mui/icons-material";
import type { QuadtreeCell, QuadtreeConfig } from "../../types";

interface QuadtreeConfigurationProps {
  sampleDistribution: { [cellId: string]: number };
  bbox: [number, number, number, number] | null;
  onQuadtreeCellsChange: (cells: QuadtreeCell[]) => void;
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
        Object.entries(sampleDistribution).forEach(([cellId, count]) => {
          if (count > 0) {
            const [row, col] = cellId.split("_").map(Number);
            const gridSize = Math.sqrt(Object.keys(sampleDistribution).length);
            const lonStep = (maxLon - minLon) / gridSize;
            const latStep = (maxLat - minLat) / gridSize;

            const cellMinLon = minLon + col * lonStep;
            const cellMaxLon = cellMinLon + lonStep;
            const cellMinLat = minLat + row * latStep;
            const cellMaxLat = cellMinLat + latStep;

            // Check if this grid cell overlaps with the quadrant
            if (
              cellMinLon < quad.bbox[2] &&
              cellMaxLon > quad.bbox[0] &&
              cellMinLat < quad.bbox[3] &&
              cellMaxLat > quad.bbox[1]
            ) {
              quadrantSampleCount += count;
            }
          }
        });

        return processCell({
          ...quad,
          sampleCount: quadrantSampleCount,
          depth: cell.depth + 1,
          maxDepth: config.maxDepth,
          minSize: config.minSize,
        });
      });
    }

    return cell;
  };

  return [processCell(rootCell)];
};

export function QuadtreeConfiguration({
  sampleDistribution,
  bbox,
  onQuadtreeCellsChange,
}: QuadtreeConfigurationProps) {
  const theme = useTheme();
  const [config, setConfig] = useState<QuadtreeConfig>({
    maxDepth: 4,
    minSize: 0.001,
    threshold: 100,
    maxSamplesPerCell: 1000,
  });
  const [showQuadtree, setShowQuadtree] = useState(false);
  const [quadtreeCells, setQuadtreeCells] = useState<QuadtreeCell[]>([]);
  const [calculating, setCalculating] = useState(false);

  const handleCalculateQuadtree = useCallback(async () => {
    if (!bbox) return;

    setCalculating(true);
    try {
      // Simulate async calculation
      await new Promise((resolve) => setTimeout(resolve, 100));

      const cells = buildQuadtree(sampleDistribution, bbox, config);
      setQuadtreeCells(cells);
      onQuadtreeCellsChange(cells);
      setShowQuadtree(true);
    } catch (error) {
      console.error("Error building quadtree:", error);
    } finally {
      setCalculating(false);
    }
  }, [bbox, sampleDistribution, config, onQuadtreeCellsChange]);

  const totalCells = useMemo(() => {
    const countCells = (cells: QuadtreeCell[]): number => {
      return cells.reduce((total, cell) => {
        return total + 1 + (cell.children ? countCells(cell.children) : 0);
      }, 0);
    };
    return countCells(quadtreeCells);
  }, [quadtreeCells]);

  const totalSamples = useMemo(() => {
    return Object.values(sampleDistribution).reduce(
      (sum, count) => sum + count,
      0
    );
  }, [sampleDistribution]);

  if (!bbox || Object.keys(sampleDistribution).length === 0) {
    return null;
  }

  return (
    <Paper
      elevation={1}
      sx={{
        p: 3,
        mb: 3,
        background: alpha(theme.palette.secondary.main, 0.02),
        border: `1px solid ${alpha(theme.palette.secondary.main, 0.1)}`,
        borderRadius: 2,
      }}
    >
      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 600,
          color: theme.palette.text.primary,
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
      >
        <DataUsageIcon sx={{ mr: 1, color: theme.palette.info.main }} />
        Adaptive Quadtree Grid
      </Typography>

      <Typography
        variant="body2"
        sx={{ mb: 3, color: theme.palette.text.secondary }}
      >
        Generate an adaptive grid that automatically subdivides regions with
        high sample density for more efficient indexing.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <TextField
            fullWidth
            label="Max Depth"
            type="number"
            value={config.maxDepth}
            onChange={(e) => {
              const value = parseInt(e.target.value);
              if (!isNaN(value)) {
                setConfig((prev) => ({ ...prev, maxDepth: value }));
              }
            }}
            size="small"
            inputProps={{ min: 1, max: 10 }}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <TextField
            fullWidth
            label="Min Size (deg)"
            type="number"
            value={config.minSize}
            onChange={(e) => {
              const value = parseFloat(e.target.value);
              if (!isNaN(value)) {
                setConfig((prev) => ({ ...prev, minSize: value }));
              }
            }}
            size="small"
            inputProps={{ min: 0.0001, max: 1, step: 0.0001 }}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <TextField
            fullWidth
            label="Threshold"
            type="number"
            value={config.threshold}
            onChange={(e) => {
              const value = parseInt(e.target.value);
              if (!isNaN(value)) {
                setConfig((prev) => ({ ...prev, threshold: value }));
              }
            }}
            size="small"
            inputProps={{ min: 1, max: 10000 }}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <TextField
            fullWidth
            label="Max Samples/Cell"
            type="number"
            value={config.maxSamplesPerCell}
            onChange={(e) => {
              const value = parseInt(e.target.value);
              if (!isNaN(value)) {
                setConfig((prev) => ({ ...prev, maxSamplesPerCell: value }));
              }
            }}
            size="small"
            inputProps={{ min: 1, max: 100000 }}
          />
        </Grid>
      </Grid>

      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button
          onClick={handleCalculateQuadtree}
          disabled={!bbox || Object.keys(sampleDistribution).length === 0}
          variant="contained"
          startIcon={<GridOnIcon />}
          sx={{ height: 40 }}
        >
          Generate Quadtree
        </Button>
      </Stack>

      {showQuadtree && quadtreeCells.length > 0 && (
        <Box
          sx={{
            mt: 3,
            p: 2,
            bgcolor: alpha(theme.palette.success.main, 0.05),
            borderRadius: 1,
            border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`,
          }}
        >
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Quadtree generated successfully!</strong>
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Total cells: {totalCells} | Total samples: {totalSamples} | Max
            depth: {config.maxDepth} | Min cell size: {config.minSize}°
          </Typography>
        </Box>
      )}

      {calculating && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 2 }}>
          <CircularProgress size={16} />
          <Typography variant="body2" color="text.secondary">
            Generating adaptive grid...
          </Typography>
        </Box>
      )}
    </Paper>
  );
}
