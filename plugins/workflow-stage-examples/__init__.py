"""
Example workflow-stage plugin.

Ten example stages (``stages.py``), the delegated operators they dispatch
(``dos.py``), and a custom HITL release panel (``panel.py``). See the
package README for the guided tour.

| Copyright 2017-2026, Voxel51, Inc.
"""

from .dos import EXAMPLE_DOS
from .panel import EXAMPLE_PANELS
from .stages import EXAMPLE_STAGES


def register(p):
    for stage in EXAMPLE_STAGES:
        p.register(stage)
    for do in EXAMPLE_DOS:
        p.register(do)
    for panel in EXAMPLE_PANELS:
        p.register(panel)
