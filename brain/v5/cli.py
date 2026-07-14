'Small JSON CLI for the AITP v5 kernel.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/cli/part_01.py",
    "_compat_shards/cli/part_02.py",
    "_compat_shards/cli/part_03.py",
    "_compat_shards/cli/part_04.py",
    "_compat_shards/cli/part_05.py",
    ),
)
del _load_module_shards

from brain.v5.cli_session_lifecycle import (
    add_session_lifecycle_parsers as _add_session_lifecycle_parsers,
    dispatch_session_lifecycle as _dispatch_session_lifecycle,
    is_session_lifecycle_command as _is_session_lifecycle_command,
)


_add_parser_section_04_without_lifecycle = _add_parser_section_04


def _add_parser_section_04(sp):
    _add_parser_section_04_without_lifecycle(sp)
    _add_session_lifecycle_parsers(sp)


_dispatch_without_lifecycle = _dispatch


def _dispatch(args):
    if _is_session_lifecycle_command(args):
        return _dispatch_session_lifecycle(args)
    return _dispatch_without_lifecycle(args)
