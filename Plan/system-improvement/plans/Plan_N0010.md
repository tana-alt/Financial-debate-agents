---
plan_id: Plan_N0010
project_id: system-improvement
status: completed
log_ref: Plan/system-improvement/logs/Plan_N0010.log.md
---

# Claim Matrix Density Plan

## 0. Goal

Define a dense but bounded matrix design that makes the final report
fact-checkable without asking agents to write more prose.

The matrix must let a reader distinguish:

- fact vs interpretation vs implication;
- current-period fact vs forward-looking assumption;
- directly checkable source-backed statements vs management claims vs model
  interpretation;
- evidence used by specialists vs evidence adopted or rejected by Judge.

## 1. Scope And Write Targets

Allowed write targets:

```text
Plan/system-improvement/index.yaml
Plan/system-improvement/plans/Plan_N0010.md
Plan/system-improvement/logs/Plan_N0010.log.md
```

No artifact output is created.

## 2. Design Verdict

- `design_verdict`: proceed
- `architecture_significance`: significant
- `selected_option`: separate report reasoning into `EvidenceItem`,
  `ClaimRecord`, and `DecisionUse`.
- `core_principle`: preserve density by limiting the number of material claims,
  not by allowing long free-form agent prose.

## 3. Problem

The current report can contain correct evidence and still be hard to audit. A
reader needs to know whether a sentence is:

- a reported fact;
- a derived metric;
- a management statement;
- an agent interpretation;
- a risk assessment;
- a forward-looking assumption;
- a missing-data caveat.

If these are mixed in one paragraph, the report may look fluent but becomes hard
to verify. The goal is not to make the report longer. The goal is to make each
important claim traceable.

## 4. Three-Layer Model

### EvidenceItem: Fact-Check Unit

`EvidenceItem` should represent the smallest checkable basis.

It answers:

- what source or metric supports this;
- what exact value or quote is being used;
- when the source applies;
- whether the item is directly verifiable.

Recommended fields:

```text
evidence_id
source_ref
source_quote
reported_value
reported_unit
metric_name
comparator_value
delta
delta_pct
source_date
reported_period
as_of_date
fact_check_status
```

`EvidenceItem` should not carry the full investment-style conclusion. It is the
evidence base.

### ClaimRecord: Agent Interpretation Unit

`ClaimRecord` should represent one material analytical claim created from one or
more evidence items.

It answers:

- what the agent claims;
- whether it is fact, interpretation, risk, or forward assumption;
- which evidence supports it;
- what counter evidence challenges it;
- what implication it has for EPS, FCF, guidance, or overall verdict.

Recommended fields:

```text
claim_id
agent_name
claim_text
claim_type
time_scope
evidence_ids
counter_evidence_ids
fact_check_status
interpretation
implication
impact_areas
confidence
limitations
```

Agents should produce only the top material claims. A default cap of three to
five claims per specialist is enough for a dense report.

### DecisionUse: Judge Usage Unit

`DecisionUse` should represent how the final Judge used or rejected a claim.

It answers:

- whether the claim was adopted, rejected, discounted, or left unresolved;
- why it affected the verdict;
- which evidence was decisive;
- how it affected confidence.

Recommended fields:

```text
claim_id
decision_role
judge_treatment
decisive_evidence_ids
counter_evidence_ids
rationale
confidence_impact
verdict_impact
```

The final report should make it obvious which claims moved the verdict and
which claims were present but discounted.

## 5. Controlled Vocabularies

### claim_type

```text
reported_fact
derived_metric
management_statement
analyst_interpretation
risk_assessment
forward_looking_assumption
missing_data_caveat
```

### fact_check_status

```text
directly_supported
derived_from_precomputed_metric
management_claim_only
partially_supported
not_directly_verifiable
missing_source
```

### time_scope

Recommended structure:

```text
reported_period
source_date
as_of_date
forward_horizon
```

`forward_horizon` examples:

```text
current_quarter
next_quarter
fiscal_year
medium_term
unclear
```

### judge_treatment

```text
adopted
discounted
rejected
unresolved
used_as_risk
used_as_caveat
```

## 6. Density Rules

Density should come from selection and structure, not volume.

Rules:

- each specialist emits at most three to five material `ClaimRecord` items;
- each claim must cite at least one `EvidenceItem` or become a
  `missing_data_caveat`;
- each material claim must have `claim_type`, `time_scope`, and
  `fact_check_status`;
- interpretation and implication must be separate fields;
- forward-looking assumptions must not be marked as reported facts;
- management statements must be labeled as statements, not as verified outcomes;
- Judge must reference `claim_id`, not rewrite source facts from scratch;
- renderer shows the most material claims and can keep the full matrix in JSON.

## 7. Report Use

The visible report should not dump the full matrix. It should show the high-signal
slice:

- top adopted claims;
- top discounted or opposing claims;
- central Bull/Bear dispute;
- material missing-data caveats;
- source appendix and fact-check status.

Recommended report table:

```text
| Claim | Type | Time | Basis | Fact-check | Interpretation | Judge use |
|---|---|---|---|---|---|---|
```

The full structured response can retain all `EvidenceItem`, `ClaimRecord`, and
`DecisionUse` rows for auditability.

## 8. Prompt Implication

Prompts should not say "write a detailed analysis." They should say:

- identify the top material claims only;
- classify each claim;
- separate evidence, interpretation, and implication;
- attach counter evidence where available;
- mark missing or unverifiable claims explicitly.

This keeps output concise while increasing report density.

## 9. Implementation Sequence

1. Add model types: `FactCheckStatus`, `ClaimType`, `TimeScope`,
   `ClaimRecord`, and `DecisionUse`.
2. Extend `EvidenceItem` or add `EvidenceBasis` fields for source quote, value,
   timing, comparator, and fact-check status.
3. Add backward-compatible adapters from old `EvidenceItem.summary/detail` into
   new claim fields for tests and fake provider fixtures.
4. Update specialist schemas to emit capped `ClaimRecord` lists.
5. Update Bull/Bear schemas to organize claims into disputes.
6. Update Judge schema to emit `DecisionUse` and a decision matrix.
7. Update renderer to show a compact matrix slice and preserve full structured
   matrix in JSON response.
8. Update prompts to request classified claims, not longer prose.

## 10. Tests

Add tests for:

- every `ClaimRecord` has `claim_type`, `time_scope`, `fact_check_status`, and
  at least one evidence link or missing-data caveat;
- forward-looking assumptions cannot be labeled as reported facts;
- management statements are not treated as verified outcomes;
- each `DecisionUse.claim_id` points to an existing `ClaimRecord`;
- Judge adopted claims appear in the report matrix;
- discounted/rejected claims appear in Bull/Bear tension or uncertainty;
- renderer uses structured matrix fields rather than parsing prose;
- each specialist output is capped to the configured claim count.

## 11. Open Design Choices

- Whether to extend `EvidenceItem` directly or introduce a separate
  `EvidenceBasis` model.
- Whether `ClaimRecord` should live inside each specialist finding or in an
  aggregated `ClaimMatrix`.
- Whether the API response should expose the full matrix by default or behind an
  `include_debug_matrix` flag.

Recommended default:

- keep `EvidenceItem` as the source/value unit;
- add `ClaimRecord` to specialist outputs;
- create `ClaimMatrix` during aggregation;
- expose compact matrix in report and full matrix in JSON response.

## 12. Residual Risk

- Too many required fields can increase LLM output failure. Keep only the audit
  fields required and make secondary prose optional.
- Claim caps may hide a weak but important signal unless ranking is clear.
- Provider-native JSON Schema should reduce shape failures, but schema
  complexity still needs careful migration through fake provider fixtures.
