import { useCallback, useMemo, useEffect, useState } from "react";
import { useRecoilState } from "recoil";
import { mappingConfigAtom } from "../state/mapping.atom";
import { useMetageoClient } from "./useMetageoClient.hook";
import type { MappingConfig, TagMapping, FieldMapping } from "../types";

export function useMappingConfig() {
  console.log("🔍 useMappingConfig: Hook starting...");

  const client = useMetageoClient();
  const [hasLoaded, setHasLoaded] = useState(false);

  let mappingConfig, setMappingConfig;
  try {
    [mappingConfig, setMappingConfig] = useRecoilState(mappingConfigAtom);
  } catch (error) {
    console.error("🔍 useMappingConfig: Error accessing atom:", error);
    // Return default state if atom access fails
    const defaultState = {
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

      // Field mapping configuration
      enableFieldMapping: false,
      fieldMappings: [],

      // Metadata configuration
      includeAllTagsAsMetadata: false,
      metadataFieldName: "osm_metadata",
    };

    return {
      state: defaultState,
      actions: {
        setDetectionRadius: () => {},
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
        setIncludeAllTagsAsMetadata: () => {},
        setMetadataFieldName: () => {},
        resetMapping: () => {},
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

  // Auto-save mapping config to backend on changes
  const saveMappingConfig = useCallback(
    async (config: MappingConfig) => {
      if (!client || !hasLoaded) return;

      try {
        console.log("🔍 useMappingConfig: Auto-saving mapping config:", config);
        await client.save_mapping_config({ mapping_config: config });
      } catch (error) {
        console.error(
          "🔍 useMappingConfig: Error auto-saving mapping config:",
          error
        );
      }
    },
    [client, hasLoaded]
  );

  // Load mapping config from backend on mount
  const loadMappingConfig = useCallback(async () => {
    if (!client || hasLoaded) return;

    try {
      console.log("🔍 useMappingConfig: Loading mapping config from backend");
      const result = await client.get_mapping_config();

      if (
        result?.result?.status === "success" &&
        result.result.mapping_config
      ) {
        console.log(
          "🔍 useMappingConfig: Loaded mapping config:",
          result.result.mapping_config
        );
        setMappingConfig(result.result.mapping_config);
      }
    } catch (error) {
      console.error(
        "🔍 useMappingConfig: Error loading mapping config:",
        error
      );
    } finally {
      setHasLoaded(true);
    }
  }, [client, hasLoaded, setMappingConfig]);

  // Load mapping config on mount
  useEffect(() => {
    loadMappingConfig();
  }, [loadMappingConfig]);

  // Auto-save when mapping config changes (but not on initial load)
  useEffect(() => {
    if (hasLoaded && mappingConfig) {
      saveMappingConfig(mappingConfig);
    }
  }, [mappingConfig, hasLoaded, saveMappingConfig]);

  const actions = useMemo(
    () => ({
      setDetectionRadius: (radius: number) => {
        setMappingConfig((prev) => ({ ...prev, detectionRadius: radius }));
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

      // Metadata configuration
      setIncludeAllTagsAsMetadata: (include: boolean) => {
        setMappingConfig((prev) => ({
          ...prev,
          includeAllTagsAsMetadata: include,
        }));
      },

      setMetadataFieldName: (fieldName: string) => {
        setMappingConfig((prev) => ({ ...prev, metadataFieldName: fieldName }));
      },

      resetMapping: () => {
        setMappingConfig((prev) => ({
          ...prev,
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
        }));
      },

      clearMappingConfig: async () => {
        if (!client) return;

        try {
          console.log(
            "🔍 useMappingConfig: Clearing mapping config from backend"
          );
          await client.clear_mapping_config();

          // Reset local state
          setMappingConfig((prev) => ({
            ...prev,
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

            // Field mapping configuration
            enableFieldMapping: false,
            fieldMappings: [],

            // Metadata configuration
            includeAllTagsAsMetadata: false,
            metadataFieldName: "osm_metadata",
          }));
        } catch (error) {
          console.error(
            "🔍 useMappingConfig: Error clearing mapping config:",
            error
          );
        }
      },
    }),
    [setMappingConfig, client]
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
