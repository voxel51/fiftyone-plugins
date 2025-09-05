import { atom } from "recoil";
import type { MappingConfig } from "../types";

export const mappingConfigAtom = atom<MappingConfig>({
  key: "metageo/mapping",
  default: {
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
  },
});
