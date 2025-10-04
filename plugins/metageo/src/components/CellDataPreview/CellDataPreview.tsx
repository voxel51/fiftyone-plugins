import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Paper,
  Chip,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  useTheme,
  alpha,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  LocationOn as LocationOnIcon,
  DataObject as DataObjectIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";
import { useMetageoClient } from "../../hooks/useMetageoClient.hook";

interface CellDataPreviewProps {
  open: boolean;
  onClose: () => void;
  cellId: string;
}

interface CellData {
  cell_id: string;
  cell_status: string;
  error?: string;
  osm_features_count: number;
  osm_data: any[];
  cell_info?: any;
  coordinates?: [number, number, number, number];
  sample_count: number;
}

export default function CellDataPreview({
  open,
  onClose,
  cellId,
}: CellDataPreviewProps) {
  const theme = useTheme();
  const client = useMetageoClient();
  const [cellData, setCellData] = useState<CellData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);


  useEffect(() => {
    if (open && cellId) {
      loadCellData();
    }
  }, [open, cellId]);

  const loadCellData = async () => {
    if (!client) {
      setError("Client not available");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await client.get_cell_data({ cell_id: cellId });
      if (result?.result?.status === "success") {
        setCellData(result.result);
      } else {
        setError(result?.result?.message || "Failed to load cell data");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cell data");
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircleIcon color="success" />;
      case "failed":
        return <ErrorIcon color="error" />;
      case "rate_limited":
        return <WarningIcon color="warning" />;
      case "cancelled":
        return <ErrorIcon color="disabled" />;
      default:
        return <LocationOnIcon color="info" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return theme.palette.success.main;
      case "failed":
        return theme.palette.error.main;
      case "rate_limited":
        return theme.palette.warning.main;
      case "cancelled":
        return theme.palette.grey[500];
      case "running":
        return theme.palette.info.main;
      default:
        return theme.palette.grey[600];
    }
  };

  const formatCoordinates = (coords?: [number, number, number, number]) => {
    if (!coords) return "N/A";
    const [minLon, minLat, maxLon, maxLat] = coords;
    return `[${minLon.toFixed(6)}, ${minLat.toFixed(6)}, ${maxLon.toFixed(6)}, ${maxLat.toFixed(6)}]`;
  };

  const getFeatureTypeStats = (osmData: any[]) => {
    const stats: { [key: string]: number } = {};
    osmData.forEach((feature) => {
      const featureType = feature.feature_type || "unknown";
      stats[featureType] = (stats[featureType] || 0) + 1;
    });
    return stats;
  };

  const getTagStats = (osmData: any[]) => {
    const tagStats: { [key: string]: number } = {};
    osmData.forEach((feature) => {
      if (feature.tags) {
        Object.keys(feature.tags).forEach((tag) => {
          tagStats[tag] = (tagStats[tag] || 0) + 1;
        });
      }
    });
    return tagStats;
  };

  const getTagStatsWithExamples = (osmData: any[]) => {
    const tagStats: { [key: string]: { count: number; examples: string[] } } = {};
    osmData.forEach((feature) => {
      if (feature.tags) {
        Object.entries(feature.tags).forEach(([tag, value]) => {
          if (!tagStats[tag]) {
            tagStats[tag] = { count: 0, examples: [] };
          }
          tagStats[tag].count += 1;
          
          // Add unique example values (limit to 5 examples per tag)
          const valueStr = String(value);
          if (!tagStats[tag].examples.includes(valueStr) && tagStats[tag].examples.length < 5) {
            tagStats[tag].examples.push(valueStr);
          }
        });
      }
    });
    return tagStats;
  };


  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <LocationOnIcon color="primary" />
          <Typography variant="h6" component="span">
            Cell Data Preview: {cellId}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {cellData && (
          <Box>
            {/* Cell Overview */}
            <Paper
              elevation={1}
              sx={{
                p: 2,
                mb: 3,
                background: alpha(theme.palette.primary.main, 0.02),
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
              }}
            >
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Cell Overview
              </Typography>
              <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                <Chip
                  icon={getStatusIcon(cellData.cell_status)}
                  label={`Status: ${cellData.cell_status}`}
                  sx={{
                    backgroundColor: alpha(getStatusColor(cellData.cell_status), 0.1),
                    color: getStatusColor(cellData.cell_status),
                    border: `1px solid ${alpha(getStatusColor(cellData.cell_status), 0.3)}`,
                  }}
                />
                <Chip
                  label={`Samples: ${cellData.sample_count}`}
                  variant="outlined"
                />
                <Chip
                  label={`OSM Features: ${cellData.osm_features_count || 0}`}
                  variant="outlined"
                />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                <strong>Coordinates:</strong> {formatCoordinates(cellData.coordinates)}
              </Typography>
              {cellData.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  <strong>Error:</strong> {cellData.error}
                </Alert>
              )}
            </Paper>

            {/* OSM Data Statistics */}
            {cellData.osm_data && cellData.osm_data.length > 0 && (
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  mb: 3,
                  background: alpha(theme.palette.info.main, 0.02),
                  border: `1px solid ${alpha(theme.palette.info.main, 0.1)}`,
                }}
              >
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  OSM Data Statistics
                </Typography>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Feature Types ({Object.keys(getFeatureTypeStats(cellData.osm_data)).length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      {Object.entries(getFeatureTypeStats(cellData.osm_data))
                        .sort(([, a], [, b]) => b - a)
                        .map(([type, count]) => (
                          <Chip
                            key={type}
                            label={`${type}: ${count}`}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                    </Stack>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      OSM Tags ({Object.keys(getTagStats(cellData.osm_data)).length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      {Object.entries(getTagStats(cellData.osm_data))
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 20) // Show top 20 tags
                        .map(([tag, count]) => (
                          <Chip
                            key={tag}
                            label={`${tag}: ${count}`}
                            size="small"
                            variant="outlined"
                            color="primary"
                          />
                        ))}
                    </Stack>
                    {Object.keys(getTagStats(cellData.osm_data)).length > 20 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        Showing top 20 tags out of {Object.keys(getTagStats(cellData.osm_data)).length} total
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Tag Counts & Examples ({Object.keys(getTagStatsWithExamples(cellData.osm_data)).length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <TableContainer sx={{ maxHeight: 400 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell><strong>Tag</strong></TableCell>
                            <TableCell align="right"><strong>Count</strong></TableCell>
                            <TableCell><strong>Example Values</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(getTagStatsWithExamples(cellData.osm_data))
                            .sort(([, a], [, b]) => b.count - a.count)
                            .slice(0, 50) // Show top 50 tags
                            .map(([tag, data]) => (
                              <TableRow key={tag}>
                                <TableCell>
                                  <Chip
                                    label={tag}
                                    size="small"
                                    variant="outlined"
                                    color="primary"
                                  />
                                </TableCell>
                                <TableCell align="right">
                                  <Typography variant="body2" fontWeight="medium">
                                    {data.count}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  <Stack direction="row" spacing={0.5} flexWrap="wrap">
                                    {data.examples.map((example, index) => (
                                      <Chip
                                        key={index}
                                        label={example}
                                        size="small"
                                        variant="filled"
                                        sx={{
                                          backgroundColor: alpha(theme.palette.secondary.main, 0.1),
                                          color: theme.palette.secondary.main,
                                          fontSize: '0.75rem',
                                          height: '20px',
                                        }}
                                      />
                                    ))}
                                    {data.examples.length === 5 && (
                                      <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center', ml: 0.5 }}>
                                        +more
                                      </Typography>
                                    )}
                                  </Stack>
                                </TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    {Object.keys(getTagStatsWithExamples(cellData.osm_data)).length > 50 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        Showing top 50 tags out of {Object.keys(getTagStatsWithExamples(cellData.osm_data)).length} total
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              </Paper>
            )}

            {/* Raw OSM Data */}
            {cellData.osm_data && cellData.osm_data.length > 0 && (
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  background: alpha(theme.palette.grey[100], 0.5),
                  border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
                }}
              >
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Raw OSM Data ({cellData.osm_data.length} features)
                </Typography>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      <DataObjectIcon sx={{ mr: 1, verticalAlign: "middle" }} />
                      View Raw Data
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <TableContainer sx={{ maxHeight: 400 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>Type</TableCell>
                            <TableCell>ID</TableCell>
                            <TableCell>Feature Type</TableCell>
                            <TableCell>Tags</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {cellData.osm_data.slice(0, 50).map((feature, index) => (
                            <TableRow key={index}>
                              <TableCell>{feature.type}</TableCell>
                              <TableCell>{feature.id}</TableCell>
                              <TableCell>{feature.feature_type || "N/A"}</TableCell>
                              <TableCell>
                                <Box sx={{ maxWidth: 200, overflow: "hidden" }}>
                                  {feature.tags ? (
                                    Object.entries(feature.tags)
                                      .slice(0, 3)
                                      .map(([key, value]) => (
                                        <Chip
                                          key={key}
                                          label={`${key}=${value}`}
                                          size="small"
                                          sx={{ mr: 0.5, mb: 0.5 }}
                                        />
                                      ))
                                  ) : (
                                    <Typography variant="caption" color="text.secondary">
                                      No tags
                                    </Typography>
                                  )}
                                  {feature.tags && Object.keys(feature.tags).length > 3 && (
                                    <Typography variant="caption" color="text.secondary">
                                      +{Object.keys(feature.tags).length - 3} more
                                    </Typography>
                                  )}
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    {cellData.osm_data.length > 50 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        Showing first 50 features out of {cellData.osm_data.length} total
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              </Paper>
            )}

            {cellData.osm_data && cellData.osm_data.length === 0 && (
              <Paper
                elevation={1}
                sx={{
                  p: 3,
                  textAlign: "center",
                  background: alpha(theme.palette.grey[100], 0.5),
                  border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
                }}
              >
                <Typography variant="body1" color="text.secondary">
                  No OSM data found in this cell
                </Typography>
              </Paper>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
        <Button onClick={loadCellData} variant="contained" disabled={loading}>
          Refresh
        </Button>
      </DialogActions>
    </Dialog>
  );
}
