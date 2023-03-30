# fiftyone-plugins

This repo serves as a registry for all **external** fiftyone plugins developed by Voxel51. If you are looking for Fiftyone core (built-in) plugins you can find them [here](https://github.com/voxel51/fiftyone/tree/develop/app).

## Installing a plugin

Each plugin is available in the public npm registry. You can install them by following the typical install instructions.

## Contributing

There are a few ways to use this repository.

1. Clone and run the plugins. Eg. the debugger plugin is useful for troubleshooting Fiftyone issues.
2. As a starter sekelton for building your own plugin.
3. As a contributor to a Voxel51 external plugin. Note: contributions can be made to core plugins [here](https://github.com/voxel51/fiftyone/tree/develop/app).

**Prerequisites**

- You must have fiftyone setup for sdk and app development. Follow [these](https://github.com/voxel51/fiftyone/blob/develop/CONTRIBUTING.md) instructions to get setup.
- Set the `FIFTYONE_DIR` env var to the location where you cloned the fiftyone repo.

**Install**

1. clone the repository and `cd fiftyone-plugins`
1. run `bash install.bash` to install the dev dependencies.

**Develop**

1. run `yarn workspace $PLUGIN_NAME dev` to compile/watch the given plugin
1. follow [these](https://github.com/voxel51/fiftyone/blob/develop/CONTRIBUTING.md) instructions to run Fiftyone from source.

**Create your own Plugin**

1. After running all the steps above, you should be ready to create your own plugin.
2. You can re-use this directory / repo, or re-clone a new copy.
3. Run `yarn create-plugin <Your-Plugin-Name>` to create a new plugin. Then to install dependencies re-run `bash install.bash`.
