"""
Scenario plugin.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

from textwrap import dedent
import bson
from datetime import datetime, timezone

import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.core.fields as fof


STORE_NAME = "scenarios"


MAX_CATEGORIES = 100
ALLOWED_BY_TYPES = (
    fof.StringField,
    fof.BooleanField,
    fof.IntField,
    fof.FloatField,
)

SCENARIO_BUILDING_CHOICES = [
    {
        "type": "sample_field",
        "label": "Select sample fields",
        "icon": "add_card_outlined",
    },
    {
        "type": "label_attribute",
        "label": "Select label attributes",
        "icon": "add_card_outlined",
    },
    {
        "type": "saved_views",
        "label": "Select saved views",
        "icon": "create_new_folder_outlined';",
    },
    {
        "type": "custom_code",
        "label": "Custom code",
        "icon": "code_outlined",
    },
]


class ConfigureScenario(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="configure_scenario",
            label="Configure scenario",
            dynamic=True,
            unlisted=True,
        )

    def get_code_example(self, plot_type):
        examples = {
            "static_field": dedent(
                """
                subsets = {
                    "sunny": dict(type="field", field="tags", value="sunny"),
                    "cloudy": dict(type="field", field="tags", value="cloudy"),
                    "rainy": dict(type="field", field="tags", value="rainy"),
                }
            """
            ).strip(),
            "dynamic_field": dedent(
                """
                from fiftyone import ViewField as F

                subsets = {
                    "Low": {"field": F($FIELD) < 0.25},
                    "middle": {"field": F($FIELD) >= 0.25 & F($FIELD) < 0.75},
                    "high": {"field": F($FIELD) > 0.75},
                }
            """
            ).strip(),
            "dynamic_field_2": dedent(
                """
                from fiftyone import ViewField as F

                bbox_area = F("bounding_box")[2] * F("bounding_box")[3]
                subsets = {
                    "Small objects": dict(type="attribute", expr=bbox_area <= 0.05),
                    "Medium objects": dict(type="attribute", expr=(0.05 <= bbox_area) & (bbox_area <= 0.5)),
                    "Large objects": dict(type="attribute", expr=bbox_area > 0.5),
                }
            """
            ).strip(),
            "dynamic_field_3": dedent(
                """
                from fiftyone import ViewField as F

                subsets = {
                    "Sunny unique objects": [
                        dict(type="field", field="tags", value="sunny"),
                        dict(type="field", expr=F("uniqueness") > 0.75),
                    ],
                    "Rainy common objects": [
                        dict(type="field", field="tags", value="rainy"),
                        dict(type="field", expr=F("uniqueness") < 0.25),
                    ]
                }
            """
            ).strip(),
        }
        return examples.get(plot_type, "")

    def render_header(self, inputs):
        inputs.view(
            "header",
            types.Header(
                label="Configure scenario",
                divider=True,
                description="Create a scenario of your dataset to analyze",
            ),
        )

    def render_name_input(self, inputs, default):
        inputs.str(
            "scenario_name",
            label="Scenario Name",
            default=default,
            required=True,
            view=types.TextFieldView(
                label="Scenario Name",
                placeholder="Enter a name for the scenario",
            ),
        )

    def render_scenario_types(self, inputs, selected_type):
        inputs.view(
            "info_header_2",
            types.Header(
                label="Define scenario",
                divider=False,
                description="The field that defines the scenario you want to analyze",
            ),
        )

        groups = types.RadioGroup()
        for choice in SCENARIO_BUILDING_CHOICES:
            groups.add_choice(choice["type"], label=choice["label"])

        radio_view = types.RadioView(
            label="Scenario type",
            description="Select the type of scenario to analyze",
            variant="button",
            choices=[
                types.Choice(
                    choice["type"],
                    label=choice["label"],
                    icon=choice["icon"],
                )
                for choice in SCENARIO_BUILDING_CHOICES
            ],
        )

        inputs.enum(
            "scenario_type",
            groups.values(),
            label="Scenario building type",
            default=selected_type,
            view=radio_view,
        )

    def process_custom_code(self, ctx, custom_code):
        try:
            local_vars = {}
            exec(custom_code, {"ctx": ctx}, local_vars)
            data = local_vars.get("subsets", {})
            return data, None
        except Exception as e:
            return None, str(e)

    def render_custom_code(self, ctx, inputs, custom_code=None):
        stack = inputs.v_stack(
            "custom_code_stack",
            width="100%",
            align_x="center",
            componentsProps={
                "grid": {
                    "sx": {
                        "border": "1px solid #333",
                        "display": "flex",
                        "flexDirection": "column",
                    }
                },
            },
        )

        control_stack = stack.h_stack(
            "control_stack",
            width="100%",
            align_x="space-between",
            py=2,
            px=2,
        )

        body_stack = stack.v_stack(
            "body_stack",
            width="100%",
            componentsProps={
                "grid": {
                    "sx": {
                        "display": "flex",
                    }
                },
            },
        )

        control_stack.view(
            "info_header_3",
            types.Header(
                label="Code Editor",
                divider=False,
            ),
        )

        control_stack.view(
            "preview_sample_distribution_btn",
            types.Button(
                label="View sample distribution",
                variant="outlined",
            ),
        )

        body_stack.view(
            "custom_code",
            default=self.get_code_example("dynamic_field_3"),
            view=types.CodeView(
                language="python",
                space=2,
                height=250,
                width="100%",
                componentsProps={
                    "editor": {
                        "width": "100%",
                        "options": {
                            "minimap": {"enabled": False},
                            "scrollBeyondLastLine": False,
                            "cursorBlinking": "phase",
                        },
                    },
                    "container": {
                        "width": "100%",
                    },
                },
            ),
        )

        if custom_code:
            _, error = self.process_custom_code(ctx, custom_code)
            if error:
                stack.view(
                    "custom_code_error",
                    view=types.AlertView(
                        severity="error",
                        label="Error in custom code",
                        description=error,
                    ),
                )
            else:
                store = ctx.store(STORE_NAME)
                scenario_name = ctx.params.get("scenario_name", "")
                if scenario_name:
                    # TODO: save this when "Analyze scenario" is clicked instead
                    pass

    def render_label_attribute(
        self, ctx, inputs, gt_field, chosen_scenario_label_attribute=None
    ):
        # TODO: refine the logic with bmoore/ritchie
        label_choices = types.Choices()

        schema = ctx.dataset.get_field_schema(flat=True)
        # bad_roots = tuple(
        #     k + "."
        #     for k, v in schema.items()
        #     if isinstance(v, fof.ListField)
        # )
        fields = [
            path
            for path, field in schema.items()
            if (
                (
                    isinstance(field, ALLOWED_BY_TYPES)
                    or (
                        isinstance(field, fof.ListField)
                        and isinstance(field.field, ALLOWED_BY_TYPES)
                    )
                )
                and path.startswith(f"{gt_field}.")
                # and not path.startswith(bad_roots)
            )
        ]

        # label_fields = ctx.dataset._get_label_fields()
        # for label_field in label_fields:
        # for label_field in fields:
        for label_path in fields:
            # _, label_path = ctx.dataset._get_label_field_path(label_field)
            label_choices.add_choice(label_path, label=label_path)

        inputs.enum(
            "scenario_label_attribute",
            label_choices.values(),
            default=None,
            label="Label attribute",
            description="Select a label attribute",
            view=label_choices,
            required=True,
        )

        if chosen_scenario_label_attribute is not None:
            counts = ctx.dataset.count_values(chosen_scenario_label_attribute)
            sorted_data = {k: v for k, v in sorted(counts.items())}

            obj = types.Object()
            for value, count in sorted_data.items():
                obj.bool(
                    value,
                    default=True,
                    label=f"{value} - {count}",
                    view=types.CheckboxView(space=3),
                )

            inputs.define_property("label_attribute_values", obj)

    def render_saved_views(self, ctx, inputs):
        view_names = ctx.dataset.list_saved_views()

        if view_names:
            sorted_view_names = sorted(view_names)
            obj = types.Object()

            for name in sorted_view_names:
                obj.bool(
                    name,
                    default=True,
                    label=name,
                    view=types.CheckboxView(space=3),
                )

            inputs.define_property("saved_views_values", obj)

    def render_sample_fields(
        self, ctx, inputs, chosen_scenario_field_name=None
    ):
        # TODO: check if we need flat=True
        all_fields = ctx.dataset.get_field_schema(flat=True)
        field_choices = types.Choices()

        for field_path, field in all_fields.items():
            if isinstance(field, ALLOWED_BY_TYPES):
                field_choices.add_choice(field_path, label=field_path)
            if isinstance(field, fof.ListField):
                if isinstance(field.field, ALLOWED_BY_TYPES):
                    field_choices.add_choice(field_path, label=field_path)

        inputs.str(
            "scenario_field",
            default=None,
            label="Field",
            description=("Choose applicable sample field values."),
            view=field_choices,
            required=True,
        )

        if chosen_scenario_field_name:
            chosen_scenario_field = ctx.dataset.get_field_schema(flat=True)[
                chosen_scenario_field_name
            ]

            if chosen_scenario_field is None:
                raise ValueError(
                    f"Field {chosen_scenario_field_name} does not exist"
                )

            values = ctx.dataset.distinct(chosen_scenario_field_name)

            # TODO: check the field type and show the custom code for continuous values or > 100 categories

            # for discrete values
            obj = types.Object()
            for value in values:
                obj.bool(
                    value,
                    default=True,
                    label=value,
                    view=types.CheckboxView(space=3),
                )

            inputs.define_property("sample_field_values", obj)

    def resolve_input(self, ctx):
        inputs = types.Object()
        self.render_header(inputs)

        # model name
        chosen_scenario_name = ctx.params.get("scenario_name", None)
        self.render_name_input(inputs, chosen_scenario_name)

        chosen_scenario_type = ctx.params.get("scenario_type", None)
        self.render_scenario_types(inputs, chosen_scenario_type)

        chosen_scenario_field_name = ctx.params.get("scenario_field", None)
        chosen_scenario_label_attribute = ctx.params.get(
            "scenario_label_attribute", None
        )
        chosen_custom_code = (
            ctx.params.get("custom_code_stack", {})
            .get("body_stack", {})
            .get("custom_code", "")
        )
        gt_field = ctx.params.get("gt_field", None)

        if chosen_scenario_type == "custom_code":
            self.render_custom_code(ctx, inputs, chosen_custom_code)

        if chosen_scenario_type == "label_attribute":
            self.render_label_attribute(
                ctx, inputs, gt_field, chosen_scenario_label_attribute
            )

        if chosen_scenario_type == "saved_views":
            self.render_saved_views(ctx, inputs)

        if chosen_scenario_type == "sample_field":
            self.render_sample_fields(ctx, inputs, chosen_scenario_field_name)

        prompt = types.PromptView(submit_button_label="Analyze scenario")
        return types.Property(inputs, view=prompt)

    def execute(self, ctx):
        return {
            "scenario_type": ctx.params.get("radio_choices", ""),
            "scenario_field": ctx.params.get("scenario_field", ""),
            "label_attribute": ctx.params.get("label_attribute", ""),
        }


def register(p):
    p.register(ConfigureScenario)
