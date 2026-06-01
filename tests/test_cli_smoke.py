from __future__ import annotations

import json

from click.testing import CliRunner

from src.main import cli
from src.preprocessor import build_financial_metrics
from src.workflow_models import DocumentSection, SourceRef, SourceType


def test_cli_fake_smoke_writes_report_and_workflow_result(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--input-json",
            "samples/request.example.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    workflow_result = json.loads((out_dir / "workflow_result.json").read_text(encoding="utf-8"))

    assert workflow_result["ticker"] == "NVDA"
    assert workflow_result["fiscal_period"] == "2025Q3"
    assert workflow_result["judge_decision"]["verdict"] in {"good", "neutral", "bad"}
    for expected in (
        "NVDA",
        "2025Q3",
        "## Verdict",
        "## Positive Evidence",
        "## Negative Evidence",
        "## EPS Outlook",
        "## FCF Outlook",
    ):
        assert expected in report


def test_cli_fake_smoke_accepts_document_files(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--input-json",
            "samples/request.document-files.example.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    workflow_result = json.loads((out_dir / "workflow_result.json").read_text(encoding="utf-8"))
    assert workflow_result["ticker"] == "NVDA"
    assert workflow_result["judge_decision"]["verdict"] in {"good", "neutral", "bad"}
    assert "## Negative Evidence" in report


def test_cli_api_mode_posts_normalized_payload_without_raw_acquisition(monkeypatch, tmp_path):
    filing_url = "https://www.sec.gov/Archives/example/sample.htm"
    captured = {}

    monkeypatch.setattr(
        "src.preprocessor.fetch_consensus",
        lambda ticker, fiscal_period: build_financial_metrics(
            ticker=ticker,
            fiscal_period=fiscal_period,
            eps=0.81,
            eps_consensus=0.75,
        ),
    )
    monkeypatch.setattr("src.preprocessor.fetch_filing_html", lambda url: "<html>mock filing</html>")
    monkeypatch.setattr(
        "src.preprocessor.segment_filing",
        lambda html, url=None: [
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
        ],
    )

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "ticker": "NVDA",
                "fiscal_period": "2025Q3",
                "judge_decision": {"verdict": "neutral", "confidence": 0.5},
                "markdown_report": "# Earnings Review\n\n## Verdict\n\nNeutral",
            }

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("src.main.requests.post", fake_post)

    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--api-url",
            "http://api.test",
            "--ticker",
            "nvda",
            "--fiscal-period",
            "2025Q3",
            "--filing-url",
            filing_url,
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    posted = captured["json"]
    assert captured["url"] == "http://api.test/reviews"
    assert captured["timeout"] == 300
    assert "filing_url" not in posted
    assert "document_files" not in posted
    assert posted["schema_version"] == "normalized-review-request.v1"
    assert posted["ticker"] == "NVDA"
    assert posted["document_sections"][0]["section_id"] == "filing:guidance"
    assert {source["source_id"] for source in posted["source_manifest"]} == {
        "financial_api:NVDA:2025Q3",
        "filing:guidance",
    }
