import os
import glob

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


class AddSamples(foo.Operator):
  @property
  def config(self):
    return foo.OperatorConfig(
      name="add_samples",
      label="Add Samples",
      dynamic=True,
      execute_as_generator=True
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    style_choices = types.RadioGroup()
    style_choices.add_choice("entire_directory", label="Entire Directory")
    style_choices.add_choice("specific_files", label="Specific Files")

    inputs.enum("style", style_choices.values(), default="entire_directory", view=style_choices)
    cur_style = ctx.params.get("style", "entire_directory")

    if cur_style == "entire_directory":
      cur_directory = ctx.params.get("directory", os.environ["HOME"])
      directory_exists = os.path.isdir(cur_directory)
      directory_prop = inputs.str("directory",  required=True, default=os.environ["HOME"], label="Directory")

      # types.Property

      if not directory_exists:
        directory_prop.invalid = True
        directory_prop.error_message = "Directory does not exist"
    else:
      cur_file_pattern = ctx.params.get("files", None)
      matched_paths = 0
      try:
        matched_paths = len(glob.glob(cur_file_pattern))
      except:
        pass
      file_pattern_view = types.View(caption=f"Matched {matched_paths} files")
      inputs.str("files", required=True, default=os.environ["HOME"], label="File Pattern", view=file_pattern_view)

    return types.Property(inputs, view=types.View(label="Add Samples"))

  def execute(self, ctx):
    glob_pattern = None
    cur_style = ctx.params.get("style", "entire_directory")
    if cur_style == "entire_directory":
      dir = ctx.params.get("directory", os.environ["HOME"])
      glob_pattern = f"{dir}/*.*"
    else:
      glob_pattern = ctx.params.get("files", None)
    
    matched_paths = None
    try:
      matched_paths = glob.glob(glob_pattern)
    except:
      pass

    if len(matched_paths) > 0:
      for path in matched_paths:
        print(f"adding sample {path}")
        # TODO: add progress bar
        sample = fo.Sample(filepath=path)
        ctx.dataset.add_sample(sample)
      
      ctx.trigger("reload_dataset")
      
    return {"added_samples": len(matched_paths)}
  
  def resolve_output(self, ctx):
    outputs = types.Object()
    outputs.int("added_samples", required=True, default=0, label="Added Samples")
    return types.Property(outputs, view=types.View(label="Add Samples"))

def list_dirs(path, depth, current_depth=0):
    dirs = []
    
    if current_depth > depth:
        return dirs

    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                dirs.append(item_path)
                dirs.extend(list_dirs(item_path, depth, current_depth + 1))
    except PermissionError:
        pass

    return dirs


def register(p):
  p.register(AddSamples)

