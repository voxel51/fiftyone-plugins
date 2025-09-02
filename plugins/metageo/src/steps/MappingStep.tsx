import React from "react";
import {
  Box,
  Typography,
  Paper,
  FormControl,
  FormControlLabel,
  Switch,
  Button,
  Stack,
  Grid,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  Autocomplete,
  Chip,
  CircularProgress,
  useTheme,
  alpha,
} from "@mui/material";
// import {
//   SettingsIcon,
//   CodeIcon,
//   ExploreIcon,
// } from "@mui/icons-material";

interface MappingStepProps {
  stepData: any;
  setStepData: (updater: any) => void;
  osmTags: Array<{ key: string; count: number; examples: string[] }>;
  osmTagsLoading: boolean;
  onLoadOsmTags: () => void;
}

export default function MappingStep({
  stepData,
  setStepData,
  osmTags,
  osmTagsLoading,
  onLoadOsmTags,
}: MappingStepProps) {
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
        <span>⚙️</span>
        Step 3: Mapping Configuration
      </Typography>

      <Typography
        variant="body2"
        sx={{
          mb: 3,
          color: theme.palette.text.secondary,
          lineHeight: 1.6,
        }}
      >
        Configure how OpenStreetMap data should be mapped to your
        dataset. Choose between form-based configuration or YAML
        editor.
      </Typography>

      {/* Configuration Mode Toggle */}
      <Box sx={{ mb: 3 }}>
        <FormControl component="fieldset">
          <Typography
            variant="subtitle1"
            sx={{ mb: 2, fontWeight: 600 }}
          >
            Configuration Mode
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button
              variant={
                stepData.mapping.useYamlConfig
                  ? "outlined"
                  : "contained"
              }
              onClick={() =>
                setStepData((prev: any) => ({
                  ...prev,
                  mapping: { ...prev.mapping, useYamlConfig: false },
                }))
              }
              startIcon={<span>⚙️</span>}
            >
              Form Configuration
            </Button>
            <Button
              variant={
                stepData.mapping.useYamlConfig
                  ? "contained"
                  : "outlined"
              }
              onClick={() =>
                setStepData((prev: any) => ({
                  ...prev,
                  mapping: { ...prev.mapping, useYamlConfig: true },
                }))
              }
              startIcon={<span>💻</span>}
            >
              YAML Editor
            </Button>
          </Stack>
        </FormControl>
      </Box>

      {/* OSM Tags Loading */}
      {!stepData.mapping.useYamlConfig && (
        <Box sx={{ mb: 3 }}>
          <Typography
            variant="subtitle1"
            sx={{ mb: 2, fontWeight: 600 }}
          >
            Available OSM Tags
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            <Button
              onClick={onLoadOsmTags}
              disabled={osmTagsLoading}
              startIcon={
                osmTagsLoading ? (
                  <CircularProgress size={20} />
                ) : (
                  <ExploreIcon />
                )
              }
              variant="outlined"
              size="small"
            >
              {osmTagsLoading ? "Loading..." : "Load OSM Tags"}
            </Button>
            {osmTags && (
              <Typography variant="body2" color="text.secondary">
                {osmTags.length} tags available
              </Typography>
            )}
          </Stack>
        </Box>
      )}

      {/* Form Configuration */}
      {!stepData.mapping.useYamlConfig && (
        <Box>
          {/* Basic Configuration */}
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
              Basic Configuration
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="medium">
                  <InputLabel>Radius (meters)</InputLabel>
                  <Select
                    value={stepData.mapping.radius}
                    onChange={(e) =>
                      setStepData((prev: any) => ({
                        ...prev,
                        mapping: {
                          ...prev.mapping,
                          radius: e.target.value as number,
                        },
                      }))
                    }
                    label="Radius (meters)"
                  >
                    <MenuItem value={100}>100m</MenuItem>
                    <MenuItem value={250}>250m</MenuItem>
                    <MenuItem value={500}>500m</MenuItem>
                    <MenuItem value={1000}>1km</MenuItem>
                    <MenuItem value={2500}>2.5km</MenuItem>
                    <MenuItem value={5000}>5km</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* 3D Detections Configuration */}
          <Paper
            elevation={1}
            sx={{
              p: 3,
              mb: 3,
              background: alpha(theme.palette.secondary.main, 0.02),
              border: `1px solid ${alpha(
                theme.palette.secondary.main,
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
              3D Detections
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={stepData.mapping.enable3DDetections}
                  onChange={(e) =>
                    setStepData((prev: any) => ({
                      ...prev,
                      mapping: {
                        ...prev.mapping,
                        enable3DDetections: e.target.checked,
                      },
                    }))
                  }
                />
              }
              label="Enable 3D detections"
            />

            {stepData.mapping.enable3DDetections && (
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="3D Slice"
                      value={stepData.mapping.threeDSlice}
                      onChange={(e) =>
                        setStepData((prev: any) => ({
                          ...prev,
                          mapping: {
                            ...prev.mapping,
                            threeDSlice: e.target.value,
                          },
                        }))
                      }
                      placeholder="e.g., point_cloud"
                      helperText="Name of the 3D slice in your dataset"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Field Name"
                      value={stepData.mapping.detectionFieldName}
                      onChange={(e) =>
                        setStepData((prev: any) => ({
                          ...prev,
                          mapping: {
                            ...prev.mapping,
                            detectionFieldName: e.target.value,
                          },
                        }))
                      }
                      placeholder="e.g., my_detections"
                      helperText="Name for the new detection field"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Autocomplete
                      multiple
                      options={osmTags || []}
                      value={[stepData.mapping.detectionLabelTag].filter(Boolean)}
                      onChange={(_, newValue) =>
                        setStepData((prev: any) => ({
                          ...prev,
                          mapping: {
                            ...prev.mapping,
                            detectionLabelTag: newValue?.[0] || "",
                          },
                        }))
                      }
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="OSM Tags for Labels"
                          placeholder="e.g., type, highway"
                          helperText="Select OSM tags to use as detection labels"
                        />
                      )}
                      renderTags={(value, getTagProps) =>
                        value.map((option, index) => (
                          <Chip
                            {...getTagProps({ index })}
                            key={option}
                            label={option}
                            size="small"
                          />
                        ))
                      }
                    />
                  </Grid>
                </Grid>
              </Box>
            )}
          </Paper>

          {/* Sample Tagging Configuration */}
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
              Sample Tagging
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={stepData.mapping.enableSampleTagging}
                  onChange={(e) =>
                    setStepData((prev: any) => ({
                      ...prev,
                      mapping: {
                        ...prev.mapping,
                        enableSampleTagging: e.target.checked,
                      },
                    }))
                  }
                />
              }
              label="Enable sample tagging"
            />

            {stepData.mapping.enableSampleTagging && (
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Slice"
                      value={stepData.mapping.tagSlice}
                      onChange={(e) =>
                        setStepData((prev: any) => ({
                          ...prev,
                          mapping: {
                            ...prev.mapping,
                            tagSlice: e.target.value,
                          },
                        }))
                      }
                      placeholder="e.g., main"
                      helperText="Slice where tags should be added"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Autocomplete
                      multiple
                      options={osmTags || []}
                      value={stepData.mapping.tagMappings?.map((m: any) => m.osmKey) || []}
                      onChange={(_, newValue) => {
                        // Update tag mappings based on selected OSM keys
                        const newMappings = newValue.map(key => ({
                          osmKey: key,
                          fieldName: `${key}_tag`,
                          fieldType: "string" as const,
                        }));
                        setStepData((prev: any) => ({
                          ...prev,
                          mapping: {
                            ...prev.mapping,
                            tagMappings: newMappings,
                          },
                        }));
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="OSM Tags to Use"
                          placeholder="e.g., building, highway"
                          helperText="Select OSM tags to add as sample fields"
                        />
                      )}
                      renderTags={(value, getTagProps) =>
                        value.map((option, index) => (
                          <Chip
                            {...getTagProps({ index })}
                            key={option}
                            label={option}
                            size="small"
                          />
                        ))
                      }
                    />
                  </Grid>
                </Grid>
              </Box>
            )}
          </Paper>

          {/* Field Mapping Configuration */}
          <Paper
            elevation={1}
            sx={{
              p: 3,
              mb: 3,
              background: alpha(theme.palette.info.main, 0.02),
              border: `1px solid ${alpha(
                theme.palette.info.main,
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
              Field Mapping
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={stepData.mapping.enableFieldMapping}
                  onChange={(e) =>
                    setStepData((prev: any) => ({
                      ...prev,
                      mapping: {
                        ...prev.mapping,
                        enableFieldMapping: e.target.checked,
                      },
                    }))
                  }
                />
              }
              label="Enable field mapping"
            />

            {stepData.mapping.enableFieldMapping && (
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Autocomplete
                      options={osmTags || []}
                      value={stepData.mapping.osmTagName || null}
                      onChange={(_, newValue) =>
                        setStepData((prev: any) => ({
                          ...prev,
                          mapping: {
                            ...prev.mapping,
                            osmTagName: newValue || "",
                          },
                        }))
                      }
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="OSM Tag Name"
                          placeholder="e.g., highway"
                          helperText="Name of the OSM tag to map"
                        />
                      )}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth size="medium">
                      <InputLabel>Field Type</InputLabel>
                      <Select
                        value={stepData.mapping.fieldType}
                        onChange={(e) =>
                          setStepData((prev: any) => ({
                            ...prev,
                            mapping: {
                              ...prev.mapping,
                              fieldType: e.target.value as string,
                            },
                          }))
                        }
                        label="Field Type"
                      >
                        <MenuItem value="string">String</MenuItem>
                        <MenuItem value="int">Integer</MenuItem>
                        <MenuItem value="float">Float</MenuItem>
                        <MenuItem value="bool">Boolean</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Paper>
        </Box>
      )}

      {/* YAML Editor */}
      {stepData.mapping.useYamlConfig && (
        <Paper
          elevation={1}
          sx={{
            p: 3,
            mb: 3,
            background: alpha(theme.palette.warning.main, 0.02),
            border: `1px solid ${alpha(
              theme.palette.warning.main,
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
            YAML Configuration
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 3 }}
          >
            Edit the mapping configuration in YAML format. This allows
            for more advanced and flexible configuration options.
          </Typography>

          <TextField
            fullWidth
            multiline
            rows={15}
            value={stepData.mapping.yamlConfig}
            onChange={(e) =>
              setStepData((prev: any) => ({
                ...prev,
                mapping: {
                  ...prev.mapping,
                  yamlConfig: e.target.value,
                },
              }))
            }
            placeholder="Enter YAML configuration here..."
            variant="outlined"
          />
        </Paper>
      )}
    </Box>
  );
}
