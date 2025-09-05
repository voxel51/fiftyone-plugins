import React from "react";
import {
  Box,
  Typography,
  Paper,
  FormControl,
  Stack,
  Button,
  TextField,
  Autocomplete,
  Switch,
  FormControlLabel,
  useTheme,
  alpha,
  CircularProgress,
  Chip,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  Code as CodeIcon,
  Explore as ExploreIcon,
} from "@mui/icons-material";
import { useMappingConfig } from "../../hooks/useMappingConfig.hook";
import { useOsmTags } from "../../hooks/useOsmTags.hook";

export default function MappingStep() {
  const theme = useTheme();
  const { state: mappingConfig, actions: mappingActions } = useMappingConfig();
  const {
    osmTags,
    loading: osmTagsLoading,
    refetch: loadOsmTags,
  } = useOsmTags();

  const handleLoadOsmTags = async () => {
    await loadOsmTags();
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
        Configure how OpenStreetMap data should be mapped to your dataset. You
        can use either a form-based approach or write YAML configuration.
      </Typography>

      {/* Configuration Mode Toggle */}
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
          <SettingsIcon color="primary" />
          Configuration Mode
        </Typography>

        <Stack direction="row" spacing={2}>
          <Button
            variant={mappingConfig.useYamlConfig ? "outlined" : "contained"}
            onClick={() => mappingActions.setUseYamlConfig(false)}
            startIcon={<SettingsIcon />}
          >
            Form Configuration
          </Button>
          <Button
            variant={mappingConfig.useYamlConfig ? "contained" : "outlined"}
            onClick={() => mappingActions.setUseYamlConfig(true)}
            startIcon={<CodeIcon />}
          >
            YAML Editor
          </Button>
        </Stack>
      </Paper>

      {/* Available OSM Tags */}
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
          <ExploreIcon color="info" />
          Available OSM Tags
        </Typography>

        <Typography
          variant="body2"
          sx={{ mb: 2, color: theme.palette.text.secondary }}
        >
          Load available OSM tags from your indexed data to help configure
          mappings.
        </Typography>

        <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
          <Button
            onClick={handleLoadOsmTags}
            disabled={osmTagsLoading}
            variant="contained"
            startIcon={
              osmTagsLoading ? <CircularProgress size={16} /> : <ExploreIcon />
            }
          >
            {osmTagsLoading ? "Loading..." : "Load OSM Tags"}
          </Button>
        </Stack>

        {osmTags.length > 0 && (
          <Box>
            <Typography variant="body2" sx={{ mb: 2, fontWeight: 600 }}>
              Found {osmTags.length} OSM tag keys:
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
              {osmTags.slice(0, 20).map((tag) => (
                <Chip
                  key={tag.key}
                  label={`${tag.key} (${tag.count})`}
                  size="small"
                  variant="outlined"
                />
              ))}
              {osmTags.length > 20 && (
                <Chip
                  label={`+${osmTags.length - 20} more`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        )}

        {osmTags.length === 0 && !osmTagsLoading && (
          <Typography variant="body2" color="text.secondary">
            No OSM tags found. Please complete the indexing step first.
          </Typography>
        )}
      </Paper>

      {mappingConfig.useYamlConfig ? (
        /* YAML Editor */
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
            <CodeIcon color="secondary" />
            YAML Configuration
          </Typography>

          <TextField
            fullWidth
            multiline
            rows={15}
            value={mappingConfig.yamlConfig}
            onChange={(e) => mappingActions.setYamlConfig(e.target.value)}
            placeholder={`# OSM Mapping Configuration
radius: 100
geoField: "location"

# 3D Detections
enable3DDetections: true
threeDSlice: "detections"
detectionFieldName: "osm_detections"
detectionLabelTag: "type"

# Sample Tagging
enableSampleTagging: true
tagSlice: "metadata"
tagMappings:
  - osmKey: "building"
    fieldName: "has_building"
    fieldType: "bool"
    boolTrueValue: "yes"
  - osmKey: "highway"
    fieldName: "road_type"
    fieldType: "string"

# Field Mapping
enableFieldMapping: true
fieldMappings:
  - osmKey: "name"
    fieldName: "osm_name"
    fieldType: "string"`}
            sx={{
              "& .MuiInputBase-root": {
                fontFamily: "monospace",
                fontSize: "0.875rem",
              },
            }}
          />
        </Paper>
      ) : (
        /* Form Configuration */
        <>
          {/* Basic Configuration */}
          <Paper
            elevation={1}
            sx={{
              p: 3,
              mb: 3,
              background: alpha(theme.palette.success.main, 0.02),
              border: `1px solid ${alpha(theme.palette.success.main, 0.1)}`,
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

            <Stack spacing={2}>
              <TextField
                fullWidth
                label="Radius (meters)"
                type="number"
                value={mappingConfig.radius}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  if (!isNaN(value)) {
                    mappingActions.setRadius(value);
                  }
                }}
                helperText="Maximum distance to search for OSM features around each sample"
              />

              <TextField
                fullWidth
                label="Geographic Field"
                value={mappingConfig.geoField}
                onChange={(e) => mappingActions.setGeoField(e.target.value)}
                helperText="Field containing geographic coordinates for each sample"
              />
            </Stack>
          </Paper>

          {/* 3D Detections */}
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
              }}
            >
              3D Detections
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={mappingConfig.enable3DDetections}
                  onChange={(e) =>
                    mappingActions.setEnable3DDetections(e.target.checked)
                  }
                />
              }
              label="Enable 3D detections"
              sx={{ mb: 2 }}
            />

            {mappingConfig.enable3DDetections && (
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="3D Slice"
                  value={mappingConfig.threeDSlice}
                  onChange={(e) =>
                    mappingActions.setThreeDSlice(e.target.value)
                  }
                  helperText="Slice name for 3D detections (e.g., 'detections')"
                />

                <TextField
                  fullWidth
                  label="Detection Field Name"
                  value={mappingConfig.detectionFieldName}
                  onChange={(e) =>
                    mappingActions.setDetectionFieldName(e.target.value)
                  }
                  helperText="Field name to store OSM detection data"
                />

                <Autocomplete
                  options={osmTags.map((tag) => tag.key)}
                  value={mappingConfig.detectionLabelTag}
                  onChange={(_, value) =>
                    mappingActions.setDetectionLabelTag(value || "")
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Detection Label Tag"
                      helperText="OSM tag to use as detection label (e.g., 'type')"
                    />
                  )}
                  disabled={osmTags.length === 0}
                />
              </Stack>
            )}
          </Paper>

          {/* Sample Tagging */}
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
              }}
            >
              Sample Tagging
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={mappingConfig.enableSampleTagging}
                  onChange={(e) =>
                    mappingActions.setEnableSampleTagging(e.target.checked)
                  }
                />
              }
              label="Enable sample tagging"
              sx={{ mb: 2 }}
            />

            {mappingConfig.enableSampleTagging && (
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="Tag Slice"
                  value={mappingConfig.tagSlice}
                  onChange={(e) => mappingActions.setTagSlice(e.target.value)}
                  helperText="Slice name for sample tags (e.g., 'metadata')"
                />

                <TextField
                  fullWidth
                  label="Tag Radius (meters)"
                  type="number"
                  value={mappingConfig.tagRadius}
                  onChange={(e) => {
                    const value = parseInt(e.target.value);
                    if (!isNaN(value)) {
                      mappingActions.setTagRadius(value);
                    }
                  }}
                  helperText="Maximum distance to search for OSM features for tagging"
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={mappingConfig.renderOn3D}
                      onChange={(e) =>
                        mappingActions.setRenderOn3D(e.target.checked)
                      }
                    />
                  }
                  label="Render on 3D"
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={mappingConfig.renderOn2D}
                      onChange={(e) =>
                        mappingActions.setRenderOn2D(e.target.checked)
                      }
                    />
                  }
                  label="Render on 2D"
                />
              </Stack>
            )}
          </Paper>

          {/* Field Mapping */}
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
              }}
            >
              Field Mapping
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={mappingConfig.enableFieldMapping}
                  onChange={(e) =>
                    mappingActions.setEnableFieldMapping(e.target.checked)
                  }
                />
              }
              label="Enable field mapping"
              sx={{ mb: 2 }}
            />

            {mappingConfig.enableFieldMapping && (
              <Typography variant="body2" color="text.secondary">
                Field mapping configuration will be implemented next. This will
                allow you to map specific OSM tags to dataset fields with type
                conversion.
              </Typography>
            )}
          </Paper>
        </>
      )}

      {/* Reset Button */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          background: alpha(theme.palette.grey[100], 0.5),
          border: `1px solid ${alpha(theme.palette.grey[300], 0.3)}`,
          borderRadius: 2,
        }}
      >
        <Stack direction="row" spacing={2} justifyContent="center">
          <Button
            onClick={() => mappingActions.resetMapping()}
            variant="outlined"
            color="secondary"
            startIcon={<span>🔄</span>}
          >
            Reset Configuration
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
