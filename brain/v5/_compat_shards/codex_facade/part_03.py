# Compatibility shard 3 for codex_facade.
from __future__ import annotations

def _profile_name(profile: str) -> str:
    clean = str(profile or "entry").strip().lower().replace("-", "_")
    aliases = {"read": "read_expansion", "recording": "guided_recording"}
    clean = aliases.get(clean, clean)
    allowed = {
        "setup",
        "entry",
        "read_expansion",
        "guided_recording",
        "literature",
        "closeout",
        "trust",
    }
    return clean if clean in allowed else "entry"

def _process_mode(process_mode: str, request_summary: str) -> str:
    clean = str(process_mode or "").strip().lower().replace("-", "_")
    allowed = {
        "setup",
        "new_topic",
        "continuation",
        "literature",
        "derivation",
        "code_numerical",
        "writing",
        "synthesis",
        "closeout",
    }
    if clean in allowed:
        return clean
    text = str(request_summary or "").lower()
    if any(token in text for token in ("paper", "literature", "arxiv", "reference", "citation")):
        return "literature"
    if any(token in text for token in ("文献", "论文", "参考文献", "引用", "读文献", "学习文献", "阅读文献")):
        return "literature"
    if any(token in text for token in ("note", "draft", "write", "article", "jhep")):
        return "writing"
    if any(token in text for token in ("笔记", "文章", "写作", "草稿", "写note", "写 note", "模板")):
        return "writing"
    if any(token in text for token in ("end", "handoff", "closeout", "summary")):
        return "closeout"
    if any(token in text for token in ("结束", "收尾", "交接", "总结", "会话结束")):
        return "closeout"
    if any(token in text for token in ("synthesis", "final", "conclusion", "综述", "综合", "结论", "最终")):
        return "synthesis"
    if any(token in text for token in ("derive", "derivation", "proof", "theorem", "algebra")):
        return "derivation"
    if any(token in text for token in ("推导", "证明", "定理", "代数", "公式")):
        return "derivation"
    if any(token in text for token in ("code", "run", "numerical", "hpc", "validation")):
        return "code_numerical"
    if any(token in text for token in ("代码", "运行", "数值", "计算", "验证", "测试", "程序")):
        return "code_numerical"
    return "continuation"

def _aitp_route_signals(
    text: str,
    *,
    session_id: str,
    topics: list[str],
    visible_files: list[str],
) -> dict[str, Any]:
    lowered = str(text or "").lower()
    reason_codes: list[str] = []
    matched: list[str] = []

    def add(code: str, token: str) -> None:
        if code not in reason_codes:
            reason_codes.append(code)
        if token and token not in matched:
            matched.append(token)

    explicit_tokens = [
        "aitp",
        "typed record",
        "claim trust",
        "trust preflight",
        "record_completeness",
        "quiet_checkpoint",
        "sensemaking_report",
        "evidence",
        "validation_result",
        "tool_run",
        "code_state",
        "claim boundary",
        "l2 memory",
    ]
    topic_tokens = [
        "topic",
        "session",
        "claim",
        "checkpoint",
        "open gap",
        "failed route",
        "wrong route",
        "superseded",
        "continue research",
        "continue this topic",
        "current topic",
        "prior result",
        "latest result",
        "research note",
        "latex",
        "pdf",
        "report",
    ]
    research_tokens = [
        "theoretical physics",
        "derivation",
        "proof",
        "theorem",
        "paper",
        "literature",
        "arxiv",
        "numerical",
        "simulation",
        "benchmark",
        "validation",
        "qsgw",
        "librpa",
        "dmft",
        "syk",
        "green function",
        "topology",
    ]
    durable_tokens = [
        "compile",
        "build",
        "artifact",
        "plot",
        "dataset",
        "log",
        "source",
        "record",
        "closeout",
        "handoff",
    ]
    chinese_tokens = [
        "\u7814\u7a76",
        "\u79d1\u7814",
        "\u8bfe\u9898",
        "\u7ee7\u7eed",
        "\u8bb0\u5f55",
        "\u8bba\u70b9",
        "\u8bc1\u636e",
        "\u9a8c\u8bc1",
        "\u4fe1\u4efb",
        "\u63a8\u5bfc",
        "\u8bc1\u660e",
        "\u8bba\u6587",
        "\u6587\u732e",
        "\u7b14\u8bb0",
        "\u62a5\u544a",
        "\u7f16\u8bd1",
        "\u9519\u8bef\u8def\u7ebf",
        "\u6700\u65b0\u7ed3\u679c",
        "\u7406\u8bba\u7269\u7406",
        "研究",
        "科研",
        "课题",
        "继续",
        "记录",
        "论点",
        "证据",
        "验证",
        "信任",
        "推导",
        "证明",
        "论文",
        "文献",
        "笔记",
        "报告",
        "编译",
        "错误路线",
        "最新结果",
        "理论物理",
    ]
    generic_question_markers = [
        "what is ",
        "explain ",
        "define ",
        "\u6982\u5ff5",
        "\u89e3\u91ca\u4e00\u4e0b",
        "\u662f\u4ec0\u4e48",
        "概念",
        "解释一下",
        "是什么",
    ]

    for token in explicit_tokens:
        if token in lowered:
            add("explicit_aitp_protocol_reference", token)
    for token in topic_tokens:
        if token in lowered:
            add("topic_or_continuation_reference", token)
    for token in research_tokens:
        if token in lowered:
            add("research_domain_reference", token)
    for token in durable_tokens:
        if token in lowered:
            add("durable_research_output_or_recording", token)
    for token in chinese_tokens:
        if token in text:
            add("chinese_research_or_protocol_reference", token)
    for path in visible_files:
        suffix = Path(path).suffix.lower()
        if suffix in {".tex", ".pdf", ".bib", ".ipynb", ".py", ".log", ".md"}:
            add("research_file_context_present", suffix)
            break
    if session_id:
        add("session_hint_present", "session_id")
    if topics:
        add("topic_hint_present", "topics")

    has_project_signal = any(
        code in reason_codes
        for code in (
            "explicit_aitp_protocol_reference",
            "topic_or_continuation_reference",
            "durable_research_output_or_recording",
            "chinese_research_or_protocol_reference",
            "research_file_context_present",
            "session_hint_present",
            "topic_hint_present",
        )
    )
    has_research_signal = "research_domain_reference" in reason_codes
    generic_only = (
        has_research_signal
        and not has_project_signal
        and any(marker in lowered or marker in text for marker in generic_question_markers)
    )
    required = False
    if "explicit_aitp_protocol_reference" in reason_codes:
        required = True
    elif session_id or topics:
        required = has_project_signal or has_research_signal
    elif has_project_signal and not generic_only:
        required = True
    elif has_research_signal and "durable_research_output_or_recording" in reason_codes:
        required = True

    confidence = "none"
    if required:
        if "explicit_aitp_protocol_reference" in reason_codes or session_id or topics:
            confidence = "high"
        elif len(reason_codes) >= 2:
            confidence = "medium"
        else:
            confidence = "low"
    elif generic_only:
        confidence = "medium"

    if not reason_codes:
        reason_codes.append("no_aitp_research_trigger_detected")
    if generic_only:
        reason_codes.append("generic_knowledge_question_without_project_context")

    return {
        "required": required,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "matched_triggers": matched,
    }

def _semantic_route_signals(assessment: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(assessment, dict) or not assessment:
        return {
            "provided": False,
            "required": None,
            "confidence": "none",
            "reason_codes": [],
            "matched_triggers": [],
            "normalized": {},
            "issues": [],
        }

    def clean_text(key: str) -> str:
        return str(assessment.get(key, "") or "").strip()

    def truthy(key: str) -> bool:
        value = assessment.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value or "").strip().lower() in {"1", "true", "yes", "y", "required", "needed"}

    task_kind = clean_text("task_kind").lower().replace("-", "_")
    confidence = clean_text("confidence").lower() or clean_text("route_confidence").lower()
    if confidence not in {"high", "medium", "low", "none"}:
        confidence = "medium"
    should_use = clean_text("should_use_aitp").lower().replace("-", "_")
    if should_use not in {"true", "false", "yes", "no", "required", "not_required", "uncertain", "unknown", ""}:
        should_use = ""

    research_fields = {
        "needs_prior_research_state": "semantic_needs_prior_research_state",
        "needs_latest_topic_state": "semantic_needs_latest_topic_state",
        "concerns_existing_topic_or_claim": "semantic_existing_topic_or_claim",
        "creates_or_updates_durable_research_output": "semantic_durable_research_output",
        "needs_validation_or_evidence_boundary": "semantic_validation_or_evidence_boundary",
        "mentions_failed_or_superseded_route": "semantic_failed_or_superseded_route",
        "trust_or_claim_status_sensitive": "semantic_trust_or_claim_status_sensitive",
    }
    true_fields = [field for field in research_fields if truthy(field)]
    generic_textbook = truthy("is_generic_textbook_question")
    uncertain = truthy("uncertain") or should_use in {"uncertain", "unknown"} or task_kind in {"uncertain", "ambiguous"}
    task_requires_aitp = task_kind in {
        "project_research",
        "topic_continuation",
        "prior_status",
        "literature_reading",
        "derivation",
        "validation",
        "note_writing",
        "report_writing",
        "closeout",
        "numerical_work",
        "artifact_production",
        "claim_boundary",
    }

    reason_codes: list[str] = []
    matched: list[str] = []

    def add(code: str, token: str) -> None:
        if code not in reason_codes:
            reason_codes.append(code)
        if token and token not in matched:
            matched.append(token)

    for field in true_fields:
        add(research_fields[field], field)
    if task_requires_aitp:
        add("semantic_task_kind_requires_aitp", task_kind)
    if generic_textbook:
        add("semantic_generic_textbook_question", "is_generic_textbook_question")
    if uncertain:
        add("semantic_route_uncertain", "uncertain")
    if should_use in {"true", "yes", "required"}:
        add("semantic_should_use_aitp", "should_use_aitp")
    elif should_use in {"false", "no", "not_required"}:
        add("semantic_should_not_use_aitp", "should_use_aitp")

    project_semantic = bool(true_fields) or task_requires_aitp
    if project_semantic:
        required: bool | None = True
    elif generic_textbook and should_use not in {"true", "yes", "required"}:
        required = False
    elif should_use in {"true", "yes", "required"}:
        required = True
    elif should_use in {"false", "no", "not_required"}:
        required = False
    elif uncertain:
        required = True
    else:
        required = None

    issues: list[str] = []
    if generic_textbook and project_semantic:
        issues.append("generic_textbook_question_conflicts_with_project_research_flags")
    if should_use in {"false", "no", "not_required"} and project_semantic:
        issues.append("should_use_aitp_false_conflicts_with_project_research_flags")

    normalized = {
        "task_kind": task_kind,
        "should_use_aitp": should_use,
        "confidence": confidence,
        "rationale": clean_text("rationale"),
        "is_generic_textbook_question": generic_textbook,
        "uncertain": uncertain,
        "true_research_fields": true_fields,
    }
    normalized.update({field: truthy(field) for field in research_fields})

    return {
        "provided": True,
        "required": required,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "matched_triggers": matched,
        "normalized": normalized,
        "issues": issues,
    }

def _merge_route_signals(heuristic: dict[str, Any], semantic: dict[str, Any]) -> dict[str, Any]:
    reason_codes = list(heuristic.get("reason_codes", []))
    matched = list(heuristic.get("matched_triggers", []))
    for code in semantic.get("reason_codes", []):
        if code not in reason_codes:
            reason_codes.append(code)
    for token in semantic.get("matched_triggers", []):
        if token and token not in matched:
            matched.append(token)

    semantic_required = semantic.get("required")
    required = bool(heuristic.get("required"))
    hard_heuristic = any(
        code in reason_codes
        for code in (
            "explicit_aitp_protocol_reference",
            "session_hint_present",
            "topic_hint_present",
            "research_file_context_present",
        )
    )
    if semantic_required is True:
        required = True
    elif semantic_required is False and not hard_heuristic:
        required = False

    confidence_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    confidence = str(heuristic.get("confidence", "none"))
    semantic_confidence = str(semantic.get("confidence", "none"))
    if semantic_required is not None and confidence_rank.get(semantic_confidence, 0) >= confidence_rank.get(confidence, 0):
        confidence = semantic_confidence
    if required and confidence == "none":
        confidence = "low"

    return {
        "required": required,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "matched_triggers": matched,
    }

def _expansions_for_mode(mode: str) -> list[str]:
    by_mode = {
        "literature": ["context_pack", "timeline", "relation_map", "note_outline"],
        "writing": ["timeline", "note_outline", "source_reconstruction", "trust_audit"],
        "synthesis": ["timeline", "relation_map", "source_reconstruction", "trust_audit"],
        "closeout": ["timeline", "recording_navigation", "context_pack"],
        "code_numerical": ["timeline", "relation_map", "process_graph", "recording_navigation"],
        "derivation": ["timeline", "relation_map", "note_outline", "recording_navigation"],
    }
    return by_mode.get(mode, ["context_pack", "timeline", "relation_map", "recording_navigation"])

def _allowed_expansions() -> list[str]:
    return [
        "context_pack",
        "brief",
        "timeline",
        "relation_map",
        "process_graph",
        "recording_navigation",
        "note_outline",
        "source_reconstruction",
        "trust_audit",
        "record_refs",
    ]

def _expansion_name(expansion: str) -> str:
    clean = str(expansion or "context_pack").strip().lower().replace("-", "_")
    aliases = {
        "context": "context_pack",
        "execution_brief": "brief",
        "continuation": "timeline",
        "research_timeline": "timeline",
        "claim_relation_map": "relation_map",
        "recording": "recording_navigation",
        "source": "source_reconstruction",
        "trust": "trust_audit",
    }
    return aliases.get(clean, clean)
