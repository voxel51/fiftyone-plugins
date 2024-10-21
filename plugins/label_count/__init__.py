from bson import ObjectId

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone import ViewField as F
import fiftyone.core.media as fom
import fiftyone.core.view as fov


class LabelCountPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="label_count_panel",
            label="Label Count",
            surfaces="modal",
            allow_multiple=True,
            reload_on_navigation=True,
        )

    def _iter_frames(self, ctx):
        current_sample = fov.make_optimized_select_view(
            ctx.view, ctx.current_sample
        ).first()
        if ctx.view.media_type == fom.VIDEO:
            for frame in current_sample.frames.values():
                yield frame

            return

        if (
            ctx.view.media_type == fom.GROUP
            and ctx.view._parent_media_type == fom.IMAGE
        ):
            for frame in ctx.dataset.match(
                F("_sample_id") == ObjectId(current_sample.sample_id)
            ):
                yield frame

            return

        raise ValueError("unexpected")

    def on_load(self, ctx):
        if not ctx.current_sample:
            ctx.panel.state.empty_state = (
                "Please select a valid numeric or list field."
            )
            return

        # Extract the selected field and its values
        sample_id = ctx.current_sample
        field = ctx.panel.state.selected_field
        if not field:
            ctx.panel.state.empty_state = (
                "Please select a valid field from the dropdown."
            )
            return

        # Get frame values for the selected field
        frames = list(self._iter_frames(ctx))
        frame_numbers, values = _get_frame_values(
            ctx.dataset, sample_id, field
        )

        # Set the plot state for rendering the bar plot
        ctx.panel.state.plot = {
            "type": "bar",
            "x": frame_numbers,
            "y": values,
            "title": field,
            "xaxis": "Frame Number",
            "yaxis": field,
            "hoverinfo": "x+y",
            "marker": {"color": ctx.panel.state.plot_color or "#ff6d04"},
            "selectedpoints": [],
            "hoverinfo": "x+y",
            "hovertemplate": (
                f"<b>Frame Number</b>: %{'{x}'}<br><b>{ctx.panel.state.selected_field}</b>: %{'{y}'}<extra></extra>"
            ),
        }
        self.load_range(ctx, (0, len(frames)))

    def render(self, ctx):
        valid_fields = _get_frame_paths(ctx.dataset)
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
                    label="Select a Field",
                    default=selected_field,
                    on_change=self.on_field_select,
                )
                panel.plot(
                    "plot",
                    height=100,
                    layout={
                        "title": {"text": selected_field},
                        "margin": {"t": 30},
                        "xaxis": {"title": "Frame Number"},
                        "yaxis": {"title": selected_field},
                    },
                )
        else:
            panel.md("No valid fields found in the dataset.")

        return types.Property(
            panel, view=types.GridView(height=100, width=100)
        )

    def on_field_select(self, ctx):
        field_name = ctx.params.get("value")
        ctx.panel.state.selected_field = field_name
        ctx.panel.set_title(f"{field_name} Plot")

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


def _get_frame_values(dataset, sample_id, path):
    view = dataset.select(sample_id)
    field = dataset.get_field("frames." + path)
    expr = "frames[]." + path
    if isinstance(field, fo.ListField):
        expr = F(expr).length()
    return view.values(["frames[].frame_number", expr])


def _get_frame_paths(dataset):
    schema = dataset.get_frame_field_schema(
        flat=True, ftype=(fo.FloatField, fo.IntField, fo.ListField)
    )
    if schema:
        return [
            path
            for path in schema
            if not any(path.startswith(p + ".") for p in schema)
        ]
    return []


def register(p):
    p.register(LabelCountPanel)
