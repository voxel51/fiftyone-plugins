import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

def create_attribute_schema(ctx):
    attribute_schema = types.Object()
    attribute_schema.define_property(
        "attribute_name",
        types.String(),
        label="Attribute Name",
        description="The name of the attribute to create.",
        required=True,
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "type",
        types.Enum(["radio", "select", "checkbox", "text"]),
        label="Attribute Type",
        description="The type of attribute to create.",
        view=types.View(space=6),
    )
    attribute_schema.define_property(
        "values",
        types.List(types.String()),
        label="Values",
        description="The classes to include in the attribute.",
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


def create_field_schema(ctx):
    field_schema = types.Object()
    field_schema.define_property(
        "field_name",
        types.String(),
        label="Field Name",
        description="The name of the field.",
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
        label="Field Type",
        description="The type of the field.",
        view=types.View(space=6),
    )
    field_schema.define_property(
        "classes",
        types.List(create_class_schema(ctx)),
        label="Classes",
        description="The classes to include in the field.",
        default=[],
    )
    return field_schema


def define_custom_label_schema(ctx, inputs):
    inputs.define_property(
        "label_schema_fields",
        types.List(create_field_schema(ctx)),
        label="Label Schema Fields",
        description="The fields to include in the label schema.",
        default=[],
    )


def create_anno_schema(ctx):
    inputs = types.Object()
    view = types.View(label="Request Annotations")
    default_view = types.View(space=6)
    target_choices = types.RadioGroup()
    target_choices.add_choice(
        "dataset",
        label="Dataset",
        description="Request annotations for the entire dataset",
    )
    target_choices.add_choice(
        "view",
        label="View",
        description=f"Request annotations for the current view ({ctx.view.count()} samples)",
    )
    target_choice = ctx.params.get("target", None)
    inputs.enum(
        "target",
        target_choices.values(),
        label="Choose what to annotate",
        view=target_choices,
    )
    inputs.str("annotation_key", label="Annotation Key", required=True)
    # all backends
    backend_keys = fo.annotation_config.backends.keys()
    backend_choices = types.RadioGroup()
    for backend_key in backend_keys:
        label = backend_key
        if backend_key == "cvat":
            label = "CVAT"
            description = "Open-source annotation tool"
        elif backend_key == "labelbox":
            label = "Labelbox"
            description = "Data labeling platform"
        elif backend_key == "labelstudio":
            label = "Label Studio"
            description = "Multi-type data labeling and annotation tool"
        backend_choices.add_choice(backend_key, label=label, description=description)

    inputs.define_property(
        "backend",
        types.Enum(backend_choices.values()),
        label="Annotation Backend",
        default=fo.annotation_config.default_backend,
        description="The annotation backend to use.",
        required=True,
        view=backend_choices,
    )
    cur_backend_name = ctx.params.get("backend", None)

    if target_choice is None or cur_backend_name is None:
        return types.Property(inputs, view=view)

    cur_backend = (
        fo.annotation_config.backends[cur_backend_name] if cur_backend_name else None
    )

    # this should only list the app_config.media_fields
    # the user is choosing the "filepath" alternative

    # if ctx.dataset.app_config.media_fields is only fiflepath, then we should not show this
    inputs.define_property(
        "media_field",
        types.Enum(ctx.dataset.app_config.media_fields),
        label="Media Field",
        default="filepath",
        required=True,
        description="The sample field containing the path to the source media to upload",
        view=default_view,
    )
    inputs.define_property(
        "use_custom_label_schema",
        types.Boolean(),
        label="Use Custom Label Schema",
        default=False,
        description="Whether to use a custom label schema",
        view=default_view,
    )
    use_custom_label_schema = ctx.params.get("use_custom_label_schema", False)

    if use_custom_label_schema:
        define_custom_label_schema(ctx, inputs)

    if not use_custom_label_schema:
        inputs.define_property(
            "label_schema",
            create_field_schema(ctx),
            label="Label Schema",
            description="The label schema to annotate.",
        )
    inputs.define_property(
        "launch_editor",
        types.Boolean(),
        label="Launch Editor",
        default=False,
        description="Whether to launch the annotation backend’s editor after uploading the samples",
        view=default_view,
    )
    inputs.define_property(
        "use_dataset_mask_targets",
        types.Boolean(),
        label="Use Dataset Mask Targets",
        description="Use the dataset's mask targets to generate segmentation masks",
    )

    checkbox_style = types.View(space=20)

    inputs.define_property(
        "allow_additions",
        types.Boolean(),
        default=True,
        label="Allow Additions",
        description="Whether to allow new labels to be added. Only applicable when editing existing label fields",
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_deletions",
        types.Boolean(),
        default=True,
        label="Allow Deletions",
        description="Whether to allow new labels to be deleted. Only applicable when editing existing label fields",
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_label_edits",
        types.Boolean(),
        default=True,
        label="Allow Label Edits",
        description="Whether to allow the label attribute of existing labels to be modified. Only applicable when editing existing fields with label attributes",
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_index_edits",
        types.Boolean(),
        default=True,
        label="Allow Index Edits",
        description="Whether to allow the index attribute of existing video tracks to be modified. Only applicable when editing existing frame fields with index attributes",
        view=checkbox_style,
    )
    inputs.define_property(
        "allow_spatial_edits",
        types.Boolean(),
        default=True,
        label="Allow Spatial Edits",
        description="Whether to allow edits to the spatial properties (bounding boxes, vertices, keypoints, masks, etc) of labels. Only applicable when editing existing spatial label fields",
        view=checkbox_style,
    )

    if ctx.params.get("backend", None) == "cvat":
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
            label="Task Size",
            description="The maximum number of images to upload per job. Not applicable to videos",
        )
        inputs.define_property(
            "segment_size",
            types.Number(min=1),
            label="Segment Size",
            description="The maximum number of images to upload per job. Not applicable to videos",
        )
        inputs.define_property(
            "image_quality",
            types.Number(min=0, max=100, int=True),
            default=75,
            label="Image Quality",
            description="An int in [0, 100] determining the image quality to upload to CVAT",
        )
        inputs.define_property(
            "use_cache",
            types.Boolean(),
            default=True,
            label="Use Cache",
            description="Whether to use a cache when uploading data. Using a cache reduces task creation time as data will be processed on-the-fly and stored in the cache when requested",
        )
        inputs.define_property(
            "use_zip_chunks",
            types.Boolean(),
            default=True,
            label="Use Zip Chunks",
            description="When annotating videos, whether to upload video frames in smaller chunks. Setting this option to False may result in reduced video quality in CVAT due to size limitations on ZIP files that can be uploaded to CVAT",
        )
        inputs.define_property(
            "chunk_size",
            types.Number(min=1),
            label="Chunk Size",
            description="The number of frames to upload per ZIP chunk",
        )
        inputs.define_property(
            "job_assignee",
            types.String(),
            label="Assignee",
            description="The username to assign the generated tasks. This argument can be a list of usernames when annotating videos as each video is uploaded to a separate task",
        )
        inputs.define_property(
            "job_reviewers",
            types.List(types.String()),
            label="Reviewers",
            description="The usernames to assign as reviewers to the generated tasks. This argument can be a list of lists of usernames when annotating videos as each video is uploaded to a separate task",
        )
        inputs.define_property(
            "task_name",
            types.String(),
            label="Task Name",
            description="The name to assign to the generated tasks. This argument can be a list of strings when annotating videos as each video is uploaded to a separate task",
        )
        inputs.define_property(
            "project_name",
            types.String(),
            label="Project Name",
            description="The name to assign to the generated project",
        )
        inputs.define_property(
            "project_id",
            types.String(),
            label="Project ID",
            description="An optional ID of an existing CVAT project to which to upload the annotation tasks. By default, no project is used",
        )
        inputs.define_property(
            "occluded_attr",
            types.String(),
            label="Occluded Attribute",
            description="The name of the attribute to use for occluded labels. If not provided, occluded labels will not be exported",
        )
        inputs.define_property(
            "group_id_attr",
            types.String(),
            label="Group ID Attribute",
            description="The name of the attribute to use for grouping labels. If not provided, labels will not be grouped",
        )
        inputs.define_property(
            "issue_tracker",
            types.String(),
            label="Issue Tracker",
            description="The issue tracker to use for the generated tasks. If not provided, no issue tracker will be used",
        )
        inputs.define_property(
            "organization",
            types.String(),
            label="Organization",
            description="The organization to use for the generated tasks. If not provided, no organization will be used",
        )

    return types.Property(inputs, view=view)


class RequestAnnotation(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="request_annotation", label="Request Annotation", dynamic=True
        )

    def resolve_input(self, ctx):
        return create_anno_schema(ctx)

    def execute(self, ctx):
        print(ctx.params)
        return {}


def register(p):
    p.register(RequestAnnotation)
