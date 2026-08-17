# Workflow Stage Examples

Ten example [workflow](https://docs.voxel51.com) stages for the FiftyOne
workflow canvas, from a one-line "hello world" to a delegated-operation +
human-in-the-loop capstone. The point: **a workflow stage is just a
FiftyOne operator**, so a Python developer can add a fully-usable custom
stage — discovered, rendered, and configurable in the editor — with the
plugin system you already know.

Requires the `@voxel51/workflows` plugin (ships with FiftyOne Teams).

## Install

```bash
fiftyone plugins download \
  https://github.com/voxel51/fiftyone-plugins \
  --plugin-names @voxel51/workflow-stage-examples
```

Or, for local development, drop this directory in your
`FIFTYONE_PLUGINS_DIR`. Every stage appears in the canvas **Stage picker**
under the **Examples** category as soon as the plugin loads — discovery is
automatic (the editor's `list_workflow_stages` catalog duck-types any
operator that exposes a `stage_descriptor`).

## The ten stages

Read `stages.py` top to bottom — the ceremony grows one concept at a time.

| # | Stage | Concept it introduces |
|---|-------|-----------------------|
| 1 | **Hello world** | The minimum: one `route_sample` call forwards each sample. |
| 2 | **Log message** | A config form (`resolve_stage_config`) whose fields round-trip into a config dataclass. |
| 3 | **Tag samples** | A **collection** stage (`on_collection_received`) doing light inline dataset work. |
| 4 | **Coin-flip router** | Two **output ports**; pick the port in ordinary Python. |
| 5 | **Delay (DO)** | Dispatch a delegated operation and **wait** — the sample advances only in `on_do_completed`. |
| 6 | **Compute metadata (DO)** | Collection-level DO wait; stash + recover the `collection_ref` across the async gap. |
| 7 | **Score samples (DO)** | A DO that writes a field and returns a summary surfaced back to the stage. |
| 8 | **Click to advance** | Simple **HITL**: open a SubTask, park the sample, release on a human click. |
| 9 | **Approve / reject** | HITL whose **outcome picks the output port** (two ports). |
| 10 | **Score, then review** | Capstone: DO scoring → conditional HITL for low scores → three routed ports. |

## The moving parts

- **`stages.py`** — the ten stages. Each subclasses `WorkflowStage`, sets
  a `stage_descriptor` (what the canvas lists/renders) + a `config_type`
  (the config dataclass), and overrides only the hooks it needs. Movement
  is always an `fop.workflows.route_sample / route_collection /
  finalize_*` call — **never a return value**. DO waits and HITL use the
  `fop.authoring` helpers (see below).
- **`dos.py`** — the three delegated operators the DO stages dispatch.
  Each ends with `fop.authoring.notify_do_completed(...)` in a `finally`;
  that callback is the load-bearing "I'm done, resume the stage" signal.
- **`panel.py`** — a custom **Release samples** panel: the surface where a
  human clicks to release a parked sample. It just executes
  `@voxel51/workflows/workflow_next` with an outcome — proving the HITL
  release is a plain operator call any custom UI can drive.
- **`_sdk.py`** — a small, self-contained base (`WorkflowStage`, port
  shorthands, the `execute` dispatcher). It exists so a stage never needs
  a load-order-fragile top-level import of `@voxel51/workflows`; the real
  routing primitives are reached lazily at execute time.

## Concepts in depth

### Ports: stream vs. collection

A port is either a **stream** (`sample_stream`, one sample at a time →
`on_sample_received`) or a **collection** (`sample_collection`, a whole
batch → `on_collection_received`). Declare them on the descriptor with the
`stream_in/stream_out/collection_in/collection_out` shorthands; route out
of a port by name.

### Waiting on a delegated operation

Heavy or slow work never runs inline. The stage calls
`fop.authoring.submit_do(...)` and returns **without routing** — the sample
stays in-flight, gated on the DO. When the DO finishes it calls the
platform trampoline (via `fop.authoring.notify_do_completed`), which
re-enters your stage's `on_do_completed`. Because hooks are stateless,
`submit_do` stashes what you'll need to route (a `sample_id`, a
`collection_ref`, a `source_collection`) and `fop.authoring.resume_do(do_id)`
hands it back — deserialized — on completion.

### Human-in-the-loop

`fop.authoring.open_review(...)` parks a sample on a human (find/create the
stage task + open a subtask). A human decision closes the subtask via
`workflow_next`, firing `on_subtask_submitted`, where
`fop.authoring.close_review(...)` does the transition → reconcile →
drop-on-skip and returns a `ReviewResult` you route by outcome
(`accepted`/`rejected`). Use the bundled Release panel, or wire your own.

## The `fop.authoring` helpers

The repeated DO-wait / HITL sequences live in the platform's
`fop.authoring` module, reached lazily through the same `fop` handle every
stage already uses — so this plugin needs **no** load-order-fragile
top-level import of `@voxel51/workflows`:

| Helper | Collapses |
|--------|-----------|
| `submit_do(ctx, stage, uri, *, sample_id=/collection_ref=/source_collection=, params=)` | `dos.submit` + hand-stashing routing context in `params` |
| `resume_do(ctx, do_id) -> DoResume` | `dos.get` + un-stash + deserialize `collection_ref`/`source_collection` |
| `notify_do_completed(ctx, *, success, result=)` | the `execute_operator(workflow_do_completed, ...)` trampoline call |
| `open_review(ctx, stage, *, sample_id, source_collection, ...)` | `tasks.find_or_create` + `subtasks.create` |
| `close_review(ctx, stage, subtask_id, outcome) -> ReviewResult \| None` | `subtasks.transition` → `tasks.reconcile` → drop-on-skip → recover source collection |

In-tree stages get the same four as convenience methods on
`WorkflowStageOperator` (`self.submit_do(...)`, etc.).

The one piece still copied here is the `execute` dispatcher in `_sdk.py`,
which mirrors the platform's `runtime/base.py`. It stays local on purpose:
subclassing the platform base would force a top-level cross-plugin import,
and plugin load order is not controllable — so an external stage defines
its own tiny base and calls into `fop` lazily at hook time instead.
