"""
Example metrics.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types


class EvaluationMetric(foo.Operator):
    def get_parameters(self, ctx, inputs):
        pass

    def parse_parameters(self, ctx, params):
        pass

    def compute(self, samples, eval_key, results, **kwargs):
        raise NotImplementedError("Subclass must implement compute()")

    def get_fields(self, samples, eval_key):
        return []

    def rename(self, samples, eval_key, new_eval_key):
        pass

    def cleanup(self, samples, eval_key):
        pass


class ExampleMetric(EvaluationMetric):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="example_metric",
            label="Example metric",
            description="This is an example metric",
            tags=["metric"],
        )

    def get_parameters(self, ctx, inputs):
        inputs.str(
            "value",
            label="Example parameter",
            description="This is an example metric parameter",
            default="foo",
            required=True,
        )

    def compute(self, samples, eval_key, results, value="foo"):
        dataset = samples._dataset
        metric_field = f"{eval_key}_example_metric"
        dataset.add_sample_field(metric_field, fo.StringField)
        samples.set_field(metric_field, value).save()
        return value

    def get_fields(self, samples, eval_key):
        metric_field = f"{eval_key}_example_metric"
        return [metric_field]

    def rename(self, samples, eval_key, new_eval_key):
        dataset = samples._dataset
        metric_field = f"{eval_key}_example_metric"
        new_metric_field = f"{new_eval_key}_example_metric"
        dataset.rename_sample_field(metric_field, new_metric_field)

    def cleanup(self, samples, eval_key):
        dataset = samples._dataset
        metric_field = f"{eval_key}_example_metric"
        dataset.delete_sample_field(metric_field, error_level=1)


def register(p):
    p.register(ExampleMetric)
