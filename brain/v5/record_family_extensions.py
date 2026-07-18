"""Merged metadata exported by milestone-specific record-family modules."""

from brain.v5 import record_family_m3 as _m3
from brain.v5 import record_family_m4 as _m4
from brain.v5 import record_family_m5 as _m5


REGISTRY_ROWS = _m3.M3_REGISTRY_ROWS + _m4.M4_REGISTRY_ROWS + _m5.M5_REGISTRY_ROWS
RECORD_ROLES = {**_m3.M3_RECORD_ROLES, **_m4.M4_RECORD_ROLES, **_m5.M5_RECORD_ROLES}
SCHEMA_VERSIONS = {
    **_m3.M3_SCHEMA_VERSIONS,
    **_m4.M4_SCHEMA_VERSIONS,
    **_m5.M5_SCHEMA_VERSIONS,
}
DEPENDENCY_FIELDS = {
    **_m3.M3_DEPENDENCY_FIELDS,
    **_m4.M4_DEPENDENCY_FIELDS,
    **_m5.M5_DEPENDENCY_FIELDS,
}
APPEND_ONLY_FAMILIES = (
    _m3.M3_APPEND_ONLY_FAMILIES
    | _m4.M4_APPEND_ONLY_FAMILIES
    | _m5.M5_APPEND_ONLY_FAMILIES
)
CANDIDATE_ONLY_FAMILIES = _m4.M4_CANDIDATE_ONLY_FAMILIES | _m5.M5_CANDIDATE_ONLY_FAMILIES
