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
import type { FieldMapping, OsmTag } from "../../types";
import { useMetageoClient } from "../../hooks/useMetageoClient.hook";

interface FieldMappingConfigProps {
  fieldMappings: FieldMapping[];
  osmTags: OsmTag[];
  onAddMapping: (mapping: FieldMapping) => void;
  onUpdateMapping: (index: number, mapping: FieldMapping) => void;
  onRemoveMapping: (index: number) => void;
}

interface FieldMappingFormData {
  osmKey: string;
  fieldName: string;
  fieldType: "string" | "int" | "float" | "bool" | "enum";
  boolTrueValue: string;
  boolFalseValues: string; // Comma-separated list
  enumMappings: { [key: string]: string };
  defaultValue: string;
  description: string;
  distance: number; // Distance threshold in meters
}

const FIELD_TYPE_OPTIONS = [
  { value: "string", label: "String", description: "Text values" },
  { value: "int", label: "Integer", description: "Whole numbers" },
  { value: "float", label: "Float", description: "Decimal numbers" },
  { value: "bool", label: "Boolean", description: "True/False values" },
  { value: "enum", label: "Enum", description: "Categorical values" },
];

export default function FieldMappingConfig({
  fieldMappings,
  osmTags,
  onAddMapping,
  onUpdateMapping,
  onRemoveMapping,
}: FieldMappingConfigProps) {
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
  }, [client, fieldMappings]);

  const [formData, setFormData] = useState<FieldMappingFormData>({
    osmKey: "",
    fieldName: "",
    fieldType: "string",
    boolTrueValue: "yes",
    boolFalseValues: "false, no",
    enumMappings: {},
    defaultValue: "",
    description: "",
    distance: 100, // Default 100 meters
  });

  const handleOpenDialog = (index?: number) => {
    if (index !== undefined) {
      const mapping = fieldMappings[index];
      setFormData({
        osmKey: mapping.osmKey,
        fieldName: mapping.fieldName,
        fieldType: mapping.fieldType,
        boolTrueValue: mapping.boolTrueValue || "yes",
        boolFalseValues: mapping.boolFalseValues || "false, no",
        enumMappings: mapping.enumMappings || {},
        defaultValue: mapping.defaultValue || "",
        description: mapping.description || "",
        distance: mapping.distance || 100,
      });
      setEditingIndex(index);
    } else {
      setFormData({
        osmKey: "",
        fieldName: "",
        fieldType: "string",
        boolTrueValue: "yes",
        boolFalseValues: "false, no",
        enumMappings: {},
        defaultValue: "",
        description: "",
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
    const mapping: FieldMapping = {
      id:
        editingIndex !== null
          ? fieldMappings[editingIndex].id
          : `mapping_${Date.now()}`,
      osmKey: formData.osmKey,
      fieldName: formData.fieldName,
      fieldType: formData.fieldType,
      boolTrueValue:
        formData.fieldType === "bool" ? formData.boolTrueValue : undefined,
      boolFalseValues:
        formData.fieldType === "bool" ? formData.boolFalseValues : undefined,
      enumMappings:
        formData.fieldType === "enum" ? formData.enumMappings : undefined,
      defaultValue: formData.defaultValue || undefined,
      description: formData.description || undefined,
      distance: formData.distance,
    };

    if (editingIndex !== null) {
      onUpdateMapping(editingIndex, mapping);
    } else {
      onAddMapping(mapping);
    }

    handleCloseDialog();
  };

  const handleAddEnumMapping = () => {
    setFormData((prev) => ({
      ...prev,
      enumMappings: {
        ...prev.enumMappings,
        "": "",
      },
    }));
  };

  const handleUpdateEnumMapping = (
    key: string,
    newKey: string,
    value: string
  ) => {
    setFormData((prev) => {
      const newMappings = { ...prev.enumMappings };
      delete newMappings[key];
      newMappings[newKey] = value;
      return {
        ...prev,
        enumMappings: newMappings,
      };
    });
  };

  const handleRemoveEnumMapping = (key: string) => {
    setFormData((prev) => {
      const newMappings = { ...prev.enumMappings };
      delete newMappings[key];
      return {
        ...prev,
        enumMappings: newMappings,
      };
    });
  };

  const getFieldTypeDescription = (fieldType: string) => {
    const option = FIELD_TYPE_OPTIONS.find((opt) => opt.value === fieldType);
    return option?.description || "";
  };

  const getOsmTagExamples = (osmKey: string) => {
    // This would typically come from the actual OSM data
    // For now, we'll provide some common examples
    const commonExamples: { [key: string]: string[] } = {
      building: ["yes", "house", "apartments", "commercial", "industrial"],
      highway: ["primary", "secondary", "residential", "footway", "cycleway"],
      amenity: ["restaurant", "school", "hospital", "bank", "fuel"],
      landuse: [
        "residential",
        "commercial",
        "industrial",
        "forest",
        "farmland",
      ],
      natural: ["water", "wood", "grassland", "scrub", "bare_rock"],
      leisure: [
        "park",
        "playground",
        "sports_centre",
        "swimming_pool",
        "golf_course",
      ],
      shop: ["supermarket", "bakery", "clothes", "electronics", "books"],
      tourism: ["hotel", "museum", "attraction", "information", "guest_house"],
    };
    return commonExamples[osmKey] || [];
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
            Field Mappings ({fieldMappings.length})
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            size="small"
          >
            Add Mapping
          </Button>
        </Box>

        {/* Mappings List */}
        {fieldMappings.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            No field mappings configured. Click "Add Mapping" to create your
            first mapping.
          </Alert>
        ) : (
          <Stack spacing={1}>
            {fieldMappings.map((mapping, index) => (
              <Paper
                key={mapping.id}
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
                        label={mapping.fieldType}
                        size="small"
                        color="default"
                        variant="filled"
                      />
                    </Stack>
                    {mapping.description && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 0.5, display: "block" }}
                      >
                        {mapping.description}
                      </Typography>
                    )}
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
          {editingIndex !== null ? "Edit Field Mapping" : "Add Field Mapping"}
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
                  helperText={`The OSM tag key to map from (${osmTags.length} available tags)`}
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
              label="Dataset Field Name"
              value={formData.fieldName}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, fieldName: e.target.value }))
              }
              placeholder="e.g., building_type, road_type"
              helperText="The field name in your FiftyOne dataset"
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

            {/* Field Type */}
            <FormControl fullWidth>
              <InputLabel>Field Type</InputLabel>
              <Select
                value={formData.fieldType}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    fieldType: e.target.value as any,
                  }))
                }
                label="Field Type"
              >
                {FIELD_TYPE_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {option.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {option.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Type-specific configuration */}
            {formData.fieldType === "bool" && (
              <Stack spacing={2}>
                <Typography variant="subtitle2">Boolean Mapping</Typography>
                <Stack direction="row" spacing={2}>
                  <TextField
                    label="True Value"
                    value={formData.boolTrueValue}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        boolTrueValue: e.target.value,
                      }))
                    }
                    helperText="OSM value that maps to true"
                    size="small"
                  />
                  <TextField
                    label="False Values"
                    value={formData.boolFalseValues}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        boolFalseValues: e.target.value,
                      }))
                    }
                    helperText="Comma-separated list of OSM values that map to false (case-insensitive)"
                    placeholder="false, no, off, 0"
                    size="small"
                  />
                </Stack>
              </Stack>
            )}

            {formData.fieldType === "enum" && (
              <Stack spacing={2}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="subtitle2">Enum Mappings</Typography>
                  <Button
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={handleAddEnumMapping}
                  >
                    Add Mapping
                  </Button>
                </Box>
                <Stack spacing={1}>
                  {Object.entries(formData.enumMappings).map(([key, value]) => (
                    <Stack
                      key={key}
                      direction="row"
                      spacing={1}
                      alignItems="center"
                    >
                      <TextField
                        label="OSM Value"
                        value={key}
                        onChange={(e) =>
                          handleUpdateEnumMapping(key, e.target.value, value)
                        }
                        size="small"
                        sx={{ flex: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        →
                      </Typography>
                      <TextField
                        label="Dataset Value"
                        value={value}
                        onChange={(e) =>
                          handleUpdateEnumMapping(key, key, e.target.value)
                        }
                        size="small"
                        sx={{ flex: 1 }}
                      />
                      <IconButton
                        size="small"
                        onClick={() => handleRemoveEnumMapping(key)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  ))}
                </Stack>
                {formData.osmKey && (
                  <Alert severity="info">
                    <Typography variant="body2">
                      Common values for <strong>{formData.osmKey}</strong>:{" "}
                      {getOsmTagExamples(formData.osmKey).join(", ")}
                    </Typography>
                  </Alert>
                )}
              </Stack>
            )}

            {/* Default Value */}
            <TextField
              label="Default Value"
              value={formData.defaultValue}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  defaultValue: e.target.value,
                }))
              }
              helperText="Value to use when OSM tag is not found"
              placeholder="e.g., unknown, null, 0"
            />

            {/* Distance Threshold */}
            <TextField
              label="Distance Threshold (meters)"
              type="number"
              value={formData.distance}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  distance: parseFloat(e.target.value) || 100,
                }))
              }
              helperText="OSM tag will only be mapped to the sample if the OSM feature is within this distance threshold from the sample's location. This ensures spatial relevance of the mapped data."
              inputProps={{ min: 1, max: 10000, step: 1 }}
              required
            />

            {/* Description */}
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              helperText="Optional description for documentation"
              multiline
              rows={2}
            />
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
                  fieldMappings[editingIndex]?.fieldName !==
                    formData.fieldName))
            }
          >
            {editingIndex !== null ? "Update" : "Add"} Mapping
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
