from __future__ import annotations

from dataclasses import asdict
import json


def test_record_physics_object_persists_typed_record(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    obj = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="hilbert_sector",
        name="N=8 Lz=28 sector",
        definition="Many-body Hilbert sector used for finite-size FQHE counting.",
        notation="H_{N=8,Lz=28}",
        assumptions=["lowest Landau level", "fixed particle number"],
        source_refs=["paper:fqhe-counting"],
        metadata={"N": 8, "Lz": 28},
    )

    fm, body = read_md(ws.registry_dir("physics_objects") / f"{obj.object_id}.md")
    assert obj.kind == "physics_object"
    assert obj.object_id.startswith("physics-object-")
    assert fm["object_type"] == "hilbert_sector"
    assert fm["assumptions"] == ["lowest Landau level", "fixed particle number"]
    assert "Many-body Hilbert sector" in body


def test_physics_object_record_is_public_surface_valid(tmp_path):
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum Gravity")
    obj = record_physics_object(
        ws,
        topic_id="qg",
        object_type="von_neumann_algebra",
        name="Local algebra A(O)",
        definition="Operator algebra associated with a spacetime region.",
    )

    payload = {"ok": True, **asdict(obj)}
    assert require_valid_public_surface("physics_object_record", payload) == payload


def test_cli_physics_object_record_returns_json(tmp_path, capsys):
    from brain.v5.cli import main

    assert main(
        [
            "--base",
            str(tmp_path),
            "object",
            "record",
            "--topic",
            "fqhe",
            "--type",
            "hilbert_sector",
            "--name",
            "N=8 sector",
            "--definition",
            "Finite-size Hilbert sector.",
            "--notation",
            "H_8",
            "--assumption",
            "lowest Landau level",
            "--source-ref",
            "paper:fqhe",
            "--metadata-json",
            '{"N":8}',
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "physics_object"
    assert payload["object_type"] == "hilbert_sector"
    assert payload["metadata"] == {"N": 8}


def test_mcp_record_physics_object_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_physics_object
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_record_physics_object(
        str(tmp_path),
        topic_id="qg",
        object_type="algebra",
        name="A(O)",
        definition="Local operator algebra.",
    )

    assert payload["ok"] is True
    assert require_valid_public_surface("physics_object_record", payload) == payload


def test_record_object_relation_links_two_physics_objects(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="edge counting sequence",
        definition="Low-lying entanglement spectrum counting.",
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Conformal field theory describing the edge.",
    )

    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="The counting sequence diagnoses the candidate edge CFT only in the correct momentum sector.",
        claim_id=claim.claim_id,
        assumptions=["sector assignment is correct"],
        failure_modes=["finite-size aliasing mimics the same sequence"],
        source_refs=["paper:fqhe-counting"],
    )

    fm, body = read_md(ws.registry_dir("object_relations") / f"{relation.relation_id}.md")
    assert relation.kind == "object_relation"
    assert relation.subject_id == counting.object_id
    assert relation.object_id == cft.object_id
    assert fm["failure_modes"] == ["finite-size aliasing mimics the same sequence"]
    assert "diagnoses" in body


def test_object_relation_record_is_public_surface_valid(tmp_path):
    from brain.v5.physics_objects import record_object_relation
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "gw", context_id="gw-methods", title="GW")
    relation = record_object_relation(
        ws,
        topic_id="gw",
        relation_type="implements",
        subject_id="object-self-energy-formula",
        object_id="object-librpa-kernel",
        statement="The kernel implements the correlation self-energy formula.",
    )

    payload = {"ok": True, **asdict(relation)}
    assert require_valid_public_surface("object_relation_record", payload) == payload


def test_cli_object_relation_record_returns_json(tmp_path, capsys):
    from brain.v5.cli import main

    assert main(
        [
            "--base",
            str(tmp_path),
            "relation",
            "record",
            "--topic",
            "fqhe",
            "--type",
            "diagnoses",
            "--subject",
            "object-counting",
            "--object",
            "object-edge-cft",
            "--statement",
            "Counting diagnoses the edge CFT in a fixed sector.",
            "--claim",
            "claim-fqhe",
            "--failure-mode",
            "finite-size aliasing",
            "--source-ref",
            "paper:fqhe",
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "object_relation"
    assert payload["failure_modes"] == ["finite-size aliasing"]


def test_mcp_record_object_relation_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_object_relation
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_record_object_relation(
        str(tmp_path),
        topic_id="gw",
        relation_type="implements",
        subject_id="object-formula",
        object_id="object-code",
        statement="The code path implements the formula.",
    )

    assert payload["ok"] is True
    assert require_valid_public_surface("object_relation_record", payload) == payload


def test_execution_brief_exposes_object_relations_for_active_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="counting sequence",
        definition="Low-lying counting data.",
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Candidate edge theory.",
    )
    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting diagnoses the edge CFT only after sector matching.",
        claim_id=claim.claim_id,
        failure_modes=["wrong momentum sector"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    relations = brief["known_context"]["object_relations"]
    assert relations == [
        {
            "relation_id": relation.relation_id,
            "relation_type": "diagnoses",
            "subject_id": counting.object_id,
            "object_id": cft.object_id,
            "statement": "Counting diagnoses the edge CFT only after sector matching.",
            "failure_modes": ["wrong momentum sector"],
            "status": "hypothesis",
        }
    ]


def test_mandatory_reflection_mentions_recorded_relation_failure_mode(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    counting = record_physics_object(ws, topic_id="fqhe", object_type="observable", name="counting", definition="Counting data.")
    cft = record_physics_object(ws, topic_id="fqhe", object_type="theory", name="edge CFT", definition="Candidate theory.")
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting diagnoses the edge CFT.",
        claim_id=claim.claim_id,
        failure_modes=["finite-size aliasing"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    questions = "\n".join(item["question"] for item in brief["mandatory_reflection"])
    assert "finite-size aliasing" in questions
