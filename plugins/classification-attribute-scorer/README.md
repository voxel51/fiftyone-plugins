# Classification Attribute Scorer

A label scorer for FiftyOne workflows that scores a `Classification` on its
attributes only. It is the built-in classification scorer without the class
slot: the share of attributes that match, averaged.

- **Class.** Not counted. A wrong class with every attribute right scores 1.
- **Conditional attributes.** Follow the label schema's `when` rules, as the
  built-in scorer does: an attribute counts when either side was asked it,
  so a wrong parent also costs the children it hides.
- **Scored attributes.** Only these count. All of them by default.
- **One side empty.** A label on only one side scores 0; neither side
  scores 1. A label with no attributes to compare also scores 1.
- **Pass/fail.** The benchmark's (or consensus stage's) own pass threshold.

Requires the `@voxel51/workflows` plugin (ships with FiftyOne Enterprise).

## Install

Zip this directory and upload it from **Settings > Plugins**, or:

```bash
fiftyone plugins download \
  https://github.com/voxel51/fiftyone-plugins \
  --plugin-names @voxel51/classification-attribute-scorer
```

It appears as **Classification attributes** in the **Metric** select of
**New benchmark** (with *Custom metrics: Yes*) and of a consensus stage.
