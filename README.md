# FiftyOne Plugins 🧩

This repository contains multiple collections of
[FiftyOne Plugins](https://docs.voxel51.com/plugins/index.html), organized into
the following categories:

1. [Core Plugins](#core-plugins): These are "built-in" plugins housing core
   functionality. They are maintained by the FiftyOne team.
2. [1st Party Plugins](#1st-party-plugins): These are plugins that are
   maintained by the FiftyOne team, but are not core functionality.
3. [Example Plugins](#example-plugins): These are example plugins that are here
   to inspire you to create your own plugins! Each emphasizes a different
   aspect of the plugin system.
4. [3rd Party Plugins](#3rd-party-plugins): These are plugins that are
   maintained by the community. They are not officially supported by the
   FiftyOne team.

> 🔌 ➕ 🤝 **Contribute Your Own Plugin 🚀🚀:** Want to showcase your own
> plugin here? See the [contributing](#contributing) section below for
> instructions!

## Core Plugins

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Version</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/blob/main/plugins/io/README.md">@voxel51/io</a></b></td>
        <td>A collection of import/export utilities</td>
        <td><code>1.0.0</code></td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/blob/main/plugins/python-view/README.md">@voxel51/python-view</a></b></td>
        <td>Create views in the FiftyOne App with Python</td>
        <td><code>1.0.0</code></td>
    </tr>
</table>

## 1st Party Plugins

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Version</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/voxelgpt">@voxel51/voxelgpt</a></b></td>
        <td>An AI assistant that can query visual datasets, search the FiftyOne docs, and answer general computer vision questions</td>
        <td><code>1.0.0</code></td>
    </tr>
</table>

## Example Plugins

<table>
    <tr>
        <th>Name</th>
        <th>Description</th>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/blob/main/plugins/hello-world">Hello world</a></b></td>
        <td>👋 An example of JavaScript and Python components and operators in a single plugin</td>
    </tr>
    <tr>
        <td><b><a href="https://github.com/voxel51/fiftyone-plugins/blob/main/plugins/examples/">Python Examples</a></b></td>
        <td>📋 Examples of how to use the operator type system to build custom FiftyOne operations</td>
    </tr>
    
</table>

## 3rd Party Plugins

> 🔌 ➕ 🤝 **Contribute Your Own Plugin 🚀🚀:** Want to showcase your own
> plugin here? See the [contributing](#contributing) section below for
> instructions!

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
</table>

## Usage

There are a few ways to use this repository:

1.  **User:** download and use the plugins! Click on the links in the table
    above for more details about using each one
2.  **Reference:** use these plugins as inspiration/starter skeletons for
    building your own plugins
3.  **Contributor:** dive in and [contribute](CONTRIBUTING.md) to a new or
    existing plugin in this repository!

## Installation

### Install FiftyOne

If you haven't already, install
[FiftyOne](https://github.com/voxel51/fiftyone):

```shell
pip install fiftyone
```

### Installing a plugin

To install one of the plugins listed above, click on the link for that plugin
and navigate to the `Installation` section of the project's README.

In general, you can install all of the plugins in a GitHub repository by
running:

```shell
fiftyone plugins download https://github.com/path/to/repo
```

For instance, to install all of the plugins in this repository, you can run:

```shell
fiftyone plugins download https://github.com/voxel51/fiftyone-plugins
```

To install a specific plugin in a repository, you can use the `--plugin-names`
flag:

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names <name>
```

### Plugin management

You can use the CLI commands below to manage your downloaded plugins:

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

## 🤝 Contributing

### Contributing a new plugin

Have a plugin you'd like to share with the community? Awesome! 🎉🎉🎉

To contribute a new plugin, please follow these steps:

1. Make sure your plugin repo has a `README.md` file that describes the plugin,
   with an `Installation` section that describes how to install the plugin.
2. Fork this repository
3. Add an entry for your plugin to the [3rd Party Plugins](#3rd-party-plugins)
   table above
4. Submit a pull request!

### Contributing to this repository

Check out the [contributions guide](CONTRIBUTING.md) for instructions.

## About FiftyOne

If you've made it this far, we'd greatly appreciate if you'd take a moment to
check out [FiftyOne](https://github.com/voxel51/fiftyone) and give us a star!

FiftyOne is an open source library for building high-quality datasets and
computer vision models. It's the engine that powers this project.

Thanks for visiting! 😊

## Join the Community

If you want join a fast-growing community of engineers, researchers, and
practitioners who love computer vision, join the
[FiftyOne Slack community](https://slack.voxel51.com/)! 🚀🚀🚀

> 💡 **Pro Tip:** The `#plugins` channel is a great place to discuss plugins!
