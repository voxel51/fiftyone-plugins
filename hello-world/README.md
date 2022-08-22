# hello-world
Example Fiftyone Plugin

## Install

**Note: You must have fiftyone installed from source.**

In this directory run the following:

```sh
npm install
```

Then link the required packages:

```sh
cd $MY_FIFTYONE_SRC_DIR/app/packages;
cd aggregations;
npm link;
cd ../plugins;
npm link;
cd ../state;
npm link;
cd $HELLO_WORLD_DIR;
npm link @fiftyone/aggregations;
npm link @fiftyone/plugins;
npm link @fiftyone/state;
```

You also must set the `FIFTYONE_PLUGINS_DIR` env var to
tell `fiftyone` to load this plugin.

Note: once the plugin system is fully released, these steps will likely change.