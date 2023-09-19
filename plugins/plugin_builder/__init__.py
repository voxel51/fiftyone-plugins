"""Plugin builder plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

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


class BuildAPlugin(foo.Operator):
    @property
    def config(self):
        _config = foo.OperatorConfig(
            name="build_a_plugin",
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


def register(plugin):
    plugin.register(BuildAPlugin)
