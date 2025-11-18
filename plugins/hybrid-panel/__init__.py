"""
Hybrid Panel Plugin

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

# from .py.sample_auditing_panel import SampleAuditingPanel
import math
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone.operators.cache import execution_cache


class SampleAuditingPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="hybrid_counter_panel",
            label="Hybrid Counter Panel",
            icon="adjust",
            surfaces="grid modal",
        )

    def get_fibonacci_number_cacheable_key_fn(self, ctx):
        n = ctx.panel.get_state("count") or 0
        return ["fibonacci_number", n]

    @execution_cache(
        key_fn=get_fibonacci_number_cacheable_key_fn
    )  # Cache the Fibonacci calculation using ExecutionCache
    def get_fibonacci_number_cacheable(self, ctx):
        # Get the current count from panel state.
        # Note: We have fallback to 0 as state is only initialized after the panel is loaded when
        #  first launched. However, on reload of app, state is available immediately as it
        #  is persisted.
        n = ctx.panel.get_state("count") or 0
        return get_fibonacci_number(n)

    def store(self, ctx):
        # Create or retrieve an ExecutionStore for this panel.
        return ctx.store("hybrid_counter_panel")

    def on_load(self, ctx):
        count = ctx.panel.get_state("count")

        # If count is not yet set, retrieve saved count from store if exist
        if count is None:
            # Restore count from ExecutionStore
            store = self.store(ctx)
            saved_count = store.get("saved_count")
            count = saved_count

        # If saved count is not yet set, initialize to 0
        if count is None:
            count = 0

        # Set count as a state so it can be used in our React component.
        # Note: Only use `set_state` for small pieces of data that change frequently. For example,
        #  configuration for your Panel, UI state (current tab, etc), etc.
        ctx.panel.set_state("count", count)

        fibonacci_value = self.get_fibonacci_number_cacheable(ctx)
        # Set fibonacci value as data so it can be used in our React component.
        # Note: Use `set_data` for larger pieces of data that don't change frequently. For example,
        #  results of expensive computations, data fetched from external sources, etc. Panel data is
        #  not accessible in panel events such as `on_load`, `save_count` below, etc.
        ctx.panel.set_data("fibonacci", fibonacci_value)

    def save_count(self, ctx):
        count = ctx.panel.get_state("count")
        store = self.store(ctx)
        store.set("saved_count", count)
        ctx.ops.notify(
            f"Saved count has been updated to: {count}",
            variant="success",
        )

    def calculate_fibonacci_event(self, ctx):
        fibonacci_value = self.get_fibonacci_number_cacheable(ctx)
        ctx.panel.set_data("fibonacci", fibonacci_value)

    def render(self, ctx):
        panel = types.Object()
        return types.Property(
            panel,
            view=types.View(
                component="HybridCounterComponent",
                composite_view=True,
                save_count=self.save_count,
                calculate_fibonacci_event=self.calculate_fibonacci_event,
            ),
        )


def register(p):
    p.register(SampleAuditingPanel)


# Utilities


def is_fibonacci(n):
    if n < 0:
        return False

    def is_perfect_square(x):
        s = math.isqrt(x)
        return s * s == x

    return is_perfect_square(5 * n * n + 4) or is_perfect_square(5 * n * n - 4)


def get_fibonacci_number(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return get_fibonacci_number(n - 1) + get_fibonacci_number(n - 2)


def get_fibonacci_sequence(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]

    seq = [0, 1]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq
