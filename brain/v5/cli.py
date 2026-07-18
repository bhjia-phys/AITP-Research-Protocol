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
from brain.v5.cli_execution import (
    add_execution_parser as _add_execution_parser,
    dispatch_execution_command as _dispatch_execution_command,
    is_execution_command as _is_execution_command,
)
from brain.v5.cli_promotion_checkpoint import (
    add_promotion_checkpoint_parser as _add_promotion_checkpoint_parser,
    dispatch_promotion_checkpoint as _dispatch_promotion_checkpoint,
    is_promotion_checkpoint_command as _is_promotion_checkpoint_command,
)
from brain.v5.cli_knowledge import (
    add_knowledge_parser as _add_knowledge_parser,
    dispatch_knowledge_command as _dispatch_knowledge_command,
    is_knowledge_command as _is_knowledge_command,
)
from brain.v5.cli_skills import (
    add_skill_parser as _add_skill_parser,
    dispatch_skill_command as _dispatch_skill_command,
    is_skill_command as _is_skill_command,
)
from brain.v5.cli_research_moments import (
    add_research_moment_parser as _add_research_moment_parser,
    dispatch_research_moment_command as _dispatch_research_moment_command,
    is_research_moment_command as _is_research_moment_command,
)


_add_parser_section_04_without_lifecycle = _add_parser_section_04


def _add_parser_section_04(sp):
    _add_parser_section_04_without_lifecycle(sp)
    _add_session_lifecycle_parsers(sp)
    _add_execution_parser(sp)
    _add_promotion_checkpoint_parser(sp)
    _add_knowledge_parser(sp)
    _add_skill_parser(sp)
    _add_research_moment_parser(sp)


_dispatch_without_lifecycle = _dispatch


def _dispatch(args):
    if _is_research_moment_command(args):
        return _dispatch_research_moment_command(args, init_workspace(args.base))
    if _is_skill_command(args):
        return _dispatch_skill_command(args)
    if _is_knowledge_command(args):
        return _dispatch_knowledge_command(args)
    if _is_promotion_checkpoint_command(args):
        return _dispatch_promotion_checkpoint(args, init_workspace(args.base))
    if _is_execution_command(args):
        return _dispatch_execution_command(args)
    if _is_session_lifecycle_command(args):
        return _dispatch_session_lifecycle(args)
    return _dispatch_without_lifecycle(args)
