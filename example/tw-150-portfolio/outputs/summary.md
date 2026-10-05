# 文獻蒐集總結

## 本次設定

- **短名單篇數 (n)**: 60
- **期刊數 (m)**: 20
- **短名單模式**: global
- **出版年份**: 2005 - 2026
- **評分訊號**: coupling, tfidf, specter
- **關鍵詞**: machine learning asset pricing; machine learning stock return prediction; cross-section of expected returns; factor exposure; low volatility anomaly; betting against beta; characteristics and covariances; anomaly return predictability; limits to arbitrage; transaction costs portfolio choice; dynamic trading transaction costs; portfolio turnover; predict then optimize; end-to-end portfolio optimization; differentiable optimization; implementable efficient frontier; deep learning portfolio; autoencoder asset pricing; deep learning asset pricing; self-supervised learning time series; transformer stock prediction; complexity return prediction; representation learning financial time series; reinforcement learning trading; reinforcement learning portfolio management; deep hedging; optimal execution; backtest overfitting

## 數量漏斗

| 階段 | 數量 |
|---|---|
| 主要文件 | 1 |
| 種子文獻（解析出 DOI／去重後） | 21 / 24 |
| 查詢次數（關鍵詞 × 期刊） | 560 |
| 檢索命中 | 9157 |
| 不重複文章 | 5785 |
| 排除：書評等非研究論文 | 29 |
| 排除：標題重複 | 35 |
| 排除：本身是種子／已在 Zotero | 17 / 0 |
| 進入評分 | 5704 |
| agent 細讀 | 180 |
| all-relevant-articles.xlsx | 1131 |
| 短名單 | 60 |
| 引文回溯：候選／列出 | 328 / 30 |

## 各期刊結果

| 期刊 | 候選 | 過門檻 | agent 判定相關 | 短名單 |
|---|---|---|---|---|
| Review of Financial Studies | 286 | 88 | 13 | 9 |
| Management Science | 378 | 85 | 14 | 8 |
| Journal of Portfolio Management | 335 | 87 | 10 | 6 |
| Journal of Empirical Finance | 273 | 83 | 6 | 5 |
| Journal of Financial Economics | 301 | 71 | 6 | 4 |
| Journal of Finance | 258 | 58 | 5 | 4 |
| Quantitative Finance | 352 | 77 | 5 | 4 |
| Financial Analysts Journal | 219 | 63 | 4 | 4 |
| Journal of Financial and Quantitative Analysis | 263 | 83 | 6 | 3 |
| Journal of Financial Data Science | 145 | 54 | 5 | 3 |
| Journal of Banking & Finance | 376 | 82 | 4 | 3 |
| Pacific-Basin Finance Journal | 296 | 56 | 5 | 1 |
| Journal of Financial Econometrics | 203 | 55 | 4 | 1 |
| Journal of Econometrics | 277 | 48 | 3 | 1 |
| Review of Finance | 208 | 40 | 3 | 1 |
| Expert Systems with Applications | 460 | 34 | 1 | 1 |
| Mathematical Finance | 218 | 26 | 1 | 1 |
| Operations Research | 295 | 17 | 1 | 1 |
| IEEE Transactions on Neural Networks and Learning Systems | 365 | 6 | 0 | 0 |
| SIAM Journal on Financial Mathematics | 196 | 18 | 0 | 0 |

## 主題分布（短名單）

| 主題 | 數量 |
|---|---|
| A 低波動與低beta異象 | 16 |
| B 交易成本與換手 | 12 |
| A 機器學習與已知因子 | 10 |
| B 決策導向與端到端學習 | 8 |
| A 異象、套利限制與因子動物園 | 7 |
| G 強化學習交易與配置 | 3 |
| 驗證與回測過度配適 | 2 |
| F 時間序列表示學習 | 1 |
| F 深度學習資產定價 | 1 |

## 最相關的文章

1. **Machine Learning and the Implementable Efficient Frontier** — Jensen, Theis Ingerslev; Kelly, Bryan; Malamud, Semyon; Pedersen, Lasse Heje (2026), *Review of Financial Studies*. 理由: 直接以經濟目標學習投組權重並納入交易成本，提出可實行效率前緣與經濟特徵重要性，正是方向B解釋v1扣成本後失效、用成本感知學習取代手寫緩衝規則的核心文獻。
2. **Deep Parametric Portfolio Policies** — Simon, Frederik; Weibels, Sebastian; Zimmermann, Tom (2026), *Management Science*. 理由: 以深度神經網路直接最佳化投資人效用的參數化投組政策，並檢驗交易成本與放空限制下的穩健性，是方向B以經濟目標取代報酬預測、端到端訓練選股模型的核心文獻。
3. **Smart Trading Rule: A Modular Machine Learning Framework for Portfolio Optimization with Transaction Costs** — Li, Silu; Mulvey, John M.; Fabozzi, Frank J. (2026), *Journal of Financial Data Science*. 理由: 提出含交易成本的模組化機器學習交易規則以學習何時與如何調整持股，正對應方向B以學習取代「前20買、跌出前30賣」手寫緩衝規則的研究目標。
4. **Distributionally robust end-to-end portfolio construction** — Costa, Giorgio; Iyengar, Garud N. (2023), *Quantitative Finance*. 理由: 提出分配穩健的端到端投組建構，將預測與最適化一起訓練，正是方向B把決策目標放進學習過程的核心文獻。
5. **Integrating prediction in mean-variance portfolio optimization** — Butler, Andrew; Kwon, Roy H. (2023), *Quantitative Finance*. 理由: 將預測模型整合進均值變異數最適化並以決策損失訓練（Butler-Kwon），是方向B predict-then-optimize與端到端學習的核心文獻。
6. **Linear Trading Rules for Portfolio Management** — Grinold, Richard (2018), *Journal of Portfolio Management*. 理由: Grinold的線性交易規則以部分調整方式在成本下逐步趨近目標投組，正是方向B中將v1手寫緩衝規則理論化的核心文獻。
7. **Deep Learning Statistical Arbitrage** — Guijarro-Ordonez, Jorge; Pelger, Markus; Zanotti, Greg (2026), *Management Science*. 理由: 以條件潛在因子殘差組合加上卷積Transformer萃取時間序列訊號並直接學習受限制的最適交易策略，是F方向時間序列表示學習與端到端交易結合的核心範例，可對照v1預訓練失敗的原因。
8. **A Taxonomy of Anomalies and Their Trading Costs** — Novy-Marx, Robert; Velikov, Mihail (2015), *Review of Financial Studies*. 理由: 系統性估算各類異象的交易成本並檢驗緩衝區等降換手策略，正是B方向「訊號扣除成本後還剩多少」與v1買前20賣出前30緩衝規則的核心文獻。
9. **Technical Note—A Robust Perspective on Transaction Costs in Portfolio Optimization** — Olivares-Nadal, Alba V.; DeMiguel, Victor (2018), *Operations Research*. 理由: 證明交易成本等價於正則化並提出以資料校準成本懲罰項的投資組合方法，是B方向將換手懲罰納入學習目標的核心文獻。
10. **Dynamic Portfolio Choice with Intertemporal Hedging and Transaction Costs** — Muhle-Karbe, Johannes; Sefton, James; Shi, Xiaofei (2026), *Management Science*. 理由: 推廣Garleanu-Pedersen部分調整框架，說明在可預測報酬與交易成本下以固定速度追蹤目標組合，是B方向設計成本感知調倉規則的核心理論。
11. **Does It Pay to Bet Against Beta? On the Conditional Performance of the Beta Anomaly** — CEDERBURG, SCOTT; O'DOHERTY, MICHAEL S. (2016), *Journal of Finance*. 理由: 指出 BAB 策略的條件 beta 隨市場波動變化、條件 CAPM 可解釋 beta 異象，直接有助於方向 A 理解 v1 在 2025 年因低波動傾斜失效的時變風險來源。
12. **New Methods for the Cross-Section of Returns** — Karolyi, G Andrew; Van Nieuwerburgh, Stijn (2020), *Review of Financial Studies*. 理由: RFS特刊導論綜述因子動物園、錯誤發現與機器學習萃取SDF的新方法，可作為方向A檢驗ML訊號是否只是已知因子及多重檢定問題的總覽入口。
13. **Rethinking Variable Importance in Machine Learning: An Economic Perspective on Empirical Asset Pricing** — Jo, Yonghwan; Kim, Yong Hwi (2026), *Financial Analysts Journal*. 理由: 從經濟角度重新定義機器學習資產定價模型的變數重要性，可直接用於方向A拆解v1模型究竟學到哪些特徵（如波動度、動能）而非僅看統計重要性。
14. **An Overview of Machine Learning for Portfolio Optimization** — Lee, Yongjae; Kim, Jang Ho; Kim, Woo Chang; Fabozzi, Frank J. (2024), *Journal of Portfolio Management*. 理由: 綜述機器學習在投組最佳化的應用（含端到端與強化學習），可作為方向B與方向G文獻地圖的直接入口。
15. **Cross-sectional expected returns: new Fama–MacBeth regressions in the era of machine learning** — Han, Yufeng; He, Ai; Rapach, David E; Zhou, Guofu (2024), *Review of Finance*. 理由: 將Fama-MacBeth迴歸結合正則化與預測組合來做橫斷面報酬預測並提供特徵報酬估計，可在方向A作為可解釋的基準模型，用以比較v1的ML訊號是否超越線性已知特徵。

## 引文回溯：期刊檢索以外的重要文獻

1. **Dynamic portfolio choice with frictions** — Gârleanu, Nicolae; Pedersen, Lasse Heje (2016). 被 3 個來源引用. 推廣 Garleanu-Pedersen 部分調整至一般摩擦下的動態組合，直接為方向 B 將交易成本納入選股決策、取代手寫緩衝規則提供理論核心。
2. **Studies in the Theory of Capital Markets** — Black Fischer (1972). 被 7 個來源引用. 收錄 Black-Jensen-Scholes 對 CAPM 的實證檢驗，記錄低 beta 股票報酬過高的平坦證券市場線，是方向 A 判斷 v1 低波動傾斜來源的低 beta 異象原點文獻。
3. **On Persistence in Mutual Fund Performance** — Carhart, Mark M. (1997). 被 18 個來源引用. 提出含動能的四因子模型，可直接用於方向 A 將 ML 選股報酬對市場、規模、價值、動能因子回歸，檢驗訊號是否為新資訊。
4. **Replicating Anomalies** — Hou, Kewei; Xue, Chen; Zhang, Lu (2018). 被 7 個來源引用. 以 452 個異象顯示多數在微型股處理與多重檢定門檻下失效，且交易摩擦類異象幾乎全滅，支持方向 A 關於異象衰減與難交易股票的論點。
5. **Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency** — JEGADEESH, NARASIMHAN; TITMAN, SHERIDAN (1993). 被 10 個來源引用. 動能效應的原始文獻，方向 A 需以此判斷價量 ML 模型學到的是否只是 3-12 個月動能。
6. **Portfolio Selection with Transaction Costs** — Davis, M. H. A.; Norman, A. R. (1990). 被 8 個來源引用. 證明比例交易成本下最適策略為「不交易區間」，正好為 v1 手寫緩衝規則（前 20 買、跌出 30 賣）提供方向 B 的理論依據。
7. **The capital asset pricing model: Some empirical tests** — Black (1972). 被 4 個來源引用. Black-Jensen-Scholes 實證發現低 beta 股票 alpha 為正，是方向 A 解釋 v1 隱性低波動傾斜的低 beta 異象基礎證據。
8. **Forest through the Trees: Building Cross‐Sections of Stock Returns** — BRYZGALOVA, SVETLANA; PELGER, MARKUS; ZHU, JASON (2025). 被 3 個來源引用. 以決策樹依 SDF 建構可解釋且樣本外 Sharpe 較高的橫斷面組合，並與 ML 預測組合比較，可為方向 A/F 檢視 ML 學到的特徵交互作用提供方法。
9. **Common risk factors in the returns on stocks and bonds** — Fama, Eugene F.; French, Kenneth R. (1993). 被 35 個來源引用. Fama-French 三因子模型，是方向 A 將 ML 選股報酬分解為市場、規模、價值暴露的標準基準。
10. **The Cross‐Section of Expected Stock Returns** — FAMA, EUGENE F.; FRENCH, KENNETH R. (1992). 被 15 個來源引用. 證明規模與淨值市價比主導橫斷面報酬且 beta 與報酬關係平坦，同時支持方向 A 的已知因子基準與低 beta 異象背景。

## 資料品質提醒

- 34% 的文章有摘要；沒有摘要的文章在自己的群組內排名，以免被系統性低估。
- 91% 的文章有公開的參考文獻清單；其餘的引文訊號是「缺少」而非 0。
- 515 篇文章至少引用一篇種子文獻。
- 種子文獻解析出 DOI：21 / 24；其中有參考文獻清單的：17。
- 檢核：檢索本身找回了 17 篇種子文獻，其中 82% 排在門檻之上。
- 4 個被引用的 DOI 不在 Crossref，未列入引文回溯。
- Crossref 幾乎不收錄中文文獻；如有需要請另外檢索。

## 分析

### 整體觀察

四個方向的文獻厚度差很多。方向 A（因子曝險）與 B（成本感知學習）在財務期刊裡有大量直接相關的研究：短名單 60 篇中，A 占 33 篇、B 占 20 篇。F（表示學習）與 G（強化學習）合計只有 5 篇。這不是因為這兩個方向不重要，而是它們的主要文獻發表在機器學習會議（NeurIPS、ICML、ICLR、AAAI、KDD），不在這次檢索的期刊清單裡，而且 Crossref 幾乎不收錄會議論文。IEEE TNNLS 與 Expert Systems with Applications 雖然有很多命中，但多是一般的股價預測應用，細讀後幾乎都判為無關（各期刊表最後兩列）。

另一個觀察是，最相關的文章很新：前 15 篇中有 7 篇是 2024–2026 年發表的。「ML 選股扣成本後還剩多少」正是近兩三年頂尖期刊的熱門題目，這對研究計畫是好消息，但也代表要定期補檢索。

### 與研究方向特別相關的文章群

- **B 的核心已經成形**：Jensen、Kelly、Malamud 與 Pedersen 的 *Implementable Efficient Frontier* 已在 RFS 正式刊出（研究計畫中仍列為 SSRN 工作論文，應更新引用）。它和 Simon 等的 *Deep Parametric Portfolio Policies*、Li–Mulvey–Fabozzi 的 *Smart Trading Rule* 都是「直接以扣成本後的經濟目標訓練投組權重」，正是方向 B 要做的事。這三篇應作為方向 B 的直接比較對象，研究計畫需要說清楚台股、月頻、小樣本的設定和它們差在哪裡。
- **v1 的緩衝規則有完整的理論譜系**：Davis–Norman（1990）、Dumas–Luciano（1991）、Liu（2004）的「不交易區間」，Gârleanu–Pedersen（2013、2016）的部分調整，Grinold（2018）的線性與非線性交易規則，以及 Moallemi–Sağlam（2017）的線性再平衡規則。v1「前 20 買、跌出前 30 賣」可以直接寫成不交易區間的一個特例，這讓方向 B／G 有現成的理論最佳解可以對照。
- **A 的低波動機制**：Cederburg–O'Doherty（2016）的條件 beta、Oderda 等的 beta 套利何時有效（2015）、Li–Sullivan–Garcia-Feijóo 與 Bali 等的低波動、彩券型需求研究，可以解釋 v1 為什麼在 2025 年高波動股反彈時失效。Novy-Marx–Velikov（2015）同時連結了 A 與 B：異象扣成本後還剩多少，以及緩衝區如何降低成本。
- **A 的方法工具**：Han 等（2024）的機器學習時代 Fama–MacBeth、Jo–Kim（2026）的經濟變數重要性、Lettau–Pelger（2020）與 Daniel 等（2020）的因子建構、Kozak–Nagel–Santosh（2020）的 shrinking the cross-section。這些可以直接用來做方向 A 的第一步：把模型分數對已知因子迴歸，看剩下多少。
- **驗證**：Soebhag 等（2024）的非標準誤差、Hou–Xue–Zhang（2018）的異象複製、Jensen–Kelly–Pedersen（2023）的複製危機，支持 v1 事前登錄與封存驗證的做法，可以寫進方法論章節。

### 這次檢索沒有涵蓋的缺口與補救建議

1. **F 與 G 的會議論文**：PatchTST、TS2Vec、MASTER 等種子文獻本身就是會議論文；相關的後續研究（金融時間序列基礎模型、股票關係圖模型、DRL 投組管理）建議用 Semantic Scholar 或 Google Scholar 另外檢索，關鍵詞如 "financial time series foundation model"、"stock relation graph neural network"、"deep reinforcement learning portfolio benchmark"，並以 NeurIPS／ICAIF（ACM International Conference on AI in Finance）為主。
2. **強化學習的下單執行與避險**：只有 Almgren–Chriss 的最適執行由引文回溯找到。方向 G 的「從答案已知的問題開始」需要 Almgren–Chriss、Ning 等的 DRL 最適執行與 Kolm–Ritter 系列；建議把 *Journal of Financial Data Science* 的 RL 專刊與 *Applied Mathematical Finance* 加入期刊清單後重跑步驟 6。
3. **台灣與新興市場**：Pacific-Basin Finance Journal 只有 1 篇進短名單，台股的低波動與 ML 選股實證幾乎沒有找到。中文文獻（如《證券市場發展季刊》、《管理學報》）Crossref 不收錄，需用華藝或 TEJ 文獻庫另外檢索。
4. **工作論文**：本領域很多最新成果先出現在 SSRN／NBER。例如 Kelly 等的 *AI asset pricing*、Jensen 等的後續研究，建議定期到 SSRN 追蹤種子作者的新作。
5. **引文回溯的重複條目**：引文回溯分頁中的 *Studies in the Theory of Capital Markets* 與 *The capital asset pricing model: Some empirical tests* 是同一篇 Black–Jensen–Scholes（1972）研究的書與專章兩種著錄，匯入 Zotero 後建議用「合併重複項目」清理。
