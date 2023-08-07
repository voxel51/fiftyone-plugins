## Text2Image Plugin

This plugin is a Python plugin that allows you to generate images from text
prompts and add them directly into your dataset.

It demonstrates how to do the following:

-   use Python to create an operator with different options depending on user
    choices
-   use `componentProps` to customize the UI
-   download images from URL and add them to the dataset

:warning: This plugin is only verified to work for local datasets. It may not
work for remote datasets.

### Supported Models

This version of the plugin supports the following models:

-   DALL-E2
-   Stable Diffusion
-   VQGAN-CLIP

It is straightforward to add support for other models!

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/txt2img
```

If you want to use Replicate models (Stable Diffusion and VQGAN-CLIP), you will
need to `pip install replicate` and set the environment variable
`REPLICATE_API_TOKEN` with your API token.

If you want to use DALL-E2, you will need to `pip install openai` and set the
environment variable `OPENAI_API_KEY` with your API key.

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Operators

### `txt2img`

-   Generates an image from a text prompt and adds it to the dataset
