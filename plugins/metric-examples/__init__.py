"""
Example metrics.

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import numpy as np


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
        dataset = samples._dataset
        for metric_field in self.get_fields(samples, eval_key):
            new_metric_field = metric_field.replace(eval_key, new_eval_key, 1)
            dataset.rename_sample_field(metric_field, new_metric_field)

    def cleanup(self, samples, eval_key):
        dataset = samples._dataset
        for metric_field in self.get_fields(samples, eval_key):
            dataset.delete_sample_field(metric_field, error_level=1)


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
        metric_field = f"{eval_key}_{self.config.name}"
        dataset.add_sample_field(metric_field, fo.StringField)
        samples.set_field(metric_field, value).save()

        return value

    def get_fields(self, samples, eval_key):
        expected_fields = [f"{eval_key}_{self.config.name}"]
        return list(filter(samples.has_field, expected_fields))


class AbsoluteErrorMetric(EvaluationMetric):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="absolute_error",
            label="Absolute Error Metric",
            description="A metric for absolute error.",
            tags=["metric"],
        )

    def compute(self, samples, eval_key, results):
        def _safe_mean(values):
            values = [v for v in values if v is not None]
            return np.mean(values) if values else None

        def _abs_error(ypred, ytrue):
            return abs(ypred - ytrue)

        dataset = samples._dataset
        is_video = dataset._is_frame_field(results.config.gt_field)
        frame_errors = None
        if is_video:
            frame_errors = [
                list(map(_abs_error, yp, yt))
                for yp, yt in zip(results.ypred, results.ytrue)
            ]
            sample_errors = [_safe_mean(e) for e in frame_errors]
        else:
            sample_errors = list(map(_abs_error, results.ypred, results.ytrue))

        metric_field = f"{eval_key}_{self.config.name}"
        if is_video:
            # Sample-level errors
            dataset.set_values(metric_field, sample_errors)

            # Per-frame errors
            dataset.set_values(
                dataset._FRAMES_PREFIX + metric_field, frame_errors
            )
        else:
            # Per-sample errors
            dataset.set_values(metric_field, sample_errors)

    def get_fields(self, samples, eval_key):
        metric_field = f"{eval_key}_{self.config.name}"
        expected_fields = [metric_field, samples._FRAMES_PREFIX + metric_field]
        return list(filter(samples.has_field, expected_fields))


class MeanAbsoluteErrorMetric(EvaluationMetric):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="mean_absolute_error",
            label="Mean Absolute Error Metric",
            description="A metric for mean absolute error.",
            tags=["metric"],
        )

    def get_parameters(self, ctx, inputs):
        eval_key = ctx.params.get("eval_key", None)
        inputs.str(
            "sample_eval_key",
            label="Sample eval key parameter",
            description="Sample eval key for Mean Absolute Error",
            default=f"{eval_key}_absolute_error",
            required=True,
        )

    def compute(self, samples, eval_key, results, sample_eval_key=None):
        dataset = samples._dataset
        if not (sample_eval_key or dataset.has_field(sample_eval_key)):
            return None
        values = dataset.values(sample_eval_key)
        return np.average(values).tolist()


def register(p):
    p.register(ExampleMetric)
    p.register(AbsoluteErrorMetric)
    p.register(MeanAbsoluteErrorMetric)
