import pytest

from src.report_renderer import ReportRenderer
from src.workflow import MarkdownRenderer
from src.workflow_models import (
    AgentRole,
    AnalysisBrief,
    AvailabilityItem,
    AvailabilityStatus,
    BearCase,
    BullCase,
    CashFlowRiskFinding,
    ClaimRecord,
    ClaimType,
    DebateResult,
    DecisionUse,
    DerivedMetricValue,
    EarningsQualityFinding,
    EvidenceItem,
    EvidencePolarity,
    FactCheckStatus,
    FinancialMetrics,
    FindingCoverage,
    FindingCoverageMap,
    GuidanceFinding,
    ImpactArea,
    JudgeDecision,
    JudgeTreatment,
    ManagementIntentFinding,
    MetricPeriodRole,
    MetricValue,
    MissingDataItem,
    PresentationMetricCandidate,
    ReportMatrix,
    ReviewRequest,
    SourceManifestEntry,
    SourceRef,
    SourceType,
)


def financial_source() -> SourceRef:
    return SourceRef(
        source_id="api:eps:2025Q3",
        source_type=SourceType.FINANCIAL_API,
        metric_name="eps",
        title="Financial API EPS",
        reported_period="2025Q3",
    )


def filing_source() -> SourceRef:
    return SourceRef(
        source_id="filing:capex:2025Q3",
        source_type=SourceType.FILING,
        document_id="10q-2025q3",
        section_id="capex",
        page=16,
        title="Q3 10-Q CapEx section",
        reported_period="2025Q3",
    )


def canonical_metric_source(
    source_id: str,
    metric_name: str,
    *,
    provider: str,
    period_role: MetricPeriodRole = MetricPeriodRole.ACTUAL,
    source_type: SourceType = SourceType.FINANCIAL_API,
) -> SourceRef:
    return SourceRef(
        source_id=source_id,
        source_type=source_type,
        metric_name=metric_name,
        title=f"{provider} {metric_name}",
        reported_period="2025Q3",
        provider=provider,
        period_role=period_role,
    )


def presentation_source() -> SourceRef:
    return SourceRef(
        source_id="presentation:metrics:page-5",
        source_type=SourceType.EARNINGS_PRESENTATION,
        document_id="deck-2025q3",
        section_id="page-5",
        page=5,
        title="Presentation metrics page",
        reported_period="2025Q3",
    )


def financial_metrics() -> FinancialMetrics:
    eps_source = canonical_metric_source(
        "financial_api:NVDA:2025Q3:yfinance:eps",
        "eps",
        provider="yfinance",
    )
    revenue_source = canonical_metric_source(
        "financial_api:NVDA:2025Q3:sec:revenue",
        "revenue",
        provider="sec",
    )
    fcf_source = canonical_metric_source(
        "metric:NVDA:2025Q3:free_cash_flow:derived",
        "free_cash_flow",
        provider="workflow",
        source_type=SourceType.DERIVED_METRIC,
    )
    return FinancialMetrics(
        ticker="NVDA",
        fiscal_period="2025Q3",
        canonical_metrics=[
            MetricValue(
                metric_id="metric:eps:actual",
                metric_name="eps",
                value=1.23,
                unit="USD/share",
                fiscal_period="2025Q3",
                period_role=MetricPeriodRole.ACTUAL,
                source_ref=eps_source,
            ),
            MetricValue(
                metric_id="metric:revenue:actual",
                metric_name="revenue",
                value=35_100_000_000,
                unit="USD",
                fiscal_period="2025Q3",
                period_role=MetricPeriodRole.ACTUAL,
                source_ref=revenue_source,
            ),
        ],
        derived_metrics=[
            DerivedMetricValue(
                metric_id="metric:fcf:actual",
                metric_name="free_cash_flow",
                value=14_900_000_000,
                unit="USD",
                fiscal_period="2025Q3",
                period_role=MetricPeriodRole.ACTUAL,
                source_ref=fcf_source,
                component_metric_ids=["metric:operating_cash_flow", "metric:capex"],
                component_source_refs=[revenue_source],
            )
        ],
        presentation_metric_candidates=[
            PresentationMetricCandidate(
                candidate_id="presentation:candidate:revenue",
                metric_name="revenue",
                raw_text="Presentation revenue candidate",
                value=35_100_000_000,
                unit="USD",
                fiscal_period="2025Q3",
                period_role=MetricPeriodRole.ACTUAL,
                source_ref=presentation_source(),
            )
        ],
    )


def positive_evidence() -> EvidenceItem:
    return EvidenceItem(
        evidence_id="ev:eps-beat",
        polarity=EvidencePolarity.POSITIVE,
        summary="Adjusted EPS of $1.23 exceeded consensus by 8%.",
        detail="Adjusted EPS was $1.23 versus consensus of $1.14.",
        impact_areas=[ImpactArea.EPS],
        source_ref=financial_source(),
        metric_name="eps",
        value=1.23,
        unit="USD/share",
        reported_period="2025Q3",
        fact_check_status=FactCheckStatus.SUPPORTED,
        confidence=0.86,
    )


def negative_evidence() -> EvidenceItem:
    return EvidenceItem(
        evidence_id="ev:capex-pressure",
        polarity=EvidencePolarity.NEGATIVE,
        summary="CapEx rose to $3.0B, pressuring free cash flow.",
        detail="The filing shows higher investment intensity during the quarter.",
        impact_areas=[ImpactArea.FCF],
        source_ref=filing_source(),
        metric_name="capex",
        value=3_000_000_000,
        unit="USD",
        reported_period="2025Q3",
        fact_check_status=FactCheckStatus.PARTIALLY_SUPPORTED,
        confidence=0.72,
    )


def finding(cls, key: EvidenceItem, counter: EvidenceItem, *, missing: list[str] | None = None):
    return cls(
        stance="mixed",
        summary=f"{cls.__name__} found support and caveats.",
        key_evidence=[key],
        counter_evidence=[counter],
        confidence=0.74,
        missing_data=missing or [],
        handoff_summary=f"{cls.__name__} handoff uses validated evidence only.",
    )


def finding_coverage() -> FindingCoverageMap:
    return {
        "earnings_quality": FindingCoverage.SUPPORTING,
        "cash_flow_risk": FindingCoverage.OPPOSING,
        "management_intent": FindingCoverage.SUPPORTING,
        "guidance": FindingCoverage.SUPPORTING,
    }


def bull_case(key: EvidenceItem) -> BullCase:
    return BullCase(
        thesis="Bull thesis: EPS quality improved and the setup can remain constructive.",
        stance_strength="moderate",
        strongest_positive_evidence=[key],
        eps_bull_argument="EPS bull detail: margin support gives EPS a credible improvement path.",
        fcf_bull_argument="FCF bull detail: FCF can improve if investment intensity normalizes.",
        conditions_needed=["Revenue growth continues.", "CapEx intensity moderates."],
        weak_points=["FCF conversion is not fully proven."],
        finding_coverage=finding_coverage(),
        disputed_points_to_watch=["CapEx timing"],
        confidence=0.68,
    )


def bear_case(key: EvidenceItem) -> BearCase:
    return BearCase(
        thesis="Bear thesis: cash-flow conversion risk keeps the print from being one-sided.",
        stance_strength="moderate",
        strongest_negative_evidence=[key],
        eps_bear_argument="EPS bear detail: some margin gains may not persist.",
        fcf_bear_argument="FCF bear detail: elevated CapEx can pressure near-term FCF.",
        failure_modes=["Demand slows.", "CapEx remains elevated."],
        counter_to_bull_case=["EPS strength does not remove cash conversion risk."],
        finding_coverage=finding_coverage(),
        unresolved_risks=["Demand durability"],
        confidence=0.66,
    )


def renderer_inputs():
    positive = positive_evidence()
    negative = negative_evidence()
    request = ReviewRequest(
        ticker="NVDA",
        fiscal_period="2025Q3",
        financial_metrics=financial_metrics(),
    )
    brief = AnalysisBrief(
        ticker="NVDA",
        fiscal_period="2025Q3",
        earnings_quality_finding=finding(EarningsQualityFinding, positive, negative),
        cash_flow_risk_finding=finding(
            CashFlowRiskFinding,
            positive,
            negative,
            missing=["FCF bridge from operating cash flow to free cash flow is incomplete."],
        ),
        management_intent_finding=finding(ManagementIntentFinding, positive, negative),
        guidance_finding=finding(
            GuidanceFinding,
            positive,
            negative,
            missing=["Forward guidance source was not routed."],
        ),
        positive_evidence_pool=[positive],
        negative_evidence_pool=[negative],
        risk_evidence_pool=[negative],
        synthesis="Validated evidence is constructive, but cash-flow durability remains uncertain.",
    )
    debate = DebateResult(
        bull_case="Bull case: EPS quality improved on a verified beat.",
        bear_case="Bear case: CapEx pressure can delay FCF conversion.",
        risk_case="Risk case: missing guidance limits forward confidence.",
        evaluation="Bull evidence is stronger for the current quarter, while bear evidence limits durability.",
        strongest_positive_evidence=[positive],
        strongest_negative_evidence=[negative],
        unresolved_questions=["How much of CapEx pressure reverses next quarter?"],
    )
    decision = JudgeDecision(
        verdict="neutral",
        confidence=0.66,
        summary="The quarter is constructive, with cash-flow caveats.",
        rationale="The Judge treated the EPS fact as supporting, but discounted durability due to CapEx.",
        positive_evidence=[positive],
        negative_evidence=[negative],
        eps_outlook="EPS outlook is constructive if margin support persists.",
        eps_outlook_reason="The EPS beat is supported by a checked financial source.",
        fcf_outlook="FCF outlook remains uncertain until the CapEx bridge is clearer.",
        fcf_outlook_reason="CapEx pressure and missing bridge data limit confidence.",
    )
    matrix = ReportMatrix(
        source_manifest=[
            SourceManifestEntry(
                source_id="api:eps:2025Q3",
                source_type=SourceType.FINANCIAL_API,
                title="Financial API EPS",
                metric_name="eps",
                reported_period="2025Q3",
            ),
            SourceManifestEntry(
                source_id="filing:capex:2025Q3",
                source_type=SourceType.FILING,
                title="Q3 10-Q CapEx section",
                document_id="10q-2025q3",
                section_id="capex",
                page=16,
                reported_period="2025Q3",
            ),
        ],
        evidence_items=[positive, negative],
        claim_records=[
            ClaimRecord(
                claim_id="claim:eps-quality",
                claim_type=ClaimType.INTERPRETATION,
                agent_role=AgentRole.EARNINGS_QUALITY,
                time_scope="Current quarter 2025Q3",
                claim="EPS quality improved because the beat was supported by reported EPS.",
                evidence_ids=[positive.evidence_id],
                counter_evidence_ids=[negative.evidence_id],
                interpretation="The fact supports current-quarter EPS quality.",
                implication="The report should avoid converting the fact into a durable forecast.",
                confidence=0.76,
                limitations=["Durability depends on margin and CapEx evidence."],
            )
        ],
        decision_uses=[
            DecisionUse(
                decision_use_id="decision:eps-quality",
                treatment=JudgeTreatment.SUPPORTING,
                claim_id="claim:eps-quality",
                decisive_evidence_ids=[positive.evidence_id],
                rationale="The checked EPS fact supports the neutral-to-positive EPS treatment.",
                verdict_impact=EvidencePolarity.POSITIVE,
                confidence_impact=0.10,
            )
        ],
        missing_data_items=[
            MissingDataItem(
                missing_data_id="missing:fcf-bridge",
                topic="FCF bridge",
                reason="The source set does not explain conversion from operating cash flow to FCF.",
                materiality="medium",
            )
        ],
    )
    return request, brief, debate, decision, matrix, bull_case(positive), bear_case(negative)


def render_report() -> str:
    request, brief, debate, decision, matrix, bull, bear = renderer_inputs()
    return ReportRenderer().render(
        request=request,
        brief=brief,
        debate=debate,
        decision=decision,
        matrix=matrix,
        bull_case=bull,
        bear_case=bear,
    )


def section(markdown: str, heading: str) -> str:
    start = markdown.index(f"## {heading}")
    next_start = markdown.find("\n## ", start + 1)
    if next_start == -1:
        return markdown[start:]
    return markdown[start:next_start]


def test_renderer_outputs_final_section_order():
    markdown = render_report()
    headings = [
        "レポート前提: canonical data",
        "要約",
        "判定理由",
        "EPS/FCF見通し",
        "Bull/Bear論点",
        "Agent分析",
        "根拠マトリクス (Evidence Matrix)",
        "データ品質",
        "不確実性と不足データ",
        "品質ゲート (Quality Gates)",
        "ソース付録 (Source Appendix)",
        "免責事項",
    ]

    positions = [markdown.index(f"## {heading}") for heading in headings]

    assert positions == sorted(positions)


def test_canonical_data_premise_excludes_presentation_candidates():
    premise = section(render_report(), "レポート前提: canonical data")

    assert "financial_api:NVDA:2025Q3:yfinance:eps" in premise
    assert "financial_api:NVDA:2025Q3:sec:revenue" in premise
    assert "metric:NVDA:2025Q3:free_cash_flow:derived" in premise
    assert "source_id" in premise
    assert "provider" in premise
    assert "source_type" in premise
    assert "period_role" in premise
    assert "presentation:metrics:page-5" not in premise
    assert "presentation抽出値は補助資料" in premise


def test_reader_report_uses_rich_bull_bear_fields_when_available():
    tension = section(render_report(), "Bull/Bear論点")

    assert "EPS bull detail" in tension
    assert "FCF bull detail" in tension
    assert "Revenue growth continues" in tension
    assert "EPS bear detail" in tension
    assert "FCF bear detail" in tension
    assert "EPS strength does not remove cash conversion risk" in tension
    assert "- 論旨:" in tension
    assert "- 強さ:" in tension
    assert "- 信頼度:" in tension
    assert "- 悪化シナリオ:" in tension
    assert "- Bull論点への反論:" in tension
    assert "### リスクケース" in tension
    assert "### Judgeの論点整理" in tension
    assert "- thesis:" not in tension
    assert "- strength:" not in tension
    assert "- confidence:" not in tension
    assert "- failure modes:" not in tension


def test_data_quality_flags_render_before_missing_data_and_filter_out_of_contract_gaps():
    request, brief, debate, decision, matrix, bull, bear = renderer_inputs()
    brief.management_intent_finding.missing_data.append("Transcript was not supplied.")
    matrix.source_manifest.append(
        SourceManifestEntry(
            source_id="presentation:page-5",
            source_type=SourceType.EARNINGS_PRESENTATION,
            title="Q3 presentation guidance page",
            document_id="deck-2025q3",
            section_id="page-5",
            page=5,
            reported_period="2025Q3",
        )
    )
    matrix.missing_data_items.append(
        MissingDataItem(
            missing_data_id="missing:transcript",
            topic="Transcript",
            reason="Transcript was not supplied.",
            materiality="medium",
            requested_source_type=SourceType.EARNINGS_CALL,
        )
    )

    markdown = ReportRenderer().render(
        request=request,
        brief=brief,
        debate=debate,
        decision=decision,
        matrix=matrix,
        bull_case=bull,
        bear_case=bear,
    )

    assert markdown.index("## データ品質") < markdown.index("## 不確実性と不足データ")
    data_quality = section(markdown, "データ品質")
    agent_contribution = section(markdown, "Agent分析")
    uncertainty = section(markdown, "不確実性と不足データ")
    assert "入力プロファイル: yfinance_sec_presentation_tagged" in data_quality
    assert "Transcript was not supplied" not in agent_contribution
    assert "Forward guidance source was not routed" in agent_contribution
    assert "Transcript was not supplied" not in uncertainty
    assert "Transcript" not in uncertainty


def test_workflow_matrix_does_not_promote_agent_missing_data_to_matrix_items():
    request, brief, debate, decision, _matrix, bull, bear = renderer_inputs()

    matrix = MarkdownRenderer().build_report_matrix(
        request=request,
        brief=brief,
        debate=debate,
        decision=decision,
    )
    markdown = ReportRenderer().render(
        request=request,
        brief=brief,
        debate=debate,
        decision=decision,
        matrix=matrix,
        bull_case=bull,
        bear_case=bear,
    )

    assert matrix.missing_data_items == []
    assert "不足データ項目: 0" in section(markdown, "品質ゲート (Quality Gates)")
    assert "matrix-levelの不足データ項目はありません" in section(
        markdown,
        "不確実性と不足データ",
    )
    assert "FCF bridge from operating cash flow" in section(markdown, "Agent分析")
    assert "Forward guidance source was not routed" in section(markdown, "Agent分析")


def test_evidence_matrix_distinguishes_contract_fields():
    matrix_section = section(render_report(), "根拠マトリクス (Evidence Matrix)")

    assert (
        "| Claim ID | Fact | Interpretation | Implication | Time scope | "
        "Fact-check status | Judge treatment | Sources |"
    ) in matrix_section
    assert "Adjusted EPS of $1.23 exceeded consensus by 8%." in matrix_section
    assert "The fact supports current-quarter EPS quality." in matrix_section
    assert "The report should avoid converting the fact into a durable forecast." in matrix_section
    assert "Current quarter 2025Q3" in matrix_section
    assert "supported" in matrix_section
    assert "supporting" in matrix_section


def test_quality_gates_list_data_quality_conflicts():
    request, brief, debate, decision, matrix, bull, bear = renderer_inputs()
    matrix = matrix.model_copy(
        update={
            "data_quality_flags": [
                AvailabilityItem(
                    key="conflict:sec_yfinance:revenue",
                    status=AvailabilityStatus.CONFLICTING,
                    reason="SEC revenue conflicts with yfinance revenue.",
                    source_type=SourceType.FINANCIAL_API,
                )
            ]
        }
    )

    markdown = ReportRenderer().render(
        request=request,
        brief=brief,
        debate=debate,
        decision=decision,
        matrix=matrix,
        bull_case=bull,
        bear_case=bear,
    )

    assert "- metric conflict: listed" in section(markdown, "データ品質")


def test_source_appendix_does_not_duplicate_unrelated_sections():
    source_appendix = section(render_report(), "ソース付録 (Source Appendix)")

    assert source_appendix.count("api:eps:2025Q3") == 1
    assert source_appendix.count("filing:capex:2025Q3") == 1
    assert "Q3 10-Q CapEx section" in source_appendix
    assert "根拠マトリクス" not in source_appendix
    assert "品質ゲート" not in source_appendix
    assert "Bull/Bear論点" not in source_appendix


def test_workflow_matrix_uses_request_source_manifest_as_authoritative_registry():
    request, brief, debate, decision, _matrix, _bull, _bear = renderer_inputs()
    request.source_manifest = [
        SourceManifestEntry(
            source_id="api:eps:2025Q3",
            source_type=SourceType.FINANCIAL_API,
            title="Financial API EPS",
            metric_name="eps",
            reported_period="2025Q3",
        )
    ]

    with pytest.raises(ValueError, match="unregistered source_id in evidence_items"):
        MarkdownRenderer().build_report_matrix(
            request=request,
            brief=brief,
            debate=debate,
            decision=decision,
        )


def test_quality_gates_and_disclaimer_are_visible():
    markdown = render_report()
    quality_gates = section(markdown, "品質ゲート (Quality Gates)")
    disclaimer = section(markdown, "免責事項")

    assert "ReportMatrix検証: passed" in quality_gates
    assert "根拠項目: 2" in quality_gates
    assert "supported: 1" in quality_gates
    assert "投資助言ではありません" in disclaimer
