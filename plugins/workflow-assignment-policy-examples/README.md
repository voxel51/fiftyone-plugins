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
    options={"max_open_tasks": 10, "high_priority_min": 7},
)
```

## The policy: by approval rate, capped

A quality-aware rule, in `policies.py`: high-priority batches go to the
labelers with the highest approval rate, the rest to the least loaded,
and nobody holds more than 10 open batches. It shows bringing in a signal
the request does not carry (the customer's own approval-rate table) and
honoring a hard cap by leaving batches unassigned instead of overloading
people. Batches it does not answer for are **not** handed to the default
policy (`"fallthrough": "none"`), so the cap holds.

### In one picture

```text
pending batches, highest priority first
  for each batch:
    eligible = people in the pool with open batches < max_open_tasks (10)
    none eligible      -> leave unassigned (stays claimable)
    priority >= 7      -> eligible person with the highest approval rate
    otherwise          -> eligible person with the fewest open batches
    count the pick, so the cap and the spread hold within the wave
```

Set it on a stage with:

```python
fom.update_stage_assignment(
    "my-dataset", workflow_id, stage_id, "auto",
    policy="@voxel51/workflow-assignment-policy-examples/example_assign_by_approval_rate",
    options={"max_open_tasks": 10, "high_priority_min": 7},
)
```

and keep the approval rates where the policy reads them, for example from
a nightly job that folds reviewer accept / reject counts per annotator:

```python
import fiftyone as fo

ds = fo.load_dataset("my-dataset")
ds.info["labeler_approval_rates"] = {"<user id>": 0.96, "<user id>": 0.71}
ds.save()
```

## The contract

A policy is an operator with one extra class attribute:

```python
class MyPolicy(foo.Operator):
    assignment_policy_descriptor = {
        "label": "My policy",            # shown in the dropdown
        "description": "...",
        "options": {                      # optional; stored on the stage,
            "threshold": {"type": "float"}  # arrives as request.stage.options
        },
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
| `assignee_pool` | `users` (id, name, `open_tasks`, `open_samples`, `last_submit_at`, `via_groups`; group members are listed here too) and `groups` (id, name, `member_ids`, `open_tasks`). An "anyone" pool arrives resolved to everyone with Can tag permission. |
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
