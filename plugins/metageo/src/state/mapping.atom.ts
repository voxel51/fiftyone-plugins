import { atom } from "recoil";
import type { MappingConfig } from "../types";
import { getStoredMappingConfig } from "../utils/persistence";

const defaultMappingConfig: MappingConfig = {
  radius: 100,
  geoField: "",
  enable3DDetections: false,
  threeDSlice: "",
  detectionFieldName: "",
  detectionLabelTag: "",
  enableSampleTagging: false,
  tagSlice: "",
  tagMappings: [],
  tagRadius: 100,
  renderOn3D: true,
  renderOn2D: false,
  enableFieldMapping: false,
  fieldMappings: [],
  useYamlConfig: false,
  yamlConfig: "",
};

export const mappingConfigAtom = atom<MappingConfig>({
  key: "metageo/mapping",
  default: getStoredMappingConfig() || defaultMappingConfig,
});
