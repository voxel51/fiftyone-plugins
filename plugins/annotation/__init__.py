"""
Annotation operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


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
        params = ctx.params.copy()
        target = ctx.params.pop("target", None)
        anno_key = ctx.params.pop("anno_key")

        # Omit internal-only parameters
        _ = ctx.params.pop("use_custom_label_schema")

        target_view = _get_target_view(ctx, target)
        # target_view.annotate(anno_key, **params)

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def register(p):
    p.register(RequestAnnotations)


_DEFAULT_STYLE = types.View(space=6)
_CHECKBOX_STYLE = types.View(space=20)


def build_annotation_request(ctx):
    inputs = types.Object()
    inputs_style = types.View(label="Request annotations")

    # Target view
    target_view = get_target_view(ctx, inputs)

    # Annotation backend
    backend = get_annotation_backend(ctx, inputs)
    if backend is None:
        warning = types.Warning(
            label="You must configure an annotation backend",
            description="https://docs.voxel51.com/user_guide/annotation.html",
        )
        inputs.view("warning", warning)

        return types.Property(inputs, view=inputs_style)

    # Annotation key
    inputs.str("annotation_key", label="Annotation key", required=True)

    # Media field
    media_fields = ctx.dataset.app_config.media_fields
    if len(media_fields) > 1:
        inputs.define_property(
            "media_field",
            types.Enum(media_fields),
            label="Media field",
            default="filepath",
            required=True,
            description=(
                "The sample field containing the path to the source media to "
                "upload"
            ),
            view=_DEFAULT_STYLE,
        )

    # Label schema
    get_label_schema(ctx, inputs)

    # Backend-independent parameters
    get_generic_parameters(ctx, inputs)

    # Backend-specific parameters
    if backend == "cvat":
        get_cvat_parameters(ctx, inputs)

    return types.Property(inputs, view=inputs_style)


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
            view=target_choices,
            default=default_target,
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
        label="Annotation backend",
        default=default_backend,
        description="The annotation backend to use",
        required=True,
        view=backend_choices,
    )
    return ctx.params.get("backend", default_backend)


def get_label_schema(ctx, inputs):
    inputs.define_property(
        "use_custom_label_schema",
        types.Boolean(),
        label="Use custom label schema",
        default=False,
        description="Whether to use a custom label schema",
        view=_DEFAULT_STYLE,
    )
    use_custom_label_schema = ctx.params.get("use_custom_label_schema", False)

    if use_custom_label_schema:
        inputs.define_property(
            "label_schema_fields",
            types.List(create_field_schema(ctx)),
            label="Label schema fields",
            description="The fields to include in the label schema",
            default=[],
        )
    else:
        inputs.define_property(
            "label_schema",
            create_field_schema(ctx),
            label="Label schema",
            description="The label schema to annotate",
        )


def create_field_schema(ctx):
    field_schema = types.Object()
    field_schema.define_property(
        "field_name",
        types.String(),
        label="Field name",
        description="The name of the field",
        required=True,
        view=types.View(space=6),
    )
    field_schema.define_property(
        "type",
        types.Enum(
            [
                "detections",
                "polygons",
                "polylines",
                "points",
                "text",
                "scalar",
                "classifcation",
                "classifcations",
            ]
        ),
        label="Field type",
        description="The type of the field",
        view=types.View(space=6),
    )
    field_schema.define_property(
        "classes",
        types.List(create_class_schema(ctx)),
        label="Classes",
        description="The classes to include in the field",
        default=[],
    )
    return field_schema


def create_attribute_schema(ctx):
    attribute_schema = types.Object()
    attribute_schema.define_property(
        "attribute_name",
        types.String(),
        label="Attribute name",
        description="The name of the attribute to create",
        required=True,
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "type",
        types.Enum(["radio", "select", "checkbox", "text"]),
        label="Attribute type",
        description="The type of attribute to create",
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "values",
        types.List(types.String()),
        label="Values",
        description="The classes to include in the attribute",
        default=[],
    )
    return attribute_schema


def create_class_schema(ctx):
    class_schema = types.Object()
    class_schema.define_property(
        "classes",
        types.List(types.String()),
        label="Classes",
        required=True,
        view=types.View(space=6),
    )
    class_schema.define_property(
        "attributes",
        types.List(create_attribute_schema(ctx)),
        label="Attributes",
        required=True,
        view=types.View(space=6),
    )
    return class_schema


def get_generic_parameters(ctx, inputs):
    inputs.define_property(
        "options",
        types.String(),
        view=types.Header(label="Options", description="General options"),
    )
    inputs.define_property(
        "launch_editor",
        types.Boolean(),
        label="Launch editor",
        default=False,
        description=(
            "Whether to launch the annotation backend’s editor after "
            "uploading the samples"
        ),
        view=_DEFAULT_STYLE,
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
        view=_CHECKBOX_STYLE,
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
        view=_CHECKBOX_STYLE,
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
        view=_CHECKBOX_STYLE,
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
        view=_CHECKBOX_STYLE,
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
        view=_CHECKBOX_STYLE,
    )


def get_cvat_parameters(ctx, inputs):
    inputs.define_property(
        "cvat_header",
        types.String(),
        view=types.Header(
            label="CVAT",
            description="Settings specific for CVAT",
        ),
    )
    inputs.define_property(
        "task_size",
        types.Number(min=1),
        label="Task size",
        description=(
            "The maximum number of images to upload per job. Only applicable "
            "to image tasks"
        ),
    )
    inputs.define_property(
        "segment_size",
        types.Number(min=1),
        label="Segment size",
        description=(
            "The maximum number of images to upload per job. Only applicable "
            "to image tasks"
        ),
    )
    inputs.define_property(
        "image_quality",
        types.Number(min=0, max=100, int=True),
        default=75,
        label="Image quality",
        description=(
            "An int in [0, 100] determining the image quality to upload "
            "to CVAT"
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
        label="Chunk size",
        description="The number of frames to upload per ZIP chunk",
    )
    inputs.define_property(
        "job_assignee",
        types.String(),
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
        label="Project name",
        description="The name to assign to the generated project",
    )
    inputs.define_property(
        "project_id",
        types.String(),
        label="Project ID",
        description=(
            "An ID of an existing CVAT project to which to "
            "upload the annotation tasks"
        ),
    )
    inputs.define_property(
        "occluded_attr",
        types.String(),
        label="Occluded attribute",
        description="An attribute to use for occluded labels",
    )
    inputs.define_property(
        "group_id_attr",
        types.String(),
        label="Group ID attribute",
        description="An attribute to use for grouping labels",
    )
    inputs.define_property(
        "issue_tracker",
        types.String(),
        label="Issue tracker",
        description="An issue tracker to use for the generated tasks",
    )
    inputs.define_property(
        "organization",
        types.String(),
        label="Organization",
        description="The organization to use for the generated tasks",
    )
