"""
Utility operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import contextlib
import json
import multiprocessing.dummy

import eta.core.utils as etau

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
            label="Name",
            description=(
                "Choose a name for the dataset. If omitted, a randomly "
                "generated name will be used"
            ),
        )

        name = ctx.params.get("name", None)

        if name and fo.dataset_exists(name):
            name_prop.invalid = True
            name_prop.error_message = f"Dataset {name} already exists"

        inputs.str(
            "description",
            required=False,
            label="Description",
            description="An optional description for the dataset",
        )

        inputs.list(
            "tags",
            types.String(),
            required=False,
            label="Tags",
            description="An optional list of tags for the dataset",
        )

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
        name = ctx.params.get("name", None) or None
        description = ctx.params.get("description", None)
        tags = ctx.params.get("tags", None)
        persistent = ctx.params.get("persistent", False)

        dataset = fo.Dataset(name, persistent=persistent)

        if description:
            dataset.description = description

        if tags:
            dataset.tags = tags

        ctx.trigger("open_dataset", dict(dataset=dataset.name))


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
        app_config = _parse_app_config(ctx)
        classes = ctx.params.get("classes", None)
        default_classes = ctx.params.get("default_classes", None)
        mask_targets = ctx.params.get("mask_targets", None)
        default_mask_targets = ctx.params.get("default_mask_targets", None)
        skeletons = ctx.params.get("skeletons", None)
        default_skeleton = ctx.params.get("default_skeleton", None) or None

        if name is not None:
            if name != ctx.dataset.name:
                ctx.dataset.name = name

        if description is not None:
            if description != ctx.dataset.description:
                ctx.dataset.description = description
        elif ctx.dataset.description is not None:
            ctx.dataset.description = None

        if persistent is not None:
            if persistent != ctx.dataset.persistent:
                ctx.dataset.persistent = persistent

        if tags is not None:
            if tags != ctx.dataset.tags:
                ctx.dataset.tags = tags

        if info is not None:
            info = json.loads(info)
            if info != ctx.dataset.info:
                ctx.dataset.info = info

        if app_config is not None:
            if app_config != ctx.dataset.app_config:
                ctx.dataset.app_config = app_config

        if classes is not None:
            classes = json.loads(classes)
            if classes != ctx.dataset.classes:
                ctx.dataset.classes = classes

        if default_classes is not None:
            default_classes = json.loads(default_classes)
            if default_classes != ctx.dataset.default_classes:
                ctx.dataset.default_classes = default_classes

        if mask_targets is not None:
            mask_targets = json.loads(mask_targets)
            if mask_targets != ctx.dataset.mask_targets:
                ctx.dataset.mask_targets = mask_targets

        if default_mask_targets is not None:
            default_mask_targets = json.loads(default_mask_targets)
            if default_mask_targets != ctx.dataset.default_mask_targets:
                ctx.dataset.default_mask_targets = default_mask_targets

        if skeletons is not None:
            skeletons = {
                field: fo.KeypointSkeleton.from_dict(skeleton)
                for field, skeleton in json.loads(skeletons).items()
            }
            if skeletons != ctx.dataset.skeletons:
                ctx.dataset.skeletons = skeletons

        if default_skeleton is not None:
            default_skeleton = fo.KeypointSkeleton.from_dict(
                json.loads(default_skeleton)
            )
            if default_skeleton != ctx.dataset.default_skeleton:
                ctx.dataset.default_skeleton = default_skeleton
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
    tab_choices.add_choice("CLASSES", label="Classes")
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
    edited_name = name is not None and name != ctx.dataset.name
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
        "description" in ctx.params  # can be None
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
        persistent is not None and persistent != ctx.dataset.persistent
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
    edited_tags = tags is not None and tags != ctx.dataset.tags
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
    edited_info = info is not None and info != ctx.dataset.info
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

    ## app_config.media_fields

    media_fields = ctx.params.get("app_config_media_fields", None)
    edited_media_fields = (
        media_fields is not None
        and media_fields != ctx.dataset.app_config.media_fields
    )
    if edited_media_fields:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        str_field_choices = types.Dropdown(multiple=True)
        for field in _get_string_fields(ctx.dataset):
            str_field_choices.add_choice(field, label=field)

        inputs.list(
            "app_config_media_fields",
            types.String(),
            default=ctx.dataset.app_config.media_fields,
            required=True,
            label="Media fields"
            + (" (edited)" if edited_media_fields else ""),
            description=(
                "The list of sample fields that contain media and should be "
                "available to choose from the App's settings menus"
            ),
            view=str_field_choices,
        )

    ## app_config.grid_media_field

    grid_media_field = ctx.params.get("app_config_grid_media_field", None)
    edited_grid_media_field = (
        grid_media_field is not None
        and grid_media_field != ctx.dataset.app_config.grid_media_field
    )
    if edited_grid_media_field:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        field_choices = types.Dropdown()
        for field in ctx.params.get("app_config_media_fields", []):
            field_choices.add_choice(field, label=field)

        inputs.enum(
            "app_config_grid_media_field",
            field_choices.values(),
            default=ctx.dataset.app_config.grid_media_field,
            required=True,
            label="Grid media field"
            + (" (edited)" if edited_grid_media_field else ""),
            description=(
                "The default sample field from which to serve media in the "
                "App's grid view"
            ),
            view=field_choices,
        )

    ## app_config.modal_media_field

    modal_media_field = ctx.params.get("app_config_modal_media_field", None)
    edited_modal_media_field = (
        modal_media_field is not None
        and modal_media_field != ctx.dataset.app_config.modal_media_field
    )
    if edited_modal_media_field:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        field_choices = types.Dropdown()
        for field in ctx.params.get("app_config_media_fields", []):
            field_choices.add_choice(field, label=field)

        inputs.enum(
            "app_config_modal_media_field",
            field_choices.values(),
            default=ctx.dataset.app_config.modal_media_field,
            required=True,
            label="Modal media field"
            + (" (edited)" if edited_modal_media_field else ""),
            description=(
                "The default sample field from which to serve media in the "
                "App's modal view"
            ),
            view=field_choices,
        )

    ## app_config.sidebar_mode

    sidebar_mode = ctx.params.get("app_config_sidebar_mode", None)
    edited_sidebar_mode = (
        "app_config_sidebar_mode" in ctx.params  # can be None
        and sidebar_mode != ctx.dataset.app_config.sidebar_mode
    )
    if edited_sidebar_mode:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        sidebar_mode_choices = types.AutocompleteView()
        sidebar_mode_choices.add_choice("fast", label="fast")
        sidebar_mode_choices.add_choice("all", label="all")
        sidebar_mode_choices.add_choice("best", label="best")

        inputs.str(
            "app_config_sidebar_mode",
            default=ctx.dataset.app_config.sidebar_mode,
            required=False,
            label="Sidebar mode"
            + (" (edited)" if edited_sidebar_mode else ""),
            description="An optional default mode for the App sidebar",
            view=sidebar_mode_choices,
        )

    ## app_config.sidebar_groups

    sidebar_groups, valid = _parse_field(
        ctx, "app_config_sidebar_groups", type=list
    )
    if sidebar_groups is not None:
        try:
            sidebar_groups = [
                fo.SidebarGroupDocument.from_dict(g) for g in sidebar_groups
            ]
        except:
            valid = False
    edited_sidebar_groups = (
        "app_config_sidebar_groups" in ctx.params  # can be None
        and sidebar_groups != ctx.dataset.app_config.sidebar_groups
    )
    if edited_sidebar_groups:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        default_sidebar_groups = ctx.dataset.app_config.sidebar_groups
        if default_sidebar_groups is not None:
            default_sidebar_groups = _serialize(
                [g.to_dict() for g in default_sidebar_groups]
            )

        prop = inputs.str(
            "app_config_sidebar_groups",
            default=default_sidebar_groups,
            required=False,
            label="Sidebar groups"
            + (" (edited)" if edited_sidebar_groups else ""),
            description=(
                "An optional list of custom sidebar groups to use in the App"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid sidebar groups"

    ## app_config.color_scheme

    color_scheme, valid = _parse_field(
        ctx, "app_config_color_scheme", type=dict
    )
    if color_scheme is not None:
        try:
            color_scheme = fo.ColorScheme.from_dict(color_scheme)
        except:
            valid = False
    edited_color_scheme = (
        "app_config_color_scheme" in ctx.params  # can be None
        and color_scheme != ctx.dataset.app_config.color_scheme
    )
    if edited_color_scheme:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        default_color_scheme = ctx.dataset.app_config.color_scheme
        if default_color_scheme is not None:
            default_color_scheme = default_color_scheme.to_json(pretty_print=4)

        prop = inputs.str(
            "app_config_color_scheme",
            default=default_color_scheme,
            required=False,
            label="Color scheme"
            + (" (edited)" if edited_color_scheme else ""),
            description=("An optional custom color scheme for the dataset"),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid color scheme"

    ## app_config.plugins

    plugins, valid = _parse_field(ctx, "app_config_plugins", type=dict)
    edited_plugins = (
        plugins is not None and plugins != ctx.dataset.app_config.plugins
    )
    if edited_plugins:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        prop = inputs.str(
            "app_config_plugins",
            default=_serialize(ctx.dataset.app_config.plugins),
            required=True,
            label="Plugin settings" + (" (edited)" if edited_plugins else ""),
            description=(
                "An optional dict mapping plugin names to plugin settings"
            ),
            view=types.CodeView(),
        )

        if not valid:
            prop.invalid = True
            prop.error_message = "Invalid plugin settings"

    ## classes

    classes, valid = _parse_field(ctx, "classes", type=dict)
    edited_classes = classes is not None and classes != ctx.dataset.classes
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
        default_classes is not None
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
        mask_targets is not None and mask_targets != ctx.dataset.mask_targets
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
        default_mask_targets is not None
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
        skeletons is not None and skeletons != ctx.dataset.skeletons
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
        "default_skeleton" in ctx.params  # can be None
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


def _parse_app_config(ctx):
    # Start from current AppConfig to ensure that additional fields aren't lost
    app_config = ctx.dataset.app_config.copy()

    if "app_config_media_fields" in ctx.params:
        app_config.media_fields = ctx.params["app_config_media_fields"]

    if "app_config_grid_media_field" in ctx.params:
        app_config.grid_media_field = ctx.params["app_config_grid_media_field"]

    if "app_config_modal_media_field" in ctx.params:
        app_config.modal_media_field = ctx.params[
            "app_config_modal_media_field"
        ]

    if "app_config_sidebar_mode" in ctx.params:
        app_config.sidebar_mode = ctx.params["app_config_sidebar_mode"]

    if "app_config_sidebar_groups" in ctx.params:
        sidebar_groups = ctx.params["app_config_sidebar_groups"]
        if sidebar_groups:
            sidebar_groups = [
                fo.SidebarGroupDocument.from_dict(g)
                for g in json.loads(sidebar_groups)
            ]
        else:
            sidebar_groups = None

        app_config.sidebar_groups = sidebar_groups

    if "app_config_color_scheme" in ctx.params:
        color_scheme = ctx.params["app_config_color_scheme"]
        if color_scheme:
            color_scheme = fo.ColorScheme.from_dict(json.loads(color_scheme))
        else:
            color_scheme = None

        app_config.color_scheme = color_scheme

    if "app_config_plugins" in ctx.params:
        plugins = ctx.params["app_config_plugins"]
        app_config.plugins = json.loads(plugins)

    return app_config


def _get_string_fields(dataset):
    for path, field in dataset.get_field_schema().items():
        if isinstance(field, fo.StringField):
            yield path


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
            ctx.trigger("open_dataset", dict(dataset=new_name))
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


class DeleteSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_samples",
            label="Delete samples",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _delete_samples_inputs(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Delete samples"))

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        view = _get_target_view(ctx, target)

        if isinstance(view, fo.Dataset):
            ctx.dataset.clear()
        else:
            ctx.dataset.delete_samples(view)

        ctx.trigger("reload_dataset")


def _delete_samples_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None
    if has_view or has_selected:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Delete all samples",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Delete the samples in the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Delete the selected samples",
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

    count = len(target_view)
    if count > 0:
        sample_text = "sample" if count == 1 else "samples"
        inputs.str(
            "msg",
            label=f"Delete {count} {sample_text}?",
            view=types.Warning(),
        )
    else:
        prop = inputs.str(
            "msg",
            label="There are no samples to delete",
            view=types.Warning(),
        )
        prop.invalid = True


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

    def __call__(
        self,
        sample_collection,
        overwrite=False,
        num_workers=None,
        delegate=False,
        delegation_target=None,
    ):
        """Populates the ``metadata`` field for the given sample collection.

        Example usage::

            import fiftyone as fo
            import fiftyone.operators as foo
            import fiftyone.zoo as foz

            dataset = foz.load_zoo_dataset("quickstart")
            compute_metadata = foo.get_operator("@voxel51/utils/compute_metadata")

            # Run immediately
            compute_metadata(dataset)

            # Delegate computation and overwrite existing values
            compute_metadata(dataset, overwrite=True, delegate=True)

        Args:
            sample_collection: a
                :class:`fiftyone.core.collections.SampleCollection`
            overwrite (False): whether to overwrite existing metadata
            num_workers (None): a suggested number of threads to use
            delegate (False): whether to delegate execution
            delegation_target (None): an optional orchestrator on which to
                schedule the operation, if it is delegated
        """
        if isinstance(sample_collection, fo.DatasetView):
            ctx = dict(view=sample_collection)
        else:
            ctx = dict(dataset=sample_collection)

        if delegation_target is not None:
            ctx["delegation_target"] = delegation_target

        params = dict(
            overwrite=overwrite,
            num_workers=num_workers,
            delegate=delegate,
        )
        return foo.execute_operator(self.uri, ctx, params=params)

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
        description="An optional number of threads to use",
    )

    return True


def _compute_metadata_generator(
    ctx, sample_collection, overwrite=False, num_workers=None
):
    # @todo can switch to this if we require `fiftyone>=0.22.2`
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

    num_total = len(ids)
    if num_total == 0:
        return

    inputs = zip(ids, filepaths, media_types)
    values = {}

    try:
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
                values[sample_id] = metadata

                num_computed += 1
                if num_computed % 10 == 0:
                    progress = num_computed / num_total
                    label = f"Computed {num_computed} of {num_total}"
                    yield ctx.trigger(
                        "set_progress", dict(progress=progress, label=label)
                    )
    finally:
        sample_collection.set_values("metadata", values, key_field="id")


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

    def __call__(
        self,
        sample_collection,
        thumbnail_path,
        output_dir,
        width=None,
        height=None,
        overwrite=False,
        num_workers=None,
        delegate=False,
        delegation_target=None,
    ):
        """Generates thumbnail images for the given sample collection.

        Example usage::

            import fiftyone as fo
            import fiftyone.operators as foo
            import fiftyone.zoo as foz

            dataset = foz.load_zoo_dataset("quickstart")
            generate_thumbnails = foo.get_operator("@voxel51/utils/generate_thumbnails")

            # Run immediately
            generate_thumbnails(dataset, "thumbnail_path", "/tmp/thumbnails", height=64)

            # Delegate computation and overwrite existing images
            generate_thumbnails(
                dataset,
                "thumbnail_path",
                "/tmp/thumbnails",
                height=32,
                overwrite=True,
                delegate=True,
            )

        Args:
            sample_collection: a
                :class:`fiftyone.core.collections.SampleCollection`
            thumbnail_path: an optional field in which to store the paths to
                the transformed images. By default, ``media_field`` is updated
                in-place
            output_dir: the directory in which to write the generated
                thumbnails
            width (None): an optional ``width`` for each thumbnail, in pixels.
                If omitted, the appropriate aspect-preserving value is computed
                from the provided ``height``. At least one of ``width`` and
                ``height`` must be provided
            height (None): an optional ``height`` for each thumbnail, in pixels.
                If omitted, the appropriate aspect-preserving value is computed
                from the provided ``width``. At least one of ``width`` and
                ``height`` must be provided
            overwrite (False): whether to overwrite existing thumbnail images
            num_workers (None): a suggested number of worker processes to use
            delegate (False): whether to delegate execution
            delegation_target (None): an optional orchestrator on which to
                schedule the operation, if it is delegated
        """
        if isinstance(sample_collection, fo.DatasetView):
            ctx = dict(view=sample_collection)
        else:
            ctx = dict(dataset=sample_collection)

        if delegation_target is not None:
            ctx["delegation_target"] = delegation_target

        params = dict(
            thumbnail_path=thumbnail_path,
            output_dir={"absolute_path": output_dir},
            width=width,
            height=height,
            overwrite=overwrite,
            num_workers=num_workers,
            delegate=delegate,
        )
        return foo.execute_operator(self.uri, ctx, params=params)

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
            num_workers = 0

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


class Delegate(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delegate",
            label="Delegate",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            unlisted=True,
        )

    def __call__(
        self,
        fcn,
        dataset=None,
        view=None,
        delegation_target=None,
        *args,
        **kwargs,
    ):
        """Delegates execution of an arbitrary function.

        Example usage::

            import fiftyone as fo
            import fiftyone.operators as foo
            import fiftyone.zoo as foz

            dataset = foz.load_zoo_dataset("quickstart")
            delegate = foo.get_operator("@voxel51/utils/delegate")

            # Compute metadata
            delegate("compute_metadata", dataset=dataset)

            # Compute visualization
            delegate(
                "fiftyone.brain.compute_visualization",
                dataset=dataset,
                brain_key="img_viz",
            )

            # Export a view
            delegate(
                "export",
                view=dataset.to_patches("ground_truth"),
                export_dir="/tmp/patches",
                dataset_type="fiftyone.types.ImageClassificationDirectoryTree",
                label_field="ground_truth",
            )

            # Load the exported patches into a new dataset
            delegate(
                "fiftyone.Dataset.from_dir",
                dataset_dir="/tmp/patches",
                dataset_type="fiftyone.types.ImageClassificationDirectoryTree",
                label_field="ground_truth",
                name="patches",
                persistent=True,
            )

        Args:
            fcn: the function to call, which can be either of the following:

                (a) the ``"fully.qualified.name"`` of a function to call with
                    the appropriate syntax below:

                -   ``fcn(dataset, *args, **kwargs)``: if a dataset is provided
                -   ``fcn(view, *args, **kwargs)``: if a view is provided
                -   ``fcn(*args, **kwargs)``: if neither is provided

                (b) the string name of an instance method on the provided
                    collection to call with the appropriate syntax below:

                -   ``dataset.fcn(*args, **kwargs)``: if a dataset is provided
                -   ``view.fcn(*args, **kwargs)``: if a view is provided

            dataset (None): a :class:`fiftyone.core.dataset.Dataset`
            view (None): a :class:`fiftyone.core.view.DatasetView`
            delegation_target (None): an optional orchestrator on which to
                schedule the operation, if it is delegated
            *args: JSON-serializable positional arguments for the function
            **kwargs: JSON-serializable keyword arguments for the function
        """
        ctx = dict(dataset=dataset, view=view)
        if delegation_target is not None:
            ctx["delegation_target"] = delegation_target

        has_dataset = dataset is not None
        has_view = view is not None

        params = dict(
            fcn=fcn,
            has_dataset=has_dataset,
            has_view=has_view,
            args=args,
            kwargs=kwargs,
        )
        return foo.execute_operator(self.uri, ctx, params=params)

    def resolve_delegation(self, ctx):
        return True

    def execute(self, ctx):
        fcn = ctx.params["fcn"]
        has_dataset = ctx.params["has_dataset"]
        has_view = ctx.params["has_view"]
        args = ctx.params["args"]
        kwargs = ctx.params["kwargs"]

        if has_view:
            sample_collection = ctx.view
        elif has_dataset:
            sample_collection = ctx.dataset
        else:
            sample_collection = None

        if sample_collection is None:
            fcn = etau.get_function(fcn)
            fcn(*args, **kwargs)
        elif "." in fcn:
            fcn = etau.get_function(fcn)
            fcn(sample_collection, *args, **kwargs)
        else:
            fcn = getattr(sample_collection, fcn)
            fcn(*args, **kwargs)


def register(p):
    p.register(CreateDataset)
    p.register(LoadDataset)
    p.register(EditDatasetInfo)
    p.register(RenameDataset)
    p.register(DeleteDataset)
    p.register(DeleteSamples)
    p.register(ComputeMetadata)
    p.register(GenerateThumbnails)
    p.register(Delegate)
