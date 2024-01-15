# FiftyOne Plugins 🔌🚀

FiftyOne provides a powerful
[plugin framework](https://docs.voxel51.com/plugins/index.html) that allows for
extending and customizing the functionality of the tool.

With plugins, you can add new functionality to the FiftyOne App, create
integrations with other tools and APIs, render custom panels, and add custom
buttons to menus. You can even schedule long running tasks from within the App
that execute on a connected workflow orchestration tool like Apache Airflow.

For example, here's a taste of what you can do with the
[@voxel51/brain](https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/brain)
plugin!

https://github.com/voxel51/fiftyone-plugins/assets/25985824/128d9fbd-9835-49e8-bbb9-93ea5093871f

## Table of Contents

This repository contains a curated collection of
[FiftyOne Plugins](https://docs.voxel51.com/plugins/index.html), organized into
the following categories:

-   [Core Plugins](#core-plugins): core functionality that all FiftyOne users
    will likely want to install. These plugins are maintained by the FiftyOne
    team
-   [Voxel51 Plugins](#voxel51-plugins): non-core plugins that are officially
    maintained by the FiftyOne team
-   [Example Plugins](#example-plugins): these plugins exist to inspire and
    educate you to create your own plugins! Each emphasizes a different aspect
    of the plugin system
-   [Community Plugins](#community-plugins): third-party plugins that are
    contributed and maintained by the community. These plugins are not
    officially supported by the FiftyOne team, but they're likely awesome!

🔌🤝 **Contribute Your Own Plugin** 🚀🚀

Want to showcase your own plugin here? See the
[contributing section](#contributing) for instructions!

## Core Plugins

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/annotation">@voxel51/annotation</a></b></td>
        <td>✏️ Utilities for integrating FiftyOne with annotation tools</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/brain">@voxel51/brain</a></b></td>
        <td>🧠 Utilities for working with the FiftyOne Brain</td>
    </tr>
    </tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/evaluation">@voxel51/evaluation</a></b></td>
        <td>✅ Utilities for evaluating models with FiftyOne</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/io">@voxel51/io</a></b></td>
        <td>📁 A collection of import/export utilities</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/indexes">@voxel51/indexes</a></b></td>
        <td>📈 Utilities working with FiftyOne database indexes</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/plugins">@voxel51/plugins</a></b></td>
        <td>🧩 Utilities for managing and building FiftyOne plugins</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/delegated">@voxel51/delegated</a></b></td>
        <td>📡 Utilities for managing your delegated operations</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/utils">@voxel51/utils</a></b></td>
        <td>⚒️ Call your favorite SDK utilities from the App</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/zoo">@voxel51/zoo</a></b></td>
        <td>🌎 Download datasets and run inference with models from the FiftyOne Zoo, all without leaving the App</td>
    </tr>
</table>

## Voxel51 Plugins

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/voxelgpt">@voxel51/voxelgpt</a></b></td>
        <td>🤖 An AI assistant that can query visual datasets, search the FiftyOne docs, and answer general computer vision questions</td>
    </tr>
</table>

## Example Plugins

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/hello-world">@voxel51/hello-world</a></b></td>
        <td>👋 An example of JavaScript and Python components and operators in a single plugin</td>
    </tr>
        <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/python-view">@voxel51/python-view</a></b></td>
        <td>🔎 Create views in the FiftyOne App with Python</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/examples">@voxel51/examples</a></b></td>
        <td>📋 Examples of how to use the operator type system to build custom FiftyOne operations</td>
    </tr>
</table>

## Community Plugins

🔌🤝 **Contribute Your Own Plugin** 🚀🚀

Want to showcase your own plugin here? See the
[contributing section](#contributing) for instructions!

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/image-quality-issues">@jacobmarks/image_issues</a></b></td>
        <td>🌩️ Find common image quality issues in your datasets</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/concept-interpolation">@jacobmarks/concept_interpolation</a></b></td>
        <td>📈 Find images that best interpolate between two text-based extremes!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/text-to-image">@jacobmarks/text_to_image</a></b></td>
        <td>🎨 Add synthetic data from prompts with text-to-image models and FiftyOne!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/twilio-automation-plugin">@jacobmarks/twilio_automation</a></b></td>
        <td>📲  Automate data ingestion with Twilio!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/wayofsamu/line2d">@wayofsamu/line2d</a></b></td>
        <td>📉 Visualize x,y-Points as a line chart.</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/vqa-plugin">@jacobmarks/vqa-plugin</a></b></td>
        <td>❔ Ask (and answer) open-ended visual questions about your images!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/fiftyone-youtube-panel-plugin">@jacobmarks/youtube_panel_plugin</a></b></td>
        <td>📺 Play YouTube videos in the FiftyOne App!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/image-deduplication-plugin">@jacobmarks/image_deduplication</a></b></td>
        <td>🪞 Find exact and approximate duplicates in your dataset!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/keyword-search-plugin">@jacobmarks/keyword_search</a></b></td>
        <td>🔑 Perform keyword search on a specified field!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/pytesseract-ocr-plugin">@jacobmarks/pytesseract_ocr</a></b></td>
        <td>👓 Run optical character recognition with PyTesseract!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/brimoor/pdf-loader">@brimoor/pdf-loader</a></b></td>
        <td>📄 Load your PDF documents into FiftyOne as per-page images</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/zero-shot-prediction-plugin">@jacobmarks/zero_shot_prediction</a></b></td>
        <td>🔮 Run zero-shot (open vocabulary) prediction on your data!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/active-learning-plugin">@jacobmarks/active_learning</a></b></td>
        <td>🏃 Accelerate your data labeling with Active Learning!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/reverse-image-search-plugin">@jacobmarks/reverse_image_search</a></b></td>
        <td>⏪ Find the images in your dataset most similar to an image from filesystem or the internet!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/concept-space-traversal-plugin">@jacobmarks/concept_space_traversal</a></b></td>
        <td>🌌 Navigate concept space with CLIP, vector search, and FiftyOne!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/audio-retrieval-plugin">@jacobmarks/audio_retrieval</a></b></td>
        <td>🔊 Find the images in your dataset most similar to an audio file!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/semantic-document-search-plugin">@jacobmarks/semantic_document_search</a></b></td>
        <td>🔎 Perform semantic search on text in your documents!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/allenleetc/model-comparison">@allenleetc/model-comparison</a></b></td>
        <td> ⚖️ Compare two object detection models!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/ehofesmann/filter-values-plugin">@ehofesmann/filter_values</a></b></td>
        <td>🔎 Filter a field of your FiftyOne dataset by one or more values.</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/gpt4-vision-plugin">@jacobmarks/gpt4_vision</a></b></td>
        <td>🤖 Chat with your images using GPT-4 Vision!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/swheaton/fiftyone-media-anonymization-plugin">@swheaton/anonymize</a></b></td>
        <td>🥸 Anonymize/blur images based on a FiftyOne Detections field.</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/double-band-filter-plugin">@jacobmarks/double_band_filter</a></b></td>
        <td><img src="https://raw.githubusercontent.com/jacobmarks/double-band-filter-plugin/main/assets/icon_grey.svg" width="14" height="14" alt="filter icon"> Filter on two numeric ranges simultaneously!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/danielgural/semantic_video_search">@danielgural/semantic_video_search</a></b></td>
        <td><img src="https://github.com/danielgural/semantic_video_search/blob/main/assets/search.svg" width="14" height="14" alt="filter icon"> Semantically search through your video datasets using FiftyOne Brain and Twelve Labs!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/jacobmarks/emoji-search-plugin">@jacobmarks/emoji_search</a></b></td>
        <td>😏 Semantically search emojis and copy to clipboard!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/danielgural/img_to_video_plugin">@danielgural/img_to_video</a></b></td>
        <td>🦋 Bring images to life with image to video!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/ehofesmann/edit_label_attributes">@ehofesmann/edit_label_attributes</a></b></td>
        <td>✏️ Edit attributes of your labels directly in the FiftyOne App!</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/danielgural/audio_loader">@danielgural/audio_loader</a></b></td>
        <td>🎧 Import your audio datasets as spectograms into FiftyOne!</td>
    </tr>
</table>

## Using Plugins

### Install FiftyOne

If you haven't already, install
[FiftyOne](https://github.com/voxel51/fiftyone):

```shell
pip install fiftyone
```

### Installing a plugin

In general, you can install all plugin(s) in a GitHub repository by running:

```shell
fiftyone plugins download https://github.com/path/to/repo
```

For instance, to install all plugins in this repository, you can run:

```shell
fiftyone plugins download https://github.com/voxel51/fiftyone-plugins
```

You can also install a specific plugin using the `--plugin-names` flag:

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names <name>
```

**💡 Pro tip:** Some plugins require additional setup. Click the plugin's link
and navigate to the project's README for instructions.

### Plugin management

You can use the
[CLI commands](https://docs.voxel51.com/cli/index.html#fiftyone-plugins) below
to manage your downloaded plugins:

```shell
# List all plugins you've downloaded
fiftyone plugins list

# List the available operators
fiftyone operators list

# Disable a particular plugin
fiftyone plugins disable <name>

# Enable a particular plugin
fiftyone plugins enable <name>
```

### Local development

If you plan to develop plugins locally, you can clone the repository and
symlink it into your FiftyOne plugins directory like so:

```shell
cd /path/to/fiftyone-plugins
ln -s "$(pwd)" "$(fiftyone config plugins_dir)/fiftyone-plugins"
```

## Contributing

### Showcasing your plugin 🤝

Have a plugin you'd like to share with the community? Awesome! 🎉🎉🎉

Just follow these steps to add your plugin to this repository:

1.  Make sure your plugin repo has a `README.md` file that describes the plugin
    and how to install it
2.  Fork this repository
3.  Add an entry for your plugin to the [Community Plugins](#community-plugins)
    table above
4.  Submit a pull request into this repository

### Contributing to this repository 🙌

You're also welcome to contribute to the plugins that live natively in this
repository. Check out the [contributions guide](CONTRIBUTING.md) for
instructions.

## Join the Community

If you want join a fast-growing community of engineers, researchers, and
practitioners who love computer vision, join the
[FiftyOne Slack community](https://slack.voxel51.com/) 🚀🚀🚀

**💡 Pro tip:** the `#plugins` channel is a great place to discuss plugins!

## About FiftyOne

If you've made it this far, we'd greatly appreciate if you'd take a moment to
check out [FiftyOne](https://github.com/voxel51/fiftyone) and give us a star!

FiftyOne is an open source library for building high-quality datasets and
computer vision models. It's the engine that powers this project.

Thanks for visiting! 😊
