import { useCallback, useMemo } from "react";
import { useRecoilState } from "recoil";
import { mappingConfigAtom } from "../state/mapping.atom";
import type { MappingConfig, TagMapping, FieldMapping } from "../types";

export function useMappingConfig() {
  console.log("🔍 useMappingConfig: Hook starting...");

  const [mappingConfig, setMappingConfig] = useRecoilState(mappingConfigAtom);
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
      setRadius: useCallback(
        (radius: number) => {
          setMappingConfig((prev) => ({ ...prev, radius }));
        },
        [setMappingConfig]
      ),

      setGeoField: useCallback(
        (geoField: string) => {
          setMappingConfig((prev) => ({ ...prev, geoField }));
        },
        [setMappingConfig]
      ),

      setUseYamlConfig: useCallback(
        (useYamlConfig: boolean) => {
          setMappingConfig((prev) => ({ ...prev, useYamlConfig }));
        },
        [setMappingConfig]
      ),

      setYamlConfig: useCallback(
        (yamlConfig: string) => {
          setMappingConfig((prev) => ({ ...prev, yamlConfig }));
        },
        [setMappingConfig]
      ),

      // 3D Detections
      setEnable3DDetections: useCallback(
        (enable: boolean) => {
          setMappingConfig((prev) => ({ ...prev, enable3DDetections: enable }));
        },
        [setMappingConfig]
      ),

      setThreeDSlice: useCallback(
        (slice: string) => {
          setMappingConfig((prev) => ({ ...prev, threeDSlice: slice }));
        },
        [setMappingConfig]
      ),

      setDetectionFieldName: useCallback(
        (fieldName: string) => {
          setMappingConfig((prev) => ({
            ...prev,
            detectionFieldName: fieldName,
          }));
        },
        [setMappingConfig]
      ),

      setDetectionLabelTag: useCallback(
        (tag: string) => {
          setMappingConfig((prev) => ({ ...prev, detectionLabelTag: tag }));
        },
        [setMappingConfig]
      ),

      // Sample Tagging
      setEnableSampleTagging: useCallback(
        (enable: boolean) => {
          setMappingConfig((prev) => ({
            ...prev,
            enableSampleTagging: enable,
          }));
        },
        [setMappingConfig]
      ),

      setTagSlice: useCallback(
        (slice: string) => {
          setMappingConfig((prev) => ({ ...prev, tagSlice: slice }));
        },
        [setMappingConfig]
      ),

      setTagRadius: useCallback(
        (radius: number) => {
          setMappingConfig((prev) => ({ ...prev, tagRadius: radius }));
        },
        [setMappingConfig]
      ),

      setRenderOn3D: useCallback(
        (render: boolean) => {
          setMappingConfig((prev) => ({ ...prev, renderOn3D: render }));
        },
        [setMappingConfig]
      ),

      setRenderOn2D: useCallback(
        (render: boolean) => {
          setMappingConfig((prev) => ({ ...prev, renderOn2D: render }));
        },
        [setMappingConfig]
      ),

      // Tag Mappings
      addTagMapping: useCallback(
        (mapping: TagMapping) => {
          setMappingConfig((prev) => ({
            ...prev,
            tagMappings: [...prev.tagMappings, mapping],
          }));
        },
        [setMappingConfig]
      ),

      updateTagMapping: useCallback(
        (index: number, mapping: TagMapping) => {
          setMappingConfig((prev) => ({
            ...prev,
            tagMappings: prev.tagMappings.map((m, i) =>
              i === index ? mapping : m
            ),
          }));
        },
        [setMappingConfig]
      ),

      removeTagMapping: useCallback(
        (index: number) => {
          setMappingConfig((prev) => ({
            ...prev,
            tagMappings: prev.tagMappings.filter((_, i) => i !== index),
          }));
        },
        [setMappingConfig]
      ),

      // Field Mappings
      addFieldMapping: useCallback(
        (mapping: FieldMapping) => {
          setMappingConfig((prev) => ({
            ...prev,
            fieldMappings: [...prev.fieldMappings, mapping],
          }));
        },
        [setMappingConfig]
      ),

      updateFieldMapping: useCallback(
        (index: number, mapping: FieldMapping) => {
          setMappingConfig((prev) => ({
            ...prev,
            fieldMappings: prev.fieldMappings.map((m, i) =>
              i === index ? mapping : m
            ),
          }));
        },
        [setMappingConfig]
      ),

      removeFieldMapping: useCallback(
        (index: number) => {
          setMappingConfig((prev) => ({
            ...prev,
            fieldMappings: prev.fieldMappings.filter((_, i) => i !== index),
          }));
        },
        [setMappingConfig]
      ),

      // Field Mapping Enable
      setEnableFieldMapping: useCallback(
        (enable: boolean) => {
          setMappingConfig((prev) => ({ ...prev, enableFieldMapping: enable }));
        },
        [setMappingConfig]
      ),

      resetMapping: useCallback(() => {
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
      }, [setMappingConfig]),
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
