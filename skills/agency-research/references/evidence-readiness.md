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

## Machine-emitted handoff

Python research runs fill this object automatically (`agency_common.evidence_gate`). Each
dimension also carries a `confidence` (0-1), and the object carries a `decision` block
(`confidence`, `route`, `source`). Treat `route` as follows: `act` means proceed on the
stated status; `review` or `escalate` means a person confirms the status before downstream
work relies on it. Dry-run data is always `unreliable`, so a dry run reports `blocked`.
Every decision is appended to `workspace/_decisions/*.jsonl`; log what a person actually
decided with `DecisionLog.record_human(decision_id, answer)` so `DecisionLog.calibration()`
can show whether the confidence is earning trust.
