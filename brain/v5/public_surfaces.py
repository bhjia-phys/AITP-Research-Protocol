'Shared validation entrypoints for public AITP v5 surfaces.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/public_surfaces/part_01.py",
    "_compat_shards/public_surfaces/part_02.py",
    ),
)
del _load_module_shards

from brain.v5.lifecycle_surface_contracts import (
    lifecycle_surface_names as _lifecycle_surface_names,
    lifecycle_surface_purposes as _lifecycle_surface_purposes,
    lifecycle_surface_validators as _lifecycle_surface_validators,
)
from brain.v5.execution_surface_contracts import (
    execution_surface_names as _execution_surface_names,
    execution_surface_purposes as _execution_surface_purposes,
    execution_surface_validators as _execution_surface_validators,
)
from brain.v5.evidence_surface_contracts import (
    evidence_surface_validators as _evidence_surface_validators,
)
from brain.v5.knowledge_surface_contracts import (
    knowledge_surface_names as _knowledge_surface_names,
    knowledge_surface_purposes as _knowledge_surface_purposes,
    knowledge_surface_validators as _knowledge_surface_validators,
)
from brain.v5.skill_surface_contracts import (
    skill_surface_names as _skill_surface_names,
    skill_surface_purposes as _skill_surface_purposes,
    skill_surface_validators as _skill_surface_validators,
)
from brain.v5.research_moment_surface_contracts import (
    research_moment_surface_names as _research_moment_surface_names,
    research_moment_surface_purposes as _research_moment_surface_purposes,
    research_moment_surface_validators as _research_moment_surface_validators,
)


_PUBLIC_SURFACE_NAMES = tuple(
    dict.fromkeys((
        *_PUBLIC_SURFACE_NAMES,
        *_lifecycle_surface_names(),
        *_execution_surface_names(),
        *_knowledge_surface_names(),
        *_skill_surface_names(),
        *_research_moment_surface_names(),
    ))
)
_PUBLIC_SURFACE_PURPOSES = {
    **_PUBLIC_SURFACE_PURPOSES,
    **_lifecycle_surface_purposes(),
    **_execution_surface_purposes(),
    **_knowledge_surface_purposes(),
    **_skill_surface_purposes(),
    **_research_moment_surface_purposes(),
}
_validators_without_lifecycle = _validators


def _validators():
    validators = _validators_without_lifecycle()
    validators.update(_lifecycle_surface_validators())
    validators.update(_execution_surface_validators())
    validators.update(_evidence_surface_validators())
    validators.update(_knowledge_surface_validators())
    validators.update(_skill_surface_validators())
    validators.update(_research_moment_surface_validators())
    return validators
