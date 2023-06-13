## About

Create a `fiftyone.View` in the FiftyoneApp using the python syntax.

To use, open the operator browser and type "Create View with Python".

## Installation

CLI

```shell
fiftyone plugins download \
        https://github.com/voxel51/fiftyone-plugins \
        --plugin-names @voxel51/python_view
```

Python

```python
import fiftyone.plugins as fop

fop.download_plugin(
    "https://github.com/voxel51/fiftyone-plugins",
    plugin_names=["@voxel51/python_view"]
```

## Operators

### create_view_with_python

 - Accepts Python as the only input param
 - The provided Python must start with "view."
 - Updates the app's view to match the provided Python