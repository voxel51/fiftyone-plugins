import React from "react";
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
  Chip,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  Explore as ExploreIcon,
  CheckCircle as CheckCircleIcon,
  LocationOn as LocationIcon,
  Analytics as DataUsageIcon,
  Clear as ClearIcon,
} from "@mui/icons-material";
// import IndexingGrid from "../IndexingGrid";
import QuadtreeConfiguration from "../QuadtreeConfiguration";
import type { CellStatus } from "../IndexingGrid";
import type { QuadtreeCell } from "../types";

interface IndexConfigurationStepProps {
  stepData: any;
  setStepData: (updater: any) => void;
  loading: boolean;
  sampleDistributionLoading: boolean;
  realSampleDistribution: { [cellId: string]: number };
  quadtreeCells: QuadtreeCell[];
  hasExistingIndex: boolean;
  existingIndexData: any;
  onAutoBbox: () => void;
  onCalculateSampleDistribution: () => void;
  onStartIndexing: () => void;
  onPauseIndexing: () => void;
  onRetryIndexing: () => void;
  onCancelIndexing: () => void;
  onDropIndex: () => void;
  onQuadtreeCellsChange: (cells: QuadtreeCell[]) => void;
  geoFields: string[];
}

export default function IndexConfigurationStep({
  stepData,
  setStepData,
  loading,
  sampleDistributionLoading,
  realSampleDistribution,
  quadtreeCells,
  hasExistingIndex,
  existingIndexData,
  onAutoBbox,
  onCalculateSampleDistribution,
  onStartIndexing,
  onPauseIndexing,
  onRetryIndexing,
  onCancelIndexing,
  onDropIndex,
  onQuadtreeCellsChange,
  geoFields,
}: IndexConfigurationStepProps) {
  const theme = useTheme();

  return (
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
        <SettingsIcon color="primary" />
        Step 1: Index Configuration
      </Typography>

      <Typography
        variant="body2"
        sx={{
          mb: 3,
          color: theme.palette.text.secondary,
          lineHeight: 1.6,
        }}
      >
        Configure the prerequisites for indexing: select the geographic field, 
        set bounding box boundaries, and calculate sample distribution. 
        This step is required before you can start indexing.
      </Typography>

      {/* Geo Field Selection */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          background: alpha(theme.palette.primary.main, 0.02),
          border: `1px solid ${alpha(
            theme.palette.primary.main,
            0.1
          )}`,
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
          Geographic Field Selection
        </Typography>

        <FormControl fullWidth size="medium" sx={{ mb: 3 }}>
          <InputLabel>Select Geographic Field</InputLabel>
          <Select
            value={stepData.mapping.geoField}
            onChange={(e) =>
              setStepData((prev: any) => ({
                ...prev,
                mapping: {
                  ...prev.mapping,
                  geoField: e.target.value,
                },
              }))
            }
            label="Select Geographic Field"
          >
            <MenuItem value="">
              Choose a field containing geographic data...
            </MenuItem>
            {geoFields?.map((field: string) => (
              <MenuItem key={field} value={field}>
                {field}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          onClick={onAutoBbox}
          disabled={loading || !stepData.mapping.geoField}
                              startIcon={<ExploreIcon />}
          variant="contained"
          size="large"
          sx={{
            mb: 3,
            px: 4,
            py: 1.5,
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
          }}
        >
          Auto-Detect Geographic Boundaries
        </Button>
      </Paper>

      {/* Bounding Box Coordinates */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          background: `linear-gradient(135deg, ${alpha(
            theme.palette.primary.main,
            0.03
          )} 0%, ${alpha(theme.palette.secondary.main, 0.02)} 100%)`,
          border: `1px solid ${alpha(
            theme.palette.primary.main,
            0.15
          )}`,
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: theme.palette.text.primary,
            }}
          >
            Geographic Boundaries
          </Typography>
          {stepData.index.bbox &&
            stepData.index.bbox.every((coord: number) => coord !== 0) && (
                                      <CheckCircleIcon
                          sx={{
                            ml: 1,
                            color: theme.palette.success.main,
                            fontSize: 20,
                          }}
                        />
            )}
        </Box>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 3 }}
        >
          Define the geographic area for OSM data indexing. You can
          auto-detect from your dataset or manually specify
          coordinates.
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 2,
                fontWeight: 600,
                color: theme.palette.text.primary,
              }}
            >
              Southwest Corner (Min)
            </Typography>
            <Stack spacing={2}>
              <TextField
                fullWidth
                size="medium"
                label="Longitude"
                type="number"
                value={stepData.index.bbox?.[0] || ""}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (!isNaN(value)) {
                    const newBbox = [
                      ...(stepData.index.bbox || [0, 0, 0, 0]),
                    ];
                    newBbox[0] = value;
                    setStepData((prev: any) => ({
                      ...prev,
                      index: { ...prev.index, bbox: newBbox },
                    }));
                  }
                }}
                inputProps={{
                  step: 0.000001,
                  placeholder: "e.g., -74.432085",
                }}
                sx={{
                  "& .MuiInputBase-input": {
                    fontFamily: "monospace",
                    fontSize: "0.9rem",
                  },
                }}
              />
              <TextField
                fullWidth
                size="medium"
                label="Latitude"
                type="number"
                value={stepData.index.bbox?.[1] || ""}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (!isNaN(value)) {
                    const newBbox = [
                      ...(stepData.index.bbox || [0, 0, 0, 0]),
                    ];
                    newBbox[1] = value;
                    setStepData((prev: any) => ({
                      ...prev,
                      index: { ...prev.index, bbox: newBbox },
                    }));
                  }
                }}
                inputProps={{
                  step: 0.000001,
                  placeholder: "e.g., 40.542997",
                }}
                sx={{
                  "& .MuiInputBase-input": {
                    fontFamily: "monospace",
                    fontSize: "0.9rem",
                  },
                }}
              />
            </Stack>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 2,
                fontWeight: 600,
                color: theme.palette.text.primary,
              }}
            >
              Northeast Corner (Max)
            </Typography>
            <Stack spacing={2}>
              <TextField
                fullWidth
                size="medium"
                label="Longitude"
                type="number"
                value={stepData.index.bbox?.[2] || ""}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (!isNaN(value)) {
                    const newBbox = [
                      ...(stepData.index.bbox || [0, 0, 0, 0]),
                    ];
                    newBbox[2] = value;
                    setStepData((prev: any) => ({
                      ...prev,
                      index: { ...prev.index, bbox: newBbox },
                    }));
                  }
                }}
                inputProps={{
                  step: 0.000001,
                  placeholder: "e.g., -73.418955",
                }}
                sx={{
                  "& .MuiInputBase-input": {
                    fontFamily: "monospace",
                    fontSize: "0.9rem",
                  },
                }}
              />
              <TextField
                fullWidth
                size="medium"
                label="Latitude"
                type="number"
                value={stepData.index.bbox?.[3] || ""}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (!isNaN(value)) {
                    const newBbox = [
                      ...(stepData.index.bbox || [0, 0, 0, 0]),
                    ];
                    newBbox[3] = value;
                    setStepData((prev: any) => ({
                      ...prev,
                      index: { ...prev.index, bbox: newBbox },
                    }));
                  }
                }}
                inputProps={{
                  step: 0.000001,
                  placeholder: "e.g., 41.041774",
                }}
                sx={{
                  "& .MuiInputBase-input": {
                    fontFamily: "monospace",
                    fontSize: "0.9rem",
                  },
                }}
              />
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {/* Indexing Configuration */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          background: alpha(theme.palette.info.main, 0.02),
          border: `1px solid ${alpha(theme.palette.info.main, 0.1)}`,
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
          Indexing Configuration
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 3 }}
        >
          Configure the indexing process. Currently only immediate
          execution is supported for simplified testing and
          development.
        </Typography>

        <Box
          sx={{
            mt: 3,
            p: 2,
            bgcolor: alpha(theme.palette.info.main, 0.05),
            borderRadius: 1,
          }}
        >
          <Typography
            variant="body2"
            sx={{ display: "flex", alignItems: "center", gap: 1 }}
          >
            <span>ℹ️</span>
            <strong>Immediate Execution:</strong> Indexing runs
            synchronously and completes immediately. Perfect for
            testing and small datasets.
          </Typography>
        </Box>
      </Paper>

      {/* Adaptive Quadtree Grid */}
      {realSampleDistribution &&
        Object.keys(realSampleDistribution).length > 0 &&
        stepData.index.bbox && (
          <QuadtreeConfiguration
            sampleDistribution={realSampleDistribution}
            bbox={stepData.index.bbox}
            onQuadtreeCellsChange={onQuadtreeCellsChange}
          />
        )}

      {/* Sample Distribution Calculation */}
      {stepData.index.bbox && stepData.mapping.geoField && (
        <Paper
          elevation={1}
          sx={{
            p: 3,
            mb: 3,
            background: alpha(theme.palette.success.main, 0.02),
            border: `1px solid ${alpha(
              theme.palette.success.main,
              0.1
            )}`,
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
            Sample Distribution Analysis (Optional)
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 3 }}
          >
            Calculate the real sample distribution across your grid to
            see which geographic regions contain your dataset samples.
            This step is optional - you can start indexing directly
            without calculating the distribution.
          </Typography>

          {/* Grid Size Controls */}
          <Box sx={{ mb: 3 }}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 2,
                fontWeight: 600,
                color: theme.palette.text.primary,
              }}
            >
              Grid Resolution
            </Typography>
            <FormControl fullWidth size="medium">
              <InputLabel>Grid Size</InputLabel>
              <Select
                value={stepData.index.gridTiles}
                onChange={(e) => {
                  const newGridTiles = e.target.value as number;
                  setStepData((prev: any) => ({
                    ...prev,
                    index: { ...prev.index, gridTiles: newGridTiles },
                  }));
                }}
                label="Grid Size"
              >
                <MenuItem value={3}>3x3 (9 cells)</MenuItem>
                <MenuItem value={9}>9x9 (81 cells)</MenuItem>
                <MenuItem value={10}>10x10 (100 cells)</MenuItem>
                <MenuItem value={16}>16x16 (256 cells)</MenuItem>
                <MenuItem value={25}>25x25 (625 cells)</MenuItem>
                <MenuItem value={50}>50x50 (2,500 cells)</MenuItem>
                <MenuItem value={100}>
                  100x100 (10,000 cells)
                </MenuItem>
              </Select>
            </FormControl>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 1, display: "block" }}
            >
              Higher resolution = smaller geographic regions per cell,
              more precise indexing
            </Typography>
          </Box>

          <Stack direction="row" spacing={2}>
            <Button
              onClick={onCalculateSampleDistribution}
              disabled={
                sampleDistributionLoading ||
                !stepData.index.bbox ||
                !stepData.mapping.geoField
              }
              startIcon={
                sampleDistributionLoading ? (
                  <CircularProgress size={20} />
                ) : (
                  <DataUsageIcon />
                )
              }
              variant="contained"
              size="large"
              sx={{
                px: 4,
                py: 1.5,
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
                bgcolor: theme.palette.success.main,
                "&:hover": {
                  bgcolor: theme.palette.success.dark,
                },
              }}
            >
              {sampleDistributionLoading
                ? "Calculating Sample Distribution..."
                : "Calculate Sample Distribution"}
            </Button>

            {stepData.index.gridCells.length > 0 && (
              <Button
                onClick={() => {
                  // Clear the calculated distribution
                  setStepData((prev: any) => ({
                    ...prev,
                    index: { ...prev.index, gridCells: [] },
                  }));
                }}
                startIcon={<ClearIcon />}
                variant="outlined"
                size="large"
                          sx={{
                            px: 4,
                            py: 1.5,
                            borderRadius: 2,
                            textTransform: "none",
                            fontWeight: 600,
                            borderColor: theme.palette.warning.main,
                            color: theme.palette.warning.main,
                            "&:hover": {
                              borderColor: theme.palette.warning.dark,
                              color: theme.palette.warning.dark,
                            },
                          }}
                        >
                          Clear Distribution
                        </Button>
            )}
          </Stack>

          {stepData.index.gridCells.length > 0 && (
            <Box
              sx={{
                mt: 3,
                p: 2,
                bgcolor: alpha(theme.palette.success.main, 0.05),
                borderRadius: 1,
              }}
            >
              <Typography
                variant="body2"
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <span style={{ color: theme.palette.success.main }}>✅</span>
                <strong>Sample distribution calculated!</strong> The
                grid now shows real sample counts for each geographic
                region.
              </Typography>
            </Box>
          )}
        </Paper>
      )}

      {/* Grid Visualization */}
      {stepData.index.bbox ? (
        <>
          <Paper
            elevation={1}
            sx={{
              p: 4,
              textAlign: "center",
              background: alpha(theme.palette.info.main, 0.05),
              border: `1px solid ${alpha(
                theme.palette.info.main,
                0.2
              )}`,
              borderRadius: 2,
            }}
          >
            <span style={{ fontSize: 48, marginBottom: 16, display: 'block' }}>📊</span>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Grid Visualization
            </Typography>
            <Typography variant="body2" color="text.secondary">
              The grid visualization and indexing controls are now available in the Indexing step. 
              Proceed to the next step to see the grid and start indexing.
            </Typography>
          </Paper>

                    <Paper
            elevation={1}
            sx={{
              p: 4,
              textAlign: "center",
              background: alpha(theme.palette.warning.main, 0.05),
              border: `1px solid ${alpha(
                theme.palette.warning.main,
                0.2
              )}`,
              borderRadius: 2,
            }}
          >
            <span style={{ fontSize: 48, marginBottom: 16, display: 'block' }}>⚙️</span>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Indexing Controls
            </Typography>
            <Typography variant="body2" color="text.secondary">
              The indexing controls are now available in the Indexing step. 
              Proceed to the next step to start, pause, or manage your indexing operation.
            </Typography>
          </Paper>
        </>
      ) : (
        <Paper
          elevation={1}
          sx={{
            p: 4,
            textAlign: "center",
            background: alpha(theme.palette.grey[100], 0.5),
            border: `2px dashed ${theme.palette.grey[300]}`,
          }}
        >
          <LocationIcon
            sx={{
              fontSize: 48,
              color: theme.palette.grey[400],
              mb: 2,
            }}
          />
          <Typography variant="body2" color="text.secondary">
            Please set geographic boundaries to continue
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
