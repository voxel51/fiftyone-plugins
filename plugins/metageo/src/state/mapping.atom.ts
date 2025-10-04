import { atom } from "recoil";
import type { MappingConfig } from "../types";
import { getStoredMappingConfig } from "../utils/persistence";

const defaultMappingConfig: MappingConfig = {
  // Basic configuration
  geoField: "",
  useYamlConfig: false,
  yamlConfig: "",
  
  // 3D Detections configuration
  enable3DDetections: false,
  threeDSlice: "",
  detectionFieldName: "",
  detectionLabelTag: "",
  detectionRadius: 100,
  
  // Sample tagging configuration
  enableSampleTagging: false,
  tagSlice: "",
  tagMappings: [],
  tagRadius: 100,
  renderOn3D: true,
  renderOn2D: false,
  
  // Field mapping configuration
  enableFieldMapping: false,
  fieldMappings: [],
  
  // Metadata configuration
  includeAllTagsAsMetadata: false,
  metadataFieldName: "osm_metadata",
};

export const mappingConfigAtom = atom<MappingConfig>({
  key: "metageo/mapping",
  default: getStoredMappingConfig() || defaultMappingConfig,
});
