In this tutorial I will be walking you through how to build your first Fiftyone plugin.
As a user, Fiftyone plugins unlock workflows unique to your exact pipeline. From
model validation, to custom visualizers and plots, plugins allow developers to customize
Fiftyone to fit your user's requirements.

For this example, we'll be creating a model validation plugin. This will allow us to
visualize the accurace of our model as well as how different types of samples are
performing.

First lets setup the quickstart dataset in our local python session.

```py
import fiftyone as fo
import fiftyone.zoo as foz

# download and load the dataset
quickstart = foz.load_zoo_dataset('quickstart')

# load up the dataset in the app
session = fo.launch_app(quickstart)
```

### Setting up your plugin dev environment

In order to setup your development environment you will need the following installed locally:

 - fiftyone source install
 - node.js v18.10.x or later
 - yarn

Create a directory to store all of your plugins. We'll refer to this directory by the
fiftyone environment variable `FIFTYONE_PLUGINS_DIR`.

```
# setup your plugin directory
git clone git@github.com:voxel51/fiftyone-plugins.git
cd fiftyone-plugins
export FIFTYONE_PLUGINS_DIR=$(pwd)
yarn init
```

You can create as many plugins in this directory. Let's create our confusion-matrix plugin:
Let's use the "hello-world" plugin as a starting point.

```
cp -r hello-world my-confusion-matrix-plugin
```

NOTE: Make sure to update the `package.json` `name` and `main` as well as the `src` filenames to match your plugin name.

Add symlinks to the fiftyone source modules:

```
cd my-confusion-matrix-plugin
mksir -p node_modules/@fiftyone
cd node_modules/@fiftyone
MY_FIFTYONE_SRC_DIR=... # set this to the directory that includes fiftyone or fiftyone-teams
ln -s $MY_FIFTYONE_SRC_DIR/app/packages/plugins
ln -s $MY_FIFTYONE_SRC_DIR/app/packages/state
ln -s $MY_FIFTYONE_SRC_DIR/app/packages/aggregations
cd ../../
yarn install
```

Add the dependencies for this plugin:

```
yarn add 

Now you should be able to build your plugin:

```
yarn build
```

Follow the directions in Fiftyone to run the application.

### Rendering a confusion matric


