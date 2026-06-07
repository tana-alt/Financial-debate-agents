## 提出課題との対応

このリポジトリは、私が四半期ごとに行っている米国株決算レビューを自動化するための multi-agent workflow です。
自動化対象は投資判断そのものではなく、EPS、P&L、FCF、guidance、management comment、Bull/Bear 主張、最終レビュー report の作成です。
参考文献に基づき、完全な自律エージェントではなく、固定 workflow、role-scoped context、structured output、validation gate、deterministic renderer を組み合わせています。

1. タスクを自動化しようと思った動機
- 私は株式投資を行なっており、投資している銘柄や監視銘柄は毎四半期ごとに決算の内容を確認してます。
- これを継続的なタスクとみなし、客観的な視点からの決算分析の自動化は将来的なタイムパフォーマンスを考えると非常に有用だと考えました。
- そのため、EPS、P&L、FCF等の持続性と市場コンセンサスとの乖離という私が普段注目している視点から決算を分析して決算の良し悪しを判定する固定ワークフローのマルチエージェントシステムを開発しました。

2. システム設計上の設計思想
参考文献を前提に以下のような設計思想で実装しました。
- 本システムは投資助言を行わず、分析する決算は評価対象の決算に加えて前四半期と前年同四半期の決算に特定し、DCF法などのバリュエーションモデルに基づく分析は行わないこととしました。
- EPS、FCF、guidance、management comment など評価軸を固定し、BullととBear, Judgeで論点を分離することで、分析の揺れを小さくするようにしました。
- また、決算レビューは四半期ごとに繰り返す定型業務なので、LLMに自由推論させるより、data ingestion -> routing ->specialist -> Bull/Bear -> Judge -> report の順序を固定した方が再現性・検証性が高いと判断しました。LLMにMarkdownを自由生成させるのではなく、構造化出力やソースやエビデンス、主張を検証してからrendererでreport化しています。
- すべてのエージェントに全データを渡すのではなく、ContextRouterによってEPSやFCFを見るエージェントには正規化済み財務データを中心に渡し、経営層のコメントやガイダンスを見るエージェントには決算資料由来の補助情報を渡すようにしました。これにより、無料APIやPDF抽出由来のノイズを減らし、各エージェントが自分の業務に集中できるようにしました。
- API key、model、SEC user-agent、log level、token上限などは環境変数で管理し、CLIとしてLLMを呼び出さなくてもワークフローの実行可能性の確認ができるようにしました。

システムについての詳細は以下に記しています。
- システムの処理責務、workflow、data processor、context routing、validation gates、CLI/API、CI/test gates の詳細: [docs/system/earnings-review-system.md](docs/system/earnings-review-system.md)
- 環境変数と default の一覧: [.env.example](.env.example) と [Configuration / Environment Variables](docs/system/earnings-review-system.md#configuration--environment-variables)

## サンプル

CLI sample と生成済み report の対応は、システム詳細の [Canonical Samples And Outputs](docs/system/earnings-review-system.md#5-canonical-samples-and-outputs) にまとめています。

- NVDA 2027Q1: `samples/request.nvda-2027q1.example.json` -> `outputs/sample-nvda-20260607/report.md`
- ZS 2026Q3: `samples/request.zs-2026q3.example.json` -> `outputs/sample-zs-20260607/report.md`

API key なしで CLI の動作確認をする場合は、下の `Minimal Run` のように `LLM_PROVIDER=fake` を指定します。
=======
# Earnings Debate Agent

Earnings Debate Agent is a fixed-workflow multi-agent system for quarterly
earnings review. It normalizes financial metrics and earnings documents, routes
role-scoped context to specialist agents, compares Bull and Bear cases, and
renders a source-backed Markdown report. It generates analysis artifacts; it
does not provide investment advice, trading recommendations, target prices, or
automated trading.


## Repository Structure

- `src/`: CLI/API entrypoints, preprocessing, context routing, workflow runtime,
  LLM provider wrappers, validation gates, and report rendering.
- `samples/`: normalized request examples that can run without live SEC or
  yfinance acquisition.
- `outputs/`: sample generated artifacts, including `workflow_result.json` and
  `report.md`.
- `docs/system/`: external system guide for architecture, input modes,
  environment variables, CLI/API usage, tests, and error handling.
- `.env.example`: environment variable template for providers, models, runtime
  limits, SEC access, output paths, and logging.
- `tests/`: contract, CLI/API, workflow, router, renderer, provider, and
  preprocessor tests.

## What It Can Do

- Run an earnings review from normalized sample JSON.
- Convert local PDF/text/Markdown files, raw text, or SEC filing input into
  source-referenced document sections through the CLI.
- Route role-specific context to financial, management, guidance, Bull/Bear,
  and Judge agents.
- Validate structured outputs, source references, evidence, claims, and report
  matrices before rendering.
- Run smoke and CI checks with `LLM_PROVIDER=fake` without real LLM API keys.

## Outputs

- `workflow_result.json`: structured workflow result, equivalent to the API
  success response.
- `report.md`: Markdown earnings review report with verdict, rationale,
  Bull/Bear tension, evidence matrix, quality gates, source appendix, and
  disclaimer.

## Minimal Run

```bash
PYTHON_DOTENV_DISABLED=1 \
LLM_PROVIDER=fake \
LOG_LEVEL=WARNING \
uv run earnings-debate run \
  --api-url local \
  --input-json samples/request.nvda-2027q1.example.json \
  --out /tmp/earnings-nvda-demo
```

The command writes:

```text
/tmp/earnings-nvda-demo/workflow_result.json
/tmp/earnings-nvda-demo/report.md
```
