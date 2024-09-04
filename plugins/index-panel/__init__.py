import psutil

import eta.core.utils as etau
import fiftyone as fo
import fiftyone.core.media as fom
import fiftyone.operators as foo
import fiftyone.core.odm as fod
from fiftyone.operators import types


_INDEXABLE_FIELDS = (
    fo.IntField,
    fo.ObjectIdField,
    fo.BooleanField,
    fo.DateField,
    fo.DateTimeField,
    fo.FloatField,
    fo.StringField,
    fo.ListField,
)


def _get_mongodb_memory_usage():
    # Function to get memory usage of MongoDB
    memory_usage = 0

    # Iterate over all processes
    for proc in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            # Check if process name is MongoDB
            if proc.info["name"] == "mongod":
                memory_info = proc.memory_info()
                memory_usage += memory_info.rss
                # RSS (Resident Set Size) - physical memory usage
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            pass

    if memory_usage > 0:
        # Convert memory usage to MB
        memory_usage = memory_usage / (1024**2)
        return f"{memory_usage:.2F} MB"
    else:
        return "N/A"


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
    # The `id` index is unique, but backend doesn't report it
    # https://github.com/voxel51/fiftyone/blob/cebfdbbc6dae4e327d2c3cfbab62a73f08f2d55c/fiftyone/core/collections.py#L8552
    return (
        True
        if name in ("id", "frames.id")
        else index_info.get("unique", False)
    )


def _get_droppable_indexes(ctx):
    index_names = set(ctx.dataset.list_indexes())
    index_names -= set(_get_default_indexes(ctx))
    return sorted(index_names)


def _get_indexable_paths(ctx):
    schema = ctx.view.get_field_schema(flat=True)
    if ctx.view._has_frame_fields():
        schema.update(
            {
                "frames." + k: v
                for k, v in ctx.view.get_frame_field_schema(flat=True).items()
            }
        )

    paths = set()
    for path, field in schema.items():
        # Skip non-leaf paths
        if any(p.startswith(path + ".") for p in schema.keys()):
            continue

        if isinstance(field, _INDEXABLE_FIELDS):
            paths.add(path)

    # Discard paths within dicts
    for path, field in schema.items():
        if isinstance(field, fo.DictField):
            for p in list(paths):
                if p.startswith(path + "."):
                    paths.discard(p)

    # Discard fields that are already indexed
    for index_name in ctx.dataset.list_indexes():
        paths.discard(index_name)

    # Discard fields that are already being newly indexed
    for obj in ctx.params.get("create", []):
        paths.discard(obj.get("field_name", None))

    return sorted(paths)


class IndexPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="index_panel",
            label="Index Management Panel",
            description="A simple panel allows users to create and drop"
            " indexes for the dataset.",
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
            rows.append(
                {
                    "Field Name": name,
                    "Size": str(size),
                    "Unique": str(unique),
                    "Default": str(default),
                }
            )

        rows = sorted(
            rows, key=lambda x: (x["Default"] == "False", x["Field Name"])
        )

        ctx.panel.state.table = rows

    def on_refresh_button_click(self, ctx):
        self._build_view(ctx)

    def on_load(self, ctx):
        self._build_view(ctx)

    def build_drop_index_view(self, ctx, dropdown):
        dropdown._choices = []
        indexes = _get_droppable_indexes(ctx)
        for index in indexes:
            dropdown.add_choice(
                index,
                label=index,
                description=f"Index {index}",
            )

    def drop_index(self, ctx):
        field_name = ctx.panel.get_state("drop_menu.dropdown")
        if field_name is None:
            ctx.ops.notify("Please select an index to drop", variant="error")
        else:
            index_name = field_name
            ctx.dataset.drop_index(index_name)
            msg = f"Index {index_name} has been dropped."
            ctx.ops.notify(msg, variant="success")
            self.refresh(ctx)

    def build_create_index_view(self, ctx, dropdown):
        dropdown._choices = []
        indexes = _get_indexable_paths(ctx)
        for index in indexes:
            dropdown.add_choice(
                index,
                label=index,
                description=f"Index {index}",
            )

    def refresh(self, ctx):
        self._build_view(ctx)

    def _create_index(self, ctx, name_or_spec, unique=False):
        try:
            ctx.dataset.create_index(name_or_spec, unique=unique, wait=False)
        except Exception as e:
            msg = str(e)
            if "wait" in msg:
                ctx.dataset.create_index(name_or_spec, unique=unique)

    def create_index(self, ctx):
        field_name = ctx.panel.get_state("create_menu.dropdown")
        if field_name is None:
            ctx.ops.notify(
                "Please select a field to create index.", variant="error"
            )
        else:
            unique = False
            self._create_index(ctx, field_name, unique=unique)

            if ctx.dataset.media_type == fom.GROUP:
                index_spec = [
                    (ctx.dataset.group_field + ".name", 1),
                    (field_name, 1),
                ]
                self._create_index(ctx, index_spec, unique=unique)

            ctx.ops.notify(f"Successfully created index {field_name}")
            self.refresh(ctx)

    def render(self, ctx):
        conn = fod.get_db_conn()
        db_info = conn.command("dbstats")

        data_size = etau.to_human_bytes_str(db_info["dataSize"])
        storage_size = etau.to_human_bytes_str(db_info["storageSize"])
        memory_usage = _get_mongodb_memory_usage()

        panel = types.Object()
        panel.md(
            "#### Index Management Panel \n"
            "\n"
            "This panel allows you to manage indexes for the dataset.\n"
            "___\n"
            f"MongoDB Data Size: {data_size} \n"
            "\n"
            f"MongoDB Storage Size: {storage_size}\n"
            "\n"
            f"MongoDB Memory Usage: {memory_usage} \n"
            "___\n"
            "Warning: index creation for large datasets might lead to an"
            " impact on database response time; please use your best"
            " judgement and/or contact your database admin or IT staffs if you"
            " have any question or concern.\n"
            "___\n"
        )
        table = types.TableView()
        table.add_column("Field Name", label="Field Name")
        table.add_column("Size", label="Size")
        table.add_column("Unique", label="Unique")
        table.add_column("Default", label="Default")

        panel.list(
            "table",
            types.Object(),
            view=table,
            label=f"Available indexes for dataset: {ctx.dataset.name}",
        )

        create_index_menu = panel.menu(
            "create_menu", variant="square", color="secondary"
        )
        create_index = types.DropdownView()
        self.build_create_index_view(ctx, create_index)

        create_index_menu.str(
            "dropdown",
            view=create_index,
            label="Create Index Menu"
        )
        create_index_menu.btn("add_btn", label="Create index", on_click=self.create_index, variant="contained")

        drop_index_menu = panel.menu(
            "drop_menu", variant="square", color="secondary"
        )
        drop_index = types.DropdownView()
        self.build_drop_index_view(ctx, drop_index)

        drop_index_menu.str(
            "dropdown",
            view=drop_index,
            label="Drop Index Menu",
        )

        drop_index_menu.btn("drop_btn", label="Drop index", on_click=self.drop_index, variant="contained")
        panel.btn(
            "refresh_btn",
            label="Refresh",
            on_click=self.on_refresh_button_click,
        )

        return types.Property(panel, view=types.ObjectView())


def register(p):
    p.register(IndexPanel)
