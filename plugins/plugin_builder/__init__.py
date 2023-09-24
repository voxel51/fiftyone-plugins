"""Plugin builder plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import re
from textwrap import dedent

import fiftyone as fo
import fiftyone.operators as foo
from fiftyone.operators import types


radio_group_view_options = {
    "Dropdown": ("types.DropdownView", types.DropdownView),
    "Radio": ("types.RadioGroupView", types.RadioView),
    "Tabs": ("types.TabsView", types.TabsView),
    "Autocomplete": ("types.AutocompleteView", types.AutocompleteView),
}

boolean_view_options = {
    "Checkbox": ("types.CheckboxView", types.CheckboxView),
    "Switch": ("types.SwitchView", types.SwitchView),
}

float_view_options = {
    "Slider": ("types.SliderView", types.SliderView),
    "Field": ("types.FieldView", types.FieldView),
}

message_view_options = {
    "Message": None,
    "Success": None,
    "Warning": None,
    "Error": None,
    "Header": None,
}


view_type_to_options = {
    "radio_group": radio_group_view_options,
    "boolean": boolean_view_options,
    "float": float_view_options,
    "message": message_view_options,
}


def _create_view_type_input(inputs):
    inputs.str(
        "view_type_header",
        view=types.Header(
            label="View Type",
            description="Select the type of view you want to create",
            divider=True,
        ),
    )

    vt_radio_group = types.RadioGroup()
    for key, _ in view_type_to_options.items():
        vt_radio_group.add_choice(key, label=key)
    inputs.enum(
        "view_type",
        vt_radio_group.values(),
        view=types.DropdownView(),
        required=True,
    )


def _create_options_input(inputs, options_dict, view_type):
    oi_radio_group = types.RadioGroup()
    for key, _ in options_dict.items():
        oi_radio_group.add_choice(key.capitalize(), label=key.capitalize())

    if view_type == "radio_group":
        inputs.message(
            "radio_view_message",
            "Select the type of radio group you want to create",
        )
        inputs.enum(
            "radio_view_type",
            oi_radio_group.values(),
            view=types.RadioView(),
            default=oi_radio_group.choices[0].value,
            required=True,
        )
    elif view_type == "boolean":
        inputs.message(
            "boolean_view_message",
            "Select the type of boolean component you want to create",
        )
        inputs.enum(
            "boolean_view_type",
            oi_radio_group.values(),
            view=types.RadioView(),
            default=oi_radio_group.choices[0].value,
            required=True,
        )
    elif view_type == "float":
        inputs.message(
            "float_view_message",
            "Select the type of float component you want to create",
        )
        inputs.enum(
            "float_view_type",
            oi_radio_group.values(),
            view=types.RadioView(),
            default=oi_radio_group.choices[0].value,
            required=True,
        )
    elif view_type == "message":
        inputs.message(
            "message_view_message",
            "Select the type of message component you want to create",
        )
        inputs.enum(
            "message_view_type",
            oi_radio_group.values(),
            view=types.RadioView(),
            default=oi_radio_group.choices[0].value,
            required=True,
        )


def _create_view_code(ctx, inputs, view_type):
    if view_type == "radio_group":
        _create_radio_group_code(ctx, inputs)
    elif view_type == "boolean":
        _create_boolean_code(ctx, inputs)
    elif view_type == "float":
        _create_float_code(ctx, inputs)
    elif view_type == "message":
        _create_message_code(ctx, inputs)


#### Radio Props ####
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


#### Radio Group ####
def _create_radio_group_code(ctx, inputs):
    view_type = ctx.params.get("radio_view_type", "Dropdown")

    _create_radio_props(inputs)
    view_text, view_realization = radio_group_view_options[view_type]
    rbp = ctx.params.get("radio_props", {})
    has_default = rbp.get("has_default", False)
    required = rbp.get("required", False)

    if has_default:
        default = "aaa"
        default_code = f"    default='{default}',\n    "
    else:
        default = None
        default_code = ""

    code = f"""
    my_choices = ["aaa", "abc", "ace"] # replace with your choices

    my_radio_group = types.RadioGroup()

    for choice in my_choices:
        my_radio_group.add_choice(choice, label=choice)

    inputs.enum(
        "my_radio_group",
        my_radio_group.values(),
        label="My radio groups label",
        description="My radio groups description",
        view={view_text}(),
    {default_code}    required={required},
    )"""

    inputs.str(
        f"radio_group_code_{view_type}_{has_default}_{default}_{required}",
        label="Radio Group Code",
        default=dedent(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "radio_groups_preview",
        view=types.Header(
            label=f"Radio Groups Preview",
            description="Preview of the radio groups you created above",
            divider=True,
        ),
    )

    radio_groups_preview = types.RadioGroup()
    for choice in ["aaa", "abc", "ace"]:
        radio_groups_preview.add_choice(choice, label=choice)
    inputs.enum(
        f"radio_groups_preview_{default}",
        radio_groups_preview.values(),
        label="My radio groups label",
        description="My radio groups description",
        view=view_realization(),
        default=default,
        required=required,
    )


#### Boolean ####
def _create_boolean_code(ctx, inputs):
    view_type = ctx.params.get("boolean_view_type", "Checkbox")
    view_text, view_realization = boolean_view_options[view_type]

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
        label="Boolean Code",
        default=dedent(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "boolean_preview_header",
        view=types.Header(
            label=f"Boolean Preview",
            description="Preview of the boolean you created above",
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


#### Float Props ####
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


#### Float ####
def _create_float_code(ctx, inputs):
    view_type = ctx.params.get("float_view_type", "Slider")
    view_text, view_realization = float_view_options[view_type]

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
        label="Float Code",
        default=dedent(code),
        view=types.CodeView(language="python"),
    )

    inputs.str(
        "float_preview_header",
        view=types.Header(
            label=f"Float Preview",
            description="Preview of the float you created above",
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


#### Message ####


def _create_message_code(ctx, inputs):
    view_type = ctx.params.get("message_view_type", "Message")

    inputs.str(
        "message_label",
        label="Message Label",
        default="Message Label",
    )
    inputs.str(
        "message_description",
        label="Message Description",
        default="Message Description",
    )

    label = ctx.params.get("message_label", "Message Label")
    description = ctx.params.get("message_description", "Message Description")

    ## Code
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
        label="Message Code",
        default=dedent(code),
        view=types.CodeView(language="python"),
    )

    ## Header
    inputs.str(
        "message_preview_header",
        view=types.Header(
            label=f"Message Preview",
            description="Preview of the message you created above",
            divider=True,
        ),
    )

    ## Preview
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


class BuildAComponent(foo.Operator):
    @property
    def config(self):
        _config = foo.OperatorConfig(
            name="build_component",
            label="Plugin Builder: create your perfect plugin component!",
            description="Manage plugins",
            dynamic=True,
        )
        _config.icon = "/assets/build_icon.svg"
        return _config

    def resolve_input(self, ctx):
        inputs = types.Object()
        form_view = types.View(
            label="Build a Plugin",
            description="Create your perfect plugin!",
        )

        _create_view_type_input(inputs)
        view_type = ctx.params.get("view_type", None)
        if view_type is None:
            return types.Property(inputs, view=form_view)

        view_options = view_type_to_options[view_type]
        _create_options_input(inputs, view_options, view_type)
        _create_view_code(ctx, inputs, view_type)

        return types.Property(inputs, view=form_view)

    def execute(self, ctx):
        pass


#################################################
############### Operator Skeleton ###############
#################################################

operator_skeleton_tabs = (
    "1️⃣ Config",
    "2️⃣ Input",
    "3️⃣ Execution",
    "4️⃣ Delegation",
    "5️⃣ Output",
    "6️⃣ Placement",
    "▶️ View Code",
)


def _operator_skeleton_tabs_input(inputs):
    os_group = types.RadioGroup()
    for choice in operator_skeleton_tabs:
        os_group.add_choice(choice, label=choice)

    inputs.enum(
        "operator_skeleton_tab",
        os_group.values(),
        label="Skeleton Creation",
        description="Walk through the steps to create a Python operator skeleton",
        view=types.TabsView(),
        default=operator_skeleton_tabs[0],
    )


def _operator_skeleton_config_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_config_header",
        view=types.Header(
            label="Config",
            description="Configure your operator",
            divider=True,
        ),
    )

    inputs.str(
        "operator_name",
        label="Operator Name",
        default="my_operator",
        description="The name of your operator",
        required=True,
    )

    inputs.str(
        "operator_label",
        label="Operator Label",
        default="My Operator",
        description="The label of your operator",
    )

    inputs.str(
        "operator_description",
        label="Operator Description",
        default="My Operator Description",
        description="The description of your operator",
    )

    obj = types.Object()
    obj.bool(
        "operator_dynamic",
        label="Dynamic?",
        default=False,
        view=types.CheckboxView(space=2),
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
        view=types.CheckboxView(space=2),
    )

    obj.bool(
        "on_startup",
        label="On startup?",
        default=False,
        view=types.CheckboxView(space=2),
    )

    icon_obj = types.Object()
    icon_obj.bool(
        "config_icon",
        label="Icon?",
        default=True,
        view=types.CheckboxView(space=2),
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
    operator_label = ctx.params.get("operator_label", "My Operator")
    operator_description = ctx.params.get(
        "operator_description", "My Operator Description"
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
        _config = foo.OperatorConfig(
            name="{operator_name}",
            label="{operator_label}",
            description="{operator_description}",
        """

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

    code += f"""
        )"""

    icon_lines = []
    if config_icon:
        icon_lines.append('_config.icon = "/path/to/icon.svg"')
    if config_light_icon:
        icon_lines.append('_config.light_icon = "/path/to/light_icon.svg"')
    if config_dark_icon:
        icon_lines.append('_config.dark_icon = "/path/to/dark_icon.svg"')

    if icon_lines:
        code += "\n        " + "\n        ".join(icon_lines)

    code += f"""
        return _config
    """

    return dedent(code).replace("\n\n", "\n")


def _operator_skeleton_input_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_input_header",
        view=types.Header(
            label="Input",
            description="Configure your operator's input",
            divider=True,
        ),
    )

    inputs.bool(
        "operator_input_has_input",
        label="Has input?",
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
    return dedent(code).replace("\n\n", "\n")


TRIGGER_CHOICES = (
    "Reload Samples",
    "Reload Dataset",
    "Set View",
    "Open A Panel",
)

LAYOUT_CHOICES = (
    "Horizontal",
    "Vertical",
)


def _get_panel_choices():
    return ("Embeddings", "Histograms")


def _operator_skeleton_execution_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_execution_header",
        view=types.Header(
            label="Execution",
            description="Configure your operator's execution",
            divider=True,
        ),
    )

    inputs.bool(
        "operator_execution_has_trigger",
        label="Has trigger?",
        description="Check this if you want the execution of your operator to trigger on a specific event",
        default=False,
        view=types.CheckboxView(),
    )

    has_trigger = ctx.params.get("operator_execution_has_trigger", False)

    if has_trigger:
        inputs.view(
            "header",
            types.Header(
                label="Trigger Details",
                description="You can trigger any operator! Here are some common choices:",
            ),
        )

        trigger_group = types.RadioGroup()
        for choice in TRIGGER_CHOICES:
            trigger_group.add_choice(choice, label=choice)

        inputs.enum(
            "operator_execution_trigger",
            trigger_group.values(),
            label="trigger_type",
            default=TRIGGER_CHOICES[0],
            view=types.DropdownView(),
        )

        trigger_type = ctx.params.get(
            "operator_execution_trigger", TRIGGER_CHOICES[0]
        )

        if trigger_type == "Open A Panel":
            panel_group = types.RadioGroup()
            for choice in _get_panel_choices():
                panel_group.add_choice(choice, label=choice)

            inputs.enum(
                "operator_execution_trigger_panel",
                panel_group.values(),
                label="panel_type",
                default=_get_panel_choices()[0],
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
                    params=dict(view=serialize_view(view)),
                )
                return {}
            """
        elif trigger_type == "Open A Panel":
            panel_type = ctx.params.get(
                "operator_execution_trigger_panel", _get_panel_choices()[0]
            )
            layout_type = ctx.params.get(
                "operator_execution_trigger_layout", LAYOUT_CHOICES[0]
            )

            code = """
            def execute(self, ctx):
                ### Your logic here ###

                ctx.trigger(
                    "open_panel",
                    params=dict(
                        name=f"{panel_type}", 
                        isActive=True, 
                        layout=f"{layout_type}"
                        ),
                )
                return {}
            """
        else:
            raise ValueError("Invalid trigger type")
    else:
        code = """
        def execute(self, ctx):
            ### Your logic here ###
        
            return {}
        """
    return dedent(code).replace("\n\n", "\n")


def _operator_skeleton_delegation_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_delegation_header",
        view=types.Header(
            label="Delegation",
            description="Configure your operator's delegation",
            divider=True,
        ),
    )

    delegation_choices = ("False", "True", "User Choice")

    degelation_group = types.RadioGroup()
    for choice in delegation_choices:
        degelation_group.add_choice(choice, label=choice)

    inputs.enum(
        "delegated_execution_choices",
        degelation_group.values(),
        label="Delegate execution?",
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
    delegate = ctx.params.get("delegate", False)

    if delegate:
        description = "Uncheck this box to execute the operation immediately"
    else:
        description = "Check this box to delegate execution of this task"

    inputs.bool(
        "delegate",
        default=False,
        required=True,
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
            return ctx.params.get("delegate", False)
        """
    else:
        raise ValueError("Invalid delegation choice")

    return dedent(code).replace("\n\n", "\n")


def _operator_skeleton_output_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_output_header",
        view=types.Header(
            label="Output",
            description="Configure your operator's output",
            divider=True,
        ),
    )

    inputs.bool(
        "operator_output_has_output",
        label="Has output?",
        default=False,
        view=types.SwitchView(),
    )


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
    return dedent(code).replace("\n\n", "\n")


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
            description="Configure your operator's placement",
            divider=True,
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
            label="Placement Label",
            default="My Placement Label",
        )

        inputs.bool(
            "placement_has_icon",
            label="Placement Icon?",
            default=True,
        )

        inputs.str(
            "placement_icon",
            label="Placement Icon",
            default="/path/to/icon.svg",
        )

        inputs.bool(
            "placement_prompt",
            label="Placement Prompt?",
            default=False,
            description="If checked, the user will be prompted when the button is clicked",
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
                label = "{placement_label}"
                icon = {placement_icon}
                prompt = {placement_prompt}
            )
        """
    else:
        code = ""
    return dedent(code).replace("\n\n", "\n")


def indent_code(code):
    # Remove any common leading whitespace
    dedented_code = dedent(code)

    # Add 4 spaces to the beginning of each line
    indented_code = "    " + dedented_code.replace("\n", "\n    ")

    return indented_code


def replace_extra_newlines(text):
    return re.sub(r"\n{3,}", "\n\n", text)


def _create_operator_class_name(ctx):
    operator_name = ctx.params.get("operator_name", "my_operator")
    class_name = operator_name.replace("_", " ").title().replace(" ", "")
    return class_name


SERIALIZE_VIEW_CODE = """
def serialize_view(view):
    return json.loads(json_util.dumps(view._serialize()))
"""


def _create_class_header(ctx):
    class_name = _create_operator_class_name(ctx)
    return f"class {class_name}(foo.Operator):" + "\n"


def _create_footer(ctx):
    class_name = _create_operator_class_name(ctx)
    footer_code = f"""
    def register(plugin):
        plugin.register({class_name})
    """
    return dedent(footer_code)


def _create_operator_skeleton_code(ctx):
    code = _create_operator_config_code(ctx)
    code += "\n\n"
    code += _operator_skeleton_input_code(ctx)
    code += "\n\n"
    code += _operator_skeleton_execution_code(ctx)
    code += "\n\n"
    code += _operator_skeleton_delegation_code(ctx)
    code += "\n\n"
    code += _operator_skeleton_output_code(ctx)
    code += "\n\n"
    code += _operator_skeleton_placement_code(ctx)

    code = replace_extra_newlines(indent_code(code))

    class_header = _create_class_header(ctx)

    header = ""
    set_view = ctx.params.get("operator_execution_trigger", None) == "Set View"
    if set_view:
        header += "import json\n"
        header += "from bson import json_util\n"
    header += IMPORTS_CODE
    if ctx.params.get("delegated_execution_choices", "False") == "User Choice":
        header += EXECUTION_MODE_CODE
    if set_view:
        header += "\n\n"
        header += SERIALIZE_VIEW_CODE
    header += "\n\n"
    header += class_header
    footer = _create_footer(ctx)
    return replace_extra_newlines(header + code + footer)


def _operator_skeleton_view_code_flow(ctx, inputs):
    inputs.str(
        "operator_skeleton_view_code_header",
        view=types.Header(
            label="Preview Operator Skeleton",
            divider=True,
        ),
    )

    inputs.str(
        "operator_skeleton_view_code",
        label="Python Code",
        description="Preview of your `__init__.py` file",
        default=_create_operator_skeleton_code(ctx),
        view=types.CodeView(language="python", readOnly=True),
    )

    operator_name = ctx.params.get("operator_name", "my_operator")

    inputs.message(
        "yml_message",
        label="fiftyone.yml instructions",
        description=f"""
        You will also need to add the operator `{operator_name}` to your plugin's
        fiftyone.yml file to register your operator
        """,
    )


class BuildOperatorSkeleton(foo.Operator):
    @property
    def config(self):
        _config = foo.OperatorConfig(
            name="build_operator_skeleton",
            label="Plugin Builder: create a Python operator!",
            description="Create a Python operator skeleton",
            dynamic=True,
        )
        _config.icon = "/assets/build_icon.svg"
        return _config

    def resolve_input(self, ctx):
        inputs = types.Object()
        form_view = types.View(
            label="Build an operator skeleton",
            description="Walk through the steps to create a Python operator skeleton",
        )

        _operator_skeleton_tabs_input(inputs)

        main_tab = ctx.params.get("operator_skeleton_tab", "1️⃣ Config")
        if "Config" in main_tab:
            _operator_skeleton_config_flow(ctx, inputs)
        elif "Input" in main_tab:
            _operator_skeleton_input_flow(ctx, inputs)
        elif "Execution" in main_tab:
            _operator_skeleton_execution_flow(ctx, inputs)
        elif "Delegation" in main_tab:
            _operator_skeleton_delegation_flow(ctx, inputs)
        elif "Output" in main_tab:
            _operator_skeleton_output_flow(ctx, inputs)
        elif "Placement" in main_tab:
            _operator_skeleton_placement_flow(ctx, inputs)
        elif "View Code" in main_tab:
            _operator_skeleton_view_code_flow(ctx, inputs)

        return types.Property(inputs, view=form_view)

    def execute(self, ctx):
        pass


def register(plugin):
    plugin.register(BuildAComponent)
    plugin.register(BuildOperatorSkeleton)
