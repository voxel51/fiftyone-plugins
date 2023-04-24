import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo

class ExportSamples(foo.DynamicOperator):
    def __init__(self):
        super().__init__(
            "export_samples",
            "Export Samples",
        )
        
    def resolve_input(self, ctx):
        show_estimate = False
        inputs = types.Object()
        view = types.View(label="Export samples")

        style_choices = types.RadioGroup()
        style_choices.add_choice("direct_download", label="Direct Download", description="Download the exported data directly to your computer")
        style_choices.add_choice("cloud_export", label="Cloud Export", description="Export the data to a cloud storage location")
        inputs.define_property("style", types.Enum(style_choices.values()), label="Export Style", description="", default="direct_download", view=style_choices)
        
        if (ctx.params.get("style", None) == "cloud_export"):
            inputs.define_property("cloud_storage_path", types.String(), label="Cloud Storage Path", description="The cloud storage location to export the data to. For example, 's3://my-bucket/my-folder'.", default="s3://")

        inputs.define_property("view", types.Enum(["current_filters"]), label="View and Filters", default="current_filters")
        data_choices = types.Choices()
        data_choices.add_choice("media_and_labels", label="Media and Labels", description="Export the media and labels for the selected samples")
        data_choices.add_choice("media_only", label="Media Only", description="Export the media for the selected samples")
        data_choices.add_choice("labels_only", label="Labels Only", description="Export the labels for the selected samples")
        data_choices.add_choice("filepaths_and_tags", label="Filepaths and Tags", description="Export the filepaths and tags for the selected samples")
        data_choices.add_choice("filepaths_only", label="Filepaths Only", description="Export the filepaths for the selected samples")
        inputs.define_property("data", types.Enum(data_choices.values()), label="Media and Data", description="Choose what data or media to export", view=data_choices)
        cur_data = ctx.params.get("data", None)
        if (cur_data == "media_and_labels" or cur_data == "labels_only"):
            inputs.define_property("label_format", types.Enum([
                "COCO",
                "CSV Dataset",
                "CVAT image",
                "FiftyOne Dataset",
                "FiftyOne image detections",
                "Image segmentation directory",
                "KITTI",
                "TF object detections",
                "VOC",
                "YOLO v4",
                "YOLO v5"
            ]))
            cur_label_format = ctx.params.get("label_format", None)
            needs_field = cur_label_format != "FiftyOne Dataset"
            if (needs_field):
                single_field = cur_label_format != "CSV Dataset"
                if (single_field):
                    inputs.define_property("field", types.Enum(get_label_fields(ctx.dataset)))
                else:
                    # TODO: add support for multiple selections
                    inputs.define_property("fields", types.Enum(ctx.dataset.get_field_schema().keys()))

        if show_estimate:
            inputs.define_property("estimate", types.String(), default="Estimated export size: TODO MB")

        return types.Property(inputs, view=view)

def register(p):
    p.register(ExportSamples)