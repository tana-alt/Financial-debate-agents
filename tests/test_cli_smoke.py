from __future__ import annotations

import json

from click.testing import CliRunner

from src.main import cli
from src.preprocessor import build_financial_metrics
from src.workflow_models import DocumentSection, SourceRef, SourceType


def _write_document_files_payload(tmp_path):
    payload = {
        "request_id": "test-local-presentation-sample",
        "ticker": "NVDA",
        "fiscal_period": "2025Q3",
        "include_markdown": True,
        "financial_metrics": {
            "ticker": "NVDA",
            "fiscal_period": "2025Q3",
            "currency": "USD",
            "eps": 0.81,
            "eps_consensus": 0.75,
            "eps_surprise_pct": 8.0,
            "revenue": 35000000000,
            "revenue_consensus": 33000000000,
            "revenue_surprise_pct": 6.06,
            "operating_margin_pct": 62.0,
            "operating_cash_flow": 15000000000,
            "capex": -3000000000,
            "source_refs": [
                {
                    "source_id": "financial_api:NVDA:2025Q3:yfinance:eps",
                    "source_type": "financial_api",
                    "metric_name": "eps",
                    "title": "Fixture yfinance EPS",
                    "provider": "yfinance",
                    "reported_period": "2025Q3",
                    "period_role": "actual",
                },
                {
                    "source_id": "financial_api:NVDA:2025Q3:sec:revenue",
                    "source_type": "financial_api",
                    "metric_name": "revenue",
                    "title": "Fixture SEC revenue",
                    "provider": "sec_company_facts",
                    "reported_period": "2025Q3",
                    "period_role": "actual",
                },
                {
                    "source_id": "financial_api:NVDA:2025Q3:sec:operating_cash_flow",
                    "source_type": "financial_api",
                    "metric_name": "operating_cash_flow",
                    "title": "Fixture SEC operating cash flow",
                    "provider": "sec_company_facts",
                    "reported_period": "2025Q3",
                    "period_role": "actual",
                },
                {
                    "source_id": "financial_api:NVDA:2025Q3:sec:capex",
                    "source_type": "financial_api",
                    "metric_name": "capex",
                    "title": "Fixture SEC capex",
                    "provider": "sec_company_facts",
                    "reported_period": "2025Q3",
                    "period_role": "actual",
                },
            ],
        },
        "document_files": [
            {
                "path": "tests/fixtures/sample_presentation.txt",
                "source_type": "earnings_presentation",
                "document_id": "test-sample-presentation",
                "title": "Test sample earnings presentation",
            }
        ],
    }
    path = tmp_path / "request.document-files.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


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
            "samples/request.nvda-2027q1.example.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    workflow_result = json.loads((out_dir / "workflow_result.json").read_text(encoding="utf-8"))

    assert workflow_result["ticker"] == "NVDA"
    assert workflow_result["fiscal_period"] == "2027Q1"
    assert workflow_result["status"] == "completed"
    assert "claim_matrix" in workflow_result
    assert "metric:NVDA:2027Q1:free_cash_flow:derived" in {
        source["source_id"] for source in workflow_result["claim_matrix"]["source_manifest"]
    }
    assert workflow_result["judge_decision"]["verdict"] in {"good", "neutral", "bad"}
    for expected in (
        "NVDA",
        "2027Q1",
        "## レポート前提: canonical data",
        "## 判定理由",
        "## 根拠マトリクス (Evidence Matrix)",
        "## 品質ゲート (Quality Gates)",
        "## 免責事項",
        "| Claim ID | Fact | Interpretation | Implication | Time scope |",
    ):
        assert expected in report


def test_cli_fake_smoke_accepts_document_files(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    out_dir = tmp_path / "out"
    input_json = _write_document_files_payload(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--input-json",
            str(input_json),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    workflow_result = json.loads((out_dir / "workflow_result.json").read_text(encoding="utf-8"))
    assert workflow_result["ticker"] == "NVDA"
    assert workflow_result["judge_decision"]["verdict"] in {"good", "neutral", "bad"}
    assert "## 根拠マトリクス (Evidence Matrix)" in report
    assert "## ソース付録 (Source Appendix)" in report


def test_cli_fake_smoke_accepts_current_local_presentation_sample(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setattr("src.workflow._fetch_consensus", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.workflow._fetch_filing_html", lambda *args, **kwargs: "")

    out_dir = tmp_path / "out"
    input_json = _write_document_files_payload(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--input-json",
            str(input_json),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    workflow_result = json.loads((out_dir / "workflow_result.json").read_text(encoding="utf-8"))
    assert workflow_result["ticker"] == "NVDA"
    assert workflow_result["judge_decision"]["verdict"] in {"good", "neutral", "bad"}
    assert "## データ品質" in report
    assert "## 根拠マトリクス (Evidence Matrix)" in report
    assert "test-sample-presentation:section-1" in report


def test_cli_fake_smoke_accepts_zs_canonical_sample(monkeypatch, tmp_path):
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
            "samples/request.zs-2026q3.example.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    workflow_result = json.loads((out_dir / "workflow_result.json").read_text(encoding="utf-8"))
    assert workflow_result["ticker"] == "ZS"
    assert workflow_result["fiscal_period"] == "2026Q3"
    assert workflow_result["status"] == "completed"
    assert "metric:ZS:2026Q3:free_cash_flow:derived" in {
        source["source_id"] for source in workflow_result["claim_matrix"]["source_manifest"]
    }
    assert "## 根拠マトリクス (Evidence Matrix)" in report


def test_cli_api_mode_posts_normalized_payload_without_raw_acquisition(monkeypatch, tmp_path):
    filing_url = "https://www.sec.gov/Archives/example/sample.htm"
    captured = {}

    monkeypatch.setattr(
        "src.preprocessor.fetch_consensus",
        lambda ticker, fiscal_period, **kwargs: build_financial_metrics(
            ticker=ticker,
            fiscal_period=fiscal_period,
            eps=0.81,
            eps_consensus=0.75,
        ),
    )
    monkeypatch.setattr(
        "src.preprocessor.fetch_filing_html", lambda url: "<html>mock filing</html>"
    )
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


def test_cli_api_mode_uses_env_defaults_without_overriding_explicit_args(monkeypatch, tmp_path):
    captured = {}

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

    env_out_dir = tmp_path / "env-out"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--input-json",
            "samples/request.nvda-2027q1.example.json",
        ],
        env={
            "EARNINGS_DEBATE_API_URL": "http://api.env",
            "EARNINGS_DEBATE_OUTPUT_DIR": str(env_out_dir),
            "EARNINGS_DEBATE_API_REQUEST_TIMEOUT_SECONDS": "12.5",
        },
    )

    assert result.exit_code == 0, result.output
    assert captured["url"] == "http://api.env/reviews"
    assert captured["timeout"] == 12.5
    assert (env_out_dir / "report.md").exists()

    explicit_out_dir = tmp_path / "explicit-out"
    result = runner.invoke(
        cli,
        [
            "run",
            "--api-url",
            "http://api.explicit",
            "--input-json",
            "samples/request.nvda-2027q1.example.json",
            "--out",
            str(explicit_out_dir),
        ],
        env={
            "EARNINGS_DEBATE_API_URL": "http://api.env",
            "EARNINGS_DEBATE_OUTPUT_DIR": str(env_out_dir),
            "EARNINGS_DEBATE_API_REQUEST_TIMEOUT_SECONDS": "15",
        },
    )

    assert result.exit_code == 0, result.output
    assert captured["url"] == "http://api.explicit/reviews"
    assert captured["timeout"] == 15.0
    assert (explicit_out_dir / "report.md").exists()


def test_cli_serve_uses_env_host_and_port_defaults(monkeypatch):
    captured = {}

    def fake_run(app, host, port, reload):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr("uvicorn.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["serve"],
        env={
            "EARNINGS_DEBATE_API_HOST": "0.0.0.0",
            "EARNINGS_DEBATE_API_PORT": "9000",
        },
    )

    assert result.exit_code == 0, result.output
    assert captured == {
        "app": "src.api:app",
        "host": "0.0.0.0",
        "port": 9000,
        "reload": False,
    }
