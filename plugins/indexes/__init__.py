"""
Index operators.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


class ManageIndexes(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="manage_indexes",
            label="Manage indexes",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        manage_indexes(ctx, inputs)

        view = types.View(label="Manage indexes")
        return types.Property(inputs, view=view)

    def execute(self, ctx):
        create = ctx.params.get("create", [])
        drop = ctx.params.get("drop", [])

        """
        for obj in create:
            ctx.dataset.create_index(obj["field_name"], unique=obj["unique"])
            pass

        for obj in drop:
            ctx.dataset.drop_index(obj["index_name"])
            pass
        """

        return {"params": {"create": create, "drop": drop}}

    def resolve_output(self, ctx):
        outputs = types.Object()

        # @todo remove
        outputs.obj("params", label="params", view=types.JSONView())

        view = types.View(label="Request complete")
        return types.Property(outputs, view=view)


def manage_indexes(ctx, inputs):
    indexes = _get_existing_indexes(ctx)
    default_indexes = set(_get_default_indexes(ctx))

    inputs.str("existing", view=types.Header(label="Existing indexes"))
    for name in sorted(indexes):
        unique = indexes[name].get("unique", False)
        default = name in default_indexes

        obj = types.Object()

        choices = types.DropdownView(space=4, read_only=True)
        choices.add_choice(name, label=name)
        obj.str(
            "name",
            default=name,
            label="Index name",
            view=choices,
        )

        """
        obj.view(name, types.Notice(label=name, space=6, read_only=True))
        """

        """
        obj.str(
            "name",
            default=name,
            label="Index name",
            view=types.View(space=6, read_only=True),
        )
        """

        obj.bool(
            "unique",
            label="unique",
            description="Whether the index has a uniqueness constraint",
            default=unique,
            view=types.View(space=4, read_only=True),
        )

        obj.bool(
            "default",
            label="Default",
            description="Whether this is a default index",
            default=default,
            view=types.View(space=4, read_only=True),
        )

        inputs.define_property(name, obj, view=types.View(read_only=True))

    inputs.list(
        "create",
        create_index(ctx),
        default=[],
        label="Create indexes",
        description="New indexes to create",
    )

    inputs.list(
        "drop",
        drop_index(ctx),
        default=[],
        label="Drop indexes",
        description="Existing indexes to drop",
    )

    label, has_action = _build_action_label(ctx)
    prop = inputs.view("confirmation", types.Notice(label=label))
    if not has_action:
        prop.invalid = True


def _build_action_label(ctx):
    nc = len(ctx.params.get("create", []))
    nd = len(ctx.params.get("drop", []))

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
    return ctx.dataset.get_index_information()


def create_index(ctx):
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


def _get_indexable_paths(ctx):
    paths = set(
        path
        for path, field in ctx.view.get_field_schema(flat=True).items()
        if not isinstance(
            field, (fo.ListField, fo.DictField, fo.EmbeddedDocumentField)
        )
    )
    paths -= set(ctx.dataset.list_indexes())

    for obj in ctx.params.get("create", []):
        paths.discard(obj.get("field_name", None))

    return sorted(paths)


def drop_index(ctx):
    obj = types.Object()

    choices = types.DropdownView()
    for name in _get_droppable_indexes(ctx):
        choices.add_choice(name, label=name)

    obj.enum(
        "index_name",
        choices.values(),
        required=True,
        label="Index name",
        description="The index to drop",
        view=choices,
    )

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
