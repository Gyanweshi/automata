---
name: agency-ideation
description: Frame marketing problems, develop propositions and differentiation, and generate campaign concepts using sourced methods from IDEO.org, Strategyzer, Blue Ocean Strategy, and Deck of Brilliance. Use for strategy or creative ideation; preserve selected positioning and concepts during execution-only work.
---

# Agency ideation

Turn a brief into concept routes that the storyboard and content skills can develop together.
This is an agent-led workflow. The selector retrieves tools; it does not generate ideas,
call an LLM, or add an ideation stage to the standalone Python pipeline.

## Context and selection

Read the brand note and its Memory before brand work. Establish the audience,
desired response, proposition, supporting evidence, format, and production constraints.
Label missing evidence as a hypothesis; a creative mechanism is not a consumer insight.
If the user supplied a selected concept, develop it without restarting brainstorming.

## Brief audit: report before ideating

If a research run is available, its `evidence_readiness` object is the authoritative
input to this audit. Preserve its evidence IDs, blockers, stale items, and confidence
when translating it into an ideation handoff. If no research object is available,
perform the fallback audit below; never assume that an absent field is supported.

Scale the audit to the decision. For a small execution request with an already
specified audience, proposition, and format (for example, "Diwali reel"), use a
one-sentence readiness note plus only material missing or risky inputs. Use the full
structured audit for a new proposition, campaign platform, competitive claim, or any
request where the research handoff is blocked or provisional. The audit should reduce
uncertainty, not become a ceremonial form before routine ideation.

Before selecting a framework or making a factual claim, audit the supplied information
and tell the user what is safe to use. Do not silently fill material gaps. Concept
generation may proceed with labelled hypotheses when the user wants exploration;
claim auditing applies when a route asserts a product, audience, market, performance,
or cultural fact.

Classify each important input as:

- **Supported:** directly relevant, sufficiently specific, and backed by a named
  source, observed data, product fact, or explicit user instruction.
- **Provisional:** plausible but unverified; carry it as a hypothesis and state what
  would confirm or reject it.
- **Stale:** potentially changed because it is outside the relevant time window or
  conflicts with current brand, market, product, or platform context. State the date
  and whether fresh verification is needed.
- **Irrelevant:** does not affect the decision being made. Exclude it from reasoning
  rather than allowing it to create false confidence.
- **Unreliable:** anonymous, contradictory, promotional, low-quality, or otherwise
  unsuitable for the claim being made. Say why and downgrade or discard it.
- **Missing:** required to make the next decision responsibly and not present in the
  brief or available research.

Return the audit using the canonical contract in
[the evidence-readiness reference](../agency-research/references/evidence-readiness.md).
For a compact execution brief, emit only the fields material to the decision while
preserving the same status vocabulary.

Use `blocked` when a missing or unreliable input would materially change a dependent
decision or make a factual claim unsafe. Ask for the smallest missing set in plain
language and pause dependent strategy work. For speculative concept generation, use
`provisional` and label the premise instead of blocking imagination. Use `ready` only
when the proposition and creative task are sufficiently supported for the requested
decision. Independent,
non-blocking research may proceed in parallel, but do not hide the audit behind it.
When research reports `blocked`, report the blockers and stop dependent concept
routes. You may propose only discovery questions or non-dependent research unless the
user explicitly requests speculative work. When it reports `provisional`, keep
assumptions visible in every route and carry the recommended test forward. Do not
downgrade a research blocker just to reach storyboard.

When source quality matters, record the source, publication or observation date,
what claim it actually supports, and whether it is primary or secondary. A recent
source is not automatically relevant or reliable; an old source is not automatically
useless. Judge it against the decision and the rate of change in that subject.

Do not use a framework to manufacture missing facts. Framework selection follows the
audit. If the user explicitly asks for speculative exploration, proceed with clearly
labelled hypotheses and explain which conclusions cannot yet be trusted.

## Claim audit, separate from concept generation

After routes exist, audit only the assertions inside them: product capability, audience
behavior, market size, performance, cultural context, and any comparative claim. Mark
each assertion supported, provisional, stale, unreliable, irrelevant, or missing;
attach evidence IDs where needed; and rewrite unsupported assertions as hypotheses or
remove them. A concept can remain creatively useful while one of its claims is unsafe.

Read [references/agency-bank.json](references/agency-bank.json), or retrieve a small relevant set:

```powershell
.\.venv\Scripts\python.exe skills/agency-ideation/scripts/select_tools.py --tag community --limit 5
.\.venv\Scripts\python.exe skills/agency-ideation/scripts/select_tools.py --id es-08 --id es-13
.\.venv\Scripts\python.exe skills/agency-ideation/scripts/select_tools.py --altitude platform --limit 6
```

The helper accepts repeatable `--tag`, `--id`, and `--exclude` arguments plus
`--altitude platform|campaign|execution`. Altitude distinguishes a repeatable
organizing platform from a bounded campaign route and a single execution device.
Tags match
any supplied tag; exclusions apply after filtering. No matching entries means an
empty result, not permission to invent a sourced entry. Use `--list` for an index
with attribution, `--list-tags` for the closed tag vocabulary and
counts, or `--validate` to check the bank. Run from the repo root with its `.venv`.

The default bank is the compact agency-authored `agency-bank.json` with 23 stable
`es-*` IDs, a closed tag vocabulary, six families, and near-twin pairing rules. The
previous authenticated Deck index has been retired. For an old `dob-*` handoff or an
explicit request for the historical pilot, read
[references/historical-bank.json](references/historical-bank.json) or use
`--historical --id dob-03`. Historical IDs are not aliases for current tool numbers.
`related_historical_ids` indicates conceptual overlap, not exact equivalence. Avoid
mixing overlapping current and historical entries merely to inflate route count.

Select mechanisms from relevant families, usually 4-6 for a normal brainstorm. Avoid
near-twin pairs unless the brief explicitly needs both treatments; use
`--allow-near-twins` when explicitly selecting both IDs. Broad browsing and altitude
surveys return a `near_twin_warning` in the payload rather than failing retrieval.
Use judgment about relevance; tag order and retrieval position are not creative scores.
Check recent run JSON and brand Memory for overused or rejected routes when available.
Use the framework routing below when the brief needs strategic development. Consult
[references/resources.json](references/resources.json) for source coverage; only
entries explicitly marked integrated have local method instructions.

## Route by the missing decision

Read [references/frameworks.json](references/frameworks.json), or use:

```powershell
.\.venv\Scripts\python.exe skills/agency-ideation/scripts/select_tools.py --frameworks --stage insight
.\.venv\Scripts\python.exe skills/agency-ideation/scripts/select_tools.py --frameworks --id strategyzer-vpc
```

`--frameworks` and `--historical` are mutually exclusive. `--stage` is available only
with `--frameworks`; use `--frameworks --list` to see all integrated methods.

| Missing decision | Methods | Carry forward |
| --- | --- | --- |
| What matters to this audience? | IDEO Find Themes; Blue Ocean Three Tiers of Noncustomers | Evidence-linked themes, barriers, unknowns |
| How will the brand be remembered and recognized? | Ehrenberg-Bass Distinctive Brand Assets and Mental Availability | Category entry points, consistent assets, reach and measurement gaps |
| What problem are we solving? | IDEO How Might We | Bounded opportunity question |
| What value can we credibly offer? | Strategyzer Value Proposition Canvas | Prioritized needs, capabilities, proposition |
| How should the offer differ? | Blue Ocean Strategy Canvas; Four Actions Framework | Competitive baseline, proposed changes, costs to check |
| How do we express it? | Agency creative mechanisms | Distinct creative concepts |
| What can we execute or test? | IDEO Gut Check; Strategyzer Test Card | Feasible revision, hypothesis, metric, threshold |

Choose the smallest set needed; existing research or approved positioning may already
answer earlier questions. Preserve evidence IDs for audience observations, competitor
claims, and product capabilities. Distinguish observations from interpretations and
untested assumptions. No framework validates a proposition by being filled in. A Test
Card is a plan until executed; selecting it does not authorize recruiting participants
or spending on ads. Proposed offer changes remain proposals until confirmed as
deliverable, and downstream copy must not advertise them as existing features.

The mechanism bank is scoped to communication and content moves: message, format,
story, participation, and execution. It does not recommend pricing, product,
distribution, or policy changes unless the user explicitly expands the brief and the
relevant capability is confirmed.

## Generate and evaluate

Apply each mechanism to the same proposition. Develop a concrete audience situation,
an unexpected turn, the brand's necessary role, and a possible execution. An alternate
headline on the same situation is a variation, not a distinct concept.

The runtime bank is agency-authored and does not require Deck login or source refresh.
The archived source index is not a license to reproduce campaign examples or scrape
authenticated pages. Never put credentials, cookies, or account details in the bank.

Evaluate routes with this priority order: (1) strategic or communication objective,
(2) brand recognition and distinctiveness, (3) audience meaning, (4) clarity and
format fit, then (5) feasibility. Feasibility breaks ties between otherwise strong
routes; it does not automatically defeat a stronger idea. Explain tradeoffs rather
than predicting performance from subjective scores. Reject concepts whose idea
survives replacing the brand with any competitor without meaningful change. For each
shortlisted route, identify the assumption worth testing and a practical test.

Before handoff, add a craft pass: opening beat or first-frame promise, progression,
payoff, pacing/length, casting or point of view, sound or silence where relevant,
brand cue timing, and the exact audience action. Craft choices must preserve the
concept rather than decorate it.

For platform- or campaign-altitude routes, add a campaign-architecture pass:

- **Duration/flighting:** burst, always-on, seasonal return, or a defined launch window.
- **Channel roles:** what Instagram, LinkedIn, YouTube, PR, events, or offline each
  contributes without changing the central meaning.
- **Message hierarchy:** one central message, supporting proof, and optional reasons
  to believe; do not let channel variants become unrelated claims.
- **Distribution thought:** priority buying situations, reach assumptions, and what
  evidence or media planning is still needed. A strong idea without a route to enough
  relevant people is incomplete, but this bank does not perform media planning.

## Handoff

Give each concept an ID and retain its `tool_ids`. Use this structure in run JSON:

```json
{
  "brand_slug": "example-brand",
  "brief": {"audience": "", "objective": "", "proposition": "", "evidence": [], "constraints": []},
  "evidence_readiness": {},
  "research_run_id": null,
  "bank_version": "1.0.0",
  "framework_bank_version": "1.1.0",
  "campaign_architecture": {"duration_or_flighting": "", "channel_roles": [], "message_hierarchy": {"central": "", "support": [], "proof": []}, "distribution_thought": ""},
  "concepts": [{"concept_id": "route-01", "tool_ids": ["es-08"], "idea": "", "brand_role": "", "execution": "", "assumptions": [], "evaluation": "", "test": ""}],
  "recommended_concept_id": "route-01",
  "selected_concept_id": null,
  "selection_basis": null
}
```

A recommendation is not user approval. If the task authorizes choosing a route and
continuing, record `selection_basis: "agent choice within requested scope"`; otherwise
present the shortlist. Pass the same concept ID, proposition, brand role, and tool IDs
to storyboard and content. Reconcile CLI scaffold outputs with this handoff: the
existing Python generators do not consume the concept JSON automatically.

Write human-readable brainstorms as vault drafts under
`Brands/<slug>/Drafts/Ideation/`, with required frontmatter and a concise Memory section.
Keep structured runs under `workspace/<slug>/ideation/`. Follow the repo's existing
finalization gate for canonical brand Memory and final notes; do not update them just
because the brainstorm or downstream execution finished.
