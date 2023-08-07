## Interpolation

This plugin allows you to "interpolate" between two text prompts and see the
results in the UI.

Given a `left_prompt`, a `right_prompt`, and an interpolation strength `alpha`,
the plugin will embed the left and right prompts into $v_l$ and $v_r$ and then
sort by similarity on similarity index with selected brain key, with the query

$$v = \alpha v_l + (1 - \alpha) v_r$$

It demonstrates how to do the following:

-   use Python and JS in the same plugin
-   create a `Panel` with custom components
-   query dataset properties from JS
-   add an SVG icon to the UI

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/interpolation
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Operators

### open_interpolation_panel

-   Opens the interpolation panel on click
-   Only activated when the dataset has a similarity index

### interpolator

-   Runs the interpolation
