"""
Dashboard plugin.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

from enum import Enum
import random
from textwrap import dedent

import numpy as np

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone import ViewField as F
import fiftyone.core.fields as fof


STORE_NAME = "scenarios"


class PlotlyPlotType(Enum):
    BAR = "bar"
    SCATTER = "scatter"
    LINE = "line"
    PIE = "pie"


class PlotType(Enum):
    CATEGORICAL_HISTOGRAM = "categorical_histogram"
    NUMERIC_HISTOGRAM = "numeric_histogram"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"


NUMERIC_TYPES = (fo.IntField, fo.FloatField, fo.DateTimeField, fo.DateField)
CATEGORICAL_TYPES = (fo.StringField, fo.BooleanField)
REQUIRES_X = [PlotType.SCATTER, PlotType.LINE, PlotType.NUMERIC_HISTOGRAM]
REQUIRES_Y = [PlotType.SCATTER, PlotType.LINE]

MAX_CATEGORIES = 100
ALLOWED_BY_TYPES = (
    fof.StringField,
    fof.BooleanField,
    fof.IntField,
    fof.FloatField,
)


class ConfigureScenario(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="configure_scenario",
            label="Configure scenario",
            dynamic=True,
            # unlisted=True,
        )

    # def on_load(self, ctx):
    #     print("asdasdasd")
    #     ctx.panel.state.scenarios = []
    #     store = ctx.store("scenarios")

    #     # store_values = store.get("user_choice")
    #     store.set("my_key", {"foo": "bar"}, ttl=60)
    #     print("asdasdasd", store.list_keys())  # ["user_choice", "my_key"]

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
            view=types.TextFieldView(
                label="Scenario Name",
                placeholder="Enter a name for the scenario",
            ),
        )

    def render_scenario_type(self, inputs):
        inputs.view(
            "info_header_2",
            types.Header(
                label="Define scenario",
                divider=False,
                description="The field that defines the scenario you want to analyze",
            ),
        )

        dropdown_choices = types.RadioGroup()

        dropdown_choices.add_choice(
            "sample_field",
            label="Select sample fields",
            description="Select sample fields",
        )
        dropdown_choices.add_choice(
            "label_attribute",
            label="Select label attributes",
            description="Select sample fields",
        )
        dropdown_choices.add_choice(
            "saved_views",
            label="Select saved views",
            description="Select label attribute",
        )
        dropdown_choices.add_choice(
            "custom_code",
            label="Custom code",
            description="Custom code",
        )

        inputs.enum(
            "scenario_type",
            dropdown_choices.values(),
            label="scenario_type",
            default=dropdown_choices.values()[-1],
            view=types.DropdownView(),
        )

    def execute_custom_code(self, ctx, custom_code):
        try:
            local_vars = {}
            exec(custom_code, {"ctx": ctx}, local_vars)
            data = local_vars.get("subsets", {})
            return data, None
        except Exception as e:
            return None, str(e)

    def render_custom_code(self, ctx, inputs, custom_code=None):
        inputs.view(
            "info_header_3",
            types.Header(
                label="Custom code",
                divider=False,
                description="Write custom code to define scenario",
            ),
        )
        inputs.view(
            "custom_code",
            label="Code editor",
            default=self.get_code_example("dynamic_field_2"),
            view=types.CodeView(
                language="python",
                space=6,
                height=150,
                componentsProps={
                    "editor": {
                        "minWidth": "520px",
                        "width": "520px",
                        "flex-grow": 1,
                    },
                },
            ),
        )

        if custom_code is not None:
            # NOTE: data is the scenario expression in mongo syntax
            data, error = self.execute_custom_code(ctx, custom_code)
            if error:
                # TODO: we have the line number in the error usually. ex: (line 4)
                # - get the line from error
                # - highlight the line in the editor
                # - look at monaco.editor.setModelMarkers(editor.getModel()!, "owner", [
                #   {
                #     startLineNumber: 3,
                #     endLineNumber: 3,
                #     startColumn: 1,
                #     endColumn: 100,
                #     message: "Syntax Error: Something is wrong here.",
                #     severity: monaco.MarkerSeverity.Error,
                #   },
                # ]);
                inputs.view(
                    "custom_code_error",
                    view=types.AlertView(
                        severity="error",
                        label="Error in custom code",
                        description=error,
                    ),
                )
            else:
                # TODO: save this when "Analyze scenario" is clicked instead
                store = ctx.store(STORE_NAME)
                scenario_name = ctx.params.get("scenario_name", "")
                if scenario_name:
                    store.set(scenario_name, custom_code)

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

            # TODO: check field type and for continuous values show custom code

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

        defaults = {
            "scenario_name": "",
        }

        # model name
        self.render_name_input(inputs, defaults["scenario_name"])

        # scenario type selection TODO: needs a new component
        self.render_scenario_type(inputs)

        chosen_scenario_type = ctx.params.get("scenario_type", None)
        chosen_scenario_field_name = ctx.params.get("scenario_field", None)
        chosen_scenario_label_attribute = ctx.params.get(
            "scenario_label_attribute", None
        )
        chosen_custom_code = ctx.params.get("custom_code", None)
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
        print("executing", ctx.params)

        return {
            "scenario_type": ctx.params.get("radio_choices", ""),
            "scenario_field": ctx.params.get("scenario_field", ""),
            "label_attribute": ctx.params.get("label_attribute", ""),
        }


def register(p):
    p.register(ConfigureScenario)
