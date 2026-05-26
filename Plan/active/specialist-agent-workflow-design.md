# Specialist Agent Workflow Design

## Purpose

AGENTS.md のフローを、インターン課題として説明しやすい専門エージェント設計へ落とし込む。

前回の4 agent案は実装コストを下げるには有効だが、context engineering / context isolation の観点では粗い。インターン課題の提出物では、AGENTS.md に書かれた Financial / Presentation / Debate / Judge の専門境界を完成スコープとして扱う。

特に EPS、P&L、CFS、BS はすべて財務領域だが、見る context と失敗モードが違う。EPS は会計利益の質、P&L は売上・利益率・事業ミックス、CFS は現金創出力、BS は財務制約を見るため、独立エージェントにする。

## Design Principles

- 独立させる基準は agent 名ではなく、必要な context と判断軸が違うかどうか。
- EPS、P&L、CFS、BS は財務分析内でも判断軸が違うため、独立させる。
- EPS と FCF は良し悪しが逆方向に出ることがあるため、特に混ぜない。
- Management intent と guidance は近いが、経営方針の解釈と来期数値目標の現実性評価は別なので独立させる。
- Bull と Bear は同じ `AnalysisBrief` を見ても目的が逆なので、反対根拠を強くするため独立させる。
- Data ingestion、財務計算、document sectioning、Markdown rendering は LLM agent にしない。
- すべての agent 出力は Pydantic で検証する。
- Judge に全文資料や全文討論ログを渡さず、圧縮済みの構造化出力だけを渡す。
- `good | neutral | bad` を正式な判定ラベルにする。
- 反対根拠が空のまま report 生成へ進めない。
- 投資助言、株価予測、売買推奨に踏み込まない。

## Recommended Implementation Workflow

```text
RunSpec
  - ticker
  - fiscal quarter
  - source URLs / local documents

        ↓

Non-LLM Data Workflow
  - financial API data fetch
  - filing / presentation / transcript fetch
  - PDF / HTML / text sectioning
  - EPS surprise, revenue surprise, margins, FCF, CapEx changes
  - output: FinancialSnapshot + DocumentSections

        ↓

Financial Specialist Agents
  - EPSQualityAnalyst
  - ProfitabilityAnalyst
  - CashFlowFcfAnalyst
  - BalanceSheetRiskAnalyst

        ↓

Presentation Specialist Agents
  - ManagementIntentAnalyst
  - GuidanceAnalyst

        ↓

Evidence Aggregation
  - deterministic Python aggregation
  - output: AnalysisBrief

        ↓

Debate Agents
  - BullAgent
  - BearAgent

        ↓

Judge Agent
  - good / neutral / bad
  - confidence
  - positive evidence
  - negative evidence
  - EPS outlook
  - FCF outlook

        ↓

Markdown Renderer
  - deterministic Python template
```

実装スコープの LLM agent は9つにする。

1. `EPSQualityAnalyst`
2. `ProfitabilityAnalyst`
3. `CashFlowFcfAnalyst`
4. `BalanceSheetRiskAnalyst`
5. `ManagementIntentAnalyst`
6. `GuidanceAnalyst`
7. `BullAgent`
8. `BearAgent`
9. `JudgeAgent`

これは AGENTS.md の専門エージェント構造と context isolation を提出物として成立させる完成スコープである。

## Why Not One Financial Analyst?

`FinancialAnalyst` へ統合すると実装は楽になる。しかし、次の理由でこの課題では分けるべき。

| 統合 | 問題 |
| --- | --- |
| EPS + FCF | EPS は会計利益、FCF は現金創出力。EPS beat でも FCF 悪化は普通にあり得る |
| EPS + P&L + CFS + BS | context が広がり、agent が headline beat に引っ張られやすい |
| Management + Guidance | 経営方針と来期数値目標の現実性は別の判断 |
| Bull + Bear | 片方の立場に引っ張られ、反対根拠が薄くなりやすい |
| Judge + Report | 構造化判断と文章整形が混ざり、Pydantic 契約が崩れやすい |

統合してよいのは、必要 context が同じで、出力の責務が重ならない場合に限る。

## Agent Decisions

| AGENTS.md の要素 | 判断 | 提出スコープでの扱い |
| --- | --- | --- |
| Data Ingestion Layer | 残すが非LLM | Python処理。外部取得、sectioning、計算を担当 |
| EPS Analyst | 独立 | `EPSQualityAnalyst` |
| P&L Analyst | 独立 | `ProfitabilityAnalyst` |
| CFS Analyst | 独立 | `CashFlowFcfAnalyst` |
| BS Analyst | 独立 | `BalanceSheetRiskAnalyst` |
| Management eval Agent | 独立 | `ManagementIntentAnalyst` |
| Guidance Agent | 独立 | `GuidanceAnalyst` |
| Bull Agent | 独立 | `BullAgent` |
| Bear Agent | 独立 | `BearAgent` |
| Risk Agent | 削る | 各分析Agent、`BalanceSheetRiskAnalyst`、`BearAgent` の `risks` / `counter_evidence` に吸収 |
| Eval Agent | 削る | `JudgeAgent` と責務が重複 |
| Judge / Report Agent | 分離 | 判断は `JudgeAgent`、Markdown 整形は Python |
| Macro Agent | 対象外 | AGENTS.md の主目的である EPS / FCF / 決算評価から外れるため実装対象に含めない |

## Pydantic Contracts

### Core Data Models

```python
RunSpec:
  ticker: str
  fiscal_quarter: str
  filing_url: str | None
  presentation_url: str | None
  transcript_url: str | None

FinancialSnapshot:
  ticker: str
  fiscal_quarter: str
  revenue_actual: float | None
  revenue_consensus: float | None
  revenue_surprise_pct: float | None
  eps_actual: float | None
  eps_consensus: float | None
  eps_surprise_pct: float | None
  eps_yoy_pct: float | None
  gross_margin: float | None
  operating_margin: float | None
  operating_margin_yoy_delta: float | None
  operating_cash_flow: float | None
  free_cash_flow: float | None
  fcf_margin: float | None
  capex: float | None
  working_capital_change: float | None
  cash: float | None
  debt: float | None
  guidance_summary: str | None

DocumentSection:
  source_type: financial_api | filing | presentation | transcript
  section_type: revenue | eps | margin | cash_flow | capex | balance_sheet | guidance | management_commentary | risk | other
  source_ref: str
  text: str
```

### Shared Evidence Model

```python
EvidenceItem:
  claim: str
  source_type: financial_api | filing | presentation | transcript
  source_ref: str
  metric: str | None
  value: float | str | None
  period: str | None
  interpretation: str
```

### Specialist Outputs

```python
EPSQualityFinding:
  agent_name: Literal["eps_quality"]
  eps_surprise_assessment: str
  quality_of_beat: positive | negative | mixed | neutral | unclear
  one_time_factors: list[EvidenceItem]
  sustainable_factors: list[EvidenceItem]
  counter_evidence: list[EvidenceItem]
  eps_outlook: positive | negative | neutral | unclear
  confidence: float
  missing_data: list[str]

ProfitabilityFinding:
  agent_name: Literal["profitability"]
  revenue_quality: positive | negative | mixed | neutral | unclear
  margin_trend: positive | negative | mixed | neutral | unclear
  operating_leverage: positive | negative | mixed | neutral | unclear
  segment_mix_effect: positive | negative | mixed | neutral | unclear
  key_evidence: list[EvidenceItem]
  counter_evidence: list[EvidenceItem]
  eps_implication: positive | negative | neutral | unclear
  fcf_implication: positive | negative | neutral | unclear
  confidence: float
  missing_data: list[str]

CashFlowFcfFinding:
  agent_name: Literal["cash_flow_fcf"]
  fcf_trend: positive | negative | mixed | neutral | unclear
  capex_pressure: str
  working_capital_effect: str
  cash_conversion_assessment: str
  key_evidence: list[EvidenceItem]
  counter_evidence: list[EvidenceItem]
  fcf_outlook: positive | negative | neutral | unclear
  confidence: float
  missing_data: list[str]

BalanceSheetRiskFinding:
  agent_name: Literal["balance_sheet_risk"]
  liquidity_assessment: strong | adequate | weak | unclear
  leverage_assessment: low_risk | moderate_risk | high_risk | unclear
  debt_maturity_risk: low | moderate | high | unclear
  dilution_or_financing_risk: low | moderate | high | unclear
  key_evidence: list[EvidenceItem]
  counter_evidence: list[EvidenceItem]
  eps_constraint: positive | negative | neutral | unclear
  fcf_constraint: positive | negative | neutral | unclear
  confidence: float
  missing_data: list[str]

ManagementIntentFinding:
  agent_name: Literal["management_intent"]
  management_priorities: list[str]
  growth_drivers: list[EvidenceItem]
  investment_or_cost_actions: list[EvidenceItem]
  eps_implication: positive | negative | neutral | unclear
  fcf_implication: positive | negative | neutral | unclear
  time_horizon: short_term | medium_term | long_term | unclear
  counter_evidence: list[EvidenceItem]
  confidence: float
  missing_data: list[str]

GuidanceFinding:
  agent_name: Literal["guidance"]
  guidance_vs_consensus: positive | negative | mixed | neutral | unclear
  conservatism_level: conservative | balanced | aggressive | unclear
  assumption_quality: str
  revision_risk: str
  key_evidence: list[EvidenceItem]
  counter_evidence: list[EvidenceItem]
  eps_implication: positive | negative | neutral | unclear
  fcf_implication: positive | negative | neutral | unclear
  confidence: float
  missing_data: list[str]
```

### Debate and Judge Outputs

```python
AnalysisBrief:
  ticker: str
  fiscal_quarter: str
  eps_finding: EPSQualityFinding
  profitability_finding: ProfitabilityFinding
  fcf_finding: CashFlowFcfFinding
  balance_sheet_risk_finding: BalanceSheetRiskFinding
  management_finding: ManagementIntentFinding
  guidance_finding: GuidanceFinding
  positive_evidence_pool: list[EvidenceItem]
  negative_evidence_pool: list[EvidenceItem]
  disputed_points: list[str]
  missing_data: list[str]

BullCase:
  thesis: str
  strongest_positive_evidence: list[EvidenceItem]
  eps_bull_argument: str
  fcf_bull_argument: str
  conditions_needed: list[str]
  weak_points: list[str]
  confidence: float

BearCase:
  thesis: str
  strongest_negative_evidence: list[EvidenceItem]
  eps_bear_argument: str
  fcf_bear_argument: str
  failure_modes: list[str]
  counter_to_bull_case: list[str]
  confidence: float

FinalVerdict:
  label: good | neutral | bad
  confidence: float
  summary: str
  positive_evidence: list[EvidenceItem]
  negative_evidence: list[EvidenceItem]
  eps_outlook: positive | negative | neutral | unclear
  eps_outlook_reason: str
  fcf_outlook: positive | negative | neutral | unclear
  fcf_outlook_reason: str
  non_advice_disclaimer: str
```

## Agent Responsibilities

### EPSQualityAnalyst

EPS surprise の大きさではなく、EPS beat / miss の質と持続性を見る。

Inputs:

- EPS actual / consensus / surprise
- EPS YoY
- margin and tax related values
- EPS / margin / one-off related sections

Outputs:

- EPS surprise assessment
- one-time factors
- sustainable factors
- EPS outlook
- counter evidence

### ProfitabilityAnalyst

P&L の売上品質、利益率、営業レバレッジ、segment mix を見る。EPS surprise そのものではなく、EPS を支える営業構造が強いか弱いかを分析する。

Inputs:

- revenue actual / consensus / growth
- gross margin
- operating margin
- operating income
- segment revenue / margin where available
- revenue / margin / segment sections

Outputs:

- revenue quality
- margin trend
- operating leverage
- segment mix effect
- EPS / FCF implication
- counter evidence

### CashFlowFcfAnalyst

FCF が将来増加する方向にあるかを見る。EPS とは独立に判断する。

Inputs:

- operating cash flow
- free cash flow
- CapEx
- working capital changes
- cash flow / CapEx / balance sheet sections

Outputs:

- FCF trend
- CapEx pressure
- working capital effect
- cash conversion assessment
- FCF outlook
- counter evidence

### BalanceSheetRiskAnalyst

BS の健全性と、EPS / FCF の将来性を制約する財務リスクを見る。株価や信用投資判断ではなく、流動性・負債・希薄化・財務制約が決算評価に与える影響に限定する。

Inputs:

- cash and equivalents
- debt and lease obligations
- current assets / current liabilities where available
- interest expense where available
- liquidity / debt / capital resources sections

Outputs:

- liquidity assessment
- leverage assessment
- debt maturity risk
- dilution or financing risk
- EPS / FCF constraints
- counter evidence

### ManagementIntentAnalyst

経営陣が何を成長ドライバー、投資領域、コスト改善策として説明しているかを読む。

Inputs:

- presentation sections
- transcript / management commentary
- risk sections where relevant

Outputs:

- management priorities
- growth drivers
- investment or cost actions
- EPS / FCF implication by time horizon
- counter evidence

### GuidanceAnalyst

来期ガイダンスと市場期待の match / mismatch、前提の保守性や楽観性を見る。

Inputs:

- guidance summary
- consensus expectations
- guidance / outlook sections
- management commentary about assumptions

Outputs:

- guidance versus consensus
- conservatism level
- assumption quality
- revision risk
- EPS / FCF implication
- counter evidence

### BullAgent

Validated findings だけを使い、良い決算と判断できる最強ケースを作る。

Inputs:

- `AnalysisBrief`

Outputs:

- bull thesis
- strongest positive evidence
- EPS bull argument
- FCF bull argument
- conditions needed
- weak points

### BearAgent

Validated findings だけを使い、悪い決算または過大評価と判断できる最強ケースを作る。

Inputs:

- `AnalysisBrief`
- compact `BullCaseSummary`

Outputs:

- bear thesis
- strongest negative evidence
- EPS bear argument
- FCF bear argument
- failure modes
- counter to bull case

### JudgeAgent

Bull / Bear の主張と `AnalysisBrief` をもとに最終判定を出す。Markdown は生成しない。

Inputs:

- `FinancialSnapshot`
- `AnalysisBrief`
- `BullCase`
- `BearCase`

Outputs:

- `good | neutral | bad`
- confidence
- positive evidence
- negative evidence
- EPS outlook
- FCF outlook
- non-advice disclaimer

## Orchestrator Responsibilities

- Validate input ticker, quarter, and source configuration.
- Fetch and normalize data.
- Calculate financial metrics in Python.
- Split documents into typed sections.
- Route only relevant sections to each agent.
- Run independent specialist agents in parallel where possible.
- Validate every LLM response with Pydantic.
- Aggregate findings into `AnalysisBrief`.
- Reject outputs with empty `counter_evidence` where counter evidence is required.
- Run `BullAgent -> BearAgent(with BullCaseSummary)` sequentially, then pass both outputs to `JudgeAgent`.
- Pass only compact evidence and debate outputs to Judge.
- Render final Markdown with a deterministic Python template.
- Log each stage as structured events.

## Implementation Scope

This is the completed scope for the internship submission. Items not listed here are intentionally out of scope, not partially promised capabilities.

Implemented specialist workflow target:

- `EPSQualityAnalyst`
- `ProfitabilityAnalyst`
- `CashFlowFcfAnalyst`
- `BalanceSheetRiskAnalyst`
- `ManagementIntentAnalyst`
- `GuidanceAnalyst`
- `BullAgent`
- `BearAgent`
- `JudgeAgent`
- Python `MarkdownRenderer`

Prompt bases for these agents live under `src/prompts/`:

- `src/prompts/financial_agents.md`
- `src/prompts/presentation_agents.md`
- `src/prompts/debate_judge_agents.md`

These are grouped reference files, not three agents. Runtime loading must be
agent-section scoped: for example, `EPSQualityAnalyst` should receive only the
`EPSQualityAnalyst` section from `financial_agents.md`, not the entire financial
prompt file.

Non-agent workflow responsibilities:

- `EvidenceAggregator`
- validation retry
- missing data gate
- source_ref gate
- confidence calibration checks

## Existing Code Alignment

The current implementation has `BullAnalyst`, `BearAnalyst`, `QuantsAnalyst`, and `MacroAnalyst`. For the AGENTS.md target workflow, these should not be treated as the final specialist set.

Recommended migration:

- Replace `QuantsAnalyst` with `EPSQualityAnalyst`, `ProfitabilityAnalyst`, `CashFlowFcfAnalyst`, and `BalanceSheetRiskAnalyst`.
- Replace `MacroAnalyst` with `ManagementIntentAnalyst` and `GuidanceAnalyst`, or remove macro-specific claims until peer/macro data is explicitly available.
- Keep `BullAnalyst` and `BearAnalyst` as debate-stage agents, not round-one analysts over raw filing sections.
- Change verdict label from `GOOD | MIXED | BAD` to `good | neutral | bad`.
- Keep report rendering in Python, but update the template to match the AGENTS.md output image.
