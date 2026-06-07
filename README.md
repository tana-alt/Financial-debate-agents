1. タスクを自動化しようと思った動機
- 私は株式投資を行なっており、投資している銘柄や監視銘柄は毎四半期ごとに決算の内容を確認している。
- これを継続的なタスクとみなし、客観的な視点からの決算分析の自動化は将来的なタイムパフォーマンスを考えると非常に有用だと考えた。
- そのため、EPS、P&L、FCF等の持続性と市場コンセンサスとの乖離という私が普段注目している視点から決算を分析して決算の良し悪しを判定する固定ワークフローのマルチエージェントシステムを開発した。

2. システム設計上の設計思想
- 本システムは投資助言を行わず、分析する決算は評価対象の決算に加えて前四半期と前年同四半期の決算に特定し、DCF法などのバリュエーションモデルに基づく分析は行わないこととした。
- EPS、FCF、guidance、management comment など評価軸を固定し、BullととBear, Judgeで論点を分離することで、分析の揺れを小さくするようにした。
- また、決算レビューは四半期ごとに繰り返す定型業務なので、LLMに自由推論させるより、data ingestion -> routing ->specialist -> Bull/Bear -> Judge -> report の順序を固定した方が再現性・検証性が高いと判断した。LLMにMarkdownを自由生成させるのではなく、構造化出力やソースやエビデンス、主張を検証してからrendererでreport化する
- すべてのエージェントに全データを渡すのではなく、ContextRouterによってEPSやFCFを見るエージェントには正規化済み財務データを中心に渡し、経営層のコメントやガイダンスを見るエージェントには決算資料由来の補助情報を渡すようにした。これにより、無料APIやPDF抽出由来のノイズを減らし、各エージェントが自分の業務に集中できるようにした。
- API key、model、SEC user-agent、log level、token上限などは環境変数で管理し、CLIとしてLLMを呼び出さなくてもワークフローの実行可能性の確認ができるようにした。

システムについての詳細は以下に記している。
- システムの処理責務、workflow、data processor、context routing、validation gates、CLI/API、CI/test gates の詳細: [docs/system/earnings-review-system.md](docs/system/earnings-review-system.md)
- 環境変数と default の一覧: [.env.example](.env.example) と [Configuration / Environment Variables](docs/system/earnings-review-system.md#configuration--environment-variables)