"""
Example assignment-policy plugin for FiftyOne workflows.

One policy (``policies.py``): high-priority batches to the best-approved
labelers, capped. See the package README.

| Copyright 2017-2026, Voxel51, Inc.
"""

from .policies import EXAMPLE_POLICIES


def register(p):
    for policy in EXAMPLE_POLICIES:
        p.register(policy)
