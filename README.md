# fiftyone-plugins

This repo serves as a registry for all **external** fiftyone plugins developed by Voxel51. If you are looking for Fiftyone core (built-in) plugins you can find them [here](https://github.com/voxel51/fiftyone/tree/develop/app).

<!-- start-table-of-contents -->
<table>
    <tr>
        <th colspan="6">
            FiftyOne Plugins
        </th>
    </tr>
    <tr>
        <td><code>1.0.0</code></td>
        <td><b><a href="https://github.com/voxel51/fiftyone-gpt">@voxel51/fiftyone-gpt</a></b></td>
        <td>Wish you could search your images or videos without writing a line of code? Now you can!</td>
        <td><a href="https://github.com/voxel51/fiftyone-gpt">About</a></td>
        <td><a href="https://github.com/voxel51/fiftyone-gpt#installation">Install</a></td>
        <td>
        </td>
    </tr>
    <tr>
        <td><code>1.0.0</code></td>
        <td><b><a href="https://github.com/voxel51/fiftyone-docs-search">@voxel51/fiftyone-docs-search</a></b></td>
        <td>Enable semantic search on the Voxel51 documentation from the FiftyOne app</td>
        <td><a href="https://github.com/voxel51/fiftyone-docs-search">About</a></td>
        <td><a href="https://github.com/voxel51/fiftyone-docs-search#installation">Install</a></td>
        <td>
        </td>
    </tr>
    <tr>
        <td><code>1.0.0</code></td>
        <td><b><a href="packages/hello-world/README.md">@voxel51/hello-world</a></b></td>
        <td>An example of JavaScript and Python components and operators in a single plugin</td>
        <td><a href="packages/hello-world/README.md#about">About</a></td>
        <td><a href="packages/hello-world/README.md#installation">Install</a></td>
        <td>
            <a href="packages/hello-world/README.md#operators">Operators</a>
        </td>
    </tr>
    <tr>
        <td><code>1.0.0</code></td>
        <td><b><a href="packages/examples/README.md">@voxel51/examples</a></b></td>
        <td>Examples of how to use the operator type system to build custom FiftyOne operations</td>
        <td><a href="packages/examples/README.md#about">About</a></td>
        <td><a href="packages/examples/README.md#installation">Install</a></td>
        <td>
            <a href="packages/examples/README.md#operators">Operators</a>
        </td>
    </tr>
    <tr>
        <td><code>1.0.0</code></td>
        <td><b><a href="packages/python_view/README.md">@voxel51/python_view</a></b></td>
        <td>Create views in the FiftyOne App with Python</td>
        <td><a href="packages/python_view/README.md#about">About</a></td>
        <td><a href="packages/python_view/README.md#installation">Install</a></td>
        <td>
            <a href="packages/python_view/README.md#operators">Operators</a>
        </td>
    </tr>
</table>
<!-- end-table-of-contents -->

## Contributing

There are a few ways to use this repository.

1. Clone and run the plugins.
2. As a starter sekelton for building your own plugin.
3. As a contributor to a Voxel51 external plugin. Note: contributions can be made to core plugins [here](https://github.com/voxel51/fiftyone/tree/develop/app).

**Prerequisites**

- You must have fiftyone setup for sdk and app development. Follow [these](https://github.com/voxel51/fiftyone/blob/develop/CONTRIBUTING.md) instructions to get setup.
- Set the `FIFTYONE_DIR` env var to the location where you cloned the fiftyone repo.

**Source Install**

1. clone the repository and `cd fiftyone-plugins`
1. run `bash install.bash` to install the dev dependencies.

**Develop**

1. run `yarn workspace $PLUGIN_NAME dev` to compile/watch the given plugin
1. follow [these](https://github.com/voxel51/fiftyone/blob/develop/CONTRIBUTING.md) instructions to run Fiftyone from source.

**Create your own Plugin**

1. After running all the steps above, you should be ready to create your own plugin.
2. You can re-use this directory / repo, or re-clone a new copy.
3. Run `yarn create-plugin <Your-Plugin-Name>` to create a new plugin. Then to install dependencies re-run `bash install.bash`.
