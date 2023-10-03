"""
Plugin management operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import functools

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

import itertools
import multiprocessing
from packaging.requirements import Requirement
from packaging.version import Version
import traceback

import fiftyone as fo
import fiftyone.constants as foc
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.plugins as fop

from .utils import find_plugins, get_zoo_plugins, get_plugin_info


class InstallPlugin(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="install_plugin",
            label="Install plugin",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        _install_plugin_inputs(ctx, inputs)
        return types.Property(inputs, view=types.View(label="Install plugin"))

    def execute(self, ctx):
        _install_plugin(ctx)


def _install_plugin_inputs(ctx, inputs):
    tab_choices = types.TabsView()
    tab_choices.add_choice("GITHUB", label="GitHub")
    tab_choices.add_choice("VOXEL51", label="Voxel51")
    tab_choices.add_choice("COMMUNITY", label="Community")
    inputs.enum(
        "tab",
        tab_choices.values(),
        default="GITHUB",
        view=tab_choices,
    )
    tab = ctx.params.get("tab", "GITHUB")

    plugin_names = None

    if tab == "GITHUB":
        instructions = """
Provide a location to download the plugin(s) from, which can be:

-   A GitHub repo URL like `https://github.com/<user>/<repo>`
-   A GitHub ref like
    `https://github.com/<user>/<repo>/tree/<branch>` or
    `https://github.com/<user>/<repo>/commit/<commit>`
-   A GitHub ref string like `<user>/<repo>[/<ref>]`
    """

        inputs.str(
            "gh_repo_instructions",
            default=instructions.strip(),
            view=types.MarkdownView(read_only=True),
        )

        inputs.str("gh_repo", required=True)

        gh_repo = ctx.params.get("gh_repo", None)
        if not gh_repo:
            return

        try:
            plugins = find_plugins(gh_repo)
        except:
            prop = inputs.view(
                "error",
                types.Error(
                    label=f"Failed to find plugins at {gh_repo}",
                    description=traceback.format_exc(),
                ),
            )
            prop.invalid = True
            return

        if not plugins:
            prop = inputs.view(
                "warning",
                types.Warning(label=f"No plugins found at {gh_repo}"),
            )
            prop.invalid = True
            return

        if len(plugins) > 1:
            plugin_choices = types.Dropdown(multiple=True)
            for plugin in plugins:
                plugin_choices.add_choice(
                    plugin["name"],
                    label=plugin["name"],
                    description=plugin["description"],
                )

            inputs.list(
                "plugin_names",
                types.String(),
                default=None,
                label="Plugins",
                description=(
                    "An optional list of plugins to install. By default, "
                    "all plugins are installed"
                ),
                view=plugin_choices,
            )

        plugin_names = ctx.params.get("plugin_names", None)
        if not plugin_names:
            plugin_names = [plugin["name"] for plugin in plugins]
    else:
        try:
            voxel51_plugins, community_plugins = get_zoo_plugins()
        except:
            prop = inputs.view(
                "error",
                types.Error(
                    label="Failed to retrieve zoo plugins",
                    description=traceback.format_exc(),
                ),
            )
            prop.invalid = True
            return

        if tab == "VOXEL51":
            param = "voxel51_plugin"
            plugins = voxel51_plugins
            description = (
                "Choose a Voxel51-authored plugin from the zoo to install"
            )
        else:
            param = "community_plugin"
            plugins = community_plugins
            description = (
                "Choose a community-authored plugin from the zoo to install"
            )

        plugin_choices = types.Dropdown()
        for plugin in plugins:
            plugin_choices.add_choice(
                plugin["name"],
                label=plugin["name"],
                description=plugin["description"],
            )

        inputs.str(
            param,
            required=True,
            label="Plugin",
            description=description,
            view=plugin_choices,
        )

        plugin_name = ctx.params.get(param, None)
        if plugin_name:
            plugin_names = [plugin_name]

    if plugin_names is None:
        return

    updates = _get_updates(plugin_names, plugins)

    if updates:
        # @todo why is a unique prop name required for Markdown to re-render?
        prop_name = tab + "_" + "_".join(plugin_names) + "_update_str"
        update_str = (
            "You are about to update the following plugins:\n"
            + "\n".join(
                [
                    f"- `{name}`: `v{curr_ver}` -> `v{ver}`"
                    for (name, curr_ver, ver) in updates
                ]
            )
        )
        inputs.str(
            prop_name,
            default=update_str,
            view=types.MarkdownView(read_only=True),
        )

        update_notice = "Are you sure you want to update these plugins?"
        inputs.view("update_notice", types.Notice(label=update_notice))


def _get_updates(plugin_names, plugins):
    curr_plugins_map = {p.name: p for p in fop.list_plugins(enabled="all")}
    update_names = sorted(set(plugin_names) & set(curr_plugins_map.keys()))

    if not update_names:
        return []

    plugins_map = {p["name"]: p for p in plugins if p["name"] in update_names}
    _hydrate_plugin_info(plugins_map)

    updates = []
    for name in update_names:
        curr_plugin = curr_plugins_map[name]
        plugin = plugins_map[name]
        updates.append((name, curr_plugin.version, plugin["version"]))

    return updates


def _hydrate_plugin_info(plugins_map):
    tasks = {}
    for name, plugin in plugins_map.items():
        if "version" not in plugin:
            tasks[name] = plugin["url"]

    num_tasks = len(tasks)

    if num_tasks == 0:
        return

    if num_tasks == 1:
        name, url = next(iter(tasks.items()))
        info = get_plugin_info(url)
        plugins_map[name] = info

    processes = min(num_tasks, 4)
    tasks = list(tasks.items())
    with multiprocessing.dummy.Pool(processes=processes) as pool:
        for name, info in pool.imap_unordered(_do_get_plugin_info, tasks):
            plugins_map[name] = info


def _do_get_plugin_info(task):
    name, url = task
    info = get_plugin_info(url)
    return name, info


def _install_plugin(ctx):
    tab = ctx.params.get("tab", None)

    if tab == "GITHUB":
        gh_repo = ctx.params["gh_repo"]
        plugin_names = ctx.params.get("plugin_names", None)
    elif tab == "VOXEL51":
        plugin_name = ctx.params["voxel51_plugin"]
        gh_repo = _get_zoo_plugin_location(plugin_name)
        plugin_names = [plugin_name]
    elif tab == "COMMUNITY":
        plugin_name = ctx.params["community_plugin"]
        gh_repo = _get_zoo_plugin_location(plugin_name)
        plugin_names = [plugin_name]

    fop.download_plugin(gh_repo, plugin_names=plugin_names, overwrite=True)


def _get_zoo_plugin_location(plugin_name):
    for plugin in itertools.chain(*get_zoo_plugins()):
        if plugin["name"] == plugin_name:
            return plugin["url"]


class ManagePlugins(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_plugins",
            label="Manage plugins",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        _manage_plugins_inputs(ctx, inputs)
        return types.Property(inputs, view=types.View(label="Manage plugins"))

    def execute(self, ctx):
        tab = ctx.params.get("tab", None)
        if tab == "ENABLEMENT":
            _plugin_enablement(ctx)


def _manage_plugins_inputs(ctx, inputs):
    tab_choices = types.TabsView()
    tab_choices.add_choice("ENABLEMENT", label="Enablement")
    tab_choices.add_choice("REQUIREMENTS", label="Requirements")
    default = "ENABLEMENT"

    inputs.enum(
        "tab",
        tab_choices.values(),
        default=default,
        view=tab_choices,
    )
    tab = ctx.params.get("tab", default)

    if tab == "ENABLEMENT":
        _plugin_enablement_inputs(ctx, inputs)
    elif tab == "REQUIREMENTS":
        _plugin_requirements_inputs(ctx, inputs)


def _plugin_enablement_inputs(ctx, inputs):
    obj = types.Object()
    obj.str(
        "name",
        default="**Name**",
        view=types.MarkdownView(read_only=True, space=3),
    )
    obj.str(
        "description",
        default="**Description**",
        view=types.MarkdownView(read_only=True, space=7),
    )
    obj.str(
        "enabled",
        default="**Enabled**",
        view=types.MarkdownView(read_only=True, space=2),
    )
    inputs.define_property("enablement_header", obj)

    enabled_plugins = set(fop.list_enabled_plugins())

    num_edited = 0
    for i, plugin in enumerate(fop.list_plugins(enabled="all"), 1):
        prop_name = f"enablement{i}"
        actual_enabled = plugin.name in enabled_plugins
        enabled = ctx.params.get(prop_name, {}).get("enabled", actual_enabled)
        edited = enabled != actual_enabled
        num_edited += int(edited)

        obj = types.Object()
        obj.str(
            "markdown_name",
            default=f"[{plugin.name}]({plugin.url})",
            view=types.MarkdownView(read_only=True, space=3),
        )
        obj.str(
            "description",
            default=plugin.description,
            view=types.MarkdownView(read_only=True, space=6.5),
        )
        obj.str(
            "name",
            default=plugin.name,
            view=types.HiddenView(read_only=True, space=0.5),
        )
        obj.bool(
            "enabled",
            label="(edited)" if edited else "",
            default=actual_enabled,
            view=types.CheckboxView(space=2),  # @todo use SwitchView
        )
        inputs.define_property(prop_name, obj)

    if num_edited > 0:
        view = types.Notice(
            label=(
                f"You are about to change the enablement of {num_edited} "
                "plugins"
            )
        )
    else:
        view = types.Notice(label="You have not made any changes")

    status_prop = inputs.view("enablement_status", view)

    if num_edited == 0:
        status_prop.invalid = True


def _plugin_enablement(ctx):
    enabled_plugins = set(fop.list_enabled_plugins())

    i = 0
    while True:
        i += 1
        prop_name = f"enablement{i}"
        obj = ctx.params.get(prop_name, None)
        if obj is None:
            break

        name = obj["name"]
        enabled = obj["enabled"]

        actual_enabled = name in enabled_plugins
        if enabled != actual_enabled:
            if enabled:
                fop.enable_plugin(name)
            else:
                fop.disable_plugin(name)


def _plugin_requirements_inputs(ctx, inputs):
    plugin_names = [p.name for p in fop.list_plugins(enabled="all")]
    plugin_choices = types.DropdownView()
    for name in sorted(plugin_names):
        plugin_choices.add_choice(name, label=name)

    inputs.str(
        "requirements_name",
        default=None,
        required=True,
        label="Plugin",
        description="Choose a plugin whose requirements you want to check",
        view=plugin_choices,
    )

    name = ctx.params.get("requirements_name", None)
    if name is None:
        return

    requirements = []

    plugin = fop.get_plugin(name)
    req_str = plugin.fiftyone_requirement
    if req_str is not None:
        requirements.append(_check_fiftyone_requirement(req_str))

    req_strs = fop.load_plugin_requirements(name)
    if req_strs is not None:
        for req_str in req_strs:
            requirements.append(_check_package_requirement(req_str))

    num_requirements = len(requirements)
    if num_requirements == 0:
        inputs.view(
            "requirements_status",
            types.Notice(label="This plugin has no package requirements"),
        )
        return

    obj = types.Object()
    obj.str(
        "requirements_requirement",
        default="**Requirement**",
        view=types.MarkdownView(read_only=True, space=5),
    )
    obj.str(
        "requirements_version",
        default="**Installed version**",
        view=types.MarkdownView(read_only=True, space=5),
    )
    obj.str(
        "requirements_satisfied",
        default="**Satisfied**",
        view=types.MarkdownView(read_only=True, space=2),
    )
    inputs.define_property("requirements_header", obj)

    num_satisfied = 0
    for i, (req_str, version, satisfied) in enumerate(requirements, 1):
        prop_name = f"requirements{i}"
        num_satisfied += int(satisfied)

        obj = types.Object()
        obj.str(
            "requirement",
            default=req_str,
            view=types.MarkdownView(read_only=True, space=5),
        )
        obj.str(
            "version",
            default=version or "",
            view=types.MarkdownView(read_only=True, space=5),
        )
        obj.bool(
            "satisfied",
            default=satisfied,
            view=types.CheckboxView(read_only=True, space=2),
        )
        inputs.define_property(prop_name, obj)

    if num_satisfied == num_requirements:
        view = types.Notice(label="All package requirements are satisfied")
    else:
        view = types.Warning(
            label=(
                f"Only {num_satisfied}/{num_requirements} package "
                "requirements are satisfied"
            )
        )

    status_prop = inputs.view("requirements_status", view)
    status_prop.invalid = True


def _check_fiftyone_requirement(req_str):
    version = foc.VERSION

    try:
        req = Requirement(req_str)
        satisfied = not req.specifier or req.specifier.contains(version)
    except:
        satisfied = False

    return req_str, version, satisfied


def _check_package_requirement(req_str):
    try:
        req = Requirement(req_str)
    except:
        pass

    try:
        version = metadata.version(req.name)
    except:
        version = None

    try:
        satisfied = (version is not None) and (
            not req.specifier or req.specifier.contains(version)
        )
    except:
        satisfied = False

    return req_str, version, satisfied


def register(p):
    p.register(InstallPlugin)
    p.register(ManagePlugins)
