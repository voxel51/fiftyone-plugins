"""
Annotation operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import json

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.utils.annotations as foua


class RequestAnnotations(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="request_annotations",
            label="Request annotations",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        return build_annotation_request(ctx)

    def execute(self, ctx):
        kwargs = ctx.params.copy()
        target = kwargs.pop("target", None)
        anno_key = kwargs.pop("anno_key")
        backend = kwargs.pop("backend")

        # Parse label schema
        kwargs.pop("schema_type")
        label_schema = kwargs.pop("label_schema", None)
        label_schema_fields = kwargs.pop("label_schema_fields", None)
        if not label_schema:
            label_schema = _build_label_schema(label_schema_fields)

        # Parse backend-specific parameters
        _get_backend(backend).parse_parameters(ctx, kwargs)

        # Remove None or [] values
        kwargs = {k: v for k, v in kwargs.items() if v not in (None, [])}

        target_view = _get_target_view(ctx, target)
        target_view.annotate(
            anno_key,
            label_schema=label_schema,
            backend=backend,
            **kwargs,
        )

        """
        return {
            "anno_key": anno_key,
            "label_schema": json.dumps(label_schema, indent=4),
            "kwargs": json.dumps(kwargs, indent=4),
        }
        """

    def resolve_output(self, ctx):
        outputs = types.Object()

        # @todo remove these outputs, just for debugging
        """
        outputs.str("anno_key", label="Annotation key")
        outputs.str(
            "label_schema",
            label="Label schema",
            # view=types.JSONView(),
        )
        outputs.str(
            "kwargs",
            label="kwargs",
            # view=types.JSONView(),
        )
        """

        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


class LoadAnnotations(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="load_annotations",
            label="Load annotations",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        anno_key_choices = types.DropdownView()
        for anno_key in ctx.dataset.list_annotation_runs():
            anno_key_choices.add_choice(anno_key, label=anno_key)

        inputs.define_property(
            "anno_key",
            types.String(),
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

        inputs.define_property(
            "unexpected",
            types.String(),
            required=True,
            default="keep",
            label="Unexpected",
            description="Choose how to handle unexpected annotations",
            view=unexpected_choices,
        )

        inputs.define_property(
            "cleanup",
            types.Boolean(),
            required=True,
            default=False,
            label="Cleanup",
            description=(
                "Whether to delete any informtation regarding this run from "
                "the annotation backend after loading the annotations"
            ),
        )

        view = types.View(label="Load annotations")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        anno_key = ctx.params["anno_key"]
        unexpected = ctx.params["unexpected"]
        cleanup = ctx.params["cleanup"]

        ctx.dataset.load_annotations(
            anno_key, unexpected=unexpected, cleanup=cleanup
        )
        ctx.trigger("reload_dataset")

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def register(p):
    p.register(RequestAnnotations)
    p.register(LoadAnnotations)


def build_annotation_request(ctx):
    inputs = types.Object()
    inputs_style = types.View(label="Request annotations")

    # Target view
    target_view = get_target_view(ctx, inputs)

    # Annotation backend
    backend = get_annotation_backend(ctx, inputs)
    if backend is None:
        return types.Property(inputs, view=inputs_style)

    # Annotation key
    anno_key = get_anno_key(ctx, inputs)
    if anno_key is None:
        return types.Property(inputs, view=inputs_style)

    # Media field
    media_fields = ctx.dataset.app_config.media_fields
    if len(media_fields) > 1:
        inputs.define_property(
            "media_field",
            types.Enum(media_fields),
            required=True,
            default="filepath",
            label="Media field",
            description=(
                "The sample field containing the path to the source media to "
                "upload"
            ),
        )

    # Label schema
    label_schema = get_label_schema(ctx, inputs, backend, target_view)
    if not label_schema:
        return types.Property(inputs, view=inputs_style)

    # Backend-independent parameters
    get_generic_parameters(ctx, inputs)

    # Backend-specific parameters
    backend.get_parameters(ctx, inputs)

    return types.Property(inputs, view=inputs_style)


def get_anno_key(ctx, inputs):
    prop = inputs.str("anno_key", label="Annotation key", required=True)
    anno_key = ctx.params.get("anno_key", None)
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
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Request annotations for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Request annotations for the current view",
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
            required=True,
            default=default_target,
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

    backend_choices = types.RadioGroup()
    for backend in backends.keys():
        if backend == "cvat":
            label = "CVAT"
            description = "Open source annotation tool"
        elif backend == "labelbox":
            label = "Labelbox"
            description = "Data labeling platform"
        elif backend == "labelstudio":
            label = "Label Studio"
            description = "Multi-type data labeling and annotation tool"
        else:
            label = backend
            description = None

        backend_choices.add_choice(
            backend, label=label, description=description
        )

    inputs.define_property(
        "backend",
        types.Enum(backend_choices.values()),
        default=default_backend,
        label="Annotation backend",
        description="The annotation backend to use",
        view=backend_choices,
    )

    backend = ctx.params.get("backend", default_backend)

    if backend is None:
        warning = types.Warning(
            label="You have no annotation backends configured",
            description="https://docs.voxel51.com/user_guide/annotation.html",
        )
        warning_prop = inputs.view("warning", warning)
        warning_prop.invalid = True

        return None

    return _get_backend(backend)


def _get_backend(backend):
    if backend == "cvat":
        return CVATBackend(backend)

    if backend == "labelbox":
        return LabelboxBackend(backend)

    if backend == "labelstudio":
        return LabelStudioBackend(backend)

    return AnnotationBackend(backend)


def get_label_schema(ctx, inputs, backend, view):
    schema_choices = types.TabsView()
    schema_choices.add_choice("BUILD", label="Build")
    schema_choices.add_choice("JSON", label="JSON")
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

    if schema_type == "JSON":
        # @todo switch to editable JSON viewer
        prop = inputs.define_property(
            "label_schema",
            types.String(),
            required=True,
            label="Paste your label schema JSON",
            description="https://docs.voxel51.com/user_guide/annotation.html#label-schema",
            # view=types.JSONView(),
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
        prop = inputs.define_property(
            "label_schema_fields",
            types.List(build_label_schema_field(ctx, backend, view)),
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

    field_schema.define_property(
        "field_name",
        types.String(),
        required=True,
        label="Field name",
        description="The new or existing field name",
        view=field_choices,
    )

    field_type_choices = types.AutocompleteView(space=6)
    for field_type in backend.get_supported_type_strings():
        field_type_choices.add_choice(field_type, label=field_type)

    # @todo set default for existing fields
    field_schema.define_property(
        "type",
        types.Enum(field_type_choices.values()),
        required=True,
        label="Field type",
        description="The type of the field",
        view=field_type_choices,
    )

    # @todo support per-class attributes
    field_schema.define_property(
        "classes",
        types.List(types.String()),
        label="Classes",
        description="The classes for the field (required for new fields)",
    )

    field_schema.define_property(
        "attributes",
        types.List(create_attribute_schema(ctx, backend)),
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
    class_schema.define_property(
        "classes",
        types.List(types.String()),
        label="Classes",
    )
    class_schema.define_property(
        "attributes",
        types.List(create_attribute_schema(ctx, backend)),
        label="Attributes",
    )
    return class_schema


def create_attribute_schema(ctx, backend):
    attribute_schema = types.Object()
    attribute_schema.define_property(
        "name",
        types.String(),
        label="Name",
        description="The attribute name",
        required=True,
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "type",
        types.Enum(backend.backend.supported_attr_types),
        label="Type",
        description="The attribute type",
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "values",
        types.List(types.String()),
        label="Values",
        description="The attribute values",
    )

    # @todo set property type based on `type` above
    attribute_schema.define_property(
        "default",
        types.String(),
        label="Default",
        description="An optional default value for the attribute",
    )

    attribute_schema.define_property(
        "mutable",
        types.Boolean(),
        default=True,
        label="Mutable",
        description="Whether the attribute should be mutable",
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "read_only",
        types.Boolean(),
        default=False,
        label="Read-only",
        description="Whether the attribute should be read-only",
        view=types.View(space=6),
    )

    return attribute_schema


def get_generic_parameters(ctx, inputs):
    checkbox_style = types.View(space=20)

    inputs.define_property(
        "options",
        types.String(),
        view=types.Header(
            label="General options",
            description="https://docs.voxel51.com/user_guide/annotation.html#requesting-annotations",
        ),
    )
    inputs.define_property(
        "launch_editor",
        types.Boolean(),
        default=False,
        label="Launch editor",
        description=(
            "Whether to launch the annotation backend’s editor after "
            "uploading the samples"
        ),
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_additions",
        types.Boolean(),
        default=True,
        label="Allow additions",
        description=(
            "Whether to allow new labels to be added. Only applicable when "
            "editing existing label fields"
        ),
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_deletions",
        types.Boolean(),
        default=True,
        label="Allow deletions",
        description=(
            "Whether to allow new labels to be deleted. Only applicable when "
            "editing existing label fields"
        ),
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_label_edits",
        types.Boolean(),
        default=True,
        label="Allow label edits",
        description=(
            "Whether to allow the label attribute of existing labels to be "
            "modified. Only applicable when editing existing fields with "
            "label attributes"
        ),
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_index_edits",
        types.Boolean(),
        default=True,
        label="Allow index edits",
        description=(
            "Whether to allow the index attribute of existing video tracks to "
            "be modified. Only applicable when editing existing frame fields "
            "with index attributes"
        ),
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_spatial_edits",
        types.Boolean(),
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
        inputs.define_property(
            "cvat_header",
            types.String(),
            view=types.Header(
                label="CVAT options",
                description="https://docs.voxel51.com/integrations/cvat.html#requesting-annotations",
            ),
        )
        inputs.define_property(
            "task_size",
            types.Number(min=1),
            default=None,
            label="Task size",
            description=(
                "The maximum number of images to upload per job. Only "
                "applicable to image tasks"
            ),
        )
        inputs.define_property(
            "segment_size",
            types.Number(min=1),
            default=None,
            label="Segment size",
            description=(
                "The maximum number of images to upload per job. Only "
                "applicable to image tasks"
            ),
        )
        inputs.define_property(
            "image_quality",
            types.Number(min=0, max=100, int=True),
            default=None,
            label="Image quality",
            description=(
                "An int in [0, 100] determining the image quality to upload "
                "to CVAT. The default is 75"
            ),
        )
        inputs.define_property(
            "use_cache",
            types.Boolean(),
            default=True,
            label="Use cache",
            description=(
                "Whether to use a cache when uploading data. Using a cache "
                "reduces task creation time as data will be processed "
                "on-the-fly and stored in the cache when requested"
            ),
        )
        inputs.define_property(
            "use_zip_chunks",
            types.Boolean(),
            default=True,
            label="Use zip chunks",
            description=(
                "When annotating videos, whether to upload video frames in "
                "smaller chunks. Setting this option to False may result in "
                "reduced video quality in CVAT due to size limitations on ZIP "
                "files that can be uploaded to CVAT"
            ),
        )
        inputs.define_property(
            "chunk_size",
            types.Number(min=1),
            default=None,
            label="Chunk size",
            description="The number of frames to upload per ZIP chunk",
        )
        inputs.define_property(
            "job_assignee",
            types.String(),
            default=None,
            label="Assignee",
            description=(
                "The username to assign the generated tasks. This argument "
                "can be a list of usernames when annotating videos as each "
                "video is uploaded to a separate task"
            ),
        )
        inputs.define_property(
            "job_reviewers",
            types.List(types.String()),
            default=None,
            label="Reviewers",
            description=(
                "The usernames to assign as reviewers to the generated tasks. "
                "This argument can be a list of lists of usernames when "
                "annotating videos as each video is uploaded to a separate "
                "task",
            ),
        )
        inputs.define_property(
            "task_name",
            types.String(),
            default=None,
            label="Task name",
            description=(
                "The name to assign to the generated tasks. This argument can "
                "be a list of strings when annotating videos as each video is "
                "uploaded to a separate task"
            ),
        )
        inputs.define_property(
            "project_name",
            types.String(),
            default=None,
            label="Project name",
            description="The name to assign to the generated project",
        )
        inputs.define_property(
            "project_id",
            types.String(),
            default=None,
            label="Project ID",
            description=(
                "An ID of an existing CVAT project to which to "
                "upload the annotation tasks"
            ),
        )
        inputs.define_property(
            "occluded_attr",
            types.String(),
            default=None,
            label="Occluded attribute",
            description="An attribute to use for occluded labels",
        )
        inputs.define_property(
            "group_id_attr",
            types.String(),
            default=None,
            label="Group ID attribute",
            description="An attribute to use for grouping labels",
        )
        inputs.define_property(
            "issue_tracker",
            types.String(),
            default=None,
            label="Issue tracker",
            description="An issue tracker to use for the generated tasks",
        )
        inputs.define_property(
            "organization",
            types.String(),
            default=None,
            label="Organization",
            description="An organization to use for the generated tasks",
        )
        inputs.define_property(
            "frame_start",
            types.Number(min=0, int=True),
            default=None,
            label="Frame start",
            description=(
                "An optional first frame of each video to upload when "
                "creating video tasks"
            ),
        )
        inputs.define_property(
            "frame_stop",
            types.Number(min=1, int=True),
            default=None,
            label="Frame stop",
            description=(
                "An optional last frame of each video to upload when "
                "creating video tasks"
            ),
        )
        inputs.define_property(
            "frame_step",
            types.Number(min=1, int=True),
            default=None,
            label="Frame step",
            description=(
                "An optional frame step defining which frames to sample when "
                "creating video tasks. Note that this argument cannot be "
                "provided when uploading existing tracks"
            ),
        )


class LabelboxBackend(AnnotationBackend):
    def get_parameters(self, ctx, inputs):
        inputs.define_property(
            "labelbox_header",
            types.String(),
            view=types.Header(
                label="Labelbox options",
                description="https://docs.voxel51.com/integrations/labelbox.html#requesting-annotations",
            ),
        )
        inputs.define_property(
            "project_name",
            types.String(),
            default=None,
            label="Project name",
            description="A name to assign to the generated project",
        )
        inputs.define_property(
            "member",
            types.List(self.create_member()),
            default=None,
            label="Members",
            description=(
                "An optional list of users to add or invite to the project"
            ),
        )
        inputs.define_property(
            "classes_as_attrs",
            types.Boolean(),
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

    def create_member(self):
        member_schema = types.Object()
        member_schema.define_property(
            "email",
            types.String(),
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

        member_schema.define_property(
            "role",
            types.String(),
            required=True,
            label="Role",
            description="The role to assign",
            view=role_choices,
        )

        return member_schema


class LabelStudioBackend(AnnotationBackend):
    def get_parameters(self, ctx, inputs):
        inputs.define_property(
            "labelstudio_header",
            types.String(),
            view=types.Header(
                label="Label Studio options",
                description="https://docs.voxel51.com/integrations/labelstudio.html#requesting-annotations",
            ),
        )
        inputs.define_property(
            "project_name",
            types.String(),
            default=None,
            label="Project name",
            description="A name to assign to the generated project",
        )
