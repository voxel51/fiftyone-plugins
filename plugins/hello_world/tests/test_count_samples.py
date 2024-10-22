import pytest
from unittest.mock import MagicMock
from hello_world import CountSamples

import fiftyone.core.dataset as fod
import fiftyone.core.view as fov


@pytest.fixture
def mock_view():
    """Fixture to create a mock view."""
    # Mocking a view with 5 samples
    mock_view = MagicMock(spec=fov.DatasetView)
    mock_view.__eq__.return_value = False
    mock_view.count.return_value = 5
    return mock_view


@pytest.fixture
def mock_context(mock_view):
    """Fixture to create a mock context."""
    # Mocking a dataset with 10 samples
    mock_dataset = MagicMock(spec=fod.Dataset)
    mock_dataset.view.return_value = mock_view
    mock_dataset.count.return_value = 10

    # Mocking the context
    ctx = MagicMock()
    ctx.dataset = mock_dataset
    ctx.view = mock_view  # Set ctx.view to the mock view initially
    ctx.params = {"target": "DATASET"}
    return ctx


def test_count_samples_init():
    """Test the initialization of the CountSamples operator."""
    operator = CountSamples()
    config = operator.config

    assert config.name == "count_samples"
    assert config.label == "Count samples"
    assert config.dynamic is True


def test_resolve_input_with_view(mock_context):
    """Test input resolution when the context has a view."""
    mock_context.dataset.view.return_value = MagicMock(spec=fov.DatasetView)

    operator = CountSamples()
    inputs = operator.resolve_input(mock_context)

    # Should have a target property
    assert len(inputs.type.properties) == 1
    assert "target" in inputs.type.properties


def test_resolve_input_without_view(mock_context):
    """Test input resolution when the context does not have a view."""
    operator = CountSamples()

    # Adjusting the context to simulate no view (view == dataset.view())
    mock_context.view = mock_context.dataset.view()
    inputs = operator.resolve_input(mock_context)

    # No enum should be present
    assert "target" not in inputs.type.properties


def test_execute_count_dataset(mock_context):
    """Test counting samples in the dataset."""
    operator = CountSamples()

    # Set the target to DATASET
    mock_context.params = {"target": "DATASET"}
    result = operator.execute(mock_context)

    assert result == {"count": 10}


def test_execute_count_view(mock_context):
    """Test counting samples in the current view."""
    operator = CountSamples()

    # Set the target to VIEW
    mock_context.params = {"target": "VIEW"}
    mock_context.view = (
        mock_context.dataset.view.return_value
    )  # Set ctx.view correctly
    result = operator.execute(mock_context)

    assert result == {"count": 5}


def test_resolve_output(mock_context):
    """Test output resolution for the CountSamples operator."""
    operator = CountSamples()

    # Set the target to DATASET
    mock_context.params = {"target": "DATASET"}
    outputs = operator.resolve_output(mock_context)

    assert "count" in outputs.type.properties
