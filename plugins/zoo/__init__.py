"""
FiftyOne Zoo operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict
import inspect

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.zoo as foz
import fiftyone.zoo.datasets as fozd
import fiftyone.zoo.models as fozm


class LoadZooDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_zoo_dataset",
            label="Load zoo dataset",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _load_zoo_dataset_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Load zoo dataset")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        kwargs.pop("tags", None)
        name = kwargs.pop("name")
        splits = kwargs.pop("splits", None)
        label_field = kwargs.pop("label_field", None)
        kwargs.pop("dataset_name", None)
        delegate = kwargs.pop("delegate", None)

        dataset_name = _get_zoo_dataset_name(ctx)

        if delegate:
            # can remove check if we require `fiftyone>=0.24`
            if (
                "progress"
                in inspect.signature(foz.load_zoo_dataset).parameters
            ):
                progress = lambda pb: ctx.set_progress(progress=pb.progress)
                kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        dataset = foz.load_zoo_dataset(
            name,
            splits=splits,
            label_field=label_field,
            dataset_name=dataset_name,
            drop_existing_dataset=True,
            **kwargs,
        )
        dataset.persistent = True

        ctx.trigger("open_dataset", dict(dataset=dataset.name))


def _get_zoo_datasets():
    datasets_by_source = fozd._get_zoo_datasets()
    all_sources, _ = fozd._get_zoo_dataset_sources()

    zoo_datasets = {}
    for source in all_sources:
        for name, zoo_dataset_cls in datasets_by_source[source].items():
            if name not in zoo_datasets:
                zoo_datasets[name] = zoo_dataset_cls()

    return zoo_datasets


def _load_zoo_dataset_inputs(ctx, inputs):
    zoo_datasets = _get_zoo_datasets()

    datasets_by_tag = defaultdict(set)
    for name, zoo_dataset in zoo_datasets.items():
        for tag in zoo_dataset.tags or []:
            datasets_by_tag[tag].add(name)

    tag_choices = types.DropdownView(multiple=True)
    for tag in sorted(datasets_by_tag.keys()):
        tag_choices.add_choice(tag, label=tag)

    inputs.list(
        "tags",
        types.String(),
        default=None,
        required=False,
        label="Tags",
        description="Provide optional tag(s) to filter the available datasets",
        view=tag_choices,
    )

    tags = ctx.params.get("tags", None)

    if tags:
        dataset_names = set.intersection(
            *[datasets_by_tag[tag] for tag in tags]
        )
    else:
        dataset_names = list(zoo_datasets.keys())

    dataset_choices = types.AutocompleteView()
    for name in sorted(dataset_names):
        dataset_choices.add_choice(name, label=name)

    inputs.enum(
        "name",
        dataset_choices.values(),
        label="Zoo dataset",
        description=(
            "The name of the dataset to load from the FiftyOne Dataset Zoo"
        ),
        caption="https://docs.voxel51.com/user_guide/model_zoo/models.html",
        view=dataset_choices,
    )

    name = ctx.params.get("name", None)
    if name is None or name not in zoo_datasets:
        return False

    zoo_dataset = zoo_datasets[name]

    _get_source_dir(ctx, inputs, zoo_dataset)

    if zoo_dataset.has_splits:
        split_choices = types.DropdownView(multiple=True)
        for split in zoo_dataset.supported_splits:
            split_choices.add_choice(split, label=split)

        inputs.list(
            "splits",
            types.String(),
            default=None,
            required=False,
            label="Splits",
            description=(
                "You can provide specific split(s) to load. By default, all "
                "available splits are loaded"
            ),
            view=split_choices,
        )

    _partial_download_inputs(ctx, inputs, zoo_dataset)

    inputs.str(
        "label_field",
        default=None,
        required=False,
        label="Label field",
        description=(
            "The label field (or prefix, if the dataset contains multiple "
            "label fields) in which to store the dataset's labels. By "
            "default, this is 'ground_truth' if the dataset contains a single "
            "label field. If the dataset contains multiple label fields and "
            "this value is not provided, the labels will be stored under "
            "dataset-specific field names"
        ),
    )

    inputs.str(
        "dataset_name",
        default=None,
        required=False,
        label="Dataset name",
        description=(
            "You can optionally customize the name of the FiftyOne dataset "
            "that will be created"
        ),
    )

    dataset_name = _get_zoo_dataset_name(ctx)

    if fo.dataset_exists(dataset_name):
        inputs.view(
            "created",
            types.Warning(
                label=(
                    f"A dataset '{dataset_name}' already exists and will be "
                    "overwritten"
                )
            ),
        )
    else:
        inputs.view(
            "created",
            types.Notice(label=f"A dataset '{dataset_name}' will be created"),
        )

    return True


def _get_zoo_dataset_name(ctx):
    name = ctx.params["name"]
    splits = ctx.params.get("splits", None)
    dataset_name = ctx.params.get("dataset_name", None)

    if dataset_name:
        return dataset_name

    if not splits:
        return name

    return name + "-" + "-".join(splits)


def _get_source_dir(ctx, inputs, zoo_dataset):
    name = zoo_dataset.name

    if name == "activitynet-100":
        description = (
            "You can optionally provide the directory containing the "
            "manually downloaded ActivityNet files to avoid downloading "
            "videos from YouTube"
        )
        url = "https://docs.voxel51.com/user_guide/dataset_zoo/datasets.html#activitynet-100"
        required = False
    elif name == "activitynet-200":
        description = (
            "You can optionally provide the directory containing the "
            "manually downloaded ActivityNet files to avoid downloading "
            "videos from YouTube"
        )
        url = "https://docs.voxel51.com/user_guide/dataset_zoo/datasets.html#activitynet-200"
        required = False
    elif name == "bdd100k":
        description = (
            "In order to load the BDD100K dataset, you must download the "
            "source data manually"
        )
        url = "https://docs.voxel51.com/user_guide/dataset_zoo/datasets.html#bdd100k"
        required = True
    elif name == "cityscapes":
        description = (
            "In order to load the Cityscapes dataset, you must download the "
            "source data manually"
        )
        url = "https://docs.voxel51.com/user_guide/dataset_zoo/datasets.html#cityscapes"
        required = True
    elif name == "imagenet-2012":
        description = (
            "In order to load the ImageNet dataset, you must download the "
            "source data manually"
        )
        url = "https://docs.voxel51.com/user_guide/dataset_zoo/datasets.html#imagenet-2012"
        required = True
    else:
        return True

    file_explorer = types.FileExplorerView(
        choose_dir=True,
        button_label="Choose a directory...",
    )
    inputs.file(
        "source_dir",
        required=required,
        label="Source directory",
        description=f"{description}.\n\nSee {url} for more information",
        view=file_explorer,
    )

    if not required:
        return True

    source_dir = _parse_path(ctx, "source_dir")

    return source_dir is not None


def _partial_download_inputs(ctx, inputs, zoo_dataset):
    if not zoo_dataset.supports_partial_downloads:
        return

    name = zoo_dataset.name

    if "coco" in name:
        label_types = ("detections", "segmentations")
        default = "only detections"
        id_type = "COCO"
        only_matching = True
    elif "open-images" in name:
        label_types = (
            "detections",
            "classifications",
            "relationships",
            "segmentations",
        )
        default = "all label types"
        id_type = "Open Images"
        only_matching = True
    elif "activitynet" in name:
        label_types = None
        id_type = None
        only_matching = False
    else:
        return

    if label_types is not None:
        label_type_choices = types.Choices()
        for field in label_types:
            label_type_choices.add_choice(field, label=field)

        inputs.list(
            "label_types",
            types.String(),
            default=None,
            required=False,
            label="Label types",
            description=(
                f"The label type(s) to load. By default, {default} are loaded"
            ),
            view=label_type_choices,
        )

    inputs.list(
        "classes",
        types.String(),
        default=None,
        required=False,
        label="Classes",
        description=(
            "An optional list of strings specifying required classes to load. "
            "If provided, only samples containing at least one instance of a "
            "specified class will be loaded"
        ),
    )

    classes = ctx.params.get("classes", None)

    if classes and only_matching:
        inputs.bool(
            "only_matching",
            default=False,
            label="Only matching",
            description=(
                "Whether to only load labels that match the classes you "
                "provided (True) or to load all labels for samples that "
                "contain the classes"
            ),
        )

    if id_type is not None:
        inputs.bool(
            "include_id",
            default=False,
            label="Include ID",
            description=(
                f"Whether to include the {id_type} ID of each sample in the "
                "loaded labels"
            ),
        )

    inputs.int(
        "max_samples",
        default=None,
        label="Max samples",
        description=(
            "A maximum number of samples to load per split. If label_types "
            "and/or classes are also specified, first priority will be given "
            "to samples that contain all of the specified label types and/or "
            "classes, followed by samples that contain at least one of the "
            "specified labels types or classes. The actual number of samples "
            "loaded may be less than this maximum value if the dataset does "
            "not contain sufficient samples matching your requirements"
        ),
    )

    max_samples = ctx.params.get("max_samples", None)
    if not max_samples:
        return

    inputs.bool(
        "shuffle",
        default=False,
        label="Shuffle",
        description=(
            "Whether to randomly shuffle the order in which samples are chosen"
        ),
    )

    shuffle = ctx.params.get("shuffle", False)
    if not shuffle:
        return

    inputs.int(
        "seed",
        default=None,
        label="Seed",
        description="A random seed to use when shuffling",
    )


class ApplyZooModel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="apply_zoo_model",
            label="Apply zoo model",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _apply_zoo_model_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Apply model")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        model = ctx.params["model"]
        embeddings = ctx.params.get("embeddings", None) == "EMBEDDINGS"
        embeddings_field = ctx.params.get("embeddings_field", None)
        patches_field = ctx.params.get("patches_field", None)
        label_field = ctx.params.get("label_field", None)
        confidence_thresh = ctx.params.get("confidence_thresh", None)
        store_logits = ctx.params.get("store_logits", False)
        batch_size = ctx.params.get("batch_size", None)
        num_workers = ctx.params.get("num_workers", None)
        skip_failures = ctx.params.get("skip_failures", True)
        output_dir = ctx.params.get("output_dir", None)
        rel_dir = ctx.params.get("rel_dir", None)
        delegate = ctx.params.get("delegate", False)

        target_view = _get_target_view(ctx, target)

        model = foz.load_zoo_model(model)

        # No multiprocessing allowed when running synchronously
        if not delegate:
            num_workers = 0

        kwargs = {}

        if delegate:
            # can remove check if we require `fiftyone>=0.24`
            if (
                "progress"
                in inspect.signature(target_view.apply_model).parameters
            ):
                progress = lambda pb: ctx.set_progress(progress=pb.progress)
                kwargs["progress"] = fo.report_progress(progress, dt=5.0)

        if embeddings and patches_field is not None:
            target_view.compute_patch_embeddings(
                model,
                patches_field,
                embeddings_field=embeddings_field,
                batch_size=batch_size,
                num_workers=num_workers,
                skip_failures=skip_failures,
                **kwargs,
            )
        elif embeddings:
            target_view.compute_embeddings(
                model,
                embeddings_field=embeddings_field,
                batch_size=batch_size,
                num_workers=num_workers,
                skip_failures=skip_failures,
                **kwargs,
            )
        else:
            target_view.apply_model(
                model,
                label_field=label_field,
                confidence_thresh=confidence_thresh,
                store_logits=store_logits,
                batch_size=batch_size,
                num_workers=num_workers,
                skip_failures=skip_failures,
                output_dir=output_dir,
                rel_dir=rel_dir,
                **kwargs,
            )


def _apply_zoo_model_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None
    if has_view or has_selected:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Export the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Export the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Export only the selected samples",
            )
            default_target = "SELECTED_SAMPLES"

        inputs.enum(
            "target",
            target_choices.values(),
            default=default_target,
            view=target_choices,
        )

    target = ctx.params.get("target", default_target)
    target_view = _get_target_view(ctx, target)

    manifest = fozm._load_zoo_models_manifest()

    models_by_tag = defaultdict(set)
    for model in manifest:
        for tag in model.tags or []:
            models_by_tag[tag].add(model.name)

    tag_choices = types.DropdownView(multiple=True)
    for tag in sorted(models_by_tag.keys()):
        tag_choices.add_choice(tag, label=tag)

    inputs.list(
        "tags",
        types.String(),
        default=None,
        required=False,
        label="Tags",
        description="Provide optional tag(s) to filter the available models",
        view=tag_choices,
    )

    tags = ctx.params.get("tags", None)

    if tags:
        model_names = set.intersection(*[models_by_tag[tag] for tag in tags])
    else:
        model_names = set(model.name for model in manifest)

    model_choices = types.AutocompleteView()
    for name in sorted(model_names):
        model_choices.add_choice(name, label=name)

    inputs.enum(
        "model",
        model_choices.values(),
        required=True,
        label="Model",
        description=(
            "The name of a model from the FiftyOne Model Zoo to use to "
            "generate predictions or embeddings"
        ),
        caption="https://docs.voxel51.com/user_guide/model_zoo/models.html",
        view=model_choices,
    )

    model = ctx.params.get("model", None)
    if model is None or model not in model_names:
        return False

    zoo_model = fozm.get_zoo_model(model)

    if zoo_model.has_tag("embeddings"):
        tab_choices = types.TabsView(
            description=(
                "This model exposes embeddings. Would you like to compute "
                "predictions or embeddings?"
            )
        )
        tab_choices.add_choice("PREDICTIONS", label="Predictions")
        tab_choices.add_choice("EMBEDDINGS", label="Embeddings")
        inputs.enum(
            "embeddings",
            tab_choices.values(),
            default="PREDICTIONS",
            view=tab_choices,
        )

    embeddings = ctx.params.get("embeddings", None) == "EMBEDDINGS"

    if embeddings:
        patch_types = (fo.Detection, fo.Detections, fo.Polyline, fo.Polylines)
        patches_fields = list(
            target_view.get_field_schema(embedded_doc_type=patch_types).keys()
        )

        if patches_fields:
            patches_field_choices = types.DropdownView()
            for field in sorted(patches_fields):
                patches_field_choices.add_choice(field, label=field)

            inputs.str(
                "patches_field",
                default=None,
                required=False,
                label="Patches field",
                description=(
                    "An optional sample field defining image patches in each "
                    "sample to embed. If omitted, the full images will be "
                    "embedded"
                ),
                view=patches_field_choices,
            )

        patches_field = ctx.params.get("patches_field", None)

        if patches_field is not None:
            root, _ = target_view._get_label_field_root(patches_field)
            field = target_view.get_field(root, leaf=True)
            schema = field.get_field_schema(ftype=fo.VectorField)
        else:
            schema = target_view.get_field_schema(ftype=fo.VectorField)

        embeddings_field_choices = types.AutocompleteView()
        for field in sorted(schema.keys()):
            embeddings_field_choices.add_choice(field, label=field)

        inputs.str(
            "embeddings_field",
            required=True,
            label="Embeddings field",
            description=(
                "The name of a new or existing field in which to store the "
                "embeddings"
            ),
            view=embeddings_field_choices,
        )
    else:
        label_field_choices = types.AutocompleteView()
        for field in _get_fields_with_type(target_view, fo.Label):
            label_field_choices.add_choice(field, label=field)

        inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "The name of a new or existing field in which to store the "
                "predictions"
            ),
            view=label_field_choices,
        )

        inputs.float(
            "confidence_thresh",
            default=None,
            label="Confidence threshold",
            description=(
                "A confidence threshold to apply to any applicable labels "
                "generated by the model"
            ),
        )

        inputs.bool(
            "store_logits",
            default=False,
            label="Store logits",
            description=(
                "Whether to store logits for the predictions, if the model "
                "supports it"
            ),
        )

    inputs.int(
        "batch_size",
        default=None,
        label="Batch size",
        description=(
            "A batch size to use when performing inference (if applicable)"
        ),
    )

    inputs.int(
        "num_workers",
        default=None,
        label="Num workers",
        description=(
            "The number of workers to use for Torch data loaders "
            "(if applicable)"
        ),
    )

    inputs.bool(
        "skip_failures",
        default=True,
        label="Skip failures",
        description=(
            "Whether to gracefully continue without raising an error "
            "if predictions cannot be generated for a sample"
        ),
    )

    if "segmentation" in (zoo_model.tags or []):
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "output_dir",
            required=False,
            label="Output directory",
            description=(
                "Choose a new or existing directory into which to write the "
                "segmentations. If omitted, the segmentations will be stored "
                "in the database"
            ),
            view=file_explorer,
        )

    return True


def _get_fields_with_type(view, type):
    if issubclass(type, fo.Field):
        return list(view.get_field_schema(ftype=type).keys())

    return list(view.get_field_schema(embedded_doc_type=type).keys())


def _parse_path(ctx, key):
    value = ctx.params.get(key, None)
    return value.get("absolute_path", None) if value else None


def _get_target_view(ctx, target):
    if target == "SELECTED_LABELS":
        return ctx.view.select_labels(labels=ctx.selected_labels)

    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", False)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=False,
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
    p.register(LoadZooDataset)
    p.register(ApplyZooModel)
