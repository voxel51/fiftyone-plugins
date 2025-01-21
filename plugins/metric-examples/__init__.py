"""
Example metrics.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import itertools

import numpy as np

import fiftyone as fo
import fiftyone.operators as foo
from fiftyone import ViewField as F


class ExampleMetric(foo.EvaluationMetric):
    @property
    def config(self):
        return foo.EvaluationMetricConfig(
            name="example_metric",
            label="Example metric",
            description="An example evaluation metric",
        )

    def get_parameters(self, ctx, inputs):
        inputs.str(
            "value",
            label="Example value",
            description="The example value to store/return",
            default="foo",
            required=True,
        )

    def compute(self, samples, results, value="foo"):
        dataset = samples._dataset
        eval_key = results.key
        metric_field = f"{eval_key}_{self.config.name}"
        dataset.add_sample_field(metric_field, fo.StringField)
        samples.set_field(metric_field, value).save()

        return value

    def get_fields(self, samples, config, eval_key):
        return [f"{eval_key}_{self.config.name}"]


class MeanAbsoluteErrorMetric(foo.EvaluationMetric):
    @property
    def config(self):
        return foo.EvaluationMetricConfig(
            name="mean_absolute_error",
            label="Mean Absolute Error",
            description="Computes the mean absolute error of the regression data",
            eval_types=["regression"],
            lower_is_better=True,
        )

    def compute(self, samples, results):
        dataset = samples._dataset
        eval_key = results.key
        is_frame_field = samples._is_frame_field(results.config.gt_field)

        ytrue = results.ytrue
        ypred = results.ypred
        missing = results.missing

        metric_field = f"{eval_key}_absolute_error"
        compute_error = _make_compute_error_fcn(_absolute_error, missing)

        if is_frame_field:
            # Split values back into frames
            frame_counts = samples.values(F("frames").length())
            _ytrue = _unflatten(ytrue, frame_counts)
            _ypred = _unflatten(ypred, frame_counts)

            frame_errors = [
                list(map(compute_error, _yp, _yt))
                for _yp, _yt in zip(_ypred, _ytrue)
            ]
            sample_errors = [_safe_mean(e) for e in frame_errors]

            errors = list(itertools.chain.from_iterable(frame_errors))

            # Per-frame errors
            _metric_field = samples._FRAMES_PREFIX + metric_field
            samples.set_values(_metric_field, frame_errors)

            # Per-sample errors
            samples.set_values(metric_field, sample_errors)
        else:
            # Per-sample errors
            errors = list(map(compute_error, ypred, ytrue))
            samples.set_values(metric_field, errors)

        return _safe_mean(errors)

    def get_fields(self, samples, config, eval_key):
        metric_field = f"{eval_key}_absolute_error"

        fields = [metric_field]
        if samples._is_frame_field(config.gt_field):
            fields.append(samples._FRAMES_PREFIX + metric_field)

        return fields


class MeanSquaredErrorMetric(foo.EvaluationMetric):
    @property
    def config(self):
        return foo.EvaluationMetricConfig(
            name="mean_squared_error",
            label="Mean Squared Error",
            description="Computes the mean squared error of the regression data",
            eval_types=["regression"],
            lower_is_better=True,
        )

    def compute(self, samples, results):
        dataset = samples._dataset
        eval_key = results.key
        is_frame_field = samples._is_frame_field(results.config.gt_field)

        ytrue = results.ytrue
        ypred = results.ypred
        missing = results.missing

        metric_field = f"{eval_key}_squared_error"
        compute_error = _make_compute_error_fcn(_squared_error, missing)

        if is_frame_field:
            # Split values back into frames
            frame_counts = samples.values(F("frames").length())
            _ytrue = _unflatten(ytrue, frame_counts)
            _ypred = _unflatten(ypred, frame_counts)

            # Per-frame errors
            frame_errors = [
                list(map(compute_error, _yp, _yt))
                for _yp, _yt in zip(_ypred, _ytrue)
            ]
            errors = list(itertools.chain.from_iterable(frame_errors))
            _metric_field = samples._FRAMES_PREFIX + metric_field
            samples.set_values(_metric_field, frame_errors)

            # Per-sample mean errors
            sample_errors = [_safe_mean(e) for e in frame_errors]
            samples.set_values(metric_field, sample_errors)
        else:
            # Per-sample errors
            errors = list(map(compute_error, ypred, ytrue))
            samples.set_values(metric_field, errors)

        return _safe_mean(errors)

    def get_fields(self, samples, config, eval_key):
        metric_field = f"{eval_key}_squared_error"

        fields = [metric_field]
        if samples._is_frame_field(config.gt_field):
            fields.append(samples._FRAMES_PREFIX + metric_field)

        return fields


def _unflatten(values, counts):
    _values = iter(values)
    return [list(itertools.islice(_values, n)) for n in counts]


def _make_compute_error_fcn(error_fcn, missing):
    def compute_error(yp, yt):
        if missing is not None:
            if yp is None:
                yp = missing

            if yt is None:
                yt = missing

        try:
            return error_fcn(yp, yt)
        except:
            return None

    return compute_error


def _absolute_error(ypred, ytrue):
    return np.abs(ypred - ytrue)


def _squared_error(ypred, ytrue):
    return np.square(ypred - ytrue)


def _safe_mean(values):
    values = [v for v in values if v is not None]
    return np.mean(values) if values else None


def register(p):
    p.register(ExampleMetric)
    p.register(MeanAbsoluteErrorMetric)
    p.register(MeanSquaredErrorMetric)
