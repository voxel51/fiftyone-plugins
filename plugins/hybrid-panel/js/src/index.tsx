import { Button, Stack, Typography } from "@mui/material";
import { PluginComponentType, registerComponent } from "@fiftyone/plugins";
import { useState } from "react";
import { useTriggerPanelEvent } from "@fiftyone/operators";
import { usePanelStatePartial } from "@fiftyone/spaces";

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
  const { count: _count, fibonacci } = data;
  const [count, setCount] = useState(_count || 0);
  const triggerPanelEvent = useTriggerPanelEvent();
  const showFibonacci = typeof fibonacci === "number";

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
