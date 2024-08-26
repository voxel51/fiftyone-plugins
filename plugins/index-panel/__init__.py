import eta.core.utils as etau
import fiftyone as fo
import fiftyone.operators as foo
from fiftyone.operators import types


def _get_existing_indexes(ctx):
    return ctx.dataset.get_index_information(include_stats=True)


def _get_default_indexes(ctx):
    index_names = ctx.dataset._get_default_indexes()
    if ctx.dataset._has_frame_fields():
        index_names.extend(
            "frames." + name
            for name in ctx.dataset._get_default_indexes(frames=True)
        )

    return index_names


def _is_unique(name, index_info):
    if name in ("id", "frames.id"):
        # The `id` index is unique, but backend doesn't report it
        # https://github.com/voxel51/fiftyone/blob/cebfdbbc6dae4e327d2c3cfbab62a73f08f2d55c/fiftyone/core/collections.py#L8552
        return True
    return index_info.get("unique", False)


class IndexPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="index_panel",
            label="Index Panel",
            description="A simple panel manages index",
            help_markdown="My plugin",
            surfaces="grid",
            icon="/assets/icon-light.svg",
            light_icon="/assets/icon-light.svg",  # light theme only
            dark_icon="/assets/icon-dark.svg",  # dark theme only
            allow_multiple=False,
        )

    def _build_view(self, ctx):
        indexes = _get_existing_indexes(ctx)
        default_indexes = set(_get_default_indexes(ctx))
        rows = []
        for name in sorted(indexes):
            index_info = indexes[name]
            default = name in default_indexes
            unique = _is_unique(name, index_info)
            size = (
                "In progress"
                if index_info.get("in_progress")
                else etau.to_human_bytes_str(index_info.get("size", 0))
            )
            rows.append({
                "Field Name": name,
                "Size": str(size),
                "Unique": str(unique),
                "Default": str(default),
            })

        ctx.panel.state.table = rows

    def on_button_click(self, ctx):
        self._build_view(ctx)

    def on_load(self, ctx):
        self._build_view(ctx)

    def render(self, ctx):
        panel = types.Object()
        panel.md("#### Index panel")
        table = types.TableView()
        table.add_column("Field Name", label="Field name")
        table.add_column("Size", label="Size")
        table.add_column("Unique", label="Unique")
        table.add_column("Default", label="Default")

        panel.list("table", types.Object(), view=table, label=f"Available index for dataset: {ctx.dataset.name}")
        panel.btn("click_me", label="Refresh", on_click=self.on_button_click)

        return types.Property(panel, view=types.ObjectView())


def register(p):
    p.register(IndexPanel)
