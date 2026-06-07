# Earnings Review System Guide

この文書は Earnings Debate Agent のシステム説明、実行方法、設定項目、検証方法をまとめた外部向けガイドです。README では開発動機と設計思想を説明し、この文書では実装上の処理責務と使い方を説明します。

## 1. Overview

Earnings Debate Agent は、四半期決算を対象にした固定ワークフロー型のマルチエージェントシステムです。LLM に自由な調査手順を任せるのではなく、Python 側で入力正規化、context routing、専門エージェント、Bull/Bear debate、Judge、Markdown rendering、quality gates を明示的に制御します。

主な出力は次の2つです。

- `workflow_result.json`: API response と同等の構造化結果
- `report.md`: 人間が読むための決算レビュー Markdown

このシステムの目的は、投資判断を代替することではありません。EPS、FCF、guidance、management comment、Bull/Bear の論点を source-backed に整理し、人間がレビューできる決算分析 artifact を作ることに範囲を限定しています。

## 2. What It Does And Does Not Do

### Does

- 決算レビュー用の入力を `NormalizedReviewRequest` に正規化する
- 財務指標、文書 section、source manifest を紐づける
- 役割別に context を分けて専門エージェントへ渡す
- Bull case と Bear case を作り、Judge が `good` / `neutral` / `bad` を判定する
- source ref、evidence、claim、decision use を検証する
- Markdown report を deterministic renderer で生成する
- fake LLM provider により、API key なしで主要な CLI/CI smoke を実行できる

### Does Not Do

- 投資助言
- 売買推奨
- 目標株価や株価予測
- 自動売買
- portfolio optimization
- DCF などの valuation model
- source-backed でない news、web、analyst 情報を主 verdict に混ぜること
- LLM に raw 財務表から未検証の計算を任せること

## 3. Repository Surfaces

主要な公開対象ファイルは次の通りです。

| Path | Role |
|---|---|
| `src/main.py` | CLI entrypoint。`serve` と `run` を提供する |
| `src/api.py` | FastAPI app。`POST /reviews` を提供する |
| `src/preprocessor.py` | raw/local input を normalized request に変換する |
| `src/workflow.py` | 固定順序の決算レビュー workflow |
| `src/context_router.py` | role 別 context routing と budget check |
| `src/workflow_agents.py` | 7つの LLM agent wrapper と出力 schema validation |
| `src/workflow_runtime.py` | specialist/debate/judge agent の実行制御 |
| `src/workflow_validation.py` | evidence pool、source、polarity、safety の validation |
| `src/report_renderer.py` | Markdown report の deterministic rendering |
| `src/workflow_models.py` | API、workflow、report の Pydantic contract |
| `src/prompts/` | role 別 prompt と shared policy |
| `samples/` | 現行仕様の normalized request samples |
| `outputs/` | 現行仕様の sample report artifacts |
| `.env.example` | 環境変数テンプレート |
| `Makefile` | local check と test entrypoint |

## 4. Quick Start

### 4.1 Install

```bash
uv sync --frozen --group dev
```

### 4.2 Run Without A Real LLM

fake provider を使うと、API key なしで workflow の入口、schema、routing、renderer を確認できます。

```bash
PYTHON_DOTENV_DISABLED=1 \
LLM_PROVIDER=fake \
LOG_LEVEL=WARNING \
uv run earnings-debate run \
  --api-url local \
  --input-json samples/request.nvda-2027q1.example.json \
  --out /tmp/earnings-nvda-demo
```

ZS の sample も同じ形で実行できます。

```bash
PYTHON_DOTENV_DISABLED=1 \
LLM_PROVIDER=fake \
LOG_LEVEL=WARNING \
uv run earnings-debate run \
  --api-url local \
  --input-json samples/request.zs-2026q3.example.json \
  --out /tmp/earnings-zs-demo
```

生成される artifact は次の2つです。

```text
/tmp/earnings-nvda-demo/workflow_result.json
/tmp/earnings-nvda-demo/report.md
```

### 4.3 Run With A Real LLM

実 LLM を使う場合は、provider と API key を環境変数で設定します。

```bash
cp .env.example .env
```

Anthropic を使う例:

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-sonnet-4-5
```

OpenAI を使う例:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

実 LLM 実行では token 使用量、API費用、provider の rate limit が発生します。CI や smoke 確認では `LLM_PROVIDER=fake` を使うのが基本です。

### 4.4 Start The API Server

```bash
uv run earnings-debate serve --host 127.0.0.1 --port 8000
```

CLI から API server へ投げる場合:

```bash
uv run earnings-debate run \
  --api-url http://127.0.0.1:8000 \
  --input-json samples/request.nvda-2027q1.example.json \
  --out outputs/local-run
```

### 4.5 CLI Help

```bash
uv run earnings-debate --help
uv run earnings-debate run --help
uv run earnings-debate serve --help
```

`earnings-debate run` の主な入力 option は次の通りです。

| Option | Description |
|---|---|
| `--input-json PATH` | sample または normalized/local payload を読み込む |
| `--api-url TEXT` | API URL。`local` を指定すると network POST ではなく local workflow を実行する |
| `--ticker TEXT` | `--input-json` なしで使う ticker |
| `--fiscal-period`, `--quarter` | `2026Q3` のような fiscal period |
| `--filing-url TEXT` | SEC filing URL から正規化する |
| `--local-path FILE` | local PDF/text/Markdown を document section 化する。複数回指定できる |
| `--raw-text TEXT` | raw text を document section 化する |
| `--out PATH` | `workflow_result.json` と `report.md` の出力先 |

### 4.6 Choose An Input Mode

入力は大きく分けて、正規化済み JSON、local file、raw text、SEC filing URL の4系統です。

| Input mode | Recommended use | External acquisition |
|---|---|---|
| normalized sample JSON | CI、contract smoke、local smoke | なし |
| local PDF/text/Markdown | 手元の決算資料、transcript、memo を使う | `financial_metrics` がない場合は財務指標取得が走る |
| raw text | 短い抜粋や手入力メモを使う | `financial_metrics` がない場合は財務指標取得が走る |
| SEC filing URL | EDGAR filing HTML を取得して section 化する | SEC filing 取得。cache miss 時は network access |
| API normalized payload | server process へ正規化済み request を送る | payload が正規化済みならなし |

外部取得なしで CLI と workflow contract を確認する場合は、`samples/request.nvda-2027q1.example.json` または `samples/request.zs-2026q3.example.json` を使います。local file や raw text を ticker/fiscal period だけで実行する簡易形では、LLM provider を `fake` にしても、足りない `financial_metrics` を補うために yfinance や SEC Company Facts への取得が発生し得ます。

### 4.7 Run With A Local PDF Or Text File

PDF や text file は repository 内に置く必要はありません。`--local-path` には、CLI を実行する directory から見える既存ファイルの相対パス、または絶対パスを渡します。公開 repository に個人用PDFや大きい入力ファイルを含めない場合は、repo外の directory を使ってください。

例として、repo外に local only の入力置き場を作る場合:

```bash
mkdir -p /tmp/earnings-inputs
cp /path/to/company-earnings-presentation.pdf /tmp/earnings-inputs/presentation.pdf
```

PDF を使って local workflow を実行する例:

```bash
PYTHON_DOTENV_DISABLED=1 \
LLM_PROVIDER=fake \
LOG_LEVEL=WARNING \
uv run earnings-debate run \
  --api-url local \
  --ticker NVDA \
  --fiscal-period 2027Q1 \
  --local-path /tmp/earnings-inputs/presentation.pdf \
  --out /tmp/earnings-nvda-local-pdf
```

複数ファイルを使う場合は `--local-path` を複数回指定します。

```bash
uv run earnings-debate run \
  --api-url local \
  --ticker NVDA \
  --fiscal-period 2027Q1 \
  --local-path /tmp/earnings-inputs/presentation.pdf \
  --local-path /tmp/earnings-inputs/transcript.txt \
  --out /tmp/earnings-nvda-local-files
```

対応する拡張子は `.pdf`、`.txt`、`.text`、`.md` です。text file は UTF-8 を前提にします。PDF は `pypdf` で抽出できる text layer が必要です。scan PDF の OCR は行いません。

短い文章だけを渡す場合は `--raw-text` を使います。

```bash
uv run earnings-debate run \
  --api-url local \
  --ticker NVDA \
  --fiscal-period 2027Q1 \
  --raw-text "Management guided to sequential revenue growth and higher capex." \
  --out /tmp/earnings-nvda-raw-text
```

SEC filing URL を使う場合は、SEC EDGAR request 用の user-agent を設定します。

```bash
SEC_USER_AGENT="Your Name your.email@example.com" \
uv run earnings-debate run \
  --api-url local \
  --ticker NVDA \
  --fiscal-period 2027Q1 \
  --filing-url "https://www.sec.gov/Archives/edgar/data/1045810/..." \
  --out /tmp/earnings-nvda-sec
```

API server の `POST /reviews` は raw acquisition fields を受け取りません。PDF、`local_path`、`raw_text`、`filing_url` を使う場合は CLI/preprocessor で正規化してから、正規化済み `NormalizedReviewRequest` を API に渡します。

## 5. Canonical Samples And Outputs

現行仕様の sample request は2本です。どちらも外部取得なしで `NormalizedReviewRequest` として使えます。

| Sample | Output artifact | Target |
|---|---|---|
| `samples/request.nvda-2027q1.example.json` | `outputs/sample-nvda-20260607/` | NVDA 2027Q1 |
| `samples/request.zs-2026q3.example.json` | `outputs/sample-zs-20260607/` | ZS 2026Q3 |

これらの sample は `schema_version`、`financial_metrics`、`document_sections`、`source_manifest`、`context_budget` を含む normalized request です。そのため、SEC や yfinance への外部取得を行わずに workflow contract を確認できます。

## 6. System Architecture

固定 workflow は次の順序で実行されます。

```text
CLI / API
  -> input normalization
  -> data ingestion
  -> context routing
  -> financial specialist agents
  -> presentation specialist agents
  -> evidence aggregation
  -> Bull / Bear debate
  -> Judge
  -> deterministic Markdown rendering
```

中核は `src/workflow.py` の `ReviewWorkflow.run()` です。各 step は `StepStatus` として記録され、失敗時は該当 step の error string が残ります。API response の error category は `src/api.py` の error envelope 側で付与されます。

quality gate は独立した workflow step ではありません。input validation、source manifest validation、context budget check、evidence aggregation、debate/judge selection、report matrix validation の各段階に分散しています。

## 7. Input Contract

API の実行境界は `POST /reviews` です。API は `NormalizedReviewRequest` を受け取ります。

主要 field:

| Field | Role |
|---|---|
| `schema_version` | normalized request の schema version |
| `request_id` | trace 用 ID |
| `ticker` | 対象 ticker |
| `fiscal_period` | 対象四半期 |
| `financial_metrics` | 正規化済み財務指標 |
| `document_sections` | source ref 付き文書 section |
| `source_manifest` | request 内で参照できる source の登録表 |
| `context_budget` | role context の token budget |
| `include_markdown` | Markdown report を含めるか |
| `purpose` | `earnings_review_not_investment_advice` 固定 |
| `is_investment_advice` | `false` 固定 |
| `dry_run` | provider/workflow を呼ばず contract を検査する |

API は raw acquisition fields を受け付けません。`filing_url`、`document_files`、`raw_text`、`local_path` などは CLI/preprocessor 側の入力です。API に直接渡す payload は、取得と正規化が完了している必要があります。

## 8. Data Processing

`src/preprocessor.py` は CLI/local payload を normalized request に変換します。

対応する入力形態:

- normalized JSON
- `document_sections`
- `document_files`
- `local_path`
- `raw_text`
- `filing_url`
- ticker / fiscal period

文書入力は `DocumentSection` に変換され、各 section に `SourceRef` が付きます。local file は text layer を前提に section 化されます。相対パスは CLI 実行時の current working directory 基準です。SEC filing は `use_sec=true` の場合に HTML を取得し、topic section に分割します。local file や raw text と `filing_url` を同時に渡した場合も、`filing_url` は追加の document source として取得対象になります。

財務指標は `FinancialMetrics` に正規化されます。対象は EPS、revenue、operating cash flow、capex、free cash flow、guidance などです。入力 payload に `financial_metrics` がない場合、preprocessor は ticker と fiscal period から財務指標取得を試みます。free cash flow のような派生値は Python 側で計算・登録し、LLM が raw 表から自由に計算する設計にはしていません。

## 9. Context Routing

`src/context_router.py` の `ContextRouter` は、全データをすべての specialist agent に渡さず、役割ごとに必要な context へ絞ります。実行時に `source_manifest` と `context_budget` がある場合、主に4つの specialist role に対して routed context と source index を作ります。

| Role | Routed Context |
|---|---|
| `EarningsQualityAnalyst` | EPS、revenue、margin、一時要因、earnings quality sections |
| `CashFlowRiskAnalyst` | operating cash flow、FCF、capex、working capital、liquidity、debt |
| `ManagementIntentAnalyst` | management、strategy、MD&A、risk、capital allocation sections |
| `GuidanceAnalyst` | guidance metrics、consensus deltas、guidance/outlook sections |
Bull/Bear/Judge の context は `src/workflow_runtime.py` 側で `AnalysisBrief` と候補 evidence pool から組み立てます。Bear は Bull summary を受け取るため、debate stage は完全並列ではありません。

Router は次を検証します。

- routed context が request の `source_manifest` 外の source を参照していないこと
- `source_ref` と `source_manifest` の locator が矛盾しないこと
- role context が `context_budget` に収まること

token count は provider tokenizer ではなく、stable compact JSON の文字数を4で割る deterministic approximation です。これは実行前 gate とテスト再現性を優先した設計です。

## 10. Agent Responsibilities

runtime agent は7つです。

| Agent | Responsibility |
|---|---|
| `EarningsQualityAnalyst` | EPS surprise、P&L quality、revenue quality、margin trend、一時要因と継続要因を分析する |
| `CashFlowRiskAnalyst` | operating cash flow、FCF、capex、working capital、liquidity、financing risk を分析する |
| `ManagementIntentAnalyst` | 経営陣の意図、投資優先順位、成長投資、株主還元、実行リスクを分析する |
| `GuidanceAnalyst` | guidance、consensusとの差分、前提、達成可能性、revision risk を分析する |
| `BullAgent` | validated evidence から positive case を構成する |
| `BearAgent` | validated evidence から downside/risk case を構成する |
| `JudgeAgent` | Bull/Bear を比較し、最終 verdict と rationale を返す |

各 agent は `AgentSpec` を持ち、role、出力 model、context keys、prompt、token cap、temperature を定義します。LLM の出力は JSON として parse され、Pydantic model で検証されます。role mismatch や schema mismatch は workflow error として扱われます。

## 11. Evidence And Quality Gates

このシステムでは、LLM の出力をそのまま最終判定に使いません。`src/workflow_validation.py` と `src/workflow_models.py` の contract で、source、evidence、claim、decision use を検証します。

主な gate:

| Gate | Purpose |
|---|---|
| Normalized input contract | API input が `NormalizedReviewRequest` として妥当か確認する |
| Raw acquisition rejection | API に raw取得用 field が混ざることを防ぐ |
| Source manifest consistency | evidence や metric が未登録 source を参照しないようにする |
| Context budget | LLM 呼び出し前に context size を確認する |
| Guidance acquisition | guidance/outlook source または no-guidance disclosure があるか確認する |
| Numeric grounding | material claim に数値根拠または missing-data caveat があるか確認する |
| Evidence pool validation | Bull/Bear/Judge が validated candidate pool 外の evidence を使わないようにする |
| Missing-data confidence cap | 必要データ不足時に Judge confidence を制限する |
| Investment-advice language guard | 投資助言表現を warning/redaction 対象にする |
| ReportMatrix validation | source、evidence、claim、decision use の参照整合性を確認する |

`EARNINGS_DEBATE_REQUIRE_GUIDANCE` は workflow の guidance acquisition gate に使われます。guidance/outlook source がない場合は、明示的な no-guidance disclosure を入力側で表現する必要があります。`EARNINGS_DEBATE_REQUIRE_NUMERIC_GROUNDING` は numeric grounding validator の切り分け用設定です。workflow 本線では ungrounded evidence を warning/filtering の対象として扱い、ReportMatrix の参照整合性で最終出力を検証します。

report の `Quality Gates: passed` は、ReportMatrix の参照整合性など workflow 内部の検証が通ったことを示します。投資リスクがないことや、外部データが完全であることを保証するものではありません。

## 12. Report Output

Markdown report は `src/report_renderer.py` の `ReportRenderer` が生成します。LLM が Markdown を直接書くのではなく、validated structured output から固定順の section を組み立てます。

主な section:

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

report section の追加や削除は output contract の変更として扱います。

## 13. Configuration / Environment Variables

設定は `.env.example` に集約しています。`.env` の実値や secret は repository に含めません。

### Provider And Model

| Env var | Default in `.env.example` | Description |
|---|---:|---|
| `LLM_PROVIDER` | `anthropic` | `fake`、`anthropic`、`openai` を選択する |
| `ANTHROPIC_API_KEY` | empty | Anthropic API key |
| `OPENAI_API_KEY` | empty | OpenAI API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | Anthropic model |
| `OPENAI_MODEL` | `gpt-5.4-mini` | OpenAI model |

`LLM_PROVIDER=fake` は CI/smoke 用です。実 provider の品質や費用を検証するものではありません。

### CLI / API Defaults

| Env var | Default | Description |
|---|---:|---|
| `EARNINGS_DEBATE_API_HOST` | `127.0.0.1` | `serve` の host default |
| `EARNINGS_DEBATE_API_PORT` | `8000` | `serve` の port default |
| `EARNINGS_DEBATE_API_URL` | `http://127.0.0.1:8000` | `run` の API URL default |
| `EARNINGS_DEBATE_OUTPUT_DIR` | `outputs` | CLI output directory default |
| `EARNINGS_DEBATE_API_REQUEST_TIMEOUT_SECONDS` | `300` | API POST timeout |
| `LOG_LEVEL` | `INFO` | CLI logging level |

CLI の明示 option は environment default より優先されます。

### LLM Runtime

| Env var | Default | Description |
|---|---:|---|
| `EARNINGS_DEBATE_LLM_DEFAULT_MAX_TOKENS` | `2048` | provider direct call の default max tokens |
| `EARNINGS_DEBATE_LLM_DEFAULT_TEMPERATURE` | `0.7` | provider direct call の default temperature |
| `EARNINGS_DEBATE_OPENAI_MIN_COMPLETION_TOKENS` | `4096` | OpenAI completion token floor |
| `EARNINGS_DEBATE_AGENT_MAX_TOKENS` | `8192` | specialist agent max tokens |
| `EARNINGS_DEBATE_DEBATE_MAX_TOKENS` | `8192` | Bull/Bear max tokens |
| `EARNINGS_DEBATE_JUDGE_MAX_TOKENS` | `12000` | Judge max tokens |
| `EARNINGS_DEBATE_AGENT_TEMPERATURE` | `0.2` | specialist/debate temperature |
| `EARNINGS_DEBATE_JUDGE_TEMPERATURE` | `0.1` | Judge temperature |
| `EARNINGS_DEBATE_AGENT_MAX_RETRIES` | `1` | agent schema repair retry |
| `EARNINGS_DEBATE_AGENT_MAX_WORKERS` | empty | specialist parallel worker cap。empty は runtime default |
| `EARNINGS_DEBATE_DEBATE_SELECTION_ATTEMPTS` | `2` | debate evidence selection attempts |
| `EARNINGS_DEBATE_JUDGE_SELECTION_ATTEMPTS` | `2` | judge evidence selection attempts |

### Acquisition / Cache

| Env var | Default | Description |
|---|---:|---|
| `SEC_USER_AGENT` | placeholder | SEC EDGAR request user-agent |
| `EARNINGS_DEBATE_SEC_REQUEST_TIMEOUT_SECONDS` | `30` | SEC request timeout |
| `EARNINGS_DEBATE_SEC_FILING_CACHE_DIR` | `samples/cache` | SEC filing cache directory |
| `EARNINGS_DEBATE_SEC_CACHE_KEY_LENGTH` | `12` | cache key length |
| `EARNINGS_DEBATE_MAX_DOCUMENT_SECTION_CHARS` | `8000` | document section chunk size |

SEC EDGAR へアクセスする場合は、識別可能な `SEC_USER_AGENT` を設定してください。

### Quality Gates

| Env var | Default | Description |
|---|---:|---|
| `EARNINGS_DEBATE_REQUIRE_GUIDANCE` | `1` | guidance acquisition gate |
| `EARNINGS_DEBATE_REQUIRE_NUMERIC_GROUNDING` | `1` | numeric grounding validator |

通常はどちらも有効のまま使います。無効化は legacy fixture や一時的な切り分け用途に限定します。

## 14. API Usage

API server を起動します。API mode で実 LLM を使う場合、provider と API key は server process 側の環境変数で決まります。

```bash
uv run earnings-debate serve --host 127.0.0.1 --port 8000
```

別 terminal から normalized sample を送ります。

```bash
curl -sS http://127.0.0.1:8000/reviews \
  -H 'content-type: application/json' \
  --data @samples/request.nvda-2027q1.example.json \
  > /tmp/earnings-review-response.json
```

`dry_run=true` の payload では、provider/workflow を解決せずに input contract、source manifest、runtime required input、context budget を検査します。実行前に payload の構造だけ確認したい場合に使えます。

```bash
jq '.dry_run = true' samples/request.nvda-2027q1.example.json \
  | curl -sS http://127.0.0.1:8000/reviews \
      -H 'content-type: application/json' \
      --data-binary @-
```

## 15. Error Handling And Troubleshooting

API は既知の失敗を JSON envelope で返します。通常の失敗は `status="failed"` と `errors`、dry-run の失敗は `status="dry_run"`、`dry_run_status="failed"`、`checks`、`errors` を含みます。error detail には `category`、`message`、任意の `field`、`retryable` が入ります。

CLI の表示は API envelope と同一ではありません。`--api-url local` は API preflight/envelope を通らず local workflow を直接実行します。remote API に投げた場合、HTTP 422/500 は `requests` の HTTP error として扱われ、成功時だけ `workflow_result.json` と `report.md` が出力されます。

| Failure | API behavior | CLI behavior | Typical fix |
|---|---|---|---|
| Request body is not a JSON object | 422 `input_contract` | remote API では HTTP error | JSON object を送る |
| Normalized request validation error | 422 `input_contract`、`source_manifest`、または `context_budget` | `--input-json` の正規化中は usage error。remote API では HTTP error | field 名、型、必須 field を修正する |
| Raw acquisition fields sent to API | 422 `input_contract` | CLI は成功時に raw field を正規化してから送る | `filing_url`、`document_files`、`local_path`、`raw_text` は CLI/preprocessor 側で使う |
| No executable document sections | 422 `input_contract`。dry-run では failed check | local mode では workflow 側の例外、remote API では HTTP error | `document_sections`、local file、raw text、または filing URL を指定する |
| Local document file cannot be read | API では raw `document_files` は基本的に拒否 | usage error | パス、拡張子、UTF-8、PDF text layer、空ファイルでないことを確認する |
| Source manifest mismatch | 422 `source_manifest` | local mode では workflow 側の例外、remote API では HTTP error | `source_id`、locator、metric/source metadata を揃える |
| Context budget exceeded | 422 `context_budget`。dry-run では failed check | local mode では workflow 側の例外、remote API では HTTP error | document section を短くする、不要 section を削る、budget を見直す |
| Guidance source is missing | workflow quality failure。API category は発生箇所により `quality_gate` または generic 500 | local mode では workflow 側の例外、remote API では HTTP error | guidance/outlook section か no-guidance disclosure を入力に含める |
| LLM output schema or role mismatch | 500 `llm_output_schema` または `agent_role`、`retryable` は category に従う | local mode では workflow 側の例外、remote API では HTTP error | provider response、prompt、agent output schema を確認する |
| Provider configuration, authentication, or transient failure | 外部へは generic 500 として返る場合がある | local mode では provider exception、remote API では HTTP error | API key、model、rate limit、network、provider status を確認する |
| Unexpected internal failure | 500 `internal_invariant` | local mode では未処理例外、remote API では HTTP error | server log と再現 payload を確認する |

local file 関連でよくある原因:

- `--local-path` の相対パスが CLI 実行 directory から見えていない
- 対応外の拡張子を渡している
- text file が UTF-8 ではない
- PDF が scan 画像のみで、extractable text がない
- 入力 document が空、または chunk 化後に section が残らない

API error body を直接確認したい場合は、CLI 経由ではなく `curl` で `/reviews` に送って response JSON を保存してください。

```bash
curl -sS http://127.0.0.1:8000/reviews \
  -H 'content-type: application/json' \
  --data @samples/request.nvda-2027q1.example.json \
  > /tmp/earnings-review-response.json
```

## 16. Tests And CI

主な Makefile target:

| Command | Description |
|---|---|
| `make sync` | locked dev dependencies を install |
| `make format-check` | Ruff formatting check |
| `make lint` | Ruff lint |
| `make typecheck` | mypy |
| `make test` | pytest |
| `make test-fast` | API smoke、CLI smoke、workflow e2e |
| `make check` | format、lint、typecheck、pytest |

CI は `.github/workflows/ci.yml` で `make check` を実行します。テストは実 API key に依存しないよう、fake provider と monkeypatch を使います。

基本確認:

```bash
make check
```

CLI smoke を手元で見る場合:

```bash
PYTHON_DOTENV_DISABLED=1 \
LLM_PROVIDER=fake \
LOG_LEVEL=WARNING \
uv run earnings-debate run \
  --api-url local \
  --input-json samples/request.nvda-2027q1.example.json \
  --out /tmp/earnings-cli-smoke
```

## 17. Limitations

- SEC filing segmentation は HTML text と heading pattern に依存します。
- PDF は text layer 抽出が前提です。scan PDF の OCR は主要責務外です。
- yfinance と SEC Company Facts は外部 provider の schema、availability、rate limit に依存します。
- fake provider は workflow 再現性確認用であり、実 LLM の分析品質を保証しません。
- approximate token count は provider tokenizer と完全一致しません。
- verdict は source-backed な決算レビュー上の分類であり、投資判断や売買判断ではありません。
