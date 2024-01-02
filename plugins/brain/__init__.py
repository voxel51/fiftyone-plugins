"""
FiftyOne Brain operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import base64
from collections import defaultdict
from datetime import datetime
import inspect
import json
from packaging.version import Version

from bson import json_util

import eta.core.image as etai

import fiftyone as fo
import fiftyone.constants as foc
import fiftyone.core.patches as fop
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.zoo.models as fozm

# pylint:disable=import-error,no-name-in-module
import fiftyone.brain as fob
from fiftyone.brain import Similarity
from fiftyone.brain.internal.core.hardness import Hardness
from fiftyone.brain.internal.core.mistakenness import MistakennessMethod
from fiftyone.brain.internal.core.uniqueness import Uniqueness

try:
    from fiftyone.brain import Visualization
except ImportError:
    # fiftyone-brain<0.16
    from fiftyone.brain.internal.core.visualization import Visualization


class ComputeVisualization(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_visualization",
            label="Compute visualization",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
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
        embeddings = ctx.params.get("embeddings", None) or None
        brain_key = ctx.params["brain_key"]
        model = ctx.params.get("model", None) or None
        method = ctx.params.get("method", None)
        batch_size = ctx.params.get("batch_size", None)
        num_workers = ctx.params.get("num_workers", None)
        skip_failures = ctx.params.get("skip_failures", True)

        kwargs = ctx.params.get("kwargs", {})
        if not kwargs.get("create_index", False):
            kwargs.pop("points_field", None)

        # No multiprocessing allowed when running synchronously
        if not ctx.delegated:
            num_workers = 0

        target_view = _get_target_view(ctx, target)

        kwargs = {}

        if ctx.delegated:
            progress = lambda pb: ctx.set_progress(progress=pb.progress)
            kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        fob.compute_visualization(
            target_view,
            patches_field=patches_field,
            embeddings=embeddings,
            brain_key=brain_key,
            model=model,
            method=method,
            batch_size=batch_size,
            num_workers=num_workers,
            skip_failures=skip_failures,
            **kwargs,
        )


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

    # @todo can remove version check if we require `fiftyone>=1.4.0`
    num_dims = ctx.params.get("num_dims", None)
    if num_dims == 2 and Version(foc.VERSION) >= Version("1.4.0"):
        kwargs = types.Object()
        inputs.define_property("kwargs", kwargs)

        kwargs.bool(
            "create_index",
            default=False,
            label="Create index",
            description=(
                "Whether to create a spatial index for the computed points on "
                "your dataset. This is highly recommended for large datasets "
                "as it enables efficient querying when lassoing points in "
                "embeddings plot"
            ),
        )

        create_index = ctx.params.get("kwargs", {}).get("create_index", False)
        if create_index:
            brain_key = ctx.params["brain_key"]
            patches_field = ctx.params.get("patches_field", None)
            if patches_field is not None:
                loc = f"`{patches_field}` attribute"
            else:
                loc = "sample field"

            inputs.str(
                "points_field",
                default=brain_key,
                label="Points field",
                description=f"The {loc} in which to store the spatial index",
            )

    return True


class ManageVisualizationIndexes(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_visualization_indexes",
            label="Manage visualization indexes",
            dynamic=True,
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        manage_visualization_indexes(ctx, inputs)

        view = types.View(label="Manage visualization indexes")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = ctx.params["brain_key"]
        points_field = ctx.params.get("points_field", None)
        create_index = ctx.params.get("create_index", True)

        info = ctx.dataset.get_brain_info(brain_key)
        results = ctx.dataset.load_brain_results(brain_key)

        if info.config.points_field is not None:
            results.remove_index()
        else:
            results.index_points(
                points_field=points_field, create_index=create_index
            )

        if not ctx.delegated:
            ctx.trigger("reload_dataset")


def manage_visualization_indexes(ctx, inputs):
    # @todo can remove this if we require `fiftyone>=1.4.0`
    if Version(foc.VERSION) < Version("1.4.0"):
        warning = types.Warning(
            label=(
                "Your FiftyOne installation does not support spatial indexes "
                "for visualization results"
            )
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True
        return

    brain_key = get_brain_key(
        ctx,
        inputs,
        run_type="visualization",
        error_message="This dataset has no visualization results",
    )

    if not brain_key:
        return

    info = ctx.dataset.get_brain_info(brain_key)
    patches_field = info.config.patches_field
    points_field = info.config.points_field

    if points_field is not None:
        warning = types.Warning(
            label=(
                "These visualization results have a spatial index in the "
                f"`{points_field}` field. Would you like to remove it?"
            )
        )
        inputs.view("warning", warning)
    else:
        notice = types.Notice(
            label=(
                "These visualization results are not indexed. Creating a "
                "spatial index is highly recommended for large datasets as it "
                "enables efficient querying when lassoing points in "
                "embeddings plots. Would you like to create one?"
            )
        )
        inputs.view("notice", notice)

        if patches_field is not None:
            loc = f"`{patches_field}` attribute"
        else:
            loc = "sample field"

        inputs.str(
            "points_field",
            default=brain_key,
            label="Points field",
            description=f"The {loc} in which to store the spatial index",
        )

        # Database indexes are not yet supported for patch visualizations
        if patches_field is None:
            inputs.bool(
                "create_index",
                default=True,
                label="Create database index",
                description=(
                    "Whether to create a database index for the points. This "
                    "is recommended as it will further optimize queries when "
                    "lassoing points"
                ),
            )


class ComputeSimilarity(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_similarity",
            label="Compute similarity",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        compute_similarity(ctx, inputs)

        view = types.View(label="Compute similarity")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        patches_field = kwargs.pop("patches_field", None)
        embeddings = kwargs.pop("embeddings", None) or None
        brain_key = kwargs.pop("brain_key")
        model = kwargs.pop("model", None) or None
        batch_size = kwargs.pop("batch_size", None)
        num_workers = kwargs.pop("num_workers", None)
        skip_failures = kwargs.pop("skip_failures", True)
        backend = kwargs.pop("backend", None)

        _inject_brain_secrets(ctx)
        _get_similarity_backend(backend).parse_parameters(ctx, kwargs)

        # No multiprocessing allowed when running synchronously
        if not ctx.delegated:
            num_workers = 0

        target_view = _get_target_view(ctx, target)

        if ctx.delegated:
            progress = lambda pb: ctx.set_progress(progress=pb.progress)
            kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        fob.compute_similarity(
            target_view,
            patches_field=patches_field,
            embeddings=embeddings,
            brain_key=brain_key,
            model=model,
            batch_size=batch_size,
            num_workers=num_workers,
            skip_failures=skip_failures,
            backend=backend,
            **kwargs,
        )


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

    if backend == "milvus":
        return MilvusBackend(backend)

    if backend == "lancedb":
        return LanceDBBackend(backend)

    if backend == "redis":
        return RedisBackend(backend)

    if backend == "mongodb":
        return MongoDBBackend(backend)

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

        inputs.str(
            "index_name",
            label="Index name",
            description=(
                "An optional name of a Pinecone index to use or create"
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
            description=(
                "The embedding distance metric to use when creating a new "
                "index"
            ),
            view=metric_choices,
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

        inputs.str(
            "collection_name",
            label="Collection name",
            description=(
                "An optional name of a Qdrant collection to use or create"
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
            description=(
                "The embedding distance metric to use when creating a new "
                "collection"
            ),
            view=metric_choices,
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


class MilvusBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "milvus",
            types.Header(
                label="Milvus options",
                description="https://docs.voxel51.com/user_guide/brain.html#similarity-api",
                divider=True,
            ),
        )

        inputs.str(
            "collection_name",
            label="Collection name",
            description=(
                "An optional name of a Milvus collection to use or create"
            ),
        )

        metric_choices = types.DropdownView()
        metric_choices.add_choice("dotproduct", label="dotproduct")
        metric_choices.add_choice("euclidean", label="euclidean")

        inputs.enum(
            "metric",
            metric_choices.values(),
            default="dotproduct",
            required=True,
            label="Metric",
            description=(
                "The embedding distance metric to use when creating a new "
                "collection"
            ),
            view=metric_choices,
        )

        consistency_level_choices = types.DropdownView()
        consistency_level_choices.add_choice("Session", label="Session")
        consistency_level_choices.add_choice("Strong", label="Strong")
        consistency_level_choices.add_choice("Bounded", label="Bounded")
        consistency_level_choices.add_choice("Eventually", label="Eventually")

        inputs.enum(
            "consistency_level",
            consistency_level_choices.values(),
            default="Session",
            required=True,
            label="Consistency level",
            description="The consistency level to use.",
            view=consistency_level_choices,
        )


class LanceDBBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "lancedb",
            types.Header(
                label="LanceDB options",
                description="https://docs.voxel51.com/user_guide/brain.html#similarity-api",
                divider=True,
            ),
        )

        inputs.str(
            "table_name",
            label="Table name",
            description=(
                "An optional name of a LanceDB table to use or create"
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
            description=(
                "The embedding distance metric to use when creating a new "
                "table"
            ),
            view=metric_choices,
        )


class RedisBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "redis",
            types.Header(
                label="Redis options",
                description="https://docs.voxel51.com/user_guide/brain.html#similarity-api",
                divider=True,
            ),
        )

        inputs.str(
            "index_name",
            label="Index name",
            description="An optional name of a Redis index to use or create",
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
            description=(
                "The embedding distance metric to use when creating a new "
                "index"
            ),
            view=metric_choices,
        )

        algorithm_choices = types.DropdownView()
        algorithm_choices.add_choice("FLAT", label="FLAT")
        algorithm_choices.add_choice("HNSW", label="HNSW")

        inputs.enum(
            "algorithm",
            algorithm_choices.values(),
            default="FLAT",
            required=True,
            label="Algorithm",
            description=(
                "The search algorithm to use when creating a new index"
            ),
            view=algorithm_choices,
        )


class MongoDBBackend(SimilarityBackend):
    def get_parameters(self, ctx, inputs):
        inputs.view(
            "mongodb",
            types.Header(
                label="MongoDB options",
                description="https://docs.voxel51.com/user_guide/brain.html#similarity-api",
                divider=True,
            ),
        )

        inputs.str(
            "index_name",
            label="Index name",
            required=True,
            description=(
                "An optional name of a MongoDB vector search index to use or "
                "create"
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
            description=(
                "The embedding distance metric to use when creating a new "
                "index"
            ),
            view=metric_choices,
        )


class SortBySimilarity(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="sort_by_similarity",
            label="Sort by similarity",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    """
    def resolve_placement(self, ctx):
        return types.Placement(
            types.Places.SAMPLES_GRID_ACTIONS,
            types.Button(label="Sort by similarity", icon="/assets/search.svg")
        )
    """

    def resolve_input(self, ctx):
        inputs = types.Object()

        choices = types.TabsView()
        choices.add_choice("SELECTED", label="Selected")
        choices.add_choice("IMAGE", label="Image")
        choices.add_choice("TEXT", label="Text")
        default = "SELECTED" if ctx.selected else "TEXT"

        inputs.enum(
            "tab",
            choices.values(),
            default=default,
            view=choices,
        )
        tab = ctx.params.get("tab", default)

        if tab == "SELECTED":
            sort_by_selected_image_similarity(ctx, inputs)
            label = "Sort by selected image similarity"
        elif tab == "IMAGE":
            sort_by_uploaded_image_similarity(ctx, inputs)
            label = "Sort by uploaded image similarity"
        elif tab == "TEXT":
            sort_by_text_similarity(ctx, inputs)
            label = "Sort by text similarity"
        else:
            label = None

        view = types.View(label=label)
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        tab = ctx.params["tab"]
        brain_key = ctx.params["brain_key"]
        target = ctx.params.get("target", None)
        k = ctx.params["k"]

        _inject_brain_secrets(ctx)
        target_view = _get_target_view(ctx, target)

        if tab == "SELECTED":
            query = ctx.selected
        elif tab == "IMAGE":
            query = _embed_query_image(ctx)
        elif tab == "TEXT":
            query = ctx.params["query"]
        else:
            return

        view = target_view.sort_by_similarity(query, k=k, brain_key=brain_key)
        ctx.trigger("set_view", params={"view": serialize_view(view)})


def _embed_query_image(ctx):
    brain_key = ctx.params["brain_key"]
    info = ctx.dataset.get_brain_info(brain_key)
    model = fozm.load_zoo_model(info.config.model)

    query_image = ctx.params["query_image"]
    img_bytes = base64.b64decode(query_image["content"])
    img = etai.decode(img_bytes)

    return model.embed(img)


def sort_by_selected_image_similarity(ctx, inputs):
    if not ctx.selected:
        warning = types.Warning(
            label="Please select query image(s) in the grid"
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return False

    if isinstance(ctx.view, fop.PatchesView):
        patches_field = ctx.view.patches_field
        sim_str = f"'{patches_field}' patch similarity"
    else:
        patches_field = None
        sim_str = "similarity"

    brain_key = get_brain_key(
        ctx,
        inputs,
        run_type="similarity",
        patches_field=patches_field,
        error_message=f"This dataset has no {sim_str} indexes",
    )

    if not brain_key:
        return

    get_target_view(ctx, inputs, allow_selected=False)

    inputs.int(
        "k",
        default=25,
        required=True,
        label="Number of matches",
        description="Choose how many similar samples to show",
    )


def sort_by_uploaded_image_similarity(ctx, inputs):
    if isinstance(ctx.view, fop.PatchesView):
        patches_field = ctx.view.patches_field
        sim_str = f"'{patches_field}' patch similarity"
    else:
        patches_field = None
        sim_str = "similarity"

    brain_keys = []
    for brain_key in ctx.dataset.list_brain_runs(
        type=Similarity, patches_field=patches_field
    ):
        info = ctx.dataset.get_brain_info(brain_key)
        if isinstance(getattr(info.config, "model", None), str):
            brain_keys.append(brain_key)

    brain_key = get_brain_key(
        ctx,
        inputs,
        brain_keys=brain_keys,
        error_message=(
            f"This dataset has no {sim_str} indexes that support query "
            "images"
        ),
    )

    if not brain_key:
        return

    get_target_view(ctx, inputs)

    inputs.obj(
        "query_image",
        required=True,
        label="Query image",
        description="Upload a query image",
        view=types.FileView(label="Query image"),
    )

    inputs.int(
        "k",
        default=25,
        required=True,
        label="Number of matches",
        description="Choose how many similar samples to show",
    )


def sort_by_text_similarity(ctx, inputs):
    if isinstance(ctx.view, fop.PatchesView):
        patches_field = ctx.view.patches_field
        sim_str = f"'{patches_field}' patch similarity"
    else:
        patches_field = None
        sim_str = "similarity"

    brain_key = get_brain_key(
        ctx,
        inputs,
        run_type="similarity",
        patches_field=patches_field,
        supports_prompts=True,
        error_message=(
            f"This dataset has no {sim_str} indexes that support text prompts"
        ),
    )

    if not brain_key:
        return

    get_target_view(ctx, inputs)

    inputs.str(
        "query",
        required=True,
        label="Text prompt",
        description="Show similar samples to the given text prompt",
    )

    inputs.int(
        "k",
        default=25,
        required=True,
        label="Number of matches",
        description="Choose how many similar samples to show",
    )


class AddSimilarSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="add_similar_samples",
            label="Add similar samples",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        dataset_names = fo.list_datasets()

        choices = types.AutocompleteView()
        for name in dataset_names:
            choices.add_choice(name, label=name)

        inputs.enum(
            "src_dataset",
            choices.values(),
            required=True,
            label="Source dataset",
            description=(
                "Choose a source dataset from which to retrieve samples"
            ),
            view=choices,
        )

        src_dataset = ctx.params.get("src_dataset", None)
        if src_dataset in dataset_names:
            src_dataset = fo.load_dataset(src_dataset)

            if ctx.selected:
                ready = search_by_image_similarity(ctx, inputs, src_dataset)
                label = "Add samples by image similarity"
            else:
                ready = search_by_text_similarity(ctx, inputs, src_dataset)
                label = "Add samples by text similarity"
        else:
            label = "Add similar samples"
            ready = False

        if ready:
            choices = types.AutocompleteView()
            for field in _get_sample_fields(ctx.dataset, fo.DateTimeField):
                choices.add_choice(field, label=field)

            inputs.str(
                "query_time_field",
                default=None,
                required=False,
                label="Store query time",
                description=(
                    "An optional new or existing field in which to store the "
                    "datetime at which this query was performed"
                ),
                view=choices,
            )

        view = types.View(label=label)
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        src_dataset = ctx.params["src_dataset"]
        brain_key = ctx.params["brain_key"]
        k = ctx.params["k"]
        query_time_field = ctx.params.get("query_time_field", None)

        _inject_brain_secrets(ctx)

        src_dataset = fo.load_dataset(src_dataset)
        dst_dataset = ctx.dataset

        if ctx.selected:
            # Image query
            index = src_dataset.load_brain_results(brain_key)
            model = index.get_model()
            query = dst_dataset.select(ctx.selected).compute_embeddings(model)
            query_field = None
        else:
            # Text query
            query = ctx.params["query"]
            query_field = ctx.params.get("query_field", None)

        view = src_dataset.sort_by_similarity(query, k=k, brain_key=brain_key)
        samples = [s.copy() for s in view]

        if query_field is not None:
            for sample in samples:
                sample[query_field] = query

        if query_time_field is not None:
            now = datetime.utcnow()
            for sample in samples:
                sample[query_time_field] = now

        # Skip existing filepaths
        filepaths = set(dst_dataset.values("filepath"))
        samples = [
            sample for sample in samples if sample.filepath not in filepaths
        ]

        sample_ids = dst_dataset.add_samples(samples)

        if ctx.selected:
            sample_ids = ctx.selected + sample_ids

        view = dst_dataset.select(sample_ids)
        ctx.trigger("set_view", params={"view": serialize_view(view)})


def search_by_image_similarity(ctx, inputs, src_dataset):
    brain_key = get_brain_key(
        ctx,
        inputs,
        run_type="similarity",
        dataset=src_dataset,
        description="Select a similarity index to use",
        error_message="This dataset has no similarity indexes",
    )

    if not brain_key:
        return False

    info = src_dataset.get_brain_info(brain_key)
    if info.config.model is None:
        error = types.Error(
            label=(
                "This similarity index does not store the name of the "
                "model used to compute its embeddings, so it cannot be used "
                "to embed query images from another dataset"
            ),
        )
        prop = inputs.view("error", error)
        prop.invalid = True

        return False

    inputs.int(
        "k",
        default=25,
        required=True,
        label="Number of matches",
        description=(
            "Choose how many similar samples to add. Note that any results "
            "that match an existing filepath in your dataset will not be added"
        ),
    )

    return True


def search_by_text_similarity(ctx, inputs, src_dataset):
    brain_key = get_brain_key(
        ctx,
        inputs,
        run_type="similarity",
        dataset=src_dataset,
        supports_prompts=True,
        description="Select a similarity index to use",
        error_message=(
            "This dataset has no similarity indexes that support text "
            "prompts"
        ),
    )

    if not brain_key:
        return False

    inputs.str(
        "query",
        required=True,
        label="Text prompt",
        description="Add similar samples to the given text prompt",
    )

    inputs.int(
        "k",
        default=25,
        required=True,
        label="Number of matches",
        description=(
            "Choose how many similar samples to add. Note that any results "
            "that match an existing filepath in your dataset will not be added"
        ),
    )

    choices = types.AutocompleteView()
    for field in _get_sample_fields(ctx.dataset, fo.StringField):
        choices.add_choice(field, label=field)

    inputs.str(
        "query_field",
        default=None,
        required=False,
        label="Store query field",
        description=(
            "An optional new or existing field in which to store the text "
            "prompt used to retrieve these samples"
        ),
        view=choices,
    )

    return True


class ComputeUniqueness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_uniqueness",
            label="Compute uniqueness",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        compute_uniqueness(ctx, inputs)

        view = types.View(label="Compute uniqueness")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        uniqueness_field = ctx.params["uniqueness_field"]
        roi_field = ctx.params.get("roi_field", None)
        embeddings = ctx.params.get("embeddings", None) or None
        model = ctx.params.get("model", None) or None
        batch_size = ctx.params.get("batch_size", None)
        num_workers = ctx.params.get("num_workers", None)
        skip_failures = ctx.params.get("skip_failures", True)

        # No multiprocessing allowed when running synchronously
        if not ctx.delegated:
            num_workers = 0

        target_view = _get_target_view(ctx, target)

        kwargs = {}

        if ctx.delegated:
            progress = lambda pb: ctx.set_progress(progress=pb.progress)
            kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        fob.compute_uniqueness(
            target_view,
            uniqueness_field=uniqueness_field,
            roi_field=roi_field,
            embeddings=embeddings,
            model=model,
            batch_size=batch_size,
            num_workers=num_workers,
            skip_failures=skip_failures,
            **kwargs,
        )

        if not ctx.delegated:
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

    return uniqueness_field is not None


class ComputeMistakenness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_mistakenness",
            label="Compute mistakenness",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        compute_mistakenness(ctx, inputs)

        view = types.View(label="Compute mistakenness")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        pred_field = kwargs.pop("pred_field")
        label_field = kwargs.pop("label_field")
        mistakenness_field = kwargs.pop("mistakenness_field")

        target_view = _get_target_view(ctx, target)

        if ctx.delegated:
            progress = lambda pb: ctx.set_progress(progress=pb.progress)
            kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        fob.compute_mistakenness(
            target_view,
            pred_field,
            label_field,
            mistakenness_field=mistakenness_field,
            **kwargs,
        )

        if not ctx.delegated:
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
    pred_fields = set(_get_label_fields(target_view, label_type))
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

    return mistakenness_field is not None


class ComputeHardness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_hardness",
            label="Compute hardness",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        compute_hardness(ctx, inputs)

        view = types.View(label="Compute hardness")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        label_field = ctx.params.get("label_field")
        hardness_field = ctx.params.get("hardness_field")
        delegate = ctx.params.get("delegate", False)

        target_view = _get_target_view(ctx, target)

        kwargs = {}

        if ctx.delegated:
            progress = lambda pb: ctx.set_progress(progress=pb.progress)
            kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        fob.compute_hardness(
            target_view,
            label_field,
            hardness_field=hardness_field,
            **kwargs,
        )

        if not ctx.delegated:
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

    hardness_field = get_new_brain_key(
        ctx,
        inputs,
        name="hardness_field",
        label="Hardness field",
        description=(
            "The field name to use to store the hardness value for each "
            "sample. This value serves as the brain key for hardness runs"
        ),
    )

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

    return hardness_field is not None


def brain_init(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    brain_key = get_new_brain_key(
        ctx,
        inputs,
        description="Provide a brain key to use to refer to this run",
    )

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
            default=None,
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

    return bool(brain_key)


def get_embeddings(ctx, inputs, view, patches_field):
    if patches_field is not None:
        root, _ = view._get_label_field_root(patches_field)
        field = view.get_field(root, leaf=True)
        schema = field.get_field_schema(ftype=fo.VectorField)
        embeddings_fields = set(root + "." + k for k in schema.keys())
    else:
        embeddings_fields = set(_get_sample_fields(view, fo.VectorField))

    embeddings_choices = types.AutocompleteView()
    for field_name in sorted(embeddings_fields):
        embeddings_choices.add_choice(field_name, label=field_name)

    if patches_field is not None:
        loc = f"`{patches_field}` attribute"
    else:
        loc = "sample field"

    inputs.str(
        "embeddings",
        default=None,
        label="Embeddings",
        description=(
            f"An optional {loc} containing pre-computed embeddings to use. "
            f"Or when a model is provided, a new {loc} in which to store the "
            "embeddings"
        ),
        view=embeddings_choices,
    )

    embeddings = ctx.params.get("embeddings", None)

    if embeddings not in embeddings_fields:
        model_names, _ = _get_zoo_models_with_embeddings(ctx, inputs)

        model_choices = types.AutocompleteView()
        for name in sorted(model_names):
            model_choices.add_choice(name, label=name)

        inputs.enum(
            "model",
            model_choices.values(),
            default=None,
            required=False,
            label="Model",
            description=(
                "An optional name of a model from the "
                "[FiftyOne Model Zoo](https://docs.voxel51.com/user_guide/model_zoo/models.html) "
                "to use to generate embeddings"
            ),
            view=model_choices,
        )

        model = ctx.params.get("model", None)

        if model:
            inputs.int(
                "batch_size",
                default=None,
                label="Batch size",
                description=(
                    "A batch size to use when computing embeddings "
                    "(if applicable)"
                ),
            )

            inputs.int(
                "num_workers",
                default=None,
                label="Num workers",
                description=(
                    "A number of workers to use for Torch data loaders "
                    "(if applicable)"
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


def _get_allowed_model_names(ctx, inputs):
    names = ctx.secrets.get("FIFTYONE_ZOO_ALLOWED_MODEL_NAMES", None)
    if names is None:
        return None

    return set(n.strip() for n in names.split(","))


def _get_allowed_model_licenses(ctx, inputs):
    license = ctx.secrets.get("FIFTYONE_ZOO_ALLOWED_MODEL_LICENSES", None)
    if license is None:
        return None

    licenses = [l.strip() for l in license.split(",")]

    inputs.view(
        "licenses",
        types.Notice(
            label=(
                f"Only models with licenses {licenses} will be available below"
            )
        ),
    )

    return licenses


def _get_zoo_models_with_embeddings(ctx, inputs):
    names = _get_allowed_model_names(ctx, inputs)

    # @todo can remove this if we require `fiftyone>=1.4.0`
    if Version(foc.VERSION) >= Version("1.4.0"):
        licenses = _get_allowed_model_licenses(ctx, inputs)
        kwargs = dict(license=licenses)
    else:
        licenses = None
        kwargs = {}

    if hasattr(fozm, "_list_zoo_models"):
        manifest = fozm._list_zoo_models(**kwargs)
    else:
        # Can remove this code path if we require fiftyone>=1.0.0
        manifest = fozm._load_zoo_models_manifest()

    # pylint: disable=no-member
    available_models = set()
    for model in manifest:
        if names is not None and model.name not in names:
            continue

        if model.has_tag("embeddings"):
            available_models.add(model.name)

    return available_models, licenses


def get_new_brain_key(
    ctx,
    inputs,
    name="brain_key",
    label="Brain key",
    description=None,
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

    if brain_key is not None and not brain_key.isidentifier():
        prop.invalid = True
        prop.error_message = "Brain keys must be valid variable names"
        brain_key = None

    return brain_key


def get_target_view(ctx, inputs, allow_selected=True):
    has_base_view = isinstance(ctx.view, fop.PatchesView)
    if has_base_view:
        has_view = ctx.view != ctx.view._base_view
    else:
        has_view = ctx.view != ctx.dataset.view()
    has_selected = allow_selected and bool(ctx.selected)
    default_target = None

    if has_view or has_selected:
        target_choices = types.RadioGroup(orientation="horizontal")

        if has_base_view:
            target_choices.add_choice(
                "BASE_VIEW",
                label="Base view",
                description="Process the base view",
            )
        else:
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

    if target == "BASE_VIEW":
        return ctx.view._base_view

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


class FindExactDuplicates(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="find_exact_duplicates",
            label="Find exact duplicates",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            description="Find exact duplicate media",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        find_exact_duplicates_inputs(ctx, inputs)

        notice = types.Notice(
            label=(
                "Executing this method will create two saved views:\n\n"
                "`exact duplicates`: all samples whose media is an exact duplicate of one or more other samples\n\n"
                "`representatives of exact duplicates`: one representative sample from each group of exact duplicates"
            )
        )
        inputs.view("notice", notice)

        view = types.View(label="Find exact duplicates")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        response = find_exact_duplicates(ctx)

        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        return response

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "num_total_dups",
            label="Number of samples with exact duplicates",
        )
        outputs.str(
            "num_unique_dups",
            label="Number of exact duplicate groupings",
        )
        view = types.View(label="Exact duplicate results")
        return types.Property(outputs, view=view)


def find_exact_duplicates_inputs(ctx, inputs):
    get_target_view(ctx, inputs)


def find_exact_duplicates(ctx):
    target = ctx.params.get("target", None)

    dataset = ctx.dataset
    target_view = _get_target_view(ctx, target)

    duplicates_dict = fob.compute_exact_duplicates(target_view)

    rep_ids = []
    dup_ids = []
    for rep_id, neighbor_ids in duplicates_dict.items():
        rep_ids.append(rep_id)
        dup_ids.append(rep_id)
        dup_ids.extend(neighbor_ids)

    dups_view = dataset.select(dup_ids, ordered=True)
    reps_view = dataset.select(rep_ids)

    dataset.save_view("exact duplicates", dups_view, overwrite=True)
    dataset.save_view(
        "representatives of exact duplicates", reps_view, overwrite=True
    )

    return {
        "num_total_dups": len(dup_ids),
        "num_unique_dups": len(rep_ids),
    }


class DeduplicateExactDuplicates(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="deduplicate_exact_duplicates",
            label="Deduplicate exact duplicates",
            description=(
                "Delete all but one copy from each group of exact duplicates"
            ),
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        dataset = ctx.dataset
        if dataset.has_saved_view("exact duplicates"):
            dups_view = dataset.load_saved_view("exact duplicates")
            reps_view = dataset.load_saved_view(
                "representatives of exact duplicates"
            )

            warning = types.Warning(
                label=(
                    f"Your last exact duplicates scan detected {len(dups_view)} "
                    f"exact duplicates across {len(reps_view)} groupings. "
                    "Executing this operator will delete all but one sample "
                    "from each group."
                )
            )
            inputs.view("warning", warning)
        else:
            deduplicate_exact_duplicates_inputs(ctx, inputs)

            warning = types.Warning(
                label=(
                    "Executing this operator will detect exact duplicate "
                    "samples and then delete all but one copy from each group."
                    "\n\n"
                    "If you wish to detect exact duplicates without deleting "
                    "them, use the `find_exact_duplicates` operator instead."
                )
            )
            inputs.view("warning", warning)

        view = types.View(label="Deduplicate exact duplicates")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        deduplicate_exact_duplicates(ctx)

        if not ctx.delegated:
            ctx.trigger("reload_dataset")


def deduplicate_exact_duplicates_inputs(ctx, inputs):
    get_target_view(ctx, inputs)


def deduplicate_exact_duplicates(ctx):
    dataset = ctx.dataset

    if not dataset.has_saved_view("exact duplicates"):
        find_exact_duplicates(ctx)

    dups_view = dataset.load_saved_view("exact duplicates")
    reps_view = dataset.load_saved_view("representatives of exact duplicates")

    repr_ids = set(reps_view.values("id"))
    del_sample_ids = [
        _id for _id in dups_view.values("id") if not _id in repr_ids
    ]

    dataset.delete_samples(del_sample_ids)

    dataset.delete_saved_view("exact duplicates")
    dataset.delete_saved_view("representatives of exact duplicates")


class FindNearDuplicates(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="find_near_duplicates",
            label="Find near duplicates",
            description="Find near duplicates",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        find_near_duplicates_inputs(ctx, inputs)

        notice = types.Notice(
            label=(
                "Executing this method will create two saved views:\n\n"
                "`near duplicates`: all samples who are near duplicate of one or more other samples\n\n"
                "`representatives of near duplicates`: one representative sample from each group of near duplicates"
            )
        )
        inputs.view("notice", notice)

        view = types.View(label="Find near duplicates")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        response = find_near_duplicates(ctx)

        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        return response

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "num_total_dups",
            label="Number of samples with near duplicates",
        )
        outputs.str(
            "num_unique_dups",
            label="Number of near duplicate groupings",
        )
        view = types.View(label="Near duplicate results")
        return types.Property(outputs, view=view)


def find_near_duplicates_inputs(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    similarity_runs = ctx.dataset.list_brain_runs(type="similarity")
    if similarity_runs:
        sim_choices = types.Dropdown(label="Similarity index")
        for sim_key in similarity_runs:
            sim_choices.add_choice(sim_key, label=sim_key)

        inputs.enum(
            "similarity_index",
            sim_choices.values(),
            label="Similarity index",
            description=(
                "An optional existing similarity index to use to detect near "
                "duplicates"
            ),
            default=None,
            required=False,
            view=sim_choices,
        )

    similarity_index = ctx.params.get("similarity_index", None)

    if similarity_index is None:
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
                "An optional sample field defining a region of interest "
                "within each image to use to compute embeddings"
            ),
            view=roi_field_choices,
        )

        roi_field = ctx.params.get("roi_field", None)

        get_embeddings(ctx, inputs, target_view, roi_field)

    inputs.float(
        "threshold",
        default=0.3,
        label="Distance threshold",
        description=(
            "A distance threshold for determining near duplicates in "
            "embedding space"
        ),
    )


def find_near_duplicates(ctx):
    target = ctx.params.get("target", None)
    threshold = ctx.params.get("threshold", 0.3)
    similarity_index = ctx.params.get("similarity_index", None)
    roi_field = ctx.params.get("roi_field", None)
    embeddings = ctx.params.get("embeddings", None) or None
    model = ctx.params.get("model", None) or None
    batch_size = ctx.params.get("batch_size", None)
    num_workers = ctx.params.get("num_workers", None)
    skip_failures = ctx.params.get("skip_failures", True)

    # No multiprocessing allowed when running synchronously
    if not ctx.delegated:
        num_workers = 0

    dataset = ctx.dataset
    target_view = _get_target_view(ctx, target)

    index = fob.compute_near_duplicates(
        samples=target_view,
        threshold=threshold,
        similarity_index=similarity_index,
        roi_field=roi_field,
        embeddings=embeddings,
        model=model,
        batch_size=batch_size,
        num_workers=num_workers,
        skip_failures=skip_failures,
    )

    dups_view = index.duplicates_view()

    repr_ids = list(index.neighbors_map.keys())
    reps_view = dataset.select(repr_ids)

    dataset.save_view("near duplicates", dups_view, overwrite=True)
    dataset.save_view(
        "representatives of near duplicates", reps_view, overwrite=True
    )

    return {
        "num_total_dups": len(dups_view),
        "num_unique_dups": len(repr_ids),
    }


class DeduplicateNearDuplicates(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="deduplicate_near_duplicates",
            label="Deduplicate near duplicates",
            description=(
                "Delete all but one copy from each group of near duplicates"
            ),
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        dataset = ctx.dataset
        if dataset.has_saved_view("near duplicates"):
            dups_view = dataset.load_saved_view("near duplicates")
            reps_view = dataset.load_saved_view(
                "representatives of near duplicates"
            )

            warning = types.Warning(
                label=(
                    f"Your last near duplicates scan detected {len(dups_view)} "
                    f"near duplicates across {len(reps_view)} groupings. "
                    "Executing this operator will delete all but one sample "
                    "from each group."
                )
            )
            inputs.view("warning", warning)
        else:
            find_near_duplicates_inputs(ctx, inputs)

            warning = types.Warning(
                label=(
                    "Executing this operator will detect near duplicate "
                    "samples and then delete all but one copy from each group "
                    "from your dataset."
                    "\n\n"
                    "If you wish to detect near duplicates without deleting "
                    "them, use the `find_near_duplicates` operator instead."
                )
            )
            inputs.view("warning", warning)

        view = types.View(label="Deduplicate near duplicates")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        deduplicate_near_duplicates(ctx)

        if not ctx.delegated:
            ctx.trigger("reload_dataset")


def deduplicate_near_duplicates(ctx):
    dataset = ctx.dataset

    if not dataset.has_saved_view("near duplicates"):
        find_near_duplicates(ctx)

    dups_view = dataset.load_saved_view("near duplicates")
    reps_view = dataset.load_saved_view("representatives of near duplicates")

    repr_ids = set(reps_view.values("id"))
    del_sample_ids = [
        _id for _id in dups_view.values("id") if not _id in repr_ids
    ]

    dataset.delete_samples(del_sample_ids)

    dataset.delete_saved_view("near duplicates")
    dataset.delete_saved_view("representatives of near duplicates")


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
        brain_key = get_brain_key(
            ctx, inputs, run_type=run_type, dynamic_param_name=True
        )

        if brain_key is not None:
            d = _get_brain_info(ctx.dataset, brain_key)

            # Run info
            inputs.view(
                "info_header",
                types.Header(label="Run info", divider=True),
            )
            inputs.str(
                "info_brain_key",
                label="Brain key",
                default=d["brain_key"],
                view=types.LabelValueView(read_only=True),
                # description=d["brain_key"],
                # view=types.MarkdownView(read_only=True),
            )
            inputs.str(
                "info_run_type",
                label="Run type",
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
                types.Header(label="Brain config", divider=True),
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

        view = types.View(label="Get brain info")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = _get_dynamic_brain_key(ctx)
        load_view = ctx.params.get("load_view", False)

        if load_view:
            ctx.trigger(
                "@voxel51/brain/load_brain_view",
                params={"brain_key": brain_key},
            )


def _get_brain_info(dataset, brain_key):
    run_type = _get_brain_run_type(dataset, brain_key)

    info = dataset.get_brain_info(brain_key)
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
        "brain_key": brain_key,
        "run_type": run_type,
        "timestamp": timestamp,
        "version": version,
        "config": config,
    }


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
        get_brain_key(ctx, inputs, run_type=run_type, dynamic_param_name=True)

        view = types.View(label="Load brain view")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        brain_key = _get_dynamic_brain_key(ctx)
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
        brain_key = get_brain_key(
            ctx, inputs, run_type=run_type, dynamic_param_name=True
        )

        if brain_key is not None:
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
        brain_key = _get_dynamic_brain_key(ctx)
        new_brain_key = ctx.params["new_brain_key"]
        run_type = _get_brain_run_type(ctx.dataset, brain_key)

        ctx.dataset.rename_brain_run(brain_key, new_brain_key)

        if run_type in ("uniqueness", "mistakenness", "hardness"):
            ctx.trigger("reload_dataset")


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
            ctx,
            inputs,
            run_type=run_type,
            dynamic_param_name=True,
            show_default=False,
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
        brain_key = _get_dynamic_brain_key(ctx)
        cleanup = ctx.params.get("cleanup", False)
        run_type = _get_brain_run_type(ctx.dataset, brain_key)

        if cleanup:
            results = ctx.dataset.load_brain_results(brain_key)
            if results is not None:
                results.cleanup()

        ctx.dataset.delete_brain_run(brain_key)

        if run_type in ("uniqueness", "mistakenness", "hardness"):
            ctx.trigger("reload_dataset")


def get_brain_run_type(ctx, inputs):
    run_types = defaultdict(list)
    for brain_key in ctx.dataset.list_brain_runs():
        run_type = _get_brain_run_type(ctx.dataset, brain_key)
        run_types[run_type].append(brain_key)

    choices = types.DropdownView()
    choices.add_choice(None, label="- all -")
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
    "visualization": Visualization,
}


def get_brain_key(
    ctx,
    inputs,
    label="Brain key",
    description="Select a brain key",
    run_type=None,
    dataset=None,
    brain_keys=None,
    dynamic_param_name=False,
    show_default=True,
    error_message=None,
    **kwargs,
):
    if dataset is None:
        dataset = ctx.dataset

    if brain_keys is None:
        type = _BRAIN_RUN_TYPES.get(run_type, None)
        brain_keys = dataset.list_brain_runs(type=type, **kwargs)

    if not brain_keys:
        if error_message is None:
            error_message = "This dataset has no brain runs"
            if run_type is not None:
                error_message += f" of type {run_type}"

        warning = types.Warning(
            label=error_message,
            description="https://docs.voxel51.com/user_guide/brain.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return

    choices = types.DropdownView()
    for brain_key in brain_keys:
        choices.add_choice(brain_key, label=brain_key)

    if dynamic_param_name:
        brain_key_param = _get_brain_key_param(run_type)
    else:
        brain_key_param = "brain_key"

    if show_default:
        default = brain_keys[0]
    else:
        default = None

    inputs.str(
        brain_key_param,
        default=default,
        required=True,
        label=label,
        description=description,
        view=choices,
    )

    return ctx.params.get(brain_key_param, None)


def _get_brain_key_param(run_type):
    if run_type is None:
        return "brain_key"

    return "brain_key_%s" % run_type


def _get_dynamic_brain_key(ctx):
    run_type = ctx.params.get("run_type", None)
    brain_key_param = _get_brain_key_param(run_type)
    return ctx.params[brain_key_param]


def _get_sample_fields(sample_collection, field_types):
    schema = sample_collection.get_field_schema(flat=True)
    bad_roots = tuple(
        k + "." for k, v in schema.items() if isinstance(v, fo.ListField)
    )
    return [
        path
        for path, field in schema.items()
        if isinstance(field, field_types) and not path.startswith(bad_roots)
    ]


def _get_label_fields(sample_collection, label_types):
    schema = sample_collection.get_field_schema(flat=True)
    bad_roots = tuple(
        k + "." for k, v in schema.items() if isinstance(v, fo.ListField)
    )
    return [
        path
        for path, field in schema.items()
        if (
            isinstance(field, fo.EmbeddedDocumentField)
            and issubclass(field.document_type, label_types)
            and not path.startswith(bad_roots)
        )
    ]


def _inject_brain_secrets(ctx):
    for key, value in ctx.secrets.items():
        # FIFTYONE_BRAIN_SIMILARITY_[UPPER_BACKEND]_[UPPER_KEY]
        if key.startswith("FIFTYONE_BRAIN_SIMILARITY_"):
            _key = key[len("FIFTYONE_BRAIN_SIMILARITY_") :].lower()
            _backend, _key = _key.split("_", 1)
            fob.brain_config.similarity_backends[_backend][_key] = value


def register(p):
    p.register(ComputeVisualization)
    # This operator is builtin to Teams
    if not hasattr(foc, "TEAMS_VERSION"):
        p.register(ManageVisualizationIndexes)
    p.register(ComputeSimilarity)
    p.register(SortBySimilarity)
    p.register(AddSimilarSamples)
    p.register(ComputeUniqueness)
    p.register(ComputeMistakenness)
    p.register(ComputeHardness)
    p.register(FindExactDuplicates)
    p.register(DeduplicateExactDuplicates)
    p.register(FindNearDuplicates)
    p.register(DeduplicateNearDuplicates)
    p.register(GetBrainInfo)
    p.register(LoadBrainView)
    p.register(RenameBrainRun)
    p.register(DeleteBrainRun)
