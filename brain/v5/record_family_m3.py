"""Focused record-family metadata owned by the M3 knowledge vertical."""

M3_REGISTRY_ROWS = (
    ("insights", "insight", "InsightRecord", "insight_id"),
    ("knowledge_review_decisions", "knowledge_review_decision", "KnowledgeReviewDecisionRecord", "decision_id"),
    ("physics_assertions", "physics_assertion", "PhysicsAssertionRecord", "assertion_id"),
    ("source_acquisition_decisions", "source_acquisition_decision", "SourceAcquisitionDecisionRecord", "decision_id"),
    ("source_acquisition_receipts", "source_acquisition_receipt", "SourceAcquisitionReceiptRecord", "receipt_id"),
)

M3_RECORD_ROLES = {
    "insights": "orientation_only_record",
    "knowledge_review_decisions": "review_record",
    "source_acquisition_decisions": "process_record",
    "source_acquisition_receipts": "process_record",
}

M3_SCHEMA_VERSIONS = {
    **{family: "v2" for family, *_rest in M3_REGISTRY_ROWS},
    "lifecycle_events": "v2",
}

M3_DEPENDENCY_FIELDS = {
    "insights": (
        "grounding_refs", "inferred_from_refs", "proof_obligation_refs",
        "source_refs", "review_decision_ref.record_ref",
    ),
    "knowledge_review_decisions": ("checkpoint_ref.record_ref", "source_refs[].record_ref", "supersedes_decision_ref.record_ref"),
    "lifecycle_events": (
        "subject_ref.record_ref", "replacement_ref_pin.record_ref",
        "supersedes_event_ref.record_ref",
    ),
    "physics_assertions": (
        "object_ref", "source_asset_refs", "source_location_refs",
        "contradiction_refs", "supersedes_assertion_ref", "review_decision_ref.record_ref",
    ),
    "source_acquisition_receipts": ("decision_ref",),
}

M3_APPEND_ONLY_FAMILIES = frozenset({
    "knowledge_review_decisions",
    "source_acquisition_decisions",
    "source_acquisition_receipts",
})
