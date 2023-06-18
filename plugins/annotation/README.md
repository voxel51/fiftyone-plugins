# Annotation Plugin

A plugin that contains utilities for integrating FiftyOne with your annotation
tools.

In order to use this plugin, you must have at least one annotation backend
configured as
[described here](https://docs.voxel51.com/user_guide/annotation.html).

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/annotation
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

### request_annotations

You can use this operator to create annotation tasks for the current dataset or
view.

This operator is essentially a wrapper around the
[request annotations Python workflow](https://docs.voxel51.com/user_guide/annotation.html#requesting-annotations):

```py
dataset_or_view.annotate(
    anno_key,
    backend=...,
    label_schema=...,
    ...
)
```

where the operator's form allows you to configure the annotation key,
annotation backend, label schema, and any other applicable fields for your
annotation backend.

### load_annotations

You can use this operator to load annotations from existing annotation runs
back onto your dataset.

This operator is essentially a wrapper around the
[load annotations Python workflow](https://docs.voxel51.com/user_guide/annotation.html#loading-annotations):

```py
dataset_or_view.load_annotations(anno_key, ...)
```

where the operator's form allows you to configure the annotation key and
related options.
