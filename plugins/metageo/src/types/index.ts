// Core types for the Metageo plugin
export interface GeoPoint {
  longitude: number;
  latitude: number;
}

export interface BoundingBox {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
}

export interface GridCell {
  id: string;
  status: CellStatus;
  progress: number;
  error?: string;
  coordinates: [number, number, number, number];
  sample_count: number;
  osm_features?: any[];
}

export type CellStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "rate_limited"
  | "retrying"
  | "cancelled"
  | "empty"
  | "unknown";

export interface QuadtreeCell {
  id: string;
  bbox: [number, number, number, number];
  sampleCount: number;
  children?: QuadtreeCell[];
  depth: number;
  maxDepth: number;
  minSize: number;
}

export interface QuadtreeConfig {
  maxDepth: number;
  minSize: number;
  threshold: number;
  maxSamplesPerCell: number;
}

export interface IndexingState {
  bbox: BoundingBox | null;
  gridTiles: number;
  location: string;
  gridCells: GridCell[];
  executionMode: "immediate" | "delegated";
  indexingStatus:
    | "idle"
    | "running"
    | "completed"
    | "failed"
    | "cancelled"
    | "paused";
  quadtreeCells: QuadtreeCell[];
  realSampleDistribution: { [cellId: string]: number };
}

export interface MappingConfig {
  // Basic configuration
  geoField: string;
  useYamlConfig: boolean;
  yamlConfig: string;
  
  // 3D Detections configuration
  enable3DDetections: boolean;
  threeDSlice: string;
  detectionFieldName: string;
  detectionLabelTag: string;
  detectionRadius: number;
  
  // Sample tagging configuration
  enableSampleTagging: boolean;
  tagSlice: string;
  tagMappings: TagMapping[];
  tagRadius: number;
  renderOn3D: boolean;
  renderOn2D: boolean;
  
  // Field mapping configuration
  enableFieldMapping: boolean;
  fieldMappings: FieldMapping[];
  
  // Metadata configuration
  includeAllTagsAsMetadata: boolean;
  metadataFieldName: string;
}

export interface TagMapping {
  osmKey: string;
  fieldName: string;
  fieldType: "string" | "int" | "float" | "bool";
  boolTrueValue?: string;
  boolFalseValue?: string;
}

export interface FieldMapping {
  id: string; // Unique identifier for the mapping
  osmKey: string;
  fieldName: string;
  fieldType: "string" | "int" | "float" | "bool" | "enum";
  // Boolean mapping
  boolTrueValue?: string;
  boolFalseValue?: string;
  // Enum mapping
  enumMappings?: { [osmValue: string]: string };
  // Default value when OSM tag is not found
  defaultValue?: string;
  // Description for documentation
  description?: string;
}

export interface StepData {
  index: IndexingState;
  mapping: MappingConfig;
  enrich: {
    prefetchId: string | null;
    enrichedCount: number;
  };
  search: {
    filters: Array<{ key: string; value: string; type: string }>;
  };
}

export interface OsmTag {
  key: string;
  count: number;
  examples: string[];
}

export interface GeoFieldsData {
  geo_fields: string[];
  has_geo_fields: boolean;
  dataset_name: string;
  total_fields: number;
  can_proceed: boolean;
}

export interface MetageoClient {
  define_area_auto: (params: { geo_field: string }) => Promise<any>;
  calculate_sample_distribution: (params: {
    bbox: number[];
    grid_tiles: number;
    geo_field: string;
  }) => Promise<any>;
  index_grid: (params: {
    bbox: number[];
    grid_tiles: number;
    location: string;
  }) => Promise<any>;
  start_indexing: (params: {
    bbox: number[];
    grid_tiles: number;
    geo_field: string;
    execution_mode: "immediate" | "delegated";
  }) => Promise<any>;
  watch_indexing: (params: { indexing_id: string }) => Promise<any>;
  get_current_indexing_state: () => Promise<any>;
  drop_index: () => Promise<any>;
  cancel_indexing: (params: {}) => Promise<any>;
  get_available_osm_tags: () => Promise<any>;
  get_field_mappings: () => Promise<any>;
  save_mapping_config: (params: { mapping_config: any }) => Promise<any>;
  get_mapping_config: () => Promise<any>;
  clear_mapping_config: () => Promise<any>;
  clear_enrichment_data: () => Promise<any>;
  enrich_dataset_async: () => Promise<any>;
  get_enrichment_status: () => Promise<any>;
  get_geo_fields: () => Promise<any>;
  get_cell_data: (params: { cell_id: string }) => Promise<any>;
  reset_metageo: () => Promise<any>;
}
