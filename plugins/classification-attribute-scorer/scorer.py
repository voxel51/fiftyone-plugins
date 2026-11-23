"""
Label scorer that scores a classification on its attributes only.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import fiftyone.operators as foo
from fiftyone.management.scoring import label_from_dict, score_attributes


class ClassificationAttributes(foo.Operator):
    """A classification scores the share of its attributes that match the
    other label. The class is not counted. Conditional attributes follow
    the label schema: one either side was asked counts, so a wrong parent
    also costs the children it hides. A label on one side only scores 0."""

    label_scorer_descriptor = {
        "label": "Classification attributes",
        "description": "Attribute agreement; the class is not counted",
        "label_types": ["Classification"],
        "kinds": ["benchmark", "consensus"],
        "options": {
            "scored": {
                "type": "attributes",
                "label": "Scored attributes",
                "description": "Only these count. All by default.",
                "default": None,
            },
        },
    }

    @property
    def config(self):
        return foo.OperatorConfig(
            name="classification_attributes",
            label="Classification attributes scorer",
            unlisted=True,
        )

    def execute(self, ctx):
        request = ctx.params["request"]
        specs = request["field"].get("attributes")
        scored = (request.get("options") or {}).get("scored")
        if specs is not None and scored is not None:
            keep = set(scored)
            specs = [s for s in specs if s.get("name") in keep]
        return {
            "scores": {
                s["id"]: score_sample(s.get("a"), s.get("b"), specs)
                for s in request["samples"]
            }
        }


def score_sample(a, b, specs):
    """``a`` is the submission (or a copy), ``b`` the gold (or another
    copy), both label dicts or ``None``."""
    a_label = label_from_dict(a)
    b_label = label_from_dict(b)
    if a_label is None and b_label is None:
        return {"score": 1.0, "note": "both empty"}
    out = {
        "expected": getattr(b_label, "label", None),
        "got": getattr(a_label, "label", None),
    }
    if a_label is None or b_label is None:
        out["score"] = 0.0
        out["note"] = "missing" if a_label is None else "extra"
        return out
    attrs = score_attributes(a_label, b_label, specs)
    slots = [s for s in attrs["slots"] if s["name"] != "label"]
    counted = [s["agree"] for s in slots if s.get("asked") != "neither"]
    score = sum(counted) / len(counted) if counted else 1.0
    out["score"] = score
    out["attributes"] = {"score": score, "slots": slots}
    return out
