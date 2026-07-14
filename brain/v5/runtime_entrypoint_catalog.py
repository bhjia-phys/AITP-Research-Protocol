"""Runtime entrypoint catalog data and CLI sample arguments."""

from __future__ import annotations

from typing import Any

from brain.v5.runtime_entrypoint_catalog_data.part_01 import RUNTIME_ENTRYPOINTS_01
from brain.v5.runtime_entrypoint_catalog_data.part_02 import RUNTIME_ENTRYPOINTS_02
from brain.v5.runtime_entrypoint_catalog_data.part_03 import RUNTIME_ENTRYPOINTS_03

RUNTIME_ENTRYPOINTS: dict[str, dict[str, Any]] = {
    **RUNTIME_ENTRYPOINTS_01,
    **RUNTIME_ENTRYPOINTS_02,
    **RUNTIME_ENTRYPOINTS_03,
}


def capability_registry_ref() -> str:
    """Return the authority that validates this compatibility catalog."""

    return "brain.v5.capability_registry:capability_specs"


def sample_args_for_template(template: str) -> list[str]:
    from brain.v5.runtime_entrypoint_samples import sample_args_for_template as _sample_args

    return _sample_args(template)
