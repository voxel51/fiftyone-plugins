"""
FiftyOne delegated operations.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import json

from bson import json_util, ObjectId

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
                id = name.rsplit("_", 1)[-1]
                ids.append(id)

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
    tab_choices.add_choice("SEARCH", label="Search")
    tab_choices.add_choice("INFO", label="Info")
    tab_choices.add_choice("CLEANUP", label="Cleanup")
    inputs.enum(
        "tab",
        tab_choices.values(),
        default="SEARCH",
        view=tab_choices,
    )
    tab = ctx.params.get("tab", "SEARCH")

    if tab == "SEARCH":
        _manage_delegated_operations_search(ctx, inputs)
        ready = False
    else:
        ready = _manage_delegated_operations_actions(ctx, inputs)

    if not ready:
        prop = inputs.str("hidden", view=types.HiddenView())
        prop.invalid = True


def _manage_delegated_operations_search(ctx, inputs):
    inputs.message(
        "search_message",
        label=(
            "Use the options below to configure what operations to see, then "
            "click the other tabs to view/act on them"
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
        description="Search for operations by operator name or label",
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


def _manage_delegated_operations_actions(ctx, inputs):
    dataset = ctx.params.get("dataset", None) or None
    search = ctx.params.get("search", None)
    state = ctx.params.get("state", "ALL")
    sort_by = ctx.params.get("sort_by", "NEWEST")
    limit = ctx.params.get("limit", None)
    tab = ctx.params.get("tab", None)

    uuid = str(dataset) + str(search) + str(state) + str(sort_by) + str(limit)
    all_datasets = dataset is None

    if search is not None:
        search = {".*" + search + ".*": ["operator", "label"]}

    if state == "ALL":
        state = None

    reverse = False
    if sort_by == "NEWEST":
        sort_by = "QUEUED_AT"
    elif sort_by == "OLDEST":
        sort_by = "QUEUED_AT"
        reverse = True

    if all_datasets:
        # 6 columns: 2 2 2 2 2 2
        space1 = 2
        space2 = 2
    else:
        # 5 columns: 3 3 2 2 2
        space1 = 3
        space2 = 2

    dos = food.DelegatedOperationService()
    ops = dos.list_operations(
        dataset_name=dataset,
        run_state=_parse_state(state),
        paging=_parse_paging(sort_by=sort_by, reverse=reverse, limit=limit),
        search=search,
    )

    if not ops:
        inputs.view("notice", types.Notice(label="No operations found"))
        return False

    obj = types.Object()
    obj.str(
        "operator",
        label="Operator",
        description="The name of the operator",
        view=types.MarkdownView(read_only=True, space=space1),
    )
    obj.str(
        "label",
        label="Label",
        description="The operation's label",
        view=types.MarkdownView(read_only=True, space=space1),
    )
    if all_datasets:
        obj.str(
            "dataset",
            label="Dataset",
            description="The name of the dataset",
            view=types.MarkdownView(read_only=True, space=space2),
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
    if tab == "CLEANUP":
        action_description = "Select runs to cleanup"
    else:
        action_description = "Select run to view info"
    obj.str(
        "action",
        label="Action",
        description=action_description,
        view=types.MarkdownView(read_only=True, space=space2),
    )
    inputs.define_property(f"{uuid}_header", obj)

    selected_ops = []
    for i, op in enumerate(ops, 1):
        prop_name = f"row_{uuid}_{op.id}"
        obj = types.Object()
        obj.str(
            "operator",
            default="/ ".join(op.operator.split("/")),
            view=types.MarkdownView(read_only=True, space=space1),
        )
        obj.str(
            "label",
            default=op.label,
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
        obj.bool(
            "action",
            default=False,
            view=types.CheckboxView(space=space2),
        )
        inputs.define_property(prop_name, obj)

        if ctx.params.get(prop_name, {}).get("action", False):
            selected_ops.append(op)

    if tab == "INFO":
        return _handle_info(ctx, inputs, selected_ops)

    if tab == "CLEANUP":
        return _handle_cleanup(ctx, inputs, selected_ops)

    return False


def _handle_info(ctx, inputs, selected_ops):
    if not selected_ops:
        return False

    inputs.str(
        "op_header",
        view=types.Header(label="Operation info", divider=True),
    )

    idx = 0
    if len(selected_ops) > 1:
        tab_choices = types.TabsView()
        for idx, op in enumerate(selected_ops):
            tab_choices.add_choice(idx, label=str(op.id))

        inputs.enum(
            "op_idx",
            tab_choices.values(),
            default=0,
            view=tab_choices,
        )
        idx = ctx.params.get("op_idx", 0)

    op = selected_ops[idx]

    show_raw = ctx.params.get("show_raw", False)

    if show_raw:
        inputs.str(
            "op_info",
            default=fo.pformat(op._doc),
            view=types.CodeView(
                read_only=True,
                height="512px",
                componentsProps={
                    "editor": {
                        "options": {
                            "minimap": {"enabled": False},
                            "scrollBeyondLastLine": False,
                        },
                    },
                },
            ),
        )
    else:
        kv_view = types.MarkdownView(read_only=True, space=4)
        code_view = types.CodeView(
            read_only=True,
            componentsProps={
                "editor": {
                    "options": {
                        "minimap": {"enabled": False},
                        "scrollBeyondLastLine": False,
                    },
                },
            },
        )

        def format_dt(dt):
            if dt is None:
                return "N/A"

            a = dt.strftime("%Y-%m-%d %H:%M:%S")
            b = _format_datetime(dt)
            return f"{a} ({b})"

        def format_code(d):
            return fo.pformat(d) if d else None

        inputs.str(
            "op_operator",
            label="Operator",
            description=op.operator,
            view=kv_view,
        )
        inputs.str(
            "op_label",
            label="Label",
            description=op.label,
            view=kv_view,
        )
        inputs.str(
            "op_id",
            label="ID",
            description=str(op.id),
            view=kv_view,
        )
        inputs.str(
            "op_state",
            label="State",
            description=op.run_state.capitalize(),
            view=kv_view,
        )
        inputs.str(
            "op_scheduled_at",
            label="Scheduled at",
            description=format_dt(op.scheduled_at),
            view=kv_view,
        )
        inputs.str(
            "op_queued_at",
            label="Queued at",
            description=format_dt(op.queued_at),
            view=kv_view,
        )
        inputs.str(
            "op_started_at",
            label="Started at",
            description=format_dt(op.started_at),
            view=kv_view,
        )
        inputs.str(
            "op_completed_at",
            label="Completed at",
            description=format_dt(op.completed_at),
            view=kv_view,
        )
        inputs.str(
            "op_failed_at",
            label="Failed at",
            description=format_dt(op.failed_at),
            view=kv_view,
        )

        tab_choices = types.TabsView()
        tab_choices.add_choice("INPUTS", label="Inputs")
        tab_choices.add_choice("VIEW", label="View")
        tab_choices.add_choice("OUTPUTS", label="Outputs")
        tab_choices.add_choice("ERRORS", label="Errors")

        inputs.enum(
            "op_tab",
            tab_choices.values(),
            default="INPUTS",
            view=tab_choices,
        )
        tab = ctx.params.get("op_tab", "INPUTS")

        request_params = op._doc["context"]["request_params"]
        result = op._doc.get("result", None)

        if tab == "INPUTS":
            inputs.str(
                "op_inputs",
                default=format_code(request_params["params"]),
                view=code_view,
            )
        elif tab == "VIEW":
            dataset_name, view_params = _parse_op_view(request_params)
            if dataset_name != ctx.dataset.name:
                inputs.btn(
                    "op_dataset",
                    label="Load input dataset",
                    on_click="open_dataset",
                    params={"dataset": dataset_name},
                )

            inputs.btn(
                "op_view",
                label="Load input view",
                on_click="set_view",
                params=view_params,
            )
        elif tab == "OUTPUTS":
            inputs.str(
                "op_outputs",
                default=format_code(result["result"]) if result else None,
                view=code_view,
            )
        elif tab == "ERRORS":
            inputs.str(
                "op_errors",
                default=result["error"] if result else None,
                view=code_view,
            )

    inputs.bool(
        "show_raw",
        label="Show raw",
        default=False,
        view=types.SwitchView(),
    )

    return False


def _handle_cleanup(ctx, inputs, selected_ops):
    if not selected_ops:
        return False

    n = len(selected_ops)
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

    okay = all(op.run_state in allowed_states for op in selected_ops)

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


def _parse_op_view(request_params):
    ctx = foo.ExecutionContext(request_params=request_params)
    dataset = ctx.dataset
    view = ctx.view

    dataset_name = dataset.name if dataset is not None else None
    view_params = {
        "view": _serialize_view(view) if view is not None else None,
        "name": view.name if view is not None else None,
    }

    return dataset_name, view_params


def _serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))


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
