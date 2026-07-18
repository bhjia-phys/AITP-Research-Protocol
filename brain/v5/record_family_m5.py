"""M5 Harness Feedback record-family metadata."""

M5_REGISTRY_ROWS = (
    (
        "harness_feedback_cases",
        "harness_feedback_case",
        "HarnessFeedbackCaseRecord",
        "case_id",
    ),
)

M5_RECORD_ROLES = {"harness_feedback_cases": "review_input_record"}
M5_SCHEMA_VERSIONS: dict[str, str] = {}
M5_DEPENDENCY_FIELDS = {
    "harness_feedback_cases": (
        "duplicate_of_refs",
        "related_case_refs",
        "source_refs",
        "supersedes_case_refs",
    )
}
M5_APPEND_ONLY_FAMILIES: set[str] = set()
M5_CANDIDATE_ONLY_FAMILIES: set[str] = set()
