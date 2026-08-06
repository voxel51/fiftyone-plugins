"""
Demo delegated operators (DOs) used by the DO-dispatch example stages.

A workflow stage never does heavy/slow work inline — it submits a DO
(``fop.dos.submit``) and returns; the sample does NOT advance. When the
DO finishes it calls the platform trampoline
``@voxel51/workflows/workflow_do_completed`` with its own DO id, which
re-enters the stage's ``on_do_completed`` where routing happens.

Every DO here ends with :func:`notify_do_completed` in a ``finally`` —
that callback is the load-bearing "I'm done, resume the stage" signal.
It is pure ceremony and an obvious candidate to fold into a shipped SDK
(see the README's utility-library notes).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from fiftyone.operators.operator import Operator, OperatorConfig

log = logging.getLogger(__name__)

#: Platform trampoline that resumes a stage after its DO completes.
WORKFLOW_DO_COMPLETED_URI = "@voxel51/workflows/workflow_do_completed"


def notify_do_completed(
    ctx, *, success: bool, result: Optional[dict] = None
) -> None:
    """Tell the workflow runtime this DO finished, so the originating
    stage's ``on_do_completed`` fires.

    ``ctx.request_params["run_doc"]`` is the delegated op's own id, which
    equals the correlation id recorded by ``fop.dos.submit`` — that's how
    the runtime maps this completion back to the waiting stage.
    """
    from fiftyone.operators import execute_operator

    do_id = ctx.request_params.get("run_doc")
    if not do_id:
        # Not running as a tracked workflow DO (e.g. invoked directly) —
        # nothing to resume.
        return
    try:
        execute_operator(
            WORKFLOW_DO_COMPLETED_URI,
            ctx={
                "dataset": ctx.dataset_name,
                "dataset_id": ctx.dataset_id,
                "params": {"do_id": str(do_id), "success": success, "result": result},
                "user": ctx.user.to_dict() if ctx.user else None,
            },
            request_token=ctx.user_request_token,
            api_key=ctx.user_api_key,
        )
    except Exception:  # noqa: BLE001 - best-effort resume
        log.exception("workflow_do_completed notify failed", extra={"do_id": do_id})


def _sample_ids(ctx) -> list[str]:
    """Sample ids the stage stashed in the DO params at submit time."""
    return list((ctx.params.get("_wf") or {}).get("sample_ids") or [])


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

__all__ = ["EXAMPLE_DOS", "notify_do_completed", "WORKFLOW_DO_COMPLETED_URI"]
