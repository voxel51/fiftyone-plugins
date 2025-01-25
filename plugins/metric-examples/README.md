# Metric Examples

A plugin that demonstrates how to define
[custom evaluation metrics](https://docs.voxel51.com/user_guide/evaluation.html)
that you can apply when evaluating models in FiftyOne.

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/metric-examples
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Usage

### `example_metric`

To use Option 1 below, you'll need to install the
[@voxel51/evaluation plugin](https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/evaluation):

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/evaluation
```

```py
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")

#
# Option 1: App usage
#
# Launch the `evaluate_model` operator from the Operator Browser
# Scroll to the bottom of the modal to choose/configure custom metrics to apply
#
# Use the `delete_evaluation` operator to cleanup an evaluation
#

session = fo.launch_app(dataset)

#
# Option 2: SDK usage
#

# A custom metric to apply
metric = "@voxel51/metric-examples/example_metric"
kwargs = dict(value="spam")

results = dataset.evaluate_detections(
    "predictions",
    gt_field="ground_truth",
    eval_key="eval",
    custom_metrics={metric: kwargs},
)

print(dataset.count_values("eval_example_metric"))
results.print_metrics()

dataset.delete_evaluation("eval")

assert not dataset.has_field("eval_example_metric")
```

### `absolute_error` and `squared_error`

```py
import random
import numpy as np

import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("cifar10", split="test")
dataset.delete_sample_field("ground_truth")

for idx, sample in enumerate(dataset.iter_samples(autosave=True, progress=True), 1):
    ytrue = random.random() * idx
    ypred = ytrue + np.random.randn() * np.sqrt(ytrue)
    confidence = random.random()
    sample["ground_truth"] = fo.Regression(value=ytrue)
    sample["predictions"] = fo.Regression(value=ypred, confidence=confidence)

results = dataset.evaluate_regressions(
    "predictions",
    gt_field="ground_truth",
    eval_key="eval",
    custom_metrics=[
        "@voxel51/metric-examples/absolute_error",
        "@voxel51/metric-examples/squared_error",
    ],
)

print(dataset.bounds("eval_absolute_error"))
print(dataset.bounds("eval_squared_error"))

results.print_metrics()

dataset.delete_evaluation("eval")

assert not dataset.has_field("eval_absolute_error")
assert not dataset.has_field("eval_squared_error")
```
