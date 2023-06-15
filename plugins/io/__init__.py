"""
I/O operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import os
import glob

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
            dir_prop = inputs.str(
                "directory",
                required=True,
                label="Directory",
            )
            directory = ctx.params.get("directory", None)

            if directory:
                n = len(glob_files(directory=directory))
                if n > 0:
                    dir_prop.view = types.View(caption=f"Found {n} files")
                else:
                    dir_prop.invalid = True
                    dir_prop.error_message = "No matching files"
        else:
            glob_prop = inputs.str(
                "glob_patt",
                required=True,
                label="Glob pattern",
            )
            glob_patt = ctx.params.get("glob_patt", None)

            if glob_patt:
                n = len(glob_files(glob_patt=glob_patt))
                if n > 0:
                    glob_prop.view = types.View(caption=f"Found {n} files")
                else:
                    glob_prop.invalid = True
                    glob_prop.error_message = "No matching files"

        return types.Property(inputs, view=types.View(label="Add samples"))

    def execute(self, ctx):
        filepaths = glob_files(
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
                loading.int("progress", view=types.ProgressView(label=label))
                yield ctx.trigger(
                    "show_output",
                    dict(
                        outputs=types.Property(loading).to_json(),
                        results={"progress": num_added / num_total},
                    ),
                )

        yield ctx.trigger("reload_dataset")


def glob_files(directory=None, glob_patt=None):
    if directory is not None:
        glob_patt = f"{directory}/*"

    try:
        return glob.glob(glob_patt, recursive=True)
    except:
        return []


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

        view = types.View(label="Export samples")
        dataset_or_view = self.get_dataset_or_view(ctx)
        if ctx.params.get("style", None) == "cloud_export":
            inputs.define_property(
                "cloud_storage_path",
                types.String(),
                label="Cloud Storage Path",
                description="The cloud storage location to export the data to. For example, 's3://my-bucket/my-folder'.",
                default="s3://",
            )

        # inputs.view(types.Notice("Exporting samples will create a new dataset."))

        view_choices = types.RadioGroup()
        view_choices.add_choice(
            "all_samples",
            label="All Samples",
            description="Export all samples in the dataset",
        )
        view_choices.add_choice(
            "current_view",
            label="Current View",
            description="Export the samples that match the current view",
        )
        view_choices.add_choice(
            "selected_samples",
            label="Selected Samples",
            description="Export the currently selected samples",
        )
        inputs.enum(
            "view",
            view_choices.values(),
            view=view_choices,
            default="all_samples",
        )
        data_choices = types.Choices()
        data_choices.add_choice(
            "media_and_labels",
            label="Media and Labels",
            description="Export the media and labels for the selected samples",
        )
        data_choices.add_choice(
            "media_only",
            label="Media Only",
            description="Export the media for the selected samples",
        )
        data_choices.add_choice(
            "labels_only",
            label="Labels Only",
            description="Export the labels for the selected samples",
        )
        data_choices.add_choice(
            "filepaths_and_tags",
            label="Filepaths and Tags",
            description="Export the filepaths and tags for the selected samples",
        )
        data_choices.add_choice(
            "filepaths_only",
            label="Filepaths Only",
            description="Export the filepaths for the selected samples",
        )
        inputs.define_property(
            "data",
            types.Enum(data_choices.values()),
            label="Media and Data",
            description="Choose what data or media to export",
            view=data_choices,
        )
        cur_data = ctx.params.get("data", None)
        if cur_data == "media_and_labels" or cur_data == "labels_only":
            labeled_dataset_types = list(get_labeled_dataset_types().keys())
            inputs.define_property(
                "label_format",
                types.Enum(labeled_dataset_types),
                default=labeled_dataset_types[0],
                label="Label Format",
                description="The format of the labels to export",
            )
            cur_label_format = ctx.params.get("label_format", None)
            needs_field = cur_label_format != "FiftyOneDataset"
            if needs_field:
                label_fields = get_label_fields(ctx.dataset)
                label_field_choices = types.Dropdown(multiple=True)
                for field in label_fields:
                    label_field_choices.add_choice(field, label=field)

                single_field = cur_label_format != "CSVDataset"
                if single_field:
                    inputs.define_property(
                        "field",
                        types.Enum(label_field_choices.values()),
                        label="Label Field",
                        description="The field containing the labels to export",
                        default=label_fields[0],
                    )
                else:
                    label_field_choices
                    inputs.define_property(
                        "fields",
                        types.List(types.String()),
                        label="Label Fields",
                        description="The fields containing the labels to export",
                        default=["ground_truth"],
                        view=label_field_choices,
                    )

        # inputs.view("estimate", types.Notice("Estimated export size: 5MB"))

        if cur_data:
            default_filepath = os.path.join(
                os.environ["HOME"], f"export-{ctx.dataset_name}"
            )
            filepath_property = inputs.define_property(
                "filepath",
                types.String(),
                label="Filepath",
                description="The filepath to export the data to. For example, '/path/to/export'.",
                default=default_filepath,
            )
            cur_filepath = ctx.params.get("filepath", None)
            if cur_filepath:
                parent_dir = os.path.dirname(cur_filepath)
                if not os.path.isdir(parent_dir):
                    filepath_property.invalid = True
                    filepath_property.error_message = (
                        "The filepath must be a valid directory"
                    )

        return types.Property(inputs, view=view)

    def get_dataset_or_view(self, ctx):
        return (
            ctx.view
            if ctx.params.get("view", None) == "current_view"
            else ctx.dataset
        )

    def execute(self, ctx):
        # The Dataset or DatasetView containing the samples you wish to export
        dataset_or_view = self.get_dataset_or_view(ctx)

        # The directory to which to write the exported dataset
        export_dir = ctx.params.get("filepath", None)

        # The name of the sample field containing the label that you wish to export
        # Used when exporting labeled datasets (e.g., classification or detection)
        label_fields = ctx.params.get("fields", None)
        label_field = ctx.params.get("field", label_fields)

        if ctx.params.get("data", None) == "media_only":
            dataset_type = fot.MediaDirectory
            label_field = None
        else:
            # The type of dataset to export
            dataset_types = get_labeled_dataset_types()
            dataset_type_name = ctx.params.get("label_format")
            dataset_type = dataset_types[dataset_type_name]

        count = dataset_or_view.count()

        # Export the dataset
        dataset_or_view.export(
            export_dir=export_dir,
            dataset_type=dataset_type,
            label_field=label_field,
        )

        return {"count": count, "export_dir": export_dir}

    def resolve_output(self, ctx):
        outputs = types.Object()
        view = types.View(label="Success! Samples Exported")
        outputs.define_property(
            "count",
            types.Number(),
            label="Number of Samples Exported",
            description="The number of samples that were exported",
        )
        outputs.define_property(
            "export_dir",
            types.String(),
            label="Export Directory",
            description="The directory that the samples were exported to",
        )
        return types.Property(outputs, view=view)


def get_labeled_dataset_types():
    keys = dir(fot)
    result = {}
    for key in keys:
        t = getattr(fot, key)
        if isinstance(t, type) and issubclass(t, fot.LabeledDataset):
            result[key] = t

    return result


def get_sample_collection_from_ctx(ctx):
    target = ctx.params.get("view", None)
    if target == "current_view":
        return ctx.view

    if target == "selected_samples":
        return ctx.dataset.select(ctx.selected)

    return ctx.dataset


def get_label_fields(dataset, dataset_type=None):
    dataset_schema = dataset.get_field_schema()
    return [
        field_name
        for field_name, field in dataset_schema.items()
        if field_name != "filepath"
    ]


def register(p):
    p.register(AddSamples)
    p.register(ExportSamples)
