"""
FiftyOne Zoo operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict
from packaging.version import Version

import fiftyone as fo
import fiftyone.constants as foc
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone.utils.github import GitHubRepository
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
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _load_zoo_dataset_inputs(ctx, inputs)

        view = types.View(label="Load zoo dataset")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        name = ctx.params.get("name")
        splits = ctx.params.get("splits", None)
        label_field = ctx.params.get("label_field", None)
        dataset_name = ctx.params.get("dataset_name", None)
        kwargs = ctx.params.get("kwargs", {})

        dataset_name = _get_zoo_dataset_name(ctx)

        dataset = foz.load_zoo_dataset(
            name,
            splits=splits,
            label_field=label_field,
            dataset_name=dataset_name,
            drop_existing_dataset=True,
            persistent=True,
            **kwargs,
        )

        if not ctx.delegated:
            ctx.trigger("open_dataset", dict(dataset=dataset.name))


def _supports_remote_datasets():
    return hasattr(fozd, "_list_zoo_datasets")


def _get_allowed_dataset_licenses(ctx, inputs):
    license = ctx.secrets.get("FIFTYONE_ZOO_ALLOWED_DATASET_LICENSES", None)
    if license is None:
        return None

    licenses = license.split(",")

    inputs.view(
        "licenses",
        types.Notice(
            label=(
                f"Only datasets with licenses {licenses} will be available "
                "below"
            )
        ),
    )

    return licenses


def _get_zoo_datasets(ctx, inputs):
    # @todo can remove this if we require `fiftyone>=1.4.0`
    if Version(foc.VERSION) >= Version("1.4.0"):
        licenses = _get_allowed_dataset_licenses(ctx, inputs)
        kwargs = dict(license=licenses)
    else:
        licenses = None
        kwargs = {}

    if _supports_remote_datasets():
        zoo_datasets = fozd._list_zoo_datasets(**kwargs)
        return zoo_datasets, licenses

    # Can remove this code path if we require fiftyone>=1.0.0
    # pylint: disable=no-value-for-parameter
    datasets_by_source = fozd._get_zoo_datasets()
    all_sources, _ = fozd._get_zoo_dataset_sources()

    zoo_datasets = {}
    for source in all_sources:
        for name, zoo_dataset_cls in datasets_by_source[source].items():
            if name not in zoo_datasets:
                zoo_datasets[name] = zoo_dataset_cls()

    return zoo_datasets, licenses


def _get_builtin_zoo_dataset(ctx, inputs):
    zoo_datasets, licenses = _get_zoo_datasets(ctx, inputs)

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

    if _supports_remote_datasets():
        description = (
            "The name of the dataset to load from the "
            "[FiftyOne Dataset Zoo](https://docs.voxel51.com/user_guide/dataset_zoo/datasets.html). "
            "Also includes any "
            "[remote datasets](https://docs.voxel51.com/dataset_zoo/remote.html) "
            "you've already downloaded"
        )
        caption = None
    else:
        # Can remove this code path if we require fiftyone>=1.0.0
        description = (
            "The name of the dataset to load from the FiftyOne Dataset Zoo"
        )
        caption = "https://docs.voxel51.com/user_guide/model_zoo/models.html"

    prop = inputs.enum(
        "name",
        dataset_choices.values(),
        required=True,
        label="Zoo dataset",
        description=description,
        caption=caption,
        view=dataset_choices,
    )

    if tags and not dataset_names:
        prop.error_message = (
            "There are no datasets with all the tags you've requested"
        )
        prop.invalid = True

    if licenses is not None and not dataset_names:
        prop.error_message = "There are no datasets with allowed licenses"
        prop.invalid = True

    name = ctx.params.get("name", None)
    if name is None or name not in zoo_datasets:
        return None, None

    zoo_dataset = zoo_datasets[name]

    return zoo_dataset, licenses


def _get_remote_zoo_dataset(ctx, inputs):
    licenses = _get_allowed_dataset_licenses(ctx, inputs)

    instructions = """
Provide a [location](https://docs.voxel51.com/dataset_zoo/remote.html) to
download the dataset from, which can be:

-   A GitHub repo URL like `https://github.com/<user>/<repo>`
-   A GitHub ref like
`https://github.com/<user>/<repo>/tree/<branch>` or
`https://github.com/<user>/<repo>/commit/<commit>`
-   A GitHub ref string like `<user>/<repo>[/<ref>]`
"""

    inputs.str(
        "remote_instructions",
        default=instructions.strip(),
        view=types.MarkdownView(read_only=True),
    )

    prop = inputs.str("name", required=True)

    name = ctx.params.get("name", None)
    if not name:
        return None, None

    try:
        GitHubRepository(name)
    except:
        prop.invalid = True
        prop.error_message = f"{name} is not a valid GitHub repo or identifier"
        return None, None

    try:
        zoo_dataset = fozd.get_zoo_dataset(name)
        return zoo_dataset, licenses
    except Exception as e:
        prop.invalid = True
        prop.error_message = str(e)
        return None, None


def _load_zoo_dataset_inputs(ctx, inputs):
    if _supports_remote_datasets():
        tab_choices = types.TabsView()
        tab_choices.add_choice("BUILTIN", label="Builtin")
        tab_choices.add_choice("REMOTE", label="Remote")
        inputs.enum(
            "tab",
            tab_choices.values(),
            default="BUILTIN",
            view=tab_choices,
        )
        tab = ctx.params.get("tab", "REMOTE")

        if tab == "REMOTE":
            zoo_dataset, licenses = _get_remote_zoo_dataset(ctx, inputs)
        else:
            zoo_dataset, licenses = _get_builtin_zoo_dataset(ctx, inputs)
    else:
        # Can remove this code path if we require fiftyone>=1.0.0
        zoo_dataset, licenses = _get_builtin_zoo_dataset(ctx, inputs)

    if zoo_dataset is None:
        return False

    if licenses is not None:
        license = zoo_dataset.license

        if license is None:
            prop = inputs.view(
                "created",
                types.Error(
                    label=(
                        f"Cannot load dataset '{zoo_dataset.name}' because "
                        "its license is unknown"
                    )
                ),
            )
            prop.invalid = True

            return False

        if not set(licenses).intersection(license.split(",")):
            prop = inputs.view(
                "created",
                types.Error(
                    label=(
                        f"Cannot load dataset '{zoo_dataset.name}' because "
                        f"its license '{license}' is not allowed"
                    )
                ),
            )
            prop.invalid = True

            return False

    kwargs = types.Object()

    _get_source_dir(ctx, kwargs, zoo_dataset)

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

    _partial_download_inputs(ctx, kwargs, zoo_dataset)

    inputs.define_property("kwargs", kwargs)

    inputs.str(
        "label_field",
        default=None,
        required=False,
        label="Label field",
        description=(
            "The label field (or prefix, if the dataset contains multiple "
            "label fields) in which to store the dataset's labels. By "
            "default, this is `ground_truth` if the dataset contains a single "
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

    dataset_name = _get_zoo_dataset_name(ctx, zoo_dataset)

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


def _get_zoo_dataset_name(ctx, zoo_dataset=None):
    dataset_name = ctx.params.get("dataset_name", None)

    if dataset_name:
        return dataset_name

    if zoo_dataset is None:
        return None

    name = zoo_dataset.name

    splits = ctx.params.get("splits", None)
    if splits:
        name += "-" + "-".join(splits)

    max_samples = ctx.params.get("max_samples", None)
    if max_samples:
        name += "-" + str(max_samples)

    return name


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
        supported_label_types = ("detections", "segmentations")
        default = "only detections"
        id_type = "COCO"
        only_matching = True
    elif "open-images" in name:
        supported_label_types = (
            "detections",
            "classifications",
            "relationships",
            "segmentations",
        )
        default = "all label types"
        id_type = "Open Images"
        only_matching = True
    elif "activitynet" in name:
        supported_label_types = None
        id_type = None
        only_matching = False
    else:
        return

    if supported_label_types is not None:
        label_type_choices = types.DropdownView(multiple=True)
        for field in supported_label_types:
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
            "Optional required class(es) to load. If provided, only samples "
            "containing at least one instance of a specified class will be "
            "loaded"
        ),
        view=types.AutocompleteView(multiple=True),
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
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
            allow_distributed_execution=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _apply_zoo_model_inputs(ctx, inputs)

        view = types.View(label="Apply zoo model")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        model = ctx.params["model"]
        source = ctx.params.get("source", None)
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

        # @todo can remove this if we require `fiftyone>=1.8.0`
        if Version(foc.VERSION) >= Version("1.8.0"):
            target_view = ctx.target_view()
        else:
            target_view = _get_target_view(ctx, target)

        # @todo can remove this if we require `fiftyone>=1.4.0`
        kwargs = {}
        if Version(foc.VERSION) >= Version("1.4.0"):
            zoo_model = foz.get_zoo_model(model)
            if isinstance(zoo_model, foz.RemoteZooModel):
                kwargs = ctx.params.get("remote_params", {})
                zoo_model.parse_parameters(ctx, kwargs)

        if source is not None:
            model = foz.load_zoo_model(source, model_name=model, **kwargs)
        else:
            model = foz.load_zoo_model(model, **kwargs)

        # No multiprocessing allowed when running synchronously
        if not ctx.delegated:
            num_workers = 0

        if embeddings and patches_field is not None:
            target_view.compute_patch_embeddings(
                model,
                patches_field,
                embeddings_field=embeddings_field,
                batch_size=batch_size,
                num_workers=num_workers,
                skip_failures=skip_failures,
            )
        elif embeddings:
            target_view.compute_embeddings(
                model,
                embeddings_field=embeddings_field,
                batch_size=batch_size,
                num_workers=num_workers,
                skip_failures=skip_failures,
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
            )

        if not ctx.delegated:
            ctx.trigger("reload_dataset")


def _supports_remote_models():
    return hasattr(fozm, "_list_zoo_models")


def _get_allowed_model_licenses(ctx, inputs):
    license = ctx.secrets.get("FIFTYONE_ZOO_ALLOWED_MODEL_LICENSES", None)
    if license is None:
        return None

    licenses = license.split(",")

    inputs.view(
        "licenses",
        types.Notice(
            label=(
                f"Only models with licenses {licenses} will be available below"
            )
        ),
    )

    return licenses


def _get_remote_zoo_model_source(ctx, inputs):
    instructions = """
Provide a [location](https://docs.voxel51.com/model_zoo/remote.html) to load
the model from, which can be:

-   A GitHub repo URL like `https://github.com/<user>/<repo>`
-   A GitHub ref like
`https://github.com/<user>/<repo>/tree/<branch>` or
`https://github.com/<user>/<repo>/commit/<commit>`
-   A GitHub ref string like `<user>/<repo>[/<ref>]`
"""

    inputs.str(
        "remote_instructions",
        default=instructions.strip(),
        view=types.MarkdownView(read_only=True),
    )

    prop = inputs.str("source", required=True)

    source = ctx.params.get("source", None)
    if not source:
        return None

    try:
        GitHubRepository(source)
    except:
        prop.invalid = True
        prop.error_message = (
            f"{source} is not a valid GitHub repo or identifier"
        )
        return None

    try:
        fozm.register_zoo_model_source(source)
    except Exception as e:
        prop.invalid = True
        prop.error_message = str(e)
        return None

    return source


def _apply_zoo_model_inputs(ctx, inputs):
    # @todo can remove this if we require `fiftyone>=1.8.0`
    if Version(foc.VERSION) >= Version("1.8.0"):
        target_prop = inputs.view_target(
            ctx,
            action_description="Apply model to",
            allow_selected_labels=True,
        )
        target_view = ctx.target_view()
    else:
        has_view = ctx.view != ctx.dataset.view()
        has_selected = bool(ctx.selected)
        default_target = None
        if has_view or has_selected:
            target_choices = types.RadioGroup()
            target_choices.add_choice(
                "DATASET",
                label="Entire dataset",
                description="Apply model to the entire dataset",
            )

            if has_view:
                target_choices.add_choice(
                    "CURRENT_VIEW",
                    label="Current view",
                    description="Apply model to the current view",
                )
                default_target = "CURRENT_VIEW"

            if has_selected:
                target_choices.add_choice(
                    "SELECTED_SAMPLES",
                    label="Selected samples",
                    description="Apply model to only the selected samples",
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

    if _supports_remote_models():
        tab_choices = types.TabsView()
        tab_choices.add_choice("BUILTIN", label="Builtin")
        tab_choices.add_choice("REMOTE", label="Remote")
        inputs.enum(
            "tab",
            tab_choices.values(),
            default="BUILTIN",
            view=tab_choices,
        )
        tab = ctx.params.get("tab", "REMOTE")

        # @todo can remove this if we require `fiftyone>=1.4.0`
        if Version(foc.VERSION) >= Version("1.4.0"):
            licenses = _get_allowed_model_licenses(ctx, inputs)
            kwargs = dict(license=licenses)
        else:
            licenses = None
            kwargs = {}

        if tab == "REMOTE":
            source = _get_remote_zoo_model_source(ctx, inputs)
            if source is None:
                return False

            manifest = fozm._list_zoo_models(source=source, **kwargs)
        else:
            source = None
            manifest = fozm._list_zoo_models(**kwargs)
    else:
        # Can remove this code path if we require fiftyone>=1.0.0
        source = None
        licenses = None
        manifest = fozm._load_zoo_models_manifest()

    # pylint: disable=no-member
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

    if licenses is not None:
        _licenses = set(licenses)
        model_names = set(
            model.name
            for model in manifest
            if model.license is not None
            and _licenses.intersection(model.license.split(","))
        )

    model_choices = types.AutocompleteView()
    for name in sorted(model_names):
        model_choices.add_choice(name, label=name)

    if _supports_remote_models():
        if source is not None:
            description = f"The name of a model from {source} to apply"
        else:
            description = (
                "The name of a model from the "
                "[FiftyOne Model Zoo](https://docs.voxel51.com/user_guide/model_zoo/models.html) "
                "to apply. Also includes models from any "
                "[remote sources](https://docs.voxel51.com/model_zoo/remote.html) "
                "you've already registered"
            )
        caption = None
    else:
        # Can remove this code path if we require fiftyone>=1.0.0
        description = (
            "The name of a model from the FiftyOne Model Zoo to apply"
        )
        caption = "https://docs.voxel51.com/user_guide/model_zoo/models.html"

    prop = inputs.enum(
        "model",
        model_choices.values(),
        required=True,
        label="Model",
        description=description,
        caption=caption,
        view=model_choices,
    )

    if tags and not model_names:
        prop.error_message = (
            "There are no models with all the tags you've requested"
        )
        prop.invalid = True

    if licenses is not None and not model_names:
        prop.error_message = "There are no models with allowed licenses"
        prop.invalid = True

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
        patches_fields = _get_label_fields(target_view, patch_types)

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
            fields = list(field.get_field_schema(ftype=fo.VectorField).keys())
        else:
            fields = _get_sample_fields(target_view, fo.VectorField)

        embeddings_field_choices = types.AutocompleteView()
        for field in sorted(fields):
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
        # @todo can remove this if we require `fiftyone>=1.4.0`
        if Version(foc.VERSION) >= Version("1.4.0"):
            if isinstance(zoo_model, foz.RemoteZooModel):
                prop = zoo_model.resolve_input(ctx)
                if prop is not None:
                    inputs.add_property("remote_params", prop)

        label_field_choices = types.AutocompleteView()
        for field in _get_label_fields(target_view, fo.Label):
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


def register(p):
    p.register(LoadZooDataset)
    p.register(ApplyZooModel)
