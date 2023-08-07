## Common Issues Plugin

![2023-08-07 15 56 33](https://github.com/voxel51/fiftyone-plugins/assets/12500356/ff2302b3-e1ab-4aa0-b599-dd11c27952bb)

This plugin is a Python plugin that allows you to find common issues in your
image datasets.

With this plugin, you can:

-   Find bright images
-   Find dark images
-   Find weird aspect ratios
-   Find low entropy images

It is straightforward to add support for other types of issues!

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/common_issues
```

## Operators

### `compute_brightness`

Computes the brightness of all images in the dataset.

### `compute_aspect_ratio`

Computes the aspect ratio of all images in the dataset.

### `compute_entropy`

Computes the entropy of all images in the dataset.

### `find_issues`

Finds images with brightness, aspect ratio, or entropy issues. You can specify
the threshold for each issue type, and which issue types to check for.
