from brain.v5.query_index_accumulator import (
    content_accumulator_from_pairs,
    content_accumulator_watermark,
    replace_content_accumulator_pair,
)


def test_incremental_content_accumulator_matches_full_rebuild_for_create_and_revision():
    initial_pairs = (
        ("claim:a", "hash-a-v1"),
        ("claim:b", "hash-b-v1"),
    )
    initial = content_accumulator_from_pairs(initial_pairs)

    created = replace_content_accumulator_pair(
        initial,
        key="claim:c",
        previous_value="",
        current_value="hash-c-v1",
    )
    revised = replace_content_accumulator_pair(
        created,
        key="claim:a",
        previous_value="hash-a-v1",
        current_value="hash-a-v2",
    )
    rebuilt = content_accumulator_from_pairs(
        (
            ("claim:a", "hash-a-v2"),
            ("claim:b", "hash-b-v1"),
            ("claim:c", "hash-c-v1"),
        )
    )

    assert revised == rebuilt
    assert content_accumulator_watermark(revised) == content_accumulator_watermark(rebuilt)
