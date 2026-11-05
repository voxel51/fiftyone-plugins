"""
Minimal contract layer for authoring workflow stages in an external
plugin.

A workflow stage is an ordinary :class:`fiftyone.operators.Operator`
whose ``execute`` dispatches over a ``hook`` param. The
``@voxel51/workflows`` plugin defines the canonical base
(``WorkflowStageOperator``) and the ``fop`` routing primitives, but a
**top-level** cross-plugin import of that base is load-order fragile
(this plugin may register before ``@voxel51/workflows`` does). So this
module ships a self-contained base that:

* needs **no** cross-plugin import at registration time — the stage
  classes below are safe to define regardless of plugin load order;
* is discovered by the canvas purely via its ``stage_descriptor``
  attribute (the editor's ``list_workflow_stages`` catalog is
  duck-typed);
* reaches the real ``fop`` routing primitives **lazily, at execute
  time**, when every plugin is guaranteed loaded (see :func:`fop`).

The ``execute`` dispatcher mirrors ``@voxel51/workflows``
``runtime/base.py`` — keep it in sync if that contract changes. (This
duplication is exactly the kind of thing a shipped SDK would remove;
see the utility-library notes in the README.)

This file is deliberately the ONLY place with framework ceremony. Each
example stage stays tiny and shows the raw ``fop`` calls.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import fiftyone.operators.types as types
from fiftyone.operators.operator import Operator, OperatorConfig

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Port + stage descriptors (shape-compatible with @voxel51/workflows)
# ---------------------------------------------------------------------------


class PortType(str, enum.Enum):
    """Wire type of a stage port. Matches the platform's values."""

    STREAM = "sample_stream"  # one sample at a time -> ``on_sample_received``
    COLLECTION = "sample_collection"  # a whole batch -> ``on_collection_received``


@dataclass(frozen=True)
class PortDescriptor:
    name: str
    type: PortType
    label: Optional[str] = None
    required: bool = True


@dataclass(frozen=True)
class StageDescriptor:
    """Static metadata the canvas palette reads to list + render a stage."""

    kind: str
    label: str
    description: str
    inputs: tuple[PortDescriptor, ...]
    outputs: tuple[PortDescriptor, ...]
    icon: Optional[str] = None
    #: Picker grouping; custom stages default to the "Custom" bucket.
    category: Optional[str] = None
    #: Seed config for a freshly-dropped node. When ``None`` the editor
    #: derives one from ``config_type`` dataclass defaults.
    default_config: Optional[dict] = field(default=None, hash=False)


def stage_operator_config(name: str, label: str, description: str) -> OperatorConfig:
    """OperatorConfig for a stage: ``unlisted`` (hidden from the operator
    browser) + ``dynamic`` (config form resolved per invocation)."""
    return OperatorConfig(
        name=name, label=label, description=description, unlisted=True, dynamic=True
    )


# ---------------------------------------------------------------------------
# Lazy handle to the platform's routing primitives
# ---------------------------------------------------------------------------


def fop():
    """The ``@voxel51/workflows`` ``fop`` module.

    Imported lazily so authoring a stage never depends on plugin load
    order — by the time any hook runs, every plugin is registered and
    this resolves. Raises a clear error if the workflows plugin is
    absent (a stage can't route without it).
    """
    from fiftyone.plugins.orgs.voxel51.workflows import fop as _fop

    return _fop


def wf_types():
    """The platform's ``fop.types`` (Stage, CollectionRef, Outcome, ...)."""
    from fiftyone.plugins.orgs.voxel51.workflows.fop import types as _t

    return _t


# ---------------------------------------------------------------------------
# Base stage operator (dispatcher mirrors @voxel51/workflows runtime/base.py)
# ---------------------------------------------------------------------------


class WorkflowStage(Operator):
    """Base for an example workflow stage.

    Subclasses set ``config_type`` + ``stage_descriptor`` and override the
    ``on_*`` hooks they need. Movement between stages is expressed by
    calling ``self.fop().workflows.route_sample(...)`` etc. — never by a
    return value.
    """

    config_type: type = type(None)
    stage_descriptor: StageDescriptor = StageDescriptor(
        kind="abstract",
        label="(abstract stage)",
        description="",
        inputs=(),
        outputs=(),
    )

    # convenience: sugar-free handles to the platform primitives
    def fop(self):
        return fop()

    # ---- overridable hooks (no-op defaults) ------------------------------

    def resolve_stage_config(self, ctx):
        return None

    def validate_stage_config(self, ctx, stage_config) -> list:
        return []

    def on_workflow_start(self, ctx, stage) -> None:
        return None

    def on_sample_received(
        self, ctx, stage, *, sample_id, stream=None, from_stage_id=None, from_port=None
    ) -> None:
        return None

    def on_collection_received(
        self,
        ctx,
        stage,
        *,
        collection_ref,
        stream=None,
        from_stage_id=None,
        from_port=None,
    ) -> None:
        return None

    def on_subtask_submitted(
        self, ctx, stage, *, subtask_id, outcome, payload=None
    ) -> None:
        return None

    def on_do_completed(self, ctx, stage, *, do_id, success, result=None) -> None:
        return None

    def report_progress(self, ctx, stage):
        return None

    # ---- dispatcher (do not override) ------------------------------------

    def _hydrate_stage(self, ctx):
        t = wf_types()
        raw = ctx.params["stage"]
        stage = t.from_dict(t.Stage, raw)
        cfg_data = raw.get("config", {}) or {}
        if self.config_type is not type(None):
            try:
                stage.config = t.from_dict(self.config_type, cfg_data)
            except TypeError:
                stage.config = cfg_data
        return stage

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("hook", required=False)
        inputs.obj("stage", required=False)
        return types.Property(inputs)

    def execute(self, ctx) -> dict[str, Any]:
        hook = ctx.params.get("hook")
        if hook is None:
            return {"ok": True}

        if hook == "resolve_stage_config":
            prop = self.resolve_stage_config(ctx)
            return {"property": prop.to_json() if prop is not None else None}

        if hook == "stage_descriptor":
            return {"descriptor": _serialize_descriptor(self.stage_descriptor)}

        if hook == "validate_stage_config":
            t = wf_types()
            raw_cfg = ctx.params.get("config", {}) or {}
            try:
                cfg = (
                    t.from_dict(self.config_type, raw_cfg)
                    if self.config_type is not type(None)
                    else raw_cfg
                )
            except TypeError as ex:
                return {"errors": [{"field": "*", "message": str(ex)}]}
            errors = self.validate_stage_config(ctx, cfg)
            return {"errors": [t.to_dict(e) for e in errors]}

        stage = self._hydrate_stage(ctx)

        if hook == "on_workflow_start":
            self.on_workflow_start(ctx, stage)
        elif hook == "on_sample_received":
            self.on_sample_received(
                ctx,
                stage,
                sample_id=ctx.params["sample_id"],
                stream=_maybe_stream(ctx.params.get("stream")),
                from_stage_id=ctx.params.get("from_stage_id"),
                from_port=ctx.params.get("from_port"),
            )
        elif hook == "on_collection_received":
            t = wf_types()
            self.on_collection_received(
                ctx,
                stage,
                collection_ref=t.from_dict(
                    t.CollectionRef, ctx.params["collection_ref"]
                ),
                stream=_maybe_stream(ctx.params.get("stream")),
                from_stage_id=ctx.params.get("from_stage_id"),
                from_port=ctx.params.get("from_port"),
            )
        elif hook == "on_subtask_submitted":
            t = wf_types()
            outcome_raw = ctx.params.get("outcome")
            self.on_subtask_submitted(
                ctx,
                stage,
                subtask_id=ctx.params["subtask_id"],
                outcome=t.Outcome(outcome_raw) if outcome_raw else None,
                payload=ctx.params.get("payload"),
            )
        elif hook == "on_do_completed":
            self.on_do_completed(
                ctx,
                stage,
                do_id=ctx.params["do_id"],
                success=bool(ctx.params.get("success", True)),
                result=ctx.params.get("result"),
            )
        elif hook == "report_progress":
            t = wf_types()
            progress = self.report_progress(ctx, stage)
            return {"progress": t.to_dict(progress) if progress is not None else None}
        else:
            return {"ok": False, "error": f"unhandled hook {hook}"}

        return {"ok": True}


def _maybe_stream(raw):
    if raw is None:
        return None
    t = wf_types()
    if isinstance(raw, t.SampleStream):
        return raw
    return t.from_dict(t.SampleStream, raw)


def _serialize_descriptor(desc: StageDescriptor) -> dict:
    return {
        "kind": desc.kind,
        "label": desc.label,
        "description": desc.description,
        "inputs": [_serialize_port(p) for p in desc.inputs],
        "outputs": [_serialize_port(p) for p in desc.outputs],
        "icon": desc.icon,
        "category": desc.category,
        "default_config": desc.default_config,
    }


def _serialize_port(p: PortDescriptor) -> dict:
    return {
        "name": p.name,
        "type": p.type.value,
        "label": p.label,
        "required": p.required,
    }


# Common port shorthands used across the examples.
def stream_in(name: str = "samples", label: str = "Samples") -> PortDescriptor:
    return PortDescriptor(name=name, type=PortType.STREAM, label=label)


def stream_out(name: str = "samples", label: str = "Samples") -> PortDescriptor:
    return PortDescriptor(name=name, type=PortType.STREAM, label=label)


def collection_in(
    name: str = "collection", label: str = "Collection"
) -> PortDescriptor:
    return PortDescriptor(name=name, type=PortType.COLLECTION, label=label)


def collection_out(
    name: str = "collection", label: str = "Collection"
) -> PortDescriptor:
    return PortDescriptor(name=name, type=PortType.COLLECTION, label=label)


__all__ = [
    "PortType",
    "PortDescriptor",
    "StageDescriptor",
    "WorkflowStage",
    "stage_operator_config",
    "fop",
    "wf_types",
    "stream_in",
    "stream_out",
    "collection_in",
    "collection_out",
]
