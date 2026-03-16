# Worked example: decomposing one paper result into Layer 2 objects

This example is illustrative.
It shows the shape of writeback, not a claim that these exact objects are already canonical.

## Starting point

Suppose a paper-level result says:

> In the large-`c`, semiclassical AdS/CFT regime, interval entanglement entropy is controlled at leading order by the minimal bulk saddle, with phase transitions when competing saddles exchange dominance.

Do not write this back as one broad paper summary.
Decompose it into reusable units.

## 1. `concept`

```json
{
  "id": "concept:rt-minimal-saddle",
  "unit_type": "concept",
  "title": "Ryu-Takayanagi minimal saddle dominance",
  "payload": {
    "definition": "Leading-order interval entropy is controlled by the minimal admissible bulk saddle in the stated semiclassical regime.",
    "key_distinctions": [
      "leading-order vs finite-c corrections",
      "single dominant saddle vs saddle-transition regime"
    ],
    "canonical_examples": [
      "single interval in static AdS backgrounds"
    ]
  }
}
```

## 2. `claim_card`

```json
{
  "id": "claim_card:rt-leading-order-entropy",
  "unit_type": "claim_card",
  "title": "Leading interval entropy follows the minimal saddle in the semiclassical regime",
  "payload": {
    "claim": "At leading order in the large-c semiclassical regime, interval entanglement entropy tracks the minimal admissible bulk saddle.",
    "confidence_note": "Validated only in the stated regime.",
    "supporting_evidence": [
      "replica-trick derivation",
      "consistency with known static examples"
    ],
    "counterpoints_or_limits": [
      "finite-c corrections can alter the conclusion",
      "phase-transition points require explicit comparison of competing saddles"
    ]
  }
}
```

## 3. `derivation_object`

```json
{
  "id": "derivation_object:rt-leading-order-interval-entropy",
  "unit_type": "derivation_object",
  "title": "Semi-formal route from replica setup to minimal-saddle entropy",
  "payload": {
    "goal": "Explain why the leading entropy term is controlled by the minimal saddle.",
    "inputs": [
      "concept:replica-trick",
      "concept:semiclassical-bulk-limit"
    ],
    "ordered_steps": [
      "Express entropy through the replica construction.",
      "Map the replicated boundary problem to admissible bulk saddles.",
      "Take the large-c semiclassical limit so the least-action saddle dominates.",
      "Relate the dominant saddle area to the leading entropy term."
    ],
    "gap_markers": [
      "Full justification of subleading corrections omitted."
    ],
    "rigor_status": "semi_formal",
    "reusable_intermediate_results": [
      "saddle-dominance heuristic"
    ],
    "fragility_points": [
      "competing saddles near transition points"
    ]
  }
}
```

## 4. `validation_pattern`

```json
{
  "id": "validation_pattern:rt-saddle-competition-check",
  "unit_type": "validation_pattern",
  "title": "Check for saddle-competition phase transitions before canonicalizing an entropy claim",
  "payload": {
    "target_object_types": [
      "claim_card",
      "derivation_object"
    ],
    "validation_question": "Does the stated entropy claim remain valid when competing saddles are compared explicitly?",
    "required_inputs": [
      "candidate derivation",
      "regime assumptions",
      "saddle comparison data"
    ],
    "check_steps": [
      "Enumerate admissible saddles in the stated regime.",
      "Compare dominance conditions.",
      "Mark transition points where the leading saddle changes."
    ],
    "pass_conditions": [
      "No hidden competing saddle invalidates the claim inside the declared scope."
    ],
    "failure_signals": [
      "dominant saddle changes inside the claimed scope"
    ]
  }
}
```

## 5. `warning_note`

```json
{
  "id": "warning_note:rt-phase-transition-scope-creep",
  "unit_type": "warning_note",
  "title": "Do not state minimal-saddle dominance without checking transition points",
  "payload": {
    "warning": "Minimal-saddle statements are easy to overgeneralize across phase-transition boundaries.",
    "trigger_conditions": [
      "multiple admissible saddles",
      "parameter scan across topology changes"
    ],
    "symptoms": [
      "claimed entropy formula fails abruptly in a nearby regime"
    ],
    "mitigation": [
      "run validation_pattern:rt-saddle-competition-check before promotion"
    ]
  }
}
```

## Optional sixth object: `bridge`

If the run also clarified a structural mapping between bulk minimal surfaces and tensor-network minimal cuts, promote that separately as a `bridge`.
Do not bury that connection inside the derivation object.

## Design lesson

The canonical writeback is not “paper summary: RT formula.”
The canonical writeback is a typed bundle of reusable units with different downstream uses.
