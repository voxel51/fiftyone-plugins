# Evaluation Plugin

A plugin that contains utilities for
[evaluating models](https://docs.voxel51.com/user_guide/evaluation.html) in
FiftyOne.

https://github.com/voxel51/fiftyone-plugins/assets/25985824/c599d737-a6f2-4737-a751-15ec4cf6a1bd

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/evaluation
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Usage

1.  Launch the App:

```py
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")
session = fo.launch_app(dataset)
```

2.  Press `` ` `` or click the `Browse operations` action to open the Operators
    list

3.  Select any of the operators listed below!

## Operators

### evaluate_model

You can use this operator to evaluate model predictions on your datasets.

This operator is essentially a wrapper around all supported
[evaluation methods](https://docs.voxel51.com/user_guide/evaluation.html) that
FiftyOne supports:

```py
# Regression evaluation
dataset_or_view.evaluate_regressions(
    "predictions",
    gt_field="ground_truth",
    eval_key=eval_key,
    ...,
)

# Classification evaluation
dataset_or_view.evaluate_classifications(
    "predictions",
    gt_field="ground_truth",
    eval_key=eval_key,
    ...,
)

# Detection evaluation
dataset_or_view.evaluate_detections(
    "predictions",
    gt_field="ground_truth",
    eval_key=eval_key,
    ...,
)

# Segmentation evaluation
dataset_or_view.evaluate_segmentations(
    "predictions",
    gt_field="ground_truth",
    eval_key=eval_key,
    ...,
)
```

where the operator's form allows you to configure the prediction/ground truth
fields of interest, an evaluation key, and all other relevant parameters.

### get_evaluation_info

You can use this operator to get information about evaluation runs.

This operator is essentially a wrapper around
[get_evaluation_info()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.get_evaluation_info):

```py
info = dataset_or_view.get_evaluation_info(eval_key)
print(info)
```

### load_evaluation_view

You can use this operator to load the view on which an evaluation was
performed.

This operator is essentially a wrapper around
[load_evaluation_view()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.load_evaluation_view):

```py
view = dataset.load_evaluation_view(eval_key)
```

### rename_evaluation

You can use this operator to rename evaluation runs.

This operator is essentially a wrapper around
[rename_evaluation()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.rename_evaluation):

```py
dataset_or_view.rename_evaluation(eval_key, new_eval_key)
```

### delete_evaluation

You can use this operator to delete evaluation runs.

This operator is essentially a wrapper around
[delete_evaluation()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.delete_evaluation):

```py
dataset_or_view.delete_evaluation(eval_key)
```
