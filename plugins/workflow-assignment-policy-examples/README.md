# Workflow Assignment Policy Examples

An example **assignment policy** for FiftyOne workflows. When an
Annotate or Review stage is set to *Automatic* assignment, the workflow
runtime hands every new batch (Task) to someone from the stage's assignee
pool. The built-in policy gives each batch to the least-loaded person. A
policy of your own replaces only that decision: **who holds what**. The
runtime keeps doing everything around it: deciding when to run, resolving
the pool, validating your answer against it, writing with a
compare-and-swap so a claim that landed first wins, and emitting the
activity event.

Requires the `@voxel51/workflows` plugin (ships with FiftyOne Enterprise).

## Install

```bash
fiftyone plugins download \
  https://github.com/voxel51/fiftyone-plugins \
  --plugin-names @voxel51/workflow-assignment-policy-examples
```

Or, for local development, drop this directory in your
`FIFTYONE_PLUGINS_DIR`. The policy appears in the stage's **Assignment
policy** dropdown as soon as the plugin loads: discovery is automatic (the
runtime duck-types any operator that exposes an
`assignment_policy_descriptor`). From a script:

```python
import fiftyone.management as fom

fom.update_stage_assignment(
    "my-dataset", workflow_id, stage_id, "auto",
    policy="@voxel51/workflow-assignment-policy-examples/example_assign_by_approval_rate",
    options={
        "desired_approval_rate": 90,
        "min_approval_rate": 30,
        "max_open_tasks": 20,
    },
)
```

## The policy: by approval rate, capped

A quality-aware rule, in `policies.py`: tasks go to labelers at the
desired first-pass approval rate first; once they are all at the cap, to
labelers at the minimum rate; and a task nobody qualifies for stays
unassigned instead of overloading people or going to someone below the
bar. Tasks it leaves unassigned are **not** handed to the default policy
(`"fallthrough": "none"`), so the rule holds.

Each stage sets its own numbers. Pick the policy in the stage's
**Assignment policy** dropdown and its fields appear right under it,
filled with the defaults:

| Field | Default |
|-------|---------|
| Desired first-pass approval rate | 90 % |
| Min first-pass approval rate | 30 % |
| Max open tasks per person | 10 |

So one policy covers, say, an Annotate stage at 75 % / 20 tasks and a
second pass at 50 % / 30 tasks.

### In one picture

```text
pending tasks, highest priority first
  for each task:
    free     = people in the pool with open tasks < max_open_tasks
    desired  = free people with first-pass approval >= desired rate
    minimum  = free people with first-pass approval >= min rate,
               or no judged work yet
    desired  -> the one with the fewest open tasks (then the higher rate)
    else minimum -> same rule
    else     -> leave unassigned (stays in the pool to claim)
    count the pick, so the cap and the spread hold within the wave
```

The rate comes from the runtime: the descriptor lists
`"request_fields": ["first_pass_approval"]`, so each pool user arrives with
`first_pass_approval` (0..1, from the Activity metrics: of their samples
judged on the first pass, the share approved, across every workflow in the
org) and `first_pass_judged`. Someone with nothing judged yet has `None`
and counts as meeting the minimum, so new labelers can build a record.

## The contract

A policy is an operator with one extra class attribute:

```python
class MyPolicy(foo.Operator):
    assignment_policy_descriptor = {
        "label": "My policy",            # shown in the dropdown
        "description": "...",
        # optional: number fields shown under the policy in the stage form;
        # each stage stores its own values, which arrive (over the
        # defaults) as request.stage.options
        "options": {
            "threshold": {
                "type": "float",          # "int" or "float"
                "label": "Threshold",
                "unit": "%",              # optional
                "default": 50,            # optional
                "min": 0, "max": 100,     # optional; checked on save
            },
        },
        # optional: facts the request leaves out unless asked for
        "request_fields": ["first_pass_approval"],
    }

    @property
    def config(self):
        return foo.OperatorConfig(name="my_policy", label="My policy", unlisted=True)

    def execute(self, ctx):
        request = ctx.params["request"]
        ...
        return {"assignments": [...], "fallthrough": "default"}
```

**Request** (`ctx.params["request"]`):

| Key | Contents |
|-----|----------|
| `stage` | `workflow_id`, `stage_id`, `kind` (`annotate` / `review`), `name`, `pool` (principals as configured), `priority`, `batching`, `options` |
| `tasks` | every open Task of the stage: `id`, `batch_index`, `sample_total`, `open_samples`, `priority`, `assigned_to`, `assigned_by`, `created_at`, `source_collection`, `sample_ids` |
| `pending` | the Tasks that need an owner: `task_id`, `reason` (`opened`, `pool_changed`, `requested`) |
| `assignee_pool` | `users` (id, name, `open_tasks`, `open_samples`, `last_submit_at`, `via_groups`, plus `first_pass_approval` and `first_pass_judged` when requested; group members are listed here too) and `groups` (id, name, `member_ids`, `open_tasks`). An "anyone" pool arrives resolved to everyone with Can tag permission. |
| `triggered_by` | `system` for a wave, or the user id behind **Auto-assign now** / a pool edit |

**Result**:

| Key | Meaning |
|-----|---------|
| `assignments` | `[{"task_id", "assignees": [principals], "note"?}, ...]`. Principals are user ids or `group:<id>` from the pool. One person, several, one or more groups, or `[]` (leave unassigned) are all valid. |
| `priorities` | optional `{task_id: 0..10}` |
| `fallthrough` | `"default"` (default): Tasks you did not answer for go to the built-in least-loaded policy in the same run. `"none"`: leave them unassigned. |

**Guarantees the runtime gives you.** An assignee outside the pool, a
closed Task, or a priority outside 0..10 is skipped and reported, never
written. A Task someone claimed between the request and the write keeps its
claimant. A policy that raises or exceeds its time budget leaves the Tasks
unassigned and claimable, and emits `workflow.auto_assign_failed`. Manual
unassign and Unclaim never trigger a policy run; a manager's **Auto-assign
now** does, even on a stage set to manual.
