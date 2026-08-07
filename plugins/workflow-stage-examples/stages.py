"""
Ten example workflow stages, from "hello world" to a DO+HITL capstone.

Each stage subclasses :class:`WorkflowStage` (see ``_sdk.py``), declares
a ``stage_descriptor`` (so the canvas discovers + renders it), and
overrides the hook(s) it needs. Movement between stages is always a
``fop.workflows.route_sample`` / ``route_collection`` / ``finalize_*``
call — never a return value.

Read them top to bottom: the ceremony grows one concept at a time.

| Copyright 2017-2026, Voxel51, Inc.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import field as dc_field

import fiftyone.operators.types as types

from ._sdk import (
    StageDescriptor,
    WorkflowStage,
    collection_in,
    collection_out,
    stage_operator_config,
    stream_in,
    stream_out,
)

log = logging.getLogger(__name__)

PLUGIN = "@voxel51/workflow-stage-examples"

# DO operator URIs (defined in dos.py, registered under this plugin).
SLEEP_DO = f"{PLUGIN}/example_sleep_do"
COMPUTE_METADATA_DO = f"{PLUGIN}/example_compute_metadata_do"
SCORE_DO = f"{PLUGIN}/example_score_do"


# ===========================================================================
# 1. Hello world — a pass-through stream stage
# ===========================================================================


@dataclass(frozen=True)
class _NoConfig:
    pass


class HelloWorldStage(WorkflowStage):
    """The smallest possible stage: forward every sample downstream."""

    config_type = _NoConfig
    stage_descriptor = StageDescriptor(
        kind="example_hello_world",
        label="Hello world",
        description="Forwards each sample downstream, untouched.",
        inputs=(stream_in(),),
        outputs=(stream_out(),),
        icon="WavingHand",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_hello_world", "Hello world", "Pass-through stage."
        )

    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        # One call is the whole stage: send this sample out the "samples"
        # port to whatever is wired downstream.
        self.fop().workflows.route_sample(
            ctx, from_stage=stage, sample_id=sample_id, port="samples", stream=stream
        )


# ===========================================================================
# 2. Log message — first taste of a config form
# ===========================================================================


@dataclass(frozen=True)
class _LogConfig:
    message: str = "sample passed through"


class LogMessageStage(WorkflowStage):
    """Log a configurable message for each sample, then forward it."""

    config_type = _LogConfig
    stage_descriptor = StageDescriptor(
        kind="example_log_message",
        label="Log message",
        description="Logs a configurable message per sample, then forwards it.",
        inputs=(stream_in(),),
        outputs=(stream_out(),),
        icon="Notes",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_log_message", "Log message", "Logs a message per sample."
        )

    def resolve_stage_config(self, ctx):
        # Field names here MUST match ``_LogConfig`` so the persisted
        # config round-trips back into the dataclass.
        inputs = types.Object()
        inputs.str("message", label="Message", default="sample passed through")
        return types.Property(inputs)

    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        log.info("[example] %s (%s)", stage.config.message, sample_id)
        self.fop().workflows.route_sample(
            ctx, from_stage=stage, sample_id=sample_id, port="samples", stream=stream
        )


# ===========================================================================
# 3. Tag samples — a COLLECTION stage doing light inline dataset work
# ===========================================================================


@dataclass(frozen=True)
class _TagConfig:
    tag: str = "reviewed"


class TagSamplesStage(WorkflowStage):
    """Add a tag to a whole incoming collection, then forward it."""

    config_type = _TagConfig
    stage_descriptor = StageDescriptor(
        kind="example_tag_samples",
        label="Tag samples",
        description="Adds a configurable tag to the collection, then forwards it.",
        inputs=(collection_in(),),
        outputs=(collection_out(),),
        icon="Sell",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_tag_samples", "Tag samples", "Tags an incoming collection."
        )

    def resolve_stage_config(self, ctx):
        inputs = types.Object()
        inputs.str("tag", label="Tag", default="reviewed", required=True)
        return types.Property(inputs)

    def on_collection_received(self, ctx, stage, *, collection_ref, **_):
        # Light, fast mutation is fine inline; heavy work belongs in a DO
        # (see stages 5-7). Rebuild the view from the ref's ids and tag.
        ids = list(collection_ref.sample_ids or [])
        if ids:
            ctx.dataset.select(ids).tag_samples(stage.config.tag)
        self.fop().workflows.route_collection(
            ctx, from_stage=stage, collection_ref=collection_ref, port="collection"
        )


# ===========================================================================
# 4. Coin-flip router — a stage with TWO output ports
# ===========================================================================


class CoinFlipRouterStage(WorkflowStage):
    """Route each sample to ``heads`` or ``tails`` (deterministic by id)."""

    config_type = _NoConfig
    stage_descriptor = StageDescriptor(
        kind="example_coin_flip",
        label="Coin-flip router",
        description="Deterministically splits samples across two output ports.",
        inputs=(stream_in(),),
        outputs=(
            stream_out("heads", "Heads"),
            stream_out("tails", "Tails"),
        ),
        icon="CallSplit",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_coin_flip", "Coin-flip router", "Splits samples two ways."
        )

    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        # Choosing the output port is ordinary Python — the port name must
        # match one of this stage's declared ``outputs``.
        port = "heads" if hash(sample_id) % 2 == 0 else "tails"
        self.fop().workflows.route_sample(
            ctx, from_stage=stage, sample_id=sample_id, port=port, stream=stream
        )


# ===========================================================================
# 5. Delay — dispatch a DO and WAIT before advancing (per-sample)
# ===========================================================================


@dataclass(frozen=True)
class _DelayConfig:
    seconds: float = 2.0


class DelayStage(WorkflowStage):
    """Submit a sleep DO per sample; advance only when the DO completes."""

    config_type = _DelayConfig
    stage_descriptor = StageDescriptor(
        kind="example_delay",
        label="Delay (DO)",
        description="Waits on a delegated operation per sample before forwarding.",
        inputs=(stream_in(),),
        outputs=(stream_out(),),
        icon="Timer",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_delay", "Delay (DO)", "Waits on a DO per sample."
        )

    def resolve_stage_config(self, ctx):
        inputs = types.Object()
        inputs.float("seconds", label="Delay (seconds)", default=2.0)
        return types.Property(inputs)

    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        # Fire-and-forget: we do NOT route here. submit_do stashes the
        # sample_id in the DO's correlation; the sample stays in-flight
        # (termination gated on the DO) until on_do_completed routes it.
        self.fop().authoring.submit_do(
            ctx,
            stage,
            SLEEP_DO,
            sample_id=sample_id,
            params={"seconds": stage.config.seconds},
            label=f"Delay {stage.config.seconds}s",
        )

    def on_do_completed(self, ctx, stage, *, do_id, success, result=None):
        # resume_do recovers what submit_do stashed (here, the sample_id).
        r = self.fop().authoring.resume_do(ctx, do_id)
        if r.sample_id is None:
            return
        self.fop().workflows.route_sample(
            ctx, from_stage=stage, sample_id=r.sample_id, port="samples"
        )


# ===========================================================================
# 6. Compute metadata — collection-level DO wait
# ===========================================================================


class ComputeMetadataStage(WorkflowStage):
    """Run compute_metadata on the collection via a DO, then forward it."""

    config_type = _NoConfig
    stage_descriptor = StageDescriptor(
        kind="example_compute_metadata",
        label="Compute metadata (DO)",
        description="Delegates compute_metadata on the collection, then forwards it.",
        inputs=(collection_in(),),
        outputs=(collection_out(),),
        icon="Memory",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_compute_metadata",
            "Compute metadata (DO)",
            "Delegates compute_metadata.",
        )

    def on_collection_received(self, ctx, stage, *, collection_ref, **_):
        # submit_do serializes + stashes the whole collection_ref for us;
        # the DO reads its sample ids back out of that stash.
        self.fop().authoring.submit_do(
            ctx,
            stage,
            COMPUTE_METADATA_DO,
            collection_ref=collection_ref,
            label="Compute metadata",
        )

    def on_do_completed(self, ctx, stage, *, do_id, success, result=None):
        r = self.fop().authoring.resume_do(ctx, do_id)
        if r.collection_ref is None:
            return
        self.fop().workflows.route_collection(
            ctx, from_stage=stage, collection_ref=r.collection_ref, port="collection"
        )


# ===========================================================================
# 7. Score samples — DO that writes a field, result surfaced in on_do_completed
# ===========================================================================


@dataclass(frozen=True)
class _ScoreConfig:
    field: str = "demo_score"


class ScoreSamplesStage(WorkflowStage):
    """Delegate a scoring pass that writes a field, then forward the batch."""

    config_type = _ScoreConfig
    stage_descriptor = StageDescriptor(
        kind="example_score",
        label="Score samples (DO)",
        description="Delegates a scoring pass that writes a field, then forwards.",
        inputs=(collection_in(),),
        outputs=(collection_out(),),
        icon="Functions",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_score", "Score samples (DO)", "Delegates a scoring pass."
        )

    def resolve_stage_config(self, ctx):
        inputs = types.Object()
        inputs.str("field", label="Score field", default="demo_score", required=True)
        return types.Property(inputs)

    def on_collection_received(self, ctx, stage, *, collection_ref, **_):
        # Non-stash params (here, the score field) pass straight through to
        # the DO; the collection_ref rides the stash for routing on resume.
        self.fop().authoring.submit_do(
            ctx,
            stage,
            SCORE_DO,
            collection_ref=collection_ref,
            params={"field": stage.config.field},
            label=f"Score -> {stage.config.field}",
        )

    def on_do_completed(self, ctx, stage, *, do_id, success, result=None):
        if result:
            log.info("[example] scored: %s", result)
        r = self.fop().authoring.resume_do(ctx, do_id)
        if r.collection_ref is None:
            return
        self.fop().workflows.route_collection(
            ctx, from_stage=stage, collection_ref=r.collection_ref, port="collection"
        )


# ===========================================================================
# 8. Click to advance — simple HITL: a human releases each sample
# ===========================================================================


@dataclass(frozen=True)
class _ClickConfig:
    reviewers: list = dc_field(default_factory=list)


class ClickToAdvanceStage(WorkflowStage):
    """Open a SubTask per sample; a human click (see the Release panel, or
    the built-in task Submit button) advances it downstream."""

    config_type = _ClickConfig
    stage_descriptor = StageDescriptor(
        kind="example_click_to_advance",
        label="Click to advance",
        description="Holds each sample until a human clicks to release it.",
        inputs=(stream_in(),),
        outputs=(stream_out(),),
        icon="TouchApp",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_click_to_advance",
            "Click to advance",
            "Human clicks to release each sample.",
        )

    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        if stream is None or stream.source_collection is None:
            raise ValueError("stream edge delivered a sample without a stream")
        # open_review parks the sample on a human (find/create task + open
        # subtask). No routing here — it waits until the human submits.
        self.fop().authoring.open_review(
            ctx,
            stage,
            sample_id=sample_id,
            source_collection=stream.source_collection,
            assignees=stage.config.reviewers,
            label=f"Release ({stage.name})",
        )

    def on_subtask_submitted(self, ctx, stage, *, subtask_id, outcome, payload=None):
        # close_review does transition + reconcile, and drops-on-skip
        # (returning None); otherwise we just route the released sample.
        r = self.fop().authoring.close_review(ctx, stage, subtask_id, outcome)
        if r is None:
            return
        self.fop().workflows.route_sample(
            ctx,
            from_stage=stage,
            sample_id=r.sample_id,
            port="samples",
            source_collection=r.source_collection,
        )


# ===========================================================================
# 9. Approve / reject — HITL with two outcome-driven ports
# ===========================================================================


@dataclass(frozen=True)
class _ApproveConfig:
    reviewers: list = dc_field(default_factory=list)


class ApproveRejectStage(WorkflowStage):
    """HITL gate: accept -> ``approved`` port, reject -> ``rejected`` port."""

    config_type = _ApproveConfig
    stage_descriptor = StageDescriptor(
        kind="example_approve_reject",
        label="Approve / reject",
        description="Human accept/reject routes to two different output ports.",
        inputs=(stream_in(),),
        outputs=(
            stream_out("approved", "Approved"),
            stream_out("rejected", "Rejected"),
        ),
        icon="Rule",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_approve_reject",
            "Approve / reject",
            "Human accept/reject gate.",
        )

    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        if stream is None or stream.source_collection is None:
            raise ValueError("stream edge delivered a sample without a stream")
        self.fop().authoring.open_review(
            ctx,
            stage,
            sample_id=sample_id,
            source_collection=stream.source_collection,
            assignees=stage.config.reviewers,
            label=f"Approve/reject ({stage.name})",
        )

    def on_subtask_submitted(self, ctx, stage, *, subtask_id, outcome, payload=None):
        r = self.fop().authoring.close_review(ctx, stage, subtask_id, outcome)
        if r is None:  # skipped + dropped
            return
        # ReviewResult.rejected/accepted read the outcome for us.
        self.fop().workflows.route_sample(
            ctx,
            from_stage=stage,
            sample_id=r.sample_id,
            port="rejected" if r.rejected else "approved",
            source_collection=r.source_collection,
        )


# ===========================================================================
# 10. Score-then-review — capstone: DO + conditional HITL + multi-port
# ===========================================================================


@dataclass(frozen=True)
class _ScoreThenReviewConfig:
    field: str = "demo_score"
    threshold: float = 0.5
    reviewers: list = dc_field(default_factory=list)


class ScoreThenReviewStage(WorkflowStage):
    """Score each sample via a DO; auto-pass high scores, send low scores to
    a human. Combines DO-wait, conditional logic, HITL, and two ports."""

    config_type = _ScoreThenReviewConfig
    stage_descriptor = StageDescriptor(
        kind="example_score_then_review",
        label="Score, then review",
        description=(
            "Scores each sample (DO); high scores auto-advance, low scores go "
            "to a human, whose accept/reject picks the output port."
        ),
        inputs=(stream_in(),),
        outputs=(
            stream_out("passed", "Auto-passed"),
            stream_out("approved", "Approved"),
            stream_out("rejected", "Rejected"),
        ),
        icon="AutoAwesome",
        category="Examples",
    )

    @property
    def config(self):
        return stage_operator_config(
            "example_score_then_review",
            "Score, then review",
            "DO scoring gated by a human for low scores.",
        )

    def resolve_stage_config(self, ctx):
        inputs = types.Object()
        inputs.str("field", label="Score field", default="demo_score")
        inputs.float("threshold", label="Auto-pass at/above", default=0.5)
        return types.Property(inputs)

    # -- step 1: score each sample via a DO ---------------------------------
    def on_sample_received(self, ctx, stage, *, sample_id, stream=None, **_):
        # Stash the source collection alongside the sample so step 2 can
        # route (auto-pass) or open a review carrying it.
        self.fop().authoring.submit_do(
            ctx,
            stage,
            SCORE_DO,
            sample_id=sample_id,
            source_collection=stream.source_collection if stream else None,
            params={"field": stage.config.field},
            label=f"Score {sample_id}",
        )

    # -- step 2: DO done -> auto-pass or open a review subtask --------------
    def on_do_completed(self, ctx, stage, *, do_id, success, result=None):
        fop = self.fop()
        r = fop.authoring.resume_do(ctx, do_id)
        if r.sample_id is None:
            return
        score = self._read_score(ctx, r.sample_id, stage.config.field)
        if score >= stage.config.threshold:
            # High score: skip the human entirely.
            fop.workflows.route_sample(
                ctx,
                from_stage=stage,
                sample_id=r.sample_id,
                port="passed",
                source_collection=r.source_collection,
            )
            return
        # Low score: hold for a human (accept/reject decides the port).
        fop.authoring.open_review(
            ctx,
            stage,
            sample_id=r.sample_id,
            source_collection=r.source_collection,
            assignees=stage.config.reviewers,
            label=f"Review low score ({stage.name})",
            payload={"score": score},
        )

    # -- step 3: human decision -> approved / rejected ----------------------
    def on_subtask_submitted(self, ctx, stage, *, subtask_id, outcome, payload=None):
        r = self.fop().authoring.close_review(ctx, stage, subtask_id, outcome)
        if r is None:
            return
        self.fop().workflows.route_sample(
            ctx,
            from_stage=stage,
            sample_id=r.sample_id,
            port="rejected" if r.rejected else "approved",
            source_collection=r.source_collection,
        )

    @staticmethod
    def _read_score(ctx, sample_id, field) -> float:
        try:
            return float(ctx.dataset[sample_id][field] or 0.0)
        except Exception:  # noqa: BLE001 - missing field -> treat as low
            return 0.0


EXAMPLE_STAGES = [
    HelloWorldStage,
    LogMessageStage,
    TagSamplesStage,
    CoinFlipRouterStage,
    DelayStage,
    ComputeMetadataStage,
    ScoreSamplesStage,
    ClickToAdvanceStage,
    ApproveRejectStage,
    ScoreThenReviewStage,
]

__all__ = ["EXAMPLE_STAGES"]
