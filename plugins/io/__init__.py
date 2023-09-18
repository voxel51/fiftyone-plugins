"""
I/O operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import multiprocessing
import os

import eta.core.utils as etau

import fiftyone as fo
import fiftyone.core.storage as fos
import fiftyone.core.utils as fou
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.types as fot


class ImportSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="import_samples",
            label="Import samples",
            dynamic=True,
            execute_as_generator=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _import_samples_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Import samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        import_type = ctx.params.get("import_type", None)

        if import_type == "MEDIA_ONLY":
            for update in _import_media_only(ctx):
                yield update
        elif import_type == "MEDIA_AND_LABELS":
            for update in _import_media_and_labels(ctx):
                yield update
        elif import_type == "LABELS_ONLY":
            for update in _import_labels_only(ctx):
                yield update

        yield ctx.trigger("reload_dataset")


def _import_samples_inputs(ctx, inputs):
    import_choices = types.Choices()
    import_choices.add_choice(
        "MEDIA_ONLY",
        label="Media only",
        description="Add new samples for media",
    )
    import_choices.add_choice(
        "LABELS_ONLY",
        label="Labels only",
        description="Add labels to existing samples",
    )
    import_choices.add_choice(
        "MEDIA_AND_LABELS",
        label="Media and labels",
        description="Add new samples with media and labels",
    )

    inputs.enum(
        "import_type",
        import_choices.values(),
        required=True,
        label="Import type",
        description="Choose what to import",
        view=import_choices,
    )
    import_type = ctx.params.get("import_type", None)

    ready = False
    if import_type == "MEDIA_ONLY":
        ready = _import_media_only_inputs(ctx, inputs)
    elif import_type == "MEDIA_AND_LABELS":
        ready = _import_media_and_labels_inputs(ctx, inputs)
    elif import_type == "LABELS_ONLY":
        ready = _import_labels_only_inputs(ctx, inputs)

    if ready and import_type in ("MEDIA_ONLY", "MEDIA_AND_LABELS"):
        _upload_media_inputs(ctx, inputs)

    return ready


def _import_media_only_inputs(ctx, inputs):
    # Choose input type
    style_choices = types.TabsView()
    style_choices.add_choice("DIRECTORY", label="Directory")
    style_choices.add_choice("GLOB_PATTERN", label="Glob pattern")
    inputs.enum(
        "style",
        style_choices.values(),
        default="DIRECTORY",
        view=style_choices,
    )
    style = ctx.params.get("style", "DIRECTORY")

    ready = False

    if style == "DIRECTORY":
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        dir_prop = inputs.file(
            "directory",
            required=True,
            label="Directory",
            description="Choose a directory of media to add to this dataset",
            view=file_explorer,
        )
        directory = _parse_path(ctx, "directory")

        if directory:
            n = len(_glob_files(directory=directory))
            if n > 0:
                ready = True
                dir_prop.view.caption = f"Found {n} files"
            else:
                dir_prop.invalid = True
                dir_prop.error_message = "No matching files"
        else:
            dir_prop.view.caption = None
    else:
        file_explorer = types.FileExplorerView(
            button_label="Provide a glob pattern...",
        )
        glob_prop = inputs.file(
            "glob_patt",
            required=True,
            label="Glob pattern",
            description=(
                "Provide a glob pattern of matching media to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        glob_patt = _parse_path(ctx, "glob_patt")

        if glob_patt:
            n = len(_glob_files(glob_patt=glob_patt))
            if n > 0:
                ready = True
                glob_prop.view.caption = f"Found {n} files"
            else:
                glob_prop.invalid = True
                glob_prop.error_message = "No matching files"
        else:
            glob_prop.view.caption = None

    if ready:
        inputs.list(
            "tags",
            types.String(),
            default=None,
            label="Tags",
            description="An optional list of tags to attach to each new sample",
        )

    return ready


def _import_media_and_labels_inputs(ctx, inputs):
    inputs.enum(
        "dataset_type",
        sorted(_DATASET_TYPES.keys()),
        required=True,
        label="Dataset type",
        description="The type of data you're importing",
    )

    dataset_type = ctx.params.get("dataset_type", None)

    if (
        dataset_type in _CLASSIFICATION_TYPES
        or dataset_type in _DETECTION_TYPES
        or dataset_type in _SEGMENTATION_TYPES
    ):
        label_field_choices = types.AutocompleteView()
        for field in _get_label_fields(ctx.dataset, dataset_type):
            label_field_choices.add_choice(field, label=field)

        inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "A new or existing field in which to store the imported labels"
            ),
            view=label_field_choices,
        )

    file_explorer = types.FileExplorerView(
        choose_dir=True,
        button_label="Choose a directory...",
    )
    inputs.file(
        "dataset_dir",
        required=True,
        label="Dataset directory",
        description=(
            "Choose the directory that contains the media and labels to add "
            "to this dataset"
        ),
        view=file_explorer,
    )
    dataset_dir = _parse_path(ctx, "dataset_dir")
    ready = bool(dataset_dir)

    _add_label_types(ctx, inputs, dataset_type)

    # @todo allow customizing `data_path`, `labels_path`, etc?

    if ready:
        inputs.bool(
            "dynamic",
            default=False,
            label="Dynamic",
            description=(
                "Whether to declare dynamic attributes of embedded document "
                "fields that are encountered"
            ),
            view=types.CheckboxView(),
        )

        inputs.list(
            "tags",
            types.String(),
            default=None,
            label="Tags",
            description="An optional list of tags to attach to each new sample",
        )

    return ready


def _import_labels_only_inputs(ctx, inputs):
    inputs.enum(
        "dataset_type",
        sorted(_DATASET_TYPES.keys()),
        required=True,
        label="Dataset type",
        description="The type of data you're importing",
    )

    dataset_type = ctx.params.get("dataset_type", None)

    if (
        dataset_type in _CLASSIFICATION_TYPES
        or dataset_type in _DETECTION_TYPES
        or dataset_type in _SEGMENTATION_TYPES
    ):
        label_field_choices = types.AutocompleteView()
        for field in _get_label_fields(ctx.dataset, dataset_type):
            label_field_choices.add_choice(field, label=field)

        inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "A new or existing field in which to store the imported labels"
            ),
            view=label_field_choices,
        )

    if dataset_type in _LABELS_DIR_TYPES:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "labels_path",
            required=True,
            label="Labels directory",
            description=(
                "Choose the directory that contains the labels to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        labels_path = _parse_path(ctx, "labels_path")
        ready = bool(labels_path)
    elif dataset_type in _LABELS_FILE_TYPES:
        file_explorer = types.FileExplorerView(button_label="Choose a file...")
        inputs.file(
            "labels_path",
            required=True,
            label="Labels path",
            description=(
                "Choose the file that contains the labels to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        labels_path = _parse_path(ctx, "labels_path")
        ready = bool(labels_path)
    else:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "dataset_dir",
            required=True,
            label="Dataset directory",
            description=(
                "Choose the directory that contains the data you wish to add "
                "to this dataset"
            ),
            view=file_explorer,
        )
        dataset_dir = _parse_path(ctx, "dataset_dir")
        ready = bool(dataset_dir)

    _add_label_types(ctx, inputs, dataset_type)

    return ready


def _add_label_types(ctx, inputs, dataset_type):
    label_types = _LABEL_TYPES.get(dataset_type, None)

    if label_types is None or etau.is_str(label_types):
        return

    label_type_choices = types.Choices()
    for field in label_types:
        label_type_choices.add_choice(field, label=field)

    inputs.list(
        "label_types",
        types.String(),
        default=None,
        label="Label types",
        description=(
            "The label type(s) to load. By default, all label types are loaded"
        ),
        view=label_type_choices,
    )


def _upload_media_inputs(ctx, inputs):
    inputs.bool(
        "upload",
        default=False,
        required=False,
        label="Upload media",
        description=(
            "You can optionally upload the media to another location before "
            "adding it to the dataset. Would you like to do this?"
        ),
        view=types.CheckboxView(),
    )
    upload = ctx.params.get("upload", False)

    if upload:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "upload_dir",
            required=False,
            label="Upload directory",
            description=(
                "Provide a directory into which to upload the selected media"
            ),
            view=file_explorer,
        )
        upload_dir = _parse_path(ctx, "upload_dir")

        if upload_dir is not None:
            inputs.bool(
                "overwrite",
                default=False,
                required=False,
                label="Overwrite existing",
                description=(
                    "Do you wish to overwrite existing media of the same name "
                    "(True) or append a unique suffix when necessary to avoid "
                    "name clashses (False)"
                ),
                view=types.CheckboxView(),
            )


def _import_media_only(ctx):
    directory = _parse_path(ctx, "directory")
    if ctx.params.get("style", None) != "DIRECTORY":
        directory = None

    glob_patt = _parse_path(ctx, "glob_patt")
    if ctx.params.get("style", None) != "GLOB_PATTERN":
        glob_patt = None

    tags = ctx.params.get("tags", None)

    filepaths = _glob_files(directory=directory, glob_patt=glob_patt)
    num_total = len(filepaths)

    if num_total == 0:
        return

    filepaths, tasks = _upload_media_tasks(ctx, filepaths)
    if tasks:
        for progress in _upload_media(ctx, tasks):
            yield progress

    batcher = fou.DynamicBatcher(
        filepaths, target_latency=0.1, max_batch_beta=2.0
    )

    num_added = 0

    with batcher:
        for batch in batcher:
            samples = [
                fo.Sample(filepath=filepath, tags=tags) for filepath in batch
            ]
            ctx.dataset._add_samples_batch(samples, True, False, True)
            num_added += len(samples)

            progress = num_added / num_total
            label = f"Loaded {num_added} of {num_total}"
            yield _set_progress(ctx, progress, label=label)


def _import_media_and_labels(ctx):
    dataset_type = ctx.params["dataset_type"]
    dataset_type = _DATASET_TYPES[dataset_type]

    dataset_dir = ctx.params["dataset_dir"]["absolute_path"]
    label_field = ctx.params.get("label_field", None)
    tags = ctx.params.get("tags", None)
    dynamic = ctx.params.get("dynamic", False)

    # Extras
    label_types = ctx.params.get("label_types", None)

    kwargs = {}
    if label_types is not None:
        kwargs["label_types"] = label_types

    ctx.dataset.add_dir(
        dataset_dir=dataset_dir,
        dataset_type=dataset_type,
        label_field=label_field,
        tags=tags,
        dynamic=dynamic,
        **kwargs,
    )

    return
    yield


def _import_labels_only(ctx):
    dataset_type = ctx.params["dataset_type"]
    dataset_type = _DATASET_TYPES[dataset_type]

    labels_path = _parse_path(ctx, "labels_path")
    dataset_dir = _parse_path(ctx, "dataset_dir")
    label_field = ctx.params.get("label_field", None)
    dynamic = ctx.params.get("dynamic", False)

    # Extras
    kwargs = {}

    label_types = ctx.params.get("label_types", None)
    if label_types is not None:
        kwargs["label_types"] = label_types

    if labels_path is not None:
        data_path = {
            os.path.basename(p): p for p in ctx.dataset.values("filepath")
        }
        ctx.dataset.merge_dir(
            data_path=data_path,
            labels_path=labels_path,
            dataset_type=dataset_type,
            label_field=label_field,
            dynamic=dynamic,
            **kwargs,
        )

    if dataset_dir is not None:
        ctx.dataset.merge_dir(
            dataset_dir=dataset_dir,
            dataset_type=dataset_type,
            label_field=label_field,
            dynamic=dynamic,
            **kwargs,
        )

    return
    yield


def _upload_media_tasks(ctx, filepaths):
    upload_dir = _parse_path(ctx, "upload_dir")
    if not ctx.params.get("upload", None):
        upload_dir = None

    if upload_dir is None:
        return filepaths, None

    overwrite = ctx.params.get("overwrite", False)

    inpaths = filepaths
    filename_maker = fou.UniqueFilenameMaker(
        output_dir=upload_dir, ignore_existing=overwrite
    )
    filepaths = [filename_maker.get_output_path(inpath) for inpath in inpaths]

    tasks = list(zip(inpaths, filepaths))

    return filepaths, tasks


def _upload_media(ctx, tasks):
    num_uploaded = 0
    num_total = len(tasks)
    num_workers = fo.config.max_thread_pool_workers or 16

    with multiprocessing.dummy.Pool(processes=num_workers) as pool:
        for _ in pool.imap_unordered(_do_upload_media, tasks):
            num_uploaded += 1
            if num_uploaded % 10 == 0:
                progress = num_uploaded / num_total
                label = f"Uploaded {num_uploaded} of {num_total}"
                yield _set_progress(ctx, progress, label=label)


def _do_upload_media(task):
    inpath, outpath = task
    fos.copy_file(inpath, outpath)


def _glob_files(directory=None, glob_patt=None):
    if directory is not None:
        glob_patt = f"{directory}/*"

    if glob_patt is None:
        return []

    return fos.get_glob_matches(glob_patt)


class MergeSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="merge_samples",
            label="Merge samples",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _merge_samples_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Merge samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        src_type = ctx.params.get("src_type", None)
        src_dataset = ctx.params.get("src_dataset", None)

        dst_type = ctx.params.get("dst_type", None)
        dst_dataset = ctx.params.get("dst_dataset", None)

        key_field = ctx.params["key_field"]
        skip_existing = ctx.params["skip_existing"]
        insert_new = ctx.params["insert_new"]
        fields = ctx.params.get("fields", None) or None
        omit_fields = ctx.params.get("omit_fields", None) or None
        merge_lists = ctx.params["merge_lists"]
        overwrite = ctx.params["overwrite"]
        expand_schema = ctx.params["expand_schema"]
        dynamic = ctx.params["dynamic"]
        include_info = ctx.params["include_info"]
        overwrite_info = ctx.params["overwrite_info"]

        src_coll = _get_merge_collection(ctx, src_type, src_dataset)
        dst_dataset = _get_merge_collection(ctx, dst_type, dst_dataset)

        dst_dataset.merge_samples(
            src_coll,
            key_field=key_field,
            skip_existing=skip_existing,
            insert_new=insert_new,
            fields=fields,
            omit_fields=omit_fields,
            merge_lists=merge_lists,
            overwrite=overwrite,
            expand_schema=expand_schema,
            dynamic=dynamic,
            include_info=include_info,
            overwrite_info=overwrite_info,
        )


def _merge_samples_inputs(ctx, inputs):
    ready = _get_src_dst_collections(ctx, inputs)
    if ready:
        _get_merge_parameters(ctx, inputs)

    return ready


def _get_src_dst_collections(ctx, inputs):
    dataset_names = fo.list_datasets()
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)

    #
    # Source view
    #

    src_choices = types.RadioGroup(orientation="horizontal")
    src_choices.add_choice(
        "DATASET",
        label="This dataset",
        description="Merge the current dataset",
    )
    default_src_type = "DATASET"

    if has_view:
        src_choices.add_choice(
            "VIEW",
            label="This view",
            description="Merge the current view",
        )
        default_src_type = "VIEW"

    if has_selected:
        src_choices.add_choice(
            "SELECTED_SAMPLES",
            label="Selected samples",
            description="Merge the selected samples",
        )
        default_src_type = "SELECTED_SAMPLES"

    src_choices.add_choice(
        "OTHER_DATASET",
        label="Another dataset",
        description="Merge another dataset",
    )

    inputs.enum(
        "src_type",
        src_choices.values(),
        required=True,
        default=default_src_type,
        label="Source",
        description="Choose a source collection that you want to merge",
        view=src_choices,
    )

    src_type = ctx.params.get("src_type", None)

    if src_type == "OTHER_DATASET":
        src_selector = types.AutocompleteView()
        for name in dataset_names:
            src_selector.add_choice(name, label=name)

        inputs.enum(
            "src_dataset",
            dataset_names,
            required=True,
            label="Choose a source dataset",
            description="Choose another dataset to merge",
            view=src_selector,
        )

        if not ctx.params.get("src_dataset", None):
            return False

    #
    # Destination dataset
    #

    if src_type == "OTHER_DATASET":
        dst_choices = types.RadioGroup(orientation="horizontal")
        dst_choices.add_choice(
            "DATASET",
            label="This dataset",
            description="Merge into this dataset",
        )
        dst_choices.add_choice(
            "OTHER_DATASET",
            label="Another dataset",
            description="Merge into another dataset",
        )

        inputs.enum(
            "dst_type",
            dst_choices.values(),
            required=True,
            default="DATASET",
            label="Destination",
            description="Choose a destination dataset to merge into",
            view=dst_choices,
        )

        dst_type = ctx.params.get("dst_type", None)
    else:
        dst_type = "OTHER_DATASET"

    if dst_type == "OTHER_DATASET":
        dst_selector = types.AutocompleteView()
        for name in dataset_names:
            dst_selector.add_choice(name, label=name)

        inputs.enum(
            "dst_dataset",
            dataset_names,
            required=True,
            label="Choose a destination dataset",
            description="Choose another dataset to merge into",
            view=dst_selector,
        )

        if not ctx.params.get("dst_dataset", None):
            return False

    return True


def _get_merge_collection(ctx, target, other_name):
    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    if target == "VIEW":
        return ctx.view

    return fo.load_dataset(other_name)


def _get_merge_parameters(ctx, inputs):
    key_fields = _get_sample_fields(ctx.view, _KEY_FIELD_TYPES)
    key_field_selector = types.AutocompleteView()
    for field in key_fields:
        key_field_selector.add_choice(field, label=field)

    inputs.enum(
        "key_field",
        key_fields,
        required=True,
        default="filepath",
        label="Key field",
        description=(
            "The sample field to use to decide whether to join with an "
            "existing sample"
        ),
        view=key_field_selector,
    )

    inputs.bool(
        "insert_new",
        required=True,
        default=True,
        label="Insert new",
        description=(
            "Whether to skip existing samples (True) or merge them (False)"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "skip_existing",
        required=True,
        default=False,
        label="Skip existing",
        description="Whether to insert new samples (True) or skip them (False)",
        view=types.CheckboxView(),
    )

    all_fields = list(ctx.view.get_field_schema().keys())

    field_choices = types.Choices()
    for field in all_fields:
        field_choices.add_choice(field, label=field)

    inputs.list(
        "fields",
        types.String(),
        default=None,
        label="Fields",
        description=(
            "An optional list of fields to which to restrict the merge. If "
            "provided, fields other than these are omitted from the source "
            "collection when merging or adding samples. One exception is that "
            "'filepath' is always included when adding new samples, since the "
            "field is required"
        ),
        view=field_choices,
    )

    omit_field_choices = types.Choices()
    for field in all_fields:
        omit_field_choices.add_choice(field, label=field)

    inputs.list(
        "omit_fields",
        types.String(),
        default=None,
        label="Omit fields",
        description=(
            "An optional list of fields to exclude from the merge. If "
            "provided, these fields are omitted from the source collection, "
            "if present, when merging or adding samples. One exception is "
            "that 'filepath' is always included when adding new samples, "
            "since the field is required"
        ),
        view=omit_field_choices,
    )

    inputs.bool(
        "merge_lists",
        required=True,
        default=True,
        label="Merge lists",
        description=(
            "Whether to merge the elements of list fields (e.g., 'tags') and "
            "label list fields (e.g., Detections fields) rather than merging "
            "the entire top-level field like other field types. For label "
            "lists fields, existing Label elements are either replaced (when "
            "'overwrite' is True) or kept (when 'overwrite' is False) when "
            "their 'id' matches a label from the provided samples"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "overwrite",
        required=True,
        default=True,
        label="Overwrite",
        description=(
            "Whether to overwrite (True) or skip (False) existing fields and "
            "label elements"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "expand_schema",
        required=True,
        default=True,
        label="Expand schema",
        description=(
            "Whether to dynamically add new fields encountered to the dataset "
            "schema. If False, an error is raised if a sample's schema is not "
            "a subset of the dataset schema"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "include_info",
        required=True,
        default=True,
        label="Include info",
        description=(
            "Whether to merge dataset-level information such as 'info' and "
            "'classes'"
        ),
        view=types.CheckboxView(),
    )

    if ctx.params.get("include_info", None):
        inputs.bool(
            "overwrite_info",
            required=True,
            default=False,
            label="Overwrite info",
            description=(
                "Whether to overwrite existing dataset-level information"
            ),
            view=types.CheckboxView(),
        )


_KEY_FIELD_TYPES = (
    fo.StringField,
    fo.ObjectIdField,
    fo.IntField,
    fo.DateField,
    fo.DateTimeField,
)


def _get_sample_fields(sample_collection, field_types):
    schema = sample_collection.get_field_schema(flat=True)
    bad_roots = tuple(
        k + "." for k, v in schema.items() if isinstance(v, fo.ListField)
    )
    return [
        path
        for path, field in schema.items()
        if (isinstance(field, field_types) and not path.startswith(bad_roots))
    ]


class MergeLabels(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="merge_labels",
            label="Merge labels",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _merge_labels_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Merge labels"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        in_field = ctx.params["in_field"]
        out_field = ctx.params["out_field"]

        view = _get_target_view(ctx, target)

        view.merge_labels(in_field, out_field)

        ctx.trigger("reload_dataset")


def _merge_labels_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    has_selected_labels = bool(ctx.selected_labels)
    default_target = None
    if has_view or has_selected or has_selected_labels:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Merge labels for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Merge labels for the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Merge labels for the selected samples",
            )
            default_target = "SELECTED_SAMPLES"

        if has_selected_labels:
            target_choices.add_choice(
                "SELECTED_LABELS",
                label="Selected labels",
                description="Merge the selected labels",
            )
            default_target = "SELECTED_LABELS"

        inputs.enum(
            "target",
            target_choices.values(),
            default=default_target,
            view=target_choices,
        )

    target = ctx.params.get("target", default_target)
    target_view = _get_target_view(ctx, target)

    field_names = _get_fields_with_type(ctx.view, fo.Label)

    in_field_selector = types.AutocompleteView()
    for field_name in field_names:
        in_field_selector.add_choice(field_name, label=field_name)

    inputs.enum(
        "in_field",
        field_names,
        required=True,
        label="Input field",
        description="Choose an input label field",
        view=in_field_selector,
    )

    in_field = ctx.params.get("in_field", None)
    if in_field is None:
        return False

    out_field_selector = types.AutocompleteView()
    for field in field_names:
        if field == in_field:
            continue

        out_field_selector.add_choice(field, label=field)

    inputs.str(
        "out_field",
        required=True,
        label="Output field",
        description=(
            "Provide the name of the output label field into which to "
            "merge the input labels. This field will be created if "
            "necessary"
        ),
        view=out_field_selector,
    )

    out_field = ctx.params.get("out_field", None)
    if out_field is None:
        return False

    if isinstance(target_view, fo.Dataset):
        inputs.view(
            "notice",
            types.Notice(
                label=f"The '{in_field}' field will be deleted after "
                f"merging its labels into the '{out_field}' field"
            ),
        )

    return True


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

        ready = _export_samples_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Export samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        export_dir = ctx.params["export_dir"]["absolute_path"]
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


def _export_samples_inputs(ctx, inputs):
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
            default=default_target,
            view=target_choices,
        )

    target = ctx.params.get("target", default_target)
    target_view = _get_target_view(ctx, target)

    if target == "SELECTED_SAMPLES":
        target_str = "selected samples"
    elif target == "CURRENT_VIEW":
        target_str = "current view"
    else:
        target_str = "dataset"

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
    if export_type is None:
        return False

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

    if export_type is not None:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        export_prop = inputs.file(
            "export_dir",
            required=True,
            label="Directory",
            description="Choose a directory at which to write the export",
            view=file_explorer,
        )
        export_dir = _parse_path(ctx, "export_dir")

        if export_dir is not None and fos.isdir(export_dir):
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

    if export_dir is not None:
        label_field = ctx.params.get("label_field", None)
        size_bytes = _estimate_export_size(
            target_view, export_type, label_field
        )
        size_str = etau.to_human_bytes_str(size_bytes)
        label = f"Estimated export size: {size_str}"
        inputs.view("estimate", types.Notice(label=label))

    if export_dir is None:
        return False

    return True


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


def _get_fields_with_type(view, type):
    if issubclass(type, fo.Field):
        return view.get_field_schema(ftype=type).keys()

    return view.get_field_schema(embedded_doc_type=type).keys()


# @todo add import-only types
# @todo add video types

_DATASET_TYPES = {
    # Classification
    "Image Classification Directory Tree": fot.ImageClassificationDirectoryTree,
    "TF Image Classification": fot.TFImageClassificationDataset,
    # Detection
    "COCO": fot.COCODetectionDataset,
    "VOC": fot.VOCDetectionDataset,
    "KITTI": fot.KITTIDetectionDataset,
    "YOLOv4": fot.YOLOv4Dataset,
    "YOLOv5": fot.YOLOv5Dataset,
    "TF Object Detection": fot.TFObjectDetectionDataset,
    "CVAT Image": fot.CVATImageDataset,
    # Segmentation
    "Image Segmentation": fot.ImageSegmentationDirectory,
    # Other
    "FiftyOne Dataset": fot.FiftyOneDataset,
    "CSV Dataset": fot.CSVDataset,
}

_LABEL_TYPES = {
    "COCO": ["detections", "segmentations", "keypoints"],
}

_CLASSIFICATION_TYPES = [
    "Image Classification Directory Tree",
    "TF Image Classification",
]

_DETECTION_TYPES = [
    "COCO",
    "VOC",
    "KITTI",
    "YOLOv4",
    "YOLOv5",
    "TF Object Detection",
    "CVAT Image",
]

_SEGMENTATION_TYPES = [
    "Image Segmentation",
]

_OTHER_TYPES = [
    "FiftyOne Dataset",
    "CSV Dataset",
]

_LABELS_FILE_TYPES = [
    "COCO",
    "CVAT Image",
    "CSV Dataset",
]

_LABELS_DIR_TYPES = [
    "VOC",
    "KITTI",
    "YOLOv4",
    "Image Segmentation",
]


class DrawLabels(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="draw_labels",
            label="Draw labels",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _draw_labels_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Draw labels"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        target = ctx.params.get("target", None)
        output_dir = ctx.params["output_dir"]["absolute_path"]
        label_fields = ctx.params.get("label_fields", None)
        overwrite = ctx.params.get("overwrite", False)

        target_view = _get_target_view(ctx, target)

        target_view.draw_labels(
            output_dir,
            label_fields=label_fields,
            overwrite=overwrite,
        )


def _draw_labels_inputs(ctx, inputs):
    has_view = ctx.view != ctx.dataset.view()
    has_selected = bool(ctx.selected)
    default_target = None
    if has_view or has_selected:
        target_choices = types.RadioGroup()
        target_choices.add_choice(
            "DATASET",
            label="Entire dataset",
            description="Draw labels for the entire dataset",
        )

        if has_view:
            target_choices.add_choice(
                "CURRENT_VIEW",
                label="Current view",
                description="Draw labels for the current view",
            )
            default_target = "CURRENT_VIEW"

        if has_selected:
            target_choices.add_choice(
                "SELECTED_SAMPLES",
                label="Selected samples",
                description="Draw labels for the selected samples",
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

    label_field_choices = types.Dropdown(multiple=True)
    for field in _get_fields_with_type(target_view, fo.Label):
        label_field_choices.add_choice(field, label=field)

    inputs.list(
        "label_fields",
        types.String(),
        required=False,
        default=None,
        label="Label fields",
        description=(
            "The label field(s) to render. By default, all labels are rendered"
        ),
        view=label_field_choices,
    )

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
            "annotated media"
        ),
        view=file_explorer,
    )
    output_dir = _parse_path(ctx, "output_dir")

    if output_dir is not None and fos.isdir(output_dir):
        inputs.bool(
            "overwrite",
            default=False,
            label=(
                "Directory already exists. Delete it before writing new "
                "media?"
            ),
            view=types.CheckboxView(),
        )

    if output_dir is None:
        return False

    return True


def _parse_path(ctx, key):
    value = ctx.params.get(key, None)
    return value.get("absolute_path", None) if value else None


def _get_target_view(ctx, target):
    if target == "SELECTED_LABELS":
        return ctx.view.select_labels(labels=ctx.selected_labels)

    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


def _set_progress(ctx, progress, label=None):
    # https://github.com/voxel51/fiftyone/pull/3516
    # return ctx.trigger("set_progress", dict(progress=progress, label=label))

    loading = types.Object()
    loading.float("progress", view=types.ProgressView(label=label))
    return ctx.trigger(
        "show_output",
        dict(
            outputs=types.Property(loading).to_json(),
            results={"progress": progress},
        ),
    )


def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", False)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=False,
        required=True,
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
                    "https://docs.voxel51.com/plugins/index.html#operators "
                    "for more information"
                )
            ),
        )


def register(p):
    p.register(ImportSamples)
    p.register(MergeSamples)
    p.register(MergeLabels)
    p.register(ExportSamples)
    p.register(DrawLabels)
