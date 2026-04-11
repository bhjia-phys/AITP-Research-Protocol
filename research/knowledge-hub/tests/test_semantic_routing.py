from pathlib import Path
import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.semantic_routing import (  # noqa: E402
    canonical_lane,
    canonical_template_mode,
    canonical_validation_mode,
)


def test_canonical_lane_preserves_first_principles() -> None:
    assert canonical_lane(template_mode="toy_numeric", research_mode="first_principles") == "first_principles"


def test_canonical_lane_preserves_theory_synthesis() -> None:
    assert canonical_lane(template_mode="code_method", research_mode="theory_synthesis") == "theory_synthesis"


def test_canonical_template_mode_for_theory_synthesis() -> None:
    assert canonical_template_mode("theory_synthesis") == "code_method"


def test_canonical_validation_mode_for_first_principles() -> None:
    assert canonical_validation_mode("toy_numeric", "first_principles") == "numerical"


def test_canonical_lane_prefers_specific_research_mode_over_template() -> None:
    assert canonical_lane(template_mode="formal_theory", research_mode="theory_synthesis") == "theory_synthesis"


def test_canonical_validation_mode_prefers_specific_research_mode_over_template() -> None:
    assert canonical_validation_mode("formal_theory", "theory_synthesis") == "analytical"
