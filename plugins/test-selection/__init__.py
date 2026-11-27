import fiftyone.operators as foo
import fiftyone.operators.types as types


class DebugSelection(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="debug_selection",
            label="Debug Selection",
        )

    def execute(self, ctx):
        print("=== Selection Debug ===")
        print("selected:", ctx.selected)
        print("selected_meta:", ctx.selected_meta)
        print("selection_style:", ctx.selection_style)
        print("=======================")
        return {
            "selected": ctx.selected,
            "selected_meta": ctx.selected_meta,
            "selection_style": ctx.selection_style,
        }


class TestSetSelectedWithMeta(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="test_set_selected_with_meta",
            label="Test: Set Selected With Meta",
        )

    def execute(self, ctx):
        ids = ctx.dataset.limit(3).values("id")
        meta = {
            ids[0]: {"type": "default"},
            ids[1]: {"type": "alt"},
            ids[2]: {"type": "alt"},
        }
        ctx.ops.set_selected_samples(ids, meta=meta)
        print("Set selected with meta:", meta)


class TestSetSelectionStyle(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="test_set_selection_style",
            label="Test: Set Selection Style (thumbsup/thumbsdown)",
        )

    def execute(self, ctx):
        ctx.ops.set_selection_style(default="thumbsup", alt="thumbsdown")
        print("Set selection style: thumbsup / thumbsdown")


class TestClearSelectionStyle(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="test_clear_selection_style",
            label="Test: Clear Selection Style",
        )

    def execute(self, ctx):
        ctx.ops.clear_selection_style()
        print("Cleared selection style")


def register(plugin):
    plugin.register(DebugSelection)
    plugin.register(TestSetSelectedWithMeta)
    plugin.register(TestSetSelectionStyle)
    plugin.register(TestClearSelectionStyle)
