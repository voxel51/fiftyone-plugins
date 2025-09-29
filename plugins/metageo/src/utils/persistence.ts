// Utility functions for persisting state to localStorage
import type { IndexingState } from "../types";

const STORAGE_KEYS = {
  INDEXING_STATE: "metageo/indexingState",
  FLOW_STATE: "metageo/flowState",
  MAPPING_CONFIG: "metageo/mappingConfig",
} as const;

export interface FlowState {
  activeStep: number;
  hasStarted: boolean;
}

export interface MappingConfig {
  radius: number;
  geoField: string;
  enable3DDetections: boolean;
  threeDSlice: string;
  detectionFieldName: string;
  detectionLabelTag: string;
  enableSampleTagging: boolean;
  tagSlice: string;
  tagMappings: Array<{
    osmKey: string;
    fieldName: string;
    fieldType: "string" | "int" | "float" | "bool";
    boolTrueValue?: string;
    boolFalseValue?: string;
  }>;
  tagRadius: number;
  renderOn3D: boolean;
  renderOn2D: boolean;
  enableFieldMapping: boolean;
  fieldMappings: Array<{
    osmKey: string;
    fieldName: string;
    fieldType: "string" | "int" | "float" | "bool";
    boolTrueValue?: string;
    boolFalseValue?: string;
  }>;
  useYamlConfig: boolean;
  yamlConfig: string;
}

// Generic storage functions
function getFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item);
  } catch (error) {
    console.warn(`Failed to parse stored data for key ${key}:`, error);
    return defaultValue;
  }
}

function setToStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn(`Failed to store data for key ${key}:`, error);
  }
}

function removeFromStorage(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Failed to remove data for key ${key}:`, error);
  }
}

// Indexing state persistence
export function getStoredIndexingState(): IndexingState | null {
  return getFromStorage(STORAGE_KEYS.INDEXING_STATE, null);
}

export function setStoredIndexingState(state: IndexingState): void {
  setToStorage(STORAGE_KEYS.INDEXING_STATE, state);
}

export function clearStoredIndexingState(): void {
  removeFromStorage(STORAGE_KEYS.INDEXING_STATE);
}

// Flow state persistence
export function getStoredFlowState(): FlowState | null {
  return getFromStorage(STORAGE_KEYS.FLOW_STATE, null);
}

export function setStoredFlowState(state: FlowState): void {
  setToStorage(STORAGE_KEYS.FLOW_STATE, state);
}

export function clearStoredFlowState(): void {
  removeFromStorage(STORAGE_KEYS.FLOW_STATE);
}

// Mapping config persistence
export function getStoredMappingConfig(): MappingConfig | null {
  return getFromStorage(STORAGE_KEYS.MAPPING_CONFIG, null);
}

export function setStoredMappingConfig(config: MappingConfig): void {
  setToStorage(STORAGE_KEYS.MAPPING_CONFIG, config);
}

export function clearStoredMappingConfig(): void {
  removeFromStorage(STORAGE_KEYS.MAPPING_CONFIG);
}

// Clear all stored state
export function clearAllStoredState(): void {
  clearStoredIndexingState();
  clearStoredFlowState();
  clearStoredMappingConfig();
}

// Check if we have any stored state
export function hasStoredState(): boolean {
  return (
    getStoredIndexingState() !== null ||
    getStoredFlowState() !== null ||
    getStoredMappingConfig() !== null
  );
}


