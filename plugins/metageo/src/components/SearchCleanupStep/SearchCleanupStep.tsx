import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  Alert,
  Chip,
  Divider,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  Search as SearchIcon,
  ContentCopy as CopyIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import { useMappingConfig } from "../../hooks/useMappingConfig.hook";

interface SearchExample {
  title: string;
  description: string;
  query: string;
  category: string;
}

export default function SearchCleanupStep() {
  const { state: mappingConfig } = useMappingConfig();

  // Generate search examples based on the current mapping configuration
  const getSearchExamples = (): SearchExample[] => {
    const examples: SearchExample[] = [];

    // Sample tagging examples
    if (mappingConfig.enableSampleTagging) {
      mappingConfig.tagMappings.forEach((mapping) => {
        if (mapping.fieldName) {
          const fieldName = mapping.fieldName;
          const fieldType = mapping.fieldType || "string";

          if (fieldType === "bool") {
            examples.push({
              title: `Find samples with ${fieldName} = true`,
              description: `Samples where the ${mapping.osmKey} OSM tag was found and converted to true`,
              query: `${fieldName} == True`,
              category: "Sample Tagging",
            });
            examples.push({
              title: `Find samples with ${fieldName} = false`,
              description: `Samples where the ${mapping.osmKey} OSM tag was found and converted to false`,
              query: `${fieldName} == False`,
              category: "Sample Tagging",
            });
          } else if (fieldType === "string") {
            examples.push({
              title: `Find samples with specific ${fieldName} value`,
              description: `Samples where ${mapping.osmKey} has a specific value`,
              query: `${fieldName} == "residential"`,
              category: "Sample Tagging",
            });
            examples.push({
              title: `Find samples with any ${fieldName} value`,
              description: `Samples where ${mapping.osmKey} has any value (not null)`,
              query: `${fieldName} != None`,
              category: "Sample Tagging",
            });
          } else if (fieldType === "int" || fieldType === "float") {
            examples.push({
              title: `Find samples with ${fieldName} > threshold`,
              description: `Samples where ${mapping.osmKey} has a numeric value above threshold`,
              query: `${fieldName} > 5`,
              category: "Sample Tagging",
            });
          }
        }
      });
    }

    // Field mapping examples
    if (mappingConfig.enableFieldMapping) {
      mappingConfig.fieldMappings.forEach((mapping) => {
        if (mapping.fieldName) {
          const fieldName = mapping.fieldName;
          const fieldType = mapping.fieldType || "string";

          examples.push({
            title: `Find samples with ${fieldName} data`,
            description: `Samples where ${mapping.osmKey} was mapped to ${fieldName}`,
            query: `${fieldName} != None`,
            category: "Field Mapping",
          });

          if (fieldType === "string") {
            examples.push({
              title: `Find samples with ${fieldName} containing text`,
              description: `Samples where ${fieldName} contains specific text`,
              query: `${fieldName}.contains("school")`,
              category: "Field Mapping",
            });
          }
        }
      });
    }

    // Metadata examples
    if (mappingConfig.includeAllTagsAsMetadata) {
      const metadataField = mappingConfig.metadataFieldName || "osm_metadata";
      examples.push({
        title: `Find samples with OSM metadata`,
        description: `Samples that have OSM metadata from the enrichment process`,
        query: `${metadataField} != None`,
        category: "Metadata",
      });
      examples.push({
        title: `Find samples with specific OSM tag in metadata`,
        description: `Samples where the metadata contains a specific OSM tag`,
        query: `${metadataField}.apply(lambda x: any(tag.get("amenity") == "school" for tag in x if isinstance(tag, dict)))`,
        category: "Metadata",
      });
    }

    // 3D Detection examples
    if (mappingConfig.enable3DDetections) {
      const detectionField = mappingConfig.detectionFieldName || "detections";
      examples.push({
        title: `Find samples with 3D detections`,
        description: `Samples that have 3D detections from OSM data`,
        query: `${detectionField} != None`,
        category: "3D Detections",
      });
      examples.push({
        title: `Find samples with specific detection types`,
        description: `Samples with detections of a specific type`,
        query: `${detectionField}.apply(lambda x: any(d.get("label") == "building" for d in x) if x else False)`,
        category: "3D Detections",
      });
    }

    return examples;
  };


  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const searchExamples = getSearchExamples();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
        Step 5: Search & Cleanup
      </Typography>

      <Typography variant="body1" sx={{ mb: 3, color: "text.secondary" }}>
        Use the enriched OSM data to search for specific samples in your
        dataset. Copy the example queries below and use them in the FiftyOne
        sidebar to find samples that match your criteria.
      </Typography>


      {/* Search Examples */}
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
          <SearchIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Search Examples
          </Typography>
        </Stack>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Use these example queries in the FiftyOne sidebar to search for
          samples based on your enriched OSM data.
        </Typography>

        {searchExamples.length > 0 ? (
          <Box>
            {/* Group examples by category */}
            {Object.entries(
              searchExamples.reduce((acc, example) => {
                if (!acc[example.category]) acc[example.category] = [];
                acc[example.category].push(example);
                return acc;
              }, {} as Record<string, SearchExample[]>)
            ).map(([category, examples], categoryIndex) => (
              <Box key={category} sx={{ mb: 3 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ fontWeight: 600, mb: 2, color: "primary.main" }}
                >
                  {category}
                </Typography>

                {examples.map((example, index) => (
                  <Paper
                    key={index}
                    elevation={0}
                    sx={{
                      p: 2,
                      mb: 2,
                      border: `1px solid rgba(0, 0, 0, 0.12)`,
                      borderRadius: 1,
                      backgroundColor: "rgba(0, 0, 0, 0.02)",
                    }}
                  >
                    <Stack
                      direction="row"
                      justifyContent="space-between"
                      alignItems="flex-start"
                      sx={{ mb: 1 }}
                    >
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {example.title}
                      </Typography>
                      <Tooltip title="Copy query to clipboard">
                        <IconButton
                          size="small"
                          onClick={() => copyToClipboard(example.query)}
                          sx={{ ml: 1 }}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>

                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2 }}
                    >
                      {example.description}
                    </Typography>

                    <Paper
                      elevation={0}
                      sx={{
                        p: 1.5,
                        backgroundColor: "rgba(0, 0, 0, 0.05)",
                        border: `1px solid rgba(0, 0, 0, 0.1)`,
                        borderRadius: 1,
                        fontFamily: "monospace",
                        fontSize: "0.875rem",
                      }}
                    >
                      <code>{example.query}</code>
                    </Paper>
                  </Paper>
                ))}
              </Box>
            ))}

            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2">
                <strong>💡 Tip:</strong> Copy any query above and paste it into
                the FiftyOne sidebar filter box. You can also combine multiple
                conditions using <code>&</code> (and) or <code>|</code> (or)
                operators.
              </Typography>
            </Alert>
          </Box>
        ) : (
          <Alert severity="info">
            <Typography variant="body2">
              No search examples available. Please complete the mapping
              configuration in previous steps to see search examples.
            </Typography>
          </Alert>
        )}
      </Paper>

    </Box>
  );
}
