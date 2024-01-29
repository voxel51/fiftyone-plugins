"""
Plugin management operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

import itertools
import multiprocessing
from packaging.requirements import Requirement
from packaging.version import Version
from textwrap import dedent
import traceback

import fiftyone as fo
import fiftyone.core.storage as fos
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

        plugin_choices = types.AutocompleteView()
        for plugin in plugins:
            plugin_choices.add_choice(
                plugin["name"],
                label=plugin["name"],
                description=plugin["description"],
            )

        inputs.enum(
            param,
            plugin_choices.values(),
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
            view=types.SwitchView(space=2),
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
    plugin_choices = types.Dropdown()
    for name in sorted(plugin_names):
        plugin_choices.add_choice(name, label=name)

    inputs.enum(
        "requirements_name",
        plugin_choices.values(),
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
        # @todo why is a unique prop name required for Markdown to re-render?
        prop_name = f"{name}_requirements{i}"
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


class BuildPluginComponent(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="build_plugin_component",
            label="Build plugin component",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _create_view_type_input(inputs)
        view_type = ctx.params.get("view_type", None)

        if view_type is not None:
            view_options = VIEW_TYPE_TO_OPTIONS[view_type]
            _create_options_input(inputs, view_options, view_type)
            _create_view_code(ctx, inputs, view_type)

        view = types.View(label="Build plugin component")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        pass


BOOLEAN_VIEW_OPTIONS = {
    "Checkbox": ("types.CheckboxView", types.CheckboxView),
    "Switch": ("types.SwitchView", types.SwitchView),
}

FLOAT_VIEW_OPTIONS = {
    "Slider": ("types.SliderView", types.SliderView),
    "Field": ("types.FieldView", types.FieldView),
}

MESSAGE_VIEW_OPTIONS = {
    "Message": None,
    "Success": None,
    "Warning": None,
    "Error": None,
    "Header": None,
}

RADIO_GROUP_VIEW_OPTIONS = {
    "Dropdown": ("types.DropdownView", types.DropdownView),
    "Radio": ("types.RadioGroupView", types.RadioView),
    "Tabs": ("types.TabsView", types.TabsView),
    "Autocomplete": ("types.AutocompleteView", types.AutocompleteView),
}

VIEW_TYPE_TO_OPTIONS = {
    "Boolean": BOOLEAN_VIEW_OPTIONS,
    "Float": FLOAT_VIEW_OPTIONS,
    "Message": MESSAGE_VIEW_OPTIONS,
    "Radio group": RADIO_GROUP_VIEW_OPTIONS,
}


def _create_view_type_input(inputs):
    radio_group = types.RadioGroup()
    for key in sorted(VIEW_TYPE_TO_OPTIONS.keys()):
        radio_group.add_choice(key, label=key)

    inputs.enum(
        "view_type",
        radio_group.values(),
        label="Component type",
        description="Select a type of component to create",
        required=True,
        default=radio_group.choices[0].value,
        view=types.RadioView(),
    )


def _create_options_input(inputs, options_dict, view_type):
    oi_radio_group = types.RadioGroup()
    for key, _ in options_dict.items():
        oi_radio_group.add_choice(key.capitalize(), label=key.capitalize())

    if view_type == "Boolean":
        inputs.str(
            "boolean_config",
            view=types.Header(
                label="Boolean configuration",
                description="Use the options below to configure a boolean property",
                divider=True,
            ),
        )

        inputs.enum(
            "boolean_view_type",
            oi_radio_group.values(),
            label="Boolean type",
            default=oi_radio_group.choices[0].value,
            required=True,
            view=types.RadioView(),
        )
    elif view_type == "Float":
        inputs.str(
            "float_config",
            view=types.Header(
                label="Float configuration",
                description="Use the options below to configure a float property",
                divider=True,
            ),
        )

        inputs.enum(
            "float_view_type",
            oi_radio_group.values(),
            label="Float type",
            default=oi_radio_group.choices[0].value,
            required=True,
            view=types.RadioView(),
        )
    elif view_type == "Message":
        inputs.str(
            "message_config",
            view=types.Header(
                label="Message configuration",
                description="Use the options below to configure a message property",
                divider=True,
            ),
        )

        inputs.enum(
            "message_view_type",
            oi_radio_group.values(),
            label="Message type",
            default=oi_radio_group.choices[0].value,
            required=True,
            view=types.RadioView(),
        )
    elif view_type == "Radio group":
        inputs.str(
            "radio_config",
            view=types.Header(
                label="Radio group configuration",
                description="Use the options below to configure a radio group",
                divider=True,
            ),
        )

        inputs.enum(
            "radio_view_type",
            oi_radio_group.values(),
            label="Radio group type",
            required=True,
            default=oi_radio_group.choices[0].value,
            view=types.RadioView(),
        )


def _create_view_code(ctx, inputs, view_type):
    if view_type == "Boolean":
        _create_boolean_code(ctx, inputs)
    elif view_type == "Float":
        _create_float_code(ctx, inputs)
    elif view_type == "Message":
        _create_message_code(ctx, inputs)
    elif view_type == "Radio group":
        _create_radio_group_code(ctx, inputs)


def _create_boolean_code(ctx, inputs):
    view_type = ctx.params.get("boolean_view_type", "Checkbox")
    view_text, view_realization = BOOLEAN_VIEW_OPTIONS[view_type]

    inputs.str(
        "boolean_code",
        view=types.Header(
            label="Boolean code",
            description="Here's the code for the boolean you created",
            divider=True,
        ),
    )

    has_default = ctx.params.get("boolean_view_has_default", False)
    if has_default:
        default = ctx.params.get("boolean_view_default", None)
        default_code = f"\n    default={default}"
    else:
        default = None
        default_code = ""

    code = f"""
    inputs.bool(
        "my_boolean",
        label="My boolean label",
        description="My boolean description",
        view={view_text}(),{default_code}
    )"""

    inputs.str(
        f"boolean_code_{view_type}",
        default=_dedent_code(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "boolean_preview_header",
        view=types.Header(
            label="Boolean preview",
            description="Here's a preview of the boolean you created",
            divider=True,
        ),
    )

    inputs.bool(
        "boolean_preview",
        label="My boolean label",
        description="My boolean description",
        view=view_realization(),
        default=default,
    )


def _create_float_props(inputs):
    obj = types.Object()
    obj.float(
        "float_view_min",
        label="Min",
        description="Min value for the float",
        view=types.FieldView(space=2),
    )
    obj.float(
        "float_view_max",
        label="Max",
        description="Max value for the float",
        view=types.FieldView(space=2),
    )
    obj.float(
        "float_view_step",
        label="Step",
        description="Step value for the float",
        view=types.FieldView(space=2),
    )
    obj.float(
        "float_view_default",
        label="Default",
        description="Default value",
        view=types.FieldView(space=2),
    )
    inputs.define_property("float_props", obj)


def _create_float_code(ctx, inputs):
    view_type = ctx.params.get("float_view_type", "Slider")
    view_text, view_realization = FLOAT_VIEW_OPTIONS[view_type]

    _create_float_props(inputs)
    float_props = ctx.params.get("float_props", {})

    min = float_props.get("float_view_min", None)
    max = float_props.get("float_view_max", None)
    step = float_props.get("float_view_step", None)
    default = float_props.get("float_view_default", None)

    componentsPropsDict = {}
    if min is not None:
        componentsPropsDict["min"] = min
    if max is not None:
        componentsPropsDict["max"] = max
    if step is not None:
        componentsPropsDict["step"] = step

    if view_text == "types.SliderView":
        componentProps = {"slider": componentsPropsDict}
    elif view_text == "types.FieldView":
        componentProps = {"field": componentsPropsDict}
    else:
        raise ValueError("Invalid view type")

    inputs.str(
        "float_code",
        view=types.Header(
            label="Float code",
            description="Here's the code for the float you created",
            divider=True,
        ),
    )

    default_code = f"\n    default={default}" if default is not None else ""

    if len(componentsPropsDict) == 0:
        component_props_code = ""
    else:
        component_props_code = "componentProps=" + str(componentProps).replace(
            "{", "{"
        ).replace("}", "}")

    code = f"""
    inputs.float(
        "my_float",
        label="My float label",
        description="My float description",
        view={view_text}({component_props_code}),{default_code}
    )"""

    inputs.str(
        f"float_code_{view_type}_{min}_{max}_{step}_{default}",
        default=_dedent_code(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "float_preview_header",
        view=types.Header(
            label="Float preview",
            description="Here's a preview of the float you created",
            divider=True,
        ),
    )

    inputs.float(
        "float_preview",
        label="My float label",
        description="My float description",
        view=view_realization(componentsProps=componentProps),
        default=default,
    )


def _create_message_code(ctx, inputs):
    view_type = ctx.params.get("message_view_type", "Message")

    inputs.str(
        "message_label",
        label="Message label",
        default="Message label",
    )
    inputs.str(
        "message_description",
        label="Message description",
        default="Message description",
    )

    inputs.str(
        "message_code",
        view=types.Header(
            label="Message code",
            description="Here's the code for the message you created",
            divider=True,
        ),
    )

    label = ctx.params.get("message_label", "Message Label")
    description = ctx.params.get("message_description", "Message Description")

    if view_type == "Message":
        code = f"""
        inputs.message(
            "message", 
            label="{label}", 
            description="{description}"
        )"""
    elif view_type == "Success":
        code = f"""
        inputs.view(
            "success", 
            types.Success(label="{label}", description="{description}")
        )"""
    elif view_type == "Warning":
        code = f"""
        inputs.view(
            "warning", 
            types.Warning(label="{label}", description="{description}")
        )"""
    elif view_type == "Error":
        code = f"""
        inputs.view(
            "error", 
            types.Error(label="{label}", description="{description}")
        )"""
    elif view_type == "Header":
        code = f"""
        inputs.view(
            "header", 
            types.Header(label="{label}", description="{description}", divider=True)
        )"""
    else:
        raise ValueError("Invalid view type")

    inputs.str(
        f"message_code_{view_type}_{label}_{description}",
        default=_dedent_code(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "message_preview_header",
        view=types.Header(
            label="Message preview",
            description="Here's a preview of the message you created",
            divider=True,
        ),
    )

    if view_type == "Message":
        inputs.message(
            f"message_{label}_{description}", label, description=description
        )
    elif view_type == "Success":
        inputs.view(
            f"success_{label}_{description}",
            types.Success(label=label, description=description),
        )
    elif view_type == "Warning":
        inputs.view(
            f"warning_{label}_{description}",
            types.Warning(label=label, description=description),
        )
    elif view_type == "Error":
        inputs.view(
            f"error_{label}_{description}",
            types.Error(label=label, description=description),
        )
    elif view_type == "Header":
        inputs.view(
            f"header_{label}_{description}",
            types.Header(label=label, description=description, divider=True),
        )


def _create_radio_props(inputs):
    obj = types.Object()
    obj.bool(
        "has_default",
        label="Set default?",
        default=False,
        view=types.CheckboxView(space=2),
    )
    obj.bool(
        "required",
        label="Required?",
        default=False,
        view=types.CheckboxView(space=3),
    )
    inputs.define_property("radio_props", obj)


def _create_radio_group_code(ctx, inputs):
    view_type = ctx.params.get("radio_view_type", "Dropdown")

    _create_radio_props(inputs)
    view_text, view_realization = RADIO_GROUP_VIEW_OPTIONS[view_type]
    rbp = ctx.params.get("radio_props", {})
    has_default = rbp.get("has_default", False)
    required = rbp.get("required", False)

    if has_default:
        default = "aaa"
        default_code = f"    default='{default}',\n    "
    else:
        default = None
        default_code = ""

    inputs.str(
        "radio_group_code",
        view=types.Header(
            label="Radio group code",
            description="Here's the code for the radio group you created",
            divider=True,
        ),
    )

    code = f"""
    my_choices = ["aaa", "abc", "ace"] # replace with your choices

    my_radio_group = types.RadioGroup()

    for choice in my_choices:
        my_radio_group.add_choice(choice, label=choice)

    inputs.enum(
        "my_radio_group",
        my_radio_group.values(),
        label="My radio group label",
        description="My radio group description",
        view={view_text}(),
    {default_code}    required={required},
    )"""

    inputs.str(
        f"radio_group_code_{view_type}_{has_default}_{default}_{required}",
        default=_dedent_code(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "radio_group_preview",
        view=types.Header(
            label="Radio group preview",
            description="Here's a preview of the radio group you created",
            divider=True,
        ),
    )

    radio_group_preview = types.RadioGroup()
    for choice in ["aaa", "abc", "ace"]:
        radio_group_preview.add_choice(choice, label=choice)

    inputs.enum(
        f"radio_group_preview_{default}",
        radio_group_preview.values(),
        label="My radio group label",
        description="My radio group description",
        view=view_realization(),
        default=default,
        required=required,
    )


class BuildOperatorSkeleton(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="build_operator_skeleton",
            label="Build operator skeleton",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _operator_skeleton_tabs_input(inputs)

        main_tab = ctx.params.get("operator_skeleton_tab", "1️⃣ Config")
        if "Config" in main_tab:
            _operator_skeleton_config_flow(ctx, inputs)
            _operator_skeleton_placement_flow(ctx, inputs)
        elif "Input" in main_tab:
            _operator_skeleton_io_flow(ctx, inputs)
        elif "Execution" in main_tab:
            _operator_skeleton_execution_flow(ctx, inputs)
            _operator_skeleton_delegation_flow(ctx, inputs)
        elif "Code" in main_tab:
            _operator_skeleton_view_code_flow(ctx, inputs)
        else:
            _create_skeleton(ctx, inputs)

        view = types.View(label="Build operator skeleton")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        plugin_dir = _parse_plugin_dir(ctx)

        # Create __init__.py
        init = _create_operator_skeleton_code(ctx)
        init_path = fos.join(plugin_dir, "__init__.py")
        fos.write_file(init, init_path)

        # Create fiftyone.yml
        yml = _create_fiftyone_yml_code(ctx)
        yml_path = fos.join(plugin_dir, "fiftyone.yml")
        fos.write_file(yml, yml_path)


OPERATOR_SKELETON_TABS = (
    "1️⃣ Config & Placement",
    "2️⃣ Input & Output",
    "3️⃣ Execution & Delegation",
    "4️⃣ Preview Code",
    "▶️ Create",
)


def _operator_skeleton_tabs_input(inputs):
    os_group = types.RadioGroup()
    for tab in OPERATOR_SKELETON_TABS:
        os_group.add_choice(tab, label=tab)

    inputs.enum(
        "operator_skeleton_tab",
        os_group.values(),
        label="Skeleton creation",
        description="Walk through the steps to create an operator skeleton",
        view=types.TabsView(),
        default=OPERATOR_SKELETON_TABS[0],
    )


def _operator_skeleton_config_flow(ctx, inputs):
    inputs.str(
        "operator_name",
        label="Operator name",
        default="my_operator",
        description="The name of your operator",
        required=True,
    )

    inputs.str(
        "operator_label",
        label="Operator label",
        default="My operator",
        description="The label of your operator",
        required=True,
    )

    inputs.str(
        "operator_description",
        label="Operator description",
        default="My operator description",
        description="The description of your operator",
    )

    obj = types.Object()
    obj.bool(
        "operator_dynamic",
        label="Dynamic?",
        default=False,
        view=types.CheckboxView(space=3),
    )

    obj.bool(
        "execute_as_generator",
        label="Execute as generator?",
        default=False,
        view=types.CheckboxView(space=3),
    )

    obj.bool(
        "unlisted",
        label="Unlisted?",
        default=False,
        view=types.CheckboxView(space=3),
    )

    obj.bool(
        "on_startup",
        label="On startup?",
        default=False,
        view=types.CheckboxView(space=3),
    )

    icon_obj = types.Object()
    icon_obj.bool(
        "config_icon",
        label="Icon?",
        default=True,
        view=types.CheckboxView(space=3),
    )

    icon_obj.bool(
        "config_light_icon",
        label="Light icon?",
        default=False,
        view=types.CheckboxView(space=3),
    )

    icon_obj.bool(
        "config_dark_icon",
        label="Dark icon?",
        default=False,
        view=types.CheckboxView(space=3),
    )

    inputs.define_property("config_bool_props", obj)
    inputs.define_property("config_icon_props", icon_obj)


def _create_operator_config_code(ctx):
    operator_name = ctx.params.get("operator_name", "my_operator")
    operator_label = ctx.params.get("operator_label", "My operator")
    operator_description = ctx.params.get(
        "operator_description", "My operator description"
    )

    config_bool_props = ctx.params.get("config_bool_props", {})
    dynamic = config_bool_props.get("operator_dynamic", False)
    execute_as_generator = config_bool_props.get("execute_as_generator", False)
    unlisted = config_bool_props.get("unlisted", False)
    on_startup = config_bool_props.get("on_startup", False)

    config_icon_props = ctx.params.get("config_icon_props", {})
    config_icon = config_icon_props.get("config_icon", True)
    config_light_icon = config_icon_props.get("config_light_icon", False)
    config_dark_icon = config_icon_props.get("config_dark_icon", False)

    code = f"""
    @property
    def config(self):
        return foo.OperatorConfig(
            name="{operator_name}",
            label="{operator_label}",
            description="{operator_description}","""

    if dynamic:
        code += f"""
            dynamic={dynamic},"""
    if execute_as_generator:
        code += f"""
            execute_as_generator={execute_as_generator},"""
    if unlisted:
        code += f"""
            unlisted={unlisted},"""
    if on_startup:
        code += f"""
            on_startup={on_startup},"""
    if config_icon:
        code += f"""
            icon="/path/to/icon.svg","""
    if config_light_icon:
        code += f"""
            light_icon="/path/to/light_icon.svg","""
    if config_dark_icon:
        code += f"""
            dark_icon="/path/to/dark_icon.svg","""

    code += f"""
        )"""

    return _dedent_code(code)


def _operator_skeleton_io_flow(ctx, inputs):
    inputs.bool(
        "operator_input_has_input",
        label="Has input?",
        default=False,
        view=types.SwitchView(),
    )

    inputs.bool(
        "operator_output_has_output",
        label="Has output?",
        default=False,
        view=types.SwitchView(),
    )


def _operator_skeleton_input_code(ctx):
    has_input = ctx.params.get("operator_input_has_input", False)
    delegation = ctx.params.get("delegated_execution_choices", "False")
    deleg_user_choice = delegation == "User Choice"

    if has_input and not deleg_user_choice:
        code = """
        def resolve_input(self, ctx):
            inputs = types.Object()

            ### Add your inputs here ###

            return types.Property(inputs)
        """
    elif has_input and deleg_user_choice:
        code = """
        def resolve_input(self, ctx):
            inputs = types.Object()

            ### Add your inputs here ###

            _execution_mode(ctx, inputs)
            return types.Property(inputs)
        """
    elif deleg_user_choice:
        code = """
        def resolve_input(self, ctx):
            inputs = types.Object()

            _execution_mode(ctx, inputs)
            return types.Property(inputs)
        """
    else:
        code = """
        def resolve_input(self, ctx):
            pass
        """

    return _dedent_code(code)


TRIGGER_CHOICES = (
    "Reload Samples",
    "Reload Dataset",
    "Set View",
    "Open A Panel",
)

LAYOUT_CHOICES = ("Horizontal", "Vertical")

PANEL_CHOICES = ("Embeddings", "Histograms")


def _operator_skeleton_execution_flow(ctx, inputs):
    inputs.bool(
        "operator_execution_has_trigger",
        label="Has trigger?",
        description=(
            "Check this if you want the execution of your operator to "
            "trigger another operation"
        ),
        default=False,
        view=types.CheckboxView(),
    )

    has_trigger = ctx.params.get("operator_execution_has_trigger", False)

    if has_trigger:
        trigger_group = types.RadioGroup()
        for choice in TRIGGER_CHOICES:
            trigger_group.add_choice(choice, label=choice)

        inputs.enum(
            "operator_execution_trigger",
            trigger_group.values(),
            label="Trigger operator",
            description="You can trigger any operator! Here are some common choices",
            default=TRIGGER_CHOICES[0],
            view=types.DropdownView(),
        )

        trigger_type = ctx.params.get(
            "operator_execution_trigger", TRIGGER_CHOICES[0]
        )

        if trigger_type == "Open A Panel":
            panel_group = types.RadioGroup()
            for choice in PANEL_CHOICES:
                panel_group.add_choice(choice, label=choice)

            inputs.enum(
                "operator_execution_trigger_panel",
                panel_group.values(),
                label="panel_type",
                default=PANEL_CHOICES[0],
                view=types.DropdownView(),
            )

            layout_group = types.RadioGroup()
            for choice in LAYOUT_CHOICES:
                layout_group.add_choice(choice, label=choice)

            inputs.enum(
                "operator_execution_trigger_layout",
                layout_group.values(),
                label="layout_type",
                default=LAYOUT_CHOICES[0],
                view=types.DropdownView(),
            )


def _operator_skeleton_execution_code(ctx):
    has_trigger = ctx.params.get("operator_execution_has_trigger", False)

    if has_trigger:
        trigger_type = ctx.params.get(
            "operator_execution_trigger", TRIGGER_CHOICES[0]
        )
        if trigger_type == "Reload Samples":
            code = """
            def execute(self, ctx):
                ### Your logic here ###

                ctx.trigger("reload_samples")
                return {}
            """
        elif trigger_type == "Reload Dataset":
            code = """
            def execute(self, ctx):
                ### Your logic here ###

                ctx.trigger("reload_dataset")
                return {}
            """
        elif trigger_type == "Set View":
            code = """
            def execute(self, ctx):
                ### Your logic here ###
            
                ### Create your view here ###
                view = ctx.dataset.take(10)

                ctx.trigger(
                    "set_view",
                    params=dict(view=_serialize_view(view)),
                )
                return {}
            """
        elif trigger_type == "Open A Panel":
            panel_type = ctx.params.get(
                "operator_execution_trigger_panel", PANEL_CHOICES[0]
            )
            layout_type = ctx.params.get(
                "operator_execution_trigger_layout", LAYOUT_CHOICES[0]
            )

            code = f"""
            def execute(self, ctx):
                ### Your logic here ###

                ctx.trigger(
                    "open_panel",
                    params=dict(
                        name="{panel_type}", 
                        isActive=True, 
                        layout="{layout_type}"
                        ),
                )
                return {{}}
            """
        else:
            raise ValueError("Invalid trigger type")
    else:
        code = """
        def execute(self, ctx):
            ### Your logic here ###
        
            return {}
        """

    return _dedent_code(code)


def _operator_skeleton_delegation_flow(ctx, inputs):
    delegation_choices = ("False", "True", "User Choice")
    degelation_group = types.RadioGroup()
    for choice in delegation_choices:
        degelation_group.add_choice(choice, label=choice)

    inputs.enum(
        "delegated_execution_choices",
        degelation_group.values(),
        label="Delegate execution?",
        description=(
            "Should this operator be executed immediately or delegated for "
            "execution on an orchestrator"
        ),
        view=types.RadioView(),
        default="False",
    )


IMPORTS_CODE = """
import fiftyone as fo
import fiftyone.operators as foo
from fiftyone.operators import types
"""

EXECUTION_MODE_CODE = """
def _execution_mode(ctx, inputs):
    delegate = ctx.params.get("delegate", None)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=None,
        label="Delegate execution?",
        description=description,
        view=types.CheckboxView(),
    )

    if delegate:
        inputs.view(
            "notice",
            types.Notice(
                label=(
                    "You've chosen delegated execution. Note that you must "
                    "have a delegated operation service running in order for "
                    "this task to be processed. See "
                    "https://docs.voxel51.com/plugins/index.html#operators "
                    "for more information"
                )
            ),
        )
"""


def _operator_skeleton_delegation_code(ctx):
    delegated_execution = ctx.params.get(
        "delegated_execution_choices", "False"
    )

    if delegated_execution == "False":
        code = ""
    elif delegated_execution == "True":
        code = """
        def resolve_delegation(self, ctx):
            True
        """
    elif delegated_execution == "User Choice":
        code = """
        def resolve_delegation(self, ctx):
            return ctx.params.get("delegate", None)
        """
    else:
        raise ValueError("Invalid delegation choice")

    return _dedent_code(code)


def _operator_skeleton_output_code(ctx):
    has_output = ctx.params.get("operator_output_has_output", False)

    if has_output:
        code = """
        def resolve_output(self, ctx):
            outputs = types.Object()

            ### Add your outputs here ###

            return types.Property(outputs)
        """
    else:
        code = ""

    return _dedent_code(code)


PLACEMENTS = (
    "SAMPLES-GRID-ACTIONS",
    "SAMPLES-GRID-SECONDARY-ACTIONS",
    "SAMPLES-VIEWER-ACTIONS",
)


def _operator_skeleton_placement_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_placement_header",
        view=types.Header(
            label="Placement",
            description=(
                "You can optionally place buttons, etc in the App to trigger "
                "operators"
            ),
        ),
    )

    inputs.bool(
        "operator_placement_has_placement",
        label="Has placement?",
        default=False,
        view=types.SwitchView(),
    )

    if ctx.params.get("operator_placement_has_placement", False):
        placement_group = types.RadioGroup()
        for choice in PLACEMENTS:
            placement_group.add_choice(choice, label=choice)

        inputs.enum(
            "operator_placement",
            placement_group.values(),
            label="Placement",
            default=PLACEMENTS[0],
            view=types.DropdownView(),
        )

        inputs.str(
            "placement_label",
            label="Placement label",
            default="My placement label",
        )

        inputs.bool(
            "placement_has_icon",
            label="Placement icon?",
            default=True,
        )

        inputs.str(
            "placement_icon",
            label="Placement icon",
            default="/path/to/icon.svg",
        )

        inputs.bool(
            "placement_prompt",
            label="Placement prompt?",
            default=False,
            description=(
                "If checked, the user will be prompted when the button is "
                "clicked"
            ),
        )


def _operator_skeleton_placement_code(ctx):
    has_placement = ctx.params.get("operator_placement_has_placement", False)

    if has_placement:
        placement = ctx.params.get("operator_placement", PLACEMENTS[0])
        placement_label = ctx.params.get(
            "placement_label", "My Placement Label"
        )
        placement_prompt = ctx.params.get("placement_prompt", False)

        placement_has_icon = ctx.params.get("placement_has_icon", True)
        placement_icon = ctx.params.get("placement_icon", "/path/to/icon.svg")
        placement_icon = (
            f'"{placement_icon}"' if placement_has_icon else "None"
        )

        code = f"""
        def resolve_placement(self, ctx):
            return types.Placement(
                types.Places.{placement},
                label="{placement_label}",
                icon={placement_icon},
                prompt={placement_prompt}
            )
        """
    else:
        code = ""

    return _dedent_code(code)


def _dedent_code(code):
    return dedent(code).strip()


def _indent_code(code):
    dedented_code = _dedent_code(code)
    return "    " + dedented_code.replace("\n", "\n    ")


def _create_operator_class_name(ctx):
    operator_name = ctx.params.get("operator_name", "my_operator")
    class_name = operator_name.replace("_", " ").title().replace(" ", "")
    return class_name


SERIALIZE_VIEW_CODE = """
def _serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))
"""


def _create_class_header(ctx):
    class_name = _create_operator_class_name(ctx)
    return f"class {class_name}(foo.Operator):"


def _create_footer(ctx):
    class_name = _create_operator_class_name(ctx)
    footer_code = f"""
    def register(plugin):
        plugin.register({class_name})
    """
    return _dedent_code(footer_code)


def _create_operator_skeleton_code(ctx):
    set_view = ctx.params.get("operator_execution_trigger", None) == "Set View"
    user_choice = (
        ctx.params.get("delegated_execution_choices", None) == "User Choice"
    )

    header = ""

    if set_view:
        header += "import json\n"
        header += "from bson import json_util\n\n"

    header += IMPORTS_CODE.strip() + "\n\n\n"
    header += _create_class_header(ctx) + "\n"

    chunks = [
        _create_operator_config_code(ctx),
        _operator_skeleton_input_code(ctx),
        _operator_skeleton_placement_code(ctx),
        _operator_skeleton_delegation_code(ctx),
        _operator_skeleton_execution_code(ctx),
        _operator_skeleton_output_code(ctx),
    ]
    body = _indent_code("\n\n".join([c for c in chunks if c])) + "\n\n\n"

    if user_choice:
        body += EXECUTION_MODE_CODE.strip() + "\n\n\n"

    if set_view:
        body += SERIALIZE_VIEW_CODE.strip() + "\n\n\n"

    footer = _create_footer(ctx) + "\n"

    return header + body + footer


def _operator_skeleton_view_code_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_view_code",
        label="Python code",
        description="Here's your __init__.py!",
        default=_create_operator_skeleton_code(ctx),
        view=types.CodeView(language="python", readOnly=True),
    )


def _create_skeleton(ctx, inputs):
    inputs.str(
        "plugin_name",
        label="Plugin name",
        default="@github_username/plugin_name",
        description="The name of your plugin",
        required=True,
    )

    inputs.str(
        "plugin_description",
        label="Plugin description",
        description="The description of your plugin",
        default="My plugin description",
    )

    inputs.str(
        "plugin_dir_header",
        view=types.Header(
            label="Plugin directory",
            description="Choose where to write your plugin's source",
        ),
    )

    tab_choices = types.TabsView()
    tab_choices.add_choice("PLUGIN", label="Plugins directory")
    tab_choices.add_choice("OTHER", label="Other directory")
    inputs.enum(
        "location",
        tab_choices.values(),
        default="PLUGIN",
        view=tab_choices,
    )
    tab = ctx.params.get("location", "PLUGIN")

    if tab == "PLUGIN":
        inputs.str(
            "plugin_subdir",
            description=(
                "Choose a subdirectory of your plugins directory to write "
                "this plugin"
            ),
            default="plugin_name",
            required=True,
        )
    else:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )

        inputs.file(
            "plugin_dir",
            required=True,
            description="Choose a directory in which to create the plugin",
            view=file_explorer,
        )

    plugin_dir = _parse_plugin_dir(ctx)
    if tab == "PLUGIN" and plugin_dir is not None:
        inputs.view(
            "confirmation",
            types.Notice(
                label=f"Plugin files will be written to {plugin_dir}"
            ),
        )


def _parse_plugin_dir(ctx):
    tab = ctx.params.get("location", "PLUGIN")
    if tab == "PLUGIN":
        plugin_subdir = ctx.params.get("plugin_subdir", None)
        if plugin_subdir:
            plugin_dir = fos.join(fo.config.plugins_dir, plugin_subdir)
        else:
            plugin_dir = None
    else:
        plugin_dir = ctx.params.get("plugin_dir", {}).get(
            "absolute_path", None
        )

    return plugin_dir


def _create_fiftyone_yml_code(ctx):
    plugin_name = ctx.params["plugin_name"]
    plugin_description = ctx.params.get(
        "plugin_description", "My plugin description"
    )
    operator_name = ctx.params.get("operator_name", "my_operator")
    yml_code = f"""
    name: "{plugin_name}"
    version: "0.1.0"
    description: "{plugin_description}"
    operators:
      - {operator_name}
    """
    return _dedent_code(yml_code) + "\n"


def register(p):
    p.register(InstallPlugin)
    p.register(ManagePlugins)
    p.register(BuildPluginComponent)
    p.register(BuildOperatorSkeleton)
