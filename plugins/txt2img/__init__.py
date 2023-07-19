"""Text2Image plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import os
import uuid

import fiftyone.operators as foo
from fiftyone.operators import types
import fiftyone as fo

import requests
import openai
import replicate

SD_MODEL_URL = "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478"
SD_SCHEDULER_CHOICES = ("DDIM", "K_EULER", "DPMSolverMultiStep", "K_EULER_ANCESTRAL", "PNDM", "KLMS")
SD_SIZE_CHOICES = ("64", "128", "192", "256", "320", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024")

VQGAN_MODEL_URL = "mehdidc/feed_forward_vqgan_clip:28b5242dadb5503688e17738aaee48f5f7f5c0b6e56493d7cf55f74d02f144d8"

DALLE2_SIZE_CHOICES = ("256x256", "512x512", "1024x1024")


def download_image(image_url, filename):
    img_data = requests.get(image_url).content
    with open(filename, 'wb') as handler:
        handler.write(img_data)


class Text2Image():
    """Wrapper for a Text2Image model."""
    def __init__(self):
        self.name = None
        self.model_name = None

    def generate_image(self, ctx):
        pass


class StableDiffusion(Text2Image):
    """Wrapper for a StableDiffusion model."""
    def __init__(self):
        super().__init__()
        self.name = "stable-diffusion"
        self.model_name =SD_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        width = int(ctx.params.get("width_choices", "None provided"))
        height = int(ctx.params.get("height_choices", "None provided"))
        inference_steps = ctx.params.get("inference_steps", "None provided")
        scheduler = ctx.params.get("scheduler_choices", "None provided")

        response = replicate.run(self.model_name, input={"prompt": prompt, "width": width, "height": height, "inference_steps": inference_steps, "scheduler": scheduler})
        if type(response) == list:
            response = response[0]
        return response


class DALLE2(Text2Image):
    """Wrapper for a DALL-E 2 model."""
    def __init__(self):
        super().__init__()
        self.name = "dalle-2"

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        size = ctx.params.get("size_choices", "None provided")

        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=size
        )
        return response['data'][0]['url']

class VQGANCLIP(Text2Image):
    """Wrapper for a VQGAN-CLIP model."""
    def __init__(self):
        super().__init__()
        self.name = "vqgan-clip"
        self.model_name = VQGAN_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        response = replicate.run(self.model_name, input={"prompt": prompt})
        if type(response) == list:
            response = response[0]
        return response


def get_model(model_name):
    if model_name == "sd":
        return StableDiffusion()
    if model_name == "dalle2":
        return DALLE2()
    if model_name == "vqgan-clip":
        return VQGANCLIP()
    
    raise ValueError(f"Model {model_name} not found.")





def generate_filepath(dataset):
    path = dataset.first().filepath
    base_dir = "/".join(path.split("/")[:-1])
    filename = str(uuid.uuid4())[:13].replace("-", "") + ".png"
    return os.path.join(base_dir, filename)


class Txt2Image(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="model_choices",
            label="Txt2Img: Generate Images from Text",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        radio_choices = types.RadioGroup()
        radio_choices.add_choice("sd", label="Stable Diffusion")
        radio_choices.add_choice("dalle2", label="DALL-E2")
        radio_choices.add_choice("vqgan-clip", label="VQGAN-CLIP")
        inputs.enum(
            "model_choices",
            radio_choices.values(),
            default=radio_choices.choices[0].value,
            label="Models",
            view=radio_choices,
        )


        if ctx.params.get("model_choices", False) == "sd":
            size_choices = SD_SIZE_CHOICES
            width_choices = types.Dropdown(label="Width")
            for size in size_choices:
                width_choices.add_choice(size, label=size)

            inputs.enum(
                "width_choices",
                width_choices.values(),
                default="512",
                view=width_choices,
            )

            height_choices = types.Dropdown(label="Height")
            for size in size_choices:
                height_choices.add_choice(size, label=size)

            inputs.enum(
                "height_choices",
                height_choices.values(),
                default="512",
                view=height_choices,
            )

            inference_steps_slider = types.SliderView(label="Num Inference Steps")
            inputs.int(
                "inference_steps",
                default = 50,
                view=inference_steps_slider)

            scheduler_choices_dropdown = types.Dropdown(label="Scheduler")
            for scheduler in SD_SCHEDULER_CHOICES:
                scheduler_choices_dropdown.add_choice(scheduler, label=scheduler)

            inputs.enum(
                "scheduler_choices",
                scheduler_choices_dropdown.values(),
                default="K_EULER",
                view=scheduler_choices_dropdown,
            )

        elif ctx.params.get("model_choices", False) == "dalle2":

            size_choices_dropdown = types.Dropdown(label="Size")
            for size in DALLE2_SIZE_CHOICES:
                size_choices_dropdown.add_choice(size, label=size)

            inputs.enum(
                "size_choices",
                size_choices_dropdown.values(),
                default="512x512",
                view=size_choices_dropdown,
            )


        inputs.str("prompt", label="Prompt", required=True)
        return types.Property(inputs)

    def execute(self, ctx):
        model_name = ctx.params.get("model_choices", "None provided")
        model = get_model(model_name)
        prompt = ctx.params.get("prompt", "None provided")
        image_url = model.generate_image(ctx)

        filename = generate_filepath(ctx.dataset)
        download_image(image_url, filename)

        sample = fo.Sample(
            filepath=filename,
            tags=["generated"],
            model = model.name,
            prompt = prompt,
        )
        ctx.dataset.add_sample(sample)

        return {
            "model_choice": ctx.params.get("model_choices", "None provided"),
            "prompt": ctx.params.get("prompt", "None provided"),
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("model_choice", label="Model Choice")
        return types.Property(outputs)


def register(plugin):
    plugin.register(Txt2Image)
