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
  finalize_*` call — **never a return value**.
- **`dos.py`** — the three delegated operators the DO stages dispatch.
  Each ends with `notify_do_completed(...)` in a `finally`; that callback
  is the load-bearing "I'm done, resume the stage" signal.
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

Heavy or slow work never runs inline. The stage calls `fop.dos.submit(...)`
and returns **without routing** — the sample stays in-flight, gated on the
DO. When the DO finishes it calls the platform trampoline
`workflow_do_completed`, which re-enters your stage's `on_do_completed`,
where you route. Because hooks are stateless, stash whatever you need to
route (a `sample_id`, a serialized `collection_ref`) in the DO's params and
recover it from `fop.dos.get(do_id)` on completion.

### Human-in-the-loop

A HITL stage opens a `SubTask` (`fop.tasks.find_or_create` +
`fop.subtasks.create`) and parks the sample. A human decision closes the
SubTask via `workflow_next`, which fires `on_subtask_submitted`, where you
transition the SubTask, reconcile the task, and route by `outcome`
(`accept`/`reject`/`skip`). Use the bundled Release panel, or wire your own.

## Where this is still too much ceremony

These examples deliberately show the **raw** contract, and in doing so they
surface the boilerplate a shipped SDK should absorb:

- The `execute` dispatcher in `_sdk.py` mirrors the platform's
  `runtime/base.py` and must be kept in sync by hand — it belongs in an
  importable base class, not copied per plugin.
- `notify_do_completed(...)` in every DO's `finally` is pure ceremony.
- The stash-in-params / recover-in-`on_do_completed` dance for DO waits,
  and the transition→reconcile→route sequence in every
  `on_subtask_submitted`, repeat verbatim across stages.

Collapsing these into utility helpers is tracked as follow-up work.
