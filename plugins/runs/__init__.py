"""
Custom runs operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict
from datetime import datetime

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


class GetRunInfo(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_run_info",
            label="Get run info",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_run_type(ctx, inputs)
        run_key = get_run_key(
            ctx, inputs, run_type=run_type, dynamic_param_name=True
        )

        if run_key is not None:
            d = _get_run_info(ctx.dataset, run_key)

            # Run info
            inputs.view(
                "info_header",
                types.Header(label="Run info", divider=True),
            )
            inputs.str(
                "info_run_key",
                label="Run key",
                default=d["run_key"],
                view=types.LabelValueView(read_only=True),
            )
            inputs.str(
                "info_run_type",
                label="Method",
                default=d["run_type"],
                view=types.LabelValueView(read_only=True),
            )
            inputs.str(
                "info_timestamp",
                label="Creation time",
                default=d["timestamp"],
                view=types.LabelValueView(read_only=True),
            )
            inputs.str(
                "info_version",
                label="FiftyOne version",
                default=d["version"],
                view=types.LabelValueView(read_only=True),
            )

            # Config
            inputs.view(
                "config_header",
                types.Header(label="Run config", divider=True),
            )
            if ctx.params.get("config_raw", False):
                inputs.obj(
                    "config_json",
                    default=d["config"],
                    view=types.JSONView(),
                )
            else:
                for key, value in d["config"].items():
                    if isinstance(value, dict):
                        inputs.obj(
                            "config_" + key,
                            label=key,
                            default=value,
                            view=types.JSONView(),
                        )
                    else:
                        inputs.str(
                            "config_" + key,
                            label=key,
                            default=str(value),
                            view=types.LabelValueView(read_only=True),
                        )

            inputs.bool(
                "config_raw",
                label="Show as JSON",
                default=False,
                view=types.SwitchView(),
            )

            # Actions
            inputs.view(
                "actions_header",
                types.Header(label="Actions", divider=True),
            )
            inputs.bool(
                "load_view",
                default=False,
                label="Load view",
                description=(
                    "Whether to load the view on which this run was performed"
                ),
            )
            ready = ctx.params.get("load_view", False)
        else:
            ready = False

        if not ready:
            prop = inputs.bool("hidden", view=types.HiddenView())
            prop.invalid = True

        view = types.View(label="Get run info")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        run_key = _get_run_key(ctx)
        load_view = ctx.params.get("load_view", False)

        if load_view:
            ctx.trigger(
                "@voxel51/runs/load_run_view",
                params={"run_key": run_key},
            )


def _get_run_info(dataset, run_key):
    run_type = _get_run_type(dataset, run_key)

    info = dataset.get_run_info(run_key)
    timestamp = info.timestamp
    version = info.version
    config = info.config

    if timestamp is not None:
        timestamp = timestamp.strftime("%Y-%M-%d %H:%M:%S")

    if config is not None:
        config = {k: v for k, v in config.serialize().items() if v is not None}
    else:
        config = {}

    return {
        "run_key": run_key,
        "run_type": run_type,
        "timestamp": timestamp,
        "version": version,
        "config": config,
    }


class LoadRunView(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_run_view",
            label="Load run view",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_run_type(ctx, inputs)
        get_run_key(ctx, inputs, run_type=run_type, dynamic_param_name=True)

        view = types.View(label="Load run view")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        run_key = _get_run_key(ctx)
        view = ctx.dataset.load_run_view(run_key)
        ctx.ops.set_view(view=view)


class RenameRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="rename_run",
            label="Rename run",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_run_type(ctx, inputs)
        run_key = get_run_key(
            ctx, inputs, run_type=run_type, dynamic_param_name=True
        )

        if run_key is not None:
            get_new_run_key(
                ctx,
                inputs,
                name="new_run_key",
                label="New run key",
                description="Provide a new key for this run",
            )

        view = types.View(label="Rename run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        run_key = _get_run_key(ctx)
        new_run_key = ctx.params["new_run_key"]
        ctx.dataset.rename_run(run_key, new_run_key)


class DeleteRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_run",
            label="Delete run",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_run_type(ctx, inputs)
        run_key = get_run_key(
            ctx,
            inputs,
            run_type=run_type,
            dynamic_param_name=True,
            show_default=False,
        )

        if run_key is not None:
            warning = types.Warning(
                label=f"You are about to delete run '{run_key}'"
            )
            inputs.view("warning", warning)

        view = types.View(label="Delete run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        run_key = _get_run_key(ctx)
        ctx.dataset.delete_run(run_key)


def get_run_type(ctx, inputs):
    run_types = []
    for run_key in ctx.dataset.list_runs():
        run_type = _get_run_type(ctx.dataset, run_key)
        if run_type is not None and run_type not in run_types:
            run_types.append(run_type)

    choices = types.DropdownView()
    choices.add_choice(None, label="- all -")
    for run_type in sorted(run_types):
        choices.add_choice(run_type, label=run_type)

    inputs.str(
        "run_type",
        default=None,
        label="Method",
        description=(
            "You can optionally choose a specific method of interest "
            "to narrow your search"
        ),
        view=choices,
    )

    return ctx.params.get("run_type", None)


def _get_run_type(dataset, run_key):
    info = dataset.get_run_info(run_key)
    config = info.config
    return getattr(config, "method", None)


def get_run_key(
    ctx,
    inputs,
    label="Run key",
    description="Select a run key",
    dataset=None,
    dynamic_param_name=False,
    show_default=True,
    error_message=None,
    run_type=None,
    **kwargs,
):
    if dataset is None:
        dataset = ctx.dataset

    if run_type is not None:
        kwargs["method"] = run_type

    run_keys = dataset.list_runs(**kwargs)

    if not run_keys:
        if error_message is None:
            error_message = "This dataset has no custom runs"
            if run_type is not None:
                error_message += f" of type {run_type}"

        warning = types.Warning(
            label=error_message,
            description="https://docs.voxel51.com/plugins/developing_plugins.html#storing-custom-runs",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return

    choices = types.DropdownView()
    for run_key in run_keys:
        choices.add_choice(run_key, label=run_key)

    if dynamic_param_name:
        run_key_param = _get_run_key_param(run_type)
    else:
        run_key_param = "run_key"

    if show_default:
        default = run_keys[0]
    else:
        default = None

    inputs.str(
        run_key_param,
        default=default,
        required=True,
        label=label,
        description=description,
        view=choices,
    )

    return ctx.params.get(run_key_param, None)


def _get_run_key_param(run_type):
    if run_type is None:
        return "run_key"

    return "run_key_%s" % run_type


def _get_run_key(ctx):
    run_type = ctx.params.get("run_type", None)
    run_key_param = _get_run_key_param(run_type)
    return ctx.params[run_key_param]


def get_new_run_key(
    ctx,
    inputs,
    name="run_key",
    label="Run key",
    description="Provide a key for this run",
):
    prop = inputs.str(
        name,
        required=True,
        label=label,
        description=description,
    )

    run_key = ctx.params.get(name, None)

    if run_key is not None and run_key in ctx.dataset.list_runs():
        prop.invalid = True
        prop.error_message = "Run key already exists"
        run_key = None

    if run_key is not None and not run_key.isidentifier():
        prop.invalid = True
        prop.error_message = "Run keys must be valid variable names"
        run_key = None

    return run_key


def register(p):
    p.register(GetRunInfo)
    p.register(LoadRunView)
    p.register(RenameRun)
    p.register(DeleteRun)
