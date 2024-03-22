# Contributing to fiftyone-plugins

Thanks for your interest in contributing to `fiftyone-plugins`!

## Pre-commit hooks

If you plan to contribute a PR, please check install the pre-commit hooks
before committing:

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

### Prerequisites

-   Follow
    [these instructions](https://github.com/voxel51/fiftyone/tree/develop?tab=readme-ov-file#installing-from-source)
    to install Fiftyone from source
-   Checkout
    [contribution guide](https://github.com/voxel51/fiftyone/blob/develop/CONTRIBUTING.md)
    for Fiftyone project
-   Set the `FIFTYONE_DIR` environment variable to the location where you
    cloned the `fiftyone` repository

### Install dependencies to create and build a plugin

-   Run `yarn install`

### Create a new plugin

-   Run `yarn create-plugin <your-plugin-name>` to create a new plugin

### Source install

-   Run `bash install.bash` to install the dev dependencies

### Build JavaScript assets (Panel, Operators, etc.) for a plugin [Optional]

-   Run `yarn workspace <plugin-name> dev` to compile/watch a plugin

### Build JavaScript assets outside of fiftyone-plugins repository [Optional]

To build a plugin with JavaScript assets (i.e. Panel, Operators, etc.) outside
of this repository, some additional configuration is required. Take a look at
[voxelgpt](https://github.com/voxel51/voxelgpt/blob/main/vite.config.js) plugin
repository for an example of configurations required for JavaScript build
externally. Mainly, your `vite.config.js` will need to be similar to
`vite.config.js` of
[voxelgpt](https://github.com/voxel51/voxelgpt/blob/main/vite.config.js)
plugin. Additionally, you will need to install the dependencies listed in
`vite.config.js` (i.e. `vite`, `@vitejs/plugin-react`,
`@rollup/plugin-node-resolve`, `vite-plugin-externals`, etc.) as a
dev-dependencies for your JavaScript plugin project.
