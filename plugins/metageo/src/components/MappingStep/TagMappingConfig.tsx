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
  fieldType: "string" | "int" | "float" | "bool";
  boolTrueValue: string;
  boolFalseValue: string;
}

const FIELD_TYPE_OPTIONS = [
  { value: "string", label: "String", description: "Text values" },
  { value: "int", label: "Integer", description: "Whole numbers" },
  { value: "float", label: "Float", description: "Decimal numbers" },
  { value: "bool", label: "Boolean", description: "True/False values" },
];

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
    fieldType: "string",
    boolTrueValue: "yes",
    boolFalseValue: "no",
  });

  const handleOpenDialog = (index?: number) => {
    if (index !== undefined) {
      const mapping = tagMappings[index];
      setFormData({
        osmKey: mapping.osmKey,
        fieldName: mapping.fieldName,
        fieldType: mapping.fieldType,
        boolTrueValue: mapping.boolTrueValue || "yes",
        boolFalseValue: mapping.boolFalseValue || "no",
      });
      setEditingIndex(index);
    } else {
      setFormData({
        osmKey: "",
        fieldName: "",
        fieldType: "string",
        boolTrueValue: "yes",
        boolFalseValue: "no",
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
      fieldType: formData.fieldType,
      boolTrueValue: formData.fieldType === "bool" ? formData.boolTrueValue : undefined,
      boolFalseValue: formData.fieldType === "bool" ? formData.boolFalseValue : undefined,
    };

    if (editingIndex !== null) {
      onUpdateMapping(editingIndex, mapping);
    } else {
      onAddMapping(mapping);
    }

    handleCloseDialog();
  };

  const getFieldTypeDescription = (fieldType: string) => {
    const option = FIELD_TYPE_OPTIONS.find(opt => opt.value === fieldType);
    return option?.description || "";
  };

  const getOsmTagExamples = (osmKey: string) => {
    const tag = osmTags.find(t => t.key === osmKey);
    return tag?.examples || [];
  };

  return (
    <Box>
      <Stack spacing={2}>
        {/* Header */}
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
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
            No tag mappings configured. Click "Add Tag Mapping" to create your first mapping.
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
                        label={mapping.fieldType}
                        size="small"
                        color="default"
                        variant="filled"
                      />
                      {mapping.fieldType === "bool" && (
                        <>
                          <Typography variant="caption" color="text.secondary">
                            {mapping.boolTrueValue} = true
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {mapping.boolFalseValue} = false
                          </Typography>
                        </>
                      )}
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
              options={osmTags.map(tag => tag.key)}
              value={formData.osmKey}
              onChange={(_, value) => {
                const osmKey = value || "";
                setFormData(prev => ({ 
                  ...prev, 
                  osmKey,
                  // Auto-populate field name with the same value as OSM key
                  fieldName: osmKey
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
                const tag = osmTags.find(t => t.key === option);
                return (
                  <Box component="li" {...props}>
                    <Box sx={{ width: "100%" }}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>{option}</Typography>
                        {tag && (
                          <Typography variant="caption" color="text.secondary">
                            {tag.count} features
                          </Typography>
                        )}
                      </Box>
                      {tag && tag.examples && tag.examples.length > 0 && (
                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                          {tag.examples.slice(0, 3).map((example, index) => (
                            <Chip
                              key={index}
                              label={example}
                              size="small"
                              variant="outlined"
                              sx={{ 
                                fontSize: "0.7rem", 
                                height: 20,
                                "& .MuiChip-label": { px: 0.5 }
                              }}
                            />
                          ))}
                          {tag.examples.length > 3 && (
                            <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center" }}>
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
              onChange={(e) => setFormData(prev => ({ ...prev, fieldName: e.target.value }))}
              placeholder="e.g., has_building, road_type, amenity_type"
              helperText="The field name where the tag value will be stored on samples"
              required
              error={usedFieldNames.includes(formData.fieldName) && formData.fieldName !== ""}
              InputProps={{
                endAdornment: usedFieldNames.includes(formData.fieldName) && formData.fieldName !== "" ? (
                  <Tooltip title="This field name is already used">
                    <InfoIcon color="error" fontSize="small" />
                  </Tooltip>
                ) : null,
              }}
            />
            {usedFieldNames.includes(formData.fieldName) && formData.fieldName !== "" && (
              <Alert severity="error" size="small">
                Field name "{formData.fieldName}" is already used in another mapping.
              </Alert>
            )}

            {/* Field Type */}
            <FormControl fullWidth>
              <InputLabel>Field Type</InputLabel>
              <Select
                value={formData.fieldType}
                onChange={(e) => setFormData(prev => ({ ...prev, fieldType: e.target.value as any }))}
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
                    onChange={(e) => setFormData(prev => ({ ...prev, boolTrueValue: e.target.value }))}
                    helperText="OSM value that maps to true"
                    size="small"
                  />
                  <TextField
                    label="False Value"
                    value={formData.boolFalseValue}
                    onChange={(e) => setFormData(prev => ({ ...prev, boolFalseValue: e.target.value }))}
                    helperText="OSM value that maps to false"
                    size="small"
                  />
                </Stack>
                {formData.osmKey && (
                  <Alert severity="info">
                    <Typography variant="body2">
                      Example values for <strong>{formData.osmKey}</strong>: {getOsmTagExamples(formData.osmKey).join(", ")}
                    </Typography>
                  </Alert>
                )}
              </Stack>
            )}

            {/* Examples for other types */}
            {formData.fieldType !== "bool" && formData.osmKey && (
              <Alert severity="info">
                <Typography variant="body2">
                  Example values for <strong>{formData.osmKey}</strong>: {getOsmTagExamples(formData.osmKey).join(", ")}
                </Typography>
              </Alert>
            )}
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
               (editingIndex === null || tagMappings[editingIndex]?.fieldName !== formData.fieldName))
            }
          >
            {editingIndex !== null ? "Update" : "Add"} Mapping
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
