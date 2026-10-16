"""
Example assignment-policy plugin for FiftyOne workflows.

One policy (``policies.py``): tasks to labelers at the desired first-pass
approval rate, then the minimum, capped per person. See the package README.

| Copyright 2017-2026, Voxel51, Inc.
"""

from .policies import EXAMPLE_POLICIES


def register(p):
    for policy in EXAMPLE_POLICIES:
        p.register(policy)
