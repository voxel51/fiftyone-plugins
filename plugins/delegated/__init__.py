"""
FiftyOne delegated operations.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from bson import ObjectId

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.delegated as food
import fiftyone.operators.executor as fooe
import fiftyone.operators.types as types


class ManageDelegatedOperations(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_delegated_operations",
            label="Manage delegated operations",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _manage_delegated_operations_inputs(ctx, inputs)

        view = types.View(label="Manage delegated operations")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        action = ctx.params.get("action", "FAIL")

        ids = []
        for name, obj in ctx.params.items():
            if name.startswith("row_") and obj.get("action", False):
                ids.append(obj["id"])

        if not ids:
            return

        dos = food.DelegatedOperationService()
        for id in ids:
            if action == "FAIL":
                dos.set_failed(ObjectId(id))
            else:
                dos.delete_operation(ObjectId(id))


def _manage_delegated_operations_inputs(ctx, inputs):
    tab_choices = types.TabsView()
    tab_choices.add_choice("OPTIONS", label="Options")
    tab_choices.add_choice("RUNS", label="Runs")
    tab_choices.add_choice("CLEANUP", label="Cleanup")
    inputs.enum(
        "tab",
        tab_choices.values(),
        default="OPTIONS",
        view=tab_choices,
    )
    tab = ctx.params.get("tab", "OPTIONS")

    if tab == "OPTIONS":
        _manage_delegated_operations_options(ctx, inputs)
        ready = False
    else:
        ready = _manage_delegated_operations_runs(ctx, inputs)

    if not ready:
        prop = inputs.str("hidden", view=types.HiddenView(read_only=True))
        prop.invalid = True


def _manage_delegated_operations_options(ctx, inputs):
    inputs.message(
        "options_message",
        label=(
            "Use the options below to configure what operations to see, then "
            "click the other tabs to view them"
        ),
    )

    dataset_choices = types.AutocompleteView()
    for name in fo.list_datasets():
        dataset_choices.add_choice(name, label=name)

    inputs.enum(
        "dataset",
        dataset_choices.values(),
        default=ctx.dataset.name,
        required=False,
        label="Dataset",
        description=(
            "Choose a dataset to view delegated operations for, or clear this "
            "field to see everything"
        ),
        view=dataset_choices,
    )

    inputs.str(
        "search",
        required=False,
        label="Search",
        description="Search for operations by operator name",
    )

    state_choices = types.DropdownView()
    state_choices.add_choice("ALL", label="All")
    state_choices.add_choice("QUEUED", label="Queued")
    state_choices.add_choice("RUNNING", label="Running")
    state_choices.add_choice("COMPLETED", label="Completed")
    state_choices.add_choice("FAILED", label="Failed")

    inputs.enum(
        "state",
        state_choices.values(),
        required=True,
        default="ALL",
        label="State",
        description="Only show runs with a specific state",
        view=state_choices,
    )

    sort_by_choices = types.DropdownView()
    sort_by_choices.add_choice("NEWEST", label="Newest")
    sort_by_choices.add_choice("OLDEST", label="Oldest")
    sort_by_choices.add_choice("OPERATOR", label="Operator name")

    inputs.enum(
        "sort_by",
        sort_by_choices.values(),
        default="NEWEST",
        required=True,
        label="Sort by",
        description="Choose how to sort the operations",
        view=sort_by_choices,
    )

    inputs.int(
        "limit",
        default=10,
        required=False,
        label="Limit",
        description="A maximum number of operations to show",
    )


def _manage_delegated_operations_runs(ctx, inputs):
    dataset = ctx.params.get("dataset", None) or None
    search = ctx.params.get("search", None)
    state = ctx.params.get("state", "ALL")
    sort_by = ctx.params.get("sort_by", "NEWEST")
    limit = ctx.params.get("limit", None)
    cleanup = ctx.params.get("tab", "RUNS") == "CLEANUP"

    uuid = str(dataset) + str(search) + str(state) + str(sort_by) + str(limit)

    all_datasets = dataset is None

    if search is not None:
        search = {".*" + search + ".*": ["operator"]}

    if state == "ALL":
        state = None

    reverse = False
    if sort_by == "NEWEST":
        sort_by = "QUEUED_AT"
    elif sort_by == "OLDEST":
        sort_by = "QUEUED_AT"
        reverse = True

    if all_datasets and cleanup:
        space1 = 3
        space2 = 2
    elif all_datasets or cleanup:
        space1 = 3
        space2 = 3
    else:
        space1 = 4
        space2 = 4

    dos = food.DelegatedOperationService()
    ops = dos.list_operations(
        dataset_name=dataset,
        run_state=_parse_state(state),
        paging=_parse_paging(sort_by=sort_by, reverse=reverse, limit=limit),
        search=search,
    )

    if not ops:
        inputs.view("warning", types.Warning(label="No operations found"))
        return False

    obj = types.Object()
    obj.str(
        "operator",
        label="Operator",
        description="The name of the operator",
        view=types.MarkdownView(read_only=True, space=space1),
    )
    if all_datasets:
        obj.str(
            "dataset",
            label="Dataset",
            description="The name of the dataset",
            view=types.MarkdownView(read_only=True, space=space1),
        )
    obj.str(
        "state",
        label="State",
        description="The state of the run",
        view=types.MarkdownView(read_only=True, space=space2),
    )
    obj.str(
        "scheduled",
        label="Scheduled at",
        description="When the run was scheduled",
        view=types.MarkdownView(read_only=True, space=space2),
    )
    if cleanup:
        obj.str(
            "action",
            label="Action",
            description="Select runs to cleanup",
            view=types.MarkdownView(read_only=True, space=space2),
        )
        obj.str("id", view=types.HiddenView(read_only=True, space=0.5))
    inputs.define_property(f"{uuid}_header", obj)

    selected_run_states = []
    for i, op in enumerate(ops, 1):
        prop_name = f"row_{uuid}_op{i}"
        obj = types.Object()
        obj.str(
            "operator",
            default="/ ".join(op.operator.split("/")),
            view=types.MarkdownView(read_only=True, space=space1),
        )
        if all_datasets:
            obj.str(
                "dataset",
                default=op.context.request_params.get("dataset_name", None),
                view=types.MarkdownView(read_only=True, space=space1),
            )
        obj.str(
            "state",
            default=op.run_state.capitalize(),
            view=types.MarkdownView(read_only=True, space=space2),
        )
        obj.str(
            "scheduled",
            default=_format_datetime(op.queued_at),
            view=types.MarkdownView(read_only=True, space=space2),
        )
        if cleanup:
            obj.bool(
                "action",
                default=False,
                view=types.CheckboxView(space=space2),
            )
            obj.str(
                "id",
                default=str(op.id),
                view=types.HiddenView(read_only=True, space=0.5),
            )
        inputs.define_property(prop_name, obj)

        if ctx.params.get(prop_name, {}).get("action", False):
            selected_run_states.append(op.run_state)

    if not cleanup or not selected_run_states:
        return False

    n = len(selected_run_states)
    s = "s" if n > 1 else ""
    pronoun = "them" if n > 1 else "it"
    inputs.message(
        "action_view",
        label=(
            f"You've selected {n} operation{s}. What action would you like to "
            f"perform on {pronoun}?"
        ),
    )

    action_choices = types.DropdownView()
    action_choices.add_choice(
        "FAIL",
        label="Mark as failed",
        description="Mark the selected operations as failed",
    )
    action_choices.add_choice(
        "DELETE",
        label="Delete",
        description="Permanently delete the selected operations",
    )

    prop = inputs.enum(
        "action",
        action_choices.values(),
        label="Action",
        default="FAIL",
        required=True,
        view=action_choices,
    )

    action = ctx.params.get("action", "FAIL")

    if action == "FAIL":
        allowed_states = (
            fooe.ExecutionRunState.QUEUED,
            fooe.ExecutionRunState.RUNNING,
        )
    else:
        allowed_states = (
            fooe.ExecutionRunState.QUEUED,
            fooe.ExecutionRunState.COMPLETED,
            fooe.ExecutionRunState.FAILED,
        )

    okay = all(state in allowed_states for state in selected_run_states)

    if not okay:
        prop.invalid = True
        if action == "FAIL":
            prop.error_message = (
                "You can only mark Queued or Running operations as failed"
            )
        else:
            prop.error_message = (
                "You can only delete Queued, Failed, or Completed operations"
            )

        return False

    return True


def _parse_state(state):
    if state is None:
        return None

    return state.lower()


def _parse_paging(sort_by=None, reverse=None, limit=None):
    from fiftyone.factory import DelegatedOperationPagingParams

    sort_by = _parse_sort_by(sort_by)
    sort_direction = _parse_reverse(reverse)
    return DelegatedOperationPagingParams(
        sort_by=sort_by, sort_direction=sort_direction, limit=limit
    )


def _parse_sort_by(sort_by):
    if sort_by is None:
        return None

    return sort_by.lower()


def _parse_reverse(reverse):
    from fiftyone.factory import SortDirection

    if reverse is None:
        return None

    return SortDirection.ASCENDING if reverse else SortDirection.DESCENDING


def _format_datetime(datetime):
    try:
        import humanize
        import pytz

        return humanize.naturaltime(datetime.replace(tzinfo=pytz.utc))
    except ImportError:
        return str(datetime.replace(microsecond=0))


def register(p):
    p.register(ManageDelegatedOperations)
