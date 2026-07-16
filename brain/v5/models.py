'Data records used by the AITP v5 kernel.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/models/part_01.py",
    "_compat_shards/models/part_02.py",
    ),
)
del _load_module_shards

from brain.v5.lifecycle_models import (  # noqa: E402 - compatibility shards load first.
    CloseoutBoundaryItem,
    CrossTopicRelationRecord,
    RecallAuditRecord,
    RecordingCandidateBatchRecord,
    ResearchProgramRecord,
    SessionCloseoutRecord,
    SessionFocusSetRecord,
)
from brain.v5.execution_models import (  # noqa: E402 - compatibility shards load first.
    ArtifactBlobReceiptRecord,
    ArtifactRecord,
    CheckpointApplicationReceiptRecord,
    CodePatchManifestRecord,
    CodeStateRecord,
    ExecutionBaselineRecord,
    ExecutionEnvironmentRecord,
    HumanCheckpointRecord,
    MonitorSnapshotRecord,
    ScopeRevalidationDecisionRecord,
    ToolRecipeRecord,
    ToolRunRecord,
    ValidationContractRecord,
    ValidationResultRecord,
)
from brain.v5.derivation_models import (  # noqa: E402 - compatibility shards load first.
    DerivationChainRecord,
    DerivationReviewRecord,
    DerivationStepRecord,
)
from brain.v5.physics_knowledge_models import (  # noqa: E402 - compatibility shards load first.
    InsightRecord,
    KnowledgeReviewDecisionRecord,
    ObjectRelationRecord,
    PhysicsAssertionRecord,
    PhysicsObjectRecord,
)
from brain.v5.record_lifecycle_models import (  # noqa: E402 - replace shard-compatible v1.
    LifecycleEventRecord,
)
from brain.v5.evidence_basis_models import (  # noqa: E402 - replace shard-compatible v1.
    EvidenceRecord,
)
from brain.v5.source_acquisition_models import (  # noqa: E402 - typed M3 process records.
    SourceAcquisitionDecisionRecord,
    SourceAcquisitionReceiptRecord,
)
from brain.v5.skill_models import (  # noqa: E402 - typed M4 reviewed-Skill records.
    SkillDistillationCandidateRecord,
    SkillInstallPlanRecord,
    SkillInstallReceiptRecord,
    SkillPackageArtifactRecord,
    SkillPatchProposalRecord,
    SkillProposalRecord,
    SkillReadinessReportRecord,
    SkillUsageRecord,
    SkillValidationExecutionRequest,
)
