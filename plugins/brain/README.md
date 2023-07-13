# Brain Plugin

A plugin that contains utilities for working with the
[FiftyOne Brain](https://docs.voxel51.com/user_guide/brain.html).

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/brain
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

### compute_visualization

You can use this operator to create embeddings visualuzations for your
datasets.

This operator is essentially a wrapper around
[compute_visualization()](https://docs.voxel51.com/user_guide/brain.html#visualizing-embeddings):

```py
import fiftyone.brain as fob

fob.compute_visualization(dataset_or_view, brain_key=brain_key, ...)
```

where the operator's form allows you to configure the brain key and all other
relevant parameters.

### compute_similarity

You can use this operator to create similarity indexes for your datasets.

This operator is essentially a wrapper around
[compute_similarity()](https://docs.voxel51.com/user_guide/brain.html#similarity):

```py
import fiftyone.brain as fob

fob.compute_similarity(dataset_or_view, brain_key=brain_key, ...)
```

where the operator's form allows you to configure the brain key and all other
relevant parameters.

### compute_uniqueness

You can use this operator to compute uniqueness for your datasets.

This operator is essentially a wrapper around
[compute_uniqueness()](https://docs.voxel51.com/user_guide/brain.html#image-uniqueness):

```py
import fiftyone.brain as fob

fob.compute_uniqueness(dataset_or_view, uniqueness_field, ...)
```

where the operator's form allows you to configure all relevant parameters.

### compute_mistakenness

You can use this operator to compute mistakenness for your datasets.

This operator is essentially a wrapper around
[compute_mistakenness()](https://docs.voxel51.com/user_guide/brain.html#label-mistakes):

```py
import fiftyone.brain as fob

fob.compute_mistakenness(dataset_or_view, pred_field, label_field, ...)
```

where the operator's form allows you to configure all relevant parameters.

### compute_hardness

You can use this operator to compute hardness for your datasets.

This operator is essentially a wrapper around
[compute_hardness()](https://docs.voxel51.com/user_guide/brain.html#sample-hardness):

```py
import fiftyone.brain as fob

fob.compute_hardness(dataset_or_view, label_field, ...)
```

where the operator's form allows you to configure all relevant parameters.

### get_brain_info

You can use this operator to get information about brain runs.

This operator is essentially a wrapper around
[get_brain_info()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.get_brain_info):

```py
info = dataset_or_view.get_brain_info(brain_key)
print(info)
```

### load_brain_view

You can use this operator to load the view on which a brain run was performed.

This operator is essentially a wrapper around
[load_brain_view()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.load_brain_view):

```py
view = dataset.load_brain_view(brain_key)
```

### rename_brain_run

You can use this operator to rename brain runs.

This operator is essentially a wrapper around
[rename_brain_run()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.rename_brain_run):

```py
dataset_or_view.rename_brain_run(brain_key, new_brain_key)
```

### delete_brain_run

You can use this operator to delete brain runs.

This operator is essentially a wrapper around
[delete_brain_run()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.delete_brain_run):

```py
dataset_or_view.delete_brain_run(brain_key)
```
