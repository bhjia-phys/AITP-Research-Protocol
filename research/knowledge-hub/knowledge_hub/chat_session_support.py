from __future__ import annotations

import re
from typing import Any


def _explicit_chat_route(
    self,
    *,
    explicit_topic_slug: str | None,
    explicit_topic: str | None,
    explicit_current_topic: bool,
    explicit_latest_topic: bool,
) -> dict[str, Any] | None:
    if explicit_topic_slug:
        return {
            "route": "explicit_topic_slug",
            "topic_slug": explicit_topic_slug,
            "topic": None,
            "reason": "Caller supplied an explicit topic slug.",
        }
    if explicit_topic:
        return {
            "route": "explicit_topic_title",
            "topic_slug": None,
            "topic": explicit_topic,
            "reason": "Caller supplied an explicit topic title.",
        }
    if explicit_current_topic:
        resolved_topic_slug = self.current_topic_slug(fallback_to_latest=True)
        return {
            "route": "explicit_current_topic",
            "topic_slug": resolved_topic_slug,
            "topic": None,
            "reason": "Caller explicitly requested the current topic route.",
        }
    if explicit_latest_topic:
        resolved_topic_slug = self.latest_topic_slug()
        return {
            "route": "explicit_latest_topic",
            "topic_slug": resolved_topic_slug,
            "topic": None,
            "reason": "Caller explicitly requested the latest topic route.",
        }
    return None


def _management_or_named_topic_route(self, *, task: str) -> dict[str, Any] | None:
    new_topic_title = self._extract_new_topic_title(task)
    if new_topic_title:
        return {
            "route": "request_new_topic",
            "topic_slug": None,
            "topic": new_topic_title,
            "reason": "The human request clearly opens a new topic.",
        }
    if re.search(
        r"(?:有哪些\s*(?:topic|课题|主题)|列出\s*(?:topic|课题|主题)|查看\s*(?:topic|课题|主题)|list\s+(?:active\s+)?topics|show\s+(?:active\s+)?topics)",
        task,
        flags=re.IGNORECASE,
    ):
        return {
            "route": "request_list_active_topics",
            "topic_slug": None,
            "topic": None,
            "reason": "The human request asks for the active-topic list.",
        }
    management_topic_slug = self._resolve_topic_reference_for_management(task)
    if management_topic_slug and re.search(r"(?:暂停|pause\b)", task, flags=re.IGNORECASE):
        return {
            "route": "request_pause_topic",
            "topic_slug": management_topic_slug,
            "topic": None,
            "reason": "The human request pauses an active topic.",
        }
    if management_topic_slug and re.search(r"(?:恢复|resume\b)", task, flags=re.IGNORECASE):
        return {
            "route": "request_resume_topic",
            "topic_slug": management_topic_slug,
            "topic": None,
            "reason": "The human request resumes an active topic.",
        }
    if management_topic_slug and re.search(r"(?:切到|切换到|focus topic|switch to|focus\s+on\s+topic)", task, flags=re.IGNORECASE):
        return {
            "route": "request_focus_topic",
            "topic_slug": management_topic_slug,
            "topic": None,
            "reason": "The human request changes the focused topic.",
        }
    resolved_slug = self._find_known_topic_slug_in_request(task)
    if resolved_slug:
        return {
            "route": "request_named_existing_topic",
            "topic_slug": resolved_slug,
            "topic": None,
            "reason": "The human request already names a known topic slug.",
        }
    if re.search(r"(?:这个\s*topic|当前\s*topic|这个\s*课题|当前\s*课题|this topic|current topic|active topic)", task, flags=re.IGNORECASE):
        resolved_topic_slug = self.current_topic_slug(fallback_to_latest=True)
        return {
            "route": "request_current_topic_reference",
            "topic_slug": resolved_topic_slug,
            "topic": None,
            "reason": "The human request refers to the current topic without naming a slug.",
        }
    return None


def _projection_or_memory_route(self, *, task: str) -> dict[str, Any]:
    registry = self._load_active_topics_registry()
    projection_hint = self._projection_routing_hint(task=task, registry=registry)
    try:
        resolved_current_topic_slug = self.current_topic_slug(fallback_to_latest=False)
    except FileNotFoundError:
        resolved_current_topic_slug = None

    if resolved_current_topic_slug:
        if projection_hint and projection_hint["matched_topic_slug"] != resolved_current_topic_slug:
            return {
                "route": "implicit_current_topic",
                "topic_slug": resolved_current_topic_slug,
                "topic": None,
                "reason": (
                    "No explicit topic was provided, so durable current-topic memory still wins. "
                    f"Projection metadata from `{projection_hint['matched_topic_slug']}` also matched the request "
                    "but did not override the current focus."
                ),
                "projection_routing": {
                    **projection_hint,
                    "used": False,
                    "decision": "current_topic_outranks_projection",
                },
            }
        if projection_hint and projection_hint["matched_topic_slug"] == resolved_current_topic_slug:
            return {
                "route": "implicit_current_topic",
                "topic_slug": resolved_current_topic_slug,
                "topic": None,
                "reason": (
                    "No explicit topic was provided, so the request falls back to durable current-topic memory. "
                    "The same topic's mature projection metadata also matches the request and reinforces that route."
                ),
                "projection_routing": {
                    **projection_hint,
                    "used": True,
                    "decision": "projection_reinforced_current_topic",
                },
            }
        return {
            "route": "implicit_current_topic",
            "topic_slug": resolved_current_topic_slug,
            "topic": None,
            "reason": "No explicit topic was provided, so the request falls back to current-topic memory.",
        }

    if projection_hint:
        return {
            "route": "projection_matched_topic",
            "topic_slug": projection_hint["matched_topic_slug"],
            "topic": None,
            "reason": (
                "No explicit topic or durable current-topic focus was available. "
                f"Mature projection metadata from `{projection_hint['matched_topic_slug']}` matched the request and is being used as bounded routing guidance."
            ),
            "projection_routing": {
                **projection_hint,
                "used": True,
                "decision": "selected_projection_match",
            },
        }

    try:
        resolved_topic_slug = self.current_topic_slug(fallback_to_latest=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Unable to infer an AITP topic from this request. Say `开一个新 topic：...` or pass an explicit topic flag."
        ) from exc

    return {
        "route": "implicit_current_topic",
        "topic_slug": resolved_topic_slug,
        "topic": None,
        "reason": "No explicit topic was provided, so the request falls back to current-topic memory.",
    }


def route_codex_chat_request(
    self,
    *,
    task: str,
    explicit_topic_slug: str | None = None,
    explicit_topic: str | None = None,
    explicit_current_topic: bool = False,
    explicit_latest_topic: bool = False,
) -> dict[str, Any]:
    explicit_route = _explicit_chat_route(
        self,
        explicit_topic_slug=explicit_topic_slug,
        explicit_topic=explicit_topic,
        explicit_current_topic=explicit_current_topic,
        explicit_latest_topic=explicit_latest_topic,
    )
    if explicit_route is not None:
        return explicit_route
    managed = _management_or_named_topic_route(self, task=task)
    if managed is not None:
        return managed
    return _projection_or_memory_route(self, task=task)


def _management_route_payload(
    self,
    *,
    task: str,
    routing: dict[str, Any],
    updated_by: str,
) -> dict[str, Any] | None:
    management_route = str(routing.get("route") or "")
    if management_route == "request_list_active_topics":
        payload = self.list_active_topics(updated_by=updated_by)
        return {
            "task": task,
            "routing": routing,
            "topic_management": payload,
            "current_topic_memory": self.get_current_topic_memory() if payload.get("focused_topic_slug") else None,
        }
    if management_route == "request_focus_topic":
        payload = self.focus_topic(topic_slug=str(routing.get("topic_slug") or ""), updated_by=updated_by, human_request=task)
        return {
            "task": task,
            "routing": routing,
            "topic_management": payload,
            "current_topic_memory": payload.get("current_topic_memory"),
        }
    if management_route == "request_pause_topic":
        payload = self.pause_topic(topic_slug=str(routing.get("topic_slug") or ""), updated_by=updated_by, human_request=task)
        return {
            "task": task,
            "routing": routing,
            "topic_management": payload,
            "current_topic_memory": payload.get("current_topic_memory"),
        }
    if management_route == "request_resume_topic":
        payload = self.resume_topic(topic_slug=str(routing.get("topic_slug") or ""), updated_by=updated_by, human_request=task)
        return {
            "task": task,
            "routing": routing,
            "topic_management": payload,
            "current_topic_memory": payload.get("current_topic_memory"),
        }
    return None


def start_chat_session(
    self,
    *,
    task: str,
    explicit_topic_slug: str | None = None,
    explicit_topic: str | None = None,
    explicit_current_topic: bool = False,
    explicit_latest_topic: bool = False,
    statement: str | None = None,
    run_id: str | None = None,
    control_note: str | None = None,
    updated_by: str = "aitp-session-start",
    skill_queries: list[str] | None = None,
    max_auto_steps: int = 4,
    research_mode: str | None = None,
    load_profile: str | None = None,
) -> dict[str, Any]:
    try:
        pre_route_current_topic = self.get_current_topic_memory()
    except FileNotFoundError:
        pre_route_current_topic = {}

    routing = route_codex_chat_request(
        self,
        task=task,
        explicit_topic_slug=explicit_topic_slug,
        explicit_topic=explicit_topic,
        explicit_current_topic=explicit_current_topic,
        explicit_latest_topic=explicit_latest_topic,
    )
    management_payload = _management_route_payload(
        self,
        task=task,
        routing=routing,
        updated_by=updated_by,
    )
    if management_payload is not None:
        return management_payload

    payload = self.run_topic_loop(
        topic_slug=routing.get("topic_slug"),
        topic=routing.get("topic"),
        statement=statement,
        run_id=run_id,
        control_note=control_note,
        updated_by=updated_by,
        human_request=task,
        skill_queries=skill_queries,
        max_auto_steps=max_auto_steps,
        research_mode=research_mode,
        load_profile=load_profile,
    )
    session_start = self._materialize_session_start_contract(
        task=task,
        routing=routing,
        loop_payload=payload,
        updated_by=updated_by,
        pre_route_current_topic=pre_route_current_topic,
    )
    payload["session_start"] = session_start
    memory_paths = self._current_topic_memory_paths()
    return {
        "task": task,
        "routing": routing,
        "topic_slug": payload["topic_slug"],
        "run_id": payload.get("run_id"),
        "loop_state_path": payload["loop_state_path"],
        "runtime_protocol_path": payload["runtime_protocol"]["runtime_protocol_path"],
        "load_profile": payload.get("load_profile"),
        "capability_report_path": payload["capability_audit"]["capability_report_path"],
        "trust_report_path": payload["trust_audit"]["trust_report_path"] if payload.get("trust_audit") else None,
        "current_topic_memory": payload["current_topic_memory"],
        "current_topic_memory_path": str(memory_paths["json"]),
        "current_topic_note_path": str(memory_paths["note"]),
        "session_start": session_start,
        "session_start_contract_path": session_start["session_start_contract_path"],
        "session_start_note_path": session_start["session_start_note_path"],
        "bootstrap": payload["bootstrap"],
        "entry_audit": payload["entry_audit"],
        "auto_actions": payload["auto_actions"],
        "exit_audit": payload["exit_audit"],
        "loop_payload": payload,
    }
