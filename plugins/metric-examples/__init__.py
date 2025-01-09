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


class EvaluationMetricConfig(foo.OperatorConfig):
    def __init__(
        self,
        name,
        label,
        description,
        tags,
        is_aggregate=False,
    ):
        super().__init__(name, label, description, tags)
        self.is_aggregate = is_aggregate


class EvaluationMetric(foo.Operator):
    @property
    def is_aggregate(self):
        return self.config.is_aggregate

    def get_parameters(self, ctx, inputs):
        pass

    def parse_parameters(self, ctx, params):
        pass

    def compute(self, samples, eval_key, results, **kwargs):
        raise NotImplementedError("Subclass must implement compute()")

    def get_fields(self, samples, eval_key):
        metric_field = f"{eval_key}_{self.config.name}"
        return [metric_field]

    def rename(self, samples, eval_key, new_eval_key):
        dataset = samples._dataset
        metric_field = f"{eval_key}_{self.config.name}"
        new_metric_field = f"{new_eval_key}_{self.config.name}"
        dataset.rename_sample_field(metric_field, new_metric_field)

    def cleanup(self, samples, eval_key):
        dataset = samples._dataset
        metric_field = f"{eval_key}_{self.config.name}"
        dataset.delete_sample_field(metric_field, error_level=1)


class ExampleMetric(EvaluationMetric):
    @property
    def config(self):
        return EvaluationMetricConfig(
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


class AbsoluteErrorMetric(EvaluationMetric):
    @property
    def config(self):
        return EvaluationMetricConfig(
            name="absolute_error",
            label="Absolute Error Metric",
            description="A metric for absolute error.",
            is_aggregate=False,
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

        if eval_key:
            metric_field = (
                f"{eval_key}_{self.config.name}"
                if eval_key
                else self.config.name
            )
            if is_video:
                eval_frame = dataset._FRAMES_PREFIX + eval_key

                # Sample-level errors
                dataset.set_values(sample_errors)

                # Per-frame errors
                dataset.set_values(eval_frame, frame_errors)
            else:
                # Per-sample errors
                dataset.set_values(metric_field, sample_errors)

        return sample_errors


class MeanAbsoluteErrorMetric(EvaluationMetric):
    @property
    def config(self):
        return EvaluationMetricConfig(
            name="mean_absolute_error",
            label="Mean Absolute Error Metric",
            description="A metric for mean absolute error.",
            is_aggregate=True,
            tags=["metric"],
        )

    def get_parameters(self, ctx, inputs):
        inputs.str(
            "sample_eval_key",
            label="Sample eval key parameter",
            description="Sample eval key",
            default=None,
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
