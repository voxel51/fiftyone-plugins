"""
FiftyOne Brain operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict
import json

from bson import json_util

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.zoo.models as fozm

# pylint:disable=import-error,no-name-in-module
import fiftyone.brain as fob
from fiftyone.brain import Similarity
from fiftyone.brain.internal.core.hardness import Hardness
from fiftyone.brain.internal.core.mistakenness import MistakennessMethod
from fiftyone.brain.internal.core.uniqueness import Uniqueness
from fiftyone.brain.internal.core.visualization import Visualization


class ComputeVisualization(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_visualization",
            label="Compute visualization",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = compute_visualization(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Compute visualization")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        patches_field = ctx.params.get("patches_field", None)
        embeddings = ctx.params.get("embeddings", None)
        brain_key = ctx.params.get("brain_key")
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


def compute_visualization(ctx, inputs):
    complete = brain_init(ctx, inputs)
    if not complete:
        return False

    method_choices = types.DropdownView()
    method_choices.add_choice(
        "umap",
        label="UMAP",
        description="Uniform Manifold Approximation and Projection",
    )
    method_choices.add_choice(
        "tsne",
        label="t-SNE",
        description="t-distributed Stochastic Neighbor Embedding",
    )
    method_choices.add_choice(
        "pca",
        label="PCA",
        description="Principal Component Analysis",
    )

    inputs.enum(
        "method",
        method_choices.values(),
        default="umap",
        required=True,
        label="method",
        description="The dimensionality reduction method to use",
        view=method_choices,
    )

    inputs.int(
        "num_dims",
        default=2,
        required=True,
        label="Number of dimensions",
        description="The dimension of the visualization space",
    )

    inputs.int(
        "seed",
        label="Random seed",
        description="An optional random seed to use",
    )

    return True


class ComputeSimilarity(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_similarity",
            label="Compute similarity",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = compute_similarity(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Compute similarity")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        patches_field = kwargs.pop("patches_field", None)
        embeddings = kwargs.pop("embeddings", None)
        brain_key = kwargs.pop("brain_key")
        model = kwargs.pop("model", None)
        backend = kwargs.pop("backend", None)
        kwargs.pop("delegate")

        _inject_brain_secrets(ctx)
        _get_similarity_backend(backend).parse_parameters(ctx, kwargs)

        target_view = _get_target_view(ctx, target)
        fob.compute_similarity(
            target_view,
            patches_field=patches_field,
            embeddings=embeddings,
            brain_key=brain_key,
            model=model,
            backend=backend,
            **kwargs,
        )

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def compute_similarity(ctx, inputs):
    ready = brain_init(ctx, inputs)
    if not ready:
        return False

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
        label="Backend",
        description="The similarity backend to use",
        view=backend_choices,
    )

    backend = ctx.params.get("backend", default_backend)

    _get_similarity_backend(backend).get_parameters(ctx, inputs)

    return True


def _get_similarity_backend(backend):
    if backend == "sklearn":
        return SklearnBackend(backend)

    if backend == "pinecone":
        return PineconeBackend(backend)

    if backend == "qdrant":
        return QdrantBackend(backend)

    return SimilarityBackend(backend)


class SimilarityBackend(object):
    def __init__(self, name):
        self.name = name

    def get_parameters(self, ctx, inputs):
        pass

    def parse_parameters(self, ctx, params):
        pass


class SklearnBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "sklearn",
            types.Header(
                label="Sklearn options",
                description="https://docs.voxel51.com/user_guide/brain.html#similarity-api",
                divider=True,
            ),
        )

        metric_choices = types.DropdownView()
        metric_choices.add_choice("cosine", label="cosine")
        metric_choices.add_choice("euclidean", label="euclidean")

        inputs.enum(
            "metric",
            metric_choices.values(),
            default="cosine",
            required=True,
            label="Metric",
            description="The embedding distance metric to use",
            view=metric_choices,
        )


class PineconeBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "pinecone",
            types.Header(
                label="Pinecone options",
                description="https://docs.voxel51.com/integrations/pinecone.html#pinecone-config-parameters",
                divider=True,
            ),
        )

        metric_choices = types.DropdownView()
        metric_choices.add_choice("cosine", label="cosine")
        metric_choices.add_choice("dotproduct", label="dotproduct")
        metric_choices.add_choice("euclidean", label="euclidean")

        inputs.enum(
            "metric",
            metric_choices.values(),
            default="cosine",
            required=True,
            label="Metric",
            description="The embedding distance metric to use",
            view=metric_choices,
        )

        inputs.str(
            "index_name",
            label="Index name",
            description=(
                "An optional name of a Pinecone index to use or create"
            ),
        )
        inputs.str(
            "index_type",
            label="Index type",
            description=(
                "An optional index type to use when creating a new index"
            ),
        )
        inputs.str(
            "namespace",
            label="Namespace",
            description=(
                "An optional namespace under which to store vectors added to "
                "the index"
            ),
        )
        inputs.int(
            "replicas",
            label="Replicas",
            description=(
                "An optional number of replicas when creating a new index"
            ),
        )
        inputs.int(
            "shards",
            label="Shards",
            description=(
                "An optional number of shards when creating a new index"
            ),
        )
        inputs.int(
            "pods",
            label="Pods",
            description="An optional number of pods when creating a new index",
        )
        inputs.str(
            "pod_type",
            label="Pod type",
            description="An optional pod type when creating a new index",
        )


class QdrantBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "qdrant",
            types.Header(
                label="Qdrant options",
                description="https://docs.voxel51.com/integrations/qdrant.html#qdrant-config-parameters",
                divider=True,
            ),
        )

        metric_choices = types.DropdownView()
        metric_choices.add_choice("cosine", label="cosine")
        metric_choices.add_choice("dotproduct", label="dotproduct")
        metric_choices.add_choice("euclidean", label="euclidean")

        inputs.enum(
            "metric",
            metric_choices.values(),
            default="cosine",
            required=True,
            label="Metric",
            description="The embedding distance metric to use",
            view=metric_choices,
        )

        inputs.str(
            "collection_name",
            label="Collection name",
            description=(
                "An optional name of a Qdrant collection to use or create"
            ),
        )
        inputs.str(
            "replication_factor",
            label="Replication factor",
            description=(
                "An optional replication factor to use when creating a new "
                "index"
            ),
        )
        inputs.int(
            "shard_number",
            label="Shard number",
            description=(
                "An optional number of shards to use when creating a new index"
            ),
        )
        inputs.int(
            "write_consistency_factor",
            label="Write consistency factor",
            description=(
                "An optional write consistency factor to use when creating a "
                "new index"
            ),
        )


class ComputeUniqueness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_uniqueness",
            label="Compute uniqueness",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = compute_uniqueness(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Compute uniqueness")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        uniqueness_field = ctx.params.get("uniqueness_field")
        roi_field = ctx.params.get("roi_field", None)
        embeddings = ctx.params.get("embeddings", None)
        model = ctx.params.get("model", None)

        target_view = _get_target_view(ctx, target)
        fob.compute_uniqueness(
            target_view,
            uniqueness_field=uniqueness_field,
            roi_field=roi_field,
            embeddings=embeddings,
            model=model,
        )
        ctx.trigger("reload_dataset")


def compute_uniqueness(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    uniqueness_field = get_new_brain_key(
        ctx,
        inputs,
        name="uniqueness_field",
        label="Uniqueness field",
        description=(
            "The field name to use to store the uniqueness value for each "
            "sample. This value serves as the brain key for uniqueness runs"
        ),
    )
    if uniqueness_field is None:
        return False

    roi_fields = _get_label_fields(
        target_view,
        (fo.Detection, fo.Detections, fo.Polyline, fo.Polylines),
    )

    roi_field_choices = types.DropdownView()
    for field_name in sorted(roi_fields):
        roi_field_choices.add_choice(field_name, label=field_name)

    inputs.str(
        "roi_field",
        label="ROI field",
        description=(
            "An optional sample field defining a region of interest within "
            "each image to use to compute uniqueness"
        ),
        view=roi_field_choices,
    )

    roi_field = ctx.params.get("roi_field", None)

    get_embeddings(ctx, inputs, target_view, roi_field)

    return True


class ComputeMistakenness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_mistakenness",
            label="Compute mistakenness",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = compute_mistakenness(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Compute mistakenness")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        pred_field = kwargs.pop("pred_field")
        label_field = kwargs.pop("label_field")
        mistakenness_field = kwargs.pop("mistakenness_field")
        kwargs.pop("delegate")

        target_view = _get_target_view(ctx, target)
        fob.compute_mistakenness(
            target_view,
            pred_field,
            label_field,
            mistakenness_field=mistakenness_field,
            **kwargs,
        )
        ctx.trigger("reload_dataset")


def compute_mistakenness(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    label_fields = _get_label_fields(
        target_view,
        (
            fo.Classification,
            fo.Classifications,
            fo.Detections,
            fo.Polylines,
            fo.Keypoints,
            fo.TemporalDetections,
        ),
    )

    if not label_fields:
        warning = types.Warning(
            label="This dataset has no suitable label fields",
            description="https://docs.voxel51.com/user_guide/brain.html#label-mistakes",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return False

    mistakenness_field = get_new_brain_key(
        ctx,
        inputs,
        name="mistakenness_field",
        label="Mistakenness field",
        description=(
            "The field name to use to store the mistakenness value for each "
            "sample. This value serves as the brain key for mistakenness runs"
        ),
    )
    if mistakenness_field is None:
        return False

    label_field_choices = types.DropdownView()
    for field_name in sorted(label_fields):
        label_field_choices.add_choice(field_name, label=field_name)

    inputs.enum(
        "label_field",
        label_field_choices.values(),
        required=True,
        label="Label field",
        description="The ground truth label field that you want to test for mistakes",
        view=label_field_choices,
    )

    label_field = ctx.params.get("label_field", None)
    if label_field is None:
        return False

    label_type = target_view._get_label_field_type(label_field)
    pred_fields = set(
        target_view.get_field_schema(embedded_doc_type=label_type).keys()
    )
    pred_fields.discard(label_field)

    if not pred_fields:
        warning = types.Warning(
            label="This dataset has no suitable prediction fields",
            description="https://docs.voxel51.com/user_guide/brain.html#label-mistakes",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return False

    pred_field_choices = types.DropdownView()
    for field_name in sorted(pred_fields):
        pred_field_choices.add_choice(field_name, label=field_name)

    inputs.enum(
        "pred_field",
        pred_field_choices.values(),
        required=True,
        label="Predictions field",
        description="The predicted label field to use from each sample",
        view=pred_field_choices,
    )

    pred_field = ctx.params.get("pred_field", None)
    if pred_field is None:
        return False

    inputs.bool(
        "use_logits",
        default=False,
        label="Use logits",
        description=(
            "Whether to use logits (True) or confidence (False) to compute "
            "mistakenness. Logits typically yield better results, when they "
            "are available"
        ),
    )

    if label_type not in (fo.Detections, fo.Polylines, fo.Keypoints):
        return False

    inputs.str(
        "missing_field",
        default="possible_missing",
        required=True,
        label="Missing field",
        description=(
            "A field in which to store per-sample counts of potential missing "
            "objects"
        ),
    )

    inputs.str(
        "spurious_field",
        default="possible_spurious",
        required=True,
        label="Spurious field",
        description=(
            "A field in which to store per-sample counts of potential "
            "spurious objects"
        ),
    )

    inputs.bool(
        "copy_missing",
        default=False,
        label="Copy missing",
        description=(
            "Whether to copy predicted objects that were deemed to be missing "
            "into the label field"
        ),
    )

    return True


def _get_label_fields(sample_collection, label_types):
    schema = sample_collection.get_field_schema(embedded_doc_type=label_types)
    return list(schema.keys())


class ComputeHardness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_hardness",
            label="Compute hardness",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = compute_hardness(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Compute hardness")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        label_field = ctx.params.get("label_field")
        hardness_field = ctx.params.get("hardness_field")

        target_view = _get_target_view(ctx, target)
        fob.compute_hardness(
            target_view,
            label_field,
            hardness_field=hardness_field,
        )
        ctx.trigger("reload_dataset")


def compute_hardness(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    label_fields = _get_label_fields(
        target_view, (fo.Classification, fo.Classifications)
    )

    if not label_fields:
        warning = types.Warning(
            label="This dataset has no classification fields",
            description="https://docs.voxel51.com/user_guide/brain.html#sample-hardness",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return False

    hardnesss_field = get_new_brain_key(
        ctx,
        inputs,
        name="hardnesss_field",
        label="Hardness field",
        description=(
            "The field name to use to store the hardness value for each "
            "sample. This value serves as the brain key for hardness runs"
        ),
    )
    if hardnesss_field is None:
        return False

    label_field_choices = types.DropdownView()
    for field_name in sorted(label_fields):
        label_field_choices.add_choice(field_name, label=field_name)

    inputs.enum(
        "label_field",
        label_field_choices.values(),
        required=True,
        label="Label field",
        description="The classification field to use from each sample",
        view=label_field_choices,
    )

    label_field = ctx.params.get("label_field", None)
    if label_field is None:
        return False

    return True


def brain_init(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    brain_key = get_new_brain_key(ctx, inputs)
    if brain_key is None:
        return False

    patches_fields = _get_label_fields(
        target_view,
        (fo.Detection, fo.Detections, fo.Polyline, fo.Polylines),
    )

    if patches_fields:
        patches_field_choices = types.DropdownView()
        for field_name in sorted(patches_fields):
            patches_field_choices.add_choice(field_name, label=field_name)

        inputs.str(
            "patches_field",
            label="Patches field",
            description=(
                "An optional sample field defining the image patches in each "
                "sample that have been/will be embedded. If omitted, the "
                "full images are processed"
            ),
            view=patches_field_choices,
        )

    patches_field = ctx.params.get("patches_field", None)

    get_embeddings(ctx, inputs, target_view, patches_field)

    return True


def get_embeddings(ctx, inputs, view, patches_field):
    if patches_field is not None:
        root, _ = view._get_label_field_root(patches_field)
        field = view.get_field(root, leaf=True)
        schema = field.get_field_schema(ftype=fo.VectorField)
        embeddings_fields = set(root + "." + k for k in schema.keys())
    else:
        schema = view.get_field_schema(ftype=fo.VectorField)
        embeddings_fields = set(schema.keys())

    embeddings_choices = types.AutocompleteView()
    for field_name in sorted(embeddings_fields):
        embeddings_choices.add_choice(field_name, label=field_name)

    inputs.str(
        "embeddings",
        label="Embeddings",
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
            label="Model",
            description=(
                "An optional name of a model from the FiftyOne Model Zoo to "
                "use to generate embeddings"
            ),
            view=model_choices,
        )

        model = ctx.params.get("model", None)

        if model is not None:
            inputs.int(
                "batch_size",
                label="Batch size",
                description=(
                    "A batch size to use when computing embeddings. Some "
                    "models may not support batching"
                ),
            )

            inputs.int(
                "num_workers",
                label="Num workers",
                description=(
                    "The number of workers to use for Torch data loaders"
                ),
            )

            inputs.bool(
                "skip_failures",
                default=True,
                label="Skip failures",
                description=(
                    "Whether to gracefully continue without raising an error "
                    "if embeddings cannot be generated for a sample"
                ),
            )


def _get_zoo_models():
    available_models = set()
    for model in fozm._load_zoo_models_manifest():
        if model.has_tag("embeddings"):
            available_models.add(model.name)

    return available_models


def get_new_brain_key(
    ctx,
    inputs,
    name="brain_key",
    label="Brain key",
    description="Provide a brain key for this run",
):
    prop = inputs.str(
        name,
        required=True,
        label=label,
        description=description,
    )

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


class GetBrainInfo(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_brain_info",
            label="Get brain info",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        get_brain_key(ctx, inputs, run_type=run_type)

        inputs.bool(
            "load_view",
            default=False,
            label="Load view",
            description=(
                "Whether to load the view on which this brain run was "
                "performed"
            ),
        )

        view = types.View(label="Get brain info")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]

        if ctx.params.get("load_view", False):
            ctx.trigger(
                "@voxel51/brain/load_brain_view",
                params={"brain_key": brain_key},
            )
            return

        info = ctx.dataset.get_brain_info(brain_key)

        run_type = _get_brain_run_type(ctx.dataset, brain_key)
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
        if ctx.params.get("load_view", False):
            return

        outputs = types.Object()
        outputs.str("brain_key", label="Brain key")
        outputs.str("run_type", label="Run type")
        outputs.str("timestamp", label="Creation time")
        outputs.str("version", label="FiftyOne version")
        outputs.obj("config", label="Brain config", view=types.JSONView())
        view = types.View(label="Brain run info")
        return types.Property(outputs, view=view)


class LoadBrainView(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_brain_view",
            label="Load brain view",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        get_brain_key(ctx, inputs, run_type=run_type)

        view = types.View(label="Load brain view")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        view = ctx.dataset.load_brain_view(brain_key)
        ctx.trigger("set_view", params={"view": serialize_view(view)})


def serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))


class RenameBrainRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="rename_brain_run",
            label="Rename brain run",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        get_brain_key(ctx, inputs, run_type=run_type)
        get_new_brain_key(
            ctx,
            inputs,
            name="new_brain_key",
            label="New brain key",
            description="Provide a new brain key for this run",
        )

        view = types.View(label="Rename brain run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        new_brain_key = ctx.params["new_brain_key"]
        run_type = _get_brain_run_type(ctx.dataset, brain_key)

        ctx.dataset.rename_brain_run(brain_key, new_brain_key)

        if run_type in ("uniqueness", "mistakenness", "hardness"):
            ctx.trigger("reload_dataset")

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
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        run_type = get_brain_run_type(ctx, inputs)
        brain_key = get_brain_key(
            ctx, inputs, run_type=run_type, show_default=False
        )

        if brain_key is not None:
            run_type = _get_brain_run_type(ctx.dataset, brain_key)

            if run_type == "similarity":
                inputs.bool(
                    "cleanup",
                    required=True,
                    default=False,
                    label="Cleanup",
                    description=(
                        "Whether to delete the underlying index from the "
                        "external vector database (if any)"
                    ),
                )

            warning = types.Warning(
                label=f"You are about to delete brain run '{brain_key}'"
            )
            inputs.view("warning", warning)

        view = types.View(label="Delete brain run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        cleanup = ctx.params.get("cleanup", False)

        if cleanup:
            results = ctx.dataset.load_brain_results(brain_key)
            if results is not None:
                results.cleanup()

        run_type = _get_brain_run_type(ctx.dataset, brain_key)

        ctx.dataset.delete_brain_run(brain_key)

        if run_type in ("uniqueness", "mistakenness", "hardness"):
            ctx.trigger("reload_dataset")

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Deletion successful")
        return types.Property(outputs, view=view)


def get_brain_run_type(ctx, inputs):
    run_types = defaultdict(list)
    for brain_key in ctx.dataset.list_brain_runs():
        run_type = _get_brain_run_type(ctx.dataset, brain_key)
        run_types[run_type].append(brain_key)

    choices = types.DropdownView()
    for run_type in sorted(run_types.keys()):
        choices.add_choice(run_type, label=run_type)

    inputs.str(
        "run_type",
        label="Run type",
        description=(
            "You can optionally choose a specific brain run type of interest "
            "to narrow your search"
        ),
        view=choices,
    )

    return ctx.params.get("run_type", None)


def _get_brain_run_type(dataset, brain_key):
    info = dataset.get_brain_info(brain_key)
    config = info.config
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


def get_brain_key(
    ctx,
    inputs,
    label="Brain key",
    description="Select a brain key",
    run_type=None,
    show_default=True,
):
    type = _BRAIN_RUN_TYPES.get(run_type, None)
    brain_keys = ctx.dataset.list_brain_runs(type=type)

    if not brain_keys:
        message = "This dataset has no brain runs"
        if run_type is not None:
            message += f" of type {run_type}"

        warning = types.Warning(
            label=message,
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
        label=label,
        description=description,
        view=choices,
    )

    return ctx.params.get("brain_key", None)


def _inject_brain_secrets(ctx):
    for key, value in getattr(ctx, "secrets", {}).items():
        # FIFTYONE_BRAIN_SIMILARITY_[UPPER_BACKEND]_[UPPER_KEY]
        if key.startswith("FIFTYONE_BRAIN_SIMILARITY_"):
            _key = key[len("FIFTYONE_BRAIN_SIMILARITY_") :].lower()
            _backend, _key = _key.split("_", 1)
            fob.brain_config.similarity_backends[_backend][_key] = value


def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", False)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=False,
        required=True,
        label="Delegate execution?",
        description=description,
        view=types.CheckboxView(),
    )

    if delegate:
        inputs.view(
            "notice",
            types.Notice(
                label=(
                    "You've chosen delegated execution. Note that you must "
                    "have a delegated operation service running in order for "
                    "this task to be processed. See "
                    "https://docs.voxel51.com/plugins/using_plugins.html#delegated-operations "
                    "for more information"
                )
            ),
        )


def register(p):
    p.register(ComputeVisualization)
    p.register(ComputeSimilarity)
    p.register(ComputeUniqueness)
    p.register(ComputeMistakenness)
    p.register(ComputeHardness)
    p.register(GetBrainInfo)
    p.register(LoadBrainView)
    p.register(RenameBrainRun)
    p.register(DeleteBrainRun)
