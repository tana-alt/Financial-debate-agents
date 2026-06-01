# Financial Debate Agents

米国株の四半期決算レビューで行う「財務数値の確認」「決算資料の読解」「Bull / Bear 両面の論点整理」「最終レポート化」を、LLM multi-agent workflow として自動化するシステムです。入力契約、context routing、evidence validation、deterministic report rendering を分離し、投資助言ではない決算レビューを再現可能な手順で生成します。

リポジトリ: https://github.com/tana-alt/Financial-debate-agents

> This project generates an earnings-analysis report. It does not provide stock-price forecasts, target prices, trading recommendations, or investment advice.

---

## 1. 概要

決算直後のレビューでは、EPS surprise や revenue growth だけでなく、FCF、CapEx、guidance、経営陣コメント、反対根拠まで短時間で整理する必要があります。

このリポジトリでは、その作業を次のような固定 workflow に分解します。

```text
NormalizedReviewRequest
  ├─ financial_metrics
  ├─ document_sections
  ├─ source_manifest
  ├─ context_budget
  └─ include_markdown / dry_run

        ↓

API / CLI ingestion
  - CLI が sample JSON, local file, raw text, filing URL を正規化
  - API が NormalizedReviewRequest を検証
  - source_manifest と context_budget を実行前に確認

        ↓

ContextRouter
  - role ごとに必要な source-scoped context だけを配布
  - context_budget 超過を LLM 実行前に検出

        ↓

Financial agents
  - EarningsQualityAnalyst
  - CashFlowRiskAnalyst

        ↓

Presentation agents
  - ManagementIntentAnalyst
  - GuidanceAnalyst

        ↓

Evidence aggregation
  - positive / negative / risk evidence
  - source traceability check
  - missing data and confidence controls

        ↓

Debate
  - BullAgent
  - BearAgent

        ↓

Judge
  - good / neutral / bad
  - confidence
  - EPS outlook
  - FCF outlook

        ↓

ReportRenderer
  - final earnings review report
```

---

## 2. なぜこのタスクを自動化したのか

自分が企業決算を読むとき、手作業では次の問題が起きやすいです。

- EPS surprise や revenue growth のような目立つ数値だけで判断してしまう
- FCF や CapEx のような将来キャッシュフローに関わる論点を後回しにしやすい
- 決算説明資料、10-Q、経営陣コメント、guidance を読む順番が毎回ぶれる
- 良い材料だけ、または悪い材料だけを拾ってしまい、反対根拠の確認が弱くなる
- 最後に Markdown レポートへ整理するまでに時間がかかる

そのため、数値計算は Python 側で決定的に処理し、LLM には「解釈」「反証」「要約」「論点整理」を担当させる構成にしました。

このシステムの目的は、投資判断を自動化することではありません。目的は、決算情報を構造化し、毎回同じ観点で、根拠と反対根拠を含むレビュー資料を短時間で作ることです。

---

## 3. 自動化する業務

| 手作業の業務 | 自動化後 |
| --- | --- |
| レビュー入力を整える | CLI ingestion が raw input を `NormalizedReviewRequest` に変換 |
| 出典を追跡する | `source_manifest` を authoritative source registry として検証 |
| agent に渡す文脈を選ぶ | `ContextRouter` が role 別 context と `context_budget` を制御 |
| EPS、収益性、cash flow risk を読む | Financial agents が観点別に structured finding を作成 |
| 経営陣コメントと guidance を読む | Presentation agents が文脈と前提を分析 |
| Bull / Bear 両面を整理する | Debate が positive / negative evidence から主張を作成 |
| 最終判断を書く | Judge が good / neutral / bad と理由を出力 |
| レポートを整形する | `ReportRenderer` が検証済み matrix から Markdown を決定的に生成 |

---

## 4. 設計思想

課題指定の参考文献を、次のように実装へ反映しています。

| 参考文献 | 設計への反映 |
| --- | --- |
| [Building Effective Agents](https://lstep.app/F1mQlQB) | 完全自律 agent ではなく、明示的な固定 workflow と specialist agents を組み合わせる |
| [Effective Context Engineering for AI Agents](https://lstep.app/R3cZy8u) | 全文を agent に渡さず、agent ごとに必要な context keys だけを渡す |
| [The Twelve-Factor App](https://lstep.app/SwKfiMq) | API key、model、log level、SEC user-agent を環境変数で管理する |
| [Shape Up](https://lstep.app/e6YVtQS) | MVP の範囲を「決算レビューの構造化とレポート生成」に限定し、株価予測や自動売買は No-Go とする |

### 4.1 Workflow-first

LLM が自由に手順を決める完全自律型ではなく、以下の順序をコードで固定しています。

```text
Data ingestion
→ Financial agents
→ Presentation agents
→ Evidence aggregation
→ Debate
→ Judge
→ Markdown rendering
```

これにより、失敗箇所の特定、テスト、再現性の確保がしやすくなります。

### 4.2 Context Engineering

Agent には必要な context だけを渡します。

例:

- `EPSQualityAnalyst` には EPS metrics と EPS sections を渡す
- `CashFlowFcfAnalyst` には cash flow / capex / risk sections を渡す
- `JudgeAgent` には validated AnalysisBrief、BullCase、BearCase だけを渡す

生の filing 全文や無関係な metrics は、原則として各 agent に渡しません。

### 4.3 Structured Output

LLM の出力は自由文として信用せず、Pydantic model で検証します。

- 未定義 field を拒否
- confidence の範囲を検証
- `good / neutral / bad` の label を enum で制限
- positive evidence / negative evidence を必須化
- source reference を必須化
- investment advice ではないことを contract に含める

### 4.4 Scope Control

この提出でやらないことを明確にしています。

- 株価予測
- 目標株価の算出
- 売買推奨
- 自動売買
- ポートフォリオ最適化
- LLM による財務指標の直接計算

---

## 5. 実装済み機能

- API: `POST /reviews` が `NormalizedReviewRequest` を受け取り、success / dry-run / error envelope を返す
- CLI ingestion: `earnings-debate run` が sample JSON、`document_files`、`local_path`、`raw_text`、`filing_url` を正規化して API または local runner に渡す
- Context routing: `ContextRouter` が role ごとの context、`source_index`、`context_budget` を検証する
- Financial agents: `EarningsQualityAnalyst` と `CashFlowRiskAnalyst` が財務面の finding を作る
- Presentation agents: `ManagementIntentAnalyst` と `GuidanceAnalyst` が経営陣コメントと guidance を分析する
- Structured outputs: Pydantic model が finding、brief、Bull / Bear case、Judge decision、`ReportMatrix` を検証する
- Evidence validation: `source_manifest` と `source_ref` の整合性、positive / negative evidence、missing data、numeric grounding を検証する
- Report renderer: `ReportRenderer` が Evidence Matrix、Agent Contribution、Quality Gates、Source Appendix、Disclaimer を含む Markdown report を決定的に生成する
- Safety: `purpose` / `is_investment_advice` contract と no-advice validation で、株価予測・目標株価・売買推奨を出力対象外にする

---

## 6. セットアップ

### 6.1 Install

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 6.2 Environment variables

```bash
cp .env.example .env
```

`.env` に少なくとも一つの LLM API key を設定します。

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...

# or
LLM_PROVIDER=openai
OPENAI_API_KEY=...
```

SEC filing を取得する場合は、SEC user-agent も設定します。

```bash
SEC_USER_AGENT="Your Name your.email@example.com"
```

---

## 7. テスト

API key なしで contract / workflow tests を実行できます。

```bash
pytest
```

テストでは fake LLM を使い、外部 API fetch に依存せず、以下を検証します。

- Pydantic contract が不正値を拒否すること
- LLM 出力が JSON として parse / validate されること
- agent ごとの context routing が守られること
- workflow が決まった順序で実行されること
- `/reviews` endpoint が dry-run / validation / execution response を分けること
- `ReportRenderer` が Evidence Matrix と quality gates を含む report を生成すること

---

## 8. 実行方法

### 8.1 API server

```bash
earnings-debate serve --host 127.0.0.1 --port 8000
```

### 8.2 CLI からレビューを実行

別ターミナルで実行します。CLI は `samples/request.example.json` を `NormalizedReviewRequest` に正規化してから API に送ります。

```bash
earnings-debate run \
  --api-url http://127.0.0.1:8000 \
  --input-json samples/request.example.json \
  --out outputs
```

API server を起動せずに fake LLM で local runner を使う場合は、次のように実行できます。

```bash
LLM_PROVIDER=fake earnings-debate run \
  --api-url local \
  --input-json samples/request.example.json \
  --out outputs/example
```

成功すると、以下のファイルが生成されます。

```text
outputs/
  ├─ workflow_result.json
  └─ report.md
```

ローカルの PDF / text file を読み込む場合は、`document_files` を含む request JSON を指定します。

```bash
LLM_PROVIDER=fake earnings-debate run \
  --api-url local \
  --input-json samples/request.document-files.example.json \
  --out outputs/document-files-example
```

### 8.3 API request

`POST /reviews` は正規化済みの `NormalizedReviewRequest` を受け取ります。raw input の正規化は CLI が担当します。

```bash
curl -X POST http://127.0.0.1:8000/reviews \
  -H "Content-Type: application/json" \
  -d @normalized-request.json
```

---

## 9. 入力例

`samples/request.example.json` は、外部 financial API や SEC fetch に依存せずに動作確認するための sample input です。CLI 実行時に `source_manifest` と `context_budget` を含む `NormalizedReviewRequest` へ変換されます。

API に直接渡す正規化済み入力の主要フィールドは次の通りです。

```json
{
  "schema_version": "normalized-review-request.v1",
  "request_id": "sample-nvda-2025q3",
  "ticker": "NVDA",
  "fiscal_period": "2025Q3",
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
    "free_cash_flow": 12000000000,
    "capex": 3000000000,
    "guidance": "Management guided to continued revenue growth.",
    "source_refs": [
      {
        "source_id": "financial_api:NVDA:2025Q3",
        "source_type": "financial_api",
        "metric_name": "consensus_snapshot",
        "title": "Fixture financial metrics"
      }
    ]
  },
  "document_sections": [
    {
      "section_id": "eps",
      "source_ref": {
        "source_id": "filing:eps",
        "source_type": "filing",
        "document_id": "10q-2025q3",
        "section_id": "eps",
        "title": "EPS section"
      },
      "heading": "EPS",
      "text": "Diluted EPS exceeded consensus..."
    },
    {
      "section_id": "guidance",
      "source_ref": {
        "source_id": "filing:guidance",
        "source_type": "filing",
        "document_id": "10q-2025q3",
        "section_id": "guidance",
        "title": "Guidance section"
      },
      "heading": "Guidance",
      "text": "Management guidance assumes continued demand."
    }
  ],
  "source_manifest": [
    {
      "source_id": "financial_api:NVDA:2025Q3",
      "source_type": "financial_api",
      "metric_name": "consensus_snapshot",
      "title": "Fixture financial metrics"
    },
    {
      "source_id": "filing:eps",
      "source_type": "filing",
      "document_id": "10q-2025q3",
      "section_id": "eps",
      "title": "EPS section"
    },
    {
      "source_id": "filing:guidance",
      "source_type": "filing",
      "document_id": "10q-2025q3",
      "section_id": "guidance",
      "title": "Guidance section"
    }
  ],
  "context_budget": {
    "max_input_tokens": 6000,
    "max_output_tokens": 2000,
    "max_total_tokens": 10000
  },
  "include_markdown": true,
  "purpose": "earnings_review_not_investment_advice",
  "is_investment_advice": false,
  "dry_run": false
}
```

### 9.1 ローカル資料ファイルの指定

`document_sections` を直接指定する代わりに、`document_files` でローカルの PDF / text file を指定できます。指定されたファイルは data ingestion layer で `DocumentSection` に展開され、既存の multi-agent workflow に渡されます。`document_sections` と `document_files` は併用できます。

```json
{
  "ticker": "NVDA",
  "fiscal_period": "2025Q3",
  "document_files": [
    {
      "path": "data/presentations/nvda-q3-2025.pdf",
      "source_type": "earnings_presentation",
      "document_id": "nvda-q3-2025-presentation",
      "title": "NVDA Q3 2025 earnings presentation"
    }
  ]
}
```

- 対応拡張子は `.pdf`, `.txt`, `.text`, `.md` です。
- PDF はページ単位で text extraction し、長いページは chunk に分割します。
- text file は UTF-8 として読み込み、長い本文は chunk に分割します。
- `source_ref` は `source_id`, `source_type`, `document_id`, `section_id`, `page`, `title` を workflow 内で安定生成します。
- PDF を repository に含めない場合は、ローカルの path を request JSON に書き、PDF 本体は手元に配置してください。
- 不正 path、存在しない file、未対応拡張子、抽出 text が空の PDF / text file は validation error として扱います。

---

## 10. 出力例

出力は Markdown report です。`ReportRenderer` は、検証済みの `ReportMatrix` から次の固定順で section を出力します。これは投資助言ではなく、決算レビュー用の構造化 report です。

```markdown
# Earnings Review: NVDA 2025Q3

## Judge Rationale

- Verdict: neutral
- Confidence: 0.66
- Summary: The quarter is constructive, with cash-flow caveats.
- Rationale: The Judge treats checked EPS evidence as supportive, but limits durability because FCF evidence is incomplete.
- EPS outlook: EPS outlook is constructive if margin support persists.
- EPS rationale: The EPS beat is supported by a checked financial source.
- FCF outlook: FCF outlook remains uncertain until the CapEx bridge is clearer.
- FCF rationale: CapEx pressure and missing bridge data limit confidence.

## Bull vs Bear Tension

### Bull Case

EPS quality improved on a verified beat.

### Bear Case

CapEx pressure can delay FCF conversion.

### Risk Case

Missing guidance limits forward confidence.

### Judge Tension

Bull evidence is stronger for the current quarter, while bear evidence limits durability.

## Evidence Matrix

| Claim ID | Fact | Interpretation | Implication | Time scope | Fact-check status | Judge treatment | Sources |
|---|---|---|---|---|---|---|---|
| claim:eps-quality | Adjusted EPS of $1.23 exceeded consensus by 8%. | The fact supports current-quarter EPS quality. | The report should avoid converting the fact into a durable forecast. | Current quarter 2025Q3 | supported | supporting | api:eps:2025Q3 / eps |

## Agent Contribution

| Agent | Stance | Contribution | Key evidence | Counter evidence | Confidence | Missing data |
|---|---|---|---|---|---:|---|
| EarningsQualityAnalyst | mixed | Uses validated evidence only. | ev:eps-beat | ev:capex-pressure | 0.74 | - |

## Uncertainty And Missing Data

| Topic | Materiality | Blocks verdict | Reason |
|---|---|---:|---|
| FCF bridge | medium | false | The source set does not explain conversion from operating cash flow to FCF. |

## Quality Gates

- ReportMatrix validation: passed
- Source manifest entries: 5
- Evidence items: 2
- Claim records: 1
- Decision uses: 2
- Missing data items: 1
- Source references: registered and internally consistent
- No-advice framing: present in Disclaimer

## Source Appendix

| Source ID | Type | Locator | Title | Reported period | URL |
|---|---|---|---|---|---|
| `api:eps:2025Q3` | financial_api | eps | Financial API EPS | 2025Q3 | no URL |

## Disclaimer

This report is an earnings analysis report and is not investment advice.
```

---

## 11. 品質管理

Report quality は追加の手順ではなく、実装済みの quality gates として workflow に組み込まれています。

- `NormalizedReviewRequest` が raw acquisition fields を拒否し、API execution input を固定する
- `ContextRouter` が `source_manifest` の重複、source mismatch、`context_budget` 超過を実行前に検出する
- `WorkflowValidationGate` が agent finding の evidence coverage と no-advice text を検証する
- `validate_guidance_required` が guidance を含む入力を要求し、不足時は実行を止める
- `validate_numeric_grounding` が material claim の数値根拠を確認する
- `apply_confidence_caps` が missing data に応じて Judge confidence を抑制する
- `ReportRenderer` が Quality Gates と Source Appendix を report に明示する

---

## 12. Project structure

```text
.
├─ src/
│  ├─ api.py                # FastAPI entry point
│  ├─ main.py               # CLI wrapper
│  ├─ workflow.py           # Explicit workflow orchestration
│  ├─ context_router.py     # Role-scoped context routing and budget checks
│  ├─ report_renderer.py    # Deterministic report renderer contract
│  ├─ workflow_agents.py    # LLM agent wrappers
│  ├─ workflow_models.py    # Pydantic contracts
│  ├─ preprocessor.py       # Metrics normalization and filing segmentation
│  ├─ workflow_validation.py # Evidence and no-advice validation
│  ├─ report_quality_*.py   # Guidance, numeric grounding, confidence controls
│  ├─ structured.py         # JSON parsing and model validation
│  └─ llm.py                # Provider abstraction
├─ tests/
│  ├─ test_api_contract.py
│  ├─ test_context_router.py
│  ├─ test_workflow_api.py
│  ├─ test_workflow_agents.py
│  ├─ test_workflow_models.py
│  ├─ test_report_renderer.py
│  └─ test_preprocessor.py
├─ samples/
│  ├─ request.example.json
│  └─ request.document-files.example.json
├─ outputs/
│  └─ example/
│     └─ report.md
├─ .env.example
├─ pyproject.toml
└─ README.md
```

---

## 13. Limitations

現在の実装では、評価しやすさと再現性を優先しています。

- `financial_metrics` と `document_sections` または `document_files` を明示的に渡す実行を推奨
- `filing_url` からの HTML fetch / segmentation は実装済みだが、実運用では filing 形式差分への追加対応が必要
- PDF extraction は text layer を持つ PDF が対象。scan image PDF の OCR は対象外
- `presentation_url` と `transcript_url` は入力 contract として保持しているが、自動取得処理は将来拡張
- `yfinance` による consensus fetch は schema 変更の影響を受けるため、MVPでは defensive に欠損を許容
- 投資助言、株価予測、売買推奨は意図的に対象外

---

## 14. Future work

- SEC filing parser の精度向上
- earnings presentation / transcript の自動取得
- source citation の line / page 単位での強化
- sample company を複数追加
- review history の比較機能
- CI 上での coverage report 追加
