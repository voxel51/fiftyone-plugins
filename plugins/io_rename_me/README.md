# I/O Plugin

A plugin that contains a collection of helpful import/export utilities.

https://github.com/voxel51/fiftyone-plugins/assets/25985824/7a8186fb-636f-4f7d-9ac7-8822a76cfded

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/io
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

### import_samples

Use this operator to import samples and/or labels to an existing dataset via
any of the following methods:

-   A directory of media for which you want to create new samples
-   A glob pattern of media paths for which you want to create new samples
-   A directory containing media and/or labels in any
    [supported format](https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#supported-import-formats)
    for which you want to create new samples
-   One or more file(s) containing labels to add to the existing samples in
    your dataset

This operator is essentially a wrapper around the following
[import recipes](https://docs.voxel51.com/user_guide/dataset_creation/index.html):

```py
# Add a directory of media
dataset.add_images_dir(input_dir)
dataset.add_videos_dir(input_dir)

# Add a glob pattern of media
dataset.add_images_patt(glob_patt)
dataset.add_videos_patt(glob_patt)

# Add a directory of media and/or labels in a supported format
dataset.add_dir(
    dataset_dir="/path/to/data",
    dataset_type=fo.types.XXXX,
    label_field=YYYYY,
)

# Add labels to existing samples in a supported format
data_path = {os.path.basename(p): p for p in dataset.values("filepath")}
dataset.merge_dir(
    data_path=data_path,
    labels_path="/path/to/labels.json",
    dataset_types=fo.types.XXXX,
    label_field=YYYYY,
)
```

### merge_samples

You can use this operator to merge a dataset or view into another dataset.

This operator is essentially a wrapper around the
[merge_samples()](https://docs.voxel51.com/api/fiftyone.core.dataset.html#fiftyone.core.dataset.Dataset.merge_samples)
method:

```py
dst_dataset.merge_samples(src_samples, ...)
```

where the operator's form allows you to configure the source collection, the
destination dataset, and any applicable optional arguments for
`merge_samples()`.

### merge_labels

You can use this operator to merge labels from one field of a collection into
another field.

This operator is essentially a wrapper around the
[merge_labels()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.merge_labels)
method:

```py
dataset_or_view.merge_labels(in_field, out_field)
```

### export_samples

You can use this operator to export your current dataset or view to disk in any
supported format.

This operator is essentially a wrapper around the following
[export recipe](https://docs.voxel51.com/user_guide/export_datasets.html#basic-recipe):

```py
# The directory to which to write the export
export_dir = "/path/for/export"

# The type of dataset to export
dataset_type = fo.types.COCODetectionDataset  # for example

# The name of the sample field containing the labels to export
label_field = "ground_truth"

# Whether to include the media files
export_media = True

dataset_or_view.export(
    export_dir=export_dir,
    dataset_type=dataset_type,
    label_field=label_field,
    export_media=export_media,
)
```

where the operator's form allows you to configure the export location, dataset
type, and necessary label field(s), if applicable.

### draw_labels

You can use this operator to render annotated versions of the media in a
collection with the specified label data overlaid to a directory on disk.

This operator is essentially a wrapper around the
[draw_labels()](https://docs.voxel51.com/api/fiftyone.core.collections.html#fiftyone.core.collections.SampleCollection.draw_labels)
method:

```py
dataset_or_view.draw_labels(
    output_dir,
    label_fields=label_fields,
    ...
)
```

where the operator's form allows you to configure the output directory on disk,
the label field(s) to render, and any other optional arguments for
`draw_labels()`.
