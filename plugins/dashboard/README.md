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

# Feature: Multi-Dataset Charts in the Dashboard Plugin

You can build charts that span **multiple FiftyOne Datasets** by pasting a
small “magic code” snippet into the Dashboard panel’s **Code** input. For now
this is an advanced/hidden capability—there’s no multi-select UI yet.

## What this does

-   Aggregates data across **multiple datasets** that share the **same
    schema/field names**.
-   Produces chart data by setting a Python variable named `data` to **Plotly
    React props** (e.g., `{"x": [...], "y": [...]}`).
-   The Dashboard will add the correct `type` automatically from the chart
    selector (no need to include it).

> Assumptions
>
> -   All selected datasets have the same fields.
> -   You can open the Dashboard in the context of any dataset; the code below
>     is what makes it multi-dataset.
> -   Pick the desired chart type (e.g., **Bar**) in the Dashboard UI; the
>     panel will set `data["type"]` for you.

---

## Example: Multi-Dataset Histogram (combined counts)

Paste this into the Dashboard panel’s **Code** editor, edit the `names`,
`path`, and `bins`, then select **Bar** as the chart type.

```python
# Multi-dataset histogram (combined) — paste into Dashboard "Code" editor

import numpy as np
import fiftyone as fo

# --- EDIT THESE ---
names = [
    "quickstart",  # add your datasets here
    "quickstart-video",
]
path = "uniqueness"  # numeric field or expression supported by FiftyOne
bins = 50
# -------------------

# Compute global range across all datasets
rmin, rmax = np.inf, -np.inf
for name in names:
    ds = fo.load_dataset(name)
    vmin, vmax = ds.bounds(path)
    rmin = min(rmin, vmin)
    rmax = max(rmax, vmax)

# Aggregate histogram counts across datasets
counts = np.zeros(bins, dtype=float)
for name in names:
    ds = fo.load_dataset(name)
    c, _, _ = ds.histogram_values(path, bins=bins, range=(rmin, rmax))
    counts += np.asarray(c, dtype=float)

# Convert to Plotly React props
edges = np.linspace(rmin, rmax, num=bins + 1)
centers = 0.5 * (edges[:-1] + edges[1:])

# IMPORTANT: The Dashboard reads this `data` variable.
# Do NOT set "type"; the panel adds it based on your UI chart selection.
data = {
    "x": centers.tolist(),
    "y": counts.tolist(),
    "name": f"{path} (combined)",
}
```

## Plotly React

See the [plotly-react documentation](https://plotly.com/javascript/react/) for
more info about the `data` object.
