"""
I/O operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import os
import glob

import eta.core.utils as etau

import fiftyone as fo
import fiftyone.core.utils as fou
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.types as fot


class AddSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="add_samples",
            label="Add samples",
            dynamic=True,
            execute_as_generator=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Choose input type
        style_choices = types.RadioGroup()
        style_choices.add_choice("DIRECTORY", label="Directory")
        style_choices.add_choice("GLOB_PATTERN", label="Glob pattern")
        inputs.enum(
            "style",
            style_choices.values(),
            default="DIRECTORY",
            view=style_choices,
        )
        style = ctx.params.get("style", "DIRECTORY")

        if style == "DIRECTORY":
            # Choose a directory
            dir_prop = inputs.str(
                "directory",
                required=True,
                label="Directory",
            )
            directory = ctx.params.get("directory", None)

            # Validate
            if directory:
                n = len(_glob_files(directory=directory))
                if n > 0:
                    dir_prop.view = types.View(caption=f"Found {n} files")
                else:
                    dir_prop.invalid = True
                    dir_prop.error_message = "No matching files"
        else:
            # Choose a glob pattern
            glob_prop = inputs.str(
                "glob_patt",
                required=True,
                label="Glob pattern",
            )
            glob_patt = ctx.params.get("glob_patt", None)

            # Validate
            if glob_patt:
                n = len(_glob_files(glob_patt=glob_patt))
                if n > 0:
                    glob_prop.view = types.View(caption=f"Found {n} files")
                else:
                    glob_prop.invalid = True
                    glob_prop.error_message = "No matching files"

        return types.Property(inputs, view=types.View(label="Add samples"))

    def execute(self, ctx):
        filepaths = _glob_files(
            directory=ctx.params.get("directory", None),
            glob_patt=ctx.params.get("glob_patt", None),
        )

        if not filepaths:
            return

        batcher = fou.DynamicBatcher(
            filepaths, target_latency=0.1, max_batch_beta=2.0
        )

        num_added = 0
        num_total = len(filepaths)

        with batcher:
            for batch in batcher:
                samples = [fo.Sample(filepath=filepath) for filepath in batch]
                ctx.dataset.add_samples(samples)
                num_added += len(samples)

                label = f"Loaded {num_added} of {num_total}"
                loading = types.Object()
                loading.float("progress", view=types.ProgressView(label=label))
                yield ctx.trigger(
                    "show_output",
                    dict(
                        outputs=types.Property(loading).to_json(),
                        results={"progress": num_added / num_total},
                    ),
                )

        yield ctx.trigger("reload_dataset")


def batched_send_to_cvat(
        dataset, 
        class_list, 
        task_size: int = 100,
        label_field: str = 'detections',
    ):
    """
    CVAT only accepts tasks ~ 300 frames of size (1920, 1080).
    ~ 1200 frames of size (960, 540).
    
    Worth noting that particularly crowded frames e.g. Aluminum Can
    bales from BRA seem to be more likely to lead to timeout errors.

    Large tasks are also harder to work with, there's no way to indicate
    that a frame has been audited at the frame level, a task is either
    included in training or not, therefore it's useful to have them
    structured as reasonably small chunks.

    Currently appends an index to each task_name to indicate which chunk it is.
    The end time of the task may be more appropriate.
    """
    dataset_name = dataset.name
    complete_dataset_size = len(dataset)
    num_chunks = (complete_dataset_size // task_size) + 1

    start_point = 0
    end_point = start_point + task_size

    logging.info(f'start point = {start_point}, end point = {end_point}')
    
    for counter in range(0, num_chunks):
        if end_point >= complete_dataset_size:
            end_point = -1

        print(dataset_name)
        print(fo.list_datasets())
        dataset_chunk = dataset[start_point: end_point].clone()
        
        dataset_chunk.name = dataset_name + f'_{counter}'
        # size limit of ~ 200 images (1920 * 1080)
        
        print(dataset.name)
        
        try:
            dataset_chunk.annotate(
                'NA',
                label_field=label_field,
                label_type='detections',
                classes=class_list,
                attributes=["iscrowd"],
                launch_editor=True,
            )
        except Exception as e:
            print(dataset.name)
            print('Could not send dataset to CVAT')
            print(e)

        start_point = start_point + task_size
        end_point = end_point + task_size


class SendToCVAT(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="send_to_cvat",
            label="Send to CVAT",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Choose what view to export, if necessary
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
                view=target_choices,
                default=default_target,
            )

        target = ctx.params.get("target", default_target)
        target_view = _get_target_view(ctx, target)

        if target == "SELECTED_SAMPLES":
            target_str = "selected samples"
        elif target == "CURRENT_VIEW":
            target_str = "current view"
        else:
            target_str = "dataset"

        # Choose whether to export media and/or labels
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

        # Choose the label field(s) to export, if applicable
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

        # Choose an export directory
        if export_type is not None:
            export_prop = inputs.str(
                "task_name",
                label="Task Name",
                required=True,
                description="The name of the task in cvat",
            )
            task_name = ctx.params.get("task_name", None)

        # Estimate export size
        if export_dir is not None:
            label_field = ctx.params.get("label_field", None)
            size_bytes = _estimate_export_size(
                target_view, export_type, label_field
            )
            size_str = etau.to_human_bytes_str(size_bytes)
            label = f"Estimated export size: {size_str}"
            inputs.view("estimate", types.Notice(label=label))

        return types.Property(inputs, view=types.View(label="Export samples"))

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        export_dir = ctx.params["export_dir"]
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

        batched_send_to_cvat(
            target_view,
            ['Desktop Monitor', 'Printer'],
            task_size=30,
            label_field='detections',
        )

        return {"count": len(target_view), "task_name": task_name}

    def resolve_output(self, ctx):
        outputs = types.Object()

        outputs.int(
            "count",
            label="Number of samples exported",
            description="The number of samples that were exported",
        )
        outputs.str(
            "export_dir",
            label="Export directory",
            description="The directory that the data was exported to",
        )

        view = types.View(label="Export complete")
        return types.Property(outputs, view=view)



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

        # Choose what view to export, if necessary
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
                view=target_choices,
                default=default_target,
            )

        target = ctx.params.get("target", default_target)
        target_view = _get_target_view(ctx, target)

        if target == "SELECTED_SAMPLES":
            target_str = "selected samples"
        elif target == "CURRENT_VIEW":
            target_str = "current view"
        else:
            target_str = "dataset"

        # Choose whether to export media and/or labels
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

        # Choose the label field(s) to export, if applicable
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

        # Choose an export directory
        if export_type is not None:
            export_prop = inputs.str(
                "export_dir",
                label="Export directory",
                required=True,
                description="The directory at which to write the export",
            )
            export_dir = ctx.params.get("export_dir", None)

            if export_dir is not None and os.path.isdir(export_dir):
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

        # Estimate export size
        if export_dir is not None:
            label_field = ctx.params.get("label_field", None)
            size_bytes = _estimate_export_size(
                target_view, export_type, label_field
            )
            size_str = etau.to_human_bytes_str(size_bytes)
            label = f"Estimated export size: {size_str}"
            inputs.view("estimate", types.Notice(label=label))

        return types.Property(inputs, view=types.View(label="Export samples"))

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        export_dir = ctx.params["export_dir"]
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

        return {"count": len(target_view), "export_dir": export_dir}

    def resolve_output(self, ctx):
        outputs = types.Object()

        outputs.int(
            "count",
            label="Number of samples exported",
            description="The number of samples that were exported",
        )
        outputs.str(
            "export_dir",
            label="Export directory",
            description="The directory that the data was exported to",
        )

        view = types.View(label="Export complete")
        return types.Property(outputs, view=view)


def register(p):
    p.register(AddSamples)
    p.register(ExportSamples)
    p.register(SendToCVAT)


def _glob_files(directory=None, glob_patt=None):
    if directory is not None:
        glob_patt = f"{directory}/*"

    try:
        return glob.glob(glob_patt, recursive=True)
    except:
        return []


def _get_target_view(ctx, target):
    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


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


def _get_fields_with_type(view, label_type):
    return view.get_field_schema(embedded_doc_type=label_type).keys()


_DATASET_TYPES = {
    # Classification
    "Classification directory tree": fot.ImageClassificationDirectoryTree,
    "TF Image Classification": fot.TFImageClassificationDataset,
    # Detection
    "COCO": fot.COCODetectionDataset,
    "VOC": fot.VOCDetectionDataset,
    "KITTI": fot.KITTIDetectionDataset,
    "YOLOv4": fot.YOLOv4Dataset,
    "YOLOv5": fot.YOLOv5Dataset,
    "TF Object Detection": fot.TFObjectDetectionDataset,
    "CVAT": fot.CVATImageDataset,
    # Segmentation
    "Image segmentation": fot.ImageSegmentationDirectory,
    # Other
    "FiftyOne Dataset": fot.FiftyOneDataset,
    "CSV Dataset": fot.CSVDataset,
}

_CLASSIFICATION_TYPES = [
    "Classification directory tree",
    "TF Image Classification",
]

_DETECTION_TYPES = [
    "COCO",
    "VOC",
    "KITTI",
    "YOLOv4",
    "YOLOv5",
    "TF Object Detection",
    "CVAT",
]

_SEGMENTATION_TYPES = [
    "Image segmentation",
]

_OTHER_TYPES = [
    "FiftyOne Dataset",
    "CSV Dataset",
]
