# Utilities Plugin

A plugin that contains common utilities for working with FiftyOne.

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
dataset.persistent = ...
dataset.tags = ...
dataset.classes = ...

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

### manage_plugins

You can use this operator to manage your FiftyOne plugins from within the App.

This operator is essentially a wrapper around the following
[plugin methods](https://docs.voxel51.com/plugins/index.html):

```py
import fiftyone.plugins as fop

# Plugin enablement
fop.list_plugins()
fop.enable_plugin(name)
fop.disable_plugin(name)

# Plugin package requirements
fop.load_plugin_requirements()
fop.ensure_plugin_requirements()

# Plugin installation
fop.download_plugin()
```

where the operator's form allows you to navigate between the available actions.
