from datetime import date

from src.sec_company_facts import build_sec_company_facts_metrics, select_sec_fact_value
from src.workflow_models import AvailabilityStatus, MetricPeriodRole


def company_facts(rows_by_tag):
    return {
        "entityName": "Example Corp",
        "facts": {"us-gaap": {tag: {"units": {"USD": rows}} for tag, rows in rows_by_tag.items()}},
    }


def row(value, start, end, *, form="10-Q", filed="2025-08-01", fp="Q2"):
    return {
        "val": value,
        "start": start,
        "end": end,
        "form": form,
        "filed": filed,
        "fp": fp,
    }


def test_select_sec_fact_value_prefers_direct_quarter_value():
    facts = company_facts(
        {
            "Revenues": [
                row(100, "2025-01-01", "2025-03-31", fp="Q1"),
                row(260, "2025-01-01", "2025-06-30"),
                row(160, "2025-04-01", "2025-06-30"),
            ]
        }
    )

    value = select_sec_fact_value(
        facts,
        "revenue",
        target_period_end_date=date(2025, 6, 30),
    )

    assert value is not None
    assert value.value == 160
    assert value.method == "direct_quarter"
    assert value.tag == "Revenues"


def test_select_sec_fact_value_prefers_closest_period_end_inside_tolerance():
    facts = company_facts(
        {
            "Revenues": [
                row(160, "2025-04-01", "2025-06-30", filed="2025-08-01"),
                row(999, "2025-04-16", "2025-07-15", filed="2025-09-01"),
            ]
        }
    )

    value = select_sec_fact_value(
        facts,
        "revenue",
        target_period_end_date=date(2025, 6, 30),
    )

    assert value is not None
    assert value.value == 160
    assert value.end == date(2025, 6, 30)


def test_select_sec_fact_value_derives_quarter_from_ytd_when_direct_absent():
    facts = company_facts(
        {
            "NetCashProvidedByUsedInOperatingActivities": [
                row(100, "2025-01-01", "2025-03-31", fp="Q1"),
                row(260, "2025-01-01", "2025-06-30"),
            ]
        }
    )

    value = select_sec_fact_value(
        facts,
        "operating_cash_flow",
        target_period_end_date=date(2025, 6, 30),
    )

    assert value is not None
    assert value.value == 160
    assert value.method == "ytd_difference"
    assert value.prior_end == date(2025, 3, 31)


def test_select_sec_fact_value_rejects_ytd_difference_without_immediate_prior_period():
    facts = company_facts(
        {
            "NetCashProvidedByUsedInOperatingActivities": [
                row(100, "2025-01-01", "2025-03-31", fp="Q1"),
                row(600, "2025-01-01", "2025-09-30", fp="Q3"),
            ]
        }
    )

    value = select_sec_fact_value(
        facts,
        "operating_cash_flow",
        target_period_end_date=date(2025, 9, 30),
    )

    assert value is None


def test_build_sec_company_facts_metrics_normalizes_p0_and_derives_fcf():
    facts = company_facts(
        {
            "Revenues": [row(160, "2025-04-01", "2025-06-30")],
            "NetCashProvidedByUsedInOperatingActivities": [
                row(100, "2025-01-01", "2025-03-31", fp="Q1"),
                row(260, "2025-01-01", "2025-06-30"),
            ],
            "PaymentsToAcquireProductiveAssets": [row(40, "2025-04-01", "2025-06-30")],
        }
    )

    metrics = build_sec_company_facts_metrics(
        "NVDA",
        "2025Q2",
        target_period_end_date=date(2025, 6, 30),
        facts=facts,
        cik=1045810,
    )

    assert metrics.revenue == 160
    assert metrics.operating_cash_flow == 160
    assert metrics.capex == -40
    assert metrics.free_cash_flow == 120
    assert {ref.provider for ref in metrics.source_refs} == {"sec_company_facts"}
    assert {ref.metric_name for ref in metrics.source_refs} >= {
        "revenue",
        "operating_cash_flow",
        "capex",
    }
    assert metrics.derived_metrics
    assert metrics.derived_metrics[0].source_ref.source_type.value == "derived_metric"
    ocf_ref = next(ref for ref in metrics.source_refs if ref.metric_name == "operating_cash_flow")
    assert "method=ytd_difference" in (ocf_ref.title or "")
    assert "prior_end=2025-03-31" in (ocf_ref.title or "")


def test_build_sec_company_facts_metrics_normalizes_comparison_periods():
    facts = company_facts(
        {
            "Revenues": [
                row(160, "2025-04-01", "2025-06-30"),
                row(140, "2025-01-01", "2025-03-31", fp="Q1"),
                row(120, "2024-04-01", "2024-06-30"),
            ],
            "NetCashProvidedByUsedInOperatingActivities": [
                row(50, "2025-04-01", "2025-06-30"),
                row(40, "2025-01-01", "2025-03-31", fp="Q1"),
                row(30, "2024-04-01", "2024-06-30"),
            ],
            "PaymentsToAcquireProductiveAssets": [
                row(10, "2025-04-01", "2025-06-30"),
                row(8, "2025-01-01", "2025-03-31", fp="Q1"),
                row(6, "2024-04-01", "2024-06-30"),
            ],
        }
    )

    metrics = build_sec_company_facts_metrics(
        "NVDA",
        "2025Q2",
        target_period_end_date=date(2025, 6, 30),
        facts=facts,
        cik=1045810,
    )

    revenue_by_role = {
        metric.period_role: metric.value
        for metric in metrics.canonical_metrics
        if metric.metric_name == "revenue"
    }
    fcf_by_role = {
        metric.period_role: metric.value
        for metric in metrics.derived_metrics
        if metric.metric_name == "free_cash_flow"
    }
    assert revenue_by_role == {
        MetricPeriodRole.ACTUAL: 160,
        MetricPeriodRole.PREVIOUS_QUARTER: 140,
        MetricPeriodRole.YEAR_AGO_QUARTER: 120,
    }
    assert fcf_by_role == {
        MetricPeriodRole.ACTUAL: 40,
        MetricPeriodRole.PREVIOUS_QUARTER: 32,
        MetricPeriodRole.YEAR_AGO_QUARTER: 24,
    }
    assert {
        ref.period_role for ref in metrics.source_refs if ref.metric_name == "operating_cash_flow"
    } == {
        MetricPeriodRole.ACTUAL,
        MetricPeriodRole.PREVIOUS_QUARTER,
        MetricPeriodRole.YEAR_AGO_QUARTER,
    }


def test_build_sec_company_facts_metrics_marks_unavailable_without_target_period():
    metrics = build_sec_company_facts_metrics(
        "NVDA",
        "2025Q2",
        target_period_end_date=None,
        facts=company_facts({}),
        cik=1045810,
    )

    assert metrics.revenue is None
    assert {item.status for item in metrics.availability} == {AvailabilityStatus.PERIOD_UNVERIFIED}


def test_select_sec_fact_value_rejects_period_outside_tolerance():
    facts = company_facts(
        {
            "Revenues": [
                row(160, "2025-04-01", "2025-06-14"),
            ]
        }
    )

    value = select_sec_fact_value(
        facts,
        "revenue",
        target_period_end_date=date(2025, 6, 30),
    )

    assert value is None


def test_select_sec_fact_value_accepts_quarter_end_within_fifteen_day_tolerance():
    facts = company_facts(
        {
            "Revenues": [
                row(160, "2025-04-01", "2025-06-15"),
            ]
        }
    )

    value = select_sec_fact_value(
        facts,
        "revenue",
        target_period_end_date=date(2025, 6, 30),
    )

    assert value is not None
    assert value.value == 160
