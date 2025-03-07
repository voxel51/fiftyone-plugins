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


class ConfigureSubset(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="configure_subset",
            label="Configure subset",
            dynamic=True,
            # unlisted=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.view(
            "info_header",
            types.Header(label="Create subset", divider=True),
        )

        defaults = {
            "subset_name": "",
        }

        inputs.str(
            "subset_name",
            label="Subset name",
            default=defaults["subset_name"],
            view=types.TextFieldView(
                label="Subset name",
                placeholder="Enter a name for the subset",
            ),
            required=True,
        )

        inputs.view(
            "info_header_2",
            types.Header(
                label="Define subset",
                divider=False,
                description="The field that defines the subset you want to analyze",
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
            "custom_code", label="Custom code", description="Custom code"
        )

        inputs.enum(
            "subset_type",
            dropdown_choices.values(),
            label="subset_type",
            default=dropdown_choices.values()[0],
            view=types.DropdownView(),
        )

        chosen_subset_type = ctx.params.get("subset_type", None)
        chosen_subset_field_name = ctx.params.get("subset_field", None)
        chosen_label_attr = ctx.params.get("label_attribute", None)
        gt_field = ctx.params.get("gt_field", None)

        if chosen_subset_type == "label_attribute":
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

            print("fields", fields)

            # label_fields = ctx.dataset._get_label_fields()
            # for label_field in label_fields:
            # for label_field in fields:
            for label_path in fields:
                # _, label_path = ctx.dataset._get_label_field_path(label_field)
                label_choices.add_choice(label_path, label=label_path)

            inputs.enum(
                "label_attribute",
                label_choices.values(),
                default=None,
                label="Label attribute",
                description="Select a label attribute",
                view=label_choices,
                required=True,
            )

        if (
            chosen_subset_type == "label_attribute"
            and chosen_label_attr is not None
        ):
            counts = ctx.dataset.count_values(chosen_label_attr)
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

        if chosen_subset_type == "saved_views":
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

        if chosen_subset_type == "sample_field":
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
                "subset_field",
                default=None,
                label="Field",
                description=("Choose applicable sample field values."),
                view=field_choices,
                required=True,
            )

        if chosen_subset_type == "sample_field" and chosen_subset_field_name:
            chosen_subset_field = ctx.dataset.get_field_schema(flat=True)[
                chosen_subset_field_name
            ]

            if chosen_subset_field is None:
                raise ValueError(
                    f"Field {chosen_subset_field_name} does not exist"
                )

            values = ctx.dataset.distinct(chosen_subset_field_name)

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

            inputs.define_property("subset_sample_field_values", obj)

        prompt = types.PromptView(submit_button_label="Analyze subset")
        return types.Property(inputs, view=prompt)

    def execute(self, ctx):
        return {
            "subset_type": ctx.params.get("radio_choices", ""),
            "subset_field": ctx.params.get("subset_field", ""),
            "label_attribute": ctx.params.get("label_attribute", ""),
        }


def register(p):
    p.register(ConfigureSubset)
