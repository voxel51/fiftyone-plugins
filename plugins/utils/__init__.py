"""
Utility operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict
import json

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

import multiprocessing
from packaging.requirements import Requirement

import fiftyone as fo
import fiftyone.constants as foc
import fiftyone.core.media as fom
import fiftyone.core.metadata as fomm
import fiftyone.core.utils as fou
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.utils.image as foui
import fiftyone.plugins as fop
import fiftyone.zoo as foz
import fiftyone.zoo.datasets as fozd
import fiftyone.zoo.models as fozm


class CreateDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="create_dataset",
            label="Create dataset",
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
        description = ctx.params.get("description", None)
        persistent = ctx.params.get("persistent", None)
        info = ctx.params.get("info", None)
        app_config = ctx.params.get("app_config", None)
        classes = ctx.params.get("classes", None)
        default_classes = ctx.params.get("default_classes", None)
        mask_targets = ctx.params.get("mask_targets", None)
        default_mask_targets = ctx.params.get("default_mask_targets", None)
        skeletons = ctx.params.get("skeletons", None)
        default_skeleton = ctx.params.get("default_skeleton", None)

        if name is not None:
            ctx.dataset.name = name

        if description is not None:
            ctx.dataset.description = description

        if persistent is not None:
            ctx.dataset.persistent = persistent

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
                field: fo.KeypointSkeleton.from_json(skeleton)
                for field, skeleton in json.loads(skeletons).items()
            }

        if default_skeleton is not None:
            ctx.dataset.default_skeleton = fo.KeypointSkeleton.from_json(
                json.loads(default_skeleton)
            )

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
    edited_name = name != ctx.dataset.name

    if tab_choice == "BASIC":
        name_prop = inputs.str(
            "name",
            default=ctx.dataset.name,
            required=True,
            label="Name" + (" (edited)" if edited_name else ""),
            description="The name of the dataset",
        )
    else:
        name_prop = None

    if edited_name:
        if name and fo.dataset_exists(name) and name_prop is not None:
            name_prop.invalid = True
            name_prop.error_message = f"Dataset {name} already exists"
        else:
            num_changed += 1

    ## description

    description = ctx.params.get("description", None) or None
    edited_description = description != ctx.dataset.description

    if tab_choice == "BASIC":
        inputs.str(
            "description",
            default=ctx.dataset.description,
            required=False,
            label="Description" + (" (edited)" if edited_description else ""),
            description="A description for the dataset",
        )

    if edited_description:
        num_changed += 1

    ## persistent

    persistent = ctx.params.get("persistent", None)
    edited_persistent = persistent != ctx.dataset.persistent

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

    if edited_persistent:
        num_changed += 1

    ## info

    info, valid = _parse_field(ctx, "info", default={})
    edited_info = info != ctx.dataset.info

    if tab_choice == "INFO":
        info_prop = inputs.str(
            "info",
            default=json.dumps(ctx.dataset.info, indent=4),
            required=True,
            label="Info" + (" (edited)" if edited_info else ""),
            description="A dict of info associated with the dataset",
            view=types.CodeView(),
        )
    else:
        info_prop = None

    if edited_info:
        if not valid and info_prop is not None:
            info_prop.invalid = True
            info_prop.error_message = "Invalid info"
        else:
            num_changed += 1

    ## app_config

    app_config, valid = _parse_field(ctx, "app_config", default={})
    edited_app_config = (
        fo.DatasetAppConfig.from_dict(app_config) != ctx.dataset.app_config
    )

    if tab_choice == "APP_CONFIG":
        app_config_prop = inputs.str(
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
    else:
        app_config_prop = None

    if edited_app_config:
        if not valid and app_config_prop is not None:
            app_config_prop.invalid = True
            app_config_prop.error_message = "Invalid App config"
        else:
            num_changed += 1

    ## classes

    classes, valid = _parse_field(ctx, "classes", default={})
    edited_classes = classes != ctx.dataset.classes

    if tab_choice == "CLASSES":
        classes_prop = inputs.str(
            "classes",
            default=json.dumps(ctx.dataset.classes, indent=4),
            required=True,
            label="Classes" + (" (edited)" if edited_classes else ""),
            description=(
                "A dict mapping field names to lists of class label strings for "
                "the corresponding fields of the dataset"
            ),
            view=types.CodeView(),
        )
    else:
        classes_prop = None

    if edited_classes:
        if not valid and classes_prop is not None:
            classes_prop.invalid = True
            classes_prop.error_message = "Invalid classes"
        else:
            num_changed += 1

    ## default_classes

    default_classes, valid = _parse_field(
        ctx, "default_classes", type=list, default=[]
    )
    edited_default_classes = default_classes != ctx.dataset.default_classes

    if tab_choice == "CLASSES":
        default_classes_prop = inputs.str(
            "default_classes",
            default=json.dumps(ctx.dataset.default_classes, indent=4),
            required=True,
            label="Default classes"
            + (" (edited)" if edited_default_classes else ""),
            description=(
                "A list of class label strings for all label fields of this "
                "dataset that do not have customized classes defined"
            ),
            view=types.CodeView(),
        )
    else:
        default_classes_prop = None

    if edited_default_classes:
        if not valid and default_classes_prop is not None:
            default_classes_prop.invalid = True
            default_classes_prop.error_message = "Invalid default classes"
        else:
            num_changed += 1

    ## mask_targets

    mask_targets, valid = _parse_field(ctx, "mask_targets", default={})
    edited_mask_targets = mask_targets != ctx.dataset.mask_targets

    if tab_choice == "MASK_TARGETS":
        mask_targets_prop = inputs.str(
            "mask_targets",
            default=json.dumps(ctx.dataset.mask_targets, indent=4),
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

    if edited_mask_targets:
        if not valid:
            mask_targets_prop.invalid = True
            mask_targets_prop.error_message = "Invalid mask targets"
        else:
            num_changed += 1

    ## default_mask_targets

    default_mask_targets, valid = _parse_field(
        ctx, "default_mask_targets", default={}
    )
    edited_default_mask_targets = (
        default_mask_targets != ctx.dataset.default_mask_targets
    )

    if tab_choice == "MASK_TARGETS":
        default_mask_targets_prop = inputs.str(
            "default_mask_targets",
            default=json.dumps(ctx.dataset.default_mask_targets, indent=4),
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
    else:
        default_mask_targets_prop = None

    if edited_default_mask_targets:
        if not valid and default_mask_targets_prop is not None:
            default_mask_targets_prop.invalid = True
            default_mask_targets_prop.error_message = (
                "Invalid default mask targets"
            )
        else:
            num_changed += 1

    ## skeletons

    skeletons, valid = _parse_field(ctx, "skeletons", default={})
    edited_skeletons = skeletons != ctx.dataset.skeletons

    if tab_choice == "SKELETONS":
        skeletons_prop = inputs.str(
            "skeletons",
            default=json.dumps(ctx.dataset.skeletons, indent=4),
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
    else:
        skeletons_prop = None

    if edited_skeletons:
        if not valid and skeletons_prop is not None:
            skeletons_prop.invalid = True
            skeletons_prop.error_message = "Invalid skeletons"
        else:
            num_changed += 1

    ## default_skeleton

    default_skeleton, valid = _parse_field(
        ctx, "default_skeleton", default=None
    )
    edited_default_skeleton = default_skeleton != ctx.dataset.default_skeleton

    if tab_choice == "SKELETONS":
        default_skeleton_prop = inputs.str(
            "default_skeleton",
            default=json.dumps(ctx.dataset.default_skeleton, indent=4),
            required=True,
            label="Default skeleton"
            + (" (edited)" if edited_default_skeleton else ""),
            description=(
                "A default KeypointSkeleton defining the semantic labels and "
                "point connectivity for all Keypoint fields of this dataset "
                "that do not have customized skeletons"
            ),
            view=types.CodeView(),
        )
    else:
        default_skeleton_prop = None

    if edited_default_skeleton:
        if not valid and default_skeleton_prop is not None:
            default_skeleton_prop.invalid = True
            default_skeleton_prop.error_message = "Invalid default skeleton"
        else:
            num_changed += 1

    ## final

    if num_changed > 0:
        view = types.Warning(
            label=f"You are about to edit {num_changed} fields"
        )
    else:
        view = types.Notice(label="You have not made any edits")

    status_prop = inputs.view("status", view)

    if num_changed == 0:
        status_prop.invalid = True


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
        delegate = ctx.params.get("delegate", False)

        view = _get_target_view(ctx, target)

        if delegate:
            view.compute_metadata(overwrite=overwrite)
        else:
            for update in _compute_metadata(ctx, view, overwrite=overwrite):
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

    return True


def _compute_metadata(ctx, sample_collection, overwrite=False):
    num_workers = multiprocessing.cpu_count()

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
    with fou.ProgressBar(total=num_total) as pb:
        with multiprocessing.dummy.Pool(processes=num_workers) as pool:
            # with fou.get_multiprocessing_context().Pool(processes=num_workers) as pool:
            for sample_id, metadata in pb(
                pool.imap_unordered(_do_compute_metadata, inputs)
            ):
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

        view = _get_target_view(ctx, target)

        if not overwrite:
            view = view.exists(thumbnail_path, False)

        size = (width or -1, height or -1)

        foui.transform_images(
            view,
            size=size,
            output_field=thumbnail_path,
            output_dir=output_dir,
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

    return True


class ManagePlugins(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_plugins",
            label="Manage plugins",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        _manage_plugins_inputs(ctx, inputs)
        return types.Property(inputs, view=types.View(label="Manage plugins"))

    def execute(self, ctx):
        tab = ctx.params.get("tab", None)
        if tab == "PLUGINS":
            _plugin_enablement(ctx)
        elif tab == "INSTALL":
            _install_plugin(ctx)


def _manage_plugins_inputs(ctx, inputs):
    tab_choices = types.TabsView()
    tab_choices.add_choice("PLUGINS", label="Plugins")
    tab_choices.add_choice("REQUIREMENTS", label="Requirements")
    tab_choices.add_choice("INSTALL", label="Install")
    default = "PLUGINS"

    inputs.enum(
        "tab",
        tab_choices.values(),
        default=default,
        view=tab_choices,
    )
    tab = ctx.params.get("tab", default)

    if tab == "PLUGINS":
        _plugin_enablement_inputs(ctx, inputs)
    elif tab == "REQUIREMENTS":
        _plugin_requirements_inputs(ctx, inputs)
    elif tab == "INSTALL":
        _install_plugin_inputs(ctx, inputs)


def _plugin_enablement_inputs(ctx, inputs):
    obj = types.Object()
    obj.str(
        "name",
        default="**Name**",
        view=types.MarkdownView(read_only=True, space=3),
    )
    obj.str(
        "description",
        default="**Description**",
        view=types.MarkdownView(read_only=True, space=7),
    )
    obj.str(
        "enabled",
        default="**Enabled**",
        view=types.MarkdownView(read_only=True, space=2),
    )
    inputs.define_property("enablement_header", obj)

    enabled_plugins = set(fop.list_enabled_plugins())

    num_edited = 0
    for i, plugin in enumerate(fop.list_plugins(enabled="all"), 1):
        prop_name = f"enablement{i}"
        actual_enabled = plugin.name in enabled_plugins
        enabled = ctx.params.get(prop_name, {}).get("enabled", actual_enabled)
        edited = enabled != actual_enabled
        num_edited += int(edited)

        obj = types.Object()
        obj.str(
            "markdown_name",
            default=f"[{plugin.name}]({plugin.url})",
            view=types.MarkdownView(read_only=True, space=3),
        )
        obj.str(
            "description",
            default=plugin.description,
            view=types.MarkdownView(read_only=True, space=6.5),
        )
        obj.str(
            "name",
            default=plugin.name,
            view=types.HiddenView(read_only=True, space=0.5),
        )
        obj.bool(
            "enabled",
            label="(edited)" if edited else "",
            default=actual_enabled,
            view=types.CheckboxView(space=2),  # @todo use SwitchView
        )
        inputs.define_property(prop_name, obj)

    if num_edited > 0:
        view = types.Notice(
            label=(
                f"You are about to change the enablement of {num_edited} "
                "plugins"
            )
        )
    else:
        view = types.Notice(label="You have not made any changes")

    status_prop = inputs.view("enablement_status", view)

    if num_edited == 0:
        status_prop.invalid = True


def _plugin_enablement(ctx):
    enabled_plugins = set(fop.list_enabled_plugins())

    i = 0
    while True:
        i += 1
        prop_name = f"enablement{i}"
        obj = ctx.params.get(prop_name, None)
        if obj is None:
            break

        name = obj["name"]
        enabled = obj["enabled"]

        actual_enabled = name in enabled_plugins
        if enabled != actual_enabled:
            if enabled:
                fop.enable_plugin(name)
            else:
                fop.disable_plugin(name)


def _plugin_requirements_inputs(ctx, inputs):
    plugins = [p.name for p in fop.list_plugins(enabled="all")]

    plugin_choices = types.DropdownView()
    for name in sorted(plugins):
        plugin_choices.add_choice(name, label=name)

    inputs.str(
        "requirements_name",
        default=None,
        required=True,
        label="Plugin",
        description="Choose a plugin whose requirements you want to check",
        view=plugin_choices,
    )

    name = ctx.params.get("requirements_name", None)
    if name is None:
        return

    requirements = []

    plugin = fop.get_plugin(name)
    req_str = plugin.fiftyone_requirement
    if req_str is not None:
        requirements.append(_check_fiftyone_requirement(req_str))

    req_strs = fop.load_plugin_requirements(name)
    if req_strs is not None:
        for req_str in req_strs:
            requirements.append(_check_package_requirement(req_str))

    num_requirements = len(requirements)
    if num_requirements == 0:
        inputs.view(
            "requirements_status",
            types.Notice(label="This plugin has no package requirements"),
        )
        return

    obj = types.Object()
    obj.str(
        "requirements_requirement",
        default="**Requirement**",
        view=types.MarkdownView(read_only=True, space=5),
    )
    obj.str(
        "requirements_version",
        default="**Installed version**",
        view=types.MarkdownView(read_only=True, space=5),
    )
    obj.str(
        "requirements_satisfied",
        default="**Satisfied**",
        view=types.MarkdownView(read_only=True, space=2),
    )
    inputs.define_property("requirements_header", obj)

    num_satisfied = 0
    for i, (req, version, success) in enumerate(requirements, 1):
        prop_name = f"requirements{i}"
        num_satisfied += int(success)

        obj = types.Object()
        obj.str(
            "requirement",
            default=str(req),
            view=types.MarkdownView(read_only=True, space=5),
        )
        obj.str(
            "version",
            default=version or "-",
            view=types.MarkdownView(read_only=True, space=5),
        )
        obj.bool(
            "satisfied",
            default=success,
            view=types.CheckboxView(read_only=True, space=2),
        )
        inputs.define_property(prop_name, obj)

    if num_satisfied == num_requirements:
        view = types.Notice(label="All package requirements are satisfied")
    else:
        view = types.Warning(
            label=(
                f"Only {num_satisfied}/{num_requirements} package "
                "requirements are satisfied"
            )
        )

    status_prop = inputs.view("requirements_status", view)
    status_prop.invalid = True


def _check_fiftyone_requirement(req_str):
    req = Requirement(req_str)
    version = foc.VERSION
    success = not req.specifier or req.specifier.contains(version)

    return req, version, success


def _check_package_requirement(req_str):
    req = Requirement(req_str)

    try:
        version = metadata.version(req.name)
    except metadata.PackageNotFoundError:
        version = None

    success = (version is not None) and (
        not req.specifier or req.specifier.contains(version)
    )

    return req, version, success


def _install_plugin_inputs(ctx, inputs):
    instructions = """
The location to download the plugin(s) from, which can be:

-   A GitHub repo URL like `https://github.com/<user>/<repo>`
-   A GitHub ref like
    `https://github.com/<user>/<repo>/tree/<branch>` or
    `https://github.com/<user>/<repo>/commit/<commit>`
-   A GitHub ref string like `<user>/<repo>[/<ref>]`
-   A publicly accessible URL of an archive (eg zip or tar) file
    """

    """
    inputs.str(
        "instructions",
        default=instructions.strip(),
        view=types.MarkdownView(read_only=True),
    )
    """

    inputs.str(
        "url_or_gh_repo",
        required=True,
        label="URL",
        description="The GitHub repository to download the plugin(s) from",
    )

    url_or_gh_repo = ctx.params.get("url_or_gh_repo", None)
    if not url_or_gh_repo:
        return

    inputs.list(
        "plugin_names",
        types.String(),
        default=None,
        required=False,
        label="Plugin names",
        description=(
            "An optional list of plugin names to install. By default, all "
            "found plugins are installed"
        ),
    )

    inputs.int(
        "max_depth",
        default=3,
        label="Max depth",
        description=(
            "The maximum depth within the downloaded archive to search for "
            "plugins"
        ),
        view=types.View(space=6),
    )

    inputs.bool(
        "overwrite",
        default=False,
        label="Overwrite",
        description=(
            "Whether to overwrite an existing plugin with the same name if it "
            "already exists"
        ),
        view=types.CheckboxView(space=6),
    )


def _install_plugin(ctx):
    url_or_gh_repo = ctx.params["url_or_gh_repo"]
    plugin_names = ctx.params.get("plugin_names", None)
    max_depth = ctx.params.get("max_depth", 3)
    overwrite = ctx.params.get("overwrite", False)

    fop.download_plugin(
        url_or_gh_repo,
        plugin_names=plugin_names,
        max_depth=max_depth,
        overwrite=overwrite,
    )


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
                    "https://docs.voxel51.com/plugins/index.html#operators "
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
    p.register(ManagePlugins)
