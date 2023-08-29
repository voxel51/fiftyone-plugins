"""
Evaluation operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


class EvaluateModel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="evaluate_model",
            label="Evaluate model",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        evaluate_model(ctx, inputs)

        view = types.View(label="Evaluate model")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        pred_field = kwargs.pop("pred_field")
        gt_field = kwargs.pop("gt_field")
        eval_key = kwargs.pop("eval_key")

        target_view = _get_target_view(ctx, target)
        _, eval_type, methods = _get_evaluation_type(target_view, pred_field)

        method = kwargs.get("method", None)
        if method is None:
            method = methods[0]

        _get_evaluation_method(eval_type, method).parse_parameters(ctx, kwargs)

        if eval_type == "regression":
            eval_fcn = target_view.evaluate_regressions
        elif eval_type == "classification":
            eval_fcn = target_view.evaluate_classifications
        elif eval_type == "detections":
            eval_fcn = target_view.evaluate_detections
        elif eval_type == "segmentations":
            eval_fcn = target_view.evaluate_segmentations

        """
        eval_fcn(
            pred_field,
            gt_field=gt_field,
            eval_key=eval_key,
            **kwargs,
        )
        """

        return {
            "params": {
                "pred_field": pred_field,
                "gt_field": gt_field,
                "eval_key": eval_key,
                **kwargs,
            }
        }

    def resolve_output(self, ctx):
        outputs = types.Object()

        # @todo remove
        outputs.obj("params", view=types.JSONView())

        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def evaluate_model(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    label_fields = _get_label_fields(
        target_view,
        (
            fo.Regression,
            fo.Classification,
            fo.Detections,
            fo.Polylines,
            fo.Keypoints,
            fo.TemporalDetections,
            fo.Segmentation,
        ),
    )

    if not label_fields:
        warning = types.Warning(
            label="This dataset has no suitable label fields",
            description="https://docs.voxel51.com/user_guide/evaluation.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return

    eval_key = get_new_eval_key(ctx, inputs)
    if eval_key is None:
        return False

    label_field_choices = types.DropdownView()
    for field_name in sorted(label_fields):
        label_field_choices.add_choice(field_name, label=field_name)

    inputs.enum(
        "pred_field",
        label_field_choices.values(),
        required=True,
        label="Predictions field",
        description="The field containing model predictions",
        view=label_field_choices,
    )

    pred_field = ctx.params.get("pred_field", None)
    if pred_field is None:
        return

    label_type, eval_type, methods = _get_evaluation_type(
        target_view, pred_field
    )

    gt_fields = set(
        target_view.get_field_schema(embedded_doc_type=label_type).keys()
    )
    gt_fields.discard(pred_field)

    if not gt_fields:
        warning = types.Warning(
            label="This dataset has no suitable ground truth fields",
            description="https://docs.voxel51.com/user_guide/evaluation.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return

    gt_field_choices = types.DropdownView()
    for field_name in sorted(gt_fields):
        gt_field_choices.add_choice(field_name, label=field_name)

    inputs.enum(
        "gt_field",
        gt_field_choices.values(),
        required=True,
        label="Ground truth field",
        description="The field containing ground truth annotations",
        view=gt_field_choices,
    )

    gt_field = ctx.params.get("gt_field", None)
    if gt_field is None:
        return

    if len(methods) > 1:
        method_choices = types.DropdownView()
        for method in methods:
            method_choices.add_choice(method, label=method)

        inputs.enum(
            "method",
            method_choices.values(),
            default=methods[0],
            required=True,
            label="Evaluation method",
            description="The evaluation method to use",
            view=method_choices,
        )

        method = ctx.params.get("method", None)
    else:
        method = methods[0]

    _get_evaluation_method(eval_type, method).get_parameters(ctx, inputs)


def _get_label_fields(sample_collection, label_types):
    schema = sample_collection.get_field_schema(embedded_doc_type=label_types)
    return list(schema.keys())


def _get_evaluation_type(view, pred_field):
    label_type = view._get_label_field_type(pred_field)

    for eval_type, label_types in _EVALUATION_TYPES.items():
        if issubclass(label_type, tuple(label_types)):
            methods = _METHOD_TYPES[eval_type]
            return label_type, eval_type, methods


_EVALUATION_TYPES = {
    "regression": [fo.Regression],
    "classification": [fo.Classification, fo.Classifications],
    "detections": [
        fo.Detections,
        fo.Polylines,
        fo.Keypoints,
        fo.TemporalDetections,
    ],
    "segmentations": [fo.Segmentation],
}

_METHOD_TYPES = {
    "regression": ["simple"],
    "classification": ["simple", "top-k", "binary"],
    "detections": ["coco", "open-images", "activitynet"],
    "segmentations": ["simple"],
}


def _get_evaluation_method(eval_type, method):
    # @todo implement this
    return EvaluationMethod(method)


class EvaluationMethod(object):
    def __init__(self, name):
        self.name = name

    def get_parameters(self, ctx, inputs):
        pass

    def parse_parameters(self, ctx, params):
        pass


def get_target_view(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None

    if has_view or has_selected:
        target_choices = types.RadioGroup(orientation="horizontal")
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Process the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Process the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Process only the selected samples",
            )
            default_target = "SELECTED_SAMPLES"

        inputs.enum(
            "target",
            target_choices.values(),
            default=default_target,
            required=True,
            label="Target view",
            view=target_choices,
        )

    target = ctx.params.get("target", default_target)

    return _get_target_view(ctx, target)


def _get_target_view(ctx, target):
    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


class GetEvaluationInfo(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_evaluation_info",
            label="Get evaluation info",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        get_eval_key(ctx, inputs)

        view = types.View(label="Get evaluation info")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        eval_key = ctx.params["eval_key"]
        info = ctx.dataset.get_evaluation_info(eval_key)

        timestamp = info.timestamp.strftime("%Y-%M-%d %H:%M:%S")
        config = info.config.serialize()
        config = {k: v for k, v in config.items() if v is not None}

        return {
            "eval_key": eval_key,
            "timestamp": timestamp,
            "version": info.version,
            "config": config,
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("eval_key", label="Evaluation key")
        outputs.str("timestamp", label="Creation time")
        outputs.str("version", label="FiftyOne version")
        outputs.obj("config", label="Evaluation config", view=types.JSONView())
        view = types.View(label="Evaluation info")
        return types.Property(outputs, view=view)


class RenameEvaluation(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="rename_evaluation",
            label="Rename evaluation",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        get_eval_key(ctx, inputs)
        get_new_eval_key(
            ctx,
            inputs,
            name="new_eval_key",
            label="New evaluation key",
            description="Provide a new evaluation key for this run",
        )

        view = types.View(label="Rename evaluation")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        eval_key = ctx.params["eval_key"]
        new_eval_key = ctx.params["new_eval_key"]
        ctx.dataset.rename_evaluation(eval_key, new_eval_key)

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Rename successful")
        return types.Property(outputs, view=view)


class DeleteEvaluation(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_evaluation",
            label="Delete evaluation",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        eval_key = get_eval_key(ctx, inputs, show_default=False)

        if eval_key is not None:
            warning = types.Warning(
                label=f"You are about to delete evaluation '{eval_key}'"
            )
            inputs.view("warning", warning)

        view = types.View(label="Delete evaluation")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        eval_key = ctx.params["eval_key"]
        ctx.dataset.delete_evaluation(eval_key)

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Deletion successful")
        return types.Property(outputs, view=view)


def get_eval_key(
    ctx,
    inputs,
    label="Evaluation key",
    description="Select an evaluation key",
    show_default=True,
):
    eval_keys = ctx.dataset.list_evaluations()

    choices = types.DropdownView()
    for eval_key in eval_keys:
        choices.add_choice(eval_key, label=eval_key)

    default = eval_keys[0] if show_default else None
    inputs.str(
        "eval_key",
        default=default,
        required=True,
        label=label,
        description=description,
        view=choices,
    )

    return ctx.params.get("eval_key", None)


def get_new_eval_key(
    ctx,
    inputs,
    name="eval_key",
    label="Evaluation key",
    description="Provide an evaluation key for this run",
):
    prop = inputs.str(
        name,
        required=True,
        label=label,
        description=description,
    )

    eval_key = ctx.params.get(name, None)
    if eval_key is not None and eval_key in ctx.dataset.list_evaluations():
        prop.invalid = True
        prop.error_message = "Evaluation key already exists"
        eval_key = None

    return eval_key


def register(p):
    p.register(EvaluateModel)
    p.register(GetEvaluationInfo)
    p.register(RenameEvaluation)
    p.register(DeleteEvaluation)
