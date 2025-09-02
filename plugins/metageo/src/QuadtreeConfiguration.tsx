import React, { useState, useCallback } from "react";
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  Alert,
  AlertTitle,
  Grid,
  useTheme,
  alpha,
} from "@mui/material";
import { GridOn as GridOnIcon, Analytics as DataUsageIcon } from "@mui/icons-material";
import type { QuadtreeCell, QuadtreeConfig } from "./types";

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

export default function QuadtreeConfiguration({
  sampleDistribution,
  bbox,
  onQuadtreeCellsChange,
}: QuadtreeConfigurationProps) {
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
                                                    startIcon={<GridOnIcon />}
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
}
