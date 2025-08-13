"""
Utility operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import contextlib
from datetime import datetime
import json
import multiprocessing.dummy
from packaging.version import Version

from bson import json_util
import humanize

import eta.core.utils as etau

import fiftyone as fo
import fiftyone.constants as foc
import fiftyone.core.fields as fof
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
            description="Optional tag(s) for the dataset",
            view=types.AutocompleteView(multiple=True),
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
        if "name" in ctx.params:
            name = ctx.params["name"]
            if name != ctx.dataset.name:
                ctx.dataset.name = name

        if "description" in ctx.params:
            description = ctx.params["description"] or None
            if description != ctx.dataset.description:
                ctx.dataset.description = description

        if "persistent" in ctx.params:
            persistent = ctx.params["persistent"]
            if persistent != ctx.dataset.persistent:
                ctx.dataset.persistent = persistent

        if "tags" in ctx.params:
            tags = ctx.params["tags"]
            if tags is None:
                tags = []
            if tags != ctx.dataset.tags:
                ctx.dataset.tags = tags

        if "info" in ctx.params:
            info = ctx.params["info"]
            if info is not None:
                info = json.loads(info)
            else:
                info = {}
            if info != ctx.dataset.info:
                ctx.dataset.info = info

        app_config = _parse_app_config(ctx)
        if app_config != ctx.dataset.app_config:
            ctx.dataset.app_config = app_config

        if "classes" in ctx.params:
            classes = ctx.params["classes"]
            if classes is not None:
                classes = json.loads(classes)
            else:
                classes = {}
            if classes != ctx.dataset.classes:
                ctx.dataset.classes = classes

        if "default_classes" in ctx.params:
            default_classes = ctx.params["default_classes"]
            if default_classes is not None:
                default_classes = json.loads(default_classes)
            else:
                default_classes = []
            if default_classes != ctx.dataset.default_classes:
                ctx.dataset.default_classes = default_classes

        if "mask_targets" in ctx.params:
            mask_targets = ctx.params["mask_targets"]
            if mask_targets is not None:
                mask_targets = {
                    k: _parse_mask_targets(v)
                    for k, v in json.loads(mask_targets).items()
                }
            else:
                mask_targets = {}
            if mask_targets != ctx.dataset.mask_targets:
                ctx.dataset.mask_targets = mask_targets

        if "default_mask_targets" in ctx.params:
            default_mask_targets = ctx.params["default_mask_targets"]
            if default_mask_targets is not None:
                default_mask_targets = _parse_mask_targets(
                    json.loads(default_mask_targets)
                )
            else:
                default_mask_targets = {}
            if default_mask_targets != ctx.dataset.default_mask_targets:
                ctx.dataset.default_mask_targets = default_mask_targets

        if "skeletons" in ctx.params:
            skeletons = ctx.params["skeletons"]
            if skeletons is not None:
                skeletons = {
                    field: fo.KeypointSkeleton.from_dict(skeleton)
                    for field, skeleton in json.loads(skeletons).items()
                }
            else:
                skeletons = {}
            if skeletons != ctx.dataset.skeletons:
                ctx.dataset.skeletons = skeletons

        if "default_skeleton" in ctx.params:
            default_skeleton = ctx.params["default_skeleton"] or None
            if default_skeleton is not None:
                default_skeleton = fo.KeypointSkeleton.from_dict(
                    json.loads(default_skeleton)
                )
            if default_skeleton != ctx.dataset.default_skeleton:
                ctx.dataset.default_skeleton = default_skeleton

        ctx.trigger("reload_dataset")


def _parse_mask_targets(mask_targets):
    if fof.is_integer_mask_targets(mask_targets):
        return {int(k): v for k, v in mask_targets.items()}

    return mask_targets


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
            required=False,
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

    tags = ctx.params.get("tags", None) or []
    edited_tags = "tags" in ctx.params and tags != ctx.dataset.tags
    if edited_tags:
        num_changed += 1

    if tab_choice == "BASIC":
        inputs.list(
            "tags",
            types.String(),
            default=ctx.dataset.tags,
            required=False,
            label="Tags" + (" (edited)" if edited_tags else ""),
            description="Optional tag(s) for the dataset",
            view=types.AutocompleteView(multiple=True),
        )

    ## info

    info, valid = _parse_field(ctx, "info", type=dict)
    edited_info = "info" in ctx.params and info != ctx.dataset.info
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
    if media_fields is None:
        media_fields = ctx.dataset.app_config.media_fields

    if tab_choice == "APP_CONFIG":
        str_field_choices = types.DropdownView(multiple=True)
        for field in _get_sample_fields(ctx.dataset, fo.StringField):
            str_field_choices.add_choice(field, label=field)

        inputs.list(
            "app_config_media_fields",
            types.String(),
            default=ctx.dataset.app_config.media_fields,
            required=True,
            label="Media fields"
            + (" (edited)" if edited_media_fields else ""),
            description=(
                "The sample field(s) that contain media and should be "
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
        for field in media_fields:
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
        for field in media_fields:
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

    ## app_config.media_fallback (added in `fiftyone==0.24.0`)

    if hasattr(ctx.dataset.app_config, "media_fallback"):
        media_fallback = ctx.params.get("app_config_media_fallback", None)
        edited_media_fallback = (
            "app_config_media_fallback" in ctx.params  # can be None
            and media_fallback != ctx.dataset.app_config.media_fallback
        )
        if edited_media_fallback:
            num_changed += 1

        if tab_choice == "APP_CONFIG":
            inputs.bool(
                "app_config_media_fallback",
                default=ctx.dataset.app_config.media_fallback,
                required=True,
                description=(
                    "Whether to fall back to the default media field "
                    "`filepath` when the configured media field's value is "
                    "not defined for a sample"
                ),
                view=types.CheckboxView(
                    label="Media fallback"
                    + (" (edited)" if edited_media_fallback else ""),
                ),
            )

    ## app_config.disable_frame_filtering (added in `fiftyone==0.25.0`)

    if hasattr(ctx.dataset.app_config, "disable_frame_filtering"):
        disable_frame_filtering = ctx.params.get(
            "app_config_disable_frame_filtering", None
        )
        edited_disable_frame_filtering = (
            "app_config_disable_frame_filtering" in ctx.params  # can be None
            and disable_frame_filtering
            != ctx.dataset.app_config.disable_frame_filtering
        )
        if edited_disable_frame_filtering:
            num_changed += 1

        if tab_choice == "APP_CONFIG":
            inputs.bool(
                "app_config_disable_frame_filtering",
                default=ctx.dataset.app_config.disable_frame_filtering,
                required=False,
                description=(
                    "Whether to disable frame filtering for video datasets in "
                    "the App's grid view"
                ),
                view=types.CheckboxView(
                    label="Disable frame filtering"
                    + (" (edited)" if edited_disable_frame_filtering else ""),
                ),
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

    ## app_config.active_fields (added in `fiftyone==1.4.0`)

    if hasattr(ctx.dataset.app_config, "active_fields"):
        active_fields, valid = _parse_field(
            ctx, "app_config_active_fields", type=dict
        )
        if active_fields is not None:
            try:
                active_fields = fo.ActiveFields.from_dict(active_fields)
            except:
                valid = False
        edited_active_fields = (
            "app_config_active_fields" in ctx.params  # can be None
            and active_fields != ctx.dataset.app_config.active_fields
        )
        if edited_active_fields:
            num_changed += 1

        if tab_choice == "APP_CONFIG":
            default_active_fields = ctx.dataset.app_config.active_fields
            if default_active_fields is not None:
                default_active_fields = default_active_fields.to_json(
                    pretty_print=4
                )

            prop = inputs.str(
                "app_config_active_fields",
                default=default_active_fields,
                required=False,
                label="Active fields"
                + (" (edited)" if edited_active_fields else ""),
                description=(
                    "An optional set of dataset fields to mark as active "
                    "(visible) by default"
                ),
                view=types.CodeView(),
            )

            if not valid:
                prop.invalid = True
                prop.error_message = "Invalid active fields"

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
        "app_config_plugins" in ctx.params  # can be None
        and plugins != ctx.dataset.app_config.plugins
    )
    if edited_plugins:
        num_changed += 1

    if tab_choice == "APP_CONFIG":
        prop = inputs.str(
            "app_config_plugins",
            default=_serialize(ctx.dataset.app_config.plugins),
            required=False,
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
    edited_classes = (
        "classes" in ctx.params  # can be None
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
        "default_classes" in ctx.params  # can be None
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
    if mask_targets is not None:
        mask_targets = {
            k: _parse_mask_targets(v) for k, v in mask_targets.items()
        }
    edited_mask_targets = (
        "mask_targets" in ctx.params  # can be None
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
    if default_mask_targets is not None:
        default_mask_targets = _parse_mask_targets(default_mask_targets)
    edited_default_mask_targets = (
        "default_mask_targets" in ctx.params  # can be None
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
        "skeletons" in ctx.params  # can be None
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
            required=False,
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
    app_config = ctx.dataset.app_config.copy()

    if "app_config_media_fields" in ctx.params:
        app_config.media_fields = ctx.params["app_config_media_fields"]

    if "app_config_grid_media_field" in ctx.params:
        app_config.grid_media_field = ctx.params["app_config_grid_media_field"]

    if "app_config_modal_media_field" in ctx.params:
        app_config.modal_media_field = ctx.params[
            "app_config_modal_media_field"
        ]

    if "app_config_media_fallback" in ctx.params:
        app_config.media_fallback = ctx.params["app_config_media_fallback"]

    if "app_config_disable_frame_filtering" in ctx.params:
        app_config.disable_frame_filtering = ctx.params[
            "app_config_disable_frame_filtering"
        ]

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

    if "app_config_active_fields" in ctx.params:
        active_fields = ctx.params["app_config_active_fields"]
        if active_fields:
            active_fields = fo.ActiveFields.from_dict(
                json.loads(active_fields)
            )
        else:
            active_fields = None

        app_config.active_fields = active_fields

    if "app_config_color_scheme" in ctx.params:
        color_scheme = ctx.params["app_config_color_scheme"]
        if color_scheme:
            color_scheme = fo.ColorScheme.from_dict(json.loads(color_scheme))
        else:
            color_scheme = None

        app_config.color_scheme = color_scheme

    if "app_config_plugins" in ctx.params:
        plugins = ctx.params["app_config_plugins"]
        if plugins:
            plugins = json.loads(plugins)
        else:
            plugins = None

        app_config.plugins = plugins

    return app_config


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


class CloneDataset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="clone_dataset",
            label="Clone dataset",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_immediate_execution=True,
            allow_delegated_execution=True,
            default_choice_to_delegated=False,
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _get_clone_dataset_inputs(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Clone dataset"))

    def execute(self, ctx):
        name = ctx.params["name"]
        new_name = ctx.params["new_name"]
        persistent = ctx.params.get("persistent", True)
        target = ctx.params.get("target", None)

        if ctx.dataset.name == name:
            sample_collection = _get_target_view(ctx, target)
        else:
            dataset = fo.load_dataset(name)
            if target == "DATASET_VIEW":
                sample_collection = dataset.view()
            else:
                sample_collection = dataset

        sample_collection.clone(new_name, persistent=persistent)

        if not ctx.delegated:
            ctx.trigger("open_dataset", dict(dataset=new_name))


def _get_clone_dataset_inputs(ctx, inputs):
    datasets = sorted(fo.list_datasets())

    dataset_choices = types.AutocompleteView()
    for name in datasets:
        dataset_choices.add_choice(name, label=name)

    name_prop = inputs.enum(
        "name",
        datasets,
        default=ctx.dataset.name,
        required=True,
        label="Dataset",
        description="The dataset to clone",
        view=dataset_choices,
    )

    name = ctx.params.get("name", None)
    if name is None:
        return
    elif name not in datasets:
        name_prop.invalid = True
        name_prop = f"Invalid dataset name '{name}'"
        return

    target_choices = types.RadioGroup()

    target_choices.add_choice(
        "DATASET",
        label="Entire dataset",
        description="Clone the entire dataset",
    )

    # @todo can remove this if we require `fiftyone>=1.6.0`
    if Version(foc.VERSION) >= Version("1.6.0"):
        description = (
            "Clone the dataset (excluding indexes, views, workspaces, and "
            "runs)"
        )
    else:
        description = (
            "Clone the dataset (excluding views, workspaces, and runs)"
        )

    target_choices.add_choice(
        "DATASET_VIEW",
        label="Dataset",
        description=description,
    )

    default_target = "DATASET"

    if name == ctx.dataset.name:
        has_view = ctx.view != ctx.dataset.view()
        has_selected = bool(ctx.selected)

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Clone the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Clone the selected samples",
            )
            default_target = "SELECTED_SAMPLES"

    inputs.enum(
        "target",
        target_choices.values(),
        default=default_target,
        view=target_choices,
    )

    new_name_prop = inputs.str(
        "new_name",
        required=True,
        label="New name",
        description="Choose a name for the new dataset",
    )

    new_name = ctx.params.get("new_name", None)
    if new_name is None:
        return

    if new_name in datasets:
        new_name_prop.invalid = True
        new_name_prop.error_message = f"Dataset {new_name} already exists"

    inputs.bool(
        "persistent",
        default=True,
        required=True,
        label="Persistent",
        description="Whether to make the dataset persistent",
    )


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


class ApplySavedView(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="apply_saved_view",
            label="Apply saved view",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _apply_saved_view_inputs(ctx, inputs)

        view = types.View(label="Apply saved view")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        src_dataset = ctx.params["src_dataset"]
        src_view = ctx.params["src_view"]

        dataset = fo.load_dataset(src_dataset)
        view = dataset.load_saved_view(src_view)
        stages = view._serialize()

        try:
            view = fo.DatasetView._build(ctx.dataset, stages)
        except Exception as e:
            raise ValueError(
                (
                    "Failed to apply saved view '%s' from dataset '%s' to "
                    "dataset '%s'"
                )
                % (src_view, src_dataset, ctx.dataset.name)
            ) from e

        ctx.trigger("set_view", params={"view": serialize_view(view)})


def _apply_saved_view_inputs(ctx, inputs):
    dataset_names = fo.list_datasets()

    dataset_choices = types.AutocompleteView()
    for name in dataset_names:
        dataset_choices.add_choice(name, label=name)

    inputs.enum(
        "src_dataset",
        dataset_choices.values(),
        default=ctx.dataset.name,
        required=True,
        label="Source dataset",
        description="Choose a source dataset from which to retrieve a view",
        view=dataset_choices,
    )

    src_dataset = ctx.params.get("src_dataset", None)

    if src_dataset in dataset_names:
        src_dataset = fo.load_dataset(src_dataset)
        view_names = src_dataset.list_saved_views()

        if view_names:
            view_choices = types.AutocompleteView()
            for name in view_names:
                view_choices.add_choice(name, label=name)

            inputs.enum(
                "src_view",
                view_choices.values(),
                required=True,
                label="Saved view",
                description="Choose a saved view to apply to this dataset",
                view=view_choices,
            )
        else:
            warning = types.Warning(
                label="Dataset '%s' has no saved views" % src_dataset.name
            )
            prop = inputs.view("warning", warning)
            prop.invalid = True


def serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))


class ReloadSavedView(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="reload_saved_view",
            label="Reload saved view",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_placement(self, ctx):
        if ctx.view._is_generated and ctx.view.name is not None:
            return types.Placement(
                types.Places.SAMPLES_GRID_ACTIONS,
                types.Button(
                    label="Reload saved view",
                    icon="/assets/autorenew.svg",
                    prompt=True,
                ),
            )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _get_reload_saved_view_inputs(ctx, inputs)

        view = types.View(label="Reload saved view")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        name = ctx.params["name"]

        view = ctx.dataset.load_saved_view(name)
        view.reload()

        view_doc = ctx.dataset._get_saved_view_doc(name)
        view_doc.view_stages = [
            json_util.dumps(s) for s in view._serialize(include_uuids=False)
        ]
        # `view_stages` may not have changed so we force `last_modified_at` to
        # update just in case
        view_doc.last_modified_at = datetime.utcnow()
        view_doc.save()

        if ctx.view.name == view.name:
            ctx.trigger("set_view", params={"name": name})
            ctx.trigger("reload_dataset")


def _get_reload_saved_view_inputs(ctx, inputs):
    saved_views = _get_generated_saved_views(ctx.dataset)

    if not saved_views:
        warning = types.Warning(
            label="This dataset has no saved views that may need reloading"
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True
        return

    view_choices = types.AutocompleteView()
    for name in saved_views:
        view_choices.add_choice(name, label=name)

    if ctx.view.name in saved_views:
        default = ctx.view.name
    else:
        default = None

    inputs.enum(
        "name",
        view_choices.values(),
        default=default,
        required=True,
        label="Saved view",
        description="The name of a saved view to reload",
        view=view_choices,
    )

    name = ctx.params.get("name", None)
    if name not in saved_views:
        return

    # @todo can remove this if we require `fiftyone>=1.1.0`
    if not hasattr(ctx.dataset, "_max"):
        return

    last_modified_at = _none_max(
        getattr(ctx.dataset, "last_deletion_at", None),
        ctx.dataset._max("last_modified_at"),
    )
    if ctx.dataset._contains_videos(any_slice=True):
        last_modified_at = _none_max(
            last_modified_at,
            ctx.dataset._max("frames.last_modified_at"),
        )

    view_doc = ctx.dataset._get_saved_view_doc(name)

    if last_modified_at > view_doc.last_modified_at:
        dt = last_modified_at - view_doc.last_modified_at
        dt_str = humanize.naturaldelta(dt)
        view = types.Notice(
            label=(
                f"Saved view '{name}' may need to be reloaded.\n\n"
                f"The dataset was last modified {dt_str} after the view was "
                "generated."
            )
        )
        inputs.view("notice", view)
    else:
        dt = view_doc.last_modified_at - last_modified_at
        dt_str = humanize.naturaldelta(dt)
        view = types.Notice(
            label=(
                f"Saved view '{name}' is up-to-date.\n\n"
                f"It was generated {dt_str} after the dataset was last "
                "modified."
            )
        )
        inputs.view("notice", view)


def _get_generated_saved_views(dataset):
    generated_views = set()

    for view_doc in dataset._doc.saved_views:
        for stage_str in view_doc.view_stages:
            if '"_state"' in stage_str:
                generated_views.add(view_doc.name)

    return sorted(generated_views)


def _none_max(*args, default=None):
    return max((a for a in args if a is not None), default=default)


class ComputeMetadata(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_metadata",
            label="Compute metadata",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
            dynamic=True,
            execute_as_generator=True,
            allow_distributed_execution=True,
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

        params = dict(
            overwrite=overwrite,
            num_workers=num_workers,
        )

        return foo.execute_operator(
            self.uri,
            ctx,
            params=params,
            request_delegation=delegate,
            delegation_target=delegation_target,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _compute_metadata_inputs(ctx, inputs)

        return types.Property(
            inputs, view=types.View(label="Compute metadata")
        )

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        overwrite = ctx.params.get("overwrite", False)
        num_workers = ctx.params.get("num_workers", None)

        view = _get_target_view(ctx, target)

        if ctx.delegated:
            view.compute_metadata(overwrite=overwrite, num_workers=num_workers)
        else:
            for update in _compute_metadata_generator(
                ctx, view, overwrite=overwrite, num_workers=num_workers
            ):
                yield update

        if not ctx.delegated:
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

    inputs.bool(
        "overwrite",
        default=False,
        label="Recompute metadata for samples that already have it?",
        view=types.CheckboxView(),
    )

    if n == 0:
        return

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
            allow_delegated_execution=True,
            allow_immediate_execution=True,
            default_choice_to_delegated=True,
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

        params = dict(
            thumbnail_path=thumbnail_path,
            output_dir={"absolute_path": output_dir},
            width=width,
            height=height,
            overwrite=overwrite,
            num_workers=num_workers,
        )

        return foo.execute_operator(
            self.uri,
            ctx,
            params=params,
            request_delegation=delegate,
            delegation_target=delegation_target,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _generate_thumbnails_inputs(ctx, inputs)

        return types.Property(
            inputs, view=types.View(label="Generate thumbnails")
        )

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        width = ctx.params.get("width", None)
        height = ctx.params.get("height", None)
        thumbnail_path = ctx.params["thumbnail_path"]
        output_dir = ctx.params["output_dir"]["absolute_path"]
        overwrite = ctx.params.get("overwrite", False)
        num_workers = ctx.params.get("num_workers", None)

        view = _get_target_view(ctx, target)

        if not overwrite:
            view = view.exists(thumbnail_path, False)

        size = (width or -1, height or -1)

        # No multiprocessing allowed when running synchronously
        if not ctx.delegated:
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

        if not ctx.delegated:
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
    for field in _get_sample_fields(target_view, fo.StringField):
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


def _parse_path(ctx, key):
    value = ctx.params.get(key, None)
    return value.get("absolute_path", None) if value else None


def _get_target_view(ctx, target):
    if target == "SELECTED_LABELS":
        return ctx.view.select_labels(labels=ctx.selected_labels)

    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET_VIEW":
        return ctx.dataset.view()

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


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

        has_dataset = dataset is not None
        has_view = view is not None

        params = dict(
            fcn=fcn,
            has_dataset=has_dataset,
            has_view=has_view,
            args=args,
            kwargs=kwargs,
        )

        return foo.execute_operator(
            self.uri,
            ctx,
            params=params,
            delegation_target=delegation_target,
        )

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
    p.register(CloneDataset)
    p.register(DeleteDataset)
    p.register(DeleteSamples)
    p.register(ApplySavedView)
    p.register(ReloadSavedView)
    p.register(ComputeMetadata)
    p.register(GenerateThumbnails)
    p.register(Delegate)
