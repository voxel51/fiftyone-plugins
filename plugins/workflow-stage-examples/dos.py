"""
Demo delegated operators (DOs) used by the DO-dispatch example stages.

A workflow stage never does heavy/slow work inline — it submits a DO
(``fop.authoring.submit_do``) and returns; the sample does NOT advance.
When the DO finishes it calls the platform trampoline (via
``fop.authoring.notify_do_completed``) with its own DO id, which re-enters
the stage's ``on_do_completed`` where routing happens.

Every DO here ends with ``notify_do_completed`` in a ``finally`` — that
callback is the load-bearing "I'm done, resume the stage" signal. It (and
the submit/resume stash) now live in the platform's ``fop.authoring``
helpers, reached lazily so this plugin never needs a load-order-fragile
top-level import of ``@voxel51/workflows``.
"""

from __future__ import annotations

import logging
import time

from fiftyone.operators.operator import Operator, OperatorConfig

log = logging.getLogger(__name__)


def _authoring():
    """Lazy handle to the platform's ``fop.authoring`` helpers."""
    from fiftyone.plugins.orgs.voxel51.workflows import fop

    return fop.authoring


def notify_do_completed(ctx, *, success, result=None):
    """Resume the originating stage — delegates to ``fop.authoring``."""
    _authoring().notify_do_completed(ctx, success=success, result=result)


def _sample_ids(ctx) -> list:
    """Sample ids to operate on, recovered from the submit-time stash.

    ``fop.authoring.submit_do`` stashes the routing context under the
    reserved ``_wf`` key: a serialized ``collection_ref`` (batch DOs) or a
    lone ``sample_id`` (per-sample DOs). Accept either shape.
    """
    wf = ctx.params.get("_wf") or {}
    ref = wf.get("collection_ref") or {}
    ids = ref.get("sample_ids") or wf.get("sample_ids")
    if ids:
        return list(ids)
    sid = wf.get("sample_id")
    return [sid] if sid else []


class ExampleSleepDO(Operator):
    """Sleep ``seconds`` then complete — stands in for slow async work."""

    @property
    def config(self):
        return OperatorConfig(
            name="example_sleep_do",
            label="Example: sleep DO",
            description="Sleeps, then resumes the waiting stage.",
            unlisted=True,
            allow_delegated_execution=True,
        )

    def execute(self, ctx):
        success, result = False, None
        try:
            seconds = float(ctx.params.get("seconds", 2))
            time.sleep(max(0.0, min(seconds, 30.0)))
            result = {"slept": seconds}
            success = True
            return result
        finally:
            notify_do_completed(ctx, success=success, result=result)


class ExampleComputeMetadataDO(Operator):
    """Compute metadata on the staged samples (real, cheap dataset work)."""

    @property
    def config(self):
        return OperatorConfig(
            name="example_compute_metadata_do",
            label="Example: compute metadata DO",
            description="Runs compute_metadata on the staged samples.",
            unlisted=True,
            allow_delegated_execution=True,
        )

    def execute(self, ctx):
        success, result = False, None
        try:
            ids = _sample_ids(ctx)
            view = ctx.dataset.select(ids) if ids else ctx.dataset
            view.compute_metadata()
            result = {"count": len(ids) if ids else len(ctx.dataset)}
            success = True
            return result
        finally:
            notify_do_completed(ctx, success=success, result=result)


class ExampleScoreDO(Operator):
    """Write a demo float score onto each staged sample and return the mean.

    A real stage would call a model / brain method here; the shape of the
    round-trip (ids in, a summary result out) is what matters.
    """

    @property
    def config(self):
        return OperatorConfig(
            name="example_score_do",
            label="Example: score DO",
            description="Writes a demo score field on the staged samples.",
            unlisted=True,
            allow_delegated_execution=True,
        )

    def execute(self, ctx):
        success, result = False, None
        try:
            import random

            field = str(ctx.params.get("field", "demo_score"))
            ids = _sample_ids(ctx)
            view = ctx.dataset.select(ids) if ids else ctx.dataset
            scores = []
            for sample in view:
                s = round(random.random(), 4)
                sample[field] = s
                sample.save()
                scores.append(s)
            mean = round(sum(scores) / len(scores), 4) if scores else 0.0
            result = {"field": field, "count": len(scores), "mean_score": mean}
            success = True
            return result
        finally:
            notify_do_completed(ctx, success=success, result=result)


EXAMPLE_DOS = [ExampleSleepDO, ExampleComputeMetadataDO, ExampleScoreDO]

__all__ = ["EXAMPLE_DOS", "notify_do_completed"]
