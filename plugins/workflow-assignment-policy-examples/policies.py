"""
Four example assignment policies.

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
                    "last_submit_at", "via_groups"}, ...],
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
# 1. The smallest policy: round robin over the pool's people
# ---------------------------------------------------------------------------


class AssignRoundRobin(_PolicyBase):
    """Batch ``i`` goes to person ``i % len(people)``.

    The minimum a policy can be. ``assignee_pool.users`` already contains
    every person in the pool, group members included, so "the pool's
    people" is one list. Returning ``"fallthrough": "none"`` says this
    policy answered for everything; with no people in the pool nothing is
    assigned and the batches stay claimable.
    """

    NAME = "example_assign_round_robin"
    LABEL = "Example: round robin"

    assignment_policy_descriptor = {
        "label": "Round robin (example)",
        "description": "Batch i goes to the i-th person in the pool, wrapping around.",
    }

    def execute(self, ctx):
        request = _request(ctx)
        people = [u["id"] for u in request["assignee_pool"].get("users") or []]
        if not people:
            return {"assignments": [], "fallthrough": "none"}
        out = []
        for task in _pending_tasks(request):
            who = people[int(task.get("batch_index") or 0) % len(people)]
            out.append(
                {
                    "task_id": task["id"],
                    "assignees": [who],
                    "note": "round robin",
                }
            )
        return {"assignments": out, "fallthrough": "none"}


# ---------------------------------------------------------------------------
# 2. Routing by a sample field, with fall-through
# ---------------------------------------------------------------------------


class AssignBySampleField(_PolicyBase):
    """Batches whose samples carry a known value of ``field`` go to the
    principal mapped to that value; everything else falls through to the
    built-in least-loaded policy.

    The customer story behind it: camera X's footage goes to the team that
    owns camera X. Options come from the stage config
    (``request.stage.options``)::

        {"field": "camera", "routes": {"cam_a": "group:<team a id>",
                                        "cam_b": "<user id>"}}

    The request carries each batch's ``sample_ids`` and nothing about the
    samples themselves, so the policy loads the one field it needs through
    ``ctx.dataset``. A route to a principal that is not in the pool is
    ignored (the runtime would refuse it anyway), so a stale mapping can
    never widen access.
    """

    NAME = "example_assign_by_sample_field"
    LABEL = "Example: by sample field"

    assignment_policy_descriptor = {
        "label": "By sample field (example)",
        "description": (
            "Route each batch to the principal mapped to its samples' value "
            "of a field (e.g. camera -> team); the rest go least-loaded."
        ),
        "options": {
            "field": {"type": "str", "label": "Sample field"},
            "routes": {"type": "dict", "label": "value -> principal"},
        },
    }

    def execute(self, ctx):
        request = _request(ctx)
        options = request["stage"].get("options") or {}
        field = str(options.get("field") or "camera")
        routes = {
            str(k): str(v) for k, v in (options.get("routes") or {}).items()
        }
        pool = request["assignee_pool"]
        in_pool = {u["id"] for u in pool.get("users") or []} | {
            g["id"] for g in pool.get("groups") or []
        }
        out = []
        for task in _pending_tasks(request):
            sample_ids = task.get("sample_ids") or []
            if not sample_ids or not routes:
                continue
            values = set(ctx.dataset.select(sample_ids).distinct(field))
            target = next(
                (routes[v] for v in sorted(map(str, values)) if v in routes),
                None,
            )
            if target and target in in_pool:
                out.append(
                    {
                        "task_id": task["id"],
                        "assignees": [target],
                        "note": f"{field} in {sorted(values)}",
                    }
                )
        # Unrouted batches (no mapped value, or a route outside the pool)
        # are handed to least-loaded in the same run.
        return {"assignments": out, "fallthrough": "default"}


# ---------------------------------------------------------------------------
# 3. Shared batches: assign the group itself, or leave unassigned
# ---------------------------------------------------------------------------


class AssignSharedToGroup(_PolicyBase):
    """Every batch goes to the pool group with the fewest open batches, as
    a **shared** assignment (the group, not a member), so any member can
    open it from Mine and the first to submit takes it.

    Shows two things the default policy never does: assigning a group as
    a group, and deliberately leaving batches unassigned (an empty
    ``assignees`` with ``"fallthrough": "none"``) when the pool has no
    groups, so they stay claimable by anyone in the pool.
    """

    NAME = "example_assign_shared_to_group"
    LABEL = "Example: shared to group"

    assignment_policy_descriptor = {
        "label": "Shared to group (example)",
        "description": (
            "Each batch goes to the pool group with the fewest open batches, "
            "as a shared group assignment; no groups -> left unassigned."
        ),
    }

    def execute(self, ctx):
        request = _request(ctx)
        groups = [
            dict(g) for g in request["assignee_pool"].get("groups") or []
        ]
        load = {g["id"]: int(g.get("open_tasks") or 0) for g in groups}
        out = []
        for task in _pending_tasks(request):
            if not groups:
                out.append(
                    {
                        "task_id": task["id"],
                        "assignees": [],
                        "note": "no group in pool",
                    }
                )
                continue
            gid = min(load, key=lambda g: (load[g], g))
            load[gid] += 1
            out.append(
                {"task_id": task["id"], "assignees": [gid], "note": "shared"}
            )
        return {"assignments": out, "fallthrough": "none"}


# ---------------------------------------------------------------------------
# 4. Quality-aware: high-priority batches to the best-approved labelers,
#    with a cap of open batches per person
# ---------------------------------------------------------------------------


class AssignByApprovalRate(_PolicyBase):
    """High-priority batches go to the labelers with the highest approval
    rate; every other batch goes to the least-loaded eligible person; and
    nobody is handed more than ``max_open_tasks`` open batches (default
    10), counting the ones they already hold anywhere.

    Options (``request.stage.options``)::

        {
          "max_open_tasks": 10,        # hard cap per person, default 10
          "high_priority_min": 7,      # batches with priority >= this are "high"
          "rates_key": "labeler_approval_rates",   # see below
          "default_rate": 0.0          # rate for a person with no history
        }

    **Where the approval rate comes from.** The request carries each
    person's load but no quality signal: that is the customer's own data.
    This example reads a ``{user_id: rate in 0..1}`` dict from
    ``ctx.dataset.info[rates_key]``, which a nightly job can refresh from
    the Activity metrics (reviewer accept / reject counts per annotator)
    or from any external scorecard. Swap :func:`_approval_rates` for your
    own lookup; nothing else changes.

    Decisions, in order:

    1. Pending batches are taken highest priority first (then lowest
       batch index), so when experts are scarce the batches that matter
       most get them.
    2. A person is eligible while their open batches (held anywhere, plus
       the ones picked earlier in this run) are under the cap. People at
       the cap are never picked.
    3. A **high-priority** batch goes to the eligible person with the
       highest approval rate; ties go to the fewest open batches.
    4. Any other batch goes to the eligible person with the fewest open
       batches; ties go to the *lowest* approval rate, which keeps the
       experts free for the next high-priority batch.
    5. If nobody is under the cap, the batch is left unassigned on purpose
       (``assignees: []``) and stays claimable; ``"fallthrough": "none"``
       keeps the default policy from overriding the cap.
    """

    NAME = "example_assign_by_approval_rate"
    LABEL = "Example: by approval rate"

    assignment_policy_descriptor = {
        "label": "By approval rate, capped (example)",
        "description": (
            "High-priority batches go to the labelers with the best approval "
            "rate, the rest to the least loaded; nobody holds more than N "
            "open batches (default 10)."
        ),
        "options": {
            "max_open_tasks": {
                "type": "int",
                "label": "Max open batches per person",
            },
            "high_priority_min": {
                "type": "int",
                "label": "High priority is >=",
            },
            "rates_key": {
                "type": "str",
                "label": "dataset.info key with {user: rate}",
            },
            "default_rate": {
                "type": "float",
                "label": "Rate for people without history",
            },
        },
    }

    def execute(self, ctx):
        request = _request(ctx)
        options = request["stage"].get("options") or {}
        cap = _int(options.get("max_open_tasks"), 10)
        high_min = _int(options.get("high_priority_min"), 7)
        default_rate = _float(options.get("default_rate"), 0.0)
        rates = self._approval_rates(ctx, options.get("rates_key"))

        people = [dict(u) for u in request["assignee_pool"].get("users") or []]
        if not people:
            return {"assignments": [], "fallthrough": "none"}
        open_count = {u["id"]: int(u.get("open_tasks") or 0) for u in people}
        rate = {
            u["id"]: _float(rates.get(u["id"]), default_rate) for u in people
        }

        pending = sorted(
            _pending_tasks(request),
            key=lambda t: (
                -int(t.get("priority") or 0),
                int(t.get("batch_index") or 0),
            ),
        )
        out = []
        for task in pending:
            eligible = [uid for uid in open_count if open_count[uid] < cap]
            if not eligible:
                out.append(
                    {
                        "task_id": task["id"],
                        "assignees": [],
                        "note": "everyone at cap",
                    }
                )
                continue
            high = int(task.get("priority") or 0) >= high_min
            if high:
                who = max(eligible, key=lambda u: (rate[u], -open_count[u]))
                note = f"high priority -> approval {rate[who]:.0%}"
            else:
                who = min(eligible, key=lambda u: (open_count[u], rate[u]))
                note = "least loaded"
            open_count[who] += 1
            out.append(
                {"task_id": task["id"], "assignees": [who], "note": note}
            )
        return {"assignments": out, "fallthrough": "none"}

    @staticmethod
    def _approval_rates(ctx, key) -> dict:
        """``{user_id: rate}`` from the dataset's ``info`` dict. Replace with
        your own source (a metrics query, a spreadsheet, an HR system)."""
        key = str(key or "labeler_approval_rates")
        try:
            info = getattr(ctx.dataset, "info", None) or {}
            value = info.get(key) or {}
            return {str(k): float(v) for k, v in value.items()}
        except Exception:  # noqa: BLE001 - a bad table is "no history"
            return {}


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


EXAMPLE_POLICIES = (
    AssignRoundRobin,
    AssignBySampleField,
    AssignSharedToGroup,
    AssignByApprovalRate,
)
