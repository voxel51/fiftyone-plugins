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
import itertools


class EvaluationMetric(foo.Operator):
    def get_parameters(self, ctx, inputs):
        pass

    def parse_parameters(self, ctx, params):
        pass

    def compute_by_sample(self, sample, eval_key, **kwargs):
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


def _safe_mean(values):
    values = [v for v in values if v is not None]
    return np.mean(values) if values else None


def _abs_error(ypred, ytrue):
    return abs(ypred - ytrue)


class AbsoluteErrorMetric(EvaluationMetric):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="absolute_error",
            label="Absolute Error Metric",
            description="A metric for absolute error.",
            tags=["metric", "regression"],
        )

    def compute_by_sample(self, sample, eval_key, ytrue, ypred):
        metric_field = f"{eval_key}_{self.config.name}"
        if sample.media_type == "video":
            frame_errors = list(map(_abs_error, ypred, ytrue))
            for idx, frame in enumerate(sample.frames.values()):
                frame[metric_field] = frame_errors[idx]
            sample[metric_field] = _safe_mean(frame_errors)
        else:
            sample[metric_field] = _abs_error(ypred, ytrue)

    def compute(self, samples, eval_key, results):
        ypred, ytrue = results.ypred, results.ytrue
        start_idx = 0
        for sample in samples.iter_samples(autosave=True):
            num_frames = (
                len(sample._frames) if sample.media_type == "video" else 1
            )
            self.compute_by_sample(
                sample,
                eval_key,
                ytrue=ytrue[start_idx : start_idx + num_frames],
                ypred=ypred[start_idx : start_idx + num_frames],
            )
            start_idx += num_frames

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
            description="A metric for computing mean absolute error across all frames or samples.",
            tags=["metric", "regression"],
        )

    def get_parameters(self, ctx, inputs):
        eval_key = ctx.params.get("eval_key", None)
        inputs.str(
            "error_eval_key",
            label="Sample/Frame error eval key parameter",
            description="Sample/Frame error eval key to use for computing Mean Absolute Error",
            default=f"{eval_key}_absolute_error",
            required=True,
        )

    def compute(self, samples, eval_key, results, error_eval_key):
        dataset = samples._dataset

        if dataset.has_field(dataset._FRAMES_PREFIX + error_eval_key):
            # Compute MAE across all frames.
            values = dataset.values(dataset._FRAMES_PREFIX + error_eval_key)
            values = list(itertools.chain.from_iterable(values))
        elif dataset.has_field(error_eval_key):
            # Compute MAE across all samples.
            values = dataset.values(error_eval_key)
        else:
            return None

        return np.average(values).tolist()


def register(p):
    p.register(ExampleMetric)
    p.register(AbsoluteErrorMetric)
    p.register(MeanAbsoluteErrorMetric)
