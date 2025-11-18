import { Button, Stack, Typography } from "@mui/material";
import { PluginComponentType, registerComponent } from "@fiftyone/plugins";
import { useCallback, useState } from "react";
import { useTriggerPanelEvent } from "@fiftyone/operators";
import { usePanelState, usePanelStatePartial } from "@fiftyone/spaces";

registerComponent({
  name: "HybridCounterComponent",
  label: "HybridCounterComponent",
  component: HybridCounter,
  type: PluginComponentType.Component,
  activator: () => true,
});

function HybridCounter(props) {
  const { data, schema } = props;
  const { save_count, calculate_fibonacci_event } = schema.view;
  const { fibonacci } = data;
  const showFibonacci = typeof fibonacci === "number";

  const [count, setCount] = useCount();
  const triggerPanelEvent = useTriggerPanelEvent();
  const panelState = usePanelStatePartial("state", {});
  const panelData = usePanelStatePartial("data", {}, true);

  console.log(">>>", panelState, panelData);

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ p: 1, py: 3 }}>
      <Typography color="secondary">Count:</Typography>
      <Typography>{count}</Typography>
      {showFibonacci && (
        <Stack direction="row" spacing={1}>
          <Typography color="secondary">Fibonacci:</Typography>
          <Typography>{fibonacci}</Typography>
        </Stack>
      )}
      <Button onClick={() => setCount(count + 1)} variant="outlined">
        Increment
      </Button>
      <Button onClick={() => setCount(count - 1)} variant="outlined">
        Decrement
      </Button>
      <Button onClick={() => setCount(0)} variant="outlined">
        Reset
      </Button>
      <Button
        variant="contained"
        onClick={() => {
          triggerPanelEvent(calculate_fibonacci_event, { value: count });
        }}
      >
        Re-calculate fibonacci
      </Button>
      <Button
        variant="contained"
        onClick={() => {
          triggerPanelEvent(save_count, { count });
        }}
      >
        Save count
      </Button>
    </Stack>
  );
}

function useCount() {
  const [state, setState] = usePanelStatePartial("state", {});

  const setCount = useCallback(
    (newCount: number) => {
      setState((state) => ({ ...state, count: newCount }));
    },
    [setState]
  );

  return [state.count, setCount];
}
