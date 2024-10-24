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

## Tests

This project contains multiple plugins, each with its own set of tests. To
simplify the testing process, we've included a script called `run_all_tests.sh`
that automatically finds and runs tests in all plugin directories.

### About the `run_tests.sh` Script

The `run_tests.sh` script:

-   Iterates through all subdirectories under the `./plugins` directory.
-   Checks each plugin for a non-empty `tests` directory.
-   Runs `pytest` in each `tests` directory found.
-   Reports test results and indicates whether all tests passed or if any
    failures occurred.
-   Adds the `./plugins` directory to the `PYTHONPATH`.

### How to run the tests

To run tests for all plugins, simply execute the script using the following
command:

```bash
# ensure pytest is installed
pip install pytest

# run all the tests
bash run_tests.sh

# or run an individual plugins tests
bash run_tests.sh hello_world
```

### Using pytest directly

You can also use pytest directly by emulating the setup in `run_tests.sh`.

- Ensure you have `$FIFTYONE_PLUGINS_DIR/plugins` in your `PYTHONPATH`
- Run a test file and use `pytest` as expected
- eg `pytest ./plugins/hello_world/test_count_samples.py -v`
