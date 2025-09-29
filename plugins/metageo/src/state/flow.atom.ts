import { atom } from "recoil";
import { getStoredFlowState } from "../utils/persistence";

const storedFlowState = getStoredFlowState();

export const activeStepAtom = atom<number>({
  key: "metageo/activeStep",
  default: storedFlowState?.activeStep ?? 0,
});

export const hasStartedAtom = atom<boolean>({
  key: "metageo/hasStarted",
  default: storedFlowState?.hasStarted ?? false,
});

export const geoFieldsAtom = atom<string[]>({
  key: "metageo/geoFields",
  default: [],
});

export const osmTagsAtom = atom<
  Array<{ key: string; count: number; examples: string[] }>
>({
  key: "metageo/osmTags",
  default: [],
});
