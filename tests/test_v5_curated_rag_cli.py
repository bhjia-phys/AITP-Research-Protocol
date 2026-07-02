from __future__ import annotations

import json


def test_cli_curated_rag_read_aliases_return_public_surfaces(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.public_surfaces import require_valid_public_surface

    assert main(["--base", str(tmp_path), "curated-rag", "catalog"]) == 0
    catalog_payload = json.loads(capsys.readouterr().out)
    catalog = catalog_payload["curated_rag_corpus"]
    assert require_valid_public_surface("curated_rag_corpus", catalog) == catalog
    assert catalog["kind"] == "curated_rag_corpus"

    assert main(["--base", str(tmp_path), "curated-rag", "search", "source claim evidence", "--limit", "2"]) == 0
    search_payload = json.loads(capsys.readouterr().out)
    search = search_payload["curated_rag_search_result"]
    assert require_valid_public_surface("curated_rag_search_result", search) == search
    assert search["result_role"] == "heuristic_context"

    chunk_id = search["results"][0]["chunk_id"]
    assert main(["--base", str(tmp_path), "curated-rag", "chunk", chunk_id]) == 0
    chunk_payload = json.loads(capsys.readouterr().out)
    chunk = chunk_payload["curated_rag_chunk"]
    assert require_valid_public_surface("curated_rag_chunk", chunk) == chunk
    assert chunk["chunk_id"] == chunk_id

    assert (
        main(
            [
                "--base",
                str(tmp_path),
                "curated-rag",
                "promotion-draft",
                chunk_id,
                "--topic",
                "qft-literature",
                "--claim",
                "claim-qft",
            ]
        )
        == 0
    )
    draft_payload = json.loads(capsys.readouterr().out)
    draft = draft_payload["curated_rag_promotion_draft"]
    assert require_valid_public_surface("curated_rag_promotion_draft", draft) == draft
    assert draft["chunk_id"] == chunk_id
    assert draft["draft_creates_records"] is False
