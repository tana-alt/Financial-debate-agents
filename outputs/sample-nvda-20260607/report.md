# 決算レビュー: NVDA 2027Q1

## レポート前提: canonical data

- canonical dataはPython workflowで正規化したSEC、yfinance、derived metricのみを前提にします。
- presentation抽出値は補助資料であり、canonical dataとして扱いません。

| 期間役割(period_role) | metric | value | unit | source_type | provider | source_id | fiscal_period |
|---|---|---:|---|---|---|---|---|
| 当四半期(actual) | capex | -1,757,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:capex` | 2027Q1 |
| 当四半期(actual) | eps | 1.87 | USD/share | financial_api | yfinance | `financial_api:NVDA:2027Q1:yf:eps` | 2027Q1 |
| 当四半期(actual) | free_cash_flow | 48,587,000,000 | USD | derived_metric | - | `metric:NVDA:2027Q1:free_cash_flow:derived` | 2027Q1 |
| 当四半期(actual) | operating_cash_flow | 50,344,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:operating_cash_flow` | 2027Q1 |
| 当四半期(actual) | revenue | 81,615,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:revenue` | 2027Q1 |
| 前四半期(previous_quarter) | capex | -1,284,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:pq:capex` | 2027Q1 |
| 前四半期(previous_quarter) | eps | 1.62 | USD/share | financial_api | yfinance | `financial_api:NVDA:2027Q1:yf:pq:eps` | 2027Q1 |
| 前四半期(previous_quarter) | free_cash_flow | 34,904,000,000 | USD | derived_metric | - | `metric:NVDA:2027Q1:previous_quarter:free_cash_flow:derived` | 2027Q1 |
| 前四半期(previous_quarter) | operating_cash_flow | 36,188,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:pq:operating_cash_flow` | 2027Q1 |
| 前四半期(previous_quarter) | revenue | 68,127,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:pq:revenue` | 2027Q1 |
| 前年同期(year_ago_quarter) | capex | -1,227,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:ya:capex` | 2027Q1 |
| 前年同期(year_ago_quarter) | eps | 0.81 | USD/share | financial_api | yfinance | `financial_api:NVDA:2027Q1:yf:ya:eps` | 2027Q1 |
| 前年同期(year_ago_quarter) | free_cash_flow | 26,187,000,000 | USD | derived_metric | - | `metric:NVDA:2027Q1:year_ago_quarter:free_cash_flow:derived` | 2027Q1 |
| 前年同期(year_ago_quarter) | operating_cash_flow | 27,414,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:ya:operating_cash_flow` | 2027Q1 |
| 前年同期(year_ago_quarter) | revenue | 44,062,000,000 | USD | financial_api | sec_company_facts | `financial_api:NVDA:2027Q1:sec:0001045810:ya:revenue` | 2027Q1 |

## 要約

- 判定: good
- 信頼度: 0.82
- 要約: 当期実績はEPS、売上、営業CF、FCFのいずれも強く、前四半期・前年同期比でも改善が見られます。特にEPSはコンセンサスを上回り、FCFも48.587B USDと高水準でした。一方で、非GAAPとGAAPの差、前年の在庫要因の反動、中国需要を前提にしない見通し、供給・第三者製造依存などの不確実性があり、将来のEPS/FCF改善は条件付きです。それでも、現四半期の強い実績とキャッシュ創出が反対材料を上回るため、総合判定はgoodです。
- 統合メモ: EPS surprise はプラスで、売上成長と高い粗利率・営業レバレッジが質の高い上振れを支えています。ただし、粗利率改善の一部は前年の大きな在庫関連 charge の反動であり、非GAAPとGAAPの差も大きいので、完全に純粋なオペレーティング改善とは言い切れません。将来 EPS は引き続き成長余地がある一方、中国向け需要や供給・製造面の不確実性を会社自身が明示しており、継続性の評価はやや慎重です。FCF は高水準で P&L の強さと整合的ですが、本ロールでは詳細な FCF 分解は行っていません。 cash創出は強く、2027Q1のOCF 503.44億ドルとFCF 485.87億ドルは前四半期・前年同期比で改善しているため、FCF改善方向という見方が優勢です。CapExは増加しており将来の投資負担は残るものの、現時点ではOCFの増勢が上回っています。会社資料は供給・需要・製造・配送の不確実性を明示しているため、今後のFCFは投資継続と運転資本変動に左右される可能性があります。流動性・負債・満期の情報がないため、BS制約の評価は要追加データです。 経営陣は、Blackwell需要と次世代Vera Rubinへの移行を成長の中心に置きつつ、強いFCFを背景に大型の自社株買いと配当増額で株主還元も拡大している。短期のEPS/FCFは実績として強いが、供給制約、第三者依存、製品投入時期、地域別需要の不確実性が中期の実現性を左右する。投資判断の軸は、成長投資を継続しながら現金創出を株主還元に振り向ける意図がどれだけ安定して続くか、という点にある。 Guidance分析としては、Q2 FY27の売上・粗利率・営業費用・税率前提は提示されており、特に『中国のData Center compute revenueを前提にしない』点が重要な条件です。一方で、会社guidance本体とprecomputed consensus差分が欠けているため、保守的/強気の判定はunclearに留めるべきです。EPSは当期実績が予想を上回り、FCF/営業CFも強いですが、次期EPS/FCF改善への含意は会社ガイダンス不足のため限定的です。revision riskは、中国売上・供給・需要・第三者依存に左右される条件付きリスクがあるため中程度以上とみるのが妥当ですが、数値的裏付けは不足しています。

## 判定理由

- 判定: good
- 信頼度: 0.82
- 判断理由: Bull側は、EPS 1.87 USD/shareがコンセンサス1.77 USD/shareを上回ったこと、売上816.15億USDが前年同期440.62億USDから大きく伸びたこと、FCFが48.587B USDと高水準で前四半期・前年同期を上回ったことを根拠にしており、当期決算の強さは明確です。Bear側は、非GAAPとGAAPの差、粗利率改善の一部が前年の在庫関連一時要因の反動である点、中国向けData Center revenueを前提にしないQ2 outlook、供給・第三者製造依存のリスクを挙げています。これらは将来の継続性に対する重要な留保ですが、今回の実績ベースではEPSとFCFの強さが明確で、反対材料を上回っています。ガイダンス本文やconsensus差分が欠けているため次期見通しの定量判断は限定的ですが、これは verdict を neutral にするほどの不足ではありません。

## EPS/FCF見通し

### EPS
- 見通し: positive
- 根拠: 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。

### FCF
- 見通し: positive
- 根拠: FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。

## Bull/Bear論点

### Bull case
- 論旨: 今回の決算は、EPSの上振れ、売上の大幅増加、高水準のOCF/FCF、そして経営陣が成長投資と株主還元を同時に進める姿勢が揃っており、good と評価できる最も強いケースがある。特に当期実績では収益成長と現金創出が同時に確認でき、短期の業績品質は高い。一方で、粗利改善の一部に一時要因が含まれること、中国需要や供給制約などの前提条件付きであることは、強気評価の弱点として残る。
- 強さ: strong
- 信頼度: 0.86
- EPS論点: EPS は 1.87 USD/share でコンセンサス 1.77 USD/share を上回り、売上も 816.15億USD と前年同期の 440.62億USD から大幅増でした。さらに presentation では非GAAP粗利率 75.0%、非GAAP営業利益 538億ドル、非GAAP営業費用 74億ドルと示され、売上成長が利益成長に結びついています。粗利改善の一部は前年の在庫関連一時要因の反動ですが、それでも当期のEPS上振れは実需と営業レバレッジの強さを示します。
- FCF論点: 営業CF は 503.44億USD、FCF は 485.87億USD で高水準です。前四半期の FCF 349.04億USD、前年同期の 261.87億USD を上回っており、現金創出は明確に改善しています。CapEx は 17.57億USD と増えているものの、OCF と FCF の水準がそれを十分に吸収しており、少なくとも当期のキャッシュ面では強い決算でした。
- 成立条件: 中国向け Data Center compute revenue が想定以上に回復すること。; 供給・第三者製造・製造/配送の制約が大きく悪化しないこと。; 高水準のFCFが次四半期以降も継続し、CapEx増加を上回る現金創出が維持されること。; 粗利改善が一時要因だけでなく、継続的な利益率改善に広がること。
- 弱点: 非GAAP EPS と GAAP EPS の差が大きく、EPSの質には調整項目の影響が残る。; 粗利率改善の一部は前年の在庫関連 charge の反動で、完全な構造改善とは言い切れない。; Q2見通しは中国向け Data Center revenue を前提にしておらず、上振れ余地に条件がある。; 供給制約、第三者依存、需要変動などのリスクが会社自身により明示されている。; 会社の数値 guidance 本体と consensus 差分が入力内で欠けており、次期見通しの強さは定量比較しにくい。
- 注視点: 非GAAPとGAAPの差が今後も大きいままか。; 中国需要を織り込まない前提が次四半期の成長をどの程度制約するか。; 供給・第三者製造依存がFCFや出荷にどの程度波及するか。; FCF改善が運転資本要因ではなく持続的な収益力かどうか。
- 主要根拠ID: e1, e5, e3

### Bear case
- 論旨: 今回の決算は当期実績では強いが、熊派の観点では「良い決算だが、質と継続性には条件が付く」と見るのが妥当です。EPSはコンセンサス超えでも、非GAAPとGAAPの差、前年の在庫要因の反動、中国需要を前提にしないガイダンス、供給・第三者製造依存の不確実性が残るため、次期以降のEPS改善は実行条件に強く依存します。FCFも高水準ですが、CapEx増加と事業運営上の不確実性により、今後のFCF改善は自動的には続かない可能性があります。
- 強さ: moderate
- 信頼度: 0.82
- EPS論点: EPSは当期の1.87 USD/shareで予想を上回ったものの、非GAAP EPSとGAAP EPSの差が大きく、利益の質には調整項目の影響が残ります。さらに、粗利率改善の一部は前年の在庫関連一時要因の反動であり、構造的な改善だけでEPSが伸びたとは言い切れません。会社自身もQ2見通しで中国向けData Center revenueを前提にしておらず、供給・需要・第三者製造依存の不確実性を明示しているため、次期EPSの継続改善には条件が多いです。
- FCF論点: FCFは48.587B USDと強い一方、CapExも増加しており、将来FCFは投資継続度合いに左右されやすいです。加えて、会社資料は供給、在庫、製造・流通、第三者依存などの不確実性を明示しており、運転資本や投資計画のぶれがFCFに波及するリスクがあります。現時点のFCFは優秀でも、今後も同じペースで改善する保証はなく、投資負担の上振れがFCFの伸びを鈍らせる可能性があります。
- 悪化シナリオ: 非GAAPとGAAPの差が大きく、EPSの質評価が単純ではない。; 粗利率改善の一部が前年の在庫関連一時要因の反動で、継続改善とは限らない。; Q2見通しは中国向け売上を前提にしておらず、上振れ余地に条件がある。; 供給制約、第三者製造依存、需要変動などの実行リスクが残る。; CapEx増加により、FCFの改善が投資ペースに左右されやすい。
- Bull論点への反論: Bull側は当期EPS上振れと高いFCFを強調するが、その多くは当期実績の強さであって、次期以降の継続性は別問題です。; Bull側は売上成長と営業レバレッジを評価するが、粗利改善の一部は一時要因の反動で説明されています。; Bull側は株主還元の拡大を前向きに見るが、これは現金創出の使途であって、将来の需要や供給リスクを消すものではありません。; Bull側はVera RubinやBlackwellを成長ドライバーとみるが、会社自身が提供時期や実行タイミングの不確実性を認めています。; Bull側はガイダンスの明確さを前向きに捉えられる一方、会社guidance本体とconsensus差分が欠けており、定量比較は限定的です。
- 未解決リスク: 中国向けData Center revenueを織り込まない前提が、実需次第でEPSと売上に影響しうる。; 供給制約と第三者製造依存により、成長の実行速度がぶれる可能性がある。; CapEx増加が続く場合、FCFの伸びが投資負担に左右される。; 製品ロードマップの時期不確実性が中期成長のタイミングを遅らせる可能性がある。
- 主要根拠ID: c2, c1, c3

### リスクケース
Q2 見通しは中国向け Data Center revenue を前提にしていない; 非GAAP EPS と GAAP EPS の差が大きい; 会社自身が供給・需要・製造依存などの広い不確実性を明示

### Judgeの論点整理
Bull and Bear cases were generated from validated AnalysisBrief only.

### 未解決の問い
- 中国向けData Center revenueを織り込まない前提が、実需次第でEPSと売上に影響しうる。
- 供給制約と第三者製造依存により、成長の実行速度がぶれる可能性がある。
- CapEx増加が続く場合、FCFの伸びが投資負担に左右される。
- 製品ロードマップの時期不確実性が中期成長のタイミングを遅らせる可能性がある。

## Agent分析

| Agent | Stance | Contribution | Key evidence | Counter evidence | Confidence | Missing data |
|---|---|---|---|---|---:|---|
| EarningsQualityAnalyst | mixed | EPS surprise はプラスで、売上成長と高い粗利率・営業レバレッジが質の高い上振れを支えています。ただし、粗利率改善の一部は前年の大きな在庫関連 charge の反動であり、非GAAPとGAAPの差も大きいので、完全に純粋なオペレーティング改善とは言い切れません。将来 EPS は引き続き成長余地がある一方、中国向け需要や供給・製造面の不確実性を会社自身が明示しており、継続性の評価はやや慎重です。FCF は高水準で P&L の強さと整合的ですが、本ロールでは詳細な FCF 分解は行っていません。 | e1, e2, e3, e4, e5 | c1, c2, c3 | 0.90 | - |
| CashFlowRiskAnalyst | positive | cash創出は強く、2027Q1のOCF 503.44億ドルとFCF 485.87億ドルは前四半期・前年同期比で改善しているため、FCF改善方向という見方が優勢です。CapExは増加しており将来の投資負担は残るものの、現時点ではOCFの増勢が上回っています。会社資料は供給・需要・製造・配送の不確実性を明示しているため、今後のFCFは投資継続と運転資本変動に左右される可能性があります。流動性・負債・満期の情報がないため、BS制約の評価は要追加データです。 | e1, e2, e3, e4 | c1, c2 | 0.91 | 流動性、現金残高、負債、満期プロファイル、利払い負担の定量指標が routed_context に含まれていないため、balance-sheet 制約と financing risk の強弱は定量的に確認できない。; working capital の前年差・前四半期差の計算済み指標がないため、FCF改善が運転資本要因かどうかは限定的にしか判断できない。 |
| ManagementIntentAnalyst | mixed | 経営陣は、Blackwell需要と次世代Vera Rubinへの移行を成長の中心に置きつつ、強いFCFを背景に大型の自社株買いと配当増額で株主還元も拡大している。短期のEPS/FCFは実績として強いが、供給制約、第三者依存、製品投入時期、地域別需要の不確実性が中期の実現性を左右する。投資判断の軸は、成長投資を継続しながら現金創出を株主還元に振り向ける意図がどれだけ安定して続くか、という点にある。 | e1, e2, e3, e4, e5, e6 | c1, c2, c3 | 0.74 | 戦略投資の内訳（R&D、採用、CapEx、在庫積み増し等）の粒度が提示されておらず、どの施策がEPS/FCFに最も効くかを定量的に分解できない。 |
| GuidanceAnalyst | unclear | Guidance分析としては、Q2 FY27の売上・粗利率・営業費用・税率前提は提示されており、特に『中国のData Center compute revenueを前提にしない』点が重要な条件です。一方で、会社guidance本体とprecomputed consensus差分が欠けているため、保守的/強気の判定はunclearに留めるべきです。EPSは当期実績が予想を上回り、FCF/営業CFも強いですが、次期EPS/FCF改善への含意は会社ガイダンス不足のため限定的です。revision riskは、中国売上・供給・需要・第三者依存に左右される条件付きリスクがあるため中程度以上とみるのが妥当ですが、数値的裏付けは不足しています。 | ev1, ev2, ev3, ev4 | ev5, ev6, ev7 | 0.56 | 会社guidanceの本体テキストが入力内にないため、guidance vs consensusの方向性、保守性/強気性、revision riskを定量比較できません。; consensus_deltasが空のため、guidanceと市場予想の差分評価ができません。 |

## 根拠マトリクス (Evidence Matrix)

| Claim ID | Fact | Interpretation | Implication | Time scope | Fact-check status | Judge treatment | Sources |
|---|---|---|---|---|---|---|---|
| claim:e1 | EPS はコンセンサスを上回った (1.87 USD/share) | 実績 EPS は 1.87 USD/share で、コンセンサス 1.77 USD/share を上回り、EPS surprise_pct は 5.6497% とプラスでした。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | 2027Q1 | supported | supporting | financial_api:NVDA:2027Q1:yf:eps / eps |
| claim:e2 | 売上は高水準で前年比も強い (81,615,000,000 USD) | 売上実績は 816.15億USD で、前年同期の 440.62億USD を大きく上回っています。売上規模の拡大は EPS の質を支える材料です。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | 2027Q1 | supported | supporting | financial_api:NVDA:2027Q1:sec:0001045810:revenue / revenue |
| claim:e3 | 非GAAP粗利率と営業利益率が高く、営業レバレッジを示唆 | Presentation では Q1 FY27 の非GAAP粗利率が 75.0%、非GAAP営業利益が 538億ドル、非GAAP営業費用が 74億ドルと示され、売上成長に対して利益成長が大きい構図です。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | 2027Q1 | supported | not_used | nvda-f1q27-presentation:p10:section-1 / nvda-f1q27-presentation:p10:section-1 |
| claim:e4 | 粗利率改善の一部は前年の在庫関連一時要因の反動 | Presentation は、粗利率の前年比改善が主として前年の 45億USD の H20 excess inventory charge に伴う在庫引当減少によるものだと説明しています。したがって、粗利率改善の一部は継続的な改善というよりベース効果の色合いがあります。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | 2027Q1 | supported | not_used | nvda-f1q27-presentation:p5:section-1 / nvda-f1q27-presentation:p5:section-1 |
| claim:e5 | 営業CF と FCF は高水準で、P&L の強さが現金創出にも整合 (48,587,000,000 USD) | 営業CF は 503.44億USD、FCF は 485.87億USD で、Presentation の FCF reconciliation でも高い現金創出が確認できます。P&L の収益性の高さが現金生成に反映されています。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | 2027Q1 | supported | supporting | metric:NVDA:2027Q1:free_cash_flow:derived / free_cash_flow |
| claim:e6 | 会社は供給、在庫、製造・流通、第三者依存などを重要な不確実性として明示している。 | プレゼンテーションは forward-looking statements に関する注意書きとして、第三者製造への依存、需要変化、技術競争、製品の市場受容、設計/製造/ソフトウェア不具合、統合時の性能低下などを列挙している。これは経営意図の実行面に重要な制約があることを会社自身が認めている材料で、近中期のEPS/FCF見通しにリスクを与える。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | 2027Q1 | supported | not_used | nvda-f1q27-presentation:p2:section-1 / nvda-f1q27-presentation:p2:section-1 |
| claim:ev1 | Q2 FY27の見通し前提が明示されている (91 USD billion) | Q2 FY27について、売上91.0B USD（±2%）、非GAAP粗利率75.0%（±50bp）、営業費用8.3B USD程度、年率税率16%-18%が示されており、見通し条件が資料上かなり明確です。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | Q2 FY27 | supported | not_used | nvda-f1q27-presentation:p11:section-1 / nvda-f1q27-presentation:p11:section-1 |
| claim:ev2 | China売上を前提にしない注意書きがある | 『Outlook does not assume any Data Center compute revenue from China』と明記されており、見通しが中国需要・規制要因に左右されうることを会社自身が示しています。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | Q2 FY27 | supported | not_used | nvda-f1q27-presentation:p11:section-1 / nvda-f1q27-presentation:p11:section-1 |
| claim:ev3 | 当期EPS実績は予想を上回っている (1.87 USD/share) | 実績EPS 1.87 USD/shareは、入力内の consensus EPS 1.77 USD/share を上回っています。これは当期実績ベースではポジティブです。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | 2027Q1 | supported | not_used | financial_api:NVDA:2027Q1:yf:eps / eps |
| claim:ev4 | 当期FCFと営業CFはプラスで堅調 (48,587,000,000 USD) | 実績FCF 48.587B USD、営業CF 50.344B USDが示されており、キャッシュ創出力は強い状態です。将来FCF改善の方向感としては支援材料ですが、guidanceがないため次期見通しそのものは未確定です。 | 当期EPSは1.87 USD/shareでコンセンサス1.77 USD/shareを上回り、売上成長と高い粗利率・営業レバレッジが支えています。粗利率改善の一部は一時要因の反動ですが、それでも実績としては強い上振れです。ただし、Q2見通しは中国向けData Center revenueを前提にしておらず、供給・第三者製造依存の不確実性もあるため、将来EPSの継続改善は条件付きです。 | 2027Q1 | supported | not_used | metric:NVDA:2027Q1:free_cash_flow:derived / free_cash_flow |
| claim:c1 | 非GAAP EPS と GAAP EPS の差が大きい | Presentation では Q1 FY27 の非GAAP EPS は 1.87 USD/share だが、GAAP EPS は 2.39 USD/share と表示され、調整項目の影響が大きいことを示します。EPS の質を評価する際は、調整要因の存在を考慮する必要があります。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | 2027Q1 | supported | counter_evidence | nvda-f1q27-presentation:p13:section-1 / nvda-f1q27-presentation:p13:section-1 |
| claim:c2 | Q2 見通しは中国向け Data Center revenue を前提にしていない | Presentation の Q2 FY27 outlook は「Outlook does not assume any Data Center compute revenue from China」と明記しており、将来の売上・EPS に関して中国要因の不確実性があることを示します。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | 2027Q1 | supported | counter_evidence | nvda-f1q27-presentation:p11:section-1 / nvda-f1q27-presentation:p11:section-1 |
| claim:c3 | 会社自身が供給・需要・製造依存などの広い不確実性を明示 | Presentation は供給と需要、第三者製造依存、製品採用、競争、技術変化などが結果を左右し得ると記載しており、EPS の継続改善には実行リスクが残ります。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | 2027Q1 | supported | counter_evidence | nvda-f1q27-presentation:p2:section-1 / nvda-f1q27-presentation:p2:section-1 |
| claim:ev5 | 会社guidance本体が入力内にない (81,615,000,000 USD) | guidance metricsに『No company guidance text is available in routed inputs.』とあり、guidance vs consensusやrevision riskを本来の形式で比較できません。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | 2027Q1 | supported | not_used | financial_api:NVDA:2027Q1:sec:0001045810:revenue / revenue |
| claim:ev6 | consensus差分が空で比較不能 | consensus_deltasが空で、guidanceと市場予想の乖離を示すprecomputed差分が提供されていません。したがって、保守的か強気かの判定は限定的です。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | Q2 FY27 | not_checkable | not_used | nvda-f1q27-presentation:p15:section-1 / nvda-f1q27-presentation:p15:section-1 |
| claim:ev7 | forward-looking注記が広く、実現には複数条件が必要 | 会社は供給制約、第三者依存、競争、需要変動、製品・ソフトウェア不具合など多数のリスクを列挙しており、見通し達成には外部条件が重要です。 | FCFは48.587B USD、営業CFは50.344B USDと非常に強く、前四半期・前年同期からも改善しています。CapExは増加しているものの、現時点ではOCFとFCFの水準が投資負担を十分に吸収しています。もっとも、会社資料は供給・在庫・製造・配送・第三者依存の不確実性を明示しており、今後のFCFは投資継続と運転資本変動に左右される可能性があります。 | Q2 FY27 | supported | not_used | nvda-f1q27-presentation:p2:section-1 / nvda-f1q27-presentation:p2:section-1 |

## データ品質

- 入力プロファイル: yfinance_sec_presentation_tagged
- 期間検証: partial
- metric conflict: none
- guidance delta: company_guidance_missing
- presentation tag coverage: guidance=yes, management=no, cash_flow=yes, risk=no
- input_profile: available - Input profile: yfinance_sec_presentation_tagged
- revenue: available - Required canonical metric revenue is available.
- eps: available - Required canonical metric eps is available.
- operating_cash_flow: available - Required canonical metric operating_cash_flow is available.
- capex: available - Required canonical metric capex is available.
- free_cash_flow: available - Required canonical metric free_cash_flow is available.
- previous_quarter:revenue: available - Required canonical metric previous_quarter:revenue is available.
- previous_quarter:eps: available - Required canonical metric previous_quarter:eps is available.
- previous_quarter:operating_cash_flow: available - Required canonical metric previous_quarter:operating_cash_flow is available.
- previous_quarter:capex: available - Required canonical metric previous_quarter:capex is available.
- previous_quarter:free_cash_flow: available - Required canonical metric previous_quarter:free_cash_flow is available.
- year_ago_quarter:revenue: available - Required canonical metric year_ago_quarter:revenue is available.
- year_ago_quarter:eps: available - Required canonical metric year_ago_quarter:eps is available.
- year_ago_quarter:operating_cash_flow: available - Required canonical metric year_ago_quarter:operating_cash_flow is available.
- year_ago_quarter:capex: available - Required canonical metric year_ago_quarter:capex is available.
- year_ago_quarter:free_cash_flow: available - Required canonical metric year_ago_quarter:free_cash_flow is available.
- period_verification: available - Period verification: verified

## 不確実性と不足データ

- matrix-levelの不足データ項目はありません。

### Agent missing data
- CashFlowRiskAnalyst: 流動性、現金残高、負債、満期プロファイル、利払い負担の定量指標が routed_context に含まれていないため、balance-sheet 制約と financing risk の強弱は定量的に確認できない。
- CashFlowRiskAnalyst: working capital の前年差・前四半期差の計算済み指標がないため、FCF改善が運転資本要因かどうかは限定的にしか判断できない。
- ManagementIntentAnalyst: 戦略投資の内訳（R&D、採用、CapEx、在庫積み増し等）の粒度が提示されておらず、どの施策がEPS/FCFに最も効くかを定量的に分解できない。
- GuidanceAnalyst: 会社guidanceの本体テキストが入力内にないため、guidance vs consensusの方向性、保守性/強気性、revision riskを定量比較できません。
- GuidanceAnalyst: consensus_deltasが空のため、guidanceと市場予想の差分評価ができません。

### 未解決の問い
- 中国向けData Center revenueを織り込まない前提が、実需次第でEPSと売上に影響しうる。
- 供給制約と第三者製造依存により、成長の実行速度がぶれる可能性がある。
- CapEx増加が続く場合、FCFの伸びが投資負担に左右される。
- 製品ロードマップの時期不確実性が中期成長のタイミングを遅らせる可能性がある。

## 品質ゲート (Quality Gates)

- ReportMatrix検証: passed
- source_manifest entries: 32
- 根拠項目: 16
- claim records: 16
- decision uses: 16
- 不足データ項目: 0
- data quality flags: 17
- fact-check statuses: not_checkable: 1, supported: 15
- judge treatments: counter_evidence: 3, not_used: 10, supporting: 3
- source_ref整合性: 登録済みsource_manifestと内部整合
- no-advice framing: 免責事項に明記

## ソース付録 (Source Appendix)

| Source ID | Type | Locator | Title | Reported period | URL |
|---|---|---|---|---|---|
| `financial_api:NVDA:2027Q1:sec:0001045810:revenue` | financial_api | revenue | SEC Company Facts Revenues period_role=actual method=direct_quarter form=10-Q end=2026-04-26 accn=0001045810-26-000052 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:operating_cash_flow` | financial_api | operating_cash_flow | SEC Company Facts NetCashProvidedByUsedInOperatingActivities period_role=actual method=direct_quarter form=10-Q end=2026-04-26 accn=0001045810-26-000052 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:capex` | financial_api | capex | SEC Company Facts PaymentsToAcquireProductiveAssets period_role=actual method=direct_quarter form=10-Q end=2026-04-26 accn=0001045810-26-000052 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:yf:eps` | financial_api | eps | yfinance verified-period metric | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:yf:consensus:eps_consensus` | financial_api | eps_consensus | yfinance verified-period metric | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:yf:pq:eps` | financial_api | eps | yfinance verified-period metric | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:yf:ya:eps` | financial_api | eps | yfinance verified-period metric | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:pq:revenue` | financial_api | revenue | SEC Company Facts Revenues period_role=previous_quarter method=ytd_difference form=10-K end=2026-01-25 accn=0001045810-26-000021 prior_end=2025-10-26 prior_accn=0001045810-25-000230 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:pq:operating_cash_flow` | financial_api | operating_cash_flow | SEC Company Facts NetCashProvidedByUsedInOperatingActivities period_role=previous_quarter method=ytd_difference form=10-K end=2026-01-25 accn=0001045810-26-000021 prior_end=2025-10-26 prior_accn=0001045810-25-000230 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:pq:capex` | financial_api | capex | SEC Company Facts PaymentsToAcquireProductiveAssets period_role=previous_quarter method=ytd_difference form=10-K end=2026-01-25 accn=0001045810-26-000021 prior_end=2025-10-26 prior_accn=0001045810-25-000230 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:ya:revenue` | financial_api | revenue | SEC Company Facts Revenues period_role=year_ago_quarter method=direct_quarter form=10-Q end=2025-04-27 accn=0001045810-26-000052 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:ya:operating_cash_flow` | financial_api | operating_cash_flow | SEC Company Facts NetCashProvidedByUsedInOperatingActivities period_role=year_ago_quarter method=direct_quarter form=10-Q end=2025-04-27 accn=0001045810-26-000052 | 2027Q1 | no URL |
| `financial_api:NVDA:2027Q1:sec:0001045810:ya:capex` | financial_api | capex | SEC Company Facts PaymentsToAcquireProductiveAssets period_role=year_ago_quarter method=direct_quarter form=10-Q end=2025-04-27 accn=0001045810-26-000052 | 2027Q1 | no URL |
| `metric:NVDA:2027Q1:free_cash_flow:derived` | derived_metric | free_cash_flow | Derived free cash flow | 2027Q1 | no URL |
| `metric:NVDA:2027Q1:previous_quarter:free_cash_flow:derived` | derived_metric | free_cash_flow | Derived free cash flow | 2027Q1 | no URL |
| `metric:NVDA:2027Q1:year_ago_quarter:free_cash_flow:derived` | derived_metric | free_cash_flow | Derived free cash flow | 2027Q1 | no URL |
| `nvda-f1q27-presentation:p1:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p1:section-1, page 1 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p2:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p2:section-1, page 2 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p3:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p3:section-1, page 3 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p4:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p4:section-1, page 4 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p5:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p5:section-1, page 5 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p6:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p6:section-1, page 6 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p7:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p7:section-1, page 7 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p8:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p8:section-1, page 8 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p9:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p9:section-1, page 9 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p10:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p10:section-1, page 10 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p11:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p11:section-1, page 11 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p12:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p12:section-1, page 12 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p13:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p13:section-1, page 13 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p14:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p14:section-1, page 14 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p15:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p15:section-1, page 15 | NVDA F1Q27 quarterly presentation | - | no URL |
| `nvda-f1q27-presentation:p16:section-1` | earnings_presentation | nvda-f1q27-presentation, nvda-f1q27-presentation:p16:section-1, page 16 | NVDA F1Q27 quarterly presentation | - | no URL |

## 免責事項

本レポートは決算分析のための成果物であり、投資助言ではありません。特定の取引判断や価格水準の提示を目的とするものではありません。