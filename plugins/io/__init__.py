"""
I/O operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import base64
import contextlib
import multiprocessing.dummy
import os

import eta.core.utils as etau

import fiftyone as fo
import fiftyone.core.fields as fof
import fiftyone.core.media as fom
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
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
            execute_as_generator=True,
        )

    def __call__(
        self,
        dataset,
        dataset_type=None,
        dataset_dir=None,
        data_path=None,
        labels_path=None,
        label_field=None,
        label_types=None,
        tags=None,
        dynamic=False,
        delegate=False,
        delegation_target=None,
        **kwargs,
    ):
        """Imports the specified media and/or labels into the given dataset.

        Example usage::

            import os

            import fiftyone as fo
            import fiftyone.operators as foo
            import fiftyone.zoo as foz

            quickstart = foz.load_zoo_dataset("quickstart")

            # A directory of images
            images_dir = os.path.dirname(quickstart.first().filepath)

            # A file of corresponding labels
            labels_path = "/tmp/labels.json"
            quickstart.export(
                dataset_type=fo.types.COCODetectionDataset,
                labels_path=labels_path,
                label_field="ground_truth",
                abs_paths=True,
            )

            dataset = fo.Dataset()
            import_samples = foo.get_operator("@voxel51/io/import_samples")

            # Import media
            import_samples(
                dataset,
                data_path=images_dir,
                tags="quickstart",
                delegate=True,
            )

            # Import labels
            import_samples(
                dataset,
                dataset_type=fo.types.COCODetectionDataset,
                labels_path=labels_path,
                label_field="ground_truth",
                label_types="detections",
                delegate=True,
            )

        Args:
            dataset: a :class:`fiftyone.core.dataset.Dataset`
            dataset_type (None): the :class:`fiftyone.types.Dataset` type of
                the dataset
            dataset_dir (None): a directory containing media and labels to
                import
            data_path (None): a directory or glob pattern of media to import
            labels_path (None): a file or directory of labels to import
            label_field (None): a new or existing field in which to store the
                imported labels, if applicable
            label_types (None): an optional label type or iterable of label
                types to load, when importing labels for dataset types that may
                contain multiple label types. By default, all labels are loaded
            tags (None): an optional tag or iterable of tags to attach to each
                sample when creating new samples
            dynamic (False): whether to declare dynamic attributes of embedded
                document fields that are encountered when importing labels
            delegate (False): whether to delegate execution
            delegation_target (None): an optional orchestrator on which to
                schedule the operation, if it is delegated
            **kwargs: optional keyword arguments to pass to the constructor of
                the :class:`fiftyone.utils.data.importers.DatasetImporter` for
                the specified ``dataset_type``
        """
        ctx = dict(dataset=dataset)
        if delegation_target is not None:
            ctx["delegation_target"] = delegation_target

        params = dict(
            label_field=label_field,
            label_types=_to_list(label_types),
            tags=_to_list(tags),
            dynamic=dynamic,
            delegate=delegate,
            kwargs=kwargs,
        )

        if dataset_dir is None and data_path is not None:
            params["import_type"] = "MEDIA_ONLY"
            try:
                assert fos.isdir(data_path)
                params["style"] = "DIRECTORY"
                params["directory"] = _to_path(data_path)
            except:
                params["style"] = "GLOB_PATTERN"
                params["glob_patt"] = _to_path(data_path)

            data_path = None
        elif dataset_dir is None and labels_path is not None:
            params["import_type"] = "LABELS_ONLY"
        else:
            params["import_type"] = "MEDIA_AND_LABELS"

        if dataset_type is not None:
            params["dataset_type"] = _get_dataset_type_label(dataset_type)

        if dataset_dir is not None:
            params["dataset_dir"] = _to_path(dataset_dir)

        if data_path is not None:
            params["data_path"] = _to_path(data_path)

        if labels_path is not None:
            params["labels_path"] = _to_path(labels_path)

        return foo.execute_operator(self.uri, ctx, params=params)

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

    if import_type == "MEDIA_ONLY":
        return _import_media_only_inputs(ctx, inputs)

    if import_type == "MEDIA_AND_LABELS":
        return _import_media_and_labels_inputs(ctx, inputs)

    if import_type == "LABELS_ONLY":
        return _import_labels_only_inputs(ctx, inputs)


def _import_media_only_inputs(ctx, inputs):
    style_choices = types.TabsView()
    style_choices.add_choice("DIRECTORY", label="Directory")
    style_choices.add_choice("GLOB_PATTERN", label="Glob pattern")
    style_choices.add_choice("UPLOAD", label="Upload")

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
        prop = inputs.file(
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
                prop.view.caption = f"Found {n} files"
            else:
                prop.invalid = True
                prop.error_message = "No matching files"
        else:
            prop.view.caption = None
    elif style == "GLOB_PATTERN":
        file_explorer = types.FileExplorerView(
            button_label="Provide a glob pattern...",
        )
        prop = inputs.file(
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
                prop.view.caption = f"Found {n} files"
            else:
                prop.invalid = True
                prop.error_message = "No matching files"
        else:
            prop.view.caption = None
    else:
        inputs.obj(
            "media_file",
            required=True,
            label="Media file",
            description="Choose a media file to add to this dataset",
            view=types.FileView(label="Media file"),
        )

        ready = bool(ctx.params.get("media_file", None))

    if not ready:
        return False

    inputs.list(
        "tags",
        types.String(),
        default=None,
        label="Tags",
        description="An optional list of tags to give each new sample",
    )

    ready = _upload_media_inputs(ctx, inputs)
    if not ready:
        return False

    # Don't allow delegation when uploading files
    return style != "UPLOAD"


def _get_import_types(dataset):
    if dataset.media_type == fom.GROUP:
        media_types = list(dataset.group_media_types.values())
    elif dataset.media_type is not None:
        media_types = [dataset.media_type]
    else:
        media_types = None

    dataset_types = []
    for d in _DATASET_TYPES:
        if not d["import"]:
            continue

        if not (
            d["media_types"] is None
            or media_types is None
            or set(media_types) & set(d["media_types"])
        ):
            continue

        dataset_types.append(d["label"])

    return sorted(dataset_types)


def _get_dataset_type(dataset_type):
    for d in _DATASET_TYPES:
        if d["label"] == dataset_type:
            return d

    return {}


def _get_dataset_type_label(dataset_type):
    if isinstance(dataset_type, str):
        dataset_type = etau.get_class(dataset_type)

    for d in _DATASET_TYPES:
        if d["dataset_type"] == dataset_type:
            return d["label"]

    raise ValueError("Unsupported dataset type: %s" % dataset_type)


def _requires_label_field(dataset_type):
    d = _get_dataset_type(dataset_type)
    return bool(d.get("label_types", None))


def _get_labels_path_type(dataset_type):
    d = _get_dataset_type(dataset_type)
    return d.get("labels_path_type", None)


def _get_labels_path_ext(dataset_type):
    d = _get_dataset_type(dataset_type)
    return d.get("labels_path_ext", None)


def _get_docs_link(dataset_type, type):
    d = _get_dataset_type(dataset_type)

    if type == "import":
        return d.get("import_docs", None)

    if type == "export":
        return d.get("export_docs", None)


def _import_media_and_labels_inputs(ctx, inputs):
    dataset_types = _get_import_types(ctx.dataset)
    inputs.enum(
        "dataset_type",
        dataset_types,
        required=True,
        label="Dataset type",
        description="The type of data you're importing",
    )

    dataset_type = ctx.params.get("dataset_type", None)
    if dataset_type is None:
        return False

    docs_link = _get_docs_link(dataset_type, type="import")
    inputs.view(
        "docs", types.Notice(label=f"Importer documentation: {docs_link}")
    )

    if _requires_label_field(dataset_type):
        label_field_choices = types.AutocompleteView()
        existing_fields = _get_label_fields(ctx.dataset, dataset_type)
        for field in existing_fields:
            label_field_choices.add_choice(field, label=field)

        prop = inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "A new or existing field in which to store the imported labels"
            ),
            view=label_field_choices,
        )

        label_field = ctx.params.get("label_field", None)
        if label_field is None:
            return False

        existing_field = ctx.dataset.get_field(label_field)
        if existing_field is not None and label_field not in existing_fields:
            prop.invalid = True
            prop.error_message = (
                f"Existing field '{label_field}' has unsupported type "
                f"{existing_field}"
            )
            return False

    tab_choices = types.TabsView()
    tab_choices.add_choice("DIRECTORY", label="Directory")
    tab_choices.add_choice("DATA_AND_LABELS", label="Data & Labels")

    inputs.enum(
        "tab",
        tab_choices.values(),
        default="DIRECTORY",
        view=tab_choices,
    )
    tab = ctx.params.get("tab", "DIRECTORY")

    if tab == "DIRECTORY":
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
        if dataset_dir is None:
            return False
    else:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "data_path",
            required=True,
            label="Data directory",
            description=(
                "Choose the directory that contains the media to add to this "
                "dataset"
            ),
            view=file_explorer,
        )
        data_path = _parse_path(ctx, "data_path")
        if data_path is None:
            return False

        labels_path_type = _get_labels_path_type(dataset_type)

        if labels_path_type == "directory":
            file_explorer = types.FileExplorerView(
                choose_dir=True,
                button_label="Choose a directory...",
            )
            inputs.file(
                "labels_path",
                required=True,
                label="Labels directory",
                description=(
                    "Choose the directory that contains the labels to add to "
                    "this dataset"
                ),
                view=file_explorer,
            )
            labels_path = _parse_path(ctx, "labels_path")
            if labels_path is None:
                return False
        elif labels_path_type == "file":
            ext = _get_labels_path_ext(dataset_type)
            file_explorer = types.FileExplorerView(
                button_label="Choose a file..."
            )
            prop = inputs.file(
                "labels_path",
                required=True,
                label="Labels path",
                description=f"Choose a {ext} file to add to this dataset",
                view=file_explorer,
            )

            labels_path = _parse_path(ctx, "labels_path")
            if labels_path is None:
                return False

            if os.path.splitext(labels_path)[1] != ext:
                prop.invalid = True
                prop.error_message = f"Please provide a {ext} path"
                return False

    _add_label_types(ctx, inputs, dataset_type)

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

    return _upload_media_inputs(ctx, inputs)


def _import_labels_only_inputs(ctx, inputs):
    dataset_types = _get_import_types(ctx.dataset)
    inputs.enum(
        "dataset_type",
        dataset_types,
        required=True,
        label="Dataset type",
        description="The type of data you're importing",
    )

    dataset_type = ctx.params.get("dataset_type", None)
    if dataset_type is None:
        return False

    docs_link = _get_docs_link(dataset_type, type="import")
    inputs.view(
        "docs", types.Notice(label=f"Importer documentation: {docs_link}")
    )

    if _requires_label_field(dataset_type):
        label_field_choices = types.AutocompleteView()
        existing_fields = _get_label_fields(ctx.dataset, dataset_type)
        for field in existing_fields:
            label_field_choices.add_choice(field, label=field)

        prop = inputs.str(
            "label_field",
            required=True,
            label="Label field",
            description=(
                "A new or existing field in which to store the imported labels"
            ),
            view=label_field_choices,
        )

        label_field = ctx.params.get("label_field", None)
        if label_field is None:
            return False

        existing_field = ctx.dataset.get_field(label_field)
        if existing_field is not None and label_field not in existing_fields:
            prop.invalid = True
            prop.error_message = (
                f"Existing field '{label_field}' has unsupported type "
                f"{existing_field}"
            )
            return False

    labels_path_type = _get_labels_path_type(dataset_type)
    tab = None

    if labels_path_type == "directory":
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
        if labels_path is None:
            return False
    elif labels_path_type == "file":
        tab_choices = types.TabsView()
        tab_choices.add_choice("FILEPATH", label="Filepath")
        tab_choices.add_choice("UPLOAD", label="Upload")

        inputs.enum(
            "tab",
            tab_choices.values(),
            default="FILEPATH",
            view=tab_choices,
        )
        tab = ctx.params.get("tab", "FILEPATH")

        if tab == "FILEPATH":
            ext = _get_labels_path_ext(dataset_type)
            file_explorer = types.FileExplorerView(
                button_label="Choose a file..."
            )
            prop = inputs.file(
                "labels_path",
                required=True,
                label="Labels path",
                description=f"Choose a {ext} file to add to this dataset",
                view=file_explorer,
            )

            labels_path = _parse_path(ctx, "labels_path")
            if labels_path is None:
                return False

            if os.path.splitext(labels_path)[1] != ext:
                prop.invalid = True
                prop.error_message = f"Please provide a {ext} path"
                return False
        else:
            inputs.obj(
                "labels_file",
                required=True,
                label="Labels file",
                description="Choose a labels file to add to this dataset",
                view=types.FileView(label="Labels file"),
            )
            labels_file = ctx.params.get("labels_file", None)
            if not labels_file:
                return False
    else:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "dataset_dir",
            required=True,
            label="Dataset directory",
            description="Choose a directory of labels to add to this dataset",
            view=file_explorer,
        )
        dataset_dir = _parse_path(ctx, "dataset_dir")
        if dataset_dir is None:
            return False

    _add_label_types(ctx, inputs, dataset_type)

    # Don't allow delegation when uploading files
    return tab != "UPLOAD"


def _add_label_types(ctx, inputs, dataset_type):
    label_types = _get_dataset_type(dataset_type).get("label_types", None)

    if label_types is None or len(label_types) <= 1:
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
    style = ctx.params.get("style", None)

    if style == "UPLOAD":
        upload = True
    else:
        inputs.bool(
            "upload",
            default=False,
            required=False,
            label="Upload media",
            description=(
                "You can optionally upload the media to another location "
                "before adding it to the dataset. Would you like to do this?"
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
            required=True,
            label="Upload directory",
            description="Provide a directory into which to upload the media",
            view=file_explorer,
        )
        upload_dir = _parse_path(ctx, "upload_dir")

        if upload_dir is None:
            return False

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

    return True


def _upload_media_bytes(ctx):
    media_obj = ctx.params["media_file"]
    upload_dir = _parse_path(ctx, "upload_dir")
    overwrite = ctx.params["overwrite"]
    filename = media_obj["name"]
    content = base64.b64decode(media_obj["content"])

    if overwrite:
        outpath = fos.join(upload_dir, filename)
    else:
        filename_maker = fou.UniqueFilenameMaker(output_dir=upload_dir)
        outpath = filename_maker.get_output_path(input_path=filename)

    fos.write_file(content, outpath)
    return outpath


def _import_media_only(ctx):
    style = ctx.params.get("style", None)
    tags = ctx.params.get("tags", None)

    if style == "UPLOAD":
        filepath = _upload_media_bytes(ctx)

        sample = fo.Sample(filepath=filepath, tags=tags)
        ctx.dataset.add_sample(sample)

        return

    directory = _parse_path(ctx, "directory")
    if style != "DIRECTORY":
        directory = None

    glob_patt = _parse_path(ctx, "glob_patt")
    if style != "GLOB_PATTERN":
        glob_patt = None

    filepaths = _glob_files(directory=directory, glob_patt=glob_patt)
    num_total = len(filepaths)

    if num_total == 0:
        return

    filepaths, tasks = _upload_media_tasks(ctx, filepaths)
    if tasks:
        for progress in _upload_media(ctx, tasks):
            yield progress

    make_sample = lambda f: fo.Sample(filepath=f, tags=tags)
    delegate = ctx.params.get("delegate", False)

    if delegate:
        samples = map(make_sample, filepaths)
        ctx.dataset.add_samples(samples, num_samples=len(filepaths))
        return

    batcher = fou.DynamicBatcher(
        filepaths, target_latency=0.2, max_batch_beta=2.0
    )

    num_added = 0

    with batcher:
        for batch in batcher:
            num_added += len(batch)
            samples = map(make_sample, batch)
            ctx.dataset._add_samples_batch(samples, True, False, True)

            progress = num_added / num_total
            label = f"Loaded {num_added} of {num_total}"
            yield ctx.trigger(
                "set_progress", dict(progress=progress, label=label)
            )


def _import_media_and_labels(ctx):
    dataset_type = ctx.params["dataset_type"]
    dataset_type = _get_dataset_type(dataset_type)["dataset_type"]

    dataset_dir = _parse_path(ctx, "dataset_dir")
    data_path = _parse_path(ctx, "data_path")
    labels_path = _parse_path(ctx, "labels_path")
    label_field = ctx.params.get("label_field", None)
    label_types = ctx.params.get("label_types", None)
    tags = ctx.params.get("tags", None)
    dynamic = ctx.params.get("dynamic", False)
    kwargs = ctx.params.get("kwargs", {})

    if label_types is not None:
        kwargs["label_types"] = label_types

    ctx.dataset.add_dir(
        dataset_dir=dataset_dir,
        dataset_type=dataset_type,
        data_path=data_path,
        labels_path=labels_path,
        label_field=label_field,
        tags=tags,
        dynamic=dynamic,
        **kwargs,
    )

    return
    yield


def _upload_labels_bytes(ctx, tmp_dir):
    labels_obj = ctx.params["labels_file"]
    filename = labels_obj["name"]
    content = base64.b64decode(labels_obj["content"])

    outpath = fos.join(tmp_dir, filename)
    fos.write_file(content, outpath)
    return outpath


def _import_labels_only(ctx):
    dataset_type = ctx.params["dataset_type"]
    dataset_type = _get_dataset_type(dataset_type)["dataset_type"]

    labels_file = ctx.params.get("labels_file", None)
    labels_path = _parse_path(ctx, "labels_path")
    dataset_dir = _parse_path(ctx, "dataset_dir")
    label_field = ctx.params.get("label_field", None)
    dynamic = ctx.params.get("dynamic", False)
    kwargs = ctx.params.get("kwargs", {})

    label_types = ctx.params.get("label_types", None)
    if label_types is not None:
        kwargs["label_types"] = label_types

    with contextlib.ExitStack() as exit_context:
        if labels_file is not None:
            tmp_dir = exit_context.enter_context(fos.TempDir())
            labels_path = _upload_labels_bytes(ctx, tmp_dir)

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
    delegate = ctx.params.get("delegate", False)

    if delegate:
        inpaths, outpaths = zip(*tasks)
        fos.copy_files(inpaths, outpaths)
        return

    num_uploaded = 0
    num_total = len(tasks)

    # @todo can switch to this if we require `fiftyone>=0.22.2`
    # num_workers = fou.recommend_thread_pool_workers()

    if hasattr(fou, "recommend_thread_pool_workers"):
        num_workers = fou.recommend_thread_pool_workers()
    else:
        num_workers = fo.config.max_thread_pool_workers or 8

    with multiprocessing.dummy.Pool(processes=num_workers) as pool:
        for _ in pool.imap_unordered(_do_upload_media, tasks):
            num_uploaded += 1
            if num_uploaded % 10 == 0:
                progress = num_uploaded / num_total
                label = f"Uploaded {num_uploaded} of {num_total}"
                yield ctx.trigger(
                    "set_progress", dict(progress=progress, label=label)
                )


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
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
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

        if dst_dataset is ctx.dataset:
            ctx.trigger("reload_dataset")


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

        src_dataset = ctx.params.get("src_dataset", None)
        if src_dataset is None or src_dataset not in dataset_names:
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

        dst_dataset = ctx.params.get("dst_dataset", None)
        if dst_dataset is None or dst_dataset not in dataset_names:
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
            "Whether to insert new samples (True) or skip them (False)"
        ),
        view=types.CheckboxView(),
    )

    inputs.bool(
        "skip_existing",
        required=True,
        default=False,
        label="Skip existing",
        description="Whether to skip existing samples (True) or merge them (False)",
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
        "dynamic",
        required=True,
        default=False,
        label="Dynamic",
        description=(
            "Whether to declare dynamic attributes of embedded document "
            "fields that are encountered"
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
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
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
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def __call__(
        self,
        sample_collection,
        export_dir=None,
        dataset_type=None,
        data_path=None,
        labels_path=None,
        export_media=None,
        label_field=None,
        overwrite=False,
        delegate=False,
        delegation_target=None,
        **kwargs,
    ):
        """Exports the specified media and/or/labels from the given sample
        collection.

        Example usage::

            import fiftyone as fo
            import fiftyone.operators as foo
            import fiftyone.zoo as foz

            dataset = foz.load_zoo_dataset("quickstart")
            export_samples = foo.get_operator("@voxel51/io/export_samples")

            # Export labels
            export_samples(
                dataset,
                dataset_type=fo.types.COCODetectionDataset,
                labels_path="/tmp/labels.json",
                label_field="ground_truth",
                abs_paths=True,
                delegate=True,
            )

            # Export filepaths
            export_samples(
                dataset,
                dataset_type=fo.types.CSVDataset,
                labels_path="/tmp/filepaths.csv",
                fields=["filepath"],
                abs_paths=True,
                delegate=True,
            )

            # Export a view
            view = dataset.take(100)
            export_samples(
                view,
                dataset_type=fo.types.FiftyOneDataset,
                export_dir="/tmp/quickstart-view",
                delegate=True,
            )

        Args:
            sample_collection: a
                :class:`fiftyone.core.collections.SampleCollection`
            export_dir (None): the directory to which to export the samples in
                format ``dataset_type``. This parameter may be omitted if you
                have provided appropriate values for the ``data_path`` and/or
                ``labels_path`` parameters. Alternatively, this can also be an
                archive path with one of the following extensions::

                    .zip, .tar, .tar.gz, .tgz, .tar.bz, .tbz

                If an archive path is specified, the export is performed in a
                directory of same name (minus extension) and then automatically
                archived and the directory then deleted
            dataset_type (None): the :class:`fiftyone.types.Dataset` type to
                write
            data_path (None): an optional parameter that enables explicit
                control over the location of the exported media for certain
                export formats. Can be any of the following:

                -   a folder name like ``"data"`` or ``"data/"`` specifying a
                    subfolder of ``export_dir`` in which to export the media
                -   an absolute directory path in which to export the media. In
                    this case, the ``export_dir`` has no effect on the location
                    of the data
                -   a filename like ``"data.json"`` specifying the filename of
                    a JSON manifest file in ``export_dir`` generated when
                    ``export_media`` is ``"manifest"``
                -   an absolute filepath specifying the location to write the
                    JSON manifest file when ``export_media`` is ``"manifest"``.
                    In this case, ``export_dir`` has no effect on the location
                    of the data

                If None, a default value of this parameter will be chosen based
                on the value of the ``export_media`` parameter. Note that this
                parameter is not applicable to certain export formats such as
                binary types like TF records
            labels_path (None): an optional parameter that enables explicit
                control over the location of the exported labels. Only
                applicable when exporting in certain labeled dataset formats.
                Can be any of the following:

                -   a type-specific folder name like ``"labels"`` or
                    ``"labels/"`` or a filename like ``"labels.json"`` or
                    ``"labels.xml"`` specifying the location in ``export_dir``
                    in which to export the labels
                -   an absolute directory or filepath in which to export the
                    labels. In this case, the ``export_dir`` has no effect on
                    the location of the labels

                For labeled datasets, the default value of this parameter will
                be chosen based on the export format so that the labels will be
                exported into ``export_dir``
            export_media (None): controls how to export the raw media. The
                supported values are:

                -   ``True``: copy all media files into the output directory
                -   ``False``: don't export media. This option is only useful
                    when exporting labeled datasets whose label format stores
                    sufficient information to locate the associated media
                -   ``"move"``: move all media files into the output directory
                -   ``"symlink"``: create symlinks to the media files in the
                    output directory
                -   ``"manifest"``: create a ``data.json`` in the output
                    directory that maps UUIDs used in the labels files to the
                    filepaths of the source media, rather than exporting the
                    actual media

                If None, an appropriate default value of this parameter will be
                chosen based on the value of the ``data_path`` parameter. Note
                that some dataset formats may not support certain values for
                this parameter (e.g., when exporting in binary formats such as
                TF records, "symlink" is not an option)
            label_field (None): controls the label field(s) to export. Only
                applicable to labeled datasets. Can be any of the following:

                -   the name of a label field to export
                -   a glob pattern of label field(s) to export
                -   a list or tuple of label field(s) to export

                Note that multiple fields can only be specified when the
                exporter used can handle dictionaries of labels. When exporting
                labeled video datasets, this argument may contain frame fields
                prefixed by ``"frames."``
            overwrite (False): whether to delete existing directories before
                performing the export (True) or to merge the export with
                existing files and directories (False)
            delegate (False): whether to delegate execution
            delegation_target (None): an optional orchestrator on which to
                schedule the operation, if it is delegated
            **kwargs: optional keyword arguments to pass to the dataset
                exporter's constructor. If you are exporting image patches,
                this can also contain keyword arguments for
                :class:`fiftyone.utils.patches.ImagePatchesExtractor`
        """
        if isinstance(sample_collection, fo.DatasetView):
            ctx = dict(view=sample_collection)
        else:
            ctx = dict(dataset=sample_collection)

        if delegation_target is not None:
            ctx["delegation_target"] = delegation_target

        dataset_type = _get_dataset_type_label(dataset_type)

        params = dict(
            dataset_type=dataset_type,
            export_type="MEDIA_AND_LABELS",  # unused
            csv_fields=["filepath"],  # unused
            export_media=export_media,
            overwrite=overwrite,
            delegate=delegate,
            manual=True,
            kwargs=kwargs,
        )

        if _can_export_multiple_fields(dataset_type):
            params["label_fields"] = _to_list(label_field)
        else:
            params["label_field"] = label_field

        if export_dir is not None:
            params["export_dir"] = _to_path(export_dir)

        if data_path is not None:
            params["data_path"] = _to_path(data_path)

        if labels_path is not None:
            params["labels_path"] = _to_path(labels_path)

        return foo.execute_operator(self.uri, ctx, params=params)

    def resolve_input(self, ctx):
        inputs = types.Object()

        ready = _export_samples_inputs(ctx, inputs)
        if ready:
            _execution_mode(ctx, inputs)

        return types.Property(inputs, view=types.View(label="Export samples"))

    def resolve_delegation(self, ctx):
        return ctx.params.get("delegate", False)

    def execute(self, ctx):
        _export_samples(ctx)


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

    dataset_type = None
    fields = None

    if export_type == "FILEPATHS_ONLY":
        export_type = "LABELS_ONLY"
        dataset_type = "CSV"
        fields = ["filepath"]
    elif export_type in ("LABELS_ONLY", "MEDIA_AND_LABELS"):
        dataset_types = _get_export_types(
            target_view, export_type, allow_coercion=True
        )
        inputs.enum(
            "dataset_type",
            dataset_types,
            required=True,
            label="Label format",
            description="The label format in which to export",
        )

        dataset_type = ctx.params.get("dataset_type", None)
        if dataset_type is None:
            return False

        docs_link = _get_docs_link(dataset_type, type="export")
        inputs.view(
            "docs", types.Notice(label=f"Exporter documentation: {docs_link}")
        )

        if dataset_type == "CSV":
            field_choices = types.Dropdown(multiple=True)
            for field in _get_csv_fields(target_view):
                field_choices.add_choice(field, label=field)

            inputs.list(
                "csv_fields",
                types.String(),
                required=True,
                label="Fields",
                description="Field(s) to include as columns of the CSV",
                view=field_choices,
            )

            fields = ctx.params.get("csv_fields", None)
            if not fields:
                return False
        elif _requires_label_field(dataset_type):
            multiple = _can_export_multiple_fields(dataset_type)
            label_field_choices = types.Dropdown(multiple=multiple)
            for field in _get_label_fields(
                target_view, dataset_type, allow_coercion=True
            ):
                label_field_choices.add_choice(field, label=field)

            if multiple:
                inputs.list(
                    "label_fields",
                    types.String(),
                    required=True,
                    label="Label fields",
                    description="The field(s) containing the labels to export",
                    view=label_field_choices,
                )

                fields = ctx.params.get("label_fields", None)
            else:
                inputs.enum(
                    "label_field",
                    label_field_choices.values(),
                    required=True,
                    label="Label field",
                    description="The field containing the labels to export",
                    view=label_field_choices,
                )

                fields = ctx.params.get("label_field", None)

            if fields is None:
                return False

    if _can_export_abs_paths(dataset_type):
        inputs.bool(
            "abs_paths",
            default=False,
            label="Absolute paths",
            description=(
                "Store absolute paths to the media in the exported labels?"
            ),
            view=types.CheckboxView(),
        )

    labels_path_type = _get_labels_path_type(dataset_type)

    if labels_path_type == "file":
        ext = _get_labels_path_ext(dataset_type)
        file_explorer = types.FileExplorerView(button_label="Choose a file...")
        prop = inputs.file(
            "labels_path",
            required=True,
            label="Labels path",
            description=f"Choose a {ext} path to write the labels",
            view=file_explorer,
        )

        labels_path = _parse_path(ctx, "labels_path")
        if labels_path is None:
            return False

        if os.path.splitext(labels_path)[1] != ext:
            prop.invalid = True
            prop.error_message = f"Please provide a {ext} path"
            return False

        if fos.isfile(labels_path):
            inputs.bool(
                "overwrite",
                default=True,
                label="File already exists. Overwrite it?",
                view=types.CheckboxView(),
            )
            overwrite = ctx.params.get("overwrite", True)

            if not overwrite:
                prop.invalid = True
                prop.error_message = "The specified file already exists"
                return False
    elif labels_path_type == "directory":
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        prop = inputs.file(
            "labels_path",
            required=True,
            label="Directory",
            description="Choose a directory at which to write the export",
            view=file_explorer,
        )

        labels_path = _parse_path(ctx, "labels_path")
        if labels_path is None:
            return False

        if fos.isdir(labels_path):
            inputs.bool(
                "overwrite",
                default=True,
                label="Directory already exists. Overwrite it?",
                view=types.CheckboxView(),
            )
            overwrite = ctx.params.get("overwrite", True)

            if not overwrite:
                prop.invalid = True
                prop.error_message = "The specified directory already exists"
                return False
    else:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        prop = inputs.file(
            "export_dir",
            required=True,
            label="Directory",
            description="Choose a directory at which to write the export",
            view=file_explorer,
        )

        export_dir = _parse_path(ctx, "export_dir")
        if export_dir is None:
            return False

        if fos.isdir(export_dir):
            inputs.bool(
                "overwrite",
                default=True,
                label="Directory already exists. Overwrite it?",
                view=types.CheckboxView(),
            )
            overwrite = ctx.params.get("overwrite", True)

            if not overwrite:
                prop.invalid = True
                prop.error_message = "The specified directory already exists"
                return False

    size_bytes = _estimate_export_size(target_view, export_type, fields)
    size_str = etau.to_human_bytes_str(size_bytes)
    label = f"Estimated export size: {size_str}"
    inputs.view("estimate", types.Notice(label=label))

    return True


def _export_samples(ctx):
    target = ctx.params.get("target", None)
    export_dir = _parse_path(ctx, "export_dir")
    labels_path = _parse_path(ctx, "labels_path")
    export_type = ctx.params["export_type"]
    export_media = ctx.params.get("export_media", None)
    dataset_type = ctx.params.get("dataset_type", None)
    label_field = ctx.params.get("label_field", None)
    label_fields = ctx.params.get("label_fields", None)
    csv_fields = ctx.params.get("csv_fields", None)
    abs_paths = ctx.params.get("abs_paths", None)
    manual = ctx.params.get("manual", False)
    kwargs = ctx.params.get("kwargs", {})

    if _can_export_multiple_fields(dataset_type):
        label_field = label_fields

    target_view = _get_target_view(ctx, target)

    if manual:
        dataset_type = _get_dataset_type(dataset_type)["dataset_type"]
    elif export_type == "FILEPATHS_ONLY":
        dataset_type = fot.CSVDataset
        csv_fields = ["filepath"]
        export_media = False
    elif export_type == "MEDIA_ONLY":
        if target_view.media_type == fom.IMAGE:
            dataset_type = fot.ImageDirectory
        elif target_view.media_type == fom.VIDEO:
            dataset_type = fot.VideoDirectory
        else:
            dataset_type = fot.MediaDirectory

        labels_path = None
        label_field = None
        export_media = True
    elif export_type == "LABELS_ONLY":
        dataset_type = _get_dataset_type(dataset_type)["dataset_type"]
        export_media = False
    else:
        dataset_type = _get_dataset_type(dataset_type)["dataset_type"]
        labels_path = None
        export_media = True

    if labels_path is not None:
        export_dir = None

    if dataset_type is fot.CSVDataset:
        if "fields" not in kwargs:
            kwargs["fields"] = csv_fields

        label_field = None

    if dataset_type is fot.GeoJSONDataset:
        if "location_field" not in kwargs:
            kwargs["location_field"] = label_field

        label_field = None

    if abs_paths is not None:
        if "abs_paths" not in kwargs:
            kwargs["abs_paths"] = abs_paths

    target_view.export(
        export_dir=export_dir,
        dataset_type=dataset_type,
        labels_path=labels_path,
        label_field=label_field,
        export_media=export_media,
        **kwargs,
    )


def _estimate_export_size(view, export_type, fields):
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

    # Estimate labels size
    if export_type != "MEDIA_ONLY":
        if fields:
            view = view.select_fields(fields)

        stats = view.stats()
        size_bytes += stats["samples_bytes"]

    return size_bytes


def _get_csv_fields(view):
    for path, field in view.get_field_schema().items():
        if isinstance(field, fo.EmbeddedDocumentField):
            for _path, _field in field.get_field_schema().items():
                if _is_valid_csv_field(_field):
                    yield path + "." + _path
        elif _is_valid_csv_field(field):
            yield path


def _is_valid_csv_field(field):
    if isinstance(field, fo.ListField):
        field = field.field

    return isinstance(field, fof._PRIMITIVE_FIELDS)


def _get_fields_with_type(view, type):
    if issubclass(type, fo.Field):
        return view.get_field_schema(ftype=type).keys()

    return view.get_field_schema(embedded_doc_type=type).keys()


def _get_export_types(view, export_type, allow_coercion=False):
    label_types = set(
        view.get_field(field).document_type
        for field in _get_fields_with_type(view, fo.Label)
    )

    label_types = set(
        k for k, v in _LABEL_TYPES_MAP.items() if v in label_types
    )

    # Label type coercion
    if allow_coercion:
        # Single label -> list coercion
        for label_type in _LABEL_LIST_TYPES:
            if label_type[:-1] in label_types:
                label_types.add(label_type)

        # Object patches -> image classifications
        if view.media_type == fom.IMAGE and (
            {"detections", "polylines", "keypoints"} & set(label_types)
        ):
            label_types.add("classification")

        # Video clips -> video classifications
        if view.media_type == fom.VIDEO and (
            {"temporal detections"} & set(label_types)
        ):
            label_types.add("classification")

    labels_only = export_type == "LABELS_ONLY"

    dataset_types = []
    for d in _DATASET_TYPES:
        if not d["export"]:
            continue

        if d["media_types"] and view.media_type not in d["media_types"]:
            continue

        if labels_only and not d["export_labels_only"]:
            continue

        _label_types = d.get("label_types", None)
        if _label_types is None or set(label_types) & set(_label_types):
            dataset_types.append(d["label"])

    return sorted(dataset_types)


def _can_export_multiple_fields(dataset_type):
    d = _get_dataset_type(dataset_type)
    return d.get("export_multiple_fields", False)


def _can_export_abs_paths(dataset_type):
    d = _get_dataset_type(dataset_type)
    return d.get("export_abs_paths", False)


def _get_label_fields(view, dataset_type, allow_coercion=False):
    d = _get_dataset_type(dataset_type)
    label_types = d.get("label_types", None)

    if not label_types:
        return []

    label_types = set(label_types)

    # Label type coercion
    if allow_coercion:
        # Object patches -> image classification
        if view.media_type == fom.IMAGE and "classification" in label_types:
            label_types.update({"detections", "polylines", "keypoints"})

        # Video clips -> video classification
        if view.media_type == fom.VIDEO and "classification" in label_types:
            label_types.add("temporal detections")

        # Single label -> list coercion
        for label_type in _LABEL_LIST_TYPES:
            if label_type in label_types:
                label_types.add(label_type[:-1])

    label_fields = set()
    for label_type, label_cls in _LABEL_TYPES_MAP.items():
        if label_type in label_types:
            label_fields.update(_get_fields_with_type(view, label_cls))

    return sorted(label_fields)


_LABEL_LIST_TYPES = (
    "classifications",
    "detections",
    "polylines",
    "keypoints",
    "temporal detections",
)

_LABEL_TYPES_MAP = {
    "classification": fo.Classification,
    "classifications": fo.Classifications,
    "detection": fo.Detection,
    "detections": fo.Detections,
    "instance": fo.Detection,
    "instances": fo.Detections,
    "polyline": fo.Polyline,
    "polylines": fo.Polylines,
    "keypoint": fo.Keypoint,
    "keypoints": fo.Keypoints,
    "temporal detection": fo.TemporalDetection,
    "temporal detections": fo.TemporalDetections,
    "segmentation": fo.Segmentation,
    "heatmap": fo.Heatmap,
    "geolocation": fo.GeoLocation,
}

_DATASET_TYPES = [
    {
        "label": "Image Classification Directory Tree",
        "dataset_type": fot.ImageClassificationDirectoryTree,
        "media_types": [fom.IMAGE],
        "label_types": ["classification"],
        "import": True,
        "export": True,
        "export_labels_only": False,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#imageclassificationdirectorytree",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#imageclassificationdirectorytree",
    },
    {
        "label": "Video Classification Directory Tree",
        "dataset_type": fot.VideoClassificationDirectoryTree,
        "media_types": [fom.VIDEO],
        "label_types": ["classification"],
        "import": True,
        "export": True,
        "export_labels_only": False,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#videoclassificationdirectorytree",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#videoclassificationdirectorytree",
    },
    {
        "label": "TF Image Classification",
        "dataset_type": fot.TFImageClassificationDataset,
        "media_types": [fom.IMAGE],
        "label_types": ["classification"],
        "import": True,
        "export": True,
        "export_labels_only": False,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#tfimageclassificationdataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#tfimageclassificationdataset",
    },
    {
        "label": "COCO",
        "dataset_type": fot.COCODetectionDataset,
        "media_types": [fom.IMAGE],
        "label_types": ["detections", "segmentations", "keypoints"],
        "labels_path_type": "file",
        "labels_path_ext": ".json",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": True,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#cocodetectiondataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#cocodetectiondataset",
    },
    {
        "label": "VOC",
        "dataset_type": fot.VOCDetectionDataset,
        "media_types": [fom.IMAGE],
        "label_types": ["detections"],
        "labels_path_type": "directory",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#vocdetectiondataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#vocdetectiondataset",
    },
    {
        "label": "KITTI",
        "dataset_type": fot.KITTIDetectionDataset,
        "media_types": [fom.IMAGE],
        "label_types": ["detections"],
        "labels_path_type": "directory",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#kittidetectiondataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#kittidetectiondataset",
    },
    {
        "label": "YOLOv4",
        "dataset_type": fot.YOLOv4Dataset,
        "media_types": [fom.IMAGE],
        "label_types": ["detections"],
        "labels_path_type": "directory",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#yolov4dataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#yolov4dataset",
    },
    {
        "label": "YOLOv5",
        "dataset_type": fot.YOLOv5Dataset,
        "media_types": [fom.IMAGE],
        "label_types": ["detections"],
        "import": True,
        "export": True,
        "export_labels_only": False,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#yolov5dataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#yolov5dataset",
    },
    {
        "label": "TF Object Detection",
        "dataset_type": fot.TFObjectDetectionDataset,
        "media_types": [fom.IMAGE],
        "label_types": ["detections"],
        "import": True,
        "export": True,
        "export_labels_only": False,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#tfobjectdetectiondataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#tfobjectdetectiondataset",
    },
    {
        "label": "CVAT Image",
        "dataset_type": fot.CVATImageDataset,
        "media_types": [fom.IMAGE],
        "label_types": [
            "classifications",
            "detections",
            "polylines",
            "keypoints",
        ],
        "labels_path_type": "file",
        "labels_path_ext": ".xml",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": True,
        "export_abs_paths": True,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#cvatimagedataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#cvatimagedataset",
    },
    {
        "label": "CVAT Video",
        "dataset_type": fot.CVATVideoDataset,
        "media_types": [fom.VIDEO],
        "label_types": None,  # @todo frame_label_types
        "labels_path_type": "directory",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": True,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#cvatvideodataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#cvatvideodataset",
    },
    {
        "label": "OpenLABEL Image",
        "dataset_type": fot.OpenLABELImageDataset,
        "media_types": [fom.IMAGE],
        "label_types": None,  # all
        "labels_path_type": "directory",
        "import": True,
        "export": False,  # no export
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#openlabelimagedataset",
    },
    {
        "label": "OpenLABEL Video",
        "dataset_type": fot.OpenLABELVideoDataset,
        "media_types": [fom.VIDEO],
        "label_types": None,  # all
        "labels_path_type": "directory",
        "import": True,
        "export": False,  # no export
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#openlabelvideodataset",
    },
    {
        "label": "Image Segmentation",
        "dataset_type": fot.ImageSegmentationDirectory,
        "media_types": [fom.IMAGE],
        "label_types": ["segmentation"],
        "labels_path_type": "directory",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#imagesegmentationdirectory",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#imagesegmentationdirectory",
    },
    {
        "label": "CSV",
        "dataset_type": fot.CSVDataset,
        "media_types": [fom.IMAGE],
        "label_types": None,  # all
        "labels_path_type": "file",
        "labels_path_ext": ".csv",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": True,
        "export_abs_paths": True,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#csvdataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#csvdataset",
    },
    {
        "label": "DICOM",
        "dataset_type": fot.DICOMDataset,
        "media_types": [fom.IMAGE],
        "label_types": None,  # all
        "import": True,
        "export": False,  # no export
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#dicomdataset",
    },
    {
        "label": "GeoJSON",
        "dataset_type": fot.GeoJSONDataset,
        "media_types": fom.MEDIA_TYPES,
        "label_types": ["geolocation"],
        "labels_path_type": "file",
        "labels_path_ext": ".json",
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": True,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#geojsondataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#geojsondataset",
    },
    {
        "label": "GeoTIFF",
        "dataset_type": fot.GeoTIFFDataset,
        "media_types": [fom.IMAGE],
        "label_types": ["geolocation"],
        "import": True,
        "export": False,  # no export
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#geotiffdataset",
    },
    {
        "label": "FiftyOne Dataset",
        "dataset_type": fot.FiftyOneDataset,
        "media_types": None,  # all
        "label_types": None,  # all
        "import": True,
        "export": True,
        "export_labels_only": True,
        "export_multiple_fields": False,
        "export_abs_paths": False,
        "import_docs": "https://docs.voxel51.com/user_guide/dataset_creation/datasets.html#fiftyonedataset",
        "export_docs": "https://docs.voxel51.com/user_guide/export_datasets.html#fiftyonedataset",
    },
]


class DrawLabels(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="draw_labels",
            label="Draw labels",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
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
        output_dir = _parse_path(ctx, "output_dir")
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


def _to_path(value):
    return {"absolute_path": value}


def _to_list(value):
    if value is None:
        return None

    if isinstance(value, str):
        return [value]

    return list(value)


def _get_target_view(ctx, target):
    if target == "SELECTED_LABELS":
        return ctx.view.select_labels(labels=ctx.selected_labels)

    if target == "SELECTED_SAMPLES":
        return ctx.view.select(ctx.selected)

    if target == "DATASET":
        return ctx.dataset

    return ctx.view


def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", False)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=False,
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
    p.register(ImportSamples)
    p.register(MergeSamples)
    p.register(MergeLabels)
    p.register(ExportSamples)
    p.register(DrawLabels)
