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
import { QuadtreeConfiguration } from "../QuadtreeConfiguration/QuadtreeConfiguration";
import { useIndexingState } from "../../hooks/useIndexingState.hook";
import { useMappingConfig } from "../../hooks/useMappingConfig.hook";
import { useMetageoFlow } from "../../hooks/useMetageoFlow.hook";
import { useGeoFields } from "../../hooks/useGeoFields.hook";
import type { QuadtreeCell } from "../../types";

export default function IndexConfigurationStep() {
  const theme = useTheme();
  const { state: indexingState, actions: indexingActions } = useIndexingState();
  const { state: mappingConfig, actions: mappingActions } = useMappingConfig();
  const { actions: flowActions } = useMetageoFlow();
  const { geoFields, loading: geoFieldsLoading } = useGeoFields();

  const handleAutoBbox = async () => {
    if (!mappingConfig.geoField) return;

    const result = await flowActions.autoDetectBbox(mappingConfig.geoField);
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handleCalculateDistribution = async () => {
    const result = await flowActions.calculateSampleDistribution();
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handleStartIndexing = async () => {
    const result = await flowActions.startIndexing();
    if (result.success) {
      flowActions.next();
    }
  };

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
        set bounding box boundaries, and calculate sample distribution. This
        step is required before you can start indexing.
      </Typography>

      {/* Geo Field Selection */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          background: alpha(theme.palette.primary.main, 0.02),
          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
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
          <LocationIcon color="primary" />
          Geographic Field Selection
        </Typography>

        <Typography
          variant="body2"
          sx={{ mb: 2, color: theme.palette.text.secondary }}
        >
          Select the geographic field that contains location data for your
          samples.
        </Typography>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Geographic Field</InputLabel>
          <Select
            value={mappingConfig.geoField}
            onChange={(e) => mappingActions.setGeoField(e.target.value)}
            disabled={geoFieldsLoading}
            label="Geographic Field"
          >
            {geoFields.map((field) => (
              <MenuItem key={field} value={field}>
                {field}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {geoFieldsLoading && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="body2" color="text.secondary">
              Loading geographic fields...
            </Typography>
          </Box>
        )}

        {geoFields.length === 0 && !geoFieldsLoading && (
          <Typography variant="body2" color="error">
            No geographic fields found in this dataset.
          </Typography>
        )}
      </Paper>

      {/* Bounding Box Configuration */}
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
          <ExploreIcon color="secondary" />
          Geographic Boundaries
        </Typography>

        <Typography
          variant="body2"
          sx={{ mb: 2, color: theme.palette.text.secondary }}
        >
          Define the geographic area to index. You can auto-detect boundaries or
          set them manually.
        </Typography>

        <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
          <Button
            onClick={handleAutoBbox}
            disabled={geoFieldsLoading || !mappingConfig.geoField}
            startIcon={<ExploreIcon />}
            variant="contained"
            size="large"
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: 2,
              textTransform: "none",
              fontWeight: 600,
            }}
          >
            Auto-detect BBox
          </Button>
        </Stack>

        {/* Manual BBox Inputs */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Min Longitude"
              type="number"
              value={indexingState.bbox?.minLon || ""}
              onChange={(e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value)) {
                  indexingActions.setBbox({
                    ...indexingState.bbox!,
                    minLon: value,
                  });
                }
              }}
              disabled={!indexingState.bbox}
              size="small"
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Min Latitude"
              type="number"
              value={indexingState.bbox?.minLat || ""}
              onChange={(e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value)) {
                  indexingActions.setBbox({
                    ...indexingState.bbox!,
                    minLat: value,
                  });
                }
              }}
              disabled={!indexingState.bbox}
              size="small"
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Max Longitude"
              type="number"
              value={indexingState.bbox?.maxLon || ""}
              onChange={(e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value)) {
                  indexingActions.setBbox({
                    ...indexingState.bbox!,
                    maxLon: value,
                  });
                }
              }}
              disabled={!indexingState.bbox}
              size="small"
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Max Latitude"
              type="number"
              value={indexingState.bbox?.maxLat || ""}
              onChange={(e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value)) {
                  indexingActions.setBbox({
                    ...indexingState.bbox!,
                    maxLat: value,
                  });
                }
              }}
              disabled={!indexingState.bbox}
              size="small"
            />
          </Grid>
        </Grid>

        {/* BBox Status */}
        {indexingState.bbox && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              p: 2,
              bgcolor: alpha(theme.palette.success.main, 0.05),
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`,
            }}
          >
            <Typography
              variant="body2"
              sx={{ display: "flex", alignItems: "center" }}
            >
              <strong>Bounding box configured:</strong>
              {indexingState.bbox.minLon.toFixed(6)},{" "}
              {indexingState.bbox.minLat.toFixed(6)} to{" "}
              {indexingState.bbox.maxLon.toFixed(6)},{" "}
              {indexingState.bbox.maxLat.toFixed(6)}
              <CheckCircleIcon
                sx={{
                  ml: 1,
                  color: theme.palette.success.main,
                  fontSize: 20,
                }}
              />
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Grid Configuration */}
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
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          <DataUsageIcon color="info" />
          Grid Configuration
        </Typography>

        <Typography
          variant="body2"
          sx={{ mb: 2, color: theme.palette.text.secondary }}
        >
          Set the grid resolution for geographic indexing. Higher values create
          more granular regions.
        </Typography>

        <FormControl sx={{ mb: 3, minWidth: 200 }}>
          <InputLabel>Grid Resolution</InputLabel>
          <Select
            value={indexingState.gridTiles}
            onChange={(e) =>
              indexingActions.setGridTiles(e.target.value as number)
            }
            label="Grid Resolution"
          >
            <MenuItem value={3}>3x3 (9 cells)</MenuItem>
            <MenuItem value={9}>9x9 (81 cells)</MenuItem>
            <MenuItem value={10}>10x10 (100 cells)</MenuItem>
            <MenuItem value={16}>16x16 (256 cells)</MenuItem>
            <MenuItem value={25}>25x25 (625 cells)</MenuItem>
            <MenuItem value={50}>50x50 (2,500 cells)</MenuItem>
            <MenuItem value={100}>100x100 (10,000 cells)</MenuItem>
          </Select>
        </FormControl>

        <Stack direction="row" spacing={2}>
          <Button
            onClick={handleCalculateDistribution}
            disabled={
              !indexingState.bbox ||
              !mappingConfig.geoField ||
              !indexingState.gridTiles
            }
            startIcon={<DataUsageIcon />}
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
            Calculate Sample Distribution
          </Button>

          {indexingState.gridCells.length > 0 && (
            <Button
              onClick={indexingActions.clearDistribution}
              startIcon={<ClearIcon />}
              variant="outlined"
              size="large"
              sx={{
                px: 4,
                py: 1.5,
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
              }}
            >
              Clear Distribution
            </Button>
          )}
        </Stack>

        {indexingState.gridCells.length > 0 && (
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
              <CheckCircleIcon
                sx={{
                  color: theme.palette.success.main,
                  fontSize: 20,
                }}
              />
              <strong>Sample distribution calculated!</strong> The grid now
              shows real sample counts for each geographic region.
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Quadtree Configuration */}
      <QuadtreeConfiguration
        sampleDistribution={indexingState.realSampleDistribution}
        bbox={
          indexingState.bbox
            ? [
                indexingState.bbox.minLon,
                indexingState.bbox.minLat,
                indexingState.bbox.maxLon,
                indexingState.bbox.maxLat,
              ]
            : null
        }
        onQuadtreeCellsChange={indexingActions.setQuadtreeCells}
      />

      {/* Start Indexing Button */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          background: alpha(theme.palette.warning.main, 0.02),
          border: `1px solid ${alpha(theme.palette.warning.main, 0.1)}`,
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
          <DataUsageIcon color="warning" />
          Ready to Index
        </Typography>

        <Typography
          variant="body2"
          sx={{ mb: 3, color: theme.palette.text.secondary }}
        >
          Once you've configured the geographic boundaries and calculated the
          sample distribution, you can proceed to start the indexing process.
        </Typography>

        <Button
          onClick={handleStartIndexing}
          disabled={
            !indexingState.bbox ||
            !mappingConfig.geoField ||
            indexingState.gridCells.length === 0
          }
          variant="contained"
          color="success"
          size="large"
          sx={{
            px: 6,
            py: 2,
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
            fontSize: "1.1rem",
          }}
        >
          Start Indexing
        </Button>
      </Paper>
    </Box>
  );
}
