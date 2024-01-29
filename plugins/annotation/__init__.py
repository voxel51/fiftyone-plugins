"""
Annotation operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import contextlib
import json
import threading

from bson import json_util

import fiftyone as fo
import fiftyone.core.utils as fou
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.utils.annotations as foua


class RequestAnnotations(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="request_annotations",
            label="Request annotations",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = request_annotations(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Request annotations")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", None)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        anno_key = kwargs.pop("anno_key")
        backend = kwargs.pop("backend")
        kwargs.pop("delegate")

        kwargs.pop("schema_type")
        label_schema = kwargs.pop("label_schema", None)
        label_schema_fields = kwargs.pop("label_schema_fields", None)
        if label_schema:
            label_schema = json.loads(label_schema)
        elif label_schema_fields:
            label_schema = _build_label_schema(label_schema_fields)

        _inject_annotation_secrets(ctx)

        _get_backend(backend).parse_parameters(ctx, kwargs)
        kwargs = {k: v for k, v in kwargs.items() if v not in (None, [])}

        target_view = _get_target_view(ctx, target)

        # @todo can remove the context if we require `fiftyone>=0.23.0` as
        # compute_metadata() no longer uses multiprocessing
        with contextlib.ExitStack() as exit_context:
            if hasattr(fo.config, "max_process_pool_workers"):
                # Don't allow using multiprocessing to compute metadata
                ctx = fou.SetAttributes(fo.config, max_process_pool_workers=1)
                exit_context.enter_context(threading.Lock())
                exit_context.enter_context(ctx)

            target_view.annotate(
                anno_key,
                label_schema=label_schema,
                backend=backend,
                **kwargs,
            )

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def request_annotations(ctx, inputs):
    target_view = get_target_view(ctx, inputs)

    backend = get_annotation_backend(ctx, inputs)
    if backend is None:
        return False

    anno_key = get_new_anno_key(ctx, inputs)
    if anno_key is None:
        return False

    media_fields = ctx.dataset.app_config.media_fields
    if len(media_fields) > 1:
        inputs.enum(
            "media_field",
            media_fields,
            required=True,
            default="filepath",
            label="Media field",
            description=(
                "The sample field containing the path to the source media to "
                "upload"
            ),
        )

    label_schema = get_label_schema(ctx, inputs, backend, target_view)
    if not label_schema:
        return False

    get_generic_parameters(ctx, inputs)
    backend.get_parameters(ctx, inputs)

    return True


def get_new_anno_key(ctx, inputs, name="anno_key", label="Annotation key"):
    prop = inputs.str(name, label=label, required=True)

    anno_key = ctx.params.get(name, None)
    if anno_key is not None and anno_key in ctx.dataset.list_annotation_runs():
        prop.invalid = True
        prop.error_message = "Annotation key already exists"
        anno_key = None

    return anno_key


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


def get_annotation_backend(ctx, inputs):
    default_backend = fo.annotation_config.default_backend
    backends = fo.annotation_config.backends

    backend_choices = types.RadioGroup(orientation="horizontal")
    for backend in backends.keys():
        if backend == "cvat":
            label = "CVAT"
            description = "Open source annotation tool"
        elif backend == "labelbox":
            label = "Labelbox"
            description = "Data labeling platform"
        elif backend == "labelstudio":
            label = "Label Studio"
            description = "Open source data labeling tool"
        elif backend == "darwin":
            label = "V7"
            description = "AI data engine"
        else:
            label = backend
            description = None

        backend_choices.add_choice(
            backend, label=label, description=description
        )

    inputs.enum(
        "backend",
        backend_choices.values(),
        default=default_backend,
        label="Annotation backend",
        view=backend_choices,
    )

    backend = ctx.params.get("backend", default_backend)

    if backend is None:
        warning = types.Warning(
            label="You have no annotation backends configured",
            description="https://docs.voxel51.com/user_guide/annotation.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return None

    return _get_backend(backend)


def _get_backend(backend):
    if backend == "cvat":
        return CVATBackend(backend)

    if backend == "labelbox":
        return LabelboxBackend(backend)

    if backend == "labelstudio":
        return LabelStudioBackend(backend)

    if backend == "darwin":
        return V7Backend(backend)

    return AnnotationBackend(backend)


def get_label_schema(ctx, inputs, backend, view):
    schema_choices = types.TabsView()
    schema_choices.add_choice("BUILD", label="Build")
    schema_choices.add_choice("JSON", label="JSON")
    if backend.name == "cvat":
        schema_choices.add_choice("PROJECT", label="Existing project")

    inputs.enum(
        "schema_type",
        schema_choices.values(),
        required=True,
        default="BUILD",
        label="Label schema",
        description="Choose how to provide your label schema",
        view=schema_choices,
    )
    schema_type = ctx.params.get("schema_type", "BUILD")

    if schema_type == "PROJECT":
        inputs.str(
            "project_name",
            required=True,
            label="Existing project",
            description=(
                "Provide the name of an existing CVAT project to which to "
                "upload new tasks"
            ),
        )

        project_name = ctx.params.get("project_name", None)

        return project_name
    elif schema_type == "JSON":
        # @todo switch to editable JSON viewer
        prop = inputs.str(
            "label_schema",
            required=True,
            label="Paste your label schema JSON",
            description="https://docs.voxel51.com/user_guide/annotation.html#label-schema",
            view=types.CodeView(),
        )

        label_schema = ctx.params.get("label_schema", None)

        if label_schema:
            try:
                label_schema = json.loads(label_schema)
            except:
                label_schema = None
                prop.invalid = True
                prop.error_message = "Invalid JSON"
        else:
            prop.invalid = True
            prop.error_message = "Required property"

        return label_schema
    else:
        prop = inputs.list(
            "label_schema_fields",
            build_label_schema_field(ctx, backend, view),
            required=True,
            label="Label fields",
            description="Configure the field(s) in your label schema",
        )

        label_schema_fields = ctx.params.get("label_schema_fields", None)

        if not _build_label_schema(label_schema_fields):
            label_schema_fields = None
            prop.invalid = True
            prop.error_message = "Required property"

        return label_schema_fields


def build_label_schema_field(ctx, backend, view):
    field_schema = types.Object()

    scalar_types, label_types = backend.get_supported_types()

    fields = []
    if scalar_types:
        scalar_fields = view.get_field_schema(ftype=scalar_types)
        fields.extend(scalar_fields.keys())

    if label_types:
        label_fields = view.get_field_schema(embedded_doc_type=label_types)
        fields.extend(label_fields.keys())

    field_choices = types.AutocompleteView(space=6)
    for field in fields:
        field_choices.add_choice(field, label=field)

    field_schema.str(
        "field_name",
        required=True,
        label="Field name",
        description="The new or existing field name",
        view=field_choices,
    )

    field_type_choices = types.AutocompleteView(space=6)
    for field_type in backend.get_supported_type_strings():
        field_type_choices.add_choice(field_type, label=field_type)

    # @todo set default for existing fields
    field_schema.enum(
        "type",
        field_type_choices.values(),
        required=True,
        label="Field type",
        description="The type of the field",
        view=field_type_choices,
    )

    # @todo support per-class attributes
    field_schema.list(
        "classes",
        types.String(),
        label="Classes",
        description="The classes for the field (required for new fields)",
    )

    field_schema.list(
        "attributes",
        create_attribute_schema(ctx, backend),
        label="Attributes",
        description="The label attributes for the field",
    )

    return field_schema


def _build_label_schema(label_schema_fields):
    if not label_schema_fields:
        return

    label_schema = {}
    for d in label_schema_fields:
        field_name = d.get("field_name", None)
        field_type = d.get("type", None)
        classes = d.get("classes", None) or None
        attributes = d.get("attributes", None) or None

        if not field_name or not field_type:
            return

        label_schema[field_name] = {"type": field_type}

        if classes:
            label_schema["classes"] = classes

        if attributes:
            label_schema["attributes"] = attributes

    return label_schema


def create_class_schema(ctx, backend):
    class_schema = types.Object()
    class_schema.list("classes", types.String(), label="Classes")
    class_schema.list(
        "attributes",
        create_attribute_schema(ctx, backend),
        label="Attributes",
    )
    return class_schema


def create_attribute_schema(ctx, backend):
    attribute_schema = types.Object()
    attribute_schema.str(
        "name",
        label="Name",
        description="The attribute name",
        required=True,
        view=types.View(space=6),
    )
    attribute_schema.enum(
        "type",
        backend.backend.supported_attr_types,
        label="Type",
        description="The attribute type",
        view=types.View(space=6),
    )
    attribute_schema.list(
        "values",
        types.String(),
        label="Values",
        description="The attribute values",
    )

    # @todo set property type based on `type` above
    attribute_schema.str(
        "default",
        label="Default",
        description="An optional default value for the attribute",
    )

    attribute_schema.bool(
        "mutable",
        default=True,
        label="Mutable",
        description="Whether the attribute should be mutable",
        view=types.View(space=6),
    )
    attribute_schema.bool(
        "read_only",
        default=False,
        label="Read-only",
        description="Whether the attribute should be read-only",
        view=types.View(space=6),
    )

    return attribute_schema


def get_generic_parameters(ctx, inputs):
    checkbox_style = types.View(space=20)

    inputs.str(
        "options",
        view=types.Header(
            label="General options",
            description="https://docs.voxel51.com/user_guide/annotation.html#requesting-annotations",
            divider=True,
        ),
    )
    inputs.bool(
        "launch_editor",
        default=False,
        label="Launch editor",
        description=(
            "Whether to launch the annotation backend’s editor after "
            "uploading the samples"
        ),
        view=checkbox_style,
    )
    inputs.bool(
        "allow_additions",
        default=True,
        label="Allow additions",
        description=(
            "Whether to allow new labels to be added. Only applicable when "
            "editing existing label fields"
        ),
        view=checkbox_style,
    )
    inputs.bool(
        "allow_deletions",
        default=True,
        label="Allow deletions",
        description=(
            "Whether to allow new labels to be deleted. Only applicable when "
            "editing existing label fields"
        ),
        view=checkbox_style,
    )
    inputs.bool(
        "allow_label_edits",
        default=True,
        label="Allow label edits",
        description=(
            "Whether to allow the label attribute of existing labels to be "
            "modified. Only applicable when editing existing fields with "
            "label attributes"
        ),
        view=checkbox_style,
    )
    inputs.bool(
        "allow_index_edits",
        default=True,
        label="Allow index edits",
        description=(
            "Whether to allow the index attribute of existing video tracks to "
            "be modified. Only applicable when editing existing frame fields "
            "with index attributes"
        ),
        view=checkbox_style,
    )
    inputs.bool(
        "allow_spatial_edits",
        default=True,
        label="Allow spatial edits",
        description=(
            "Whether to allow edits to the spatial properties (bounding "
            "boxes, vertices, keypoints, masks, etc) of labels. Only "
            "applicable when editing existing spatial label fields"
        ),
        view=checkbox_style,
    )


class AnnotationBackend(object):
    def __init__(self, name):
        config = foua._parse_config(name, None)
        backend = config.build()

        self.name = name
        self.backend = backend

    def get_supported_type_strings(self):
        field_types = self.backend.supported_label_types
        singles = ("detection", "instance", "polyline", "polygon", "keypoint")
        return [t for t in field_types if t not in singles]

    def get_supported_types(self):
        scalar = False
        label_types = []

        for type_str in self.backend.supported_label_types:
            if type_str == "scalar":
                scalar = True
            else:
                label_type = foua._LABEL_TYPES_MAP.get(type_str, None)
                if label_type is not None:
                    label_types.append(label_type)

        if scalar:
            scalar_types = self.backend.supported_scalar_types
        else:
            scalar_types = None

        return scalar_types, label_types

    def get_parameters(self, ctx, inputs):
        pass

    def parse_parameters(self, ctx, params):
        pass


class CVATBackend(AnnotationBackend):
    def get_parameters(self, ctx, inputs):
        inputs.str(
            "cvat_header",
            view=types.Header(
                label="CVAT options",
                description="https://docs.voxel51.com/integrations/cvat.html#requesting-annotations",
                divider=True,
            ),
        )
        inputs.int(
            "task_size",
            min=1,
            default=None,
            label="Task size",
            description=(
                "The maximum number of images to upload per job. Only "
                "applicable to image tasks"
            ),
        )
        inputs.int(
            "segment_size",
            min=1,
            default=None,
            label="Segment size",
            description=(
                "The maximum number of images to upload per job. Only "
                "applicable to image tasks"
            ),
        )
        inputs.int(
            "image_quality",
            min=0,
            max=100,
            default=None,
            label="Image quality",
            description=(
                "An int in [0, 100] determining the image quality to upload "
                "to CVAT. The default is 75"
            ),
        )
        inputs.bool(
            "use_cache",
            default=True,
            label="Use cache",
            description=(
                "Whether to use a cache when uploading data. Using a cache "
                "reduces task creation time as data will be processed "
                "on-the-fly and stored in the cache when requested"
            ),
        )
        inputs.bool(
            "use_zip_chunks",
            default=True,
            label="Use zip chunks",
            description=(
                "When annotating videos, whether to upload video frames in "
                "smaller chunks. Setting this option to False may result in "
                "reduced video quality in CVAT due to size limitations on ZIP "
                "files that can be uploaded to CVAT"
            ),
        )
        inputs.int(
            "chunk_size",
            min=1,
            default=None,
            label="Chunk size",
            description="The number of frames to upload per ZIP chunk",
        )
        inputs.str(
            "job_assignee",
            default=None,
            label="Assignee",
            description=(
                "The username to assign the generated tasks. This argument "
                "can be a comma-separated list of usernames when annotating "
                "videos as each video is uploaded to a separate task"
            ),
        )
        inputs.list(
            "job_reviewers",
            types.String(),
            default=None,
            label="Reviewers",
            description=(
                "The usernames to assign as reviewers to the generated tasks. "
                "This argument can contain comma-separated lists of usernames "
                "when annotating videos as each video is uploaded to a "
                "separate task",
            ),
        )
        inputs.str(
            "task_name",
            default=None,
            label="Task name",
            description=(
                "The name to assign to the generated tasks. This argument can "
                "be a comma-separated list of strings when annotating videos "
                "as each video is uploaded to a separate task"
            ),
        )

        if ctx.params.get("schema_type", None) != "PROJECT":
            inputs.str(
                "project_name",
                default=None,
                label="Project name",
                description=(
                    "An optional project name to which to upload the created "
                    "tasks. If a project with this name exists, it will be "
                    "used, otherwise a new project is created. By default, no "
                    "project is used"
                ),
            )

        inputs.str(
            "occluded_attr",
            default=None,
            label="Occluded attribute",
            description="An attribute to use for occluded labels",
        )
        inputs.str(
            "group_id_attr",
            default=None,
            label="Group ID attribute",
            description="An attribute to use for grouping labels",
        )
        inputs.str(
            "issue_tracker",
            default=None,
            label="Issue tracker",
            description="An issue tracker to use for the generated tasks",
        )
        inputs.str(
            "organization",
            default=None,
            label="Organization",
            description="An organization to use for the generated tasks",
        )
        inputs.int(
            "frame_start",
            min=0,
            default=None,
            label="Frame start",
            description=(
                "An optional first frame of each video to upload when "
                "creating video tasks"
            ),
        )
        inputs.int(
            "frame_stop",
            min=1,
            default=None,
            label="Frame stop",
            description=(
                "An optional last frame of each video to upload when "
                "creating video tasks"
            ),
        )
        inputs.int(
            "frame_step",
            min=1,
            default=None,
            label="Frame step",
            description=(
                "An optional frame step defining which frames to sample when "
                "creating video tasks. Note that this argument cannot be "
                "provided when uploading existing tracks"
            ),
        )

    def parse_parameters(self, ctx, params):
        if "," in (params.get("job_assignee", None) or ""):
            params["job_assignee"] = params["job_assignee"].split(",")

        if any(
            "," in usernames
            for usernames in (params.get("job_reviewers", None) or [])
        ):
            params["job_reviewers"] = [
                usernames.split(",") for usernames in params["job_reviewers"]
            ]

        if "," in (params.get("task_name", None) or ""):
            params["task_name"] = params["task_name"].split(",")


class LabelboxBackend(AnnotationBackend):
    def get_parameters(self, ctx, inputs):
        inputs.str(
            "labelbox_header",
            view=types.Header(
                label="Labelbox options",
                description="https://docs.voxel51.com/integrations/labelbox.html#requesting-annotations",
                divider=True,
            ),
        )
        inputs.str(
            "project_name",
            default=None,
            label="Project name",
            description="A name to assign to the generated project",
        )
        inputs.list(
            "member",
            self.build_member(),
            default=None,
            label="Members",
            description=(
                "An optional list of users to add or invite to the project"
            ),
        )
        inputs.bool(
            "classes_as_attrs",
            default=True,
            label="Annotate classes as attributes",
            description=(
                "Whether to show the label field at the top level and "
                "annotate the class as a required attribute of each object"
            ),
        )

    def parse_parameters(self, ctx, params):
        if "member" in params:
            params["member"] = [
                (m["email"], m["role"]) for m in params["member"]
            ]

    def build_member(self):
        member_schema = types.Object()
        member_schema.str(
            "email",
            required=True,
            label="Email",
            description="Email address",
            view=types.View(space=6),
        )

        role_choices = types.DropdownView(space=6)
        role_choices.add_choice("LABELER", label="Labeler")
        role_choices.add_choice("REVIEWER", label="Reviewer")
        role_choices.add_choice("TEAM_MANAGER", label="Team manager")
        role_choices.add_choice("ADMIN", label="Admin")

        member_schema.str(
            "role",
            required=True,
            label="Role",
            description="The role to assign",
            view=role_choices,
        )

        return member_schema


class LabelStudioBackend(AnnotationBackend):
    def get_parameters(self, ctx, inputs):
        inputs.str(
            "labelstudio_header",
            view=types.Header(
                label="Label Studio options",
                description="https://docs.voxel51.com/integrations/labelstudio.html#requesting-annotations",
                divider=True,
            ),
        )
        inputs.str(
            "project_name",
            default=None,
            label="Project name",
            description="A name to assign to the generated project",
        )


class V7Backend(AnnotationBackend):
    def get_parameters(self, ctx, inputs):
        inputs.str(
            "v7_header",
            view=types.Header(
                label="V7 options",
                description="https://docs.voxel51.com/integrations/v7.html#requesting-annotations",
                divider=True,
            ),
        )
        inputs.str(
            "dataset_slug",
            default=None,
            label="Dataset slug",
            description="The name of the dataset to use or create on Darwin",
        )
        inputs.str(
            "external_storage",
            default=None,
            label="External storage",
            description=(
                "An optional sluggified name of the Darwin external storage "
                "to use. Indicates that all files should be treated as "
                "external storage"
            ),
        )


class LoadAnnotations(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_annotations",
            label="Load annotations",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = load_annotations(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        view = types.View(label="Load annotations")
        return types.Property(inputs, view=view)

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", None)

    def execute(self, ctx):
        anno_key = ctx.params["anno_key"]
        unexpected = ctx.params["unexpected"]
        cleanup = ctx.params["cleanup"]

        _inject_annotation_secrets(ctx)

        ctx.dataset.load_annotations(
            anno_key, unexpected=unexpected, cleanup=cleanup
        )
        ctx.trigger("reload_dataset")


def load_annotations(ctx, inputs):
    anno_keys = ctx.dataset.list_annotation_runs()

    if not anno_keys:
        warning = types.Warning(
            label="This dataset has no annotation runs",
            description="https://docs.voxel51.com/user_guide/annotation.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return False

    anno_key_choices = types.DropdownView()
    for anno_key in anno_keys:
        anno_key_choices.add_choice(anno_key, label=anno_key)

    inputs.str(
        "anno_key",
        default=anno_keys[0],
        required=True,
        label="Annotation key",
        description="The annotation key for which to load annotations",
        view=anno_key_choices,
    )

    unexpected_choices = types.DropdownView()
    unexpected_choices.add_choice(
        "keep",
        label="keep",
        description=(
            "Automatically keep all unexpected annotations in a field "
            "whose name matches the the label type"
        ),
    )
    unexpected_choices.add_choice(
        "ignore",
        label="ignore",
        description="Automatically ignore any unexpected annotations",
    )

    inputs.str(
        "unexpected",
        required=True,
        default="keep",
        label="Unexpected",
        description="Choose how to handle unexpected annotations",
        view=unexpected_choices,
    )

    inputs.bool(
        "cleanup",
        required=True,
        default=False,
        label="Cleanup",
        description=(
            "Whether to delete any informtation regarding this run from "
            "the annotation backend after loading the annotations"
        ),
    )

    return True


class GetAnnotationInfo(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_annotation_info",
            label="Get annotation info",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        anno_key = get_anno_key(ctx, inputs)

        if anno_key is not None:
            d = _get_annotation_info(ctx.dataset, anno_key)

            # Run info
            inputs.view(
                "info_header",
                types.Header(label="Run info", divider=True),
            )
            inputs.str(
                "info_anno_key",
                label="Annotation key",
                default=d["anno_key"],
                view=types.LabelValueView(read_only=True),
                # description=d["anno_key"]
                # view=types.MarkdownView(read_only=True),
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
                types.Header(label="Annotation config", divider=True),
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

        view = types.View(label="Get annotation info")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        anno_key = ctx.params["anno_key"]
        load_view = ctx.params.get("load_view", False)

        if load_view:
            ctx.trigger(
                "@voxel51/annotation/load_annotation_view",
                params={"anno_key": anno_key},
            )


def _get_annotation_info(dataset, anno_key):
    info = dataset.get_annotation_info(anno_key)
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
        "anno_key": anno_key,
        "timestamp": timestamp,
        "version": version,
        "config": config,
    }


class LoadAnnotationView(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_annotation_view",
            label="Load annotation view",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        get_anno_key(ctx, inputs)

        view = types.View(label="Load annotation view")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        anno_key = ctx.params["anno_key"]
        anno_view = ctx.dataset.load_annotation_view(anno_key)
        ctx.trigger("set_view", params={"view": serialize_view(anno_view)})


def serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))


class RenameAnnotationRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="rename_annotation_run",
            label="Rename annotation run",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        get_anno_key(ctx, inputs)
        get_new_anno_key(
            ctx, inputs, name="new_anno_key", label="New annotation key"
        )

        view = types.View(label="Rename annotation run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        anno_key = ctx.params["anno_key"]
        new_anno_key = ctx.params["new_anno_key"]
        ctx.dataset.rename_annotation_run(anno_key, new_anno_key)

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Rename successful")
        return types.Property(outputs, view=view)


class DeleteAnnotationRun(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_annotation_run",
            label="Delete annotation run",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        anno_key = get_anno_key(ctx, inputs, show_default=False)

        if anno_key is not None:
            inputs.bool(
                "cleanup",
                required=True,
                default=False,
                label="Cleanup",
                description=(
                    "Whether to delete any informtation regarding this run "
                    "from the annotation backend"
                ),
            )

            warning = types.Warning(
                label=f"You are about to delete annotation run '{anno_key}'"
            )
            inputs.view("warning", warning)

        view = types.View(label="Delete annotation run")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        anno_key = ctx.params["anno_key"]
        cleanup = ctx.params.get("cleanup", False)

        _inject_annotation_secrets(ctx)

        if cleanup:
            results = ctx.dataset.load_annotation_results(anno_key)
            if results:
                results.cleanup()

        ctx.dataset.delete_annotation_run(anno_key)
        ctx.trigger("reload_dataset")


def get_anno_key(ctx, inputs, show_default=True):
    anno_keys = ctx.dataset.list_annotation_runs()

    if not anno_keys:
        warning = types.Warning(
            label="This dataset has no annotation runs",
            description="https://docs.voxel51.com/user_guide/annotation.html",
        )
        prop = inputs.view("warning", warning)
        prop.invalid = True

        return

    choices = types.DropdownView()
    for anno_key in anno_keys:
        choices.add_choice(anno_key, label=anno_key)

    default = anno_keys[0] if show_default else None
    inputs.str(
        "anno_key",
        default=default,
        required=True,
        label="Annotation key",
        view=choices,
    )

    return ctx.params.get("anno_key", None)


_ANNOTATION_BACKENDS = [
    ("cvat", "FIFTYONE_CVAT_"),
    ("labelbox", "FIFTYONE_LABELBOX_"),
    ("labelstudio", "FIFTYONE_LABELSTUDIO_"),
    ("darwin", "FIFTYONE_DARWIN_"),
]


def _inject_annotation_secrets(ctx):
    for key, value in getattr(ctx, "secrets", {}).items():
        for backend, prefix in _ANNOTATION_BACKENDS:
            if key.startswith(prefix) and value:
                if backend not in fo.annotation_config.backends:
                    fo.annotation_config.backends[backend] = {}

                _key = key[len(prefix) :].lower()
                fo.annotation_config.backends[backend][_key] = value


def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", None)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=None,
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
    p.register(RequestAnnotations)
    p.register(LoadAnnotations)
    p.register(GetAnnotationInfo)
    p.register(LoadAnnotationView)
    p.register(RenameAnnotationRun)
    p.register(DeleteAnnotationRun)
