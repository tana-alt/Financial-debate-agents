# Workflow Agent Handoff

## Scope

この要項書は、workflow 実装側へ渡す専門エージェント構成と実行順序を定義する。インターン課題の提出スコープとして、AGENTS.md にある主要な専門エージェント境界は完成対象に含める。

実装対象から外すのは、独立エージェントである必要が薄いものだけに限定する。

- `RiskAgent` は独立させない。各分析Agentの `counter_evidence` / `risks` と `BearAgent` に吸収する。
- `EvalAgent` は独立させない。最終評価は `JudgeAgent` に一本化する。
- `ReportAgent` は独立LLMにしない。Markdown生成は Python renderer にする。
- `DataIngestionAgent` は作らない。外部取得、計算、sectioning は Python workflow にする。

## Workflow

```text
RunSpec
  - ticker
  - fiscal_quarter
  - source URLs or local source files

        ↓

Data Ingestion / Normalization  [Python]
  - fetch financial API data
  - fetch filing / presentation / transcript
  - split documents into typed DocumentSection objects
  - calculate EPS surprise, revenue surprise, margins, CFO, FCF, CapEx, liquidity values
  - output FinancialSnapshot + DocumentSections + SourceIndex

        ↓

Financial Agents  [parallel LLM calls]
  - EPSQualityAnalyst
  - ProfitabilityAnalyst
  - CashFlowFcfAnalyst
  - BalanceSheetRiskAnalyst

        ↓

Presentation Agents  [parallel LLM calls]
  - ManagementIntentAnalyst
  - GuidanceAnalyst

        ↓

Evidence Aggregation  [Python]
  - validate all findings with Pydantic
- reject missing source_ref
- reject empty counter_evidence unless the agent explicitly records the lack of
  available counter evidence in missing_data and caps confidence at 0.6
  - compress findings into AnalysisBrief

        ↓

Debate Agents
  - BullAgent
  - build compact BullCaseSummary  [Python]
  - BearAgent(with BullCaseSummary)

        ↓

JudgeAgent
  - label: good | neutral | bad
  - confidence
  - positive_evidence
  - negative_evidence
  - eps_outlook
  - fcf_outlook

        ↓

MarkdownRenderer  [Python]
  - input: MarkdownRendererInput = RunSpec + FinalVerdict + SourceIndex(optional)
  - deterministic report formatting
```

`BullAgent -> BearAgent(with BullCaseSummary) -> JudgeAgent` is fixed. Bull and
Bear are intentionally sequential, not parallel, so the debate structure is
visible and Bear can directly challenge the strongest Bull case.

## Agent List

| Agent | Purpose | Input Context | Output |
| --- | --- | --- | --- |
| `EPSQualityAnalyst` | EPS surprise の質と持続性を見る | EPS actual/consensus/surprise, tax/share count/one-time item sections | `EPSQualityFinding` |
| `ProfitabilityAnalyst` | 売上品質、利益率、営業レバレッジ、segment mix を見る | revenue, gross margin, operating margin, segment sections | `ProfitabilityFinding` |
| `CashFlowFcfAnalyst` | CFO、FCF、CapEx、working capital を見る | CFO, FCF, CapEx, working capital, liquidity/capital resources sections | `CashFlowFcfFinding` |
| `BalanceSheetRiskAnalyst` | 流動性、負債、満期、資金調達制約を見る | cash, debt, liquidity, maturity, interest burden sections | `BalanceSheetRiskFinding` |
| `ManagementIntentAnalyst` | 経営陣の意図、投資判断、時間軸を読む | strategy, MD&A, CEO/CFO commentary, management sections | `ManagementIntentFinding` |
| `GuidanceAnalyst` | guidance と consensus の差分、前提、revision risk を見る | guidance sections, precomputed consensus deltas, assumptions | `GuidanceFinding` |
| `BullAgent` | good と判断できる最強ケースを作る | validated `AnalysisBrief` | `BullCase` |
| `BearAgent` | bad/neutral と判断すべき最強ケースを作る | validated `AnalysisBrief`, `BullCaseSummary` | `BearCase` |
| `JudgeAgent` | good/neutral/bad を構造化判定する | `AnalysisBrief`, `BullCase`, `BearCase` | `FinalVerdict` |

## Context Routing

各Agentに全文を渡さない。workflow は `DocumentSection.section_type` と `source_ref` を使って、必要な section だけを渡す。

```text
EPSQualityAnalyst:
  - eps
  - margin only when EPS driver
  - one_time_item
  - tax / share_count if available

ProfitabilityAnalyst:
  - revenue
  - margin
  - segment
  - operating_expense

CashFlowFcfAnalyst:
  - cash_flow
  - capex
  - working_capital
  - liquidity when tied to cash generation

BalanceSheetRiskAnalyst:
  - balance_sheet
  - liquidity
  - debt
  - maturity
  - capital_resources

ManagementIntentAnalyst:
  - management_commentary
  - strategy
  - mdna
  - risk when tied to management actions

GuidanceAnalyst:
  - guidance
  - outlook
  - guidance_assumptions
  - precomputed consensus deltas
```

## Context Isolation Rationale

- `EPSQualityAnalyst`: EPS は会計利益の質を評価するため、EPS surprise、税率、株数、一時要因に限定する。
- `ProfitabilityAnalyst`: P&L は営業構造を評価するため、売上、利益率、segment mix、opex に限定する。
- `CashFlowFcfAnalyst`: CFS は現金創出力を評価するため、CFO、FCF、CapEx、working capital に限定する。
- `BalanceSheetRiskAnalyst`: BS は財務制約を評価するため、現金、負債、満期、金利負担、流動性に限定する。
- `ManagementIntentAnalyst`: Management は経営意図を評価するため、戦略、投資判断、CEO/CFO commentary に限定する。
- `GuidanceAnalyst`: Guidance は将来数値目標の妥当性を評価するため、guidance、前提、consensus delta に限定する。
- `BullAgent` / `BearAgent`: 反対方向の主張を分離し、肯定根拠と否定根拠を独立して強くする。
- `JudgeAgent`: 最終構造化判定のみを担当し、Markdown 生成や追加調査を行わない。

## Required Models

Core models:

```python
RunSpec
FinancialSnapshot
DocumentSection
SourceIndex
EvidenceItem
```

`EvidenceItem` minimal fields:

```python
EvidenceItem:
  source_ref: str
  source_type: str
  metric: str | None
  period: str | None
  quote_or_value: str
  interpretation: str
```

Specialist outputs:

```python
EPSQualityFinding
ProfitabilityFinding
CashFlowFcfFinding
BalanceSheetRiskFinding
ManagementIntentFinding
GuidanceFinding
AnalysisBrief
BullCase
BearCase
FinalVerdict
```

Debate coverage field:

```python
finding_coverage: dict[
  Literal[
    "eps_quality",
    "profitability",
    "cash_flow_fcf",
    "balance_sheet_risk",
    "management_intent",
    "guidance",
  ],
  Literal["supporting", "opposing", "not_material", "missing"],
]
```

`supporting` / `opposing` are relative to the current debate agent's thesis.

Renderer input:

```python
MarkdownRendererInput = RunSpec + FinalVerdict + SourceIndex(optional)
```

## Validation Gates

Before aggregation:

- Pydantic validation must pass.
- `confidence` must be `0.0 <= confidence <= 1.0`.
- Evidence items must include `source_ref`.
- Agents must not output stock forecasts, target prices, or trading advice.
- Agents must not calculate metrics from raw values.
- Run a banned phrase scan for investment-advice language such as `buy`, `sell`,
  `hold`, `target price`, `price target`, `undervalued`, and `overvalued`.
  Treat this as a review gate, not a blind reject, because terms such as `buy`
  can appear as ordinary words in source text.

Before Judge:

- `AnalysisBrief` must include all six specialist findings.
- Positive and negative evidence pools must both be non-empty.
- `BullCase.strongest_positive_evidence` must be non-empty.
- `BullCase.finding_coverage` and `BearCase.finding_coverage` must include all six specialist keys.
- `BullCase.weak_points` must be non-empty.
- `BearCase.strongest_negative_evidence` must be non-empty.
- `BearCase.counter_to_bull_case` must be non-empty.
- Judge should prefer `neutral` when Bull and Bear are close.
- Judge should prefer `neutral` when EPS outlook and FCF outlook point in opposite directions.
- Important missing data should cap final confidence.
- Missing or unclear important findings should cap final confidence and bias toward `neutral`.
- `bad` requires negative evidence to clearly outweigh positive evidence, not merely one weak dimension.

Before report:

- `FinalVerdict.label` must be `good | neutral | bad`.
- `FinalVerdict.positive_evidence` must be non-empty.
- `FinalVerdict.negative_evidence` must be non-empty.
- `eps_outlook_reason` and `fcf_outlook_reason` must be non-empty.
- `non_advice_disclaimer` must be present.
- `MarkdownRendererInput` must equal `RunSpec + FinalVerdict + SourceIndex(optional)`.
- Run the banned phrase scan again on rendered Markdown, with the same false-positive caution.

## Prompt References

Use these files as prompt bases:

- `src/prompts/financial_agents.md`
- `src/prompts/presentation_agents.md`
- `src/prompts/debate_judge_agents.md`

The workflow should load only the prompt section for the agent being called.
The three prompt files are grouped references for consistency; they do not
represent three runtime agents.
