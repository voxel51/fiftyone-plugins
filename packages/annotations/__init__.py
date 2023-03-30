import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

def create_anno_schema(ctx):
  inputs = types.Object()
  view = types.View(label="Request Annotations")
  # all backends
  inputs.define_property(
    "backend",
    types.Enum(fo.annotation_config.backends.keys()),
    label="Annotation Backend",
    default=fo.annotation_config.default_backend,
    description="The annotation backend to use.",
    required=True,
    view=types.RadioGroup()
  )
  cur_backend_name = ctx.params.get("backend", None)
  cur_backend = fo.annotation_config.backends[cur_backend_name] if cur_backend_name else None

  inputs.define_property(
    "media_field",
    types.SampleField(ctx.dataset),
    label="Media Field"
    default="filepath",
    required=True,
    description="The sample field containing the path to the source media to upload",
  )
  inputs.define_property(
    "launch_editor",
    types.Boolean(),
    label="Launch Editor",
    default=False,
    description="Whether to launch the annotation backend’s editor after uploading the samples",
  )
  inputs.define_property(
    "use_custom_label_schema",
    types.Boolean(),
    label="Use Custom Label Schema",
    default=False,
    description="Whether to use a custom label schema",
  )
  if (ctx.params.get("use_custom_label_schema", False)):
    inputs.define_property(
      "label_schema",
      types.String(),
      label="Label Schema",
      description="A dictionary defining the label schema to use. If this argument is provided, it takes precedence over label_field and label_type",
    )
  else:
    inputs.define_property(
      "label_field",
      types.String(),
      required=True,
      label="Label Field",
      description="A string indicating a new or existing label field to annotate"
    )
    label_type_choices = [
      types.Choice("classification", label="Classification"),
      types.Choice("classifications", label="Classifications"),
      types.Choice("detections", label="Detections"),
      types.Choice("polylines", label="Polylines"),
      types.Choice("polygons", label="Polygons"),
      types.Choice("keypoints", label="Keypoints"),
      types.Choice("segmentations", label="Segmentations"),
    ]
    inputs.define_property(
      "label_type",
      types.Enum([c.value for c in label_type_choices]),
      required=True,
      label="Label Type",
      view=types.Dropdown(
        choices=label_type_choices
      )
    )
    classDef = types.Object()
    classDef.define_property(
      "classes",
      types.List(types.String()),
      label="Classes",
    )
    attributeDef = types.Object()
    attributeDef.define_property(
      "key",
      types.String(),
      label="Name"
    )
    # TODO fix this - so the values are dynamic
    # attributeDef.define_property(
    #   "type",
    #   types.Enum(cur_backend.supported_attr_types() if cur_backend else []),
    # )
    attributeDef.define_property(
      "type",
      types.Enum(["select", "checkbox", "radio", "occluded", "text", "groud_id"]),
      label="Type"
    )
    inputs.define_property(
      "override_attributes_for_classes",
      types.Boolean(),
      label="Override Attributes for Classes",
      default=False,
    )
    classDef.define_property(
      "attributes",
      types.List(attributeDef),
      label="Attributes"
    )
    override_attributes_for_classes = ctx.params.get("override_attributes_for_classes", False)
    simpleClassDef = types.Object()
    simpleClassDef.define_property(
      "name",
      types.String(),
      label="Name",
      description="The name of the class",
    )
    inputs.define_property(
      "classes",
      types.List(
        classDef if override_attributes_for_classes else types.String(),
        min_items=1
      ),
      label="Classes",
      required=True,
    )

    attributes_style_choices = types.RadioGroup(
      choices=[
        types.Choice("default", description="Use the default label schema", label="Default"),
        types.Choice("list", description="Use a list of class names", label="List"),
        types.Choice("dict", description="Use a dictionary mapping class names to attributes", label="Dict"),
      ]
    )
    inputs.define_property(
      "attributes_style",
      types.Enum(attributes_style_choices.values()),
      label="Attributes Style",
      view=attributes_style_choices
    )
    if (ctx.params.get("attributes_style", None) == "list"):
      inputs.define_property(
        "attributes_list",
        types.List(types.String()),
        label="Attributes",
      )
    if (ctx.params.get("attributes_style", None) == "dict"):
      inputs.define_property(
        "attributes_dict",
        types.Object(),
        label="Attributes",
      )
    
    inputs.define_property(
      "use_dataset_mask_targets",
      types.Boolean(),
      label="Use Dataset Mask Targets",
      description="Use the dataset's mask targets to generate segmentation masks",
    )
    
    inputs.define_property(
      "allow_additions",
      types.Boolean(),
      default=True,
      label="Allow Additions",
      description="Whether to allow new labels to be added. Only applicable when editing existing label fields",
    )
    inputs.define_property(
      "allow_deletions",
      types.Boolean(),
      default=True,
      label="Allow Deletions",
      description="Whether to allow new labels to be deleted. Only applicable when editing existing label fields",
    )
    inputs.define_property(
      "allow_label_edits",
      types.Boolean(),
      default=True,
      label="Allow Label Edits",
      description="Whether to allow the label attribute of existing labels to be modified. Only applicable when editing existing fields with label attributes",
    )
    inputs.define_property(
      "allow_index_edits",
      types.Boolean(),
      default=True,
      label="Allow Index Edits",
      description="Whether to allow the index attribute of existing video tracks to be modified. Only applicable when editing existing frame fields with index attributes",
    )
    inputs.define_property(
      "allow_spatial_edits",
      types.Boolean(),
      default=True,
      label="Allow Spatial Edits",
      description="Whether to allow edits to the spatial properties (bounding boxes, vertices, keypoints, masks, etc) of labels. Only applicable when editing existing spatial label fields"
    )
    
  if (ctx.params.get("backend", None) == "cvat"):
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
      description="An optional ID of an existing CVAT project to which to upload the annotation tasks. By default, no project is used"
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

class RequestAnnotation(foo.DynamicOperator):
  def __init__(self):
    super().__init__(
      "request_annotation",
      "Request Annotation",
    )


  def resolve_input(self, ctx):
    return create_anno_schema(ctx)

  def execute(self, ctx):
    somehow_trigger_workflow(ctx)
    return {}

op = None

def register():
  op = RequestAnnotation()
  foo.register_operator(op)

def unregister():
  foo.unregister_operator(op)

