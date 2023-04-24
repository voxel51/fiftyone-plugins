import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo
import fiftyone.brain as fob
import fiftyone.zoo as foz

class ComputeVis(foo.DynamicOperator):
  def __init__(self):
    super().__init__(
      "compute_visualization",
      "Compute Visualization",
    )
  
  def resolve_input(self, ctx):
    inputs = types.Object()
    inputs.str("brain_key", label="Brain Key", description="A key for storing the results of the visualization.", required=True)
    inputs.int("max_samples", label="Max Samples", description="The maximum number of samples to use for the visualization.", required=True)
    inputs.enum("method", ["tsne", "umap", "pca"], label="Method", description="The method to use for computing the visualization.", required=True)
    inputs.enum("model", foz.list_zoo_models(), label="Model", description="The model to use for computing the visualization.", required=True)
    return types.Property(inputs)

  def execute(self, ctx):
    max_samples = ctx.params.get("max_samples", 100)
    method = ctx.params.get("method", "tsne")
    model = ctx.params.get("model", "resnet50-imagenet")
    brain_key = ctx.params.get("brain_key", None)
    results = fob.compute_visualization(ctx.dataset.limit(100), brain_key=brain_key, method="tsne")
    return {"results": results}

def register(p):
  p.register(ComputeVis)