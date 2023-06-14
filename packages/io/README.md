# I/O Plugin

A plugin that contains standard import/export utilities.

## Installation

### Install latest

To install the latest version of this plugin, simply run:

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/io
```

### Plugin management

```shell
# List all downloaded plugins
fiftyone plugins list

# List available operators
fiftyone operators list

# Disable this plugin
fiftyone plugins disable @voxel51/io

# Enable this plugin
fiftyone plugins enable @voxel51/io
```

### Local development

If you plan to develop this plugin (or any other plugins in the
`fiftyone-plugins` repository), you can clone the repository and symlink it
into your plugins directory like so:

```shell
git clone https://github.com/voxel51/fiftyone-plugins
ln -s "$(pwd)/fiftyone-plugins" "$(fiftyone config plugins_dir)/fiftyone-plugins"
```

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

### add_samples

Use this operator to add samples to an existing dataset by specifying a
directory or glob pattern of media paths for which you want to create new
samples.

This operator is essentially a wrapper around the following import recipes:

```py
# Directories
dataset.add_images_dir(input_dir)
dataset.add_videos_dir(input_dir)

# Glob patterns
dataset.add_images_patt(glob_patt)
dataset.add_videos_patt(glob_patt)
```

### export_samples

You can use this operator to export your current dataset or view to disk in any
supported format.

This operator is essentially a wrapper around the following
[export receipe](https://docs.voxel51.com/user_guide/export_datasets.html#basic-recipe):

```py
# The directory to which to write the exported dataset
export_dir = "/path/for/export"

# The type of dataset to export
dataset_type = fo.types.COCODetectionDataset  # for example

# The name of the sample field containing the label that you wish to export
# Used when exporting labeled datasets (e.g., classification or detection)
label_field = "ground_truth"  # for example

dataset_or_view.export(
    export_dir=export_dir,
    dataset_type=dataset_type,
    label_field=label_field,
)
```

where the operator's form allows you to configure the export location, dataset
type, and necessary label field(s), if applicable.
