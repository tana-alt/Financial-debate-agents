# 決算レビュー: ZS 2026Q3

## レポート前提: canonical data

- canonical dataはPython workflowで正規化したSEC、yfinance、derived metricのみを前提にします。
- presentation抽出値は補助資料であり、canonical dataとして扱いません。

| 期間役割(period_role) | metric | value | unit | source_type | provider | source_id | fiscal_period |
|---|---|---:|---|---|---|---|---|
| 当四半期(actual) | capex | -42,401,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:capex` | 2026Q3 |
| 当四半期(actual) | eps | 1.08 | USD/share | financial_api | yfinance | `financial_api:ZS:2026Q3:yf:eps` | 2026Q3 |
| 当四半期(actual) | free_cash_flow | 155,615,000 | USD | derived_metric | - | `metric:ZS:2026Q3:free_cash_flow:derived` | 2026Q3 |
| 当四半期(actual) | operating_cash_flow | 198,016,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:operating_cash_flow` | 2026Q3 |
| 当四半期(actual) | revenue | 850,475,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:revenue` | 2026Q3 |
| 前四半期(previous_quarter) | capex | -17,755,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:pq:capex` | 2026Q3 |
| 前四半期(previous_quarter) | eps | 1.01 | USD/share | financial_api | yfinance | `financial_api:ZS:2026Q3:yf:pq:eps` | 2026Q3 |
| 前四半期(previous_quarter) | free_cash_flow | 186,318,000 | USD | derived_metric | - | `metric:ZS:2026Q3:previous_quarter:free_cash_flow:derived` | 2026Q3 |
| 前四半期(previous_quarter) | operating_cash_flow | 204,073,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:pq:operating_cash_flow` | 2026Q3 |
| 前四半期(previous_quarter) | revenue | 815,751,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:pq:revenue` | 2026Q3 |
| 前年同期(year_ago_quarter) | capex | -72,163,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:ya:capex` | 2026Q3 |
| 前年同期(year_ago_quarter) | eps | 0.84 | USD/share | financial_api | yfinance | `financial_api:ZS:2026Q3:yf:ya:eps` | 2026Q3 |
| 前年同期(year_ago_quarter) | free_cash_flow | 138,918,000 | USD | derived_metric | - | `metric:ZS:2026Q3:year_ago_quarter:free_cash_flow:derived` | 2026Q3 |
| 前年同期(year_ago_quarter) | operating_cash_flow | 211,081,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:ya:operating_cash_flow` | 2026Q3 |
| 前年同期(year_ago_quarter) | revenue | 678,034,000 | USD | financial_api | sec_company_facts | `financial_api:ZS:2026Q3:sec:0001713683:ya:revenue` | 2026Q3 |

## 要約

- 判定: neutral
- 信頼度: 0.87
- 要約: Q3はEPS・売上・FCFの実績がそろって強く、表面的には良い決算です。一方で、GAAP EPSは赤字でnon-GAAP依存があり、会社自身がQ4のCapEx前倒しとFY27のCapEx上昇、営業体制移行を明示しているため、EPSとFCFの将来方向が完全にそろっていません。したがって総合判断はgoodでもbadでもなくneutralです。
- 統合メモ: EPS surprise はプラスで、売上成長・粗利率・営業利益率の組み合わせから今四半期の利益品質は良好です。特に売上はコンセンサス超えというより、会社ガイダンス上限も超過しており、需要面の強さが示唆されます。いっぽう、non-GAAP EPS 依存でGAAPは赤字である点、ならびにQ4以降のcapex増加見通しと営業リーダー交代に伴う慎重姿勢が、将来EPS/FCFの伸びをやや抑制する可能性があります。次工程では、ガイダンスの実現性、調整項目の持続性、capex上昇がFCFマージンに与える影響を重点確認してください。 FCFは黒字を維持し、前年差では改善しているため短期のキャッシュ生成基盤は良好です。一方で、前四半期比ではFCFが低下し、会社自身がcash collectionsのタイミングと今後のCapEx前倒しを明示しています。流動性は3.5B USDの現金等と1.7B USDの負債で当面は厚く、直ちに資金制約が強い局面ではありません。ただし、Q4およびFY27のCapEx上昇見通しは将来FCFの拡大を抑える主要リスクで、次工程ではこのCapEx強化が売上成長に見合う投資か、あるいはFCFマージンの再拡大を遅らせる要因かを重視してください。 Managementの本音は、AI関連需要を成長エンジンとして取り込みつつ、Zero Trust Everywhere・AI Security・Data Securityを横断的に拡大し、販売経路としてZ-Flex、GSI、Cloud Marketplaceを強化することです。足元のQ3は売上・利益・FCFともに強く、EPS/FCFへの短期影響はポジティブでした。一方で、データセンター設備の価格上昇に対応するためのcapex前倒しは近い期間のFCFを圧迫し、Red Canaryは更新依存と高churnのためFY27の質に注意が必要です。営業組織の入れ替えも短期実行リスクとして残ります。 Guidance は売上・EPS・FCF ともに継続成長を示す内容だが、consensus delta が空のため期待比の強弱は判定不能。会社はQ4/FY26で non-GAAP Revenue $875M-$878M、FY26 Revenue $3.3295B-$3.3325B、Q4 EPS $1.08-$1.09、FY26 EPS $4.10-$4.11、Q4/FY26 FCF margin 約22.8%-23.3% を提示し、同時に営業リーダー交代、capex前倒し、FY27 capex率上昇、Red Canary高churn などの条件付きリスクも明示している。短期は保守的なガイダンスの可能性がある一方、中期のrevision risk はFCF側でやや高め。

## 判定理由

- 判定: neutral
- 信頼度: 0.87
- 判断理由: Bull側は、EPS 1.08がコンセンサス1.01を上回り、売上も850.475M USDで前年同期比25%増かつガイダンス上限超え、non-GAAP営業利益率23.0%、non-GAAP gross margin 81%、FCF 155.615M USDと営業CF 198.016M USDがそろって強い点を示しています。Bear側は、GAAP EPSが(0.09)で赤字、Q3 FCFマージンが16.0%へ低下し、会社がcash collectionsのタイミング要因とQ4/FY27のCapEx上昇を明示している点、さらに営業リーダー2名の退任でガイダンスがprudent approach になっている点を挙げています。重要なのは、EPS面は短期では強い一方で、FCF面はCapEx前倒しと回収タイミングの影響で逆風があり、将来EPS/FCFの方向が同じ強さで改善するとまでは言えないことです。なお、required canonical metrics はすべて利用可能で、missing data による判定不能ではありません。

## EPS/FCF見通し

### EPS
- 見通し: mixed
- 根拠: EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。

### FCF
- 見通し: mixed
- 根拠: FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。

## Bull/Bear論点

### Bull case
- 論旨: 今回のQ3は、EPSがコンセンサスを上回り、売上もガイダンス上限を超え、非GAAP営業利益率と粗利率が高位で維持されたため、利益面の質は概ね良好です。さらにFCFは黒字で前年差改善、営業CFも十分で、当面の流動性も厚いです。短期の逆風としては、会社自身が示すcapex前倒しと回収タイミング要因があるものの、今回の決算自体をgood寄りに評価できる根拠は強いです。
- 強さ: strong
- 信頼度: 0.93
- EPS論点: EPSは1.08 USD/shareでコンセンサス1.01 USD/shareを上回り、売上も850,475,000 USDで前年同期比25%増、かつガイダンス上限を超過しました。加えて非GAAP営業利益率は23.0%へ上昇し、non-GAAP gross margin 81%も高位を維持しており、売上成長が利益改善に結びついています。GAAP赤字という弱点はあるものの、当四半期のheadline EPSは少なくとも期待超えとして扱える内容です。
- FCF論点: FCFは155,615,000 USDで黒字を維持し、営業CFも198,016,000 USDと十分でした。前年同期のFCF 138,918,000 USDからは改善しており、capex 42,401,000 USDは投資負担として存在するものの、現時点ではキャッシュ創出を大きく損なう水準ではありません。さらに期末の現金等3.5B USDと負債1.7B USDにより、短期の資金制約は見えにくいです。
- 成立条件: Q4以降のcapex前倒しが売上成長に見合う形で回収されること。; cash collectionsのタイミング要因が一時的で、FCFマージンの基調悪化にならないこと。; 営業体制の移行がQ4の実行力を大きく損なわないこと。
- 弱点: GAAP EPSは(0.09)で、利益の質は非GAAP依存が強いです。; 会社自身がQ4とFY27でcapex上昇を明示しており、将来FCFの伸びは圧迫されやすいです。; Q3のFCFマージンは16.0%で、前年18.0%から低下しています。; 営業リーダー2名の退任により、短期のガイダンス/実行リスクがあります。
- 注視点: GAAP赤字とnon-GAAP EPSの差が今後も大きいままか。; capex前倒しがFY27以降のFCF改善を遅らせないか。; 営業リーダー交代が受注やガイダンス精度に影響しないか。; cash collectionsのタイミング要因が継続的な弱さではないか。
- 主要根拠ID: ev1, ev2, ev5

### Bear case
- 論旨: 今回の決算は表面的にはEPS・売上ともに強いが、質の面では非GAAP依存が大きく、GAAP EPSは赤字でした。加えて、会社自身がQ4の高CapExとFY27のCapEx比率上昇を明示しており、短期FCFの伸びは今後鈍化しやすいです。したがって、四半期の評価は「良い」よりも、利益品質とFCF持続性に条件付きの懸念が残るneutral寄りの見方が妥当です。
- 強さ: moderate
- 信頼度: 0.79
- EPS論点: EPSは1.08でコンセンサス1.01を上回りましたが、GAAP EPSは(0.09)で赤字でした。つまり、今回の上振れは非GAAP調整の恩恵が大きく、利益の質は全面的に強いとは言えません。さらに会社は営業リーダー2名の退任を受けてガイダンスをprudent approachで示しており、短期の実行リスクがEPSの継続性を曇らせます。
- FCF論点: FCFは155.615M USDで黒字を維持したものの、前四半期186.318M USDからは低下しており、会社もcash collectionsのtimingが影響したと説明しています。加えて、Q4にCapExを前倒しし、FY27ではCapEx as a percentage of revenue がFY26比で最大200bp上昇する可能性を会社自身が示しており、FCFの拡大余地は将来圧迫されやすいです。短期的な流動性は厚い一方で、FCFの質と持続性には明確な逆風があります。
- 悪化シナリオ: GAAP利益が赤字で、non-GAAP EPSだけで強さを判断すると利益品質を過大評価しやすい。; CapEx前倒しとFY27のCapEx率上昇により、FCFマージンの再拡大が遅れる可能性がある。; cash collectionsのタイミング要因でFCFがブレており、四半期比較の見栄えが安定しにくい。; 営業リーダー退任に伴う移行期リスクがあり、ガイダンスの実現確度がやや下がる。
- Bull論点への反論: Bull case の「EPS上振れと売上超過で良い決算」という主張は事実だが、GAAP EPS赤字と調整後利益依存を無視しており、利益の質まで十分には示していません。; Bull case の「FCFはプラスだから問題ない」という見方に対しては、Q3で前四半期比低下しており、会社自身が将来CapEx増加を明示しているため、持続性は別問題です。; Bull case の「ガイダンスは成長継続を示す」という点も、営業リーダー交代とprudent approachの明示があり、単純な強気評価にはできません。; Bull case の「流動性が厚いので安心」という論点は短期資金繰りには有効でも、FCF成長の鈍化リスクを打ち消すものではありません。
- 未解決リスク: GAAPベースでの利益回復が続くかは、現時点では非GAAP調整の持続性次第です。; CapEx前倒しが一時的なものか、FY27以降も高水準で続くかは未確定です。; 営業組織の移行が売上成長とEPS達成に与える影響はまだ見極め段階です。; cash collectionsのタイミング要因が来四半期以降に正常化するかは不明です。
- 主要根拠ID: ce2, ce1, ce3

### リスクケース
今後はcapex増加でFCFが圧迫される可能性がある; EPSは調整後ベースで、GAAP利益は赤字だった; ガイダンスは人事移行リスクを織り込んでいる

### Judgeの論点整理
Bull and Bear cases were generated from validated AnalysisBrief only.

### 未解決の問い
- GAAPベースでの利益回復が続くかは、現時点では非GAAP調整の持続性次第です。
- CapEx前倒しが一時的なものか、FY27以降も高水準で続くかは未確定です。
- 営業組織の移行が売上成長とEPS達成に与える影響はまだ見極め段階です。
- cash collectionsのタイミング要因が来四半期以降に正常化するかは不明です。

## Agent分析

| Agent | Stance | Contribution | Key evidence | Counter evidence | Confidence | Missing data |
|---|---|---|---|---|---:|---|
| EarningsQualityAnalyst | positive | EPS surprise はプラスで、売上成長・粗利率・営業利益率の組み合わせから今四半期の利益品質は良好です。特に売上はコンセンサス超えというより、会社ガイダンス上限も超過しており、需要面の強さが示唆されます。いっぽう、non-GAAP EPS 依存でGAAPは赤字である点、ならびにQ4以降のcapex増加見通しと営業リーダー交代に伴う慎重姿勢が、将来EPS/FCFの伸びをやや抑制する可能性があります。次工程では、ガイダンスの実現性、調整項目の持続性、capex上昇がFCFマージンに与える影響を重点確認してください。 | ev1, ev2, ev3, ev4, ev5 | ce1, ce2, ce3 | 0.92 | - |
| CashFlowRiskAnalyst | mixed | FCFは黒字を維持し、前年差では改善しているため短期のキャッシュ生成基盤は良好です。一方で、前四半期比ではFCFが低下し、会社自身がcash collectionsのタイミングと今後のCapEx前倒しを明示しています。流動性は3.5B USDの現金等と1.7B USDの負債で当面は厚く、直ちに資金制約が強い局面ではありません。ただし、Q4およびFY27のCapEx上昇見通しは将来FCFの拡大を抑える主要リスクで、次工程ではこのCapEx強化が売上成長に見合う投資か、あるいはFCFマージンの再拡大を遅らせる要因かを重視してください。 | e1, e2, e3, e4, e5 | c1, c2 | 0.89 | - |
| ManagementIntentAnalyst | positive | Managementの本音は、AI関連需要を成長エンジンとして取り込みつつ、Zero Trust Everywhere・AI Security・Data Securityを横断的に拡大し、販売経路としてZ-Flex、GSI、Cloud Marketplaceを強化することです。足元のQ3は売上・利益・FCFともに強く、EPS/FCFへの短期影響はポジティブでした。一方で、データセンター設備の価格上昇に対応するためのcapex前倒しは近い期間のFCFを圧迫し、Red Canaryは更新依存と高churnのためFY27の質に注意が必要です。営業組織の入れ替えも短期実行リスクとして残ります。 | e1, e2, e3, e4, e5 | c1, c2, c3 | 0.90 | counter_evidenceは十分に確認できたため主要論点の判定は可能ですが、guidance数値の詳細比較は本ロールの対象外のため、見通しの強弱は定量的には深掘りしていません。 |
| GuidanceAnalyst | unclear | Guidance は売上・EPS・FCF ともに継続成長を示す内容だが、consensus delta が空のため期待比の強弱は判定不能。会社はQ4/FY26で non-GAAP Revenue $875M-$878M、FY26 Revenue $3.3295B-$3.3325B、Q4 EPS $1.08-$1.09、FY26 EPS $4.10-$4.11、Q4/FY26 FCF margin 約22.8%-23.3% を提示し、同時に営業リーダー交代、capex前倒し、FY27 capex率上昇、Red Canary高churn などの条件付きリスクも明示している。短期は保守的なガイダンスの可能性がある一方、中期のrevision risk はFCF側でやや高め。 | e1, e2, e3, e4, e5 | c1, c2, c3 | 0.58 | 会社のguidance本文に対応する precomputed guidance deltas が提供されていないため、guidance vs consensus を定量評価できません。; Q4/FY26の revenue / EPS / FCF guidance に対応する consensus estimate が routed_context にありません。; required canonical metric の欠損はありませんが、guidance の妥当性をより厳密に比較するための guidance_consensus_deltas が必要です。 |

## 根拠マトリクス (Evidence Matrix)

| Claim ID | Fact | Interpretation | Implication | Time scope | Fact-check status | Judge treatment | Sources |
|---|---|---|---|---|---|---|---|
| claim:ev1 | EPSはコンセンサスを上回った (1.08 USD/share) | 実績EPSは1.08 USD/shareで、コンセンサス1.01 USD/shareを上回った。source_indexではyfinance verified-period metricとして記録されている。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | supporting | financial_api:ZS:2026Q3:yf:eps / eps |
| claim:ev2 | 売上は高い成長率で増加した (850,475,000 USD) | 実績売上は850,475,000 USDで、前年同期の678,034,000 USDから増加している。shareholder letterでもRevenue of $850 million grew 25% year-over-year and 4% sequentially, exceeding the high end of guidance と説明されている。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | supporting | financial_api:ZS:2026Q3:sec:0001713683:revenue / revenue |
| claim:ev3 | 営業利益率が高水準で拡大した (23 %) | 会社はnon-GAAP operating marginが23.0%で前年比140bp上昇したと示しており、non-GAAP operating incomeも196百万USDへ増加している。売上成長に対する利益成長が強く、オペレーティングレバレッジの改善を示唆する。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p18:section-1 / zs-fy2026-q3-shareholder-letter:p18:section-1 |
| claim:ev4 | 粗利率は高位を維持した (81 %) | shareholder letterのAppendixではnon-GAAP gross marginが81%で、前年同期80%から高位で推移している。粗利率の安定は売上品質と収益性の両面でプラス。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p27:section-1 / zs-fy2026-q3-shareholder-letter:p27:section-1 |
| claim:ev5 | FCFはプラスで営業CFも十分大きい (155,615,000 USD) | 実績free_cash_flowは155,615,000 USD、営業CFは198,016,000 USD、capexは42,401,000 USDで、P&L面から見た現金創出は健全。前年同期のFCF 138,918,000 USDからも上向いている。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | supporting | metric:ZS:2026Q3:free_cash_flow:derived / free_cash_flow |
| claim:e1 | Q3のOCFは198.0M USDで黒字を維持した。 (198,016,000 USD) | 計算済み指標で、2026Q3 actual の operating_cash_flow は 198.016M USD。FCF改善の基礎となる営業キャッシュ創出は維持されている。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | not_used | financial_api:ZS:2026Q3:sec:0001713683:operating_cash_flow / operating_cash_flow |
| claim:e2 | Q3のFCFは155.6M USDで、前四半期と前年同期の両方を上回る水準ではないが、前年同期比では改善した。 (155,615,000 USD) | 計算済み指標で、actual free_cash_flow は155.615M USD、previous_quarter は186.318M USD、year_ago_quarter は138.918M USD。短期の勢いは鈍化したが、前年差では改善している。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | not_used | metric:ZS:2026Q3:free_cash_flow:derived / free_cash_flow |
| claim:e3 | CapExは42.4M USDで、Q3のFCFを圧迫しつつも現時点では管理可能な水準だった。 (-42,401,000 USD) | 2026Q3 actual の capex は -42.401M USD。会社説明でもQ3のcapexは売上の5%とされており、FCF算定上の投資負担は存在するが、現時点ではOCFを大きく上回る投資ではない。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | not_used | financial_api:ZS:2026Q3:sec:0001713683:capex / capex |
| claim:e4 | 会社はQ4にCapExが高まり、FY26通期でも高シングルディジット対売上比率になると説明している。 | 会社側テキストで、データセンター機器とZero Trust Branch appliancesの投資を前倒しし、Q4に高いCapExを見込むと明示。さらにFY27ではCapEx比率がFY26より最大200bp上昇する可能性が示され、将来FCFの押し下げ要因として重要。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p18:section-1 / zs-fy2026-q3-shareholder-letter:p18:section-1 |
| claim:e5 | 期末現金等は3.5B USD、負債は1.7B USDで、現時点の流動性は厚い。 | 会社説明では期末にcash, cash equivalents, and short-term investments が3.5B USD、debt が1.7B USD。短期的な資金繰り制約は強く示されていない。 | EPSの足元は強いです。実績EPSは1.08 USD/shareでコンセンサス1.01を上回り、売上も前年同期比25%増、non-GAAP営業利益率23.0%と粗利率81%が利益面を支えています。一方でGAAP EPSは(0.09)で赤字であり、営業リーダー交代に伴う移行期リスクも会社自身が認めています。よって、短期は改善基調ですが、質の面を含めると方向はmixedです。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p18:section-1 / zs-fy2026-q3-shareholder-letter:p18:section-1 |
| claim:ce1 | EPSは調整後ベースで、GAAP利益は赤字だった (-0.09 USD/share) | AppendixではGAAP net income lossが(13.883)百万USD、GAAP EPSが(0.09)である一方、non-GAAP EPSは1.08。headline EPSの質は調整項目の影響を受けている。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | counter_evidence | zs-fy2026-q3-shareholder-letter:p28:section-1 / zs-fy2026-q3-shareholder-letter:p28:section-1 |
| claim:ce2 | 今後はcapex増加でFCFが圧迫される可能性がある | 会社は、メモリ・ストレージ・プロセッサ価格上昇への対応としてQ4に投資を前倒しし、FY2026 capexは売上高比の高い1桁台に上昇すると説明した。さらにFY2027はFY2026比でcapex比率が最大200bp上昇する見通しを示しており、将来FCFには逆風。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | counter_evidence | zs-fy2026-q3-shareholder-letter:p18:section-1 / zs-fy2026-q3-shareholder-letter:p18:section-1 |
| claim:ce3 | ガイダンスは人事移行リスクを織り込んでいる | Q4および通期ガイダンスについて、期末に2名の営業リーダーが退任したため、会社は慎重なアプローチを取っていると明示した。これは継続的な売上成長の見通しに対する執行リスクを示す。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | counter_evidence | zs-fy2026-q3-shareholder-letter:p19:section-1 / zs-fy2026-q3-shareholder-letter:p19:section-1 |
| claim:c1 | FCFマージンは前年16.0%で、会社は回収タイミングの影響を明示している。 | 会社はQ3のfree cash flow margin が16.0%で、前年の18.0%から低下したと説明し、その理由として cash collections の timing を挙げている。これはFCFの質が一部タイミング要因に左右されていることを示す。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p18:section-1 / zs-fy2026-q3-shareholder-letter:p18:section-1 |
| claim:c2 | 会社はFCF計算上、今後のCapEx上昇を明示しており、近い将来のFCF拡大を抑える可能性がある。 | Q4の高CapEx見込みに加え、FY27ではCapEx as a percentage of revenue がFY26比で最大200bp上昇する可能性が示されている。FCFはOCFから投資を差し引くため、この増加はFCF拡大に逆風。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p19:section-1 / zs-fy2026-q3-shareholder-letter:p19:section-1 |
| claim:c3 | Q3のFCFマージン低下は回収タイミング要因と説明され、短期の変動余地がある (155,615,000 USD) | Q3のFCFマージンは16%で、前年18%から低下したと説明され、その要因としてcash collectionsのtimingが挙げられた。FCFの短期変動が営業成績以外の要因にも左右されることを示す。 | FCFは当四半期155.615M USDで黒字を維持し、前年同期比では改善していますが、前四半期比では低下しました。会社自身がcash collectionsのtimingによる変動を説明し、Q4のCapEx前倒しとFY27のCapEx比率上昇を明示しているため、近い将来のFCF拡大は押し下げられやすいです。流動性は厚いものの、FCFトレンドは強さと逆風が併存しており mixed です。 | 2026Q3 | supported | not_used | zs-fy2026-q3-shareholder-letter:p18:section-1 / zs-fy2026-q3-shareholder-letter:p18:section-1 |

## データ品質

- 入力プロファイル: yfinance_sec_presentation_tagged
- 期間検証: partial
- metric conflict: none
- guidance delta: company_guidance_missing
- presentation tag coverage: guidance=no, management=no, cash_flow=yes, risk=no
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
- ManagementIntentAnalyst: counter_evidenceは十分に確認できたため主要論点の判定は可能ですが、guidance数値の詳細比較は本ロールの対象外のため、見通しの強弱は定量的には深掘りしていません。
- GuidanceAnalyst: 会社のguidance本文に対応する precomputed guidance deltas が提供されていないため、guidance vs consensus を定量評価できません。
- GuidanceAnalyst: Q4/FY26の revenue / EPS / FCF guidance に対応する consensus estimate が routed_context にありません。
- GuidanceAnalyst: required canonical metric の欠損はありませんが、guidance の妥当性をより厳密に比較するための guidance_consensus_deltas が必要です。

### 未解決の問い
- GAAPベースでの利益回復が続くかは、現時点では非GAAP調整の持続性次第です。
- CapEx前倒しが一時的なものか、FY27以降も高水準で続くかは未確定です。
- 営業組織の移行が売上成長とEPS達成に与える影響はまだ見極め段階です。
- cash collectionsのタイミング要因が来四半期以降に正常化するかは不明です。

## 品質ゲート (Quality Gates)

- ReportMatrix検証: passed
- source_manifest entries: 52
- 根拠項目: 16
- claim records: 16
- decision uses: 16
- 不足データ項目: 0
- data quality flags: 17
- fact-check statuses: supported: 16
- judge treatments: counter_evidence: 3, not_used: 10, supporting: 3
- source_ref整合性: 登録済みsource_manifestと内部整合
- no-advice framing: 免責事項に明記

## ソース付録 (Source Appendix)

| Source ID | Type | Locator | Title | Reported period | URL |
|---|---|---|---|---|---|
| `financial_api:ZS:2026Q3:sec:0001713683:revenue` | financial_api | revenue | SEC Company Facts RevenueFromContractWithCustomerExcludingAssessedTax period_role=actual method=direct_quarter form=10-Q end=2026-04-30 accn=0001713683-26-000096 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:operating_cash_flow` | financial_api | operating_cash_flow | SEC Company Facts NetCashProvidedByUsedInOperatingActivities period_role=actual method=ytd_difference form=10-Q end=2026-04-30 accn=0001713683-26-000096 prior_end=2026-01-31 prior_accn=0001713683-26-000048 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:capex` | financial_api | capex | SEC Company Facts PaymentsToAcquirePropertyPlantAndEquipment period_role=actual method=ytd_difference form=10-Q end=2026-04-30 accn=0001713683-26-000096 prior_end=2026-01-31 prior_accn=0001713683-26-000048 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:yf:eps` | financial_api | eps | yfinance verified-period metric | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:yf:consensus:eps_consensus` | financial_api | eps_consensus | yfinance verified-period metric | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:yf:pq:eps` | financial_api | eps | yfinance verified-period metric | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:yf:ya:eps` | financial_api | eps | yfinance verified-period metric | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:pq:revenue` | financial_api | revenue | SEC Company Facts RevenueFromContractWithCustomerExcludingAssessedTax period_role=previous_quarter method=direct_quarter form=10-Q end=2026-01-31 accn=0001713683-26-000048 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:pq:operating_cash_flow` | financial_api | operating_cash_flow | SEC Company Facts NetCashProvidedByUsedInOperatingActivities period_role=previous_quarter method=ytd_difference form=10-Q end=2026-01-31 accn=0001713683-26-000048 prior_end=2025-10-31 prior_accn=0001713683-25-000205 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:pq:capex` | financial_api | capex | SEC Company Facts PaymentsToAcquirePropertyPlantAndEquipment period_role=previous_quarter method=ytd_difference form=10-Q end=2026-01-31 accn=0001713683-26-000048 prior_end=2025-10-31 prior_accn=0001713683-25-000205 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:ya:revenue` | financial_api | revenue | SEC Company Facts RevenueFromContractWithCustomerExcludingAssessedTax period_role=year_ago_quarter method=direct_quarter form=10-Q end=2025-04-30 accn=0001713683-26-000096 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:ya:operating_cash_flow` | financial_api | operating_cash_flow | SEC Company Facts NetCashProvidedByUsedInOperatingActivities period_role=year_ago_quarter method=ytd_difference form=10-Q end=2025-04-30 accn=0001713683-26-000096 prior_end=2025-01-31 prior_accn=0001713683-26-000048 | 2026Q3 | no URL |
| `financial_api:ZS:2026Q3:sec:0001713683:ya:capex` | financial_api | capex | SEC Company Facts PaymentsToAcquirePropertyPlantAndEquipment period_role=year_ago_quarter method=ytd_difference form=10-Q end=2025-04-30 accn=0001713683-26-000096 prior_end=2025-01-31 prior_accn=0001713683-26-000048 | 2026Q3 | no URL |
| `metric:ZS:2026Q3:free_cash_flow:derived` | derived_metric | free_cash_flow | Derived free cash flow | 2026Q3 | no URL |
| `metric:ZS:2026Q3:previous_quarter:free_cash_flow:derived` | derived_metric | free_cash_flow | Derived free cash flow | 2026Q3 | no URL |
| `metric:ZS:2026Q3:year_ago_quarter:free_cash_flow:derived` | derived_metric | free_cash_flow | Derived free cash flow | 2026Q3 | no URL |
| `zs-fy2026-q3-shareholder-letter:p1:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p1:section-1, page 1 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p2:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p2:section-1, page 2 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p3:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p3:section-1, page 3 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p4:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p4:section-1, page 4 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p5:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p5:section-1, page 5 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p6:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p6:section-1, page 6 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p7:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p7:section-1, page 7 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p8:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p8:section-1, page 8 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p9:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p9:section-1, page 9 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p10:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p10:section-1, page 10 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p11:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p11:section-1, page 11 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p12:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p12:section-1, page 12 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p13:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p13:section-1, page 13 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p14:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p14:section-1, page 14 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p15:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p15:section-1, page 15 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p16:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p16:section-1, page 16 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p17:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p17:section-1, page 17 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p18:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p18:section-1, page 18 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p19:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p19:section-1, page 19 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p20:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p20:section-1, page 20 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p21:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p21:section-1, page 21 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p22:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p22:section-1, page 22 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p23:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p23:section-1, page 23 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p24:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p24:section-1, page 24 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p25:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p25:section-1, page 25 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p26:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p26:section-1, page 26 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p27:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p27:section-1, page 27 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p28:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p28:section-1, page 28 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p29:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p29:section-1, page 29 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p30:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p30:section-1, page 30 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p31:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p31:section-1, page 31 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p32:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p32:section-1, page 32 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p33:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p33:section-1, page 33 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p34:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p34:section-1, page 34 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p35:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p35:section-1, page 35 | ZS FY2026 Q3 shareholder letter | - | no URL |
| `zs-fy2026-q3-shareholder-letter:p36:section-1` | earnings_presentation | zs-fy2026-q3-shareholder-letter, zs-fy2026-q3-shareholder-letter:p36:section-1, page 36 | ZS FY2026 Q3 shareholder letter | - | no URL |

## 免責事項

本レポートは決算分析のための成果物であり、投資助言ではありません。特定の取引判断や価格水準の提示を目的とするものではありません。