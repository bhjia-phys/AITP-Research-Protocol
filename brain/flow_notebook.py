"""Backward-compatibility shim — imports from brain.flow_notebook package.

This file exists so existing import paths continue to work:
    from brain.flow_notebook import build_notebook, SECTION_ORDER, _esc

The actual implementation lives in the brain/flow_notebook/ package.
"""
from brain.flow_notebook import *  # noqa: F401, F403
from brain.flow_notebook import __all__  # noqa: F401
