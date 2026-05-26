# Agent Prompt References

This directory stores prompt bases for specialist agents used by the earnings
debate workflow. Treat these files as skill/tool references: the orchestrator
loads only the prompt needed for the current agent, then passes a narrow,
validated context payload.

Design rules:

- Data fetching, financial calculations, document sectioning, and Markdown
  rendering stay outside LLM agents.
- Agents receive only precomputed values and routed document sections.
- Agents return JSON only; Pydantic validation is required before handoff.
- Evidence must include a traceable `source_ref`.
- Positive and counter evidence must both be considered.
- No agent may provide stock-price forecasts, target prices, or trading advice.

Prompt groups:

- `financial_agents.md`: `EPSQualityAnalyst`, `ProfitabilityAnalyst`, `CashFlowFcfAnalyst`, `BalanceSheetRiskAnalyst`
- `presentation_agents.md`: `ManagementIntentAnalyst`, `GuidanceAnalyst`
- `debate_judge_agents.md`: `BullAgent`, `BearAgent`, `JudgeAgent`

The file count is not the agent count. These are grouped references for review
consistency. At runtime, load only the section for the agent being invoked.
