"""Interpolation plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

from bson import json_util
import json
from scipy import linalg


import fiftyone.operators as foo
import fiftyone.operators.types as types


def get_valid_indexes(dataset):
    valid_indexes = []
    for br in dataset.list_brain_runs():
        bri = dataset.get_brain_info(br).config
        if (
            ("Similarity" in bri.cls)
            and bri.supports_prompts
            and bri.metric == "cosine"
        ):
            valid_indexes.append(br)
    return valid_indexes


def generate_text_vector(index, left_prompt, right_prompt, alpha):
    model = index.get_model()
    left_embedding = model.embed_prompts([left_prompt])
    right_embedding = model.embed_prompts([right_prompt])
    interp_embedding = (1 - alpha) * left_embedding + alpha * right_embedding
    return interp_embedding / linalg.norm(interp_embedding)


def run_interpolation(ctx):
    dataset = ctx.dataset
    index_name = ctx.params.get("index", "None provided")
    index = dataset.load_brain_results(index_name)
    left_prompt = ctx.params.get("left_extreme", "None provided")
    right_prompt = ctx.params.get("right_extreme", "None provided")
    alpha = ctx.params.get("slider_value", 0.5)

    text_vector = generate_text_vector(index, left_prompt, right_prompt, alpha)
    view = dataset.sort_by_similarity(text_vector, brain_key=index.key, k=25)

    return view


def serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))


class OpenInterpolationPanel(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="open_interpolation_panel",
            label="Open Interpolation Panel",
            unlisted=True,
        )

    def resolve_placement(self, ctx):
        return types.Placement(
            types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
            types.Button(
                label="Open Interpolation Panel",
                icon="/assets/interpolate.svg",
                prompt=False,
            ),
        )

    def execute(self, ctx):
        ctx.trigger(
            "open_panel",
            params=dict(
                name="InterpolationPanel", isActive=True, layout="vertical"
            ),
        )


class RunInterpolation(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="interpolator",
            label="Interpolate",
            unlisted=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        inputs.str("index", label="Brain Key", required=True)
        inputs.str("left_extreme", label="Left Prompt", required=True)
        inputs.str("right_extreme", label="Right Prompt", required=True)

        left_extreme = ctx.params.get("left_extreme", "Left")
        right_extreme = ctx.params.get("right_extreme", "Right")
        marks = [
            {
                "value": 0,
                "label": left_extreme,
            },
            {
                "value": 1,
                "label": right_extreme,
            },
        ]

        interpolation_slider = types.SliderView(
            label="Interpolation",
            componentsProps={
                "slider": {"min": 0, "max": 1, "step": 0.05, "marks": marks}
            },
        )
        inputs.float("slider_value", default=0.5, view=interpolation_slider)
        return types.Property(inputs)

    def execute(self, ctx):
        view = run_interpolation(ctx)
        ctx.trigger(
            "set_view",
            params=dict(view=serialize_view(view)),
        )


def register(p):
    p.register(RunInterpolation)
    p.register(OpenInterpolationPanel)
