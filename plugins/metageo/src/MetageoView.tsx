import React, { useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stepper,
  Step,
  StepLabel,
  useTheme,
  alpha,
} from "@mui/material";
import {
  PlayArrow as PlayIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
} from "@mui/icons-material";
import { useMetageoFlow, STEPS } from "./hooks/useMetageoFlow.hook";
import IndexConfigurationStep from "./components/IndexConfigurationStep/IndexConfigurationStep";
import IndexingStep from "./components/IndexingStep/IndexingStep";
import MappingStep from "./components/MappingStep/MappingStep";
import EnrichStep from "./components/EnrichStep/EnrichStep";
import SearchCleanupStep from "./components/SearchCleanupStep/SearchCleanupStep";

const stepLabels = [
  "Index Configuration",
  "Indexing",
  "Mapping",
  "Enrich",
  "Search & Cleanup",
];

export default function MetageoView() {
  const theme = useTheme();
  const { state, actions, derived } = useMetageoFlow();
  const hasLoadedRef = useRef(false);

  console.log("🔍 MetageoView render: state =", state, "derived =", derived);

  useEffect(() => {
    // Load existing state when component mounts (only once)
    if (!hasLoadedRef.current) {
      console.log(
        "🔍 MetageoView: useEffect triggered, calling loadCurrentIndexingState"
      );
      hasLoadedRef.current = true;

      // Call loadCurrentIndexingState and handle the result
      actions
        .loadCurrentIndexingState()
        .then((result) => {
          console.log(
            "🔍 MetageoView: loadCurrentIndexingState result:",
            result
          );
          if (result?.success && result?.hasExistingIndex) {
            console.log(
              "🔍 MetageoView: Found existing index, should show indexing step"
            );
          } else {
            console.log("🔍 MetageoView: No existing index found");
          }
        })
        .catch((error) => {
          console.error(
            "🔍 MetageoView: Error loading current indexing state:",
            error
          );
        });
    }
  }, []); // Empty dependency array since we use hasLoadedRef to ensure it only runs once

  // Watch for reset operations and allow reload
  useEffect(() => {
    // If we're on the first step and haven't started, allow reload
    if (state.activeStep === 0 && !state.hasStarted) {
      hasLoadedRef.current = false;
      // Trigger a reload of the current state
      console.log("🔍 MetageoView: Reset detected, reloading state...");
      actions
        .loadCurrentIndexingState()
        .then((result) => {
          console.log("🔍 MetageoView: State reloaded after reset:", result);
        })
        .catch((error) => {
          console.error(
            "🔍 MetageoView: Error reloading state after reset:",
            error
          );
        });
    }
  }, [state.activeStep, state.hasStarted]); // Remove actions dependency to prevent infinite loop

  if (state.isLoadingState) {
    return (
      <Box>
        <Paper
          elevation={1}
          sx={{
            p: 6,
            textAlign: "center",
            borderRadius: 2,
            backgroundColor: theme.palette.background.paper,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Loading Metageo Configuration...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please wait while we check for existing indexing data.
          </Typography>
        </Paper>
      </Box>
    );
  }

  if (!state.hasStarted && !derived.hasExistingIndex) {
    console.log(
      "🔍 MetageoView: Showing Configuration Required - hasStarted =",
      state.hasStarted,
      "hasExistingIndex =",
      derived.hasExistingIndex
    );
    return (
      <Box>
        <Paper
          elevation={1}
          sx={{
            p: 6,
            textAlign: "center",
            background: `linear-gradient(135deg, ${alpha(
              theme.palette.primary.main,
              0.05
            )} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            borderRadius: 3,
          }}
        >
          <Typography
            variant="h3"
            sx={{
              mb: 3,
              fontWeight: 700,
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Welcome to Metageo
          </Typography>

          <Typography
            variant="h6"
            sx={{
              mb: 4,
              color: theme.palette.text.secondary,
              fontWeight: 400,
              lineHeight: 1.6,
            }}
          >
            Enrich your datasets with OpenStreetMap data using intelligent
            geographic indexing
          </Typography>

          <Button
            onClick={actions.start}
            variant="contained"
            size="large"
            startIcon={<PlayIcon />}
            sx={{
              px: 6,
              py: 2,
              borderRadius: 3,
              fontSize: "1.2rem",
              fontWeight: 600,
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              "&:hover": {
                background: `linear-gradient(135deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`,
              },
            }}
          >
            Get Started
          </Button>

          <Box
            sx={{ mt: 4, display: "flex", justifyContent: "center", gap: 3 }}
          >
            <Box sx={{ textAlign: "center" }}>
              <Typography
                variant="h4"
                sx={{ color: theme.palette.primary.main, fontWeight: 600 }}
              >
                🗺️
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Geographic Indexing
              </Typography>
            </Box>
            <Box sx={{ textAlign: "center" }}>
              <Typography
                variant="h4"
                sx={{ color: theme.palette.secondary.main, fontWeight: 600 }}
              >
                🔍
              </Typography>
              <Typography variant="body2" color="text.secondary">
                OSM Integration
              </Typography>
            </Box>
            <Box sx={{ textAlign: "center" }}>
              <Typography
                variant="h4"
                sx={{ color: theme.palette.success.main, fontWeight: 600 }}
              >
                ⚡
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Real-time Updates
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 4,
          background: `linear-gradient(135deg, ${alpha(
            theme.palette.primary.main,
            0.05
          )} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
          borderRadius: 2,
        }}
      >
        <Typography
          variant="h4"
          sx={{
            mb: 1,
            fontWeight: 700,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          Metageo Plugin
        </Typography>
        <Typography variant="body1" color="text.secondary">
          OpenStreetMap Data Enrichment for FiftyOne
        </Typography>
      </Paper>

      {/* Stepper */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 4,
          background: alpha(theme.palette.background.paper, 0.8),
          border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
          borderRadius: 2,
        }}
      >
        <Stepper activeStep={derived.effectiveStep as number} alternativeLabel>
          {stepLabels.map((label, index) => (
            <Step key={label}>
              <StepLabel
                sx={{
                  "& .MuiStepLabel-label": {
                    fontSize: "0.875rem",
                    fontWeight: 500,
                  },
                }}
              >
                {label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Step Content */}
      <Box sx={{ mb: 4 }}>
        {derived.effectiveStep === STEPS.INDEX_CONFIGURATION && (
          <IndexConfigurationStep />
        )}

        {derived.effectiveStep === STEPS.INDEXING && <IndexingStep />}

        {derived.effectiveStep === STEPS.MAPPING && <MappingStep />}

        {derived.effectiveStep === STEPS.ENRICH && <EnrichStep />}

        {derived.effectiveStep === STEPS.SEARCH_CLEANUP && (
          <SearchCleanupStep />
        )}
      </Box>

      {/* Navigation Footer */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          background: alpha(theme.palette.background.paper, 0.9),
          border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
          borderRadius: 2,
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Button
            onClick={actions.back}
            disabled={!derived.canGoBack}
            startIcon={<ArrowBackIcon />}
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
            Back
          </Button>

          <Box sx={{ display: "flex", gap: 2 }}>
            <Button
              onClick={actions.next}
              disabled={!derived.canGoNext}
              endIcon={<ArrowForwardIcon />}
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
              Next
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
