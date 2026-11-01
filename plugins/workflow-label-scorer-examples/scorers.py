"""
Example label scorer for FiftyOne workflows: boxes scored on overlap and
on their attributes, with conditional attributes counted the way the
label schema asks them.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import fiftyone.operators as foo
from fiftyone.management.scoring import (
    label_from_dict,
    pair_objects,
    score_attributes,
)


class BoxesWithAttributes(foo.Operator):
    """Each pair of boxes scores ``(1 - w) * IoU + w * attribute
    agreement``; a wrong critical attribute zeroes the box. A sample
    scores the sum over pairs, extra and missed boxes. An attempt (or a
    consensus set) passes when the mean clears the pass score and its
    critical misses stay within the allowance."""

    label_scorer_descriptor = {
        "label": "Boxes + attributes",
        "description": "IoU and attribute agreement per matched box",
        "label_types": ["Detections"],
        "kinds": ["benchmark", "consensus"],
        "verdict": True,
        "options": {
            "min_iou": {
                "type": "float",
                "label": "Match at IoU",
                "description": "Boxes below this overlap don't pair.",
                "default": 0.5,
                "min": 0,
                "max": 1,
            },
            "attribute_weight": {
                "type": "float",
                "label": "Attribute weight",
                "description": "Share of a box's score from its attributes; the rest is IoU.",
                "default": 0.4,
                "min": 0,
                "max": 1,
            },
            "scored": {
                "type": "attributes",
                "label": "Scored attributes",
                "description": "Only these count toward a box's attribute score. All by default.",
                "default": None,
            },
            "critical": {
                "type": "attributes",
                "label": "Critical attributes",
                "description": "A wrong value zeroes the box.",
                "default": [],
            },
            "pass_threshold": {
                "type": "float",
                "label": "Pass score",
                "description": "Mean sample score needed to pass.",
                "default": 0.8,
                "min": 0,
                "max": 1,
            },
            "max_critical_misses": {
                "type": "int",
                "label": "Critical misses allowed",
                "description": "Per attempt.",
                "default": 0,
                "min": 0,
            },
        },
    }

    @property
    def config(self):
        return foo.OperatorConfig(
            name="boxes_with_attributes",
            label="Boxes + attributes scorer",
            unlisted=True,
        )

    def execute(self, ctx):
        request = ctx.params["request"]
        options = request["options"]
        if request["step"] == "verdict":
            return _verdict(options, request["samples"])
        specs = request["field"].get("attributes")
        if specs is not None and options.get("scored") is not None:
            keep = set(options["scored"])
            specs = [s for s in specs if s.get("name") in keep]
        return {
            "scores": {
                s["id"]: _score(options, specs, s) for s in request["samples"]
            }
        }


def _score(options, specs, sample):
    w = options["attribute_weight"]
    critical = set(options.get("critical") or [])
    res = pair_objects(
        label_from_dict(sample["a"]),
        label_from_dict(sample["b"]),
        min_iou=options["min_iou"],
    )
    matches = []
    misses = 0
    for m in res["matches"]:
        attrs = score_attributes(m["pred"], m["gold"], specs)
        wrong = {
            slot["name"]
            for slot in attrs["slots"]
            if slot.get("agree") == 0.0
        }
        if wrong & critical:
            misses += 1
            score = 0.0
        else:
            score = (1 - w) * m["iou"] + w * attrs["score"]
        matches.append(
            {
                "pred_id": m["pred_id"],
                "gold_id": m["gold_id"],
                "label": m["label"],
                "iou": round(m["iou"], 4),
                "score": score,
                "wrong": sorted(wrong),
            }
        )
    n = len(matches) + len(res["extra"]) + len(res["missed"])
    return {
        "score": sum(m["score"] for m in matches) / n if n else 1.0,
        "matches": matches,
        "extra": res["extra"],
        "missed": res["missed"],
        "detail": {"critical_misses": misses},
    }


def _verdict(options, samples):
    if not samples:
        return {"score": None, "passed": False, "summary": "Nothing scored"}
    mean = sum(s["score"] for s in samples) / len(samples)
    misses = sum(
        (s.get("detail") or {}).get("critical_misses", 0) for s in samples
    )
    return {
        "score": mean,
        "passed": mean >= options["pass_threshold"]
        and misses <= options["max_critical_misses"],
        "summary": f"{misses} critical attribute miss"
        + ("" if misses == 1 else "es"),
    }


EXAMPLE_SCORERS = (BoxesWithAttributes,)
