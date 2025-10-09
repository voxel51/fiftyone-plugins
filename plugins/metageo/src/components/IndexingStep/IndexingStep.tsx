import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  useTheme,
  alpha,
  CircularProgress,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Alert,
} from "@mui/material";
import {
  LocationOn as LocationOnIcon,
  Warning as WarningIcon,
  Clear as ClearIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import { IndexingGrid } from "../IndexingGrid/IndexingGrid";
import { useIndexingState } from "../../hooks/useIndexingState.hook";
import { useMetageoFlow } from "../../hooks/useMetageoFlow.hook";
import CellDataPreview from "../CellDataPreview/CellDataPreview";

export default function IndexingStep() {
  const theme = useTheme();
  const { state: indexingState, derived: indexingDerived, actions: indexingActions } = useIndexingState();
  const { state: flowState, actions: flowActions, derived: flowDerived } = useMetageoFlow();
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [executionMode, setExecutionMode] = useState<"immediate" | "delegated">("immediate");


  const handleStartIndexing = async () => {
    const result = await flowActions.startIndexing(executionMode);
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handlePauseIndexing = async () => {
    // TODO: Implement pause functionality
    console.log("Pausing indexing...");
  };

  const handleRetryIndexing = async () => {
    // First reset failed cells to idle status
    indexingActions.retryFailedCells();
    
    // Then start indexing again
    const result = await flowActions.startIndexing(executionMode);
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handleCancelIndexing = async () => {
    const result = await flowActions.cancelIndexing();
    if (result.success) {
      // Success handled by the hook
      console.log("Indexing cancelled successfully");
    } else {
      console.error("Failed to cancel indexing:", result.error);
    }
  };

  const handleDropIndex = async () => {
    const result = await flowActions.dropIndex();
    if (result.success) {
      // Success handled by the hook
    }
  };


  const handleCellClick = (cellId: string, status: string) => {
    setSelectedCellId(cellId);
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setSelectedCellId(null);
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

      {/* Only show the configuration message if we don't have an existing index */}
      {!flowDerived.hasExistingIndex && (
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
      )}
      
      {/* Show different message if we have an existing index */}
      {flowDerived.hasExistingIndex && (
        <Typography
          variant="body2"
          sx={{
            mb: 3,
            color: theme.palette.text.secondary,
            lineHeight: 1.6,
          }}
        >
          {indexingDerived.isCompleted 
            ? "Indexing completed successfully! You can view the results below or proceed to the next step."
            : indexingDerived.isIndexing
            ? "Indexing is currently in progress. Monitor the grid below to track progress."
            : "Resume or restart the indexing operation to download OpenStreetMap data for each geographic region."
          }
        </Typography>
      )}

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
            onCellStatusChange={handleCellClick}
            quadtreeCells={indexingState.quadtreeCells || []}
            useQuadtree={(indexingState.quadtreeCells || []).length > 0}
            indexingStatus={indexingState.indexingStatus}
            gridCells={indexingState.gridCells || []}
          />

          {/* Completion Message */}
          {indexingDerived.isCompleted && (
            <Paper
              elevation={1}
              sx={{
                p: 3,
                mb: 3,
                background: alpha(theme.palette.success.main, 0.05),
                border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`,
                borderRadius: 2,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                <CheckCircleIcon
                  sx={{
                    fontSize: 32,
                    color: theme.palette.success.main,
                    mr: 2,
                  }}
                />
                <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.success.main }}>
                  Indexing Completed Successfully!
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                All grid cells have been processed. You can now proceed to the Mapping step to configure how OSM data should be mapped to your dataset fields.
              </Typography>
            </Paper>
          )}

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

            {/* Grid Status Warning */}
            {(!indexingState.gridCells || indexingState.gridCells.length === 0) && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Grid not calculated yet.</strong> Please go back to the Index Configuration step 
                  and click "Calculate Sample Distribution" to create the indexing grid before starting indexing.
                </Typography>
              </Alert>
            )}

            {/* Execution Mode Selection */}
            <Box sx={{ mb: 3 }}>
              <FormControl component="fieldset">
                <FormLabel component="legend" sx={{ mb: 1, fontWeight: 600 }}>
                  Execution Mode
                </FormLabel>
                <RadioGroup
                  row
                  value={executionMode}
                  onChange={(e) => setExecutionMode(e.target.value as "immediate" | "delegated")}
                >
                  <FormControlLabel
                    value="immediate"
                    control={<Radio />}
                    label="Immediate (Local)"
                  />
                  <FormControlLabel
                    value="delegated"
                    control={<Radio />}
                    label="Delegated (Remote)"
                  />
                </RadioGroup>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                  {executionMode === "immediate" 
                    ? "Runs locally with real-time progress updates" 
                    : "Runs on remote worker with better resource management"}
                </Typography>
              </FormControl>
            </Box>

            <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
              <Button
                onClick={handleStartIndexing}
                disabled={
                  !indexingState.bbox || 
                  indexingDerived.isIndexing ||
                  !indexingState.gridCells ||
                  indexingState.gridCells.length === 0
                }
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
                  : !indexingState.gridCells || indexingState.gridCells.length === 0
                  ? "Calculate Grid First"
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
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Please complete the Index Configuration step first to set geographic
            boundaries before you can start indexing.
          </Typography>
          <Button
            variant="outlined"
            color="warning"
            onClick={handleDropIndex}
            startIcon={<DeleteIcon />}
            sx={{
              textTransform: "none",
              fontWeight: 600,
            }}
          >
            Clear All Metageo State
          </Button>
        </Paper>
      )}

      {/* Cell Data Preview Dialog */}
      <CellDataPreview
        open={previewOpen}
        onClose={handleClosePreview}
        cellId={selectedCellId || ""}
      />

    </Box>
  );
}
