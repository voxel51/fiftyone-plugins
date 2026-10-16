"""
An example assignment policy: tasks to labelers at the desired first-pass
approval rate, then to those at the minimum, with a cap of open tasks per
person.

An assignment policy is an ordinary FiftyOne operator with one extra class
attribute, ``assignment_policy_descriptor``. The workflow runtime finds it
by that attribute, offers it in the stage's **Assignment policy** dropdown,
and calls it whenever a stage on automatic assignment has unassigned
batches: after every wave of samples, after a pool edit, or when a manager
presses **Auto-assign now**.

The policy only answers *who holds what*. Everything else is the
runtime's: it decides when to run, resolves the pool and each person's
load, validates every answer against the pool, writes it with a
compare-and-swap (a claim that landed first wins) and emits the activity
event. A policy therefore needs no database access and no FiftyOne
internals; it is a pure function of the request it is handed.

The request arrives as ``ctx.params["request"]``::

    {
      "stage":   {"workflow_id", "stage_id", "kind", "name", "pool",
                  "priority", "batching", "options"},
      "tasks":   [{"id", "batch_index", "sample_total", "open_samples",
                   "priority", "assigned_to", "assigned_by", "created_at",
                   "source_collection", "sample_ids"}, ...],
      "pending": [{"task_id", "reason"}, ...],
      "assignee_pool": {
        "users":  [{"id", "name", "open_tasks", "open_samples",
                    "last_submit_at", "via_groups",
                    "first_pass_approval"?, "first_pass_judged"?}, ...],
        "groups": [{"id", "name", "member_ids", "open_tasks"}, ...]
      },
      "triggered_by": "system" | "<user id>"
    }

and the policy returns::

    {
      "assignments": [{"task_id", "assignees": [...], "note"?}, ...],
      "priorities":  {"<task_id>": 0..10},           # optional
      "fallthrough": "default" | "none"              # optional
    }

``assignees`` are principals from the pool: user ids and/or ``group:<id>``.
One person, several people, one or more groups, or ``[]`` to leave the
batch unassigned are all valid. Batches the policy does not answer for are
handed to the built-in least-loaded policy unless the result says
``"fallthrough": "none"``.

| Copyright 2017-2026, Voxel51, Inc.
"""

from __future__ import annotations

import fiftyone.operators as foo
import fiftyone.operators.types as types


def _request(ctx) -> dict:
    return (ctx.params or {}).get("request") or {}


def _pending_tasks(request: dict) -> list[dict]:
    """The pending Tasks as full rows, lowest batch index first."""
    by_id = {t["id"]: t for t in request.get("tasks") or []}
    rows = [
        by_id[p["task_id"]]
        for p in request.get("pending") or []
        if p.get("task_id") in by_id
    ]
    return sorted(rows, key=lambda t: int(t.get("batch_index") or 0))


class _PolicyBase(foo.Operator):
    """Shared ceremony: an unlisted, dynamic operator that takes ``request``."""

    #: Subclasses set these.
    NAME = ""
    LABEL = ""

    @property
    def config(self):
        return foo.OperatorConfig(
            name=self.NAME, label=self.LABEL, unlisted=True, dynamic=True
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.obj("request", required=True)
        return types.Property(inputs)


# ---------------------------------------------------------------------------
# Quality-aware: labelers at the desired first-pass approval rate first,
# then those at the minimum, with a cap of open tasks per person
# ---------------------------------------------------------------------------


class AssignByApprovalRate(_PolicyBase):
    """Two tiers by first-pass approval rate, and a cap per person.

    Options (``request.stage.options``; each stage sets its own, the form
    shows them under the policy)::

        {
          "desired_approval_rate": 90,   # %, first choice
          "min_approval_rate": 30,       # %, used once the first tier is full
          "max_open_tasks": 10           # open tasks per person, anywhere
        }

    **Where the rate comes from.** The descriptor asks for
    ``first_pass_approval`` in ``request_fields``, so the runtime adds each
    person's first-pass approval rate (0..1, from the Activity metrics:
    of their samples judged on the first pass, the share approved) and how
    many were judged. People with nothing judged yet arrive with ``None``.

    Decisions, in order:

    1. Pending tasks are taken highest priority first (then lowest batch
       index), so the tasks that matter most get the best people.
    2. A person is eligible while their open tasks (held anywhere, plus the
       ones picked earlier in this run) are under the cap.
    3. The task goes to an eligible person at or above the desired rate.
    4. When nobody at the desired rate is under the cap, it goes to an
       eligible person at or above the minimum. People with no judged work
       yet count as meeting the minimum, so new labelers can build a record.
    5. Within a tier: fewest open tasks first, then the higher rate.
    6. When nobody qualifies, the task is left unassigned on purpose
       (``assignees: []``); ``"fallthrough": "none"`` keeps the default
       policy from handing it out anyway. It stays in the pool for anyone
       allowed to claim it.
    """

    NAME = "example_assign_by_approval_rate"
    LABEL = "Example: by approval rate"

    assignment_policy_descriptor = {
        "label": "By approval rate, capped (example)",
        "description": (
            "Labelers at the desired first-pass approval rate first, then "
            "those at the minimum; nobody above the cap. A task nobody "
            "qualifies for stays unassigned."
        ),
        "request_fields": ["first_pass_approval"],
        "options": {
            "desired_approval_rate": {
                "type": "float",
                "label": "Desired first-pass approval rate",
                "description": "Tried first.",
                "unit": "%",
                "default": 90,
                "min": 0,
                "max": 100,
            },
            "min_approval_rate": {
                "type": "float",
                "label": "Min first-pass approval rate",
                "description": "Used once everyone at the desired rate is full.",
                "unit": "%",
                "default": 30,
                "min": 0,
                "max": 100,
            },
            "max_open_tasks": {
                "type": "int",
                "label": "Max open tasks per person",
                "default": 10,
                "min": 1,
            },
        },
    }

    def execute(self, ctx):
        request = _request(ctx)
        options = request["stage"].get("options") or {}
        desired = _float(options.get("desired_approval_rate"), 90.0) / 100
        minimum = _float(options.get("min_approval_rate"), 30.0) / 100
        cap = _int(options.get("max_open_tasks"), 10)

        people = request["assignee_pool"].get("users") or []
        open_count = {u["id"]: int(u.get("open_tasks") or 0) for u in people}
        rate = {u["id"]: u.get("first_pass_approval") for u in people}

        def desired_tier(uid):
            return rate[uid] is not None and rate[uid] >= desired

        def minimum_tier(uid):
            return rate[uid] is None or rate[uid] >= minimum

        def pick(candidates):
            return min(
                candidates,
                key=lambda u: (open_count[u], -(rate[u] or 0.0), u),
            )

        pending = sorted(
            _pending_tasks(request),
            key=lambda t: (
                -int(t.get("priority") or 0),
                int(t.get("batch_index") or 0),
            ),
        )
        out = []
        for task in pending:
            free = [u for u in open_count if open_count[u] < cap]
            first = [u for u in free if desired_tier(u)]
            second = [u for u in free if minimum_tier(u)]
            if first:
                who, note = pick(first), "desired rate"
            elif second:
                who, note = pick(second), "minimum rate"
            else:
                out.append(
                    {
                        "task_id": task["id"],
                        "assignees": [],
                        "note": (
                            "nobody under the cap"
                            if not free
                            else "nobody meets the minimum rate"
                        ),
                    }
                )
                continue
            open_count[who] += 1
            if rate[who] is not None:
                note += f" ({rate[who]:.0%})"
            else:
                note += " (no history)"
            out.append(
                {"task_id": task["id"], "assignees": [who], "note": note}
            )
        return {"assignments": out, "fallthrough": "none"}


def _int(value, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _float(value, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


EXAMPLE_POLICIES = (AssignByApprovalRate,)
