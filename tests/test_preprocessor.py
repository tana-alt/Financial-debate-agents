from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.preprocessor import (
    DEFAULT_CONTEXT_BUDGET,
    build_financial_metrics,
    build_normalized_review_request,
    calculate_surprise_pct,
    document_files_to_sections,
    fetch_filing_html,
    safe_float,
    segment_filing,
)
from src.workflow_models import (
    AvailabilityStatus,
    DocumentFile,
    DocumentSection,
    MetricPeriodRole,
    SourceRef,
    SourceType,
)


def test_safe_float_discards_invalid_external_values():
    assert safe_float("1.25") == 1.25
    assert safe_float(None) is None
    assert safe_float("not-a-number") is None
    assert safe_float(float("nan")) is None


def test_default_context_budget_allows_source_forward_reports():
    assert DEFAULT_CONTEXT_BUDGET == {
        "max_input_tokens": 96_000,
        "max_output_tokens": 16_000,
        "max_total_tokens": 128_000,
    }


def test_calculate_surprise_pct_handles_missing_consensus():
    assert calculate_surprise_pct(0.81, 0.75) == pytest.approx(8.0)
    assert calculate_surprise_pct(0.81, None) is None
    assert calculate_surprise_pct(0.81, 0) is None


def test_build_financial_metrics_computes_eps_surprise():
    metrics = build_financial_metrics(
        ticker="nvda",
        fiscal_period="2025Q3",
        eps=0.81,
        eps_consensus=0.75,
    )

    assert metrics.ticker == "NVDA"
    assert round(metrics.eps_surprise_pct or 0, 2) == 8.0


def test_build_normalized_review_request_acquires_filing_url_and_drops_raw_fields(
    monkeypatch,
):
    filing_url = "https://www.sec.gov/Archives/example/sample.htm"
    calls = {}

    def fake_fetch_filing_html(url):
        calls["fetch_url"] = url
        return "<html>mock filing</html>"

    def fake_segment_filing(html, url=None):
        calls["segment_html"] = html
        calls["segment_url"] = url
        return [
            DocumentSection(
                section_id="filing:guidance",
                source_ref=SourceRef(
                    source_id="filing:guidance",
                    source_type=SourceType.FILING,
                    url=filing_url,
                    document_id="filing-html",
                    section_id="filing:guidance",
                    title="Filing guidance",
                ),
                heading="guidance",
                text="Management guided to durable demand and elevated investment.",
            )
        ]

    monkeypatch.setattr("src.preprocessor.fetch_filing_html", fake_fetch_filing_html)
    monkeypatch.setattr("src.preprocessor.segment_filing", fake_segment_filing)
    monkeypatch.setattr(
        "src.preprocessor.fetch_consensus",
        lambda ticker, fiscal_period, **kwargs: build_financial_metrics(
            ticker=ticker,
            fiscal_period=fiscal_period,
            eps=0.81,
            eps_consensus=0.75,
        ),
    )

    request = build_normalized_review_request(
        {
            "ticker": "nvda",
            "fiscal_period": "2025Q3",
            "filing_url": filing_url,
        }
    )

    payload = request.model_dump(mode="json")
    assert request.ticker == "NVDA"
    assert calls == {
        "fetch_url": filing_url,
        "segment_html": "<html>mock filing</html>",
        "segment_url": filing_url,
    }
    assert "filing_url" not in payload
    assert "document_files" not in payload
    assert request.registered_source_ids == {
        "financial_api:NVDA:2025Q3",
        "filing:guidance",
    }
    assert payload["document_sections"][0]["source_ref"]["url"] == filing_url


def test_build_normalized_review_request_converts_raw_text_to_manifested_section():
    request = build_normalized_review_request(
        {
            "ticker": "nvda",
            "fiscal_period": "2025Q3",
            "financial_metrics": build_financial_metrics(
                ticker="NVDA",
                fiscal_period="2025Q3",
                eps=0.81,
                eps_consensus=0.75,
            ).model_dump(mode="json"),
            "raw_text": "Guidance improved.\n\nFree cash flow was pressured by investment.",
        }
    )

    payload = request.model_dump(mode="json")
    assert "raw_text" not in payload
    assert request.document_sections[0].section_id == "raw-text:NVDA:2025Q3:section-1"
    assert request.document_sections[0].source_ref.source_id in request.registered_source_ids


def test_build_normalized_review_request_rejects_non_target_period_sections():
    with pytest.raises(ValueError, match="target-period only"):
        build_normalized_review_request(
            {
                "ticker": "nvda",
                "fiscal_period": "2025Q3",
                "financial_metrics": build_financial_metrics(
                    ticker="NVDA",
                    fiscal_period="2025Q3",
                    eps=0.81,
                    eps_consensus=0.75,
                ).model_dump(mode="json"),
                "document_sections": [
                    {
                        "section_id": "presentation:future-guidance",
                        "source_ref": {
                            "source_id": "presentation:future-guidance",
                            "source_type": "earnings_presentation",
                            "document_id": "deck",
                            "section_id": "presentation:future-guidance",
                            "reported_period": "2025Q4",
                        },
                        "heading": "Future guidance",
                        "text": "Guidance for a different period.",
                    }
                ],
            }
        )


def test_fetch_consensus_uses_yfinance_revenue_alias(monkeypatch):
    from src.preprocessor import fetch_consensus

    class FakeTicker:
        earnings_dates = pd.DataFrame(
            [
                {"Reported EPS": 0.52, "EPS Estimate": 0.50, "Surprise(%)": 4.0},
                {"Reported EPS": 0.81, "EPS Estimate": 0.75, "Surprise(%)": 8.0},
            ],
            index=pd.to_datetime(["2026-02-20", "2025-08-28"]),
        )
        quarterly_financials = pd.DataFrame(
            [[999_000.0, 123_000.0]],
            index=["Operating Revenue"],
            columns=pd.to_datetime(["2026-01-31", "2025-07-31"]),
        )
        quarterly_cashflow = pd.DataFrame(
            [[99_000.0, 20_000.0], [-9_000.0, -5_000.0], [90_000.0, 99_000.0]],
            index=["OperatingCashFlow", "Capital Expenditure", "Free Cash Flow"],
            columns=pd.to_datetime(["2026-01-31", "2025-07-31"]),
        )

        def __init__(self, ticker):
            self.ticker = ticker

    monkeypatch.setattr("src.preprocessor.yf.Ticker", FakeTicker)

    metrics = fetch_consensus(
        "nvda",
        "2025Q3",
        target_earnings_date=date(2025, 8, 28),
        target_period_end_date=date(2025, 7, 31),
    )

    assert metrics.eps == 0.81
    assert metrics.eps_consensus == 0.75
    assert metrics.revenue == 123_000.0
    assert metrics.operating_cash_flow == 20_000.0
    assert metrics.capex == -5_000.0
    assert metrics.free_cash_flow == 15_000.0
    assert {ref.metric_name for ref in metrics.source_refs} >= {
        "eps",
        "eps_consensus",
        "revenue",
        "operating_cash_flow",
        "capex",
    }
    assert "free_cash_flow" not in {ref.metric_name for ref in metrics.source_refs}
    assert metrics.derived_metrics
    assert metrics.derived_metrics[0].component_metric_ids == [
        "metric:NVDA:2025Q3:operating_cash_flow",
        "metric:NVDA:2025Q3:capex",
    ]
    assert {ref.metric_name for ref in metrics.derived_metrics[0].component_source_refs} == {
        "operating_cash_flow",
        "capex",
    }


def test_fetch_consensus_adds_eps_for_previous_and_year_ago_quarters(monkeypatch):
    from src.preprocessor import fetch_consensus

    class FakeTicker:
        earnings_dates = pd.DataFrame(
            [
                {"Reported EPS": 0.91, "EPS Estimate": 0.88, "Surprise(%)": 3.4},
                {"Reported EPS": 0.81, "EPS Estimate": 0.75, "Surprise(%)": 8.0},
                {"Reported EPS": 0.76, "EPS Estimate": 0.72, "Surprise(%)": 5.6},
                {"Reported EPS": 0.68, "EPS Estimate": 0.65, "Surprise(%)": 4.6},
                {"Reported EPS": 0.55, "EPS Estimate": 0.54, "Surprise(%)": 1.9},
            ],
            index=pd.to_datetime(
                [
                    "2025-11-21",
                    "2025-08-28",
                    "2025-05-29",
                    "2024-08-27",
                    "2024-05-23",
                ]
            ),
        )
        quarterly_financials = pd.DataFrame(
            [[123_000.0]],
            index=["Operating Revenue"],
            columns=pd.to_datetime(["2025-07-31"]),
        )
        quarterly_cashflow = pd.DataFrame(
            [[20_000.0], [-5_000.0]],
            index=["OperatingCashFlow", "Capital Expenditure"],
            columns=pd.to_datetime(["2025-07-31"]),
        )

        def __init__(self, ticker):
            self.ticker = ticker

    monkeypatch.setattr("src.preprocessor.yf.Ticker", FakeTicker)

    metrics = fetch_consensus(
        "nvda",
        "2025Q3",
        target_earnings_date=date(2025, 8, 28),
        target_period_end_date=date(2025, 7, 31),
    )

    eps_by_role = {
        metric.period_role: metric
        for metric in metrics.canonical_metrics
        if metric.metric_name == "eps"
    }
    assert eps_by_role[MetricPeriodRole.ACTUAL].value == 0.81
    assert eps_by_role[MetricPeriodRole.PREVIOUS_QUARTER].value == 0.76
    assert eps_by_role[MetricPeriodRole.YEAR_AGO_QUARTER].value == 0.68
    assert eps_by_role[MetricPeriodRole.PREVIOUS_QUARTER].source_ref.provider_row_date == date(
        2025, 5, 29
    )
    assert eps_by_role[MetricPeriodRole.YEAR_AGO_QUARTER].source_ref.provider_row_date == date(
        2024, 8, 27
    )


def test_fetch_consensus_accepts_yfinance_earnings_date_within_fifteen_days(monkeypatch):
    from src.preprocessor import fetch_consensus

    class FakeTicker:
        earnings_dates = pd.DataFrame(
            [
                {"Reported EPS": 0.81, "EPS Estimate": 0.75, "Surprise(%)": 8.0},
                {"Reported EPS": 0.76, "EPS Estimate": 0.72, "Surprise(%)": 5.6},
                {"Reported EPS": 0.68, "EPS Estimate": 0.65, "Surprise(%)": 4.6},
            ],
            index=pd.to_datetime(["2025-08-28", "2025-05-29", "2024-08-27"]),
        )
        quarterly_financials = pd.DataFrame(
            [[123_000.0]],
            index=["Operating Revenue"],
            columns=pd.to_datetime(["2025-07-31"]),
        )
        quarterly_cashflow = pd.DataFrame(
            [[20_000.0], [-5_000.0]],
            index=["OperatingCashFlow", "Capital Expenditure"],
            columns=pd.to_datetime(["2025-07-31"]),
        )

        def __init__(self, ticker):
            self.ticker = ticker

    monkeypatch.setattr("src.preprocessor.yf.Ticker", FakeTicker)

    metrics = fetch_consensus(
        "nvda",
        "2025Q3",
        target_earnings_date=date(2025, 8, 29),
        target_period_end_date=date(2025, 7, 31),
    )

    eps_by_role = {
        metric.period_role: metric
        for metric in metrics.canonical_metrics
        if metric.metric_name == "eps"
    }
    assert eps_by_role[MetricPeriodRole.ACTUAL].value == 0.81
    assert eps_by_role[MetricPeriodRole.ACTUAL].source_ref.provider_row_date == date(2025, 8, 28)
    assert eps_by_role[MetricPeriodRole.PREVIOUS_QUARTER].value == 0.76
    assert eps_by_role[MetricPeriodRole.YEAR_AGO_QUARTER].value == 0.68


def test_fetch_consensus_accepts_yfinance_period_column_within_fifteen_days(monkeypatch):
    from src.preprocessor import fetch_consensus

    class FakeTicker:
        earnings_dates = pd.DataFrame(
            [{"Reported EPS": 0.81, "EPS Estimate": 0.75, "Surprise(%)": 8.0}],
            index=pd.to_datetime(["2025-08-28"]),
        )
        quarterly_financials = pd.DataFrame(
            [[123_000.0]],
            index=["Operating Revenue"],
            columns=pd.to_datetime(["2025-08-05"]),
        )
        quarterly_cashflow = pd.DataFrame(
            [[20_000.0], [-5_000.0]],
            index=["OperatingCashFlow", "Capital Expenditure"],
            columns=pd.to_datetime(["2025-08-05"]),
        )

        def __init__(self, ticker):
            self.ticker = ticker

    monkeypatch.setattr("src.preprocessor.yf.Ticker", FakeTicker)

    metrics = fetch_consensus(
        "nvda",
        "2025Q3",
        target_earnings_date=date(2025, 8, 28),
        target_period_end_date=date(2025, 7, 31),
    )

    assert metrics.revenue == 123_000.0
    assert metrics.operating_cash_flow == 20_000.0
    assert metrics.capex == -5_000.0
    assert metrics.free_cash_flow == 15_000.0


def test_build_normalized_review_request_registers_derived_metric_source_refs():
    metrics = build_financial_metrics(
        ticker="NVDA",
        fiscal_period="2025Q3",
        operating_cash_flow=20_000.0,
        capex=-5_000.0,
        source_refs=[
            SourceRef(
                source_id="financial_api:NVDA:2025Q3:operating_cash_flow",
                source_type=SourceType.FINANCIAL_API,
                metric_name="operating_cash_flow",
                reported_period="2025Q3",
            ),
            SourceRef(
                source_id="financial_api:NVDA:2025Q3:capex",
                source_type=SourceType.FINANCIAL_API,
                metric_name="capex",
                reported_period="2025Q3",
            ),
        ],
    )

    request = build_normalized_review_request(
        {
            "ticker": "NVDA",
            "fiscal_period": "2025Q3",
            "financial_metrics": metrics.model_dump(mode="json"),
            "raw_text": "Free cash flow conversion was pressured by investment.",
        }
    )

    assert "metric:NVDA:2025Q3:free_cash_flow:derived" in request.registered_source_ids


def test_fetch_consensus_without_target_dates_does_not_use_latest_yfinance_row(monkeypatch):
    from src.preprocessor import fetch_consensus

    class FakeTicker:
        earnings_dates = pd.DataFrame(
            [{"Reported EPS": 9.99, "EPS Estimate": 8.88, "Surprise(%)": 12.5}],
            index=pd.to_datetime(["2026-02-20"]),
        )
        quarterly_financials = pd.DataFrame(
            [[999_000.0]],
            index=["Operating Revenue"],
            columns=pd.to_datetime(["2026-01-31"]),
        )
        quarterly_cashflow = pd.DataFrame(
            [[99_000.0], [-9_000.0]],
            index=["OperatingCashFlow", "Capital Expenditure"],
            columns=pd.to_datetime(["2026-01-31"]),
        )

        def __init__(self, ticker):
            self.ticker = ticker

    monkeypatch.setattr("src.preprocessor.yf.Ticker", FakeTicker)

    metrics = fetch_consensus("nvda", "2025Q3")

    assert metrics.eps is None
    assert metrics.revenue is None
    assert metrics.operating_cash_flow is None
    assert metrics.availability
    assert {item.status for item in metrics.availability} >= {AvailabilityStatus.PERIOD_UNVERIFIED}


def test_fetch_financial_metrics_uses_sec_p0_to_fill_canonical_gaps(monkeypatch):
    from src.preprocessor import fetch_financial_metrics

    monkeypatch.setattr(
        "src.preprocessor.fetch_consensus",
        lambda *args, **kwargs: build_financial_metrics(
            ticker="NVDA",
            fiscal_period="2025Q3",
            eps=0.81,
            eps_consensus=0.75,
            free_cash_flow=999,
            source_refs=[
                SourceRef(
                    source_id="financial_api:NVDA:2025Q3:yfinance:eps",
                    source_type=SourceType.FINANCIAL_API,
                    metric_name="eps",
                    reported_period="2025Q3",
                    provider="yfinance",
                    period_role=MetricPeriodRole.ACTUAL,
                )
            ],
        ),
    )
    monkeypatch.setattr(
        "src.sec_company_facts.build_sec_company_facts_metrics",
        lambda *args, **kwargs: build_financial_metrics(
            ticker="NVDA",
            fiscal_period="2025Q3",
            revenue=35_000_000_000,
            operating_cash_flow=15_000_000_000,
            capex=-3_000_000_000,
            source_refs=[
                SourceRef(
                    source_id="financial_api:NVDA:2025Q3:sec:revenue",
                    source_type=SourceType.FINANCIAL_API,
                    metric_name="revenue",
                    reported_period="2025Q3",
                    provider="sec_company_facts",
                    period_role=MetricPeriodRole.ACTUAL,
                ),
                SourceRef(
                    source_id="financial_api:NVDA:2025Q3:sec:operating_cash_flow",
                    source_type=SourceType.FINANCIAL_API,
                    metric_name="operating_cash_flow",
                    reported_period="2025Q3",
                    provider="sec_company_facts",
                    period_role=MetricPeriodRole.ACTUAL,
                ),
                SourceRef(
                    source_id="financial_api:NVDA:2025Q3:sec:capex",
                    source_type=SourceType.FINANCIAL_API,
                    metric_name="capex",
                    reported_period="2025Q3",
                    provider="sec_company_facts",
                    period_role=MetricPeriodRole.ACTUAL,
                ),
            ],
        ),
    )

    metrics = fetch_financial_metrics(
        "NVDA",
        "2025Q3",
        target_period_end_date=date(2025, 10, 31),
    )

    assert metrics.revenue == 35_000_000_000
    assert metrics.operating_cash_flow == 15_000_000_000
    assert metrics.capex == -3_000_000_000
    assert metrics.free_cash_flow == 12_000_000_000
    availability = {item.key: item.status for item in metrics.availability}
    assert {
        ("revenue", AvailabilityStatus.AVAILABLE),
        ("operating_cash_flow", AvailabilityStatus.AVAILABLE),
        ("capex", AvailabilityStatus.AVAILABLE),
        ("free_cash_flow", AvailabilityStatus.AVAILABLE),
    }.issubset(set(availability.items()))
    assert {ref.provider for ref in metrics.source_refs if ref.metric_name == "revenue"} == {
        "sec_company_facts"
    }
    assert not [
        ref
        for ref in metrics.source_refs
        if ref.metric_name == "free_cash_flow" and ref.provider == "yfinance"
    ]
    assert metrics.derived_metrics
    assert metrics.derived_metrics[0].metric_name == "free_cash_flow"


def test_build_normalized_review_request_fetches_sec_when_presentation_sections_exist(
    monkeypatch,
):
    filing_url = "https://www.sec.gov/Archives/example/sample.htm"
    calls = {}

    monkeypatch.setattr(
        "src.preprocessor.fetch_consensus",
        lambda ticker, fiscal_period, **kwargs: build_financial_metrics(
            ticker=ticker,
            fiscal_period=fiscal_period,
            eps=0.81,
            eps_consensus=0.75,
        ),
    )

    def fake_fetch_filing_html(url):
        calls["fetch_url"] = url
        return "<html>mock filing</html>"

    def fake_segment_filing(html, url=None):
        return [
            DocumentSection(
                section_id="filing:risk",
                source_ref=SourceRef(
                    source_id="filing:risk",
                    source_type=SourceType.FILING,
                    url=filing_url,
                    document_id="filing-html",
                    section_id="filing:risk",
                    title="Filing risk",
                ),
                heading="risk",
                text="Risk factors discuss demand uncertainty.",
            )
        ]

    monkeypatch.setattr("src.preprocessor.fetch_filing_html", fake_fetch_filing_html)
    monkeypatch.setattr("src.preprocessor.segment_filing", fake_segment_filing)

    request = build_normalized_review_request(
        {
            "ticker": "nvda",
            "fiscal_period": "2025Q3",
            "raw_text": "Page 5\nManagement guidance assumes durable demand.",
            "filing_url": filing_url,
            "use_sec": True,
        }
    )

    assert calls == {"fetch_url": filing_url}
    assert {section.source_ref.source_type for section in request.document_sections} == {
        SourceType.MANUAL_UPLOAD,
        SourceType.FILING,
    }


def test_segment_filing_extracts_semantic_sections():
    html = Path("tests/fixtures/sample_filing.html").read_text(encoding="utf-8")
    filing_url = "https://www.sec.gov/Archives/example/sample.htm"

    sections = segment_filing(html, url=filing_url)
    names = {section.heading for section in sections}

    assert {"revenue", "eps", "guidance", "segments", "risk"}.issubset(names)
    assert all(section.text for section in sections)
    assert all(section.source_ref.source_id for section in sections)
    assert all(str(section.source_ref.url) == filing_url for section in sections)


def test_segment_filing_uses_env_section_cap(monkeypatch):
    monkeypatch.setenv("EARNINGS_DEBATE_MAX_DOCUMENT_SECTION_CHARS", "40")
    html = "<html><body><p>net revenue " + ("x" * 100) + "</p></body></html>"

    sections = segment_filing(html, url="https://www.sec.gov/Archives/example/sample.htm")

    assert len(sections) == 1
    assert sections[0].heading == "revenue"
    assert len(sections[0].text) == 40


def test_document_files_to_sections_extracts_local_text_fixture():
    sections = document_files_to_sections(
        [
            DocumentFile(
                path="tests/fixtures/sample_presentation.txt",
                source_type="earnings_presentation",
                document_id="sample-presentation",
                title="Sample earnings presentation",
            )
        ]
    )

    assert len(sections) == 1
    section = sections[0]
    assert section.section_id == "sample-presentation:section-1"
    assert section.source_ref.source_id == "sample-presentation:section-1"
    assert section.source_ref.source_type == "earnings_presentation"
    assert section.source_ref.document_id == "sample-presentation"
    assert section.source_ref.section_id == "sample-presentation:section-1"
    assert section.source_ref.title == "Sample earnings presentation"
    assert "Free cash flow was pressured" in section.text


def test_document_files_to_sections_uses_env_chunk_cap(monkeypatch, tmp_path):
    monkeypatch.setenv("EARNINGS_DEBATE_MAX_DOCUMENT_SECTION_CHARS", "20")
    source = tmp_path / "presentation.txt"
    source.write_text("A" * 45, encoding="utf-8")

    sections = document_files_to_sections(
        [
            DocumentFile(
                path=str(source),
                source_type="earnings_presentation",
                document_id="sample-presentation",
                title="Sample earnings presentation",
            )
        ]
    )

    assert [len(section.text) for section in sections] == [20, 20, 5]


def test_fetch_filing_html_uses_env_cache_key_length_dir_and_timeout(monkeypatch, tmp_path):
    captured = {}

    class FakeResponse:
        text = "<html>mock filing</html>"

        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    cache_dir = tmp_path / "filing-cache"
    monkeypatch.setenv("EARNINGS_DEBATE_SEC_FILING_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("EARNINGS_DEBATE_SEC_CACHE_KEY_LENGTH", "8")
    monkeypatch.setenv("EARNINGS_DEBATE_SEC_REQUEST_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setattr("requests.get", fake_get)

    html = fetch_filing_html("https://www.sec.gov/Archives/example/sample.htm")

    assert html == "<html>mock filing</html>"
    assert captured["timeout"] == 12.5
    cached_files = list(cache_dir.glob("*.html"))
    assert len(cached_files) == 1
    assert len(cached_files[0].stem) == 8


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("tests/fixtures/missing_presentation.txt", "does not exist"),
        ("tests/fixtures/sample_filing.html", "unsupported document file extension"),
    ],
)
def test_document_files_to_sections_rejects_invalid_files(path, message):
    with pytest.raises(ValueError, match=message):
        document_files_to_sections(
            [
                DocumentFile(
                    path=path,
                    source_type="earnings_presentation",
                    document_id="sample-presentation",
                    title="Sample earnings presentation",
                )
            ]
        )
