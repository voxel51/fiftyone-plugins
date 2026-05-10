# @voxel51/management — Operator Reference

This plugin provides operators for managing FiftyOne Teams service accounts and their API keys. All operators require admin privileges. They are invoked from the FiftyOne App operator browser.

---

## Service Account Operators

### `create_service_account`

Creates a new service account in the organization.

**Inputs:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Display name for the service account |
| `role` | dropdown | yes | One of `MEMBER`, `COLLABORATOR`, `LABELER`, `GUEST`. Defaults to `MEMBER` |
| `description` | string | no | Optional free-text description |

**Output:** Toast notification confirming the name of the created account. No popup.

**What an agent should know:** Role controls what the service account can access across the organization — `MEMBER` is the standard starting point for automation accounts. The ID assigned to the new account is not shown in the notification; use `list_service_accounts` immediately after if the ID is needed for follow-up operations.

---

### `list_service_accounts`

Lists all service accounts in the organization.

**Inputs:** None.

**Output:** A popup table with columns `ID | Name | Role | Description` and a total count.

**What an agent should know:** Run this first to discover service account IDs before running any operator that targets a specific account. The ID column is the value used internally by all other operators — it is not shown in dropdowns (which display `name (ROLE)` instead), so listing first is the way to get the raw ID.

---

### `delete_service_account`

Permanently deletes a service account and all of its API keys.

**Inputs:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `service_account_id` | dropdown | yes | Shows all existing accounts as `name (ROLE)` |

**Output:** Toast notification. No popup.

**What an agent should know:** Deleting a service account also deletes every API key attached to it. Any running processes using those keys will immediately lose access. This is irreversible — the account and keys cannot be recovered, only recreated.

---

### `update_service_account`

Updates the name, role, or description of an existing service account.

**Inputs:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `service_account_id` | dropdown | yes | Shows all existing accounts as `name (ROLE)` |
| `name` | string | no | Pre-filled with the current name |
| `role` | dropdown | no | Pre-filled with the current role |
| `description` | string | no | Pre-filled with the current description |

**Output:** Toast notification. No popup.

**What an agent should know:** When an account is selected from the dropdown, the name/role/description fields automatically populate with that account's current values. The form will not allow submission until at least one field has been changed from its current value — if nothing differs, a blocking error appears and the submit button is disabled. Only the fields that actually changed are sent to the server; the rest are left untouched.

---

## API Key Operators

API keys are credentials attached to a specific service account. They grant programmatic access with that account's role. A key's raw value is only available at generation time — it cannot be retrieved later.

---

### `generate_service_account_api_key`

Generates a new API key for a service account.

**Inputs:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `service_account_id` | dropdown | yes | Shows all existing accounts as `name (ROLE)` |
| `key_name` | string | yes | A descriptive label for the key (e.g. `"ci-pipeline"`) |

**Output:** A popup displaying the raw API key string. The popup stays open until dismissed — it does not auto-close because the key cannot be retrieved again after the popup is closed.

**What an agent should know:** The key name is a human-readable label only — it has no effect on permissions or access. A service account can have multiple keys. If a key is lost before being copied, it must be deleted and a new one generated; there is no way to view the raw value of an existing key.

---

### `delete_service_account_api_key`

Deletes a specific API key from a service account.

**Inputs (two steps):**
| Field | Type | Required | Notes |
|---|---|---|---|
| `service_account_id` | dropdown | yes | Select the service account first |
| `key_id` | dropdown | yes | Appears only after an account is selected; shows that account's keys by name |

**Output:** Toast notification. No popup.

**What an agent should know:** The key dropdown does not appear until a service account is selected — this is intentional, since keys belong to a specific account. The dropdown shows keys by their human-readable name. Both the account and the key must be selected before the form can be submitted. Deletion is immediate and irreversible; any service using the deleted key loses access instantly.

---

### `list_service_account_api_keys`

Lists all API keys for a specific service account.

**Inputs:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `service_account_id` | dropdown | yes | Shows all existing accounts as `name (ROLE)` |

**Output:** A popup table with columns `ID | Name | Created At` and a total count.

**What an agent should know:** The raw key value is never shown here — only the key's ID, name, and creation date. Use this to audit what keys exist before deciding whether to rotate one. The ID shown in this table is what the system uses internally when deleting a key, though the delete operator exposes this through a name-labeled dropdown rather than requiring the ID directly.

---

## Common workflows

**Provision a new automation account:**
1. `create_service_account` — create with appropriate role
2. `list_service_accounts` — confirm it exists and note its ID if needed
3. `generate_service_account_api_key` — generate a key and copy it from the popup immediately

**Rotate a compromised or expired key:**
1. `list_service_account_api_keys` — identify which key needs rotation by name and creation date
2. `generate_service_account_api_key` — create the replacement key first and distribute it
3. `delete_service_account_api_key` — delete the old key once the replacement is confirmed working

**Change an account's access level:**
1. `update_service_account` — select the account, change the role field, submit
