import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import { useMappingConfig } from "../../hooks/useMappingConfig.hook";
import { useMetageoClient } from "../../hooks/useMetageoClient.hook";
import { useEnrichmentState } from "../../hooks/useEnrichmentState.hook";

export default function EnrichStep() {
  const { state: mappingConfig } = useMappingConfig();
  const client = useMetageoClient();
  const { state: enrichmentState, actions: enrichmentActions } =
    useEnrichmentState();
  const [clearingEnrichmentData, setClearingEnrichmentData] = useState(false);
  const [showClearConfirmation, setShowClearConfirmation] = useState(false);
  const [executionMode, setExecutionMode] = useState<"immediate" | "delegated">("immediate");

  // Get list of fields that will be cleared
  const getFieldsToBeCleared = () => {
    const fields = new Set<string>();

    // Sample tagging fields
    if (mappingConfig.enableSampleTagging) {
      mappingConfig.tagMappings.forEach((mapping) => {
        if (mapping.fieldName) {
          fields.add(mapping.fieldName);
        }
      });
    }

    // Field mapping fields
    if (mappingConfig.enableFieldMapping) {
      mappingConfig.fieldMappings.forEach((mapping) => {
        if (mapping.fieldName) {
          fields.add(mapping.fieldName);
        }
      });
    }

    // Metadata field
    if (mappingConfig.includeAllTagsAsMetadata) {
      fields.add(mappingConfig.metadataFieldName || "osm_metadata");
    }

    // Detection field
    if (mappingConfig.enable3DDetections) {
      fields.add(mappingConfig.detectionFieldName || "detections");
    }

    return Array.from(fields);
  };

  // Get detailed information about fields that will be enriched
  const getFieldsToBeEnriched = () => {
    const fields = [];

    // Sample tagging fields
    if (mappingConfig.enableSampleTagging) {
      mappingConfig.tagMappings.forEach((mapping) => {
        if (mapping.fieldName) {
          fields.push({
            name: mapping.fieldName,
            type: mapping.fieldType || "string",
            category: "Sample Tagging",
            description: `OSM tag "${mapping.osmKey}" → ${
              mapping.fieldType || "string"
            } field`,
            enabled: true,
          });
        }
      });
    }

    // Field mapping fields
    if (mappingConfig.enableFieldMapping) {
      mappingConfig.fieldMappings.forEach((mapping) => {
        if (mapping.fieldName) {
          fields.push({
            name: mapping.fieldName,
            type: mapping.fieldType || "string",
            category: "Field Mapping",
            description: `OSM tag "${mapping.osmKey}" → ${
              mapping.fieldType || "string"
            } field`,
            enabled: true,
          });
        }
      });
    }

    // Metadata field
    if (mappingConfig.includeAllTagsAsMetadata) {
      fields.push({
        name: mappingConfig.metadataFieldName || "osm_metadata",
        type: "list",
        category: "Metadata",
        description: "All OSM features from the grid cell",
        enabled: true,
      });
    }

    // Detection field
    if (mappingConfig.enable3DDetections) {
      fields.push({
        name: mappingConfig.detectionFieldName || "detections",
        type: "list",
        category: "3D Detections",
        description: `3D detections using "${
          mappingConfig.detectionLabelTag || "type"
        }" tag`,
        enabled: true,
      });
    }

    return fields;
  };

  const handleClearEnrichmentData = async () => {
    if (!client || clearingEnrichmentData) return;
    setClearingEnrichmentData(true);
    try {
      const result = await client.clear_enrichment_data();
      if (result?.result?.status === "success") {
        console.log(
          "Enrichment data cleared successfully:",
          result.result.message
        );
      } else {
        console.error(
          "Failed to clear enrichment data:",
          result?.result?.message
        );
      }
    } catch (error) {
      console.error("Error clearing enrichment data:", error);
    } finally {
      setClearingEnrichmentData(false);
      setShowClearConfirmation(false);
    }
  };

  const handleStartEnrichment = async () => {
    if (!client) return;

    try {
      // Save the mapping configuration first
      await client.save_mapping_config({ mapping_config: mappingConfig });

      // Start the enrichment process
      const result = await client.enrich_dataset_async({ execution_mode: executionMode });

      if (result?.result?.status === "success") {
        // Get the enrichment ID from the result
        const enrichmentId =
          result.result.enrichment_id || `enrichment_${Date.now()}`;
        const totalSamples = result.result.total_samples || 0;

        // Start watching the enrichment progress
        await enrichmentActions.startEnrichment(enrichmentId, totalSamples);

        console.log("Enrichment started successfully");
      } else {
        console.error("Failed to start enrichment:", result?.result?.message);
      }
    } catch (error) {
      console.error("Error starting enrichment:", error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
        Step 4: Dataset Enrichment
      </Typography>

      <Typography variant="body1" sx={{ mb: 3, color: "text.secondary" }}>
        Apply your mapping configuration to enrich the dataset with
        OpenStreetMap data. This process runs asynchronously and supports
        multi-dashboard environments.
      </Typography>

      {/* Clear Enrichment Data Button */}
      <Box sx={{ mb: 3, display: "flex", justifyContent: "flex-end" }}>
        <Button
          variant="outlined"
          color="info"
          startIcon={
            clearingEnrichmentData ? (
              <CircularProgress size={20} />
            ) : (
              <DeleteIcon />
            )
          }
          onClick={() => setShowClearConfirmation(true)}
          disabled={clearingEnrichmentData}
          sx={{ minWidth: 200 }}
        >
          {clearingEnrichmentData ? "Clearing..." : "Clear Enrichment Data"}
        </Button>
      </Box>

      {/* Dataset Enrichment Section */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          mb: 3,
          border: `1px solid rgba(0, 0, 0, 0.12)`,
          borderRadius: 1,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Dataset Enrichment
          </Typography>
        </Stack>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Start the enrichment process to apply your mapping configuration to
          the dataset. This process runs asynchronously and supports
          multi-dashboard environments.
        </Typography>

        {/* Enrichment Summary */}
        {getFieldsToBeEnriched().length > 0 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>
                Ready to enrich {getFieldsToBeEnriched().length} field
                {getFieldsToBeEnriched().length !== 1 ? "s" : ""}
              </strong>{" "}
              across your dataset. Each sample will be enriched with
              OpenStreetMap data based on its geographic location and your
              configured mappings.
            </Typography>
          </Alert>
        )}

        {/* Preview of what will be enriched */}
        <Paper
          elevation={0}
          sx={{
            p: 2,
            mb: 3,
            border: `1px solid rgba(0, 0, 0, 0.12)`,
            borderRadius: 1,
            backgroundColor: "rgba(0, 0, 0, 0.02)",
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
            📋 Enrichment Preview
          </Typography>

          {getFieldsToBeEnriched().length > 0 ? (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                The following fields will be populated in your dataset:
              </Typography>

              {/* Group fields by category */}
              {Object.entries(
                getFieldsToBeEnriched().reduce((acc, field) => {
                  if (!acc[field.category]) acc[field.category] = [];
                  acc[field.category].push(field);
                  return acc;
                }, {} as Record<string, any[]>)
              ).map(([category, fields]) => (
                <Box key={category} sx={{ mb: 2 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: 600,
                      color: "primary.main",
                      display: "block",
                      mb: 1,
                    }}
                  >
                    {category}
                  </Typography>
                  <Box
                    sx={{ display: "flex", flexWrap: "wrap", gap: 1, ml: 1 }}
                  >
                    {fields.map((field, index) => (
                      <Chip
                        key={index}
                        label={`${field.name} (${field.type})`}
                        color="primary"
                        variant="filled"
                        size="small"
                        title={field.description}
                      />
                    ))}
                  </Box>
                </Box>
              ))}

              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 2, display: "block" }}
              >
                💡 Hover over field chips to see detailed mapping information
              </Typography>
            </Box>
          ) : (
            <Alert severity="info" sx={{ mb: 0 }}>
              No enrichment fields are configured. Please go back to the Mapping
              step to configure field mappings.
            </Alert>
          )}
        </Paper>

        {/* Execution Mode Selection */}
        {getFieldsToBeEnriched().length > 0 && (
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
        )}

        <Stack direction="row" spacing={2} alignItems="center">
          <Button
            variant="contained"
            onClick={handleStartEnrichment}
            disabled={
              enrichmentState.status === "running" ||
              getFieldsToBeEnriched().length === 0
            }
            sx={{ minWidth: 200 }}
          >
            {enrichmentState.status === "running"
              ? "Enrichment Running..."
              : getFieldsToBeEnriched().length === 0
              ? "No Fields Configured"
              : "Start Enrichment"}
          </Button>

          {enrichmentState.status === "running" && (
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" color="primary" sx={{ mb: 1 }}>
                Enrichment in progress... {enrichmentState.processedSamples}/
                {enrichmentState.totalSamples} samples processed (
                {enrichmentState.progress.toFixed(1)}%)
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <CircularProgress size={20} />
                <Typography variant="caption" color="text.secondary">
                  {enrichmentState.failedSamples > 0 &&
                    `${enrichmentState.failedSamples} failed`}
                </Typography>
              </Box>
            </Box>
          )}

          {enrichmentState.status === "completed" && (
            <Alert severity="success" sx={{ flex: 1 }}>
              Dataset enrichment completed successfully!{" "}
              {enrichmentState.processedSamples} samples processed.
              {enrichmentState.failedSamples > 0 &&
                ` ${enrichmentState.failedSamples} samples failed.`}
            </Alert>
          )}

          {enrichmentState.status === "failed" && (
            <Alert severity="error" sx={{ flex: 1 }}>
              Dataset enrichment failed:{" "}
              {enrichmentState.error || "Unknown error"}
            </Alert>
          )}

          {enrichmentState.status === "cancelled" && (
            <Alert severity="warning" sx={{ flex: 1 }}>
              Dataset enrichment was cancelled.
            </Alert>
          )}
        </Stack>
      </Paper>

      {/* Clear Enrichment Data Confirmation Dialog */}
      <Dialog
        open={showClearConfirmation}
        onClose={() =>
          !clearingEnrichmentData && setShowClearConfirmation(false)
        }
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <DeleteIcon color="warning" />
            Confirm Clear Enrichment Data
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            This action will permanently delete all enrichment data from the
            following fields:
          </Typography>

          {getFieldsToBeCleared().length > 0 ? (
            <Box sx={{ mb: 2 }}>
              {getFieldsToBeCleared().map((fieldName, index) => (
                <Chip
                  key={index}
                  label={fieldName}
                  color="primary"
                  variant="outlined"
                  size="small"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          ) : (
            <Alert severity="info" sx={{ mb: 2 }}>
              No enrichment fields are currently configured. Nothing will be
              cleared.
            </Alert>
          )}

          <Alert severity="warning" sx={{ mt: 2 }}>
            <strong>Warning:</strong> This action cannot be undone. All data in
            these fields will be permanently removed from your dataset.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setShowClearConfirmation(false)}
            disabled={clearingEnrichmentData}
          >
            Cancel
          </Button>
          <Button
            onClick={handleClearEnrichmentData}
            color="error"
            variant="contained"
            disabled={
              clearingEnrichmentData || getFieldsToBeCleared().length === 0
            }
            startIcon={
              clearingEnrichmentData ? (
                <CircularProgress size={20} />
              ) : (
                <DeleteIcon />
              )
            }
          >
            {clearingEnrichmentData ? "Clearing..." : "Clear Data"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
