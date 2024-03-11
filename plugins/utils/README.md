# Utilities Plugin

A plugin that contains common utilities for working with FiftyOne.

https://github.com/voxel51/fiftyone-plugins/assets/25985824/21ed4dd0-b4f3-4dfa-abb3-949672f59e46

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/utils
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

### create_dataset

You can use this operator to create a new dataset from within the App.

This operator is essentially a wrapper around the
[Dataset()](https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.Dataset)
constructor:

```py
dataset = fo.Dataset(name, persistent=persistent)
```

where the operator's form allows you to configure the name and persistence of
the dataset.

### load_dataset

You can use this operator to switch to a different dataset in the App.

This operator is essentially a wrapper around the
[load_dataset()](https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.load_dataset)
method:

```py
session.dataset = fo.load_dataset(name)
```

where the operator's form allows you to configure the name of the dataset to
load.

### edit_dataset_info

You can use this operator to edit dataset-level metadata in the App.

This operator is essentially a wrapper around the various dataset properties
described in
[this section](https://docs.voxel51.com/user_guide/using_datasets.html#datasets)
of the docs:

```py
# Basic
dataset.name = ...
dataset.description = ...
dataset.persistent = ...
dataset.tags = ...

# Info
dataset.info = ...

# App config
dataset.app_config = ...

# Classes
dataset.classes = ...
dataset.default_classes = ...

# Mask targets
dataset.mask_targets = ...
dataset.default_mask_targets = ...

# Keypoint skeletons
dataset.skeletons = ...
dataset.default_skeleton = ...
```

where the operator's form allows you to edit any of the above properties.

### rename_dataset

You can use this operator to rename a dataset in the App.

This operator is essentially a wrapper around setting the dataset's
[name](https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.Dataset.name)
property:

```py
dataset.name = new_name
```

where the operator's form allows you to configure the new name for the dataset.

### delete_dataset

You can use this operator to delete a dataset in the App.

This operator is essentially a wrapper around the
[delete_dataset()](https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.delete_dataset)
method:

```py
fo.delete_dataset(name)
```

where the operator's form allows you to configure the name of the dataset to
delete.

### delete_samples

You can use this operator to delete samples from a dataset in the App.

This operator is essentially a wrapper around the
[delete_samples()](https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.delete_samples)
method:

```py
# Delete the currently selected samples
dataset.delete_samples(session.selected)

# Delete the current view
datast.delete_samples(session.view)

# Delete all samples
dataset.clear()
```

where the operator's form allows you to choose which samples to delete.

### compute_metadata

You can use this operator to populate the `metadata` field of a collection.

This operator is essentially a wrapper around the
[compute_metadata()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.compute_metadata)
method:

```py
dataset_or_view.compute_metadata(...)
```

where the operator's form allows you to configure any applicable optional
arguments for `compute_metadata()`.

### generate_thumbnails

You can use this operator to generate thumbnails for the media in a collection.

This operator is essentially a wrapper around the
[following pattern](https://docs.voxel51.com/user_guide/app.html#multiple-media-fields):

```py
import fiftyone.utils.image as foui

foui.transform_images(
    dataset_or_view,
    size=(width, height),
    output_field="thumbnail_path",
    output_dir="/path/for/thumbnails",
    skip_failures=True,
)

dataset.app_config.media_fields.append("thumbnail_path")
dataset.app_config.grid_media_field = "thumbnail_path"
dataset.save()
```

where the operator's form allows you to configure the `(width, height)` for the
thumbnails, the field in which to store their paths, and the directory in which
to store the thumbnail images.

### delegate (SDK-only)

You can use this operator to programmatically
[delegate execution](https://docs.voxel51.com/plugins/using_plugins.html#delegated-operations)
of an arbitrary function call that can be expressed in any of the following
forms:

-   Execute an arbitrary function: `fcn(*args, **kwargs)`
-   Apply a function to a dataset or view:
    `fcn(dataset_or_view, *args, **kwargs)`
-   Call an instance method of a dataset or view:
    `dataset_or_view.fcn(*args, **kwargs)`

```py
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")
delegate = foo.get_operator("@voxel51/utils/delegate")

# Compute metadata
delegate("compute_metadata", dataset=dataset)

# Compute visualization
delegate(
    "fiftyone.brain.compute_visualization",
    dataset=dataset,
    brain_key="img_viz",
)

# Export a view
delegate(
    "export",
    view=dataset.to_patches("ground_truth"),
    export_dir="/tmp/patches",
    dataset_type="fiftyone.types.ImageClassificationDirectoryTree",
    label_field="ground_truth",
)

# Load the exported patches into a new dataset
delegate(
    "fiftyone.Dataset.from_dir",
    dataset_dir="/tmp/patches",
    dataset_type="fiftyone.types.ImageClassificationDirectoryTree",
    label_field="ground_truth",
    name="patches",
    persistent=True,
)
```

### reload_saved_view

You can use this operator to reload saved views on a dataset that are
_generated_ (patches, frames, or clips).

This operator is essentially a wrapper around the following pattern:

```py
view = dataset.load_saved_view(name)
view.reload()

dataset.save_view(name, view, overwrite=True)
```

where the operator's form allows you to select the saved view to reload.
