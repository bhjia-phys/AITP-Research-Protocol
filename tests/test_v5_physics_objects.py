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
