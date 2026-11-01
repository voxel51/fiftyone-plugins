"""
Example label-scorer plugin for FiftyOne workflows.

One scorer (``scorers.py``): boxes scored on overlap and attributes, with
critical attributes. See the package README.

| Copyright 2017-2026, Voxel51, Inc.
"""

from .scorers import EXAMPLE_SCORERS


def register(p):
    for scorer in EXAMPLE_SCORERS:
        p.register(scorer)
