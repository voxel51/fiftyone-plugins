# Brain Plugin

A plugin that contains utilities for working with the
[FiftyOne Brain](https://docs.voxel51.com/user_guide/brain.html).

https://github.com/voxel51/fiftyone-plugins/assets/25985824/9215bb6b-8d16-4409-bd59-37ad3ccc4679

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/brain
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Configuration

You can optionally configure which license(s) models must be distributed under
in order to be made available by this plugin's operators by setting the
following
[plugin secret](https://docs.voxel51.com/plugins/using_plugins.html#plugin-secrets):

```shell
export FIFTYONE_ZOO_ALLOWED_MODEL_LICENSES="MIT,Apache 2.0"
```

Run the following command to see the available models and their licenses:

```shell
fiftyone zoo models list
```

You can also provide a specific list of models that should be made available by
this plugin's operators by setting the following
[plugin secret](https://docs.voxel51.com/plugins/using_plugins.html#plugin-secrets):

```shell
export FIFTYONE_ZOO_ALLOWED_MODEL_NAMES="clip-vit-base32-torch,zero-shot-classification-transformer-torch"
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

### compute_visualization

You can use this operator to create embeddings visualizations for your
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

### sort_by_similarity

You can use this operator to perform image/text similarity queries against any
similarity indexes on your dataset.

This operator is essentially a wrapper around
[sort_by_similarity()](https://docs.voxel51.com/user_guide/brain.html#similarity):

```py
view = dataset.sort_by_similarity(query, brain_key=brain_key, k=k, ...)
```

This operator supports all of the following similarity queries:

-   Searching by
    [image similarity](https://docs.voxel51.com/user_guide/brain.html#image-similarity)
    based on the currently selected samples in the App
-   Searching by
    [image similarity](https://docs.voxel51.com/user_guide/brain.html#image-similarity)
    to an uploaded image
-   Searching by
    [text similarity](https://docs.voxel51.com/user_guide/brain.html#text-similarity)

### add_similar_samples

You can use this operator to retrieve similar samples from another dataset to
add to your current dataset.

This operator is essentially a wrapper around the following pseudocode:

```py
view = src_dataset.sort_by_similarity(query, brain_key=brain_key, k=k)

dataset.add_samples(view)
```

This operator supports both image and text similarity queries, depending on
whether you have samples currently selected in the App when you launch the
operator:

-   If one or more samples currently selected, an
    [image similarity](https://docs.voxel51.com/user_guide/brain.html#image-similarity)
    query will be performed to retrieve similar images from `src_dataset` to
    your currently selected samples in `dataset`
-   Otherwise, a
    [text similarity](https://docs.voxel51.com/user_guide/brain.html#text-similarity)
    query will be performed to retrieve new images from `src_dataset` that
    match the provided text prompt

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

### find_exact_duplicates + deduplicate_exact_duplicates

You can use these operators to detect and delete samples with exact duplicate
media in a dataset.

The `find_exact_duplicates` operator is essentially a wrapper around
[compute_exact_duplicates()](https://docs.voxel51.com/api/fiftyone.brain.html#fiftyone.brain.compute_exact_duplicates):

```py
import fiftyone.brain as fob

results = fob.compute_exact_duplicates(dataset_or_view)
print(results)
```

Executing this operator will create two saved views on your dataset:

-   `exact duplicates`: a view that contains all samples whose media is an
    exact duplicate of one or more other samples
-   `representatives of exact duplicates`: a view that contains one
    representative sample from each group of exact duplicates

Executing the `deduplicate_exact_duplicates` operator will delete all of the
exact duplicate samples from the `exact duplicates` view **except** the one
representiatve from each group in the `representatives of exact duplicates`
view.

### find_near_duplicates + deduplicate_near_duplicates

You can use these operators to detect and delete near duplicate samples in a
dataset.

The `find_near_duplicates` operator is essentially a wrapper around
[compute_near_duplicates()](https://docs.voxel51.com/api/fiftyone.brain.html#fiftyone.brain.compute_near_duplicates):

```py
import fiftyone.brain as fob

results = fob.compute_near_duplicates(dataset_or_view, threshold=threshold, ...)
print(results)
```

where the operator's form allows you to configure the embeddings to use to
compute near duplicates along with an appropriate distance threshold to use to
detect duplicates in embeddings space.

Executing this operator will create two saved views on your dataset:

-   `near duplicates`: a view that contains all samples that are near
    duplicates of one or more other samples
-   `representatives of near duplicates`: a view that contains one
    representative sample from each group of near duplicates

Executing the `deduplicate_near_duplicates` operator will delete all of the
near duplicate samples from the `near duplicates` view **except** the one
representiatve from each group in the `representatives of near duplicates`
view.

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
