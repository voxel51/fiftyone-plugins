import React from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  useTheme,
  alpha,
  CircularProgress,
} from "@mui/material";
import {
  LocationOn as LocationOnIcon,
  Warning as WarningIcon,
  Clear as ClearIcon,
} from "@mui/icons-material";
import { IndexingGrid } from "../IndexingGrid/IndexingGrid";
import { useIndexingState } from "../../hooks/useIndexingState.hook";
import { useMetageoFlow } from "../../hooks/useMetageoFlow.hook";

export default function IndexingStep() {
  const theme = useTheme();
  const { state: indexingState, derived: indexingDerived } = useIndexingState();
  const { actions: flowActions } = useMetageoFlow();

  const handleStartIndexing = async () => {
    const result = await flowActions.startIndexing();
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handlePauseIndexing = async () => {
    // TODO: Implement pause functionality
    console.log("Pausing indexing...");
  };

  const handleRetryIndexing = async () => {
    const result = await flowActions.startIndexing();
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handleCancelIndexing = async () => {
    // TODO: Implement cancel functionality
    console.log("Cancelling indexing...");
  };

  const handleDropIndex = async () => {
    const result = await flowActions.dropIndex();
    if (result.success) {
      // Success handled by the hook
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
        <LocationOnIcon color="primary" />
        Step 2: Indexing
      </Typography>

      <Typography
        variant="body2"
        sx={{
          mb: 3,
          color: theme.palette.text.secondary,
          lineHeight: 1.6,
        }}
      >
        Run the indexing operation to download OpenStreetMap data for each
        geographic region. This step requires the configuration from Step 1.
      </Typography>

      {/* IndexingGrid - Only show if bbox is configured */}
      {indexingState.bbox ? (
        <>
          <IndexingGrid
            bbox={[
              indexingState.bbox.minLon,
              indexingState.bbox.minLat,
              indexingState.bbox.maxLon,
              indexingState.bbox.maxLat,
            ]}
            isLoading={indexingDerived.isIndexing}
            realSampleCounts={indexingState.realSampleDistribution || {}}
            onCellStatusChange={(cellId, status) => {
              console.log(`Cell ${cellId} status changed to ${status}`);
            }}
            quadtreeCells={indexingState.quadtreeCells || []}
            useQuadtree={(indexingState.quadtreeCells || []).length > 0}
            indexingStatus={indexingState.indexingStatus}
            gridCells={indexingState.gridCells || []}
          />

          {/* Indexing Controls */}
          <Paper
            elevation={1}
            sx={{
              p: 3,
              mt: 3,
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
              }}
            >
              Indexing Controls
            </Typography>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Control the indexing process. Start indexing to begin downloading
              OSM data for each geographic region.
            </Typography>

            {indexingDerived.hasExistingIndex && (
              <Box
                sx={{
                  mb: 3,
                  p: 2,
                  bgcolor: alpha(theme.palette.info.main, 0.05),
                  borderRadius: 1,
                  border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    mb: 2,
                  }}
                >
                  <span>ℹ️</span>
                  <strong>Existing index loaded!</strong> You can continue with
                  this index or drop it to start fresh.
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: "block", mb: 2 }}
                >
                  Grid cells: {indexingState.gridCells.length} | Status:{" "}
                  {indexingState.indexingStatus} | Quadtree cells:{" "}
                  {indexingState.quadtreeCells.length}
                </Typography>
                <Button
                  onClick={handleDropIndex}
                  startIcon={<ClearIcon />}
                  variant="outlined"
                  size="small"
                  sx={{
                    borderColor: theme.palette.error.main,
                    color: theme.palette.error.main,
                    "&:hover": {
                      borderColor: theme.palette.error.dark,
                      color: theme.palette.error.dark,
                    },
                  }}
                >
                  Drop Index
                </Button>
              </Box>
            )}

            <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
              <Button
                onClick={handleStartIndexing}
                disabled={!indexingState.bbox || indexingDerived.isIndexing}
                startIcon={<span>▶️</span>}
                variant="contained"
                color="success"
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                {indexingDerived.isIndexing
                  ? "Indexing..."
                  : indexingDerived.hasExistingIndex
                  ? "Resume Indexing"
                  : "Start Indexing"}
              </Button>

              <Button
                onClick={handlePauseIndexing}
                disabled={!indexingDerived.isIndexing}
                startIcon={<span>⏸️</span>}
                variant="outlined"
                color="warning"
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                Pause
              </Button>

              <Button
                onClick={handleRetryIndexing}
                disabled={!indexingDerived.isFailed}
                startIcon={<span>🔄</span>}
                variant="outlined"
                color="info"
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                Retry
              </Button>

              <Button
                onClick={handleCancelIndexing}
                disabled={!indexingDerived.isIndexing}
                startIcon={<span>❌</span>}
                variant="outlined"
                color="error"
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                Cancel & Clear
              </Button>
            </Stack>
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
          <WarningIcon
            sx={{
              fontSize: 48,
              color: theme.palette.warning.main,
              mb: 2,
            }}
          />
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Configuration Required
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please complete the Index Configuration step first to set geographic
            boundaries before you can start indexing.
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
