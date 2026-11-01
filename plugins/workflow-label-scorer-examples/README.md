# Workflow Label Scorer Examples

An example **label scorer** for FiftyOne workflows. A benchmark scores
each person's labels against the gold set, and a consensus stage scores
how much the copies of a sample agree. The built-in scorer gives boxes
their same-class IoU and nothing for their attributes. A scorer of your
own replaces only the maths: **how close two labels are, and what
passes**. The runtime keeps doing everything around it: queueing the
work so a submit never waits, building the request, retrying when the
scorer is down, storing the scores, settling attempts, routing consensus
sets and feeding the Metrics rollups.

Requires the `@voxel51/workflows` plugin (ships with FiftyOne Enterprise).

## Install

```bash
fiftyone plugins download \
  https://github.com/voxel51/fiftyone-plugins \
  --plugin-names @voxel51/workflow-label-scorer-examples
```

Or zip this directory and upload it from **Settings > Plugins**. The
scorer appears in the **Metric** select of **New benchmark** (with
*Custom metrics: Yes*) and of a consensus group, as soon as the plugin
loads: discovery is automatic (the runtime duck-types any operator that
exposes a `label_scorer_descriptor`). The scorer must be installed where
the workflows plugin runs.

## The scorer: boxes + attributes

In `scorers.py`, for `Detections` fields:

- **Pairing.** Boxes pair within a class, highest IoU first, at IoU of
  at least *Match at IoU*.
- **Box score.** `(1 - w) * IoU + w * attribute agreement`, where `w` is
  *Attribute weight*. Attribute agreement uses the label schema's
  conditional (`when`) rules: an attribute counts when either side was
  asked it, so a wrong parent also costs the children it hides.
- **Scored attributes.** Only these count. All of them by default.
- **Critical attributes.** A wrong value zeroes the box.
- **Sample score.** The sum of box scores over pairs + extra + missed
  boxes.
- **Verdict.** An attempt (or consensus set) passes when its mean clears
  *Pass score* and its critical misses are at most *Critical misses
  allowed*.

This formula is only the example's choice. Yours can ignore IoU, score
other label types, or decide pass/fail any way it likes.

## The contract

A scorer is a plain operator with a `label_scorer_descriptor`:

| Key | Meaning |
|-----|---------|
| `label`, `description` | Shown in the Metric select |
| `label_types` | Field types it scores, e.g. `["Detections"]` (none: any) |
| `kinds` | `"benchmark"`, `"consensus"` or both |
| `verdict` | `True` to decide pass/fail yourself (step `verdict`) |
| `options` | Fields shown under the Metric select: `float`, `int`, `bool`, `choice` or `attributes` |

An option named `pass_threshold` replaces the benchmark's own pass score.

The runtime calls `execute` with `ctx.params["request"]`. Step `score`
carries many samples per call; `a` is the submission (or one copy), `b`
the gold (or another copy), both as label dicts:

```python
{
    "kind": "benchmark",
    "step": "score",
    "field": {"name": "gt", "label_type": "Detections", "attributes": [...]},
    "options": {"min_iou": 0.5, ...},
    "samples": [{"id": "...", "sample_id": "...", "a": {...}, "b": {...}}],
}
```

Return a 0–1 score per sample id, and optionally `passed`, per-box
`matches` / `extra` / `missed` (the App colours the boxes) and a free
`detail`. `None` for an id hands it to the built-in scorer:

```python
{"scores": {"<id>": {"score": 0.8, "detail": {...}}}}
```

Step `verdict` runs once per attempt (or consensus set) after its last
score, with every sample's score and detail, and returns
`{"score", "passed", "summary"?, "kept"?}`.

`fiftyone.management.scoring` has the built-in scorer's pieces to build
on: `pair_objects`, `score_attributes` (with the `when` rules) and
`label_from_dict`.
