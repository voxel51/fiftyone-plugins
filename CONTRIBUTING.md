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

A convenient way to do that is to symlink your `fiftyone-plugins` directory
into your FiftyOne plugins directory:

```shell
git clone https://github.com/voxel51/fiftyone-plugins
ln -s "$(pwd)/fiftyone-plugins" "$(fiftyone config plugins_dir)/voxelgpt"
```
