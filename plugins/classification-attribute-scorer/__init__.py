"""
Classification attribute scorer for FiftyOne workflows.

| Copyright 2017-2026, Voxel51, Inc.
"""

from .scorer import ClassificationAttributes


def register(p):
    p.register(ClassificationAttributes)
