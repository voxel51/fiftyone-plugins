import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  Switch,
  FormControlLabel,
  TextField,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
} from "@mui/material";
import {
  Code as CodeIcon,
  Explore as ExploreIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
} from "@mui/icons-material";
import { useMappingConfig } from "../../hooks/useMappingConfig.hook";
import { useOsmTags } from "../../hooks/useOsmTags.hook";
import { useMetageoClient } from "../../hooks/useMetageoClient.hook";
import { useDatasetInfo } from "../../hooks/useDatasetInfo.hook";
import FieldMappingConfig from "./FieldMappingConfig";
import TagMappingConfig from "./TagMappingConfig";
import type { OsmTag } from "../../types";

export default function MappingStep() {
  const theme = useTheme();
  const { state: mappingConfig, actions: mappingActions } = useMappingConfig();
  const {
    osmTags,
    loading: osmTagsLoading,
    error: osmTagsError,
    hasLoaded: osmTagsHasLoaded,
    refetch: loadOsmTags,
  } = useOsmTags();
  const {
    datasetInfo,
    loading: datasetInfoLoading,
    refetch: refetchDatasetInfo,
  } = useDatasetInfo();

  // Force refresh dataset info when component mounts
  React.useEffect(() => {
    console.log(
      "🔍 MappingStep: Component mounted, forcing dataset info refresh"
    );
    refetchDatasetInfo();
  }, []);
  const client = useMetageoClient();

  return (
    <Box sx={{ maxWidth: 1200, mx: "auto", p: 3 }}>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 600 }}>
        Step 3: Mapping Configuration
      </Typography>

      <Typography variant="body1" sx={{ mb: 4, color: "text.secondary" }}>
        Configure how OpenStreetMap data should be mapped to your dataset. You
        can create 3D detections, tag samples, map OSM tags to fields, and
        include metadata.
      </Typography>

      {/* Clear Configuration Button */}
      <Box sx={{ mb: 3, display: "flex", justifyContent: "flex-end" }}>
        <Button
          variant="outlined"
          color="warning"
          startIcon={<DeleteIcon />}
          onClick={mappingActions.clearMappingConfig}
          sx={{ minWidth: 200 }}
        >
          Clear Configuration
        </Button>
      </Box>

      {/* Available OSM Tags Section */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <ExploreIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Available OSM Tags
          </Typography>
          {osmTagsLoading && (
            <Typography variant="caption" color="primary">
              Loading...
            </Typography>
          )}
        </Stack>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          OSM tags from your indexed data are automatically loaded to help
          configure mappings.
        </Typography>

        {osmTagsError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Error: {osmTagsError}
          </Alert>
        )}

        {osmTags.length > 0 && (
          <Box>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Found {osmTags.length} OSM tags:
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
              {osmTags.slice(0, 20).map((tag) => (
                <Chip
                  key={tag.key}
                  label={`${tag.key} (${tag.count})`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              ))}
              {osmTags.length > 20 && (
                <Chip
                  label={`+${osmTags.length - 20} more`}
                  size="small"
                  color="default"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        )}

        {osmTags.length === 0 &&
          !osmTagsLoading &&
          !osmTagsError &&
          osmTagsHasLoaded && (
            <Typography variant="body2" color="text.secondary">
              No OSM tags found. Please complete the indexing step first.
            </Typography>
          )}

        {osmTags.length === 0 &&
          !osmTagsLoading &&
          !osmTagsError &&
          !osmTagsHasLoaded && (
            <Typography variant="body2" color="text.secondary">
              Loading OSM tags...
            </Typography>
          )}
      </Paper>

      {/* Configuration Sections */}

      {/* 3D Detections Configuration */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          borderRadius: 1,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            3D Detections
          </Typography>
        </Stack>

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
          <Stack spacing={3}>
            <TextField
              label="3D Slice"
              value={mappingConfig.threeDSlice}
              onChange={(e) => mappingActions.setThreeDSlice(e.target.value)}
              placeholder="e.g., default, lidar, pointcloud"
              helperText="The slice of the group dataset containing 3D data"
              fullWidth
            />

            <TextField
              label="Detection Field Name"
              value={mappingConfig.detectionFieldName}
              onChange={(e) =>
                mappingActions.setDetectionFieldName(e.target.value)
              }
              placeholder="e.g., my_detections, osm_detections"
              helperText="The field name where 3D detections will be stored"
              fullWidth
            />

            <Autocomplete
              freeSolo
              options={osmTags.map((tag) => tag.key)}
              value={mappingConfig.detectionLabelTag}
              onChange={(_, value) =>
                mappingActions.setDetectionLabelTag(value || "")
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Label Tag"
                  placeholder="e.g., type, amenity, building"
                  helperText="The OSM tag to use as the detection label"
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

            <TextField
              label="Detection Radius (meters)"
              type="number"
              value={mappingConfig.detectionRadius}
              onChange={(e) =>
                mappingActions.setDetectionRadius(Number(e.target.value))
              }
              helperText="OSM nodes further than this distance will not be mapped"
              inputProps={{ min: 1, max: 10000 }}
              fullWidth
            />
          </Stack>
        )}
      </Paper>

      {/* Sample Tagging Configuration */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          borderRadius: 1,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Sample Tagging
          </Typography>
        </Stack>

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
          <Stack spacing={3}>
            {/* Tag Slice - only show for grouped datasets */}
            {datasetInfo?.is_grouped ? (
              <FormControl fullWidth>
                <InputLabel>Tag Slice</InputLabel>
                <Select
                  value={mappingConfig.tagSlice}
                  onChange={(e) => mappingActions.setTagSlice(e.target.value)}
                  label="Tag Slice"
                >
                  {datasetInfo.slices.map((slice) => (
                    <MenuItem key={slice} value={slice}>
                      {slice}
                    </MenuItem>
                  ))}
                </Select>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 1 }}
                >
                  Select the slice where tags will be stored
                </Typography>
              </FormControl>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Note:</strong> Tag slice selection is only available
                  for grouped datasets. Your current dataset is not grouped, so
                  tags will be stored at the sample level.
                </Typography>
              </Alert>
            )}

            {/* Tag Mappings */}
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                OSM Tag Mappings
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Configure which OSM tags should be used for sample tagging. For
                example, map "building=yes" to a boolean field.
              </Alert>
              <TagMappingConfig
                tagMappings={mappingConfig.tagMappings}
                osmTags={osmTags}
                onAddMapping={mappingActions.addTagMapping}
                onUpdateMapping={mappingActions.updateTagMapping}
                onRemoveMapping={mappingActions.removeTagMapping}
              />
            </Box>
          </Stack>
        )}
      </Paper>

      {/* Field Mapping Configuration */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          borderRadius: 1,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Field Mapping
          </Typography>
        </Stack>

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
          <FieldMappingConfig
            fieldMappings={mappingConfig.fieldMappings}
            osmTags={osmTags}
            onAddMapping={mappingActions.addFieldMapping}
            onUpdateMapping={mappingActions.updateFieldMapping}
            onRemoveMapping={mappingActions.removeFieldMapping}
          />
        )}
      </Paper>

      {/* Metadata Configuration */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          borderRadius: 1,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Metadata
          </Typography>
        </Stack>

        <FormControlLabel
          control={
            <Switch
              checked={mappingConfig.includeAllTagsAsMetadata}
              onChange={(e) =>
                mappingActions.setIncludeAllTagsAsMetadata(e.target.checked)
              }
            />
          }
          label="Include all OSM tags as metadata"
          sx={{ mb: 2 }}
        />

        {mappingConfig.includeAllTagsAsMetadata && (
          <TextField
            label="Metadata Field Name"
            value={mappingConfig.metadataFieldName}
            onChange={(e) =>
              mappingActions.setMetadataFieldName(e.target.value)
            }
            placeholder="e.g., osm_metadata, tags, properties"
            helperText="The field name where all OSM tags will be stored as metadata"
            fullWidth
          />
        )}
      </Paper>

      {/* Reset Button */}
      <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 3 }}>
        <Button
          variant="outlined"
          color="error"
          onClick={() => mappingActions.resetMapping()}
        >
          Reset Configuration
        </Button>
      </Box>
    </Box>
  );
}
