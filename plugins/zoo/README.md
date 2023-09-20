# Zoo Plugin

A plugin that contains utilities for working with the
[FiftyOne Dataset Zoo](https://docs.voxel51.com/user_guide/dataset_zoo/index.html)
and
[FiftyOne Model Zoo](https://docs.voxel51.com/user_guide/model_zoo/index.html).

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/zoo
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

### load_zoo_dataset

You can use this operator to download any dataset from the
[FiftyOne Dataset Zoo](https://docs.voxel51.com/user_guide/dataset_zoo/index.html).

This operator is essentially a wrapper around the
[load_zoo_dataset()](https://docs.voxel51.com/api/fiftyone.zoo.html#fiftyone.zoo.load_zoo_dataset)
method:

```py
dataset = foz.load_zoo_dataset(name, splits=splits, ...)
```

where the operator's form allows you to choose a dataset and provide any
applicable optional arguments for `load_zoo_dataset()`.

### apply_zoo_model

You can use this operator to download and run inference with any model from the
[FiftyOne Model Zoo](https://docs.voxel51.com/user_guide/model_zoo/index.html).

This operator is essentially a wrapper around the
[load_zoo_model()](https://docs.voxel51.com/api/fiftyone.zoo.html#fiftyone.zoo.load_zoo_model),
[apply_model()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.apply_model),
[compute_embeddings()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.compute_embeddings),
and
[compute_patch_embeddings()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.compute_patch_embeddings)
methods:

```py
model = foz.load_zoo_model(name)

# Predictions
dataset_or_view.apply_model(
    model,
    label_field=label_field,
    ...,
)

# Embeddings
dataset_or_view.compute_embeddings(
    model,
    embeddings_field=embeddings_field,
    ...
)

# Patch embeddings
dataset_or_view.compute_patch_embeddings(
    model,
    patches_field,
    embeddings_field=embeddings_field,
    ...
)
```

where the operator's form allows you to choose a model, an inference type
(predictions or embeddings, if applicable), a field in which to store the
inference results, and provide any applicable optional arguments.
