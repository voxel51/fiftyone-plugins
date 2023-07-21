import fiftyone.operators as foo
import fiftyone.operators.types as types
from time import sleep
from scipy import linalg
import json
import numpy as np

from bson import json_util

def get_index(dataset):
    for br in dataset.list_brain_runs():
        bri = dataset.get_brain_info(br).config
        if "Similarity" in bri.cls and bri.supports_prompts:
            return dataset.load_brain_results(br)
    return None


def generate_text_vector(
        index,
        left_prompt,
        right_prompt,
        alpha
):
    model = index.get_model()
    left_embedding = model.embed_prompts([left_prompt])
    right_embedding = model.embed_prompts([right_prompt])
    interp_embedding = (1 - alpha) * left_embedding + alpha * right_embedding
    return interp_embedding/linalg.norm(interp_embedding)


def run_interpolation(ctx):
    dataset = ctx.dataset
    index = get_index(dataset)

    left_prompt = ctx.params.get("left_extreme", "None provided")
    right_prompt = ctx.params.get("right_extreme", "None provided")
    alpha = ctx.params.get("slider_value", 0.5)

    # left_prompt = "cat"
    # right_prompt = "cat"
    # alpha = 1.

    text_vector = generate_text_vector(
        index,
        left_prompt,
        right_prompt,
        alpha
    )
    view = dataset.sort_by_similarity(
        text_vector, 
        brain_key = index.key, 
        k = 25
        )
    
    # view = dataset.sort_by_similarity(
    #     "cat", 
    #     brain_key = index.key, 
    #     k = 10
    #     )
    # view = dataset.select(view.values('id'))
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
            name="interpolation_panel", 
            isActive=True, 
            layout="vertical"
            ),
        )


class RunInterpolation(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="interpolator", label="Interpolate")
    
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("left_extreme", label="Left Prompt", required=True)
        inputs.str("right_extreme", label="Right Prompt", required=True)

        left_extreme = ctx.params.get("left_extreme", "Left")
        right_extreme = ctx.params.get("right_extreme", "Right")
        marks = [
            {
                'value': 0,
                'label': left_extreme,
            },
            {
                'value': 1,
                'label': right_extreme,
            },
        ]

        interpolation_slider = types.SliderView(
            label="Interpolation",
            componentsProps={"slider": {
                "min": 0, 
                "max": 1, 
                "step": 0.05,
                "marks": marks
                }}
            )
        inputs.float(
            "slider_value",
            default = 0.5,
            view=interpolation_slider
            )
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
