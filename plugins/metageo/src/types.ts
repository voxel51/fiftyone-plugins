export interface QuadtreeCell {
  id: string;
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  sampleCount: number;
  children?: QuadtreeCell[];
  depth: number;
  maxDepth: number;
  minSize: number; // minimum bbox size in degrees
}

export interface QuadtreeConfig {
  maxDepth: number;
  minSize: number;
  threshold: number; // max samples per cell before splitting
  maxSamplesPerCell: number;
}

export interface GeoFieldsData {
  geo_fields: string[];
  has_geo_fields: boolean;
  dataset_name: string;
  total_fields: number;
  can_proceed: boolean;
}
