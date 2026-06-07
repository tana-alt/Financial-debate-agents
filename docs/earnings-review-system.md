# Earnings Review System Details

この文書は Earnings Debate Agent のシステム面を説明する README 派生ドキュメントです。
動機、設計思想、開発背景は README 側の担当範囲とし、ここでは実装から確認できる処理責務、入出力契約、検証観点、運用設定だけを扱います。

## 1. System Boundary

### 観測事実

- API の実行境界は `POST /reviews` です。`src/api.py` は request body を `NormalizedReviewRequest` として検証し、成功時は `ReviewSuccessResponse`、dry-run 時は `ReviewDryRunResponse`、失敗時は `ReviewErrorResponse` 系の envelope を返します。
- `NormalizedReviewRequest` は `src/workflow_models.py` で定義され、`schema_version`、`request_id`、`ticker`、`fiscal_period`、`financial_metrics`、`document_sections`、`source_manifest`、`context_budget`、`include_markdown`、`purpose`、`is_investment_advice`、`dry_run` を持ちます。
- API 入力では raw acquisition fields が拒否されます。`NormalizedReviewRequest.reject_raw_fields()` が `filing_url`、`raw_text`、`document_files` などの取得用 field を normalized API contract から切り離しています。
- CLI は raw/local input を扱えます。`src/main.py` の `earnings-debate run` は `src/preprocessor.py` の `build_normalized_review_request()` を通じて sample JSON、local file、raw text、filing URL などを正規化し、API または local fake provider 実行に渡します。
- 最終レスポンスと Markdown は `purpose="earnings_review_not_investment_advice"`、`is_investment_advice=False`、disclaimer を持つ契約です。

### 推論

この境界により、API は「取得と正規化が完了した payload の検証と workflow 実行」に集中し、raw document acquisition は CLI/preprocessor 側へ寄せられています。運用上は、外部取得処理を変更しても API の normalized contract を保てることが重要です。

## 2. Workflow Overview

### 観測事実

中核の同期 workflow は `src/workflow.py` の `ReviewWorkflow.run()` です。処理順序は固定されています。

1. `data_ingestion`
2. `financial_agents`
3. `presentation_agents`
4. `evidence_aggregation`
5. `debate`
6. `judge`
7. `markdown_renderer`

各 step は `StepStatus` として記録され、失敗時は該当 step に error が残る構造です。LLM 呼び出しは agent runtime と debate/judge runner に閉じ込められ、最終 Markdown は renderer が決定的に生成します。

### 推論

この workflow は LLM に手順選択を任せる agentic loop ではありません。Python 側が順序、入力契約、source scope、validation gate、Markdown rendering を管理し、LLM は役割別の構造化分析を返す部品として使われます。

## 3. Data Processor / Normalization

### 観測事実

`src/preprocessor.py` の `build_normalized_review_request()` は CLI/local payload を `NormalizedReviewRequest` に変換します。

対応する入力面は次の通りです。

- すでに normalized された payload
- `document_sections`
- `document_files`
- `local_path`
- `raw_text`
- `filing_url`
- ticker / fiscal period などの最小実行情報

文書入力は `DocumentSection` に変換され、各 section には `SourceRef` が付きます。`fetch_filing_html()` は SEC filing HTML を取得し、`segment_filing()` が filing text を topic section に分割します。PDF/text/Markdown などの local file は `document_files_to_sections()` 側で section 化されます。

財務データは `FinancialMetrics` として正規化されます。yfinance 由来の EPS / revenue / cash flow 系 metric と、SEC Company Facts 由来の revenue / operating cash flow / capex を統合し、Python 側で canonical metrics、derived metrics、availability、metric conflict を構築します。FCF などの派生値も Python 側で扱われ、LLM が raw 財務表から直接計算する設計ではありません。

### 推論

Data processor の責務は「取得済みまたは取得可能な入力を、source traceable な normalized contract に揃えること」です。LLM の自由記述に任せる前に、数値、期間、source、availability を構造化することで、後段 gate と renderer が検証可能になります。

## 4. Context Routing

### 観測事実

`src/context_router.py` の `ContextRouter` は `NormalizedReviewRequest` から role 別 context を作ります。`ROLE_CONTEXT_KEYS` は role ごとに渡せる key を固定しています。

- `EarningsQualityAnalyst`: EPS / P&L / revenue / margin / one-time items などの earnings quality context
- `CashFlowRiskAnalyst`: operating cash flow / FCF / capex / working capital / liquidity / debt などの cash-flow risk context
- `ManagementIntentAnalyst`: management / strategy / MD&A / risk / capital allocation などの management context
- `GuidanceAnalyst`: guidance metrics / consensus deltas / guidance sections / assumptions / track record などの guidance context
- `BullAgent`: validated brief と positive/negative evidence pool
- `BearAgent`: validated brief、Bull summary、positive/negative evidence pool
- `JudgeAgent`: validated brief、Bull/Bear case、evidence pool

Router は `source_manifest` と各 `source_ref` の整合性を検証します。role context には source scope に応じた `source_index` が付きます。さらに stable compact JSON の文字数を 4 で割る概算 token counter を使い、`context_budget.max_input_tokens` と `max_total_tokens` を LLM 呼び出し前に検証します。

### 推論

Context routing は「全情報を全 agent に渡す」設計ではなく、role ごとに必要な context と source index を絞る設計です。これにより、役割境界、source traceability、context budget gate を同時に満たします。

## 5. Agent Set And Responsibilities

### 観測事実

runtime agent は次の 7 つです。名前は `src/workflow_agents.py` と `tests/test_workflow_e2e.py` で確認できます。

| Agent | 主な責務 | 主な入力 |
|---|---|---|
| `EarningsQualityAnalyst` | EPS surprise と P&L の質、売上品質、margin trend、一時要因/継続要因、将来 EPS への示唆を分析する | earnings quality metrics / sections |
| `CashFlowRiskAnalyst` | CFO、FCF、CapEx、working capital、liquidity、debt、financing constraint を統合し、将来 FCF 改善方向とリスクを分析する | cash flow / balance sheet / risk context |
| `ManagementIntentAnalyst` | 経営陣の意図、優先順位、投資判断、EPS/FCF への時間軸別示唆を分析する | management / strategy / MD&A / risk sections |
| `GuidanceAnalyst` | guidance、precomputed consensus 差分、前提、達成可能性、revision risk を分析する | guidance metrics / consensus deltas / guidance sections |
| `BullAgent` | validated `AnalysisBrief` だけから positive case を作る | brief と validated evidence pool |
| `BearAgent` | validated `AnalysisBrief` と必要に応じて Bull summary から downside/neutral case を作る | brief、Bull summary、validated evidence pool |
| `JudgeAgent` | Bull/Bear を比較し `good` / `neutral` / `bad` を判定する | brief、Bull/Bear case、validated evidence pool |

各 agent は `AgentSpec` を持ち、public role、出力 model、context keys、system prompt、task prompt、token cap、temperature を定義します。`WorkflowAgent.run()` は LLM 出力を JSON として parse し、Pydantic model で検証します。role mismatch や schema mismatch は workflow error として扱われ、repair retry の対象になる場合があります。

### 推論

Specialist agent は一次分析を作り、Bull/Bear/Judge は検証済み brief と evidence pool だけを使う後段 role です。この分離により、討論・判定段階で raw source を読み直して未検証の根拠を増やす動きを抑えています。

## 6. Evidence Validation

### 観測事実

`src/workflow_validation.py` の `WorkflowValidationGate.aggregate_evidence()` は specialist findings から positive / negative evidence pool を作ります。空の positive pool または negative pool は workflow validation error です。

主な validation は次の通りです。

- evidence の `source_ref` が request の canonical source set と整合すること
- 同じ source を参照する evidence は canonical source ref に寄せること
- material claim が numeric grounding か明示的な missing-data caveat を持つこと
- grounding されていない material evidence は、代替根拠が残る場合 Judge candidate pool から除外すること
- Bull/Bear/Judge が選ぶ evidence id は validated `AnalysisBrief` 内の候補に存在すること
- Judge の positive evidence は positive polarity、negative evidence は negative/risk polarity であること
- investment-advice language は warning 化し、deterministic rendering 前に redaction すること

`ReportMatrix` は `src/workflow_models.py` で、`source_manifest`、`evidence_items`、`claim_records`、`decision_uses`、`missing_data_items`、`data_quality_flags` を持ちます。model validator は duplicate evidence id、unregistered source ref、unregistered evidence id、decision use と claim/evidence の不整合を拒否します。

### 推論

Evidence validation は LLM 出力の「もっともらしい文章」をそのまま判定材料にせず、source ref、polarity、numeric grounding、候補 pool への所属を deterministic に確認する gate です。

## 7. Quality Gates

### 観測事実

この system で確認できる主な gate は次の通りです。

| Gate | 実装面 | 失敗時の扱い |
|---|---|---|
| Normalized input contract | `NormalizedReviewRequest` validation | API 422 envelope |
| Raw acquisition field rejection | `reject_raw_fields()` | API 422 envelope |
| Runtime required input | `_runtime_required_input_error()` | API 422 envelope |
| Source manifest consistency | `ContextRouter` / model validators / `WorkflowValidationGate` | API 422 または workflow validation error |
| Context budget | `ContextRouter.check_budget()` | LLM 呼び出し前に 422 |
| Guidance acquisition | `report_quality_guidance.validate_guidance_required()` | guidance source 不足を検出 |
| Numeric grounding | `report_quality_numeric_grounding` と evidence degradation | warning または candidate pool 除外 |
| Missing-data confidence cap | `report_quality_missing_data.apply_confidence_caps()` | Judge confidence を上限で cap |
| Investment-advice language | `WorkflowValidationGate.investment_advice_warnings()` | warning + redaction |
| ReportMatrix reference validation | `ReportMatrix.validate_references()` | model validation error |

Guidance gate と numeric grounding gate は環境変数で legacy test 用に無効化できる実装がありますが、既定は有効です。`.env` の実値はこの調査では読まず、`.env.example` にある公開テンプレートだけを参照しています。

### 推論

Gate は「投資判断を自動化するため」ではなく、「source-backed な決算分析 artifact として破綻しないため」の防御線です。特に missing-data confidence cap は、必要な canonical data が欠ける場合に判定の強さを制約します。

## 8. Report Rendering

### 観測事実

最終 Markdown は `src/report_renderer.py` の `ReportRenderer` が生成します。LLM が Markdown report を直接書くのではなく、validated `AnalysisBrief`、`DebateResult`、`JudgeDecision`、`ReportMatrix` から固定順の section を組み立てます。

現在の section order は次の通りです。

1. `レポート前提: canonical data`
2. `要約`
3. `判定理由`
4. `EPS/FCF見通し`
5. `Bull/Bear論点`
6. `Agent分析`
7. `根拠マトリクス (Evidence Matrix)`
8. `データ品質`
9. `不確実性と不足データ`
10. `品質ゲート (Quality Gates)`
11. `ソース付録 (Source Appendix)`
12. `免責事項`

Report は canonical metrics table、Judge rationale、Bull/Bear 論点、agent contribution、claim/evidence matrix、data quality flags、source appendix、disclaimer を含みます。`tests/test_workflow_e2e.py`、`tests/test_api_smoke.py`、`tests/test_cli_smoke.py` は主要 section が出力されることを検証しています。

### 推論

Renderer は LLM 生成文の最終整形ではなく、検証済み構造化データを人間が読める報告書へ変換する deterministic layer です。そのため、report section の追加・削除は output contract 変更として扱う必要があります。

## 9. CLI

### 観測事実

CLI entrypoint は `pyproject.toml` の `earnings-debate = "src.main:cli"` です。`src/main.py` は Click command として `serve` と `run` を提供します。

- `earnings-debate serve`: FastAPI app を uvicorn で起動します。
- `earnings-debate run`: input JSON、ticker/fiscal period、filing URL、local file、raw text などを受け取り、normalized payload を作って `POST /reviews` へ送ります。
- `--api-url local`、または `LLM_PROVIDER=fake` かつ default local API URL の場合、CLI は network POST ではなく local `ReviewWorkflow(get_provider()).run()` を実行します。
- 出力 artifact は `workflow_result.json` と `report.md` です。

`tests/test_cli_smoke.py` は fake provider を使って CLI が report と workflow result を書くこと、raw acquisition fields を API mode の payload に残さないことを検証しています。

### 推論

CLI は API-first workflow の薄い adapter です。運用上は「local acquisition と normalized API contract の橋渡し」として理解すると、API 側へ raw source handling を混ぜずに済みます。

## 10. API

### 観測事実

FastAPI app は `src/api.py` の `app = FastAPI(title="Earnings Debate Agent API")` です。主要 endpoint は `POST /reviews` です。

通常実行の流れ:

1. body が JSON object であることを確認
2. `NormalizedReviewRequest` として validation
3. `dry_run=false` の場合、runtime required input と context budget を preflight
4. `ReviewWorkflow` を解決し、legacy `ReviewRequest` へ bridge
5. workflow 実行結果から `ReviewSuccessResponse` を構築

dry-run の流れ:

1. normalized contract check
2. source manifest check
3. runtime required input check
4. context budget check
5. provider/workflow を解決せずに `ReviewDryRunResponse` を返す

`tests/test_api_contract.py` は dry-run が external fetch や workflow provider 解決を行わないこと、context budget failure が workflow 前に発生すること、quality-gate failure が 422 envelope になることを検証しています。

### 推論

dry-run は「LLM と外部 provider に到達する前の契約検査」です。CI や integration では、payload の schema/source/context 問題を早期に切り分ける用途に向いています。

## 11. CI And Test Gates

### 観測事実

`Makefile` は次の主要 target を提供します。

- `make test`: `uv run pytest`
- `make test-fast`: `tests/test_contract_models.py`、`tests/test_extension_surface_integrity.py`、`tests/test_system_design_integrity.py` の structural smoke
- `make check-fast`: format check、lint、hook syntax、lane map check、test-fast
- `make check-required`: format/lint/typecheck/hooks/shell/hygiene/secrets/lane/test
- `make check-ci`: toolchain、required checks、CD guard
- `make check-foundation`: `check-ci`
- `make check-doc-consistency`: foundation integrity の doc consistency / work contract git scope subset

`pyproject.toml` は pytest の `testpaths = ["tests"]`、ruff、mypy、dependency を定義します。`.github/workflows/ci.yml` は Ubuntu runner で uv、shellcheck、gitleaks を準備し、`make check-foundation` を実行します。

テストは外部 API key に依存しない形を持ちます。`tests/test_workflow_e2e.py` は `LLM_PROVIDER=fake` と `FakeProvider` で 7 agent workflow を API key なしに実行します。API/CLI/preprocessor 系テストは `monkeypatch` で fetch や provider を差し替える箇所があります。

### 推論

通常の system 変更では、まず最小の対象 pytest を実行し、shared contract や output surface を触る場合に `make check-required` / `make check-foundation` へ広げるのが妥当です。CI/GitHub Actions 自体を変える場合は human gate 対象です。

## 12. Configuration / Environment Variables

### 観測事実

公開テンプレート `.env.example` と `src/runtime_config.py` / `src/llm.py` / `src/main.py` / `src/preprocessor.py` / `src/workflow_agents.py` / `src/workflow_runtime.py` から確認できる主要設定面は次の通りです。

| Surface | Env var | 用途 |
|---|---|---|
| LLM provider | `LLM_PROVIDER` | `fake` / `anthropic` / `openai` の provider 選択 |
| Anthropic auth/model | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | Anthropic SDK が env から key を読み、model を選択 |
| OpenAI auth/model | `OPENAI_API_KEY`, `OPENAI_MODEL` | OpenAI SDK が env から key を読み、model を選択 |
| SEC access | `SEC_USER_AGENT` | SEC EDGAR request の user-agent |
| Logging | `LOG_LEVEL` | CLI logging level |
| CLI/API local defaults | `EARNINGS_DEBATE_API_HOST`, `EARNINGS_DEBATE_API_PORT`, `EARNINGS_DEBATE_API_URL`, `EARNINGS_DEBATE_OUTPUT_DIR`, `EARNINGS_DEBATE_API_REQUEST_TIMEOUT_SECONDS` | local server / CLI POST / output artifact の既定値 |
| LLM call defaults | `EARNINGS_DEBATE_LLM_DEFAULT_MAX_TOKENS`, `EARNINGS_DEBATE_LLM_DEFAULT_TEMPERATURE`, `EARNINGS_DEBATE_OPENAI_MIN_COMPLETION_TOKENS` | provider direct call と OpenAI completion token floor |
| Agent/runtime tunables | `EARNINGS_DEBATE_AGENT_MAX_TOKENS`, `EARNINGS_DEBATE_DEBATE_MAX_TOKENS`, `EARNINGS_DEBATE_JUDGE_MAX_TOKENS`, `EARNINGS_DEBATE_AGENT_TEMPERATURE`, `EARNINGS_DEBATE_JUDGE_TEMPERATURE`, `EARNINGS_DEBATE_AGENT_MAX_RETRIES`, `EARNINGS_DEBATE_AGENT_MAX_WORKERS`, `EARNINGS_DEBATE_DEBATE_SELECTION_ATTEMPTS`, `EARNINGS_DEBATE_JUDGE_SELECTION_ATTEMPTS` | agent 出力長、temperature、retry、並列数、selection retry |
| Acquisition/network/cache | `EARNINGS_DEBATE_SEC_REQUEST_TIMEOUT_SECONDS`, `EARNINGS_DEBATE_SEC_FILING_CACHE_DIR`, `EARNINGS_DEBATE_SEC_CACHE_KEY_LENGTH`, `EARNINGS_DEBATE_MAX_DOCUMENT_SECTION_CHARS` | SEC request timeout、filing cache、document section chunk cap |
| Quality gates | `EARNINGS_DEBATE_REQUIRE_GUIDANCE`, `EARNINGS_DEBATE_REQUIRE_NUMERIC_GROUNDING` | guidance / numeric grounding gate の既定有効化 |

`src/runtime_config.py` は unset または空文字を既存 default として扱い、不正な int / float / bool / path は `ValueError` にします。CLI の明示オプションは env default より優先されます。

`.env` や secret-bearing file は読んでいません。secret 値は docs に書かず、`.env.example` のような空または placeholder のテンプレートだけを使います。

### 推論

deploy ごとに変わる provider、model、API key、SEC user-agent、logging、local URL、timeout、cache 位置、LLM token cap は環境変数で切り替える面です。一方で API schema、role 名、safety invariant、financial metric semantics、report section order は設定ではなく contract として扱う方が安全です。

## 13. Limitations And Non-Goals

### No-Go Scope

この system は次を行いません。

- 株価予測
- 目標株価の提示
- 売買推奨
- 自動売買
- portfolio optimization
- LLM による raw 財務表からの未検証計算
- source-backed でない外部 web/news/analyst 情報を主 verdict に混ぜること

### 現在の制約

- SEC filing segmentation は HTML text block と header pattern に依存します。filing format の差異には継続対応が必要です。
- PDF は text layer 抽出が前提です。OCR 前提の scan PDF は現在の主要責務外です。
- Token count は provider tokenizer ではなく deterministic approximate counter です。
- yfinance と SEC Company Facts は外部 provider の schema / availability / rate limit に依存します。
- fake provider は CI/smoke 用の deterministic fixture であり、実 provider の出力品質を保証するものではありません。

### 推論

この system の成果物は「決算分析のための検証可能な報告 artifact」です。投資判断を代替するものではなく、canonical data、source refs、evidence matrix、quality gate、missing-data caveat を通じて、人間がレビューできる材料を作ることに範囲を限定しています。
