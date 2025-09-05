import { atom } from "recoil";

export const activeStepAtom = atom<number>({
  key: "metageo/activeStep",
  default: 0,
});

export const hasStartedAtom = atom<boolean>({
  key: "metageo/hasStarted",
  default: false,
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
