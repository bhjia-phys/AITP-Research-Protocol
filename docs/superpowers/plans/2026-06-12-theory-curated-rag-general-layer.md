# Theory Curated RAG General Layer Plan

## Goal

Build a conservative AITP general-layer curated RAG shelf for theoretical
physics. The shelf should improve object discovery and source backtrace for new
research topics, while preserving the v5 trust boundary:

- AITP remains the canonical typed store.
- Curated RAG retrieval is `heuristic_context` only.
- A retrieved chunk cannot be evidence, validation, final-gate satisfaction, or
  claim-trust input unless the underlying source passage is promoted through
  normal AITP records.

The first implemented fixture is deliberately small. It stores source identities
and short orientation summaries for open lecture/review shelves, not copied
lecture text.

## Current Implementation

Implemented kernel surface:

- `brain/v5/curated_rag_corpus.py`
- `brain/v5/curated_rag_contracts.py`
- `brain/v5/runtime_bridge_targets.py`
- tests in `tests/test_v5_adapters.py`

Public surfaces:

- `curated_rag_corpus`
- `curated_rag_search_result`
- `curated_rag_chunk`
- `curated_rag_promotion_draft`
- `curated_rag_ingest_result`

The default fixture now includes:

- `curated_rag_doc:open_theory_lecture_shelf`
- `curated_rag_doc:open_ads_holography_orientation`
- `curated_rag_chunk:open_theory_lecture_shelf:0001`
- `curated_rag_chunk:open_theory_lecture_shelf:0002`
- `curated_rag_chunk:open_ads_holography_orientation:0001`

The lexical search path now tokenizes punctuation-separated physics terms,
searches document tags/domain hints/topic hints/title/source URI/anchor terms,
and keeps all retrieval outputs orientation-only.

## Why This Is Not Plain RAG

Theory work fails if retrieval returns plausible text but misses the physical
objects. The general layer therefore optimizes for object discovery before
answer generation:

- dynamical degrees of freedom;
- background geometry, lattice, or medium;
- control parameters and regimes;
- boundary, source, sink, bath, detector, and cutoff terms;
- observables such as survival probability, hitting time, current, energy flux,
  response, and correlation functions;
- constraints, limits, checks, and failure modes;
- diagnostics such as spectra, normal modes, or poles only when they are
  actually primary.

This differs from trusted AITP memory. A curated chunk is a pointer saying
"look here and ask these questions." A trusted claim still needs typed source
asset, reference location, evidence, validation, and trust preflight records.

## RAG Architecture Direction

The current fixture is deterministic lexical retrieval because it is stable,
testable, and dependency-light. The planned production path is layered:

1. Lexical baseline:
   BM25-style lexical indexes plus explicit field boosts for source, title,
   domain, topic, anchor, equation labels, and physical-object tags.

2. Hybrid retrieval:
   Combine lexical, dense, and formula-aware rankings using RRF-like rank
   fusion. This is a good default because high-quality theory queries contain
   both exact terms (`AdS`, `Klein-Gordon`, `flux`) and fuzzy conceptual
   targets.

3. Scientific reranking:
   Add late-interaction or domain rerankers only after the manifest contract is
   stable. They should rerank candidates; they should not change trust state.

4. Equation-aware chunking:
   Chunk TeX/Markdown/PDF sources around definitions, displayed equations,
   theorem/proposition labels, derivation steps, examples, figures, and
   bibliography anchors. Store equation labels and nearby prose as fields, not
   opaque text blobs.

5. Graph-oriented sensemaking:
   Build a read-only concept graph over source assets, chunks, physical
   objects, regimes, assumptions, observables, and known checks. Use it for
   source backtrace and object discovery. Promotion to typed AITP truth remains
   separate.

6. Query expansion and HyDE:
   Generated expansions can help sparse new topics, but their generated text is
   never evidence. It may only produce candidate retrieval queries.

## Open Source Shelf Candidates

Initial high-quality open orientation sources:

- David Tong lecture notes: broad theory shelf spanning classical mechanics,
  QFT, gauge theory, statistical physics, GR, string theory, solitons, and
  related topics. Source: https://davidtong.org/teaching/
- Sean Carroll GR notes: graduate general relativity notes with chapters on
  geometry, curvature, geodesics, black holes, cosmology, and related basics.
  Source: https://www.preposterousuniverse.com/grnotes/
- John Preskill Physics 229 / Ph219 notes: quantum information, measurement,
  evolution, decoherence, error correction, and computation. Source:
  https://www.preskill.caltech.edu/ph229/
- Sean Hartnoll holographic methods notes: AdS/CFT transport-oriented lecture
  review. Source: https://arxiv.org/abs/0903.3246
- John McGreevy holographic duality notes: AdS/CFT introduction aimed at
  many-body/condensed-matter readers. Source: https://arxiv.org/abs/0909.0518

Ingestion rule:

- Store stable source identity, local asset hash, source URI, license/open
  access note, short orientation summary, and chunk role.
- Do not ingest copyrighted books wholesale.
- Do not copy large passages into the fixture.
- Promote exact passages only through normal AITP source and evidence records.

## Research Basis

Relevant retrieval literature and design implications:

- RAG introduced the explicit parametric plus non-parametric memory pattern for
  knowledge-intensive generation: https://arxiv.org/abs/2005.11401
- RRF gives a simple unsupervised method for combining rankings:
  https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
- ColBERT-style late interaction is a plausible later reranking layer:
  https://arxiv.org/abs/2004.12832
- GraphRAG motivates graph indexes and community summaries for global
  sensemaking questions: https://arxiv.org/abs/2404.16130
- HyDE motivates generated query documents for zero-shot retrieval, with the
  important caveat that generated details may be false:
  https://arxiv.org/abs/2212.10496
- Mathematical information retrieval and Tangent-style formula search motivate
  formula-aware fields and equation-local chunking:
  https://arxiv.org/abs/2408.11646 and https://arxiv.org/abs/1507.06235

## Next Implementation Slices

1. Expand the fixture into a versioned `source_shelf` manifest:
   source id, source URI, local asset id when available, license/access note,
   topic/domain tags, and curation rationale.

2. Add chunk roles:
   `definition_orientation`, `method_orientation`, `object_discovery_lens`,
   `known_limit`, `derivation_map`, `source_backtrace_suggestion`,
   `formula_anchor`.

3. Add equation fields:
   equation labels, nearby symbols, assumptions, and physical-object links.

4. Add hybrid index metadata:
   lexical index stays canonical for tests; optional dense/formula indexes are
   sidecar acceleration layers with hashes and stale-index diagnostics.

5. Add graph projection:
   read-only object/source graph for discovery, with no trust mutation.

6. Add eval fixtures:
   the AdS massive-matter random boundary task remains a regression case focused
   on massive matter, cutoff wall, survival, hitting time, and energy flux.
   Normal modes are auxiliary diagnostics only.

