"""CommonIssues plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import numpy as np
from PIL import Image, ImageStat


import fiftyone.operators as foo
from fiftyone.operators import types
import fiftyone as fo
from fiftyone import ViewField as F


def get_filepath(sample):
    return (
        sample.local_path if hasattr(sample, "local_path") else sample.filepath
    )


def compute_sample_brightness(sample):
    image = Image.open(get_filepath(sample))
    stat = ImageStat.Stat(image)
    try:
        r, g, b = stat.mean
    except:
        r, g, b = (
            stat.mean[0],
            stat.mean[0],
            stat.mean[0],
        )

    ## equation from here:
    ## https://www.nbdtech.com/Blog/archive/2008/04/27/calculating-the-perceived-brightness-of-a-color.aspx
    brightness = (
        np.sqrt(0.241 * r**2 + 0.691 * g**2 + 0.068 * b**2) / 255
    )
    return brightness


def compute_dataset_brightness(dataset):
    dataset.add_sample_field("brightness", fo.FloatField)
    for sample in dataset.iter_samples(autosave=True):
        brightness = compute_sample_brightness(sample)
        sample["brightness"] = brightness


class ComputeBrightness(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_brightness",
            label="Common Issues: compute brightness",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message("compute brightness", label="compute brightness")
        return types.Property(inputs)

    def execute(self, ctx):
        compute_dataset_brightness(ctx.dataset)
        ctx.trigger("reload_dataset")


def compute_sample_aspect_ratio(sample):
    width, height = sample.metadata.width, sample.metadata.height
    size_score = min(width / height, height / width)
    return size_score


def compute_dataset_aspect_ratio(dataset):
    dataset.compute_metadata()
    dataset.add_sample_field("aspect_ratio", fo.FloatField)
    for sample in dataset.iter_samples(autosave=True):
        aspect_ratio = compute_sample_aspect_ratio(sample)
        sample["aspect_ratio"] = aspect_ratio


class ComputeAspectRatio(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_aspect_ratio",
            label="Common Issues: compute aspect ratio",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message("compute aspect ratio", label="compute aspect ratio")
        return types.Property(inputs)

    def execute(self, ctx):
        compute_dataset_aspect_ratio(ctx.dataset)
        ctx.trigger("reload_dataset")


def compute_sample_entropy(sample):
    image = Image.open(get_filepath(sample))
    return image.entropy()


def compute_dataset_entropy(dataset):
    dataset.add_sample_field("entropy", fo.FloatField)
    for sample in dataset.iter_samples(autosave=True):
        entropy = compute_sample_entropy(sample)
        sample["entropy"] = entropy


class ComputeEntropy(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="compute_entropy",
            label="Common Issues: compute entropy",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.message("compute entropy", label="compute entropy")
        return types.Property(inputs)

    def execute(self, ctx):
        compute_dataset_entropy(ctx.dataset)
        ctx.trigger("reload_dataset")


def _need_to_compute(dataset, field_name):
    if field_name in list(dataset.get_field_schema().keys()):
        return False
    else:
        return field_name not in dataset.first()


def _run_computation(dataset, field_name):
    if field_name == "brightness":
        compute_dataset_brightness(dataset)
    elif field_name == "aspect_ratio":
        compute_dataset_aspect_ratio(dataset)
    elif field_name == "entropy":
        compute_dataset_entropy(dataset)
    else:
        raise ValueError("Unknown field name %s" % field_name)


def find_issue_images(
    dataset,
    threshold,
    field_name,
    issue_name,
    lt=True,
):
    dataset.add_sample_field(issue_name, fo.BooleanField)
    if _need_to_compute(dataset, field_name):
        _run_computation(dataset, field_name)

    if lt:
        view = dataset.set_field(issue_name, F(field_name) < threshold)
    else:
        view = dataset.set_field(issue_name, F(field_name) > threshold)
    view.save()
    view = dataset.match(F(issue_name))
    view.tag_samples(issue_name)
    view.tag_samples("issue")
    view.save()


def find_dark_images(dataset, threshold=0.1):
    find_issue_images(dataset, threshold, "brightness", "dark", lt=True)


def find_bright_images(dataset, threshold=0.55):
    find_issue_images(dataset, threshold, "brightness", "bright", lt=False)


def find_weird_aspect_ratio_images(dataset, threshold=0.5):
    find_issue_images(
        dataset, threshold, "aspect_ratio", "weird_aspect_ratio", lt=True
    )


def find_low_entropy_images(dataset, threshold=5.0):
    find_issue_images(dataset, threshold, "entropy", "low_entropy", lt=True)


class FindIssues(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="find_issues",
            label="Common Issues: find issues",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        form_view = types.View(label="Find Common Issues")
        if ctx.dataset.media_type != "image":
            warning = types.Warning(
                label="This operator is only available for image datasets!"
            )
            inputs.view("warning", warning)
            return types.Property(inputs)

        threshold_view = types.TextFieldView(
            componentsProps={
                "textField": {
                    "step": "0.01",
                    "inputMode": "numeric",
                    "pattern": "[0-9]*",
                },
            }
        )

        #### DARK IMAGES ####
        inputs.bool(
            "dark",
            default=True,
            label="Find dark images in the dataset",
            view=types.CheckboxView(),
        )

        if ctx.params.get("dark", False) == True:
            inputs.float(
                "dark_threshold",
                default=0.1,
                label="darkness threshold",
                view=threshold_view,
            )

        #### BRIGHT IMAGES ####
        inputs.bool(
            "bright",
            default=True,
            label="Find bright images in the dataset",
            view=types.CheckboxView(),
        )

        if ctx.params.get("bright", False) == True:
            inputs.float(
                "bright_threshold",
                default=0.55,
                label="brightness threshold",
                view=threshold_view,
            )

        #### WEIRD ASPECT RATIO IMAGES ####
        inputs.bool(
            "weird_aspect_ratio",
            default=True,
            label="Find weird aspect ratio images in the dataset",
            view=types.CheckboxView(),
        )

        if ctx.params.get("weird_aspect_ratio", False) == True:
            inputs.float(
                "weird_aspect_ratio_threshold",
                default=0.5,
                label="weird aspect ratio threshold",
                view=threshold_view,
            )

        #### LOW ENTROPY IMAGES ####
        inputs.bool(
            "low_entropy",
            default=True,
            label="Find low entropy images in the dataset",
            view=types.CheckboxView(),
        )

        if ctx.params.get("low_entropy", False) == True:
            inputs.float(
                "low_entropy_threshold",
                default=5.0,
                label="low entropy threshold",
                view=threshold_view,
            )

        return types.Property(inputs, view=form_view)

    def execute(self, ctx):
        if ctx.params.get("dark", False) == True:
            dark_threshold = ctx.params.get("dark_threshold", 0.1)
            find_dark_images(ctx.dataset, dark_threshold)
        if ctx.params.get("bright", False) == True:
            bright_threshold = ctx.params.get("bright_threshold", 0.55)
            find_bright_images(ctx.dataset, bright_threshold)
        if ctx.params.get("weird_aspect_ratio", False) == True:
            weird_aspect_ratio_threshold = ctx.params.get(
                "weird_aspect_ratio_threshold", 2.5
            )
            find_weird_aspect_ratio_images(
                ctx.dataset, weird_aspect_ratio_threshold
            )
        if ctx.params.get("low_entropy", False) == True:
            low_entropy_threshold = ctx.params.get(
                "low_entropy_threshold", 5.0
            )
            find_low_entropy_images(ctx.dataset, low_entropy_threshold)
        ctx.trigger("reload_dataset")


def register(plugin):
    plugin.register(ComputeBrightness)
    plugin.register(ComputeAspectRatio)
    plugin.register(ComputeEntropy)
    plugin.register(FindIssues)
