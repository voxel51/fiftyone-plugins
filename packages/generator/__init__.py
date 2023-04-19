import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone.plugins import list_all_plugins

class Generator(foo.DynamicOperator):
  def __init__(self):
    super().__init__(
      "manage_plugins",
      "Manage Plugins",
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    actions = types.RadioGroup(label="Choose an Action")
    actions.add_choice("install", label="Install a Plugin")
    actions.add_choice("create", label="Create a new Plugin")
    actions.add_choice("add", label="Add to an existing Plugin")
    inputs.enum("action", actions.values(), view=actions, required=True)
    choices = types.Choices(label="Type", description="Choose the type of artifact to generate", space=6)
    cur_action = ctx.params.get("action", None)
    is_install = cur_action == "install"
    is_create = cur_action == "create"
    is_add = cur_action == "add"
    cur_lang = ctx.params.get("lang", None)
    if is_create or is_add:
      langs = types.RadioGroup(label="Language", space=3)
      langs.add_choice("javascript", label="JavaScript")
      langs.add_choice("python", label="Python")
      choices = types.Choices(label="Type", description="Choose the type of artifact to generate", space=6)
      inputs.enum("lang", langs.values(), view=langs, required=True)
      choices.add_choice("operator", label="Operator")
      if is_add and cur_lang == "javascript":
        choices.add_choice("view", label="View")
        choices.add_choice("panel", label="Panel")
        choices.add_choice("visualizer", label="Visualizer")
        choices.add_choice("component", label="Component")
      if is_add:
        inputs.enum("type", choices.values(), view=choices, required=True)
    if is_create and cur_lang is not None:
      inputs.str("org_name", label="Organization", view=types.View(space=6))
      inputs.str("name", label="Name", required=True, view=types.View(space=6))
      inputs.str("description", label="Description")
    elif is_add and cur_lang is not None:
      all_plugins = list_all_plugins()
      plugins = types.Choices()
      for plugin_name in all_plugins.get(cur_lang, []):
        plugins.add_choice(plugin_name, label=plugin_name)
      inputs.enum("plugin", plugins.values(), label="Plugin", description="Choose a plugin", view=plugins, required=True)
      if ctx.params.get("type", None) == "operator":
        inputs.str("op_name", label="Operator Name", required=True, view=types.View(space=6))
        inputs.str("op_description", label="Operator Description", view=types.View(space=6))
    elif is_install:
      inputs.str("url", label="Github URL", required=True)
    view = types.View(label="Manage Plugins")
    return types.Property(inputs, view=view)

  def execute(self, ctx):
    src = ctx.params.get("type", None)


op = None

def register():
  op = Generator()
  foo.register_operator(op)

def unregister():
  foo.unregister_operator(op)
