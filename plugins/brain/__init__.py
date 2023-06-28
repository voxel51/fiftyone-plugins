"""
FiftyOne Brain operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict

import fiftyone as fo
import fiftyone.brain as fob
from fiftyone.brain import Similarity
from fiftyone.brain.internal.core.hardness import Hardness
from fiftyone.brain.internal.core.mistakenness import MistakennessMethod
from fiftyone.brain.internal.core.uniqueness import Uniqueness
from fiftyone.brain.internal.core.visualization import Visualization
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.zoo.models as fozm


class ComputeSimilarity(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_similarity",
            label="Compute similarity",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        compute_similarity(ctx, inputs)

        view = types.View(label="Compute similarity")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        patches_field = ctx.params.get("patches_field", None)
        embeddings = ctx.params.get("embeddings", None)
        brain_key = ctx.params["brain_key"]
        model = ctx.params.get("model", None)
        backend = ctx.params.get("backend", None)

        target_view = _get_target_view(ctx, target)
        fob.compute_similarity(
            target_view,
            patches_field=patches_field,
            embeddings=embeddings,
            brain_key=brain_key,
            model=model,
            backend=backend,
        )

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


class ComputeVisualization(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_visualization",
            label="Compute visualization",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        compute_visualization(ctx, inputs)

        view = types.View(label="Compute visualization")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        patches_field = ctx.params.get("patches_field", None)
        embeddings = ctx.params.get("embeddings", None)
        brain_key = ctx.params["brain_key"]
        model = ctx.params.get("model", None)
        method = ctx.params.get("method", None)

        target_view = _get_target_view(ctx, target)
        fob.compute_visualization(
            target_view,
            patches_field=patches_field,
            embeddings=embeddings,
            brain_key=brain_key,
            model=model,
            method=method,
        )

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def compute_similarity(ctx, inputs):
    brain_init(ctx, inputs)

    default_backend = fob.brain_config.default_similarity_backend
    backends = fob.brain_config.similarity_backends

    backend_choices = types.DropdownView()
    for backend in sorted(backends.keys()):
        backend_choices.add_choice(backend, label=backend)

    inputs.enum(
        "backend",
        backend_choices.values(),
        default=default_backend,
        required=True,
        label="backend",
        description="The similarity backend to use",
        view=backend_choices,
    )

    # @todo add `backend`-specific parameters


def compute_visualization(ctx, inputs):
    brain_init(ctx, inputs)

    method_choices = types.DropdownView()
    method_choices.add_choice("umap", label="UMAP")
    method_choices.add_choice("tsne", label="t-SNE")
    method_choices.add_choice("pca", label="PCA")

    inputs.enum(
        "method",
        method_choices.values(),
        default="umap",
        required=True,
        label="method",
        description="The dimensionality-reduction method to use",
        view=method_choices,
    )

    # @todo add `method`-specific parameters


def brain_init(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    brain_key = get_new_brain_key(ctx, inputs)
    if brain_key is None:
        return

    patches_field_choices = types.DropdownView()
    for field_name in sorted(_get_patches_fields(target_view)):
        patches_field_choices.add_choice(field_name, label=field_name)

    inputs.str(
        "patches_field",
        label="patches_field",
        description=(
            "An optional sample field defining the image patches in each "
            "sample that have been/will be embedded"
        ),
        view=patches_field_choices,
    )

    patches_field = ctx.params.get("patches_field", None)

    if patches_field is not None:
        root, _ = target_view._get_label_field_root(patches_field)
        field = target_view.get_field(root, leaf=True)
        schema = field.get_field_schema(ftype=fo.VectorField)
        embeddings_fields = set(root + "." + k for k in schema.keys())
    else:
        schema = target_view.get_field_schema(ftype=fo.VectorField)
        embeddings_fields = set(schema.keys())

    embeddings_choices = types.AutocompleteView()
    for field_name in sorted(embeddings_fields):
        embeddings_choices.add_choice(field_name, label=field_name)

    inputs.str(
        "embeddings",
        label="embeddings",
        description=(
            "An optional sample field containing pre-computed embeddings to "
            "use. Or when a model is provided, a new field in which to store "
            "the embeddings"
        ),
        view=embeddings_choices,
    )

    embeddings = ctx.params.get("embeddings", None)

    if embeddings not in embeddings_fields:
        model_choices = types.DropdownView()
        for name in sorted(_get_zoo_models()):
            model_choices.add_choice(name, label=name)

        inputs.str(
            "model",
            label="model",
            description=(
                "The name of a model from the FiftyOne Model Zoo to use to "
                "generate embeddings"
            ),
            view=model_choices,
        )


_PATCHES_TYPES = (fo.Detection, fo.Detections, fo.Polyline, fo.Polylines)


def _get_patches_fields(sample_collection):
    schema = sample_collection.get_field_schema(
        embedded_doc_type=_PATCHES_TYPES
    )
    return list(schema.keys())


def _get_zoo_models():
    available_models = set()
    for model in fozm._load_zoo_models_manifest():
        if model.has_tag("embeddings"):
            available_models.add(model.name)

    return available_models


def get_new_brain_key(ctx, inputs, name="brain_key", label="Brain key"):
    prop = inputs.str(name, label=label, required=True)

    brain_key = ctx.params.get(name, None)
    if brain_key is not None and brain_key in ctx.dataset.list_brain_runs():
        prop.invalid = True
        prop.error_message = "Brain key already exists"
        brain_key = None

    return brain_key


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
            required=True,
            default=default_target,
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


class GetBrainInfo(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_brain_info",
            label="Get brain info",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        get_brain_key(ctx, inputs, run_type=run_type)

        view = types.View(label="Get brain info")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        info = ctx.dataset.get_brain_info(brain_key)

        run_type = _get_brain_run_type(info.config)
        timestamp = info.timestamp.strftime("%Y-%M-%d %H:%M:%S")
        config = info.config.serialize()
        config = {k: v for k, v in config.items() if v is not None}

        return {
            "brain_key": brain_key,
            "run_type": run_type,
            "timestamp": timestamp,
            "version": info.version,
            "config": config,
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("brain_key", label="Brain key")
        outputs.str("run_type", label="Run type")
        outputs.str("timestamp", label="Creation time")
        outputs.str("version", label="FiftyOne version")
        outputs.obj("config", label="Brain config", view=types.JSONView())
        view = types.View(label="Brain run info")
        return types.Property(outputs, view=view)


class RenameBrainRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="rename_brain_run",
            label="Rename brain run",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        get_brain_key(ctx, inputs, run_type=run_type)
        get_new_brain_key(
            ctx, inputs, name="new_brain_key", label="New brain key"
        )

        view = types.View(label="Rename brain run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        new_brain_key = ctx.params["new_brain_key"]
        ctx.dataset.rename_brain_run(brain_key, new_brain_key)

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Rename successful")
        return types.Property(outputs, view=view)


class DeleteBrainRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_brain_run",
            label="Delete brain run",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        brain_key = get_brain_key(
            ctx, inputs, run_type=run_type, show_default=False
        )

        if brain_key is not None:
            warning = types.Warning(
                label=f"You are about to delete brain run '{brain_key}'"
            )
            inputs.view("warning", warning)

        view = types.View(label="Delete brain run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        ctx.dataset.delete_brain_run(brain_key)

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Deletion successful")
        return types.Property(outputs, view=view)


def get_brain_run_type(ctx, inputs):
    run_types = defaultdict(list)
    for brain_key in ctx.dataset.list_brain_runs():
        info = ctx.dataset.get_brain_info(brain_key)
        run_type = _get_brain_run_type(info.config)
        run_types[run_type].append(brain_key)

    choices = types.DropdownView()
    for run_type in sorted(run_types.keys()):
        choices.add_choice(run_type, label=run_type)

    inputs.str(
        "run_type",
        label="Run type",
        description=(
            "You can optionally choose a specific brain run type of interest"
        ),
        view=choices,
    )

    return ctx.params.get("run_type", None)


def _get_brain_run_type(config):
    for type_str, cls in _BRAIN_RUN_TYPES.items():
        if issubclass(config.run_cls, cls):
            return type_str

    return None


_BRAIN_RUN_TYPES = {
    "hardness": Hardness,
    "mistakenness": MistakennessMethod,
    "similarity": Similarity,
    "uniqueness": Uniqueness,
    "visualiazation": Visualization,
}


def get_brain_key(ctx, inputs, run_type=None, show_default=True):
    type = _BRAIN_RUN_TYPES.get(run_type, None)
    brain_keys = ctx.dataset.list_brain_runs(type=type)

    if not brain_keys:
        label = "This dataset has no brain runs"
        if run_type is not None:
            label += f" of type {run_type}"

        warning = types.Warning(
            label=label,
            description="https://docs.voxel51.com/user_guide/brain.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return

    choices = types.DropdownView()
    for brain_key in brain_keys:
        choices.add_choice(brain_key, label=brain_key)

    default = brain_keys[0] if show_default else None
    inputs.str(
        "brain_key",
        default=default,
        required=True,
        label="Brain key",
        view=choices,
    )

    return ctx.params.get("brain_key", None)


def register(p):
    p.register(ComputeSimilarity)
    p.register(ComputeVisualization)
    p.register(GetBrainInfo)
    p.register(RenameBrainRun)
    p.register(DeleteBrainRun)
