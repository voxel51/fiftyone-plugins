import fiftyone.operators as foo
import fiftyone.operators.types as types


class SampleAuditingPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="sample_auditing_panel",
            label="Sample Auditing",
            icon="list",
            allow_multiple=False,
            surfaces="grid modal",
        )

    def on_load(self, ctx):
        pass

    def render(self, ctx):
        panel = types.Object()
        return types.Property(
            panel,
            view=types.View(
                component="SampleAuditingComponent",
                # composite_view=True,
            ),
        )
