import { useCallback, useMemo } from "react";
import { useRecoilState } from "recoil";
import { mappingConfigAtom } from "../state/mapping.atom";
import type { MappingConfig, TagMapping, FieldMapping } from "../types";

export function useMappingConfig() {
  console.log("🔍 useMappingConfig: Hook starting...");

  let mappingConfig, setMappingConfig;
  try {
    [mappingConfig, setMappingConfig] = useRecoilState(mappingConfigAtom);
  } catch (error) {
    console.error("🔍 useMappingConfig: Error accessing atom:", error);
    // Return default state if atom access fails
    const defaultState = {
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
    
    return {
      state: defaultState,
      actions: {
        setRadius: () => {},
        setGeoField: () => {},
        setUseYamlConfig: () => {},
        setYamlConfig: () => {},
        setEnable3DDetections: () => {},
        setThreeDSlice: () => {},
        setDetectionFieldName: () => {},
        setDetectionLabelTag: () => {},
        setEnableSampleTagging: () => {},
        setTagSlice: () => {},
        setTagRadius: () => {},
        setRenderOn3D: () => {},
        setRenderOn2D: () => {},
        setEnableFieldMapping: () => {},
        addTagMapping: () => {},
        removeTagMapping: () => {},
        updateTagMapping: () => {},
        addFieldMapping: () => {},
        removeFieldMapping: () => {},
        updateFieldMapping: () => {},
      },
    };
  }
  
  console.log("🔍 useMappingConfig: mappingConfig =", mappingConfig);
  console.log(
    "🔍 useMappingConfig: mappingConfig.tagMappings =",
    mappingConfig?.tagMappings
  );
  console.log(
    "🔍 useMappingConfig: mappingConfig.fieldMappings =",
    mappingConfig?.fieldMappings
  );

  const actions = useMemo(
    () => ({
      setRadius: (radius: number) => {
        setMappingConfig((prev) => ({ ...prev, radius }));
      },

      setGeoField: (geoField: string) => {
        setMappingConfig((prev) => ({ ...prev, geoField }));
      },

      setUseYamlConfig: (useYamlConfig: boolean) => {
        setMappingConfig((prev) => ({ ...prev, useYamlConfig }));
      },

      setYamlConfig: (yamlConfig: string) => {
        setMappingConfig((prev) => ({ ...prev, yamlConfig }));
      },

      // 3D Detections
      setEnable3DDetections: (enable: boolean) => {
        setMappingConfig((prev) => ({ ...prev, enable3DDetections: enable }));
      },

      setThreeDSlice: (slice: string) => {
        setMappingConfig((prev) => ({ ...prev, threeDSlice: slice }));
      },

      setDetectionFieldName: (fieldName: string) => {
        setMappingConfig((prev) => ({
          ...prev,
          detectionFieldName: fieldName,
        }));
      },

      setDetectionLabelTag: (tag: string) => {
        setMappingConfig((prev) => ({ ...prev, detectionLabelTag: tag }));
      },

      // Sample Tagging
      setEnableSampleTagging: (enable: boolean) => {
        setMappingConfig((prev) => ({
          ...prev,
          enableSampleTagging: enable,
        }));
      },

      setTagSlice: (slice: string) => {
        setMappingConfig((prev) => ({ ...prev, tagSlice: slice }));
      },

      setTagRadius: (radius: number) => {
        setMappingConfig((prev) => ({ ...prev, tagRadius: radius }));
      },

      setRenderOn3D: (render: boolean) => {
        setMappingConfig((prev) => ({ ...prev, renderOn3D: render }));
      },

      setRenderOn2D: (render: boolean) => {
        setMappingConfig((prev) => ({ ...prev, renderOn2D: render }));
      },

      // Tag Mappings
      addTagMapping: (mapping: TagMapping) => {
        setMappingConfig((prev) => ({
          ...prev,
          tagMappings: [...prev.tagMappings, mapping],
        }));
      },

      updateTagMapping: (index: number, mapping: TagMapping) => {
        setMappingConfig((prev) => ({
          ...prev,
          tagMappings: prev.tagMappings.map((m, i) =>
            i === index ? mapping : m
          ),
        }));
      },

      removeTagMapping: (index: number) => {
        setMappingConfig((prev) => ({
          ...prev,
          tagMappings: prev.tagMappings.filter((_, i) => i !== index),
        }));
      },

      // Field Mappings
      addFieldMapping: (mapping: FieldMapping) => {
        setMappingConfig((prev) => ({
          ...prev,
          fieldMappings: [...prev.fieldMappings, mapping],
        }));
      },

      updateFieldMapping: (index: number, mapping: FieldMapping) => {
        setMappingConfig((prev) => ({
          ...prev,
          fieldMappings: prev.fieldMappings.map((m, i) =>
            i === index ? mapping : m
          ),
        }));
      },

      removeFieldMapping: (index: number) => {
        setMappingConfig((prev) => ({
          ...prev,
          fieldMappings: prev.fieldMappings.filter((_, i) => i !== index),
        }));
      },

      // Field Mapping Enable
      setEnableFieldMapping: (enable: boolean) => {
        setMappingConfig((prev) => ({ ...prev, enableFieldMapping: enable }));
      },

      resetMapping: () => {
        setMappingConfig((prev) => ({
          ...prev,
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
        }));
      },
    }),
    [setMappingConfig]
  );

  const derived = useMemo(
    () => ({
      hasValidConfig: Boolean(
        mappingConfig.geoField && mappingConfig.radius > 0
      ),
      has3DDetections: mappingConfig.enable3DDetections,
      hasSampleTagging: mappingConfig.enableSampleTagging,
      hasFieldMapping: mappingConfig.enableFieldMapping,
      tagMappingsCount: mappingConfig.tagMappings
        ? mappingConfig.tagMappings.length
        : 0,
      fieldMappingsCount: mappingConfig.fieldMappings
        ? mappingConfig.fieldMappings.length
        : 0,
    }),
    [mappingConfig]
  );

  return {
    state: mappingConfig,
    actions,
    derived,
  };
}
