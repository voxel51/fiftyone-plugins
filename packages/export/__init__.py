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

        inputs.define_property("style", types.Enum(["direct_download", "cloud_export"]), default="direct_download")
        
        if (ctx.params.get("style", None) == "cloud_export"):
            inputs.define_property("cloud_storage_path", types.String())

        inputs.define_property("view", types.Enum(["current_filters"]), default="current_filters")
        inputs.define_property("data", types.Enum([
            "media_and_labels",
            "media_only",
            "labels_only",
            "filepaths_and_tags",
            "filepaths_only"
        ]))
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

        return inputs
        

op = None

def register():
    op = ExportSamples()
    foo.register_operator(op)

def unregister():
    foo.unregister_operator(op)

def get_label_fields(dataset):
    return list(dataset.get_field_schema(embedded_doc_type=fo.Label).keys())
