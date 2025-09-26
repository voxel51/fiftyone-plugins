# Dashboard Plugin

A plugin that enables users to construct custom dashboards that display
statistics of interest about the current dataset (and beyond).

https://github.com/user-attachments/assets/373a7cfe-aab7-45a2-a9f5-76775dcdfa72

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/dashboard
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Usage

1.  Launch the App:

```py
import fiftyone as fo
import fiftyone.zoo as foz
import fiftyone.utils.random as four

dataset = foz.load_zoo_dataset("quickstart")

dataset.untag_samples("validation")
four.random_split(dataset, {"train": 0.6, "test": 0.3, "val": 0.1})

session = fo.launch_app(dataset)
```

2.  Press the `+` button next to the "Samples" tab

3.  Select the `Dashboard` panel

4.  Build a dashboard as shown in the video above!

## Custom data sources

The Dashboard panel supports defining arbitrary custom plots via Python code.
This feature is useful for defining plots that require custom aggregations or
for more advanced use cases such as defining plots that operate across multiple
datasets.

To use this functionality:

1.  Enable **Custom data source** mode in the plot configuration modal
2.  Define your data source by entering valid Python code into the editor

### Defining data sources

All data sources must define `data` object that describes a valid
[plotly-react](https://plotly.com/javascript/react) plot for the chart type
that you've selected in the dashboard's plot creation modal:

```py
# eg: pie chart
data = {
    "labels": ["foo", "bar", ...],
    "values": [1, 2, ...],
}

# eg: histogram
data = {
    "x": [0.1, 0.2, ...],
    "y": [100, 150, ...],
    "name": "...",
}
```

> Do **not** set the `type` property of the `data` object; it will be
> automatically populated based on the chart type you've selected in the modal

Your code has access to a `ctx` variable that contains the dashboard's
[ExecutionContext](https://docs.voxel51.com/plugins/developing_plugins.html#execution-context):

```py
# Use the `ctx` object to interact with the current dataset, view, and more
dataset = ctx.dataset           # the current dataset
view = ctx.view                 # the current view
ids = ctx.selected              # the list of currently selected samples in the App, if any
labels = ctx.selected_labels    # the list of currently selected labels in the App, if any
group_slice = ctx.group_slice   # the active group slice in the App, if any
...
```

You can also add and use custom imports when defining your data sources:

```py
import numpy as np
import fiftyone as fo

...
```

### Example: custom pie chart of label counts

The following custom data source defines a simple pie chart of label counts in
a specified field of the current dataset:

```py
import fiftyone as fo

# Use the `ctx` object to interact with the current view or dataset
dataset = ctx.dataset  # or ctx.view

# Choose a field with categorical values
field = "ground_truth.detections.label"

counts = dataset.count_values(field)

# Define a `data` variable for the dashboard
# NOTE: do not set "type"; instead choose Pie in the chart selector
data = {
    "labels": list(counts.keys()),
    "values": list(counts.values()),
}
```

### Example: multi-dataset histogram

The following custom data source defines a histogram that aggregates values
across multiple datasets:

```python
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import fiftyone as fo

###############################################################################
# Configuration
###############################################################################
names = ["quickstart", "quickstart-video", ...]  # the datasets of interest
path = "uniqueness"  # numeric field that exists on all datasets
bins = 50
max_workers = 16
###############################################################################


def compute_range(name):
    dataset = fo.load_dataset(name)
    return dataset.bounds(path)


def compute_histogram(name):
    dataset = fo.load_dataset(name)
    counts, _, _ = dataset.histogram_values(path, bins=bins, range=range)
    return counts


# compute range (using thread pool for efficiency)
range = (np.inf, -np.inf)
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    for r1, r2 in executor.map(compute_range, names):
        range = (min(range[0], r1), max(range[1], r2))

# compute counts (using thread pool for efficiency)
counts = np.zeros(bins)
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    for c in executor.map(compute_histogram, names):
        counts += np.array(c)

edges = np.linspace(*range, num=bins + 1)
centers = 0.5 * (edges[:-1] + edges[1:])

# Define `data` variable for the dashboard
# NOTE: do not set "type"; instead choose Numeric histogram in the modal
data = {
    "x": centers.tolist(),
    "y": counts.tolist(),
    "name": f"{path} (combined)",
}
```
