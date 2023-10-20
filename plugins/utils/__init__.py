"""
Utility operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import contextlib
import json
import multiprocessing.dummy

import fiftyone as fo
import fiftyone.core.media as fom
import fiftyone.core.metadata as fomm
import fiftyone.core.utils as fou
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.utils.image as foui


class CreateDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="create_dataset",
            label="Create dataset",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        name_prop = inputs.str(
            "name",
            required=False,
            label="Dataset name",
            description=(
                "Choose a name for the dataset. If omitted, a randomly "
                "generated name will be used"
            ),
        )

        name = ctx.params.get("name", None)

        if name and fo.dataset_exists(name):
            name_prop.invalid = True
            name_prop.error_message = f"Dataset {name} already exists"

        inputs.bool(
            "persistent",
            default=True,
            required=True,
            label="Persistent",
            description="Whether to make the dataset persistent",
            view=types.CheckboxView(),
        )

        return types.Property(inputs, view=types.View(label="Create dataset"))

    def execute(self, ctx):
        name = ctx.params.get("name", None)
        persistent = ctx.params.get("persistent", False)

        fo.Dataset(name, persistent=persistent)
        ctx.trigger("open_dataset", dict(dataset=name))


class LoadDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_dataset",
            label="Load dataset",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        sort_by_choices = types.RadioGroup()
        sort_by_choices.add_choice("NAME", label="Name")
        sort_by_choices.add_choice("CREATED_AT", label="Recently created")
        sort_by_choices.add_choice("LAST_LOADED_AT", label="Recently loaded")
        default = "NAME"

        inputs.enum(
            "sort_by",
            sort_by_choices.values(),
            default=default,
            label="Sort by",
            description="Choose how to sort the datasets in the dropdown",
            view=sort_by_choices,
        )
        sort_by = ctx.params.get("sort_by", default).lower()

        info = fo.list_datasets(info=True)
        key = lambda i: (i[sort_by] is not None, i[sort_by])
        reverse = sort_by != "name"

        dataset_choices = types.AutocompleteView()
        for i in sorted(info, key=key, reverse=reverse):
            dataset_choices.add_choice(i["name"], label=i["name"])

        inputs.enum(
            "name",
            dataset_choices.values(),
            required=True,
            label="Dataset name",
            description="The name of a dataset to load",
            view=dataset_choices,
        )

        return types.Property(inputs, view=types.View(label="Load dataset"))

    def execute(self, ctx):
        name = ctx.params["name"]
        ctx.trigger("open_dataset", dict(dataset=name))


class EditDatasetInfo(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="edit_dataset_info",
            label="Edit dataset info",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _dataset_info_inputs(ctx, inputs)

        return types.Property(
            inputs, view=types.View(label="Edit dataset info")
        )

    def execute(self, ctx):
        name = ctx.params.get("name", None)
        description = ctx.params.get("description", None) or None
        persistent = ctx.params.get("persistent", None)
        tags = ctx.params.get("tags", None)
        info = ctx.params.get("info", None)
        app_config = ctx.params.get("app_config", None)
        classes = ctx.params.get("classes", None)
        default_classes = ctx.params.get("default_classes", None)
        mask_targets = ctx.params.get("mask_targets", None)
        default_mask_targets = ctx.params.get("default_mask_targets", None)
        skeletons = ctx.params.get("skeletons", None)
        default_skeleton = ctx.params.get("default_skeleton", None) or None

        if name is not None:
            ctx.dataset.name = name

        if description is not None:
            ctx.dataset.description = description
        elif ctx.dataset.description is not None:
            ctx.dataset.description = None

        if persistent is not None:
            ctx.dataset.persistent = persistent

        if tags is not None:
            ctx.dataset.tags = tags

        if info is not None:
            ctx.dataset.info = json.loads(info)

        if app_config is not None:
            ctx.dataset.app_config = fo.DatasetAppConfig.from_json(app_config)

        if classes is not None:
            ctx.dataset.classes = json.loads(classes)

        if default_classes is not None:
            ctx.dataset.default_classes = json.loads(default_classes)

        if mask_targets is not None:
            ctx.dataset.mask_targets = json.loads(mask_targets)

        if default_mask_targets is not None:
            ctx.dataset.default_mask_targets = json.loads(default_mask_targets)

        if skeletons is not None:
            ctx.dataset.skeletons = {
                field: fo.KeypointSkeleton.from_dict(skeleton)
                for field, skeleton in json.loads(skeletons).items()
            }

        if default_skeleton is not None:
            ctx.dataset.default_skeleton = fo.KeypointSkeleton.from_dict(
                json.loads(default_skeleton)
            )
        elif ctx.dataset.default_skeleton is not None:
            ctx.dataset.default_skeleton = None

        ctx.trigger("reload_dataset")


def _dataset_info_inputs(ctx, inputs):
    num_changed = 0

    ## tabs

    tab_choices = types.TabsView()
    tab_choices.add_choice("BASIC", label="Basic")
    tab_choices.add_choice("INFO", label="Info")
    tab_choices.add_choice("APP_CONFIG", label="App config")
    tab_choices.add_choice("CLASSES", label="Clasess")
    tab_choices.add_choice("MASK_TARGETS", label="Mask targets")
    tab_choices.add_choice("SKELETONS", label="Keypoint skeletons")
    default = "BASIC"
    inputs.enum(
        "tab_choice",
        tab_choices.values(),
        default=default,
        view=tab_choices,
    )
    tab_choice = ctx.params.get("tab_choice", default)

    ## name

    name = ctx.params.get("name", None)
    edited_name = (
        "name" in ctx.params and name is not None and name != ctx.dataset.name
    )
    if edited_name:
        num_changed += 1

    if tab_choice == "BASIC":
        prop = inputs.str(
            "name",
            default=ctx.dataset.name,
            required=True,
            label="Name" + (" (edited)" if edited_name else ""),
            description="The name of the dataset",
        )

        if name and edited_name:
            try:
                _ = fou.to_slug(name)
            except ValueError as e:
                prop.invalid = True
                prop.error_message = str(e)

            if fo.dataset_exists(name):
                prop.invalid = True
                prop.error_message = f"Dataset {name} already exists"

    ## description

    description = ctx.params.get("description", None) or None
    edited_description = (
        "description" in ctx.params
        # can be None
        and description != ctx.dataset.description
    )
    if edited_description:
        num_changed += 1

    if tab_choice == "BASIC":
        inputs.str(
            "description",
            default=ctx.dataset.description,
            required=False,  # can be None
            label="Description" + (" (edited)" if edited_description else ""),
            description="A description for the dataset",
        )

    ## persistent

    persistent = ctx.params.get("persistent", None)
    edited_persistent = (
        "persistent" in ctx.params
        and persistent is not None
        and persistent != ctx.dataset.persistent
    )
    if edited_persistent:
        num_changed += 1

    if tab_choice == "BASIC":
        inputs.bool(
            "persistent",
            default=ctx.dataset.persistent,
            required=True,
            description="Whether the dataset is persistent",
            view=types.CheckboxView(
                label="Persistent" + (" (edited)" if edited_persistent else "")
            ),
        )

    ## tags

    tags = ctx.params.get("tags", None)
    edited_tags = (
        "tags" in ctx.params and tags is not None and tags != ctx.dataset.tags
    )
    if edited_tags:
        num_changed += 1

    if tab_choice == "BASIC":
        inputs.list(
            "tags",
            types.String(),
            default=ctx.dataset.tags,
            required=False,
            label="Tags" + (" (edited)" if edited_tags else ""),
            description="A list of tags for the dataset",
        )

    ## info

    info, valid = _parse_field(ctx, "info", type=dict)
    edited_info = (
        "info" in ctx.params and info is not None and info != ctx.dataset.info
    )
    if edited_info:
        num_changed += 1

    if tab_choice == "INFO":
        inputs.view(
            "info_help",
            view=types.Notice(
                label=(
                    "For more information about dataset info, see: "
                    "https://docs.voxel51.com/user_guide/using_datasets.html#storing-info"
                )
            ),
        )

        prop = inputs.str(
            "info",
            default=_serialize(ctx.dataset.info),
            required=True,
            label="Info" + (" (edited)" if edited_info else ""),
            description="A dict of info associated with the dataset",
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid info"

    ## app_config

    app_config, valid = _parse_field(ctx, "app_config", type=dict)
    if app_config is not None:
        try:
            app_config = fo.DatasetAppConfig.from_dict(app_config)
        except:
            valid = False
    edited_app_config = (
        "app_config" in ctx.params
        and app_config is not None
        and app_config != ctx.dataset.app_config
    )
    if edited_app_config:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        inputs.view(
            "app_config_help",
            view=types.Notice(
                label=(
                    "For more information about dataset App configs, see: "
                    "https://docs.voxel51.com/user_guide/using_datasets.html#dataset-app-config"
                )
            ),
        )

        prop = inputs.str(
            "app_config",
            default=ctx.dataset.app_config.to_json(pretty_print=4),
            required=True,
            label="App config" + (" (edited)" if edited_app_config else ""),
            description=(
                "A DatasetAppConfig that customizes how this dataset is "
                "visualized in the FiftyOne App"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid App config"

    ## classes

    classes, valid = _parse_field(ctx, "classes", type=dict)
    edited_classes = (
        "classes" in ctx.params
        and classes is not None
        and classes != ctx.dataset.classes
    )
    if edited_classes:
        num_changed += 1

    if tab_choice == "CLASSES":
        inputs.view(
            "classes_help",
            view=types.Notice(
                label=(
                    "For more information about class lists, see: "
                    "https://docs.voxel51.com/user_guide/using_datasets.html#storing-class-lists"
                )
            ),
        )

        prop = inputs.str(
            "classes",
            default=_serialize(ctx.dataset.classes),
            required=True,
            label="Classes" + (" (edited)" if edited_classes else ""),
            description=(
                "A dict mapping field names to lists of class label strings for "
                "the corresponding fields of the dataset"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid classes"

    ## default_classes

    default_classes, valid = _parse_field(ctx, "default_classes", type=list)
    edited_default_classes = (
        "default_classes" in ctx.params
        and default_classes is not None
        and default_classes != ctx.dataset.default_classes
    )
    if edited_default_classes:
        num_changed += 1

    if tab_choice == "CLASSES":
        prop = inputs.str(
            "default_classes",
            default=_serialize(ctx.dataset.default_classes),
            required=True,
            label="Default classes"
            + (" (edited)" if edited_default_classes else ""),
            description=(
                "A list of class label strings for all label fields of this "
                "dataset that do not have customized classes defined"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid default classes"

    ## mask_targets

    mask_targets, valid = _parse_field(ctx, "mask_targets", type=dict)
    edited_mask_targets = (
        "mask_targets" in ctx.params
        and mask_targets is not None
        and mask_targets != ctx.dataset.mask_targets
    )
    if edited_mask_targets:
        num_changed += 1

    if tab_choice == "MASK_TARGETS":
        inputs.view(
            "mask_targets_help",
            view=types.Notice(
                label=(
                    "For more information about mask targets, see: "
                    "https://docs.voxel51.com/user_guide/using_datasets.html#storing-mask-targets"
                )
            ),
        )

        prop = inputs.str(
            "mask_targets",
            default=_serialize(ctx.dataset.mask_targets),
            required=True,
            label="Mask targets"
            + (" (edited)" if edited_mask_targets else ""),
            description=(
                "A dict mapping field names to mask target dicts, each of "
                "which defines a mapping between pixel values (2D masks) or "
                "RGB hex strings (3D masks) and label strings for the "
                "segmentation masks in the corresponding field of the dataset"
            ),
            view=types.CodeView(),
        )
        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid mask targets"

    ## default_mask_targets

    default_mask_targets, valid = _parse_field(
        ctx, "default_mask_targets", type=dict
    )
    edited_default_mask_targets = (
        "default_mask_targets" in ctx.params
        and default_mask_targets is not None
        and default_mask_targets != ctx.dataset.default_mask_targets
    )
    if edited_default_mask_targets:
        num_changed += 1

    if tab_choice == "MASK_TARGETS":
        prop = inputs.str(
            "default_mask_targets",
            default=_serialize(ctx.dataset.default_mask_targets),
            required=True,
            label="Default mask targets"
            + (" (edited)" if edited_default_mask_targets else ""),
            description=(
                "A dict defining a default mapping between pixel values "
                "(2D masks) or RGB hex strings (3D masks) and label strings "
                "for the segmentation masks of all label fields of this "
                "dataset that do not have customized mask targets"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid default mask targets"

    ## skeletons

    skeletons, valid = _parse_field(ctx, "skeletons", type=dict)
    if skeletons is not None:
        try:
            skeletons = {
                field: fo.KeypointSkeleton.from_dict(skeleton)
                for field, skeleton in skeletons.items()
            }
        except:
            valid = False
    edited_skeletons = (
        "skeletons" in ctx.params
        and skeletons is not None
        and skeletons != ctx.dataset.skeletons
    )
    if edited_skeletons:
        num_changed += 1

    if tab_choice == "SKELETONS":
        inputs.view(
            "skeletons_help",
            view=types.Notice(
                label=(
                    "For more information about keypoint skeletons, see: "
                    "https://docs.voxel51.com/user_guide/using_datasets.html#storing-keypoint-skeletons"
                )
            ),
        )

        if ctx.dataset.skeletons is not None:
            default = _serialize(
                {
                    field: skeleton.to_dict()
                    for field, skeleton in ctx.dataset.skeletons.items()
                }
            )
        else:
            default = None

        prop = inputs.str(
            "skeletons",
            default=default,
            required=True,
            label="Skeletons" + (" (edited)" if edited_skeletons else ""),
            description=(
                "A dict mapping field names to KeypointSkeleton instances, "
                "each of which defines the semantic labels and point "
                "connectivity for the Keypoint instances in the corresponding "
                "field of the dataset"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid skeletons"

    ## default_skeleton

    default_skeleton, valid = _parse_field(ctx, "default_skeleton", type=dict)
    if default_skeleton is not None:
        try:
            default_skeleton = fo.KeypointSkeleton.from_dict(default_skeleton)
        except:
            valid = False
    edited_default_skeleton = (
        "default_skeleton" in ctx.params
        # can be None
        and default_skeleton != ctx.dataset.default_skeleton
    )
    if edited_default_skeleton:
        num_changed += 1

    if tab_choice == "SKELETONS":
        if ctx.dataset.default_skeleton is not None:
            default = _serialize(ctx.dataset.default_skeleton.to_dict())
        else:
            default = None

        prop = inputs.str(
            "default_skeleton",
            default=default,
            required=False,  # can be None
            label="Default skeleton"
            + (" (edited)" if edited_default_skeleton else ""),
            description=(
                "A default KeypointSkeleton defining the semantic labels and "
                "point connectivity for all Keypoint fields of this dataset "
                "that do not have customized skeletons"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid default skeleton"

    ## edits

    inputs.str(
        "edits",
        view=types.Header(
            label="Edits",
            description="Any changes you've made above are summarized here",
            divider=True,
        ),
    )

    if num_changed > 0:
        view = types.Warning(
            label=f"You are about to edit {num_changed} fields"
        )
    else:
        view = types.Notice(label="You have not made any edits")

    prop = inputs.view("status", view)
    if num_changed == 0:
        prop.invalid = True


def _serialize(value):
    if value is None:
        return None

    return json.dumps(value, indent=4)


def _parse_field(ctx, name, type=dict, default=None):
    value = ctx.params.get(name, None)
    valid = True

    if value:
        try:
            value = json.loads(value)
            assert isinstance(value, type)
        except:
            value = default
            valid = False
    else:
        value = default

    return value, valid


class RenameDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="rename_dataset",
            label="Rename dataset",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        dataset_choices = types.AutocompleteView()
        for name in sorted(fo.list_datasets()):
            dataset_choices.add_choice(name, label=name)

        inputs.str(
            "name",
            default=ctx.dataset.name,
            required=True,
            label="Dataset name",
            description="The name of a dataset to delete",
            view=dataset_choices,
        )

        new_name_prop = inputs.str(
            "new_name",
            required=True,
            label="New name",
            description="Choose a new name for the dataset",
        )

        new_name = ctx.params.get("new_name", None)

        if new_name and fo.dataset_exists(new_name):
            new_name_prop.invalid = True
            new_name_prop.error_message = f"Dataset {new_name} already exists"

        return types.Property(inputs, view=types.View(label="Rename dataset"))

    def execute(self, ctx):
        name = ctx.params["name"]
        new_name = ctx.params["new_name"]

        if ctx.dataset.name == name:
            ctx.dataset.name = new_name
            ctx.trigger("open_dataset", dict(name=new_name))
        else:
            dataset = fo.load_dataset(name)
            dataset.name = new_name


class DeleteDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_dataset",
            label="Delete dataset",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        dataset_choices = types.AutocompleteView()
        for name in sorted(fo.list_datasets()):
            dataset_choices.add_choice(name, label=name)

        inputs.str(
            "name",
            default=ctx.dataset.name,
            required=True,
            label="Dataset name",
            description="The name of the dataset to delete",
            view=dataset_choices,
        )

        return types.Property(inputs, view=types.View(label="Delete dataset"))

    def execute(self, ctx):
        name = ctx.params.get("name", None)

        if name == ctx.dataset.name:
            ctx.trigger("open_dataset", dict(dataset=None))

        fo.delete_dataset(name)


class ComputeMetadata(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_metadata",
            label="Compute metadata",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
            execute_as_generator=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _compute_metadata_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(
            inputs, view=types.View(label="Compute metadata")
        )

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        overwrite = ctx.params.get("overwrite", False)
        num_workers = ctx.params.get("num_workers", None)
        delegate = ctx.params.get("delegate", False)

        view = _get_target_view(ctx, target)

        if delegate:
            view.compute_metadata(overwrite=overwrite, num_workers=num_workers)
        else:
            for update in _compute_metadata_generator(
                ctx, view, overwrite=overwrite, num_workers=num_workers
            ):
                yield update

        yield ctx.trigger("reload_dataset")


def _compute_metadata_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None
    if has_view or has_selected:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Compute metadata for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Compute metadata for the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Compute metadata for the selected samples",
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

    if target == "SELECTED_SAMPLES":
        target_str = "selection"
    elif target == "CURRENT_VIEW":
        target_str = "current view"
    else:
        target_str = "dataset"

    inputs.bool(
        "overwrite",
        default=False,
        label="Recompute metadata for samples that already have it?",
        view=types.CheckboxView(),
    )

    overwrite = ctx.params.get("overwrite", False)

    if overwrite:
        n = len(target_view)
        if n > 0:
            label = f"Found {n} samples to (re)compute metadata for"
        else:
            label = f"Your {target_str} is empty"
    else:
        n = len(target_view.exists("metadata", False))
        if n > 0:
            label = f"Found {n} samples that need metadata computed"
        else:
            label = (
                f"All samples in your {target_str} already have metadata "
                "computed"
            )

    if n > 0:
        inputs.view("status", types.Notice(label=label))
    else:
        status = inputs.view("status", types.Warning(label=label))
        status.invalid = True
        return False

    inputs.int(
        "num_workers",
        default=None,
        required=False,
        label="Num workers",
        description="An optional number of workers to use",
    )

    return True


def _compute_metadata_generator(
    ctx, sample_collection, overwrite=False, num_workers=None
):
    # @todo switch to this when `fiftyone==0.22.2` is released
    # num_workers = fou.recommend_thread_pool_workers(num_workers)

    if hasattr(fou, "recommend_thread_pool_workers"):
        num_workers = fou.recommend_thread_pool_workers(num_workers)
    elif num_workers is None:
        num_workers = fo.config.max_thread_pool_workers or 8

    if not overwrite:
        sample_collection = sample_collection.exists("metadata", False)

    ids, filepaths, media_types = sample_collection.values(
        ["id", "filepath", "_media_type"],
        _allow_missing=True,
    )

    inputs = list(zip(ids, filepaths, media_types))
    num_total = len(inputs)

    if num_total == 0:
        return

    view = sample_collection.select_fields()

    num_computed = 0
    with contextlib.ExitStack() as exit_context:
        pb = fou.ProgressBar(total=num_total)
        exit_context.enter_context(pb)

        if num_workers > 1:
            pool = multiprocessing.dummy.Pool(processes=num_workers)
            exit_context.enter_context(pool)
            tasks = pool.imap_unordered(_do_compute_metadata, inputs)
        else:
            tasks = map(_do_compute_metadata, inputs)

        for sample_id, metadata in pb(tasks):
            sample = view[sample_id]
            sample.metadata = metadata
            sample.save()

            num_computed += 1
            if num_computed % 10 == 0:
                progress = num_computed / num_total
                label = f"Computed {num_computed} of {num_total}"
                yield _set_progress(ctx, progress, label=label)


def _do_compute_metadata(args):
    sample_id, filepath, media_type = args
    metadata = _compute_sample_metadata(
        filepath, media_type, skip_failures=True
    )
    return sample_id, metadata


def _compute_sample_metadata(filepath, media_type, skip_failures=False):
    if not skip_failures:
        return _get_metadata(filepath, media_type)

    try:
        return _get_metadata(filepath, media_type)
    except:
        return None


def _get_metadata(filepath, media_type):
    if media_type == fom.IMAGE:
        metadata = fomm.ImageMetadata.build_for(filepath)
    elif media_type == fom.VIDEO:
        metadata = fomm.VideoMetadata.build_for(filepath)
    else:
        metadata = fomm.Metadata.build_for(filepath)

    return metadata


class GenerateThumbnails(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="generate_thumbnails",
            label="Generate thumbnails",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _generate_thumbnails_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(
            inputs, view=types.View(label="Generate thumbnails")
        )

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        width = ctx.params.get("width", None)
        height = ctx.params.get("height", None)
        thumbnail_path = ctx.params["thumbnail_path"]
        output_dir = ctx.params["output_dir"]["absolute_path"]
        overwrite = ctx.params.get("overwrite", False)
        num_workers = ctx.params.get("num_workers", None)
        delegate = ctx.params.get("delegate", False)

        view = _get_target_view(ctx, target)

        if not overwrite:
            view = view.exists(thumbnail_path, False)

        size = (width or -1, height or -1)

        # No multiprocessing allowed when running synchronously
        if not delegate:
            num_workers = 1

        foui.transform_images(
            view,
            size=size,
            output_field=thumbnail_path,
            output_dir=output_dir,
            num_workers=num_workers,
            skip_failures=True,
        )

        if thumbnail_path not in ctx.dataset.app_config.media_fields:
            ctx.dataset.app_config.media_fields.append(thumbnail_path)

        if ctx.dataset.app_config.grid_media_field != thumbnail_path:
            ctx.dataset.app_config.grid_media_field = thumbnail_path

        ctx.dataset.save()

        ctx.trigger("reload_dataset")


def _generate_thumbnails_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None
    if has_view or has_selected:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Generate thumbnails for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Generate thumbnails for the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Generate thumbnails for the selected samples",
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

    if target == "SELECTED_SAMPLES":
        target_str = "selection"
    elif target == "CURRENT_VIEW":
        target_str = "current view"
    else:
        target_str = "dataset"

    field_selector = types.AutocompleteView()
    for field in _get_fields_with_type(target_view, fo.StringField):
        if field == "filepath":
            continue

        field_selector.add_choice(field, label=field)

    inputs.str(
        "thumbnail_path",
        required=True,
        label="Thumbnail field",
        description=(
            "Provide the name of a new or existing field in which to "
            "store the thumbnail paths"
        ),
        view=field_selector,
    )

    thumbnail_path = ctx.params.get("thumbnail_path", None)

    if thumbnail_path is None:
        return False

    file_explorer = types.FileExplorerView(
        choose_dir=True,
        button_label="Choose a directory...",
    )
    inputs.file(
        "output_dir",
        required=True,
        label="Output directory",
        description=(
            "Choose a new or existing directory into which to write the "
            "generated thumbnails"
        ),
        view=file_explorer,
    )
    output_dir = _parse_path(ctx, "output_dir")

    if output_dir is None:
        return False

    inputs.bool(
        "overwrite",
        default=False,
        label=(
            f"Regenerate thumbnails for samples that already have their "
            f"{thumbnail_path} populated?"
        ),
        view=types.CheckboxView(),
    )

    overwrite = ctx.params.get("overwrite", False)

    if overwrite:
        n = len(target_view)
        if n > 0:
            label = f"Found {n} samples to (re)generate thumbnails for"
        else:
            label = f"Your {target_str} is empty"
    else:
        n = len(target_view.exists("thumbnail_path", False))
        if n > 0:
            label = f"Found {n} samples that need thumbnails generated"
        else:
            label = (
                f"All samples in your {target_str} already have "
                "thumbnails generated"
            )

    if n > 0:
        inputs.view("status1", types.Notice(label=label))
    else:
        status1 = inputs.view("status1", types.Warning(label=label))
        status1.invalid = True
        return False

    inputs.str(
        "size",
        view=types.Header(
            label="Thumbnail size",
            description=(
                "Provide a (width, height) for each thumbnails. "
                "Either dimension can be omitted, in which case the aspect "
                "ratio is preserved"
            ),
            divider=True,
        ),
    )

    inputs.int(
        "width",
        required=False,
        label="Width",
        view=types.View(space=6),
    )

    inputs.int(
        "height",
        required=False,
        label="Height",
        view=types.View(space=6),
    )

    width = ctx.params.get("width", None)
    height = ctx.params.get("height", None)

    if width is None and height is None:
        status2 = inputs.view(
            "status2",
            types.Warning(label="You must provide a width and/or height"),
        )
        status2.invalid = True
        return False

    inputs.int(
        "num_workers",
        default=None,
        required=False,
        label="Num workers",
        description="An optional number of workers to use",
    )

    return True


def _get_fields_with_type(view, type):
    if issubclass(type, fo.Field):
        return view.get_field_schema(ftype=type).keys()

    return view.get_field_schema(embedded_doc_type=type).keys()


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


def _set_progress(ctx, progress, label=None):
    # https://github.com/voxel51/fiftyone/pull/3516
    # return ctx.trigger("set_progress", dict(progress=progress, label=label))

    loading = types.Object()
    loading.float("progress", view=types.ProgressView(label=label))
    return ctx.trigger(
        "show_output",
        dict(
            outputs=types.Property(loading).to_json(),
            results={"progress": progress},
        ),
    )


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
    p.register(CreateDataset)
    p.register(LoadDataset)
    p.register(EditDatasetInfo)
    p.register(RenameDataset)
    p.register(DeleteDataset)
    p.register(ComputeMetadata)
    p.register(GenerateThumbnails)
