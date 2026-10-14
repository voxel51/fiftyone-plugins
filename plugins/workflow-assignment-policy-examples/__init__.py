"""
Example assignment-policy plugin for FiftyOne workflows.

Three policies (``policies.py``), from the smallest possible one to a
routing rule with fall-through. See the package README.

| Copyright 2017-2026, Voxel51, Inc.
"""

from .policies import EXAMPLE_POLICIES


def register(p):
    for policy in EXAMPLE_POLICIES:
        p.register(policy)
