"""
Index operators.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import eta.core.utils as etau

import fiftyone as fo
import fiftyone.core.media as fom
import fiftyone.operators as foo
import fiftyone.operators.types as types


class ManageIndexes(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_indexes",
            label="Manage indexes",
            light_icon="/assets/icon-light.svg",
            dark_icon="/assets/icon-dark.svg",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        _manage_indexes(ctx, inputs)

        view = types.View(label="Manage indexes")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        create = ctx.params.get("create", None) or []
        drop = ctx.params.get("drop", None) or []

        for obj in create:
            field_name = obj["field_name"]
            unique = obj["unique"]

            ctx.dataset.create_index(field_name, unique=unique, wait=False)

            if ctx.dataset.media_type == fom.GROUP:
                index_spec = [
                    (ctx.dataset.group_field + ".name", 1),
                    (field_name, 1),
                ]
                ctx.dataset.create_index(index_spec, unique=unique, wait=False)

        for obj in drop:
            index_name = obj["index_name"]
            ctx.dataset.drop_index(index_name)


def _manage_indexes(ctx, inputs):
    indexes = _get_existing_indexes(ctx)
    default_indexes = set(_get_default_indexes(ctx))
    supports_size = "size" in next(iter(indexes.values()), {})
    space = 2 if supports_size else 4

    inputs.str(
        "existing",
        view=types.Header(
            label="Existing indexes",
            description=(
                "This dataset currently has the following indexes. Note that "
                "you cannot delete default indexes."
            ),
            divider=True,
        ),
    )

    obj = types.Object()
    obj.str(
        "field_name",
        label="Field name",
        description="The field name or compound index name",
        view=types.MarkdownView(read_only=True, space=4),
    )
    obj.str(
        "default",
        label="Default",
        description="Whether the index is a default index",
        view=types.MarkdownView(read_only=True, space=space),
    )
    obj.str(
        "unique",
        label="Unique",
        description="Whether the index has a uniqueness constraint",
        view=types.MarkdownView(read_only=True, space=space),
    )
    if supports_size:
        obj.str(
            "size",
            label="Size",
            description="The size of the index",
            view=types.MarkdownView(read_only=True, space=4),
        )
    inputs.define_property("header", obj)

    for name in sorted(indexes):
        prop_name = name.replace(".", "_")  # prop names can't contain "."
        default = name in default_indexes
        unique = indexes[name].get("unique", False)
        if name in ("id", "frames.id"):
            # The `id` index is unique, but backend doesn't report it
            # https://github.com/voxel51/fiftyone/blob/cebfdbbc6dae4e327d2c3cfbab62a73f08f2d55c/fiftyone/core/collections.py#L8552
            unique = True

        index_info = indexes[name]
        size = (
            "In progress"
            if index_info.get("in_progress")
            else etau.to_human_bytes_str(index_info.get("size", 0))
        )

        obj = types.Object()
        obj.str(
            "field_name",
            default=name,
            view=types.MarkdownView(read_only=True, space=4),
        )
        obj.bool(
            "default",
            default=default,
            view=types.CheckboxView(read_only=True, space=space),
        )
        obj.bool(
            "unique",
            default=unique,
            view=types.CheckboxView(read_only=True, space=space),
        )
        if supports_size:
            obj.str(
                "size",
                default=size,
                view=types.MarkdownView(read_only=True, space=4),
            )
        inputs.define_property(prop_name, obj)

    inputs.list(
        "create",
        _create_index(ctx),
        label="Create indexes",
        description="New indexes to create",
    )
    inputs.list(
        "drop",
        _drop_index(ctx),
        label="Drop indexes",
        description="Existing indexes to drop",
    )

    label, has_action = _build_action_label(ctx)
    prop = inputs.view("confirmation", types.Notice(label=label))
    if not has_action:
        prop.invalid = True
        return False

    return True


def _build_action_label(ctx):
    create = [
        c
        for c in ctx.params.get("create", None) or []
        if c.get("field_name", None) is not None
    ]
    nc = len(create)

    drop = [
        d
        for d in ctx.params.get("drop", None) or []
        if d.get("index_name", None) is not None
    ]
    nd = len(drop)

    if nc > 0 and nd > 0:
        label = f"You are about to create {_istr(nc)} and drop {_istr(nd)}"
    elif nc > 0:
        label = f"You are about to create {_istr(nc)}"
    elif nd > 0:
        label = f"You are about to drop {_istr(nd)}"
    else:
        label = "You have not specified any indexes to create or drop"

    has_action = nc > 0 or nd > 0

    return label, has_action


def _istr(n):
    return f"{n} indexes" if n != 1 else "1 index"


def _get_existing_indexes(ctx):
    try:
        return ctx.dataset.get_index_information(include_stats=True)
    except TypeError:
        # `include_stats` is not supported by the backend
        return ctx.dataset.get_index_information()


def _create_index(ctx):
    obj = types.Object()

    choices = types.DropdownView(space=6)
    for path in _get_indexable_paths(ctx):
        choices.add_choice(path, label=path)

    obj.str(
        "field_name",
        required=True,
        label="Field name",
        description="The field to index",
        view=choices,
    )

    obj.bool(
        "unique",
        default=False,
        required=True,
        label="Unique",
        description="Whether to add a uniqueness constraint to the index",
        view=types.View(space=6),
    )

    return obj


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
    for obj in ctx.params.get("create", None) or []:
        paths.discard(obj.get("field_name", None))

    return sorted(paths)


def _get_index_name(ctx, field_name):
    if ctx.dataset.media_type == fom.GROUP:
        return f"{ctx.dataset.group_field}.name_1_{field_name}_1"

    return field_name


def _get_field_name(ctx, index_name):
    if ctx.dataset.media_type == fom.GROUP:
        prefix = f"{ctx.dataset.group_field}.name_1_"
        if index_name.startswith(prefix):
            # Extract $FIELD from "$GROUP_1_$FIELD_1"
            return index_name[len(prefix) : -2]
        else:
            return index_name

    return index_name


def _drop_index(ctx):
    index_names = _get_droppable_indexes(ctx)

    obj = types.Object()

    if index_names:
        choices = types.DropdownView()
        for name in index_names:
            choices.add_choice(name, label=name)

        obj.enum(
            "index_name",
            choices.values(),
            required=True,
            label="Index name",
            description="The index to drop",
            view=choices,
        )
    else:
        warning = types.Warning(label="There are no indexes to drop")
        prop = obj.view("warning", warning)
        prop.invalid = True

    return obj


def _get_droppable_indexes(ctx):
    index_names = set(ctx.dataset.list_indexes())
    index_names -= set(_get_default_indexes(ctx))
    return sorted(index_names)


def _get_default_indexes(ctx):
    index_names = ctx.dataset._get_default_indexes()
    if ctx.dataset._has_frame_fields():
        index_names.extend(
            "frames." + name
            for name in ctx.dataset._get_default_indexes(frames=True)
        )

    return index_names


def register(p):
    p.register(ManageIndexes)
