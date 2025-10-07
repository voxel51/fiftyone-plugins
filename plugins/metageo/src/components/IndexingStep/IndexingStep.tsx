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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
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
  const { state: indexingState, derived: indexingDerived } = useIndexingState();
  const { state: flowState, actions: flowActions, derived: flowDerived } = useMetageoFlow();
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);


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
    // First reset failed cells to idle status
    indexingActions.retryFailedCells();
    
    // Then start indexing again
    const result = await flowActions.startIndexing();
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

  const handleStartOver = () => {
    setResetDialogOpen(true);
  };

  const handleConfirmReset = async () => {
    setResetDialogOpen(false);
    const result = await flowActions.resetMetageo();
    if (result.success) {
      // Success handled by the hook
    }
  };

  const handleCancelReset = () => {
    setResetDialogOpen(false);
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

              <Button
                onClick={handleStartOver}
                startIcon={<span>🔄</span>}
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
                Start Over
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

      {/* Reset Confirmation Dialog */}
      <Dialog
        open={resetDialogOpen}
        onClose={handleCancelReset}
        aria-labelledby="reset-dialog-title"
        aria-describedby="reset-dialog-description"
      >
        <DialogTitle id="reset-dialog-title">
          Start Over - Reset All Metageo Data
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="reset-dialog-description">
            This will completely reset all Metageo configuration and indexing data. 
            You will lose:
            <br />• All indexing progress and OSM data
            <br />• Grid configuration and sample distribution
            <br />• Mapping configuration
            <br />• Any completed indexing results
            <br /><br />
            This action cannot be undone. Are you sure you want to start over?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelReset} color="primary">
            Cancel
          </Button>
          <Button onClick={handleConfirmReset} color="error" variant="contained">
            Yes, Start Over
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
