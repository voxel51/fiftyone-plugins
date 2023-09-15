"""
I/O operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

import json
import multiprocessing
import os
from packaging.requirements import Requirement

import eta.core.utils as etau

import fiftyone as fo
import fiftyone.constants as foc
import fiftyone.core.media as fom
import fiftyone.core.metadata as fomm
import fiftyone.plugins as fop
import fiftyone.core.storage as fos
import fiftyone.core.utils as fou
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.utils.image as foui
import fiftyone.types as fot
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


class ImportSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="import_samples",
            label="Import samples",
            dynamic=True,
            execute_as_generator=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        import_choices = types.Choices()
        import_choices.add_choice(
            "MEDIA_ONLY",
            label="Media only",
            description="Add new samples for media",
        )
        import_choices.add_choice(
            "LABELS_ONLY",
            label="Labels only",
            description="Add labels to existing samples",
        )
        import_choices.add_choice(
            "MEDIA_AND_LABELS",
            label="Media and labels",
            description="Add new samples with media and labels",
        )

        inputs.enum(
            "import_type",
            import_choices.values(),
            required=True,
            label="Import type",
            description="Choose what to import",
            view=import_choices,
        )
        import_type = ctx.params.get("import_type", None)

        ready = False
        if import_type == "MEDIA_ONLY":
            ready = _import_media_only_inputs(ctx, inputs)
        elif import_type == "MEDIA_AND_LABELS":
            ready = _import_media_and_labels_inputs(ctx, inputs)
        elif import_type == "LABELS_ONLY":
            ready = _import_labels_only_inputs(ctx, inputs)

        if ready and import_type in ("MEDIA_ONLY", "MEDIA_AND_LABELS"):
            _upload_media_inputs(ctx, inputs)

        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Import samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        import_type = ctx.params.get("import_type", None)

        if import_type == "MEDIA_ONLY":
            for update in _import_media_only(ctx):
                yield update
        elif import_type == "MEDIA_AND_LABELS":
            for update in _import_media_and_labels(ctx):
                yield update
        elif import_type == "LABELS_ONLY":
            for update in _import_labels_only(ctx):
                yield update

        yield ctx.trigger("reload_dataset")


def _import_media_only_inputs(ctx, inputs):
    # Choose input type
    style_choices = types.TabsView()
    style_choices.add_choice("DIRECTORY", label="Directory")
    style_choices.add_choice("GLOB_PATTERN", label="Glob pattern")
    inputs.enum(
        "style",
        style_choices.values(),
        default="DIRECTORY",
        view=style_choices,
    )
    style = ctx.params.get("style", "DIRECTORY")

    ready = False

    if style == "DIRECTORY":
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        dir_prop = inputs.file(
            "directory",
            required=True,
            label="Directory",
            description="Choose a directory of media to add to this dataset",
            view=file_explorer,
        )
        directory = _parse_path(ctx, "directory")

        if directory:
            n = len(_glob_files(directory=directory))
            if n > 0:
                ready = True
                dir_prop.view.caption = f"Found {n} files"
            else:
                dir_prop.invalid = True
                dir_prop.error_message = "No matching files"
        else:
            dir_prop.view.caption = None
    else:
        file_explorer = types.FileExplorerView(
            button_label="Provide a glob pattern...",
        )
        glob_prop = inputs.file(
            "glob_patt",
            required=True,
            label="Glob pattern",
            description=(
                "Provide a glob pattern of matching media to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        glob_patt = _parse_path(ctx, "glob_patt")

        if glob_patt:
            n = len(_glob_files(glob_patt=glob_patt))
            if n > 0:
                ready = True
                glob_prop.view.caption = f"Found {n} files"
            else:
                glob_prop.invalid = True
                glob_prop.error_message = "No matching files"
        else:
            glob_prop.view.caption = None

    if ready:
        inputs.list(
            "tags",
            types.String(),
            default=None,
            label="Tags",
            description="An optional list of tags to attach to each new sample",
        )

    return ready


def _import_media_and_labels_inputs(ctx, inputs):
    inputs.enum(
        "dataset_type",
        sorted(_DATASET_TYPES.keys()),
        required=True,
        label="Dataset type",
        description="The type of data you're importing",
    )

    dataset_type = ctx.params.get("dataset_type", None)

    if (
        dataset_type in _CLASSIFICATION_TYPES
        or dataset_type in _DETECTION_TYPES
        or dataset_type in _SEGMENTATION_TYPES
    ):
        label_field_choices = types.AutocompleteView()
        for field in _get_label_fields(ctx.dataset, dataset_type):
            label_field_choices.add_choice(field, label=field)

        inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "A new or existing field in which to store the imported labels"
            ),
            view=label_field_choices,
        )

    file_explorer = types.FileExplorerView(
        choose_dir=True,
        button_label="Choose a directory...",
    )
    inputs.file(
        "dataset_dir",
        required=True,
        label="Dataset directory",
        description=(
            "Choose the directory that contains the media and labels to add "
            "to this dataset"
        ),
        view=file_explorer,
    )
    dataset_dir = _parse_path(ctx, "dataset_dir")
    ready = bool(dataset_dir)

    _add_label_types(ctx, inputs, dataset_type)

    # @todo allow customizing `data_path`, `labels_path`, etc?

    if ready:
        inputs.bool(
            "dynamic",
            default=False,
            label="Dynamic",
            description=(
                "Whether to declare dynamic attributes of embedded document "
                "fields that are encountered"
            ),
            view=types.CheckboxView(),
        )

        inputs.list(
            "tags",
            types.String(),
            default=None,
            label="Tags",
            description="An optional list of tags to attach to each new sample",
        )

    return ready


def _import_labels_only_inputs(ctx, inputs):
    inputs.enum(
        "dataset_type",
        sorted(_DATASET_TYPES.keys()),
        required=True,
        label="Dataset type",
        description="The type of data you're importing",
    )

    dataset_type = ctx.params.get("dataset_type", None)

    if (
        dataset_type in _CLASSIFICATION_TYPES
        or dataset_type in _DETECTION_TYPES
        or dataset_type in _SEGMENTATION_TYPES
    ):
        label_field_choices = types.AutocompleteView()
        for field in _get_label_fields(ctx.dataset, dataset_type):
            label_field_choices.add_choice(field, label=field)

        inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "A new or existing field in which to store the imported labels"
            ),
            view=label_field_choices,
        )

    if dataset_type in _LABELS_DIR_TYPES:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "labels_path",
            required=True,
            label="Labels directory",
            description=(
                "Choose the directory that contains the labels to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        labels_path = _parse_path(ctx, "labels_path")
        ready = bool(labels_path)
    elif dataset_type in _LABELS_FILE_TYPES:
        file_explorer = types.FileExplorerView(button_label="Choose a file...")
        inputs.file(
            "labels_path",
            required=True,
            label="Labels path",
            description=(
                "Choose the file that contains the labels to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        labels_path = _parse_path(ctx, "labels_path")
        ready = bool(labels_path)
    else:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "dataset_dir",
            required=True,
            label="Dataset directory",
            description=(
                "Choose the directory that contains the data you wish to add "
                "to this dataset"
            ),
            view=file_explorer,
        )
        dataset_dir = _parse_path(ctx, "dataset_dir")
        ready = bool(dataset_dir)

    _add_label_types(ctx, inputs, dataset_type)

    return ready


def _add_label_types(ctx, inputs, dataset_type):
    label_types = _LABEL_TYPES.get(dataset_type, None)

    if label_types is None or etau.is_str(label_types):
        return

    label_type_choices = types.Choices()
    for field in label_types:
        label_type_choices.add_choice(field, label=field)

    inputs.list(
        "label_types",
        types.String(),
        default=None,
        label="Label types",
        description=(
            "The label type(s) to load. By default, all label types are loaded"
        ),
        view=label_type_choices,
    )


def _upload_media_inputs(ctx, inputs):
    inputs.bool(
        "upload",
        default=False,
        required=False,
        label="Upload media",
        description=(
            "You can optionally upload the media to another location before "
            "adding it to the dataset. Would you like to do this?"
        ),
        view=types.CheckboxView(),
    )
    upload = ctx.params.get("upload", False)

    if upload:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "upload_dir",
            required=False,
            label="Upload directory",
            description=(
                "Provide a directory into which to upload the selected media"
            ),
            view=file_explorer,
        )
        upload_dir = _parse_path(ctx, "upload_dir")

        if upload_dir is not None:
            inputs.bool(
                "overwrite",
                default=False,
                required=False,
                label="Overwrite existing",
                description=(
                    "Do you wish to overwrite existing media of the same name "
                    "(True) or append a unique suffix when necessary to avoid "
                    "name clashses (False)"
                ),
                view=types.CheckboxView(),
            )


def _import_media_only(ctx):
    directory = _parse_path(ctx, "directory")
    if ctx.params.get("style", None) != "DIRECTORY":
        directory = None

    glob_patt = _parse_path(ctx, "glob_patt")
    if ctx.params.get("style", None) != "GLOB_PATTERN":
        glob_patt = None

    tags = ctx.params.get("tags", None)

    filepaths = _glob_files(directory=directory, glob_patt=glob_patt)
    num_total = len(filepaths)

    if num_total == 0:
        return

    filepaths, tasks = _upload_media_tasks(ctx, filepaths)
    if tasks:
        for progress in _upload_media(ctx, tasks):
            yield progress

    batcher = fou.DynamicBatcher(
        filepaths, target_latency=0.1, max_batch_beta=2.0
    )

    num_added = 0

    with batcher:
        for batch in batcher:
            samples = [
                fo.Sample(filepath=filepath, tags=tags) for filepath in batch
            ]
            ctx.dataset._add_samples_batch(samples, True, False, True)
            num_added += len(samples)

            progress = num_added / num_total
            label = f"Loaded {num_added} of {num_total}"
            yield _set_progress(ctx, progress, label=label)


def _import_media_and_labels(ctx):
    dataset_type = ctx.params["dataset_type"]
    dataset_type = _DATASET_TYPES[dataset_type]

    dataset_dir = ctx.params["dataset_dir"]["absolute_path"]
    label_field = ctx.params.get("label_field", None)
    tags = ctx.params.get("tags", None)
    dynamic = ctx.params.get("dynamic", False)

    # Extras
    label_types = ctx.params.get("label_types", None)

    kwargs = {}
    if label_types is not None:
        kwargs["label_types"] = label_types

    ctx.dataset.add_dir(
        dataset_dir=dataset_dir,
        dataset_type=dataset_type,
        label_field=label_field,
        tags=tags,
        dynamic=dynamic,
        **kwargs,
    )

    return
    yield


def _import_labels_only(ctx):
    dataset_type = ctx.params["dataset_type"]
    dataset_type = _DATASET_TYPES[dataset_type]

    labels_path = _parse_path(ctx, "labels_path")
    dataset_dir = _parse_path(ctx, "dataset_dir")
    label_field = ctx.params.get("label_field", None)
    dynamic = ctx.params.get("dynamic", False)

    # Extras
    kwargs = {}

    label_types = ctx.params.get("label_types", None)
    if label_types is not None:
        kwargs["label_types"] = label_types

    if labels_path is not None:
        data_path = {
            os.path.basename(p): p for p in ctx.dataset.values("filepath")
        }
        ctx.dataset.merge_dir(
            data_path=data_path,
            labels_path=labels_path,
            dataset_type=dataset_type,
            label_field=label_field,
            dynamic=dynamic,
            **kwargs,
        )

    if dataset_dir is not None:
        ctx.dataset.merge_dir(
            dataset_dir=dataset_dir,
            dataset_type=dataset_type,
            label_field=label_field,
            dynamic=dynamic,
            **kwargs,
        )

    return
    yield


def _upload_media_tasks(ctx, filepaths):
    upload_dir = _parse_path(ctx, "upload_dir")
    if not ctx.params.get("upload", None):
        upload_dir = None

    if upload_dir is None:
        return filepaths, None

    overwrite = ctx.params.get("overwrite", False)

    inpaths = filepaths
    filename_maker = fou.UniqueFilenameMaker(
        output_dir=upload_dir, ignore_existing=overwrite
    )
    filepaths = [filename_maker.get_output_path(inpath) for inpath in inpaths]

    tasks = list(zip(inpaths, filepaths))

    return filepaths, tasks


def _upload_media(ctx, tasks):
    num_uploaded = 0
    num_total = len(tasks)
    num_workers = fo.config.max_thread_pool_workers or 16

    with multiprocessing.dummy.Pool(processes=num_workers) as pool:
        for _ in pool.imap_unordered(_do_upload_media, tasks):
            num_uploaded += 1
            if num_uploaded % 10 == 0:
                progress = num_uploaded / num_total
                label = f"Uploaded {num_uploaded} of {num_total}"
                yield _set_progress(ctx, progress, label=label)


def _do_upload_media(task):
    inpath, outpath = task
    fos.copy_file(inpath, outpath)


def _glob_files(directory=None, glob_patt=None):
    if directory is not None:
        glob_patt = f"{directory}/*"

    if glob_patt is None:
        return []

    return fos.get_glob_matches(glob_patt)


class MergeSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="merge_samples",
            label="Merge samples",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _get_src_dst_collections(ctx, inputs)

        if ready:
            _get_merge_parameters(ctx, inputs)
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Merge samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        src_type = ctx.params.get("src_type", None)
        src_dataset = ctx.params.get("src_dataset", None)

        dst_type = ctx.params.get("dst_type", None)
        dst_dataset = ctx.params.get("dst_dataset", None)

        key_field = ctx.params["key_field"]
        skip_existing = ctx.params["skip_existing"]
        insert_new = ctx.params["insert_new"]
        fields = ctx.params.get("fields", None) or None
        omit_fields = ctx.params.get("omit_fields", None) or None
        merge_lists = ctx.params["merge_lists"]
        overwrite = ctx.params["overwrite"]
        expand_schema = ctx.params["expand_schema"]
        dynamic = ctx.params["dynamic"]
        include_info = ctx.params["include_info"]
        overwrite_info = ctx.params["overwrite_info"]

        src_coll = _get_merge_collection(ctx, src_type, src_dataset)
        dst_dataset = _get_merge_collection(ctx, dst_type, dst_dataset)

        dst_dataset.merge_samples(
            src_coll,
            key_field=key_field,
            skip_existing=skip_existing,
            insert_new=insert_new,
            fields=fields,
            omit_fields=omit_fields,
            merge_lists=merge_lists,
            overwrite=overwrite,
            expand_schema=expand_schema,
            dynamic=dynamic,
            include_info=include_info,
            overwrite_info=overwrite_info,
        )


def _get_src_dst_collections(ctx, inputs):
    dataset_names = fo.list_datasets()
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)

    #
    # Source view
    #

    src_choices = types.RadioGroup(orientation="horizontal")
    src_choices.add_choice(
        "DATASET",
        label="This dataset",
        description="Merge the current dataset",
    )
    default_src_type = "DATASET"

    if has_view:
        src_choices.add_choice(
            "VIEW",
            label="This view",
            description="Merge the current view",
        )
        default_src_type = "VIEW"

    if has_selected:
        src_choices.add_choice(
            "SELECTED_SAMPLES",
            label="Selected samples",
            description="Merge the selected samples",
        )
        default_src_type = "SELECTED_SAMPLES"

    src_choices.add_choice(
        "OTHER_DATASET",
        label="Another dataset",
        description="Merge another dataset",
    )

    inputs.enum(
        "src_type",
        src_choices.values(),
        required=True,
        default=default_src_type,
        label="Source",
        description="Choose a source collection that you want to merge",
        view=src_choices,
    )

    src_type = ctx.params.get("src_type", None)

    if src_type == "OTHER_DATASET":
        src_selector = types.AutocompleteView()
        for name in dataset_names:
            src_selector.add_choice(name, label=name)

        inputs.enum(
            "src_dataset",
            dataset_names,
            required=True,
            label="Choose a source dataset",
            description="Choose another dataset to merge",
            view=src_selector,
        )

        if not ctx.params.get("src_dataset", None):
            return False

    #
    # Destination dataset
    #

    if src_type == "OTHER_DATASET":
        dst_choices = types.RadioGroup(orientation="horizontal")
        dst_choices.add_choice(
            "DATASET",
            label="This dataset",
            description="Merge into this dataset",
        )
        dst_choices.add_choice(
            "OTHER_DATASET",
            label="Another dataset",
            description="Merge into another dataset",
        )

        inputs.enum(
            "dst_type",
            dst_choices.values(),
            required=True,
            default="DATASET",
            label="Destination",
            description="Choose a destination dataset to merge into",
            view=dst_choices,
        )

        dst_type = ctx.params.get("dst_type", None)
    else:
        dst_type = "OTHER_DATASET"

    if dst_type == "OTHER_DATASET":
        dst_selector = types.AutocompleteView()
        for name in dataset_names:
            dst_selector.add_choice(name, label=name)

        inputs.enum(
            "dst_dataset",
            dataset_names,
            required=True,
            label="Choose a destination dataset",
            description="Choose another dataset to merge into",
            view=dst_selector,
        )

        if not ctx.params.get("dst_dataset", None):
            return False

    return True


def _get_merge_collection(ctx, target, other_name):
    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    if target == "VIEW":
        return ctx.view

    return fo.load_dataset(other_name)


def _get_merge_parameters(ctx, inputs):
    key_fields = _get_sample_fields(ctx.view, _KEY_FIELD_TYPES)
    key_field_selector = types.AutocompleteView()
    for field in key_fields:
        key_field_selector.add_choice(field, label=field)

    inputs.enum(
        "key_field",
        key_fields,
        required=True,
        default="filepath",
        label="Key field",
        description=(
            "The sample field to use to decide whether to join with an "
            "existing sample"
        ),
        view=key_field_selector,
    )

    inputs.bool(
        "insert_new",
        required=True,
        default=True,
        label="Insert new",
        description=(
            "Whether to skip existing samples (True) or merge them (False)"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "skip_existing",
        required=True,
        default=False,
        label="Skip existing",
        description="Whether to insert new samples (True) or skip them (False)",
        view=types.CheckboxView(),
    )

    all_fields = list(ctx.view.get_field_schema().keys())

    field_choices = types.Choices()
    for field in all_fields:
        field_choices.add_choice(field, label=field)

    inputs.list(
        "fields",
        types.String(),
        default=None,
        label="Fields",
        description=(
            "An optional list of fields to which to restrict the merge. If "
            "provided, fields other than these are omitted from the source "
            "collection when merging or adding samples. One exception is that "
            "'filepath' is always included when adding new samples, since the "
            "field is required"
        ),
        view=field_choices,
    )

    omit_field_choices = types.Choices()
    for field in all_fields:
        omit_field_choices.add_choice(field, label=field)

    inputs.list(
        "omit_fields",
        types.String(),
        default=None,
        label="Omit fields",
        description=(
            "An optional list of fields to exclude from the merge. If "
            "provided, these fields are omitted from the source collection, "
            "if present, when merging or adding samples. One exception is "
            "that 'filepath' is always included when adding new samples, "
            "since the field is required"
        ),
        view=omit_field_choices,
    )

    inputs.bool(
        "merge_lists",
        required=True,
        default=True,
        label="Merge lists",
        description=(
            "Whether to merge the elements of list fields (e.g., 'tags') and "
            "label list fields (e.g., Detections fields) rather than merging "
            "the entire top-level field like other field types. For label "
            "lists fields, existing Label elements are either replaced (when "
            "'overwrite' is True) or kept (when 'overwrite' is False) when "
            "their 'id' matches a label from the provided samples"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "overwrite",
        required=True,
        default=True,
        label="Overwrite",
        description=(
            "Whether to overwrite (True) or skip (False) existing fields and "
            "label elements"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "expand_schema",
        required=True,
        default=True,
        label="Expand schema",
        description=(
            "Whether to dynamically add new fields encountered to the dataset "
            "schema. If False, an error is raised if a sample's schema is not "
            "a subset of the dataset schema"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "include_info",
        required=True,
        default=True,
        label="Include info",
        description=(
            "Whether to merge dataset-level information such as 'info' and "
            "'classes'"
        ),
        view=types.CheckboxView(),
    )

    if ctx.params.get("include_info", None):
        inputs.bool(
            "overwrite_info",
            required=True,
            default=False,
            label="Overwrite info",
            description=(
                "Whether to overwrite existing dataset-level information"
            ),
            view=types.CheckboxView(),
        )


_KEY_FIELD_TYPES = (
    fo.StringField,
    fo.ObjectIdField,
    fo.IntField,
    fo.DateField,
    fo.DateTimeField,
)


def _get_sample_fields(sample_collection, field_types):
    schema = sample_collection.get_field_schema(flat=True)
    bad_roots = tuple(
        k + "." for k, v in schema.items() if isinstance(v, fo.ListField)
    )
    return [
        path
        for path, field in schema.items()
        if (isinstance(field, field_types) and not path.startswith(bad_roots))
    ]


class MergeLabels(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="merge_labels",
            label="Merge labels",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _merge_labels_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Merge labels"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        in_field = ctx.params["in_field"]
        out_field = ctx.params["out_field"]

        view = _get_target_view(ctx, target)

        view.merge_labels(in_field, out_field)

        ctx.trigger("reload_dataset")


def _merge_labels_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    has_selected_labels = bool(ctx.selected_labels)
    default_target = None
    if has_view or has_selected or has_selected_labels:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Merge labels for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Merge labels for the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Merge labels for the selected samples",
            )
            default_target = "SELECTED_SAMPLES"

        if has_selected_labels:
            target_choices.add_choice(
                "SELECTED_LABELS",
                label="Selected labels",
                description="Merge the selected labels",
            )
            default_target = "SELECTED_LABELS"

        inputs.enum(
            "target",
            target_choices.values(),
            default=default_target,
            view=target_choices,
        )

    target = ctx.params.get("target", default_target)
    target_view = _get_target_view(ctx, target)

    field_names = _get_fields_with_type(ctx.view, fo.Label)

    in_field_selector = types.AutocompleteView()
    for field_name in field_names:
        in_field_selector.add_choice(field_name, label=field_name)

    inputs.enum(
        "in_field",
        field_names,
        required=True,
        label="Input field",
        description="Choose an input label field",
        view=in_field_selector,
    )

    in_field = ctx.params.get("in_field", None)
    if in_field is None:
        return False

    out_field_selector = types.AutocompleteView()
    for field in field_names:
        if field == in_field:
            continue

        out_field_selector.add_choice(field, label=field)

    inputs.str(
        "out_field",
        required=True,
        label="Output field",
        description=(
            "Provide the name of the output label field into which to "
            "merge the input labels. This field will be created if "
            "necessary"
        ),
        view=out_field_selector,
    )

    out_field = ctx.params.get("out_field", None)
    if out_field is None:
        return False

    if isinstance(target_view, fo.Dataset):
        inputs.view(
            "notice",
            types.Notice(
                label=f"The '{in_field}' field will be deleted after "
                f"merging its labels into the '{out_field}' field"
            ),
        )

    return True


class ExportSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="export_samples",
            label="Export samples",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _export_samples_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Export samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        export_dir = ctx.params["export_dir"]["absolute_path"]
        export_type = ctx.params["export_type"]
        dataset_type = ctx.params.get("dataset_type", None)
        label_field = ctx.params.get("label_field", None)

        target_view = _get_target_view(ctx, target)
        export_media = True

        if export_type == "MEDIA_ONLY":
            dataset_type = fot.MediaDirectory
            label_field = None
        elif export_type == "FILEPATHS_ONLY":
            dataset_type = fot.CSVDataset
            label_field = "filepath"
            export_media = False
        elif export_type == "LABELS_ONLY":
            dataset_type = _DATASET_TYPES[dataset_type]
            export_media = False
        else:
            dataset_type = _DATASET_TYPES[dataset_type]

        target_view.export(
            export_dir=export_dir,
            dataset_type=dataset_type,
            label_field=label_field,
            export_media=export_media,
        )


def _export_samples_inputs(ctx, inputs):
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

    if target == "SELECTED_SAMPLES":
        target_str = "selected samples"
    elif target == "CURRENT_VIEW":
        target_str = "current view"
    else:
        target_str = "dataset"

    export_choices = types.Choices()
    export_choices.add_choice(
        "FILEPATHS_ONLY",
        label="Filepaths only",
        description=f"Export the filepaths of the {target_str}",
    )
    export_choices.add_choice(
        "MEDIA_ONLY",
        label="Media only",
        description=f"Export media of the {target_str}",
    )
    export_choices.add_choice(
        "LABELS_ONLY",
        label="Labels only",
        description=f"Export labels of the {target_str}",
    )
    export_choices.add_choice(
        "MEDIA_AND_LABELS",
        label="Media and labels",
        description=f"Export media and labels of the {target_str}",
    )

    inputs.enum(
        "export_type",
        export_choices.values(),
        required=True,
        label="Export type",
        description="Choose what to export",
        view=export_choices,
    )

    export_type = ctx.params.get("export_type", None)
    if export_type is None:
        return False

    if export_type in ("LABELS_ONLY", "MEDIA_AND_LABELS"):
        dataset_type_choices = _get_labeled_dataset_types(target_view)
        inputs.enum(
            "dataset_type",
            dataset_type_choices,
            required=True,
            label="Label format",
            description="The label format in which to export",
        )

        dataset_type = ctx.params.get("dataset_type", None)
        if dataset_type == "CSV Dataset":
            field_choices = types.Dropdown(multiple=True)
            for field in _get_csv_fields(target_view):
                field_choices.add_choice(field, label=field)

            inputs.list(
                "label_field",
                types.String(),
                required=True,
                label="Fields",
                description="Field(s) to include as columns of the CSV",
                view=field_choices,
            )
        elif dataset_type not in ("FiftyOne Dataset", None):
            label_field_choices = types.Dropdown()
            for field in _get_label_fields(target_view, dataset_type):
                label_field_choices.add_choice(field, label=field)

            inputs.enum(
                "label_field",
                label_field_choices.values(),
                required=True,
                label="Label field",
                description="The field containing the labels to export",
                view=label_field_choices,
            )

    if export_type is not None:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        export_prop = inputs.file(
            "export_dir",
            required=True,
            label="Directory",
            description="Choose a directory at which to write the export",
            view=file_explorer,
        )
        export_dir = _parse_path(ctx, "export_dir")

        if export_dir is not None and fos.isdir(export_dir):
            inputs.bool(
                "overwrite",
                default=True,
                label="Directory already exists. Overwrite it?",
                view=types.CheckboxView(),
            )
            overwrite = ctx.params.get("overwrite", True)

            if not overwrite:
                export_prop.invalid = True
                export_prop.error_message = (
                    "The specifieid export directory already exists"
                )
    else:
        export_dir = None

    if export_dir is not None:
        label_field = ctx.params.get("label_field", None)
        size_bytes = _estimate_export_size(
            target_view, export_type, label_field
        )
        size_str = etau.to_human_bytes_str(size_bytes)
        label = f"Estimated export size: {size_str}"
        inputs.view("estimate", types.Notice(label=label))

    if export_dir is None:
        return False

    return True


def _estimate_export_size(view, export_type, label_field):
    size_bytes = 0

    # Estimate media size
    if export_type in ("MEDIA_ONLY", "MEDIA_AND_LABELS"):
        num_valid = len(view.exists("metadata.size_bytes"))
        num_total = len(view)

        if num_valid == 0:
            size_bytes += 100e3 * num_total
        else:
            media_size = view.sum("metadata.size_bytes")
            size_bytes += (num_total / num_valid) * media_size

    if export_type == "FILEPATHS_ONLY":
        label_field = "filepath"

    # Estimate labels size
    if label_field:
        stats = view.select_fields(label_field).stats()
        size_bytes += stats["samples_bytes"]

    return size_bytes


def _get_csv_fields(view):
    for path, field in view.get_field_schema().items():
        if isinstance(field, fo.EmbeddedDocumentField):
            for _path, _field in field.get_field_schema().items():
                if not isinstance(_field, (fo.ListField, fo.DictField)):
                    yield path + "." + _path
        elif not isinstance(field, (fo.ListField, fo.DictField)):
            yield path


def _get_labeled_dataset_types(view):
    label_types = set(
        view.get_field(field).document_type
        for field in _get_fields_with_type(view, fo.Label)
    )

    dataset_types = []

    if fo.Classification in label_types:
        dataset_types.extend(_CLASSIFICATION_TYPES)

    if fo.Detections in label_types:
        dataset_types.extend(_DETECTION_TYPES)

    if fo.Segmentation in label_types:
        dataset_types.extend(_SEGMENTATION_TYPES)

    dataset_types.extend(_OTHER_TYPES)

    return sorted(set(dataset_types))


def _get_label_fields(view, dataset_type):
    label_fields = []

    if dataset_type in _CLASSIFICATION_TYPES:
        label_fields.extend(_get_fields_with_type(view, fo.Classification))

    if dataset_type in _DETECTION_TYPES:
        label_fields.extend(_get_fields_with_type(view, fo.Detections))

    if dataset_type in _SEGMENTATION_TYPES:
        label_fields.extend(_get_fields_with_type(view, fo.Segmentation))

    return sorted(set(label_fields))


def _get_fields_with_type(view, type):
    if issubclass(type, fo.Field):
        return view.get_field_schema(ftype=type).keys()

    return view.get_field_schema(embedded_doc_type=type).keys()


# @todo add import-only types
# @todo add video types

_DATASET_TYPES = {
    # Classification
    "Image Classification Directory Tree": fot.ImageClassificationDirectoryTree,
    "TF Image Classification": fot.TFImageClassificationDataset,
    # Detection
    "COCO": fot.COCODetectionDataset,
    "VOC": fot.VOCDetectionDataset,
    "KITTI": fot.KITTIDetectionDataset,
    "YOLOv4": fot.YOLOv4Dataset,
    "YOLOv5": fot.YOLOv5Dataset,
    "TF Object Detection": fot.TFObjectDetectionDataset,
    "CVAT Image": fot.CVATImageDataset,
    # Segmentation
    "Image Segmentation": fot.ImageSegmentationDirectory,
    # Other
    "FiftyOne Dataset": fot.FiftyOneDataset,
    "CSV Dataset": fot.CSVDataset,
}

_LABEL_TYPES = {
    "COCO": ["detections", "segmentations", "keypoints"],
}

_CLASSIFICATION_TYPES = [
    "Image Classification Directory Tree",
    "TF Image Classification",
]

_DETECTION_TYPES = [
    "COCO",
    "VOC",
    "KITTI",
    "YOLOv4",
    "YOLOv5",
    "TF Object Detection",
    "CVAT Image",
]

_SEGMENTATION_TYPES = [
    "Image Segmentation",
]

_OTHER_TYPES = [
    "FiftyOne Dataset",
    "CSV Dataset",
]

_LABELS_FILE_TYPES = [
    "COCO",
    "CVAT Image",
    "CSV Dataset",
]

_LABELS_DIR_TYPES = [
    "VOC",
    "KITTI",
    "YOLOv4",
    "Image Segmentation",
]


class DrawLabels(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="draw_labels",
            label="Draw labels",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _draw_labels_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Draw labels"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        output_dir = ctx.params["output_dir"]["absolute_path"]
        label_fields = ctx.params.get("label_fields", None)
        overwrite = ctx.params.get("overwrite", False)

        target_view = _get_target_view(ctx, target)

        target_view.draw_labels(
            output_dir,
            label_fields=label_fields,
            overwrite=overwrite,
        )


def _draw_labels_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None
    if has_view or has_selected:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Draw labels for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Draw labels for the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Draw labels for the selected samples",
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

    label_field_choices = types.Dropdown(multiple=True)
    for field in _get_fields_with_type(target_view, fo.Label):
        label_field_choices.add_choice(field, label=field)

    inputs.list(
        "label_fields",
        types.String(),
        required=False,
        default=None,
        label="Label fields",
        description=(
            "The label field(s) to render. By default, all labels are rendered"
        ),
        view=label_field_choices,
    )

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
            "annotated media"
        ),
        view=file_explorer,
    )
    output_dir = _parse_path(ctx, "output_dir")

    if output_dir is not None and fos.isdir(output_dir):
        inputs.bool(
            "overwrite",
            default=False,
            label=(
                "Directory already exists. Delete it before writing new "
                "media?"
            ),
            view=types.CheckboxView(),
        )

    if output_dir is None:
        return False

    return True


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


class LoadZooDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_zoo_dataset",
            label="Load zoo dataset",
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
        kwargs.pop("delegate", None)

        dataset_name = _get_zoo_dataset_name(ctx)

        dataset = foz.load_zoo_dataset(
            name,
            splits=splits,
            label_field=label_field,
            dataset_name=dataset_name,
            drop_existing_dataset=True,
            **kwargs,
        )
        dataset.persistent = True

        ctx.trigger("open_dataset", dict(name=dataset.name))


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

    tag_choices = types.Dropdown(multiple=True)
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
    if name is None:
        return False

    zoo_dataset = zoo_datasets[name]

    _get_source_dir(ctx, inputs, zoo_dataset)

    if zoo_dataset.has_splits:
        split_choices = types.Dropdown(multiple=True)
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


class ApplyModel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="apply_model",
            label="Apply model",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _apply_model_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Apply model")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        model = ctx.params["model"]
        label_field = ctx.params["label_field"]
        confidence_thresh = ctx.params.get("confidence_thresh", None)
        store_logits = ctx.params.get("store_logits", False)
        batch_size = ctx.params.get("batch_size", None)
        num_workers = ctx.params.get("num_workers", None)
        skip_failures = ctx.params.get("skip_failures", True)
        output_dir = ctx.params.get("output_dir", None)
        rel_dir = ctx.params.get("rel_dir", None)

        target_view = _get_target_view(ctx, target)

        model = foz.load_zoo_model(model)

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


def _apply_model_inputs(ctx, inputs):
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

    field_choices = types.AutocompleteView()
    for field in _get_fields_with_type(target_view, fo.Label):
        field_choices.add_choice(field, label=field)

    inputs.str(
        "label_field",
        required=True,
        label="Label field",
        description=(
            "The name of a new or existing field in which to store the model "
            "predictions"
        ),
        view=field_choices,
    )

    manifest = fozm._load_zoo_models_manifest()

    models_by_tag = defaultdict(set)
    for model in manifest:
        for tag in model.tags or []:
            models_by_tag[tag].add(model.name)

    tag_choices = types.Dropdown(multiple=True)
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
        model_names = [model.name for model in manifest]

    model_choices = types.DropdownView()
    for name in sorted(model_names):
        model_choices.add_choice(name, label=name)

    inputs.enum(
        "model",
        model_choices.values(),
        label="Model",
        description=(
            "The name of a model from the FiftyOne Model Zoo to use to "
            "generate predictions"
        ),
        caption="https://docs.voxel51.com/user_guide/model_zoo/models.html",
        view=model_choices,
    )

    model = ctx.params.get("model", None)
    if model is None:
        return False

    zoo_model = fozm.get_zoo_model(model)

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
            "A batch size to use when performing inference, if the model "
            "supports it"
        ),
    )

    inputs.int(
        "num_workers",
        default=None,
        label="Num workers",
        description="The number of workers to use for Torch data loaders",
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


class InstallPlugin(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="install_plugin",
            label="Install plugin",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _install_plugin_inputs(ctx, inputs)

        view = types.View(label="Install plugin")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
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


def _install_plugin_inputs(ctx, inputs):
    """
    The location to download the plugin(s) from, which can be:

    -   a GitHub repo URL like ``https://github.com/<user>/<repo>``
    -   a GitHub ref like
        ``https://github.com/<user>/<repo>/tree/<branch>`` or
        ``https://github.com/<user>/<repo>/commit/<commit>``
    -   a GitHub ref string like ``<user>/<repo>[/<ref>]``
    -   a publicly accessible URL of an archive (eg zip or tar) file
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
    )

    inputs.bool(
        "overwrite",
        default=False,
        label=(
            "Whether to overwrite an existing plugin with the same name if it "
            "already exists"
        ),
        view=types.CheckboxView(),
    )


class CheckPluginRequirements(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="check_plugin_requirements",
            label="Check plugin requirements",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _check_plugin_requirements_inputs(ctx, inputs)
        inputs.invalid = True

        view = types.View(label="Check plugin requirements")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        pass


def _check_plugin_requirements_inputs(ctx, inputs):
    plugins = [p.name for p in fop.list_plugins()]

    plugin_choices = types.DropdownView()
    for name in sorted(plugins):
        plugin_choices.add_choice(name, label=name)

    inputs.str(
        "name",
        required=True,
        label="Plugin",
        view=plugin_choices,
    )

    name = ctx.params.get("name", None)
    if name is None:
        return False

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
            "status",
            types.Notice(label="This plugin has no package requirements"),
        )

        return

    inputs.str(
        "requirements",
        view=types.Header(label="Package requirements", divider=True),
    )

    num_satisfied = 0
    for i, (req, version, success) in enumerate(requirements, 1):
        num_satisfied += int(success)

        obj = types.Object()
        obj.str(
            "requirement",
            default=str(req),
            view=types.LabelValueView(label="Requirement", space=4),
        )
        obj.str(
            "version",
            default=version or "-",
            view=types.LabelValueView(label="Installed version", space=4),
        )
        obj.bool(
            "satisfied",
            default=success,
            label="Satisfied",
            description="Requirement satisfied",
            view=types.View(space=4, read_only=True),
        )
        inputs.define_property("req" + str(i), obj)

    if num_satisfied == num_requirements:
        view = types.Notice(label="All package requirements are satisfied")
    else:
        view = types.Warning(
            label=(
                f"Only {num_satisfied}/{num_requirements} package "
                "requirements are satisfied"
            )
        )

    inputs.view("status", view)


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
    p.register(ImportSamples)
    p.register(MergeSamples)
    p.register(MergeLabels)
    p.register(ExportSamples)
    p.register(DrawLabels)
    p.register(ComputeMetadata)
    p.register(GenerateThumbnails)
    p.register(LoadZooDataset)
    p.register(ApplyModel)
    p.register(InstallPlugin)
    p.register(CheckPluginRequirements)
