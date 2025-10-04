#!/usr/bin/env python3
"""
Tests for the metageo plugin operators.

This file contains tests for the IndexGridOperator and WatchIndexingOperator classes.
"""

import pytest
import sys
import os

# Add the plugin directory to the path so we can import the module
plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_dir)

try:
    from __init__ import IndexGridOperator, WatchIndexingOperator
except ImportError:
    pytest.skip("Could not import operators from __init__.py", allow_module_level=True)


class TestOperators:
    """Test cases for the metageo plugin operators."""

    def test_index_grid_operator_initialization(self):
        """Test that IndexGridOperator initializes correctly."""
        operator = IndexGridOperator()
        assert operator is not None
        
        # Test config
        config = operator.config
        assert config.name == "index_grid"
        assert config.label == "Index Entire Grid"
        assert config.allow_delegated_execution is True
        assert config.allow_immediate_execution is True

    def test_watch_indexing_operator_initialization(self):
        """Test that WatchIndexingOperator initializes correctly."""
        operator = WatchIndexingOperator()
        assert operator is not None
        
        # Test config
        config = operator.config
        assert config.name == "watch_indexing"
        assert config.label == "Watch Indexing Progress"
        assert config.execute_as_generator is True
        assert config.allow_delegated_execution is True
        assert config.allow_immediate_execution is True


if __name__ == "__main__":
    print("Testing metageo plugin operators...")
    print("=" * 50)
    print("Run with: pytest tests/test_operators.py -v")
