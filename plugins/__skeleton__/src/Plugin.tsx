import * as fos from "@fiftyone/state";
import { useRecoilValue } from "recoil";

export function Plugin() {
  const dataset = useRecoilValue(fos.dataset);
  return (
    <h1>
      You are viewing the <strong>{dataset.name}</strong> dataset.
    </h1>
  );
}
