"""
FiftyOne Teams management operators.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import fiftyone.management as fom
import fiftyone.operators as foo
import fiftyone.operators.types as types


_ROLES = ["MEMBER", "COLLABORATOR", "LABELER", "GUEST"]


def _service_account_dropdown(inputs, field_name, label):
    accounts = fom.list_service_accounts()
    dropdown = types.Dropdown(label=label)
    for sa in accounts:
        dropdown.add_choice(sa.id, label=f"{sa.name} ({sa.role.value})")
    inputs.enum(
        field_name,
        [sa.id for sa in accounts],
        label=label,
        required=True,
        view=dropdown,
    )


def _api_key_dropdown(inputs, sa_id, field_name, label):
    api_keys = fom.list_api_keys(user=sa_id)
    dropdown = types.Dropdown(label=label)
    for key in api_keys:
        dropdown.add_choice(key.id, label=key.name)
    inputs.enum(
        field_name,
        [key.id for key in api_keys],
        label=label,
        required=True,
        view=dropdown,
    )


class CreateServiceAccount(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="create_service_account",
            label="Create service account",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("name", label="Name", required=True)

        role_dropdown = types.Dropdown(label="Role")
        for role in _ROLES:
            role_dropdown.add_choice(role, label=role.capitalize())
        inputs.enum(
            "role",
            _ROLES,
            label="Role",
            required=True,
            default="MEMBER",
            view=role_dropdown,
        )

        inputs.str("description", label="Description", required=False)

        return types.Property(inputs, view=types.View(label="Create service account"))

    def execute(self, ctx):
        sa = fom.create_service_account(
            name=ctx.params["name"],
            role=ctx.params.get("role", "MEMBER"),
            description=ctx.params.get("description") or None,
        )
        ctx.ops.notify(f"Service account '{sa.name}' created.")


class ListServiceAccounts(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="list_service_accounts",
            label="List service accounts",
        )

    def execute(self, ctx):
        accounts = fom.list_service_accounts()

        if accounts:
            rows = [
                f"| {sa.id} | {sa.name} | {sa.role.value} "
                f"| {sa.description or ''} |"
                for sa in accounts
            ]
            table = (
                "| ID | Name | Role | Description |\n"
                "|---|---|---|---|\n"
                + "\n".join(rows)
            )
        else:
            table = "_No service accounts found._"

        return {"count": len(accounts), "markdown": table}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.int("count", label="Total")
        outputs.str("markdown", label="Service accounts", view=types.MarkdownView())
        return types.Property(outputs, view=types.View(label="Service accounts"))


class DeleteServiceAccount(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_service_account",
            label="Delete service account",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.view(
            "warning",
            types.Warning(
                label="Irreversible action",
                description=(
                    "The service account and all its API keys will be "
                    "permanently deleted and cannot be recovered."
                ),
            ),
        )
        _service_account_dropdown(inputs, "service_account_id", "Service account")
        return types.Property(inputs, view=types.View(label="Delete service account"))

    def execute(self, ctx):
        sa_id = ctx.params["service_account_id"]
        fom.delete_service_account(sa_id)
        ctx.ops.notify("Service account deleted.")


class UpdateServiceAccount(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="update_service_account",
            label="Update service account",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        _service_account_dropdown(inputs, "service_account_id", "Service account")

        sa_id = ctx.params.get("service_account_id")
        current = fom.get_service_account(sa_id) if sa_id else None

        inputs.str(
            "name",
            label="Name",
            required=False,
            default=current.name if current else None,
        )

        role_dropdown = types.Dropdown(label="Role")
        for role in _ROLES:
            role_dropdown.add_choice(role, label=role.capitalize())
        inputs.enum(
            "role",
            _ROLES,
            label="Role",
            required=False,
            default=current.role.value if current else None,
            view=role_dropdown,
        )

        inputs.str(
            "description",
            label="Description",
            required=False,
            default=current.description if current else None,
        )

        # Validate once the form has fully rendered (name will be present in
        # params after the first dynamic re-render with defaults applied)
        if current and ctx.params.get("name") is not None:
            name_changed = ctx.params.get("name") != current.name
            role_changed = ctx.params.get("role") != current.role.value
            desc_changed = (ctx.params.get("description") or None) != current.description
            if not (name_changed or role_changed or desc_changed):
                inputs.view(
                    "no_changes_error",
                    types.Error(
                        label="No changes",
                        description="Modify at least one field before submitting.",
                    ),
                )

        return types.Property(inputs, view=types.View(label="Update service account"))

    def execute(self, ctx):
        sa_id = ctx.params["service_account_id"]
        current = fom.get_service_account(sa_id)

        new_name = ctx.params.get("name") or None
        new_role = ctx.params.get("role") or None
        new_description = ctx.params.get("description") or None

        sa = fom.update_service_account(
            service_account=sa_id,
            name=new_name if new_name != current.name else None,
            role=new_role if new_role != current.role.value else None,
            description=new_description if new_description != current.description else None,
        )
        ctx.ops.notify(f"Service account '{sa.name}' updated.")


class GenerateServiceAccountApiKey(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="generate_service_account_api_key",
            label="Generate service account API key",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        _service_account_dropdown(inputs, "service_account_id", "Service account")
        inputs.str("key_name", label="Key name", required=True)
        inputs.view(
            "warning",
            types.Warning(
                label="Key shown once",
                description=(
                    "The generated API key will only be displayed once and "
                    "cannot be recovered. Copy it immediately after generation."
                ),
            ),
        )
        return types.Property(inputs, view=types.View(label="Generate API key"))

    def execute(self, ctx):
        key = fom.generate_api_key(
            key_name=ctx.params["key_name"],
            user=ctx.params["service_account_id"],
        )
        return {"api_key": key}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "api_key",
            label="API Key — copy now, cannot be recovered",
            view=types.CodeView(language="text"),
        )
        return types.Property(outputs, view=types.View(label="API key generated"))


class DeleteServiceAccountApiKey(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="delete_service_account_api_key",
            label="Delete service account API key",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.view(
            "warning",
            types.Warning(
                label="Irreversible action",
                description=(
                    "The API key will be permanently deleted. Any services "
                    "using it will immediately lose access."
                ),
            ),
        )
        _service_account_dropdown(inputs, "service_account_id", "Service account")

        sa_id = ctx.params.get("service_account_id")
        if sa_id:
            _api_key_dropdown(inputs, sa_id, "key_id", "API key")

        return types.Property(inputs, view=types.View(label="Delete API key"))

    def execute(self, ctx):
        fom.delete_api_key(ctx.params["key_id"], user=ctx.params["service_account_id"])
        ctx.ops.notify("API key deleted.")


class ListServiceAccountApiKeys(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="list_service_account_api_keys",
            label="List service account API keys",
            dynamic=True,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        _service_account_dropdown(inputs, "service_account_id", "Service account")
        return types.Property(inputs, view=types.View(label="List API keys"))

    def execute(self, ctx):
        api_keys = fom.list_api_keys(user=ctx.params["service_account_id"])

        if api_keys:
            rows = [
                f"| {key.id} | {key.name} | {key.created_at} |"
                for key in api_keys
            ]
            table = (
                "| ID | Name | Created At |\n"
                "|---|---|---|\n"
                + "\n".join(rows)
            )
        else:
            table = "_No API keys found for this service account._"

        return {"count": len(api_keys), "markdown": table}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.int("count", label="Total")
        outputs.str("markdown", label="API keys", view=types.MarkdownView())
        return types.Property(outputs, view=types.View(label="API keys"))


def register(p):
    p.register(CreateServiceAccount)
    p.register(ListServiceAccounts)
    p.register(DeleteServiceAccount)
    p.register(UpdateServiceAccount)
    p.register(GenerateServiceAccountApiKey)
    p.register(DeleteServiceAccountApiKey)
    p.register(ListServiceAccountApiKeys)
