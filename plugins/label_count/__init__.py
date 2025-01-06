"""
Label count operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.core.media as fom
import fiftyone.core.view as fov
from fiftyone import ViewField as F


class LabelCountPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="label_count_panel",
            label="Label count",
            surfaces="modal",
            allow_multiple=True,
        )

    def on_load(self, ctx):
        field = ctx.panel.state.selected_field
        if not field:
            ctx.panel.state.empty_state = (
                "Please select a valid numeric or list field"
            )
            return

        frame_numbers, values = _get_values(ctx, field)

        ctx.panel.state.plot = {
            "type": "bar",
            "x": frame_numbers,
            "y": values,
            "title": field,
            "xaxis": "Frame number",
            "yaxis": field,
            "hoverinfo": "x+y",
            "marker": {"color": ctx.panel.state.plot_color or "#ff6d04"},
            "selectedpoints": [],
            "hoverinfo": "x+y",
            "hovertemplate": (
                f"<b>Frame number</b>: %{'{x}'}<br><b>{ctx.panel.state.selected_field}</b>: %{'{y}'}<extra></extra>"
            ),
        }
        self.load_range(ctx, (0, len(frame_numbers)))

    def render(self, ctx):
        valid_fields = _get_fields(ctx)
        if not ctx.panel.state.selected_field:
            empty_state = types.Object()
            empty_state.enum(
                "field_selector",
                valid_fields,
                label="Select a field to display",
                on_change=self.on_field_select,
            )
            return types.Property(
                empty_state,
                view=types.GridView(
                    align_x="center",
                    align_y="center",
                    orientation="vertical",
                    height=100,
                ),
            )

        panel = types.Object()

        if len(valid_fields):
            selected_field = ctx.panel.state.get(
                "selected_field", valid_fields[0]
            )
            panel.obj(
                "frame_data",
                view=types.FrameLoaderView(
                    on_load_range=self.on_load_range,
                    target="plot.selectedpoints",
                ),
            )
            if selected_field:
                menu = panel.menu("menu", overlay="top-left")
                menu.enum(
                    "field_selector",
                    valid_fields,
                    label="Select a field",
                    default=selected_field,
                    on_change=self.on_field_select,
                )
                panel.plot(
                    "plot",
                    height=100,
                    layout={
                        "title": {"text": selected_field},
                        "margin": {"t": 30},
                        "xaxis": {"title": "Frame number"},
                        "yaxis": {"title": selected_field},
                    },
                )
        else:
            panel.md("There are no compatible fields to display")

        return types.Property(
            panel, view=types.GridView(height=100, width=100)
        )

    def on_field_select(self, ctx):
        field_name = ctx.params.get("value")
        ctx.panel.state.selected_field = field_name
        ctx.panel.set_title(f"{field_name} plot")

        self.on_load(ctx)

    def on_change_current_sample(self, ctx):
        self.on_load(ctx)

    def load_range(self, ctx, range_to_load):
        r = range_to_load

        chunk = {}
        for i in range(r[0], r[1]):
            rendered_frame = self.render_frame(i)
            chunk[f"frame_data.frames[{i}]"] = rendered_frame

        ctx.panel.set_data(chunk)
        current_field = ctx.panel.state.selected_field or "default_field"
        ctx.panel.set_state("frame_data.signature", current_field + str(r))

    def on_load_range(self, ctx):
        r = ctx.params.get("range")
        self.load_range(ctx, r)

    def render_frame(self, frame):
        return [frame - 1]


def _get_fields(ctx):
    if ctx.view._is_dynamic_groups:
        schema_fcn = ctx.view.get_field_schema
    else:
        schema_fcn = ctx.view.get_frame_field_schema

    schema = schema_fcn(
        flat=True, ftype=(fo.FloatField, fo.IntField, fo.ListField)
    )
    if not schema:
        return []

    return [
        path
        for path in schema
        if not any(path.startswith(p + ".") for p in schema)
    ]


def _get_values(ctx, path):
    if ctx.view._is_dynamic_groups:
        sample_id = ctx.view._base_view[ctx.current_sample].sample_id
        field = ctx.view.get_field(path)
        expr = path
        if isinstance(field, fo.ListField):
            expr = F(expr).length()
        view = ctx.view.get_dynamic_group(sample_id)
        return view.values(["frame_number", expr])
    else:
        sample_id = ctx.current_sample
        field = ctx.view.get_field("frames." + path)
        expr = "frames[]." + path
        if isinstance(field, fo.ListField):
            expr = F(expr).length()
        view = fov.make_optimized_select_view(ctx.view, [sample_id])
        return view.values(["frames[].frame_number", expr])


def register(p):
    p.register(LabelCountPanel)
