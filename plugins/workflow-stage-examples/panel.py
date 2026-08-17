"""
A custom Human-in-the-Loop panel: "Release samples".

The HITL example stages (``example_click_to_advance``,
``example_approve_reject``, ``example_score_then_review``) park a sample
by opening a SubTask and *not* routing. Something has to close that
SubTask to let the sample continue. That "something" is a human click —
and this panel is where the click lives.

It shows how many samples are waiting, names the next one, and offers
**Release** / **Reject** / **Skip** buttons. Each button just executes
the platform operator ``@voxel51/workflows/workflow_next`` with an
``outcome`` — exactly what the built-in task UI does, wrapped in a panel
you fully control. Point being: the release mechanism is a plain
operator call, so any custom surface (a panel, a dashboard button, an
external tool) can drive a HITL stage.

Note: it queries OPEN SubTasks for the current dataset directly — fine
for a demo. A production panel would scope to the viewer's task inbox.

| Copyright 2017-2026, Voxel51, Inc.
"""

from __future__ import annotations

import logging

import fiftyone.operators as foo
import fiftyone.operators.types as types

log = logging.getLogger(__name__)

WORKFLOW_NEXT_URI = "@voxel51/workflows/workflow_next"


def _wf():
    """Lazy handles to the platform's subtask store + types."""
    from fiftyone.plugins.orgs.voxel51.workflows.fop import subtasks, types as t

    return subtasks, t


def _open_subtasks(ctx):
    """OPEN SubTasks for the current dataset, oldest first.

    Uses the store's collection directly (demo scope); a production panel
    would call the platform's assigned-work query for the viewer.
    """
    subtasks, t = _wf()
    ds = subtasks._scope(ctx=ctx)
    docs = subtasks._coll().find(
        {"dataset_id": ds, "state": t.SubTaskState.OPEN.value}, sort=False
    )
    subs = [s for s in (subtasks._from_doc(d) for d in docs) if s is not None]
    subs.sort(key=lambda s: s.created_at)
    return subs


class ReleaseSamplesPanel(foo.Panel):
    """Click-to-advance UI for the HITL example stages."""

    @property
    def config(self):
        return foo.PanelConfig(
            name="example_release_panel",
            label="Workflow: Release samples",
            icon="TouchApp",
        )

    def on_load(self, ctx):
        self._refresh(ctx)

    def refresh(self, ctx):
        self._refresh(ctx)

    def _refresh(self, ctx):
        subs = _open_subtasks(ctx)
        ctx.panel.state.count = len(subs)
        head = subs[0] if subs else None
        ctx.panel.state.next_subtask_id = head.id if head else None
        ctx.panel.state.next_sample_id = (head.sample_id if head else None) or "—"

    # -- button handlers: each is one workflow_next call -------------------

    def _submit(self, ctx, outcome):
        subtask_id = ctx.panel.state.next_subtask_id
        if not subtask_id:
            ctx.ops.notify("Nothing waiting.")
            return
        ctx.trigger(
            WORKFLOW_NEXT_URI,
            params={"subtask_id": subtask_id, "outcome": outcome},
        )
        ctx.ops.notify(f"{outcome} -> sample released")
        self._refresh(ctx)

    def release(self, ctx):
        self._submit(ctx, "accept")

    def reject(self, ctx):
        self._submit(ctx, "reject")

    def skip(self, ctx):
        self._submit(ctx, "skip")

    def render(self, ctx):
        panel = types.Object()

        count = ctx.panel.state.count or 0
        if count == 0:
            panel.md(
                "### 🎉 Nothing waiting\n\n"
                "No samples are parked in a HITL stage right now. Run a "
                "workflow that uses **Click to advance**, **Approve / "
                "reject**, or **Score, then review** and they'll queue here.",
                name="empty",
            )
            menu = panel.menu("actions", variant="square")
            menu.btn("refresh", icon="Refresh", label="Refresh", on_click=self.refresh)
            return types.Property(panel, view=types.GridView(width=100))

        panel.md(
            f"### {count} sample(s) waiting\n\n"
            f"**Next:** `{ctx.panel.state.next_sample_id}`\n\n"
            "Release it downstream, reject it, or skip (drop) it.",
            name="summary",
        )
        menu = panel.menu("actions", variant="square")
        menu.btn("release", icon="CheckCircle", label="Release", on_click=self.release)
        menu.btn("reject", icon="Cancel", label="Reject", on_click=self.reject)
        menu.btn("skip", icon="Block", label="Skip", on_click=self.skip)
        menu.btn("refresh", icon="Refresh", label="Refresh", on_click=self.refresh)
        return types.Property(panel, view=types.GridView(width=100))


EXAMPLE_PANELS = [ReleaseSamplesPanel]

__all__ = ["EXAMPLE_PANELS"]
