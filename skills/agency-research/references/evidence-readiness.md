# Evidence-readiness handoff

Research emits one `evidence_readiness` object per run. The object is the contract
between research and downstream ideation, storyboard, and content work.

```json
{
  "evidence_readiness": "blocked | provisional | ready",
  "audience": {"status": "supported|provisional|stale|unreliable|missing", "evidence_ids": [], "notes": ""},
  "problem": {"status": "supported|provisional|stale|unreliable|missing", "evidence_ids": [], "notes": ""},
  "proposition": {"status": "supported|provisional|stale|unreliable|missing", "evidence_ids": [], "notes": ""},
  "differentiation": {"status": "supported|provisional|stale|unreliable|missing", "evidence_ids": [], "notes": ""},
  "constraints": {"status": "supported|provisional|stale|unreliable|missing", "evidence_ids": [], "notes": ""},
  "supported_claims": [],
  "stale_inputs": [],
  "irrelevant_or_unreliable": [],
  "missing_inputs": [],
  "assumptions": [],
  "recommended_next_step": ""
}
```

`blocked` stops dependent concept and execution work. `provisional` permits labelled
hypotheses with tests. `ready` means the next decision has adequate support, not that
every marketing claim is proven.
