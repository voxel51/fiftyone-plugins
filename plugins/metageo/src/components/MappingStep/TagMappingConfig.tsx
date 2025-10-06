import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  TextField,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme,
  alpha,
  Divider,
  Tooltip,
  Alert,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import type { TagMapping, OsmTag } from "../../types";
import { useMetageoClient } from "../../hooks/useMetageoClient.hook";

interface TagMappingConfigProps {
  tagMappings: TagMapping[];
  osmTags: OsmTag[];
  onAddMapping: (mapping: TagMapping) => void;
  onUpdateMapping: (index: number, mapping: TagMapping) => void;
  onRemoveMapping: (index: number) => void;
}

interface TagMappingFormData {
  osmKey: string;
  fieldName: string;
  boolFalseValues: string; // Comma-separated list of values to consider as false
  distance: number; // Distance threshold in meters
}

// Removed FIELD_TYPE_OPTIONS since we no longer use field types

export default function TagMappingConfig({
  tagMappings,
  osmTags,
  onAddMapping,
  onUpdateMapping,
  onRemoveMapping,
}: TagMappingConfigProps) {
  const theme = useTheme();
  const client = useMetageoClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [usedFieldNames, setUsedFieldNames] = useState<string[]>([]);

  // Load used field names from backend
  useEffect(() => {
    const loadUsedFieldNames = async () => {
      if (client) {
        try {
          const result = await client.get_field_mappings();
          if (result?.result?.status === "success") {
            setUsedFieldNames(result.result.used_field_names || []);
          }
        } catch (error) {
          console.error("Error loading field mappings:", error);
        }
      }
    };
    loadUsedFieldNames();
  }, [client, tagMappings]);

  const [formData, setFormData] = useState<TagMappingFormData>({
    osmKey: "",
    fieldName: "",
    boolFalseValues: "false, no",
    distance: 100, // Default 100 meters
  });

  const handleOpenDialog = (index?: number) => {
    if (index !== undefined) {
      const mapping = tagMappings[index];
      setFormData({
        osmKey: mapping.osmKey,
        fieldName: mapping.fieldName,
        boolFalseValues: mapping.boolFalseValues || "false, no",
        distance: mapping.distance || 100,
      });
      setEditingIndex(index);
    } else {
      setFormData({
        osmKey: "",
        fieldName: "",
        boolFalseValues: "false, no",
        distance: 100,
      });
      setEditingIndex(null);
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingIndex(null);
  };

  const handleSave = () => {
    const mapping: TagMapping = {
      osmKey: formData.osmKey,
      fieldName: formData.fieldName,
      fieldType: "bool", // Always boolean since we're tagging presence/absence
      boolFalseValues: formData.boolFalseValues,
      distance: formData.distance,
    };

    if (editingIndex !== null) {
      onUpdateMapping(editingIndex, mapping);
    } else {
      onAddMapping(mapping);
    }

    handleCloseDialog();
  };

  // Removed getFieldTypeDescription since we no longer use field types

  const getOsmTagExamples = (osmKey: string) => {
    const tag = osmTags.find((t) => t.key === osmKey);
    return tag?.examples || [];
  };

  return (
    <Box>
      <Stack spacing={2}>
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Tag Mappings ({tagMappings.length})
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            size="small"
          >
            Add Tag Mapping
          </Button>
        </Box>

        {/* Mappings List */}
        {tagMappings.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            No tag mappings configured. Click "Add Tag Mapping" to create your
            first mapping.
          </Alert>
        ) : (
          <Stack spacing={1}>
            {tagMappings.map((mapping, index) => (
              <Paper
                key={`${mapping.osmKey}-${mapping.fieldName}-${index}`}
                elevation={1}
                sx={{
                  p: 2,
                  border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                  borderRadius: 1,
                }}
              >
                <Stack direction="row" spacing={2} alignItems="center">
                  <Box sx={{ flex: 1 }}>
                    <Stack direction="row" spacing={2} alignItems="center">
                      <Chip
                        label={mapping.osmKey}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Typography variant="body2" color="text.secondary">
                        →
                      </Typography>
                      <Chip
                        label={mapping.fieldName}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                      <Chip
                        label="Tag"
                        size="small"
                        color="success"
                        variant="filled"
                      />
                      <Typography variant="caption" color="text.secondary">
                        Skip tagging for: {mapping.boolFalseValues}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Distance: {mapping.distance || 100}m
                      </Typography>
                    </Stack>
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="Edit mapping">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(index)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete mapping">
                      <IconButton
                        size="small"
                        onClick={() => onRemoveMapping(index)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}
      </Stack>

      {/* Add/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingIndex !== null ? "Edit Tag Mapping" : "Add Tag Mapping"}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* OSM Key */}
            <Autocomplete
              freeSolo
              options={osmTags.map((tag) => tag.key)}
              value={formData.osmKey}
              onChange={(_, value) => {
                const osmKey = value || "";
                setFormData((prev) => ({
                  ...prev,
                  osmKey,
                  // Auto-populate field name with the same value as OSM key
                  fieldName: osmKey,
                }));
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="OSM Tag Key"
                  placeholder="e.g., building, highway, amenity"
                  helperText="The OSM tag key to map from"
                  required
                />
              )}
              renderOption={(props, option) => {
                const tag = osmTags.find((t) => t.key === option);
                return (
                  <Box component="li" {...props}>
                    <Box sx={{ width: "100%" }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          mb: 0.5,
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {option}
                        </Typography>
                        {tag && (
                          <Typography variant="caption" color="text.secondary">
                            {tag.count} features
                          </Typography>
                        )}
                      </Box>
                      {tag && tag.examples && tag.examples.length > 0 && (
                        <Box
                          sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}
                        >
                          {tag.examples.slice(0, 3).map((example, index) => (
                            <Chip
                              key={index}
                              label={example}
                              size="small"
                              variant="outlined"
                              sx={{
                                fontSize: "0.7rem",
                                height: 20,
                                "& .MuiChip-label": { px: 0.5 },
                              }}
                            />
                          ))}
                          {tag.examples.length > 3 && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ alignSelf: "center" }}
                            >
                              +{tag.examples.length - 3} more
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Box>
                  </Box>
                );
              }}
            />

            {/* Field Name */}
            <TextField
              label="Sample Field Name"
              value={formData.fieldName}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, fieldName: e.target.value }))
              }
              placeholder="e.g., has_building, road_type, amenity_type"
              helperText="The field name where the tag value will be stored on samples"
              required
              error={
                usedFieldNames.includes(formData.fieldName) &&
                formData.fieldName !== ""
              }
              InputProps={{
                endAdornment:
                  usedFieldNames.includes(formData.fieldName) &&
                  formData.fieldName !== "" ? (
                    <Tooltip title="This field name is already used">
                      <InfoIcon color="error" fontSize="small" />
                    </Tooltip>
                  ) : null,
              }}
            />
            {usedFieldNames.includes(formData.fieldName) &&
              formData.fieldName !== "" && (
                <Alert severity="error" size="small">
                  Field name "{formData.fieldName}" is already used in another
                  mapping.
                </Alert>
              )}

            {/* Tag Configuration */}
            <Stack spacing={2}>
              <Typography variant="subtitle2">Tag Configuration</Typography>
              <Alert severity="info">
                <Typography variant="body2">
                  <strong>How it works:</strong> If the OSM tag is present on a
                  sample, the sample will be <strong>tagged</strong>. If the OSM
                  tag value matches any of the "False Values" below, the sample
                  will <strong>NOT be tagged</strong>. All other OSM tag values
                  will result in the sample being <strong>tagged</strong>.
                </Typography>
              </Alert>
              <TextField
                label="False Values"
                value={formData.boolFalseValues}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    boolFalseValues: e.target.value,
                  }))
                }
                helperText="Comma-separated list of OSM tag values that will prevent the sample from being tagged (case-insensitive)"
                placeholder="false, no, off, 0"
                fullWidth
              />
              <TextField
                label="Distance Threshold (meters)"
                type="number"
                value={formData.distance}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    distance: Number(e.target.value),
                  }))
                }
                helperText="Only OSM nodes within this distance from the sample will be considered for tagging"
                inputProps={{ min: 1, max: 10000 }}
                fullWidth
              />
              {formData.osmKey && (
                <Alert severity="info">
                  <Typography variant="body2">
                    Example values for <strong>{formData.osmKey}</strong>:{" "}
                    {getOsmTagExamples(formData.osmKey).join(", ")}
                  </Typography>
                </Alert>
              )}
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={
              !formData.osmKey ||
              !formData.fieldName ||
              (usedFieldNames.includes(formData.fieldName) &&
                (editingIndex === null ||
                  tagMappings[editingIndex]?.fieldName !== formData.fieldName))
            }
          >
            {editingIndex !== null ? "Update" : "Add"} Mapping
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
