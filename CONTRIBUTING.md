# Contributing to fiftyone-plugins

Thanks for your interest in contributing to `fiftyone-plugins`!

## Pre-commit hooks

If you plan to contribute a PR, please check install the pre-commit hooks
before commiting:

```shell
pre-commit install
```

You can manually lint a file if necessary like so:

```shell
# Manually run linting configured in the pre-commit hook
pre-commit run --files <file>
```

## Local development

When developing locally, you must make your source install of this repository
available to FiftyOne.

A convenient way to do that is to symlink this repository into your FiftyOne
plugins directory:

```shell
cd /path/to/fiftyone-plugins
ln -s "$(pwd)" "$(fiftyone config plugins_dir)/voxelgpt"
```

## Legacy instructions (possibly outdated)

### Prerequisites

-   Follow
    [these instructions](https://github.com/voxel51/fiftyone/blob/develop/CONTRIBUTING.md)
    to install Fiftyone from source
-   Set the `FIFTYONE_DIR` environment variable to the location where you
    cloned the `fiftyone` repository

### Create a new plugin

-   Run `yarn create-plugin <your-plugin-name>` to create a new plugin

### Source install

-   Run `bash install.bash` to install the dev dependencies

### Develop

-   Run `yarn workspace <plugin-name> dev` to compile/watch a plugin
