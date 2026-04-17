from __future__ import annotations

import json
import unittest

import test_hypothesis_route_transition_commitment_contracts as commitment_contracts

from knowledge_hub.topic_replay import materialize_topic_replay_bundle


class HypothesisRouteTransitionAuthorityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._base = commitment_contracts.HypothesisRouteTransitionCommitmentContractTests(methodName="runTest")
        self._base.setUp()
        self._tmpdir = self._base._tmpdir
        self.root = self._base.root
        self.kernel_root = self._base.kernel_root
        self.repo_root = self._base.repo_root
        self.package_root = self._base.package_root
        self.service = self._base.service

    def tearDown(self) -> None:
        self._base.tearDown()

    def _write_json(self, relative_path: str, payload: dict) -> None:
        self._base._write_json(relative_path, payload)

    def _seed_demo_topic(self, *, topic_slug: str, route_mode: str) -> None:
        if route_mode != "current_target_missing_route_ref":
            self._base._seed_demo_topic(topic_slug=topic_slug, route_mode=route_mode)
            return

        self._base._seed_demo_topic(topic_slug=topic_slug, route_mode="current_target")
        contract_path = self.kernel_root / "topics" / topic_slug / "runtime" / "research_question.contract.json"
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        payload["question"] = "Has the committed route become the authoritative bounded truth surface yet?"
        payload["scope"] = [
            "Keep route transition authority bounded to explicit commitment and current topic truth surfaces."
        ]
        payload["non_goals"] = [
            "Do not auto-assert route authority or mutate runtime state in this slice."
        ]
        payload["observables"] = [
            "Route transition authority should stay explicit on the active topic surface."
        ]
        payload["deliverables"] = [
            "Keep route transition authority durable on the active topic surface."
        ]
        payload["acceptance_tests"] = [
            "Runtime status and replay expose route transition authority directly."
        ]
        payload["forbidden_proxies"] = [
            "Do not infer route transition authority from prose-only notes."
        ]
        payload["uncertainty_markers"] = [
            "The committed route may still lack aligned current-topic truth surfaces."
        ]
        payload["competing_hypotheses"][0]["summary"] = (
            "The symmetry-breaking route is active, but its durable route ref still points at transition history instead of a current-topic truth surface."
        )
        payload["competing_hypotheses"][0]["route_target_ref"] = (
            f"topics/{topic_slug}/runtime/transition_history.md"
        )
        contract_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    def test_no_authority_when_no_commitment_is_active(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-no-authority", route_mode="current_weak")
        status_payload = self.service.topic_status(topic_slug="demo-topic-no-authority")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-no-authority")["payload"]

        authority = status_payload["active_research_contract"]["route_transition_authority"]
        self.assertEqual(authority["authority_status"], "none")
        self.assertEqual(authority["authority_kind"], "none")
        self.assertEqual(replay_payload["route_transition_authority"]["authority_status"], "none")
        self.assertEqual(replay_payload["current_position"]["route_transition_authority_status"], "none")
        self.assertEqual(replay_payload["conclusions"]["route_transition_authority_status"], "none")

    def test_authority_waits_while_commitment_is_not_ready(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-authority-waiting", route_mode="deferred_target")
        status_payload = self.service.topic_status(topic_slug="demo-topic-authority-waiting")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-authority-waiting")["payload"]

        authority = status_payload["active_research_contract"]["route_transition_authority"]
        self.assertEqual(authority["authority_status"], "waiting_commitment")
        self.assertEqual(authority["authority_kind"], "commitment_not_ready")
        self.assertEqual(replay_payload["route_transition_authority"]["authority_status"], "waiting_commitment")

    def test_authority_pending_when_route_target_ref_is_not_current_topic_truth_surface(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-authority-pending", route_mode="current_target_missing_route_ref")
        status_payload = self.service.topic_status(topic_slug="demo-topic-authority-pending")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-authority-pending")["payload"]

        authority = status_payload["active_research_contract"]["route_transition_authority"]
        self.assertEqual(authority["authority_status"], "pending_authority")
        self.assertEqual(authority["authority_kind"], "authority_ref_not_current_topic")
        self.assertEqual(authority["route_kind"], "current_topic")
        self.assertIn("transition_history.md", authority["route_target_ref"])
        self.assertEqual(replay_payload["route_transition_authority"]["authority_status"], "pending_authority")

    def test_authority_visible_when_current_topic_truth_surfaces_align(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-authority-authoritative", route_mode="current_target")
        status_payload = self.service.topic_status(topic_slug="demo-topic-authority-authoritative")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-authority-authoritative")["payload"]

        authority = status_payload["active_research_contract"]["route_transition_authority"]
        self.assertEqual(authority["authority_status"], "authoritative")
        self.assertEqual(authority["authority_kind"], "current_topic_authoritative")
        self.assertEqual(authority["route_kind"], "current_topic")
        self.assertIn("topics/demo-topic-authority-authoritative/runtime/", authority["authority_ref"])
        self.assertEqual(replay_payload["route_transition_authority"]["authority_status"], "authoritative")
        self.assertEqual(replay_payload["current_position"]["route_transition_authority_status"], "authoritative")
        self.assertEqual(replay_payload["conclusions"]["route_transition_authority_status"], "authoritative")


if __name__ == "__main__":
    unittest.main()
