# 弱訊號與交易成本下的機器學習選股：四個研究方向的文獻回顧

> 本文為 tw-150-portfolio 研究所研究計畫的文獻回顧，涵蓋計畫中的四個方向：A 因子曝險、B 成本感知學習、F 表示學習、G 強化學習。
>
> **文獻來源**：主體是本專案以 lit-review skill 蒐集並保留的 78 篇（見 `zotero-import.ris`），加上研究計畫原有的 24 篇種子文獻。F、G 兩個方向的主要文獻發表在機器學習會議，期刊檢索涵蓋不足，因此另以網路檢索補充並逐筆核對出處。參考文獻中，**＊** 表示種子文獻，**†** 表示網路補充（不在 RIS 檔中），未標記者為本次蒐集所得。
>
> 撰寫：Claude Opus 5.5，2026-10-05。

---

## 一、問題的提出

v1 專案用台灣 50 與中型 100 成分股的月頻價量資料訓練選股模型，留下三個值得追問的現象：

1. 不計成本時，模型勝過簡單規則；扣成本後反而落後，原因是換手太高。
2. 2025 年的失敗，來自一個開發期沒有察覺的低波動與防禦類股傾斜。
3. 自監督預訓練沒有任何增量。全研究最有效的改善，反而是一條手寫的緩衝換股規則：「進前 20 才買、跌出前 30 才賣」。

這三個現象可以歸結成同一個問題：**在訊號很弱、交易成本不可忽略的市場裡，機器學習選股模型到底學到了什麼？其中有多少是新東西？扣掉成本後還剩多少？** 四個方向從不同的面向回答這個問題：

| 方向 | 對應的 v1 現象 | 核心文獻群 |
|---|---|---|
| A 因子曝險 | 未察覺的低波動傾斜 | ML 資產定價、因子歸因、低波動異象、異象衰退 |
| B 成本感知學習 | 扣成本後落後 | 不交易區間理論、異象的交易成本、決策導向學習 |
| F 表示學習 | 預訓練無效 | 經濟結構化深度模型、複雜度、時間序列基礎模型 |
| G 強化學習 | 手寫緩衝規則最有效 | 直接強化學習、最適執行、學習不交易區間 |

以下各節先整理文獻的發現，再說明它對本計畫的意涵與尚未回答的問題。

---

## 二、方向 A：模型學到的是新東西，還是已知因子？

### 2.1 機器學習選股學到了什麼

Gu、Kelly 與 Xiu（2020）＊的研究是這個領域的基準。在美股，樹模型與神經網路預測個股報酬的能力明顯優於線性模型，增益來自預測變數之間的非線性交互作用；然而各種方法都認同的少數主導訊號是動能、流動性與波動度，大多屬於已知的因子類別。換言之，ML 的貢獻比較像是「更有效地組合已知特徵」，而不是「發現新特徵」。

後續研究從三個角度削弱了 ML 選股的表面成績：

- **獲利集中在難交易的股票。** Avramov、Cheng 與 Metzker（2023）＊發現，深度學習訊號的獲利主要來自難套利的股票與套利限制高的時期；排除微型股、財務困境股或市場高波動期間後，獲利大幅縮小，再加上合理的交易成本，因為換手高、部位極端而進一步惡化。Jo 與 Kim（2026）同樣指出，傳統的 ML 模型由微型股主導，報酬被成本高昂的股票灌水，樣本內的變數重要性也會過度配適。
- **獲利隨期限、規模與時間而異。** Cakici、Fieberg、Metko 與 Zaremba（2023）發現 ML 預測只在短期、小型公司與較早的樣本期有效；過去二十年，年度預測在美股多數區塊沒有實質的經濟增益。Brogaard 與 Zareei（2022）以多種 ML 演算法從過去價格尋找技術交易規則，發現確實找得到獲利的規則，但樣本外獲利隨時間遞減。
- **重要的特徵很少。** Fallahgoul、Franstianto 與 Lin（2024）為神經網路資產定價模型建立變數顯著性檢定，結果只有少數個股特徵顯著，總體經濟變數在 1% 水準下全部不顯著，且跨網路結構一致。

這些發現對方向 A 很重要：v1 只用價量資料，其訊號在大中型股、月頻、扣成本的條件下仍有約 0.04–0.08 的 Rank IC。合理的推測是它也主要來自動能、反轉、波動與流動性這幾類已知特徵，而這正是需要被量化檢驗的部分。

### 2.2 已知因子的基準與歸因方法

要判斷 ML 訊號「新不新」，需要一組基準因子與一套歸因方法。

**因子基準。** 經典的規模與價值（Fama & French, 1992, 1993）、動能（Jegadeesh & Titman, 1993；Carhart, 1997）以及獲利與投資因子（Fama & French, 2015）構成標準的時間序列迴歸基準；Fama 與 French（1996）示範了用因子迴歸解釋異象的做法，Gibbons、Ross 與 Shanken（1989）的 GRS 檢定則可聯合檢驗一組組合的 alpha 是否為零。Lewellen（2015）以 Fama–MacBeth 迴歸結合多個特徵產生樣本外預測，Han、He、Rapach 與 Zhou（2024）再把它擴充為加入正則化、變數選擇與預測組合的版本。這兩者是衡量「非線性 ML 比簡單線性組合多出多少」的合適對照。

**潛在因子與風險歸因。** Kelly、Pruitt 與 Su（2019）＊的 IPCA 主張個股特徵之所以能預測報酬，主要是因為它們反映了對少數風險因子的曝險。Lettau 與 Pelger（2020）的 RP-PCA 在主成分分析中加入定價誤差懲罰，能找出 PCA 偵測不到的弱因子。Kim、Korajczyk 與 Neuhierl（2020）的套利組合方法在歸因時先盡量以風險解釋特徵的預測力，剩下的才算作異常報酬，這正是方向 A 需要的「保守歸因」。Daniel、Mota、Rottke 與 Santos（2020）則指出特徵排序組合同時帶有未定價的風險，並提出用歷史共變異數去除它的方法。這可以直接用來清除 v1 組合中非意圖的產業與波動曝險。

**主動與被動成分的拆解。** Irvine、Kim 與 Ren（2024）在基金績效中辨識出與 beta 異象相關的被動成分，並將其餘部分定義為主動 alpha；他們發現標準的四因子模型、甚至加入 BAB 因子都無法完全吸收 beta 異象。這個拆解方法可以移植到 ML 選股：把模型分數中可由低 beta 與低波動解釋的部分分離出來。

### 2.3 低波動與低 beta 異象

v1 在 2025 年失敗的直接原因是低波動傾斜，因此這一支文獻是方向 A 的重心。

**起源與解釋。** Black（1972）的受限借貸 CAPM 與 Black、Jensen 與 Scholes（1972）的實證，最早記錄了證券市場線過於平坦、低 beta 股票報酬偏高的現象。Haugen 與 Baker（1996）以大量特徵預測個股報酬，同樣發現低風險股票報酬較高，可以看作「多特徵選股模型會自然帶上低波動傾斜」的早期例證。對此現象的主流解釋有兩類：一是槓桿限制，Frazzini 與 Pedersen（2014）＊認為不能或不願使用槓桿的投資人會追逐高 beta 股票；二是以大盤為基準的委託代理問題，Baker、Bradley 與 Wurgler（2011）＊指出這使得機構投資人無法套利低波動異象。另外還有彩券偏好：Bali、Cakici 與 Whitelaw（2011）的 MAX 效應顯示投資人偏好具極端正報酬的股票，與特異波動度異象密切相關。

**它是風險還是錯誤定價？** Li、Sullivan 與 Garcia-Feijóo（2016）以 1966–2011 年資料檢驗，認為低波動組合的高報酬不能以系統性因子風險解釋，比較可能是與波動度特徵相關的錯誤定價。Blitz 與 Vidojevic（2017）反駁「五因子模型（含獲利因子）可以解釋低風險異象」的說法；Blitz（2016）則發現價值因子雖能解釋 1963 年以後美股的低波動報酬，卻無法解釋其他時期與小型股，低波動效應在所有子樣本中都存在。

**它能不能被交易？** Li、Sullivan 與 Garcia-Feijóo（2014）發現，低波動異象在等權多空組合中不存在；在市值加權組合中，排除股價低於 5 美元的股票後，alpha 大致消失。剩下的超額報酬集中在流動性差的小型股，反轉快、需要頻繁調整，高交易成本使其難以實現。Cao 與 Han（2016）則從套利成本的角度說明特異波動度與報酬的關係：被低估的股票報酬隨特異風險上升，被高估的則下降。

**它何時會反轉？** 這一點與 v1 最直接相關。Cederburg 與 O'Doherty（2016）發現高減低 beta 組合的條件 beta 與股權溢酬負相關、與市場波動正相關，因此無條件 alpha 會低估真實的 alpha，條件 CAPM 能解釋大部分的 beta 異象。Barroso、Detzel 與 Maio（2025）則發現，BAB 因子的超額報酬在實現波動低於中位數的月份之後較高，而且這個時變模式無法被錯誤定價、套利限制、彩券偏好、分析師意見分歧或情緒等主流理論解釋。Oderda、Berrada、Messikh 與 Pictet（2015）從市場多樣性的角度說明 beta 套利策略為何在機制上會勝過市值組合。這些研究共同意味著：低波動傾斜的報酬具有明顯的時變性，在市場急漲或高波動股反彈時會集中付出代價，這正是 v1 在 2025 年遭遇的情況。

**台灣的證據。** Hsu、Wei 與 Chen（2020）†以馬可夫狀態轉換模型分析台股，發現低波動異象在資金流動性風險高時最強，在流動性風險低時則顯著反轉，機制是機構對高波動股的賣壓。Lin 與 Lin（2021）†發現台股散戶的賭博偏好使高特異偏態股票被高估、未來報酬為負，且在市場下跌與套利受限時更明顯。這兩篇提供了台股低波動傾斜「何時有利、何時不利」的在地證據，可以用來檢驗 v1 在 2025 年的失敗是否落在可預期的狀態中。

**估計工具。** Drobetz、Hollstein、Otto 與 Prokopczuk（2024）以 ML 估計個股的時變 beta，預測與避險誤差最低，並能改善市場中性與最小變異數組合；Bali、Engle 與 Tang（2017）的動態條件 beta 則顯示 beta 與日報酬的橫斷面關係是正的。這兩篇提供了測量並控制 v1 beta 曝險的方法。

### 2.4 異象衰退、資料探勘與可複製性

方向 A 的另一個面向是：即使訊號是「新的」，它能持續多久？McLean 與 Pontiff（2016）＊發現異象在學術發表後報酬明顯下降。Chordia、Subrahmanyam 與 Tong（2014）記錄了高流動性時代異象報酬的衰退，Linnainmaa 與 Roberts（2018）以延伸的歷史樣本檢驗異象的樣本外表現，認為許多異象可能來自資料探勘。Bowles、Reed、Ringgenberg 與 Thornock（2024）則發現異象報酬集中在資訊公開後的第一個月並迅速衰退。

關於可複製性，Hou、Xue 與 Zhang（2018）在控制微型股與提高多重檢定門檻後，發現多數異象無法複製；Harvey、Liu 與 Zhu（2016）＊主張因子的 t 值門檻應提高到 3 以上。Jensen、Kelly 與 Pedersen（2023）則以貝氏方法得出較樂觀的結論：多數因子可以複製，且在 93 個國家的資料中樣本外仍然成立。Kozak、Nagel 與 Santosh（2020）以收縮估計在大量特徵下建構隨機折現因子，處理「因子動物園」的高維問題；Karolyi 與 Van Nieuwerburgh（2020）的 RFS 特刊導論則提供了這一系列新方法的總覽。

### 2.5 方向 A 的小結與研究缺口

文獻的共識相當清楚：ML 選股的訊號大量與已知因子重疊、集中在難交易的股票，且隨時間衰退；低波動傾斜是多特徵模型很容易「不知不覺」帶上的曝險，其報酬具有明顯的狀態相依性。

尚未被充分回答、而本計畫能夠貢獻的問題有三：

1. **非美國、非微型股的證據不足。** 多數研究使用美股全市場且受微型股主導。台股大中型股、月頻、扣成本的設定，恰好是 Avramov 等（2023）與 Jo 與 Kim（2026）所指出「排除難交易股票後還剩多少」的自然實驗。Bui、Kong、Lin 與 Lin（2023）†在台股以 86 個異象訓練神經網路與 PLS，得到每月 1.20–1.50% 的多空報酬，前 20 大預測變數中有 5 個與動能有關。但他們使用的是全市場與多種特徵，與 v1 只用價量、大中型股的設定不同。
2. **「如何在模型設計上控制曝險」的研究很少。** 現有文獻多半是事後歸因，即把報酬對因子迴歸。較少研究在訓練時就中和波動或產業曝險，並比較中和前後的預測力與淨報酬。
3. **時變曝險的事前偵測。** Cederburg 與 O'Doherty（2016）、Barroso 等（2025）與 Hsu 等（2020）都指向低波動報酬的狀態相依性，但很少研究把它轉成選股模型的事前監控規則。

---

## 三、方向 B：把交易成本放進模型的學習目標

### 3.1 理論基準：不交易區間與部分調整

有交易成本時的最適交易理論，為 v1 的緩衝規則提供了完整的理論譜系。

**比例成本與不交易區間。** Davis 與 Norman（1990）證明，在比例交易成本下，最適策略是在持股比例周圍維持一個「不交易區間」：在區間內不動，碰到邊界才交易到邊界。Dumas 與 Luciano（1991）給出兩道控制邊界的精確解，Liu（2004）推廣到多資產與固定加比例成本的情況，並指出交易成本會大幅削弱報酬可預測性的價值。當報酬可以預測時，Balduzzi 與 Lynch（1999）量化了成本造成的效用損失；Lynch 與 Balduzzi（2000）則顯示可預測性會讓不交易區間隨狀態改變而且變寬。v1「進前 20 才買、跌出前 30 才賣」的規則，在形式上就是一個以排名定義、寬度固定的不交易區間。

**二次成本與部分調整。** Gârleanu 與 Pedersen（2013）＊在二次（價格衝擊）成本下得到封閉解：最適組合是「目前持股」與「瞄準組合」的線性組合，每期只朝目標移動一部分；瞄準組合是未來各期無摩擦最適組合的加權平均，訊號衰減越慢的權重越高。Gârleanu 與 Pedersen（2016）把它推廣到一般摩擦，Muhle-Karbe、Sefton 與 Shi（2026）進一步納入跨期避險，證明在可預測報酬與交易成本下，投資人以固定速度追蹤一個調整過的目標組合。

**實務化的交易規則。** Grinold（2018a）在簡化假設下推導出最適的線性交易規則：以單一「交易速率」決定每期移動的比例與各 alpha 來源的權重，並可據此計算預期風險、成本、換手與 alpha 曝險。Grinold（2018b）再擴充為分段線性的買進、持有、賣出規則：在不交易區內持有，區外只交易超出部分的一個比例。Moallemi 與 Sağlam（2017）提出可有效最佳化的線性再平衡規則族，在一般的可預測性、成本與限制下接近最佳。Mei 與 Nogales（2018）以簡單的二次規劃建構多資產、比例成本、報酬可預測下的次佳再平衡政策，並給出其確定等值損失的上界。Blomvall、Ekblom 與 Birge（2026）則以近似動態規劃處理高維度、異質比例成本與可預測報酬的多期配置。

這些研究的共同結論是：**在有成本的情況下，「慢慢調整」與「設定緩衝區」都是理論上的最適形式，而不是權宜之計**。訊號越持久，越值得交易。

### 3.2 實證：成本吃掉多少訊號？

Novy-Marx 與 Velikov（2016）系統性估計了各類異象的交易成本。月換手低於 50% 的異象，在採取降成本設計後多數仍有顯著的淨報酬，換手更高的則很少。最有效的降成本技術是「買持價差」（buy/hold spread），也就是開倉條件比續抱條件更嚴格，這和 v1 的緩衝規則是同一個概念。Korajczyk 與 Sadka（2004）以價格衝擊模型估計動能策略的損益兩平規模，並發現流動性加權可以降低成本。de Roon 與 Szymanowska（2012）顯示，只要數十個基點的交易成本，就能解釋多數組合報酬的可預測性。Carrasco 與 Koné（2023）以 GMM 檢定交易成本對異象組合選擇的影響，發現納入成本能改善樣本外表現。

對 ML 策略而言，問題更嚴重。Avramov 等（2023）＊指出，深度學習訊號在合理的交易成本下績效進一步惡化，原因正是高換手與極端部位。v1 的經驗完全一致：S1 中模型輸給固定規則的缺口，全部可以歸因於換手。

### 3.3 把成本或決策目標放進學習

**成本即正則化。** Olivares-Nadal 與 DeMiguel（2018）證明，含交易成本的組合問題等價於穩健最佳化、正則化迴歸與貝氏組合問題，因此可以把交易成本當作一個由資料校準的正則化項。這為「在訓練目標中加入換手懲罰」提供了直接的理論依據。

**決策導向學習。** Elmachtoub 與 Grigas（2022）＊的「Smart Predict, then Optimize」主張以下游決策的損失訓練預測模型；在模型不完美時，這比單純最小化預測誤差能得到更好的決策。Ho-Nguyen 與 Kılınç-Karzan（2022）則釐清了預測方法在什麼條件下能保證下游最佳化的表現。Agrawal 等（2019）＊把凸最佳化問題寫成神經網路中可微分的一層，使「預測 → 最佳化」可以端到端訓練。在組合問題上，Butler 與 Kwon（2023）把迴歸預測整合進均值—變異數最佳化，在無限制與等式限制下給出封閉解，不等式限制則用神經網路二次規劃層處理。Costa 與 Iyengar（2023）在端到端系統中加入分配穩健的組合層，明確處理模型風險，並從資料中學習風險容忍度與穩健程度。

**直接學習組合權重。** Zhang、Zohren 與 Roberts（2020）＊讓神經網路以 Sharpe 為目標直接輸出少數 ETF 的權重。Simon、Weibels 與 Zimmermann（2026）以深度神經網路建構參數化組合政策，直接最大化投資人效用；風險趨避在其中扮演經濟上的正則化角色，非線性政策的月確定等值報酬比線性政策高出 43–102 個基點。Babiak 與 Baruník（2026）顯示，長期投資人在動態配置中使用深度學習報酬預測，樣本外能得到統計與經濟上顯著的增益，增益在衰退期最大，且在交易成本與放空、借貸限制下仍然存在。

**成本感知的 ML 組合。** 與方向 B 最直接相關的是 Jensen、Kelly、Malamud 與 Pedersen（2026）。他們主張策略應以「可實行效率前緣」評估，也就是每一風險水準下扣成本後的報酬。忽略成本的 ML 組合過度依賴短暫的小型股特徵，淨報酬很差；他們推廣 Gârleanu–Pedersen 的框架，以考慮成本的經濟目標直接學習組合權重，得到明顯更好的前緣，並提出「經濟特徵重要性」的衡量方式。研究計畫原本把這篇列為 SSRN 工作論文，它已刊於 *Review of Financial Studies*。Li、Mulvey 與 Fabozzi（2026）則提出模組化的兩步驟「智慧交易規則」：先求無摩擦的最適組合，再只在預期增益超過成本時交易。它可以掛在任何預測模型之後；在 XGBoost 與 LSTM 上，它比把成本直接嵌入的一步驟方法有更高的報酬與 Sharpe、更低的換手。Allena（2025）的方法則與成本間接相關：他為 ML 報酬預測建立事前信賴區間，只交易預測精確的股票，結果優於傳統的高減低策略，可以看作從預測端降低雜訊換手的方法。

### 3.4 方向 B 的小結與研究缺口

理論與實證的結論一致：有成本時應該慢慢調整、設定緩衝區，而且已經有現成的工具把成本放進訓練。在美股大樣本中，Jensen 等（2026）證明成本感知的 ML 組合有明顯改善。

尚未回答的問題是：

1. **小樣本、月頻、資產數少的情境。** Jensen 等（2026）使用美股 1981–2020 年的大樣本；Simon 等（2026）、Babiak 與 Baruník（2026）也都是美股。台股 150 檔、132 個月的開發期，參數與樣本比完全不同，端到端方法是否還能穩定訓練，沒有答案。
2. **兩步驟與一步驟的比較。** Li、Mulvey 與 Fabozzi（2026）認為兩步驟（先預測、再以成本門檻決定交易）優於把成本嵌入訓練，這與 Jensen 等（2026）的一步驟取向相反。v1 的緩衝規則正好是兩步驟方法的特例，可以在台股資料上直接比較這兩種取向。
3. **換手懲罰對預測力的影響。** 計畫中「讓訊號變慢但預測力不降」的假說，在文獻中沒有直接檢驗。Olivares-Nadal 與 DeMiguel（2018）的「成本即正則化」提供了理論框架，但沒有應用在 ML 選股訊號上。

---

## 四、方向 F：預訓練為什麼沒有用？什麼條件下才有用？

### 4.1 成功的深度學習案例多半嵌入了經濟結構

金融領域中成功的深度學習模型，大多把經濟結構放進網路設計：

- Gu、Kelly 與 Xiu（2021）＊的條件自編碼器把因子模型的結構寫進網路，從個股特徵學出隱含因子，樣本外解釋報酬的能力優於傳統因子模型。
- Chen、Pelger 與 Zhu（2024）＊在深度學習模型中加入無套利條件，績效優於不加限制的模型。
- Bryzgalova、Pelger 與 Zhu（2025）以決策樹（AP-Trees）建構可解釋的管理組合，其樣本外 Sharpe 與 alpha 比傳統排序組合與 ML 預測組合高出最多三倍。
- Guijarro-Ordonez、Pelger 與 Zanotti（2026）先以條件潛在因子建構殘差組合，再用卷積 Transformer 萃取時間序列訊號，最後直接學習受限制的最適交易策略。
- Kelly、Kuznetsov、Malamud 與 Xu（2025）†把 Transformer 嵌入隨機折現因子，讓資訊在不同資產之間共享，相較於先前的 ML 定價模型大幅降低了定價誤差。

早期的 Heaton、Polson 與 Witte（2016）則以深度自編碼器建構組合，是表示學習應用於選股的先例。

這一系列研究的共同點是：網路學習的對象是有經濟意義的物件，例如因子、殘差或隨機折現因子，而不是讓模型自由地從價格序列中學。v1 的預訓練屬於後者。

### 4.2 低訊雜比與「複雜度的美德」之爭

Israel、Kelly 與 Moskowitz（2020）†指出，ML 在資產管理中面臨其他領域沒有的困難：訊雜比極低、時間序列樣本少、訊號一旦被發現就會被套利掉，因此需要經濟理論與人的判斷。

Kelly、Malamud 與 Zhou（2024）＊則提出相反方向的論點：在報酬預測中，參數多於樣本的模型配合適當的正則化，樣本外的擇時表現反而更好，樣本外 R² 低估了這類模型的經濟價值。不過 Nagel（2025）†的工作論文對此提出批評：當特徵遠多於樣本時，隨機傅立葉特徵的預測等同於對近期訓練報酬的相似度加權平均，實質上是一個依波動擇時的動能策略，其成功反映的是動能過去的表現，而不是學到的訊號。

這場爭論和 v1 直接相關：如果「大模型的增益」實際上只是隱含的動能或波動曝險，那麼方向 F 的問題就和方向 A 合流了，預訓練的表示學到的也可能只是已知因子。

### 4.3 自監督預訓練與時間序列基礎模型

在一般時間序列基準（電力、天氣、交通等）上，自監督與對比學習的效果相當明確。PatchTST（Nie et al., 2023）＊把序列切成區塊輸入 Transformer，TS2Vec（Yue et al., 2022）＊以階層式對比學習得到通用的序列表示。近年的時間序列基礎模型更進一步：TimesFM（Das et al., 2024）†在大量真實與合成資料上預訓練，零樣本預測接近有監督的最佳模型；Chronos（Ansari et al., 2024）†把數值量化成詞元，以語言模型架構訓練，在 42 個資料集上有競爭力的零樣本表現。

但金融報酬是例外。Rahimikia、Ni 與 Wang（2025）†的預印本直接檢驗了這個問題：現成的時間序列基礎模型，不論零樣本或微調，在 94 個市場的日超額報酬預測上表現都很差；改用金融資料從頭預訓練的模型，才得到實質的預測與經濟增益，更多資料、合成資料擴增與調參也會帶來進一步的改善。Hou 等（2021）†的 CMLF 架構在跨資料粒度（日內與日頻）的設定下加入對比預訓練目標，也得到了改善。

整體而言，預訓練在金融上有用的證據都附帶條件：**大量的金融專屬資料、較高的頻率，或跨粒度的輔助訊號**。在月頻、橫斷面、約 150 檔股票的設定下，目前沒有同儕審查的研究直接證明自監督預訓練有用或無用。v1 的負面結果在這個空白中有其價值。

### 4.4 股票之間的關係

另一條路線是讓模型同時看同一時點的所有股票。Feng 等（2019）†的時間關係排序模型以時間圖卷積同時建模股票的時間演變與彼此的關係，並把預測寫成排序問題。HIST（Xu et al., 2021）†從預先定義與隱藏的「概念」中萃取股票共享的資訊。MASTER（Li et al., 2024）＊以 Transformer 建模股票之間短暫的相關性，並用市場層級的資訊引導特徵選擇；它在中國股市的排序預測上有改善。這些模型多以日頻、中國或美國的大型股票池驗證；但 v1 月頻、150 檔的設定下，每期的橫斷面很小，關係建模能否發揮作用仍是未知數。

### 4.5 方向 F 的小結與研究缺口

文獻顯示，深度學習在金融上的成功多半來自嵌入經濟結構或建模股票間的關係；預訓練的成功案例則來自規律性高的非金融資料，或大量的金融專屬資料。研究計畫的停損點設計與此一致：先確認「讀整段價格走勢」是否有額外價值，若無，就把結果整理成有對照組的負面結果。

本方向可以貢獻的是：

1. **一份有對照組的負面結果。** 文獻中缺少「月頻、橫斷面、小樣本下預訓練無效」的系統性證據；v1 已有 50 個 GPU 小時的實驗紀錄，補上全市場資料後即可形成完整的對照。
2. **把預訓練目標換成有經濟結構的目標。** 依 4.1 的文獻，與選股目標一致的預訓練方式（例如預測殘差報酬或因子曝險），比通用的遮罩重建更有機會成功。這可以作為停損前的最後一個檢驗。
3. **與方向 A 合流。** 檢驗預訓練的表示和已知因子的相關性，即可回答「預訓練學到的是不是只是動能與波動」。

---

## 五、方向 G：換股能不能用強化學習來學？

### 5.1 直接強化學習與組合管理

Moody 與 Saffell（2001）＊以差分 Sharpe 比率為目標、納入交易成本，直接訓練交易系統，表現優於先估計價值再決策的方法。這是「以最終績效訓練」的早期代表，概念上與方向 B 的決策導向學習相通。在理論面，Wang 與 Zhou（2020）以熵正則化把連續時間均值—變異數配置寫成強化學習問題，證明最適回饋政策必為高斯分布且變異數隨時間遞減，並據此設計出可實行的演算法。

深度強化學習的組合管理研究數量很多，但證據品質參差不齊。Jiang、Xu 與 Liang（2017）＊在加密貨幣上報告了很高的回測報酬，但期間短、市場特殊。Wang 與 Ku（2022）以階層式 DDPG 控制組合風險，並以 CVaR 作為風險衡量。Fjellavli 等（2025）從標題看是在均值—變異數之外加入流動性，以強化學習做組合最佳化；本次未能取得其摘要。FinRL（Liu et al., 2021）†提供了開源的深度強化學習交易框架與基準環境。Gort 等（2022）†則指出，現有深度強化學習交易的成果可能是回測過度配適造成的偽陽性；他們以假設檢定剔除過度配適的代理人後，剩下的代理人樣本外報酬較高。

### 5.2 有模擬環境、答案已知的問題

強化學習在金融上最可信的成果，集中在有模擬環境、有理論解可以對照的問題。

- **最適下單執行。** Almgren 與 Chriss（2001）的經典模型在市場衝擊與價格風險之間取得平衡，是執行問題的理論基準。Nevmyvaka、Feng 與 Kearns（2006）†首次以大規模的毫秒級限價簿資料把強化學習用於最適執行；Ning、Lin 與 Jaimungal（2021）†以雙重深度 Q 學習處理執行問題，不需要隨機控制方法的嚴格模型假設。
- **避險。** Buehler、Gonon、Teichmann 與 Wood（2019）＊的深度避險在有交易成本、流動性與風險限制的模擬市場中學習衍生性商品組合的避險策略；Kolm 與 Ritter（2019）＊以強化學習在離散交易與非線性成本下複製並避險選擇權，是「在已知最適解附近驗證強化學習」的乾淨例子。
- **綜述。** Hambly、Xu 與 Yang（2023）＊回顧了強化學習在最適執行、組合最佳化、選擇權定價與避險、造市、智慧下單路由與機器人理財的應用。他們的結論是：最成功的是有模擬環境的問題，直接用來預測報酬或選股則受限於資料少與市場會變。Kolm 與 Ritter（2019）†的另一篇綜述把強化學習定位為解決跨期金融決策的近乎無模型方法。

### 5.3 學習「何時換、換多少」：不交易區間的學習

這是方向 G 與 v1 緩衝規則的交會點。Imaki 等（2021）†在深度避險中證明，對一大類效用函數與衍生性商品，不交易區間策略是最適的；他們設計了直接輸出區間上下界的「不交易區間網路」，訓練速度更快、避險效果更好。這是目前最清楚的「學習不交易區間」的例子。Li 與 Mulvey（2021）†結合動態規劃與遞迴神經網路，在狀態轉換與線性交易成本下求解多期組合問題，最多可處理 11 檔資產、250 期。這兩篇加上 3.1 節的 Gârleanu 與 Pedersen（2013）＊與 Grinold（2018b），構成方向 G 的方法基礎：理論給出最適解的形式（部分調整或不交易區間），神經網路或強化學習負責學習其參數。

### 5.4 方向 G 的小結與研究缺口

文獻的結論相當一致：強化學習在「有模擬環境、有已知答案可對照」的問題上表現好，直接選股的證據薄弱且容易過度配適。研究計畫「先建立答案已知的模擬市場、再固定訊號只學何時換與換多少」的設計，與這個結論吻合。

缺口在於：

1. **以排名為基礎的緩衝規則缺少理論對應。** 現有的不交易區間理論以持股權重定義區間，v1 則以排名定義（前 20／前 30）。把排名緩衝規則對應到權重空間的不交易區間，並以此作為強化學習的已知最適解，是一個具體、可做的貢獻。
2. **月頻小樣本下的強化學習。** 一百多個決策點遠少於強化學習一般需要的樣本。模擬環境的設計，例如以 v1 的訊號特性與 Gârleanu–Pedersen 的成本結構產生合成路徑，會決定研究能否進行。
3. **與方向 B 的比較基準。** 計畫中「G 接在 B 之後」的順序，在文獻上有依據：Li、Mulvey 與 Fabozzi（2026）的兩步驟規則與 Grinold（2018）的線性規則，都是強化學習必須勝過的簡單基準。

---

## 六、貫穿四個方向的驗證方法

四個方向都面對同一個統計問題：樣本短、訊號弱、嘗試的規格多。v1 以事前登錄與一次性封存驗證處理這個問題，文獻支持這個做法：

- **資料探勘與多重檢定。** Lo 與 MacKinlay（1990）說明依已知樣本特徵分組會造成資料窺探偏誤；Harvey、Liu 與 Zhu（2016）＊主張提高 t 值門檻；Yan 與 Zheng（2017）以 bootstrap 檢驗大量基本面訊號是否只是運氣。
- **回測過度配適。** Bailey 與 López de Prado（2014）＊的「消除膨脹的 Sharpe 比率」（deflated Sharpe ratio）校正了多重嘗試與非常態分布造成的高估，適合用來報告 v1 這種經過多輪挑選的結果。
- **研究設計的敏感度。** Soebhag、Van Vliet 與 Verwijmeren（2024）發現，組合排序方式等研究設計選擇會大幅改變異象的結果，也就是「非標準誤差」。
- **簡單基準。** DeMiguel、Garlappi 與 Uppal（2009）顯示，在估計誤差下，最佳化組合的樣本外表現常輸給 1/N。這與 v1 輸給動能規則與 0050 的經驗一致，也說明了為什麼每個方向都必須保留簡單基準。

---

## 七、綜合討論：四個方向的關係與研究定位

把四個方向的文獻放在一起，可以看到一條清楚的主線：

1. **方向 A 是其他方向的前提。** 若 ML 訊號主要是已知因子的組合（2.1、2.3 節），那麼方向 B 的成本問題、方向 F 的表示問題、方向 G 的換股問題，處理的其實都是「已知因子曝險的交易方式」。先完成曝險分解，其他三個方向才知道自己在優化什麼。
2. **方向 B 與 G 是同一個問題的單期與多期版本。** 理論上（3.1 節），有成本時的最適解是部分調整或不交易區間；B 把成本放進單期的訓練目標，G 學習多期的調整政策。Gârleanu 與 Pedersen（2013）與 Grinold（2018）提供了兩者共同的已知最適解。
3. **方向 F 的答案很可能是「瓶頸在資料，不在模型」。** 4.2、4.3 節的證據顯示，在低訊雜比與小樣本下，預訓練的成功依賴大量金融專屬資料。這與研究計畫的停損點設計一致。

在研究定位上，本計畫最有把握的貢獻，是提供一個**非美國、非微型股、扣成本、事前登錄**的完整檢驗。文獻中多數的正面結果來自美股全市場的大樣本，而 Avramov 等（2023）、Jo 與 Kim（2026）、Cakici 等（2023）都顯示，一旦排除難交易的股票、考慮成本與時間變化，ML 的優勢會大幅縮小。台股大中型股的設定正是檢驗這些發現的自然場域。

### 本回顧的限制

- 期刊檢索以 Crossref 為來源，F 與 G 的會議論文主要靠網路補充，未必完整；ICAIF、NeurIPS、KDD 等會議的金融應用論文值得再系統性檢索一次。
- 中文文獻未涵蓋。台股的低波動、ML 選股與交易成本研究，建議以華藝線上圖書館與 TEJ 另行檢索，例如《證券市場發展季刊》、《管理學報》、《財務金融學刊》。
- 部分文章（尤其是 *Journal of Portfolio Management*、*Financial Analysts Journal*、*Journal of Financial Data Science*）的摘要未公開。本文對這些文章的描述依據可取得的摘要或出版社頁面；Fjellavli 等（2025）只依標題描述。引用前建議核對全文。
- Nagel（2025）、Rahimikia 等（2025）、Kelly 等（2025）、Xu 等（2021）、Imaki 等（2021）、Gort 等（2022）為工作論文或預印本，尚未經同儕審查。

---

## 參考文獻

格式：作者（年）。標題。期刊或來源。DOI 或網址。＊ 表示研究計畫的種子文獻；† 表示網路補充，不在本次的 RIS 檔中。

### 方向 A：因子曝險、低波動異象與異象衰退

- Allena, R. (2025). Confident risk premiums and investments using machine learning uncertainties. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhaf087
- ＊Avramov, D., Cheng, S., & Metzker, L. (2023). Machine learning vs. economic restrictions: Evidence from stock return predictability. *Management Science*, 69(5).
- ＊Baker, M., Bradley, B., & Wurgler, J. (2011). Benchmarks as limits to arbitrage: Understanding the low-volatility anomaly. *Financial Analysts Journal*, 67(1).
- Bali, T. G., Cakici, N., & Whitelaw, R. F. (2011). Maxing out: Stocks as lotteries and the cross-section of expected returns. *Journal of Financial Economics*. https://doi.org/10.1016/j.jfineco.2010.08.014
- Bali, T. G., Engle, R. F., & Tang, Y. (2017). Dynamic conditional beta is alive and well in the cross section of daily stock returns. *Management Science*. https://doi.org/10.1287/mnsc.2016.2536
- Barroso, P., Detzel, A., & Maio, P. (2025). The volatility puzzle of the beta anomaly. *Journal of Financial Economics*. https://doi.org/10.1016/j.jfineco.2025.103994
- Black, F. (1972). Capital market equilibrium with restricted borrowing. *Journal of Business*. https://doi.org/10.1086/295472
- Black, F., Jensen, M. C., & Scholes, M. (1972). The capital asset pricing model: Some empirical tests. In M. C. Jensen (Ed.), *Studies in the Theory of Capital Markets*. Praeger.
- Blitz, D. (2016). The value of low volatility. *Journal of Portfolio Management*. https://doi.org/10.3905/jpm.2016.42.3.094
- Blitz, D., & Vidojevic, M. (2017). The profitability of low-volatility. *Journal of Empirical Finance*. https://doi.org/10.1016/j.jempfin.2017.05.001
- Bowles, B., Reed, A. V., Ringgenberg, M. C., & Thornock, J. (2024). Anomaly time. *Journal of Finance*. https://doi.org/10.1111/jofi.13372
- Brogaard, J., & Zareei, A. (2022). Machine learning and the stock market. *Journal of Financial and Quantitative Analysis*. https://doi.org/10.1017/s0022109022001120
- †Bui, D. G., Kong, D.-R., Lin, C.-Y., & Lin, T.-C. (2023). Momentum in machine learning: Evidence from the Taiwan stock market. *Pacific-Basin Finance Journal*, 82, 102178. https://doi.org/10.1016/j.pacfin.2023.102178
- Cakici, N., Fieberg, C., Metko, D., & Zaremba, A. (2023). Predicting returns with machine learning across horizons, firm size, and time. *Journal of Financial Data Science*. https://doi.org/10.3905/jfds.2023.1.139
- Cao, J., & Han, B. (2016). Idiosyncratic risk, costly arbitrage, and the cross-section of stock returns. *Journal of Banking & Finance*. https://doi.org/10.1016/j.jbankfin.2016.08.004
- Carhart, M. M. (1997). On persistence in mutual fund performance. *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.1997.tb03808.x
- Cederburg, S., & O'Doherty, M. S. (2016). Does it pay to bet against beta? On the conditional performance of the beta anomaly. *Journal of Finance*. https://doi.org/10.1111/jofi.12383
- Chordia, T., Subrahmanyam, A., & Tong, Q. (2014). Have capital market anomalies attenuated in the recent era of high liquidity and trading activity? *Journal of Accounting and Economics*. https://doi.org/10.1016/j.jacceco.2014.06.001
- Daniel, K., Mota, L., Rottke, S., & Santos, T. (2020). The cross-section of risk and returns. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhaa021
- Drobetz, W., Hollstein, F., Otto, T., & Prokopczuk, M. (2024). Estimating stock market betas via machine learning. *Journal of Financial and Quantitative Analysis*. https://doi.org/10.1017/s0022109024000036
- Fama, E. F., & French, K. R. (1992). The cross-section of expected stock returns. *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.1992.tb04398.x
- Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics*. https://doi.org/10.1016/0304-405x(93)90023-5
- Fama, E. F., & French, K. R. (1996). Multifactor explanations of asset pricing anomalies. *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.1996.tb05202.x
- Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*. https://doi.org/10.1016/j.jfineco.2014.10.010
- Fallahgoul, H., Franstianto, V., & Lin, X. (2024). Asset pricing with neural networks: Significance tests. *Journal of Econometrics*. https://doi.org/10.1016/j.jeconom.2023.105574
- ＊Frazzini, A., & Pedersen, L. H. (2014). Betting against beta. *Journal of Financial Economics*, 111(1).
- Gibbons, M. R., Ross, S. A., & Shanken, J. (1989). A test of the efficiency of a given portfolio. *Econometrica*. https://doi.org/10.2307/1913625
- ＊Gu, S., Kelly, B., & Xiu, D. (2020). Empirical asset pricing via machine learning. *Review of Financial Studies*, 33(5), 2223–2273.
- Han, Y., He, A., Rapach, D. E., & Zhou, G. (2024). Cross-sectional expected returns: New Fama–MacBeth regressions in the era of machine learning. *Review of Finance*. https://doi.org/10.1093/rof/rfae027
- ＊Harvey, C. R., Liu, Y., & Zhu, H. (2016). … and the cross-section of expected returns. *Review of Financial Studies*, 29(1).
- Haugen, R. A., & Baker, N. L. (1996). Commonality in the determinants of expected stock returns. *Journal of Financial Economics*. https://doi.org/10.1016/0304-405x(95)00868-f
- Hou, K., Xue, C., & Zhang, L. (2018). Replicating anomalies. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhy131
- †Hsu, C.-C., Wei, A.-P., & Chen, M.-L. (2020). Funding liquidity risk and the low-volatility anomaly: Evidence from the Taiwan stock market. *North American Journal of Economics and Finance*, 54, 100932. https://doi.org/10.1016/j.najef.2019.02.010
- Irvine, P., Kim, J. H., & Ren, J. (2024). The beta anomaly and mutual fund performance. *Management Science*. https://doi.org/10.1287/mnsc.2022.4639
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.1993.tb04702.x
- Jensen, T. I., Kelly, B., & Pedersen, L. H. (2023). Is there a replication crisis in finance? *Journal of Finance*. https://doi.org/10.1111/jofi.13249
- Jo, Y., & Kim, Y. H. (2026). Rethinking variable importance in machine learning: An economic perspective on empirical asset pricing. *Financial Analysts Journal*. https://doi.org/10.1080/0015198x.2026.2621646
- Karolyi, G. A., & Van Nieuwerburgh, S. (2020). New methods for the cross-section of returns. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhaa019
- ＊Kelly, B., Pruitt, S., & Su, Y. (2019). Characteristics are covariances: A unified model of risk and return. *Journal of Financial Economics*, 134(3).
- Kim, S., Korajczyk, R. A., & Neuhierl, A. (2020). Arbitrage portfolios. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhaa102
- Kozak, S., Nagel, S., & Santosh, S. (2020). Shrinking the cross-section. *Journal of Financial Economics*. https://doi.org/10.1016/j.jfineco.2019.06.008
- Lettau, M., & Pelger, M. (2020). Factors that fit the time series and cross-section of stock returns. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhaa020
- Lewellen, J. (2015). The cross-section of expected stock returns. *Critical Finance Review*. https://doi.org/10.1561/104.00000024
- Li, X., Sullivan, R. N., & Garcia-Feijóo, L. (2014). The limits to arbitrage and the low-volatility anomaly. *Financial Analysts Journal*. https://doi.org/10.2469/faj.v70.n1.3
- Li, X., Sullivan, R. N., & Garcia-Feijóo, L. (2016). The low-volatility anomaly: Market evidence on systematic risk vs. mispricing. *Financial Analysts Journal*. https://doi.org/10.2469/faj.v72.n1.6
- †Lin, M.-C., & Lin, Y.-L. (2021). Idiosyncratic skewness and cross-section of stock returns: Evidence from Taiwan. *International Review of Financial Analysis*, 77, 101816. https://doi.org/10.1016/j.irfa.2021.101816
- Linnainmaa, J. T., & Roberts, M. R. (2018). The history of the cross-section of stock returns. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhy030
- ＊McLean, R. D., & Pontiff, J. (2016). Does academic research destroy stock return predictability? *Journal of Finance*, 71(1).
- Oderda, G., Berrada, T., Messikh, R. J., & Pictet, O. (2015). Beta-arbitrage strategies: When do they work, and why? *Quantitative Finance*. https://doi.org/10.1080/14697688.2014.938446
- Zhao, A. B., & Cheng, T. (2022). Stock return prediction: Stacking a variety of models. *Journal of Empirical Finance*. https://doi.org/10.1016/j.jempfin.2022.04.001

### 方向 B：交易成本與決策導向學習

- ＊Agrawal, A., Amos, B., Barratt, S., Boyd, S., Diamond, S., & Kolter, J. Z. (2019). Differentiable convex optimization layers. *Advances in Neural Information Processing Systems (NeurIPS)*.
- Babiak, M., & Baruník, J. (2026). Deep learning, predictability, and optimal portfolio returns. *Journal of Empirical Finance*. https://doi.org/10.1016/j.jempfin.2026.101705
- Balduzzi, P., & Lynch, A. W. (1999). Transaction costs and predictability: Some utility cost calculations. *Journal of Financial Economics*. https://doi.org/10.1016/s0304-405x(99)00004-5
- Blomvall, J., Ekblom, J., & Birge, J. R. (2026). Approximate dynamic programming for high-dimensional portfolio choice with transaction costs. *Quantitative Finance*. https://doi.org/10.1080/14697688.2026.2708220
- Butler, A., & Kwon, R. H. (2023). Integrating prediction in mean-variance portfolio optimization. *Quantitative Finance*. https://doi.org/10.1080/14697688.2022.2162432
- Carrasco, M., & Koné, N. (2023). Test for trading costs effect in a portfolio selection problem with recursive utility. *Journal of Financial Econometrics*. https://doi.org/10.1093/jjfinec/nbad015
- Costa, G., & Iyengar, G. N. (2023). Distributionally robust end-to-end portfolio construction. *Quantitative Finance*. https://doi.org/10.1080/14697688.2023.2236148
- Davis, M. H. A., & Norman, A. R. (1990). Portfolio selection with transaction costs. *Mathematics of Operations Research*. https://doi.org/10.1287/moor.15.4.676
- de Roon, F., & Szymanowska, M. (2012). Asset pricing restrictions on predictability: Frictions matter. *Management Science*. https://doi.org/10.1287/mnsc.1120.1522
- Dumas, B., & Luciano, E. (1991). An exact solution to a dynamic portfolio choice problem under transactions costs. *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.1991.tb02675.x
- ＊Elmachtoub, A. N., & Grigas, P. (2022). Smart "predict, then optimize". *Management Science*, 68(1).
- ＊Gârleanu, N., & Pedersen, L. H. (2013). Dynamic trading with predictable returns and transaction costs. *Journal of Finance*, 68(6), 2309–2340.
- Gârleanu, N., & Pedersen, L. H. (2016). Dynamic portfolio choice with frictions. *Journal of Economic Theory*. https://doi.org/10.1016/j.jet.2016.06.001
- Grinold, R. (2018a). Linear trading rules for portfolio management. *Journal of Portfolio Management*. https://doi.org/10.3905/jpm.2018.44.6.109
- Grinold, R. (2018b). Nonlinear trading rules for portfolio management. *Journal of Portfolio Management*. https://doi.org/10.3905/jpm.2018.45.1.062
- Ho-Nguyen, N., & Kılınç-Karzan, F. (2022). Risk guarantees for end-to-end prediction and optimization processes. *Management Science*. https://doi.org/10.1287/mnsc.2022.4321
- Jensen, T. I., Kelly, B., Malamud, S., & Pedersen, L. H. (2026). Machine learning and the implementable efficient frontier. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhag022
- Korajczyk, R. A., & Sadka, R. (2004). Are momentum profits robust to trading costs? *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.2004.00656.x
- Lee, Y., Kim, J. H., Kim, W. C., & Fabozzi, F. J. (2024). An overview of machine learning for portfolio optimization. *Journal of Portfolio Management*. https://doi.org/10.3905/jpm.2024.1.639
- Li, S., Mulvey, J. M., & Fabozzi, F. J. (2026). Smart trading rule: A modular machine learning framework for portfolio optimization with transaction costs. *Journal of Financial Data Science*. https://doi.org/10.3905/jfds.2026.1.217
- Liu, H. (2004). Optimal consumption and investment with transaction costs and multiple risky assets. *Journal of Finance*. https://doi.org/10.1111/j.1540-6261.2004.00634.x
- Lynch, A. W., & Balduzzi, P. (2000). Predictability and transaction costs: The impact on rebalancing rules and behavior. *Journal of Finance*. https://doi.org/10.1111/0022-1082.00287
- Mei, X., & Nogales, F. J. (2018). Portfolio selection with proportional transaction costs and predictability. *Journal of Banking & Finance*. https://doi.org/10.1016/j.jbankfin.2018.07.012
- Moallemi, C. C., & Sağlam, M. (2017). Dynamic portfolio choice with linear rebalancing rules. *Journal of Financial and Quantitative Analysis*. https://doi.org/10.1017/s0022109017000345
- Muhle-Karbe, J., Sefton, J., & Shi, X. (2026). Dynamic portfolio choice with intertemporal hedging and transaction costs. *Management Science*. https://doi.org/10.1287/mnsc.2024.05913
- Novy-Marx, R., & Velikov, M. (2016). A taxonomy of anomalies and their trading costs. *Review of Financial Studies*, 29(1), 104–147. https://doi.org/10.1093/rfs/hhv063
- Olivares-Nadal, A. V., & DeMiguel, V. (2018). Technical note—A robust perspective on transaction costs in portfolio optimization. *Operations Research*. https://doi.org/10.1287/opre.2017.1699
- Simon, F., Weibels, S., & Zimmermann, T. (2026). Deep parametric portfolio policies. *Management Science*. https://doi.org/10.1287/mnsc.2025.00721
- ＊Zhang, Z., Zohren, S., & Roberts, S. (2020). Deep learning for portfolio optimization. *Journal of Financial Data Science*, 2(4).

### 方向 F：表示學習與深度學習資產定價

- †Ansari, A. F., Stella, L., Turkmen, C., et al. (2024). Chronos: Learning the language of time series. *Transactions on Machine Learning Research*. https://openreview.net/forum?id=gerNCVqqtR
- Bryzgalova, S., Pelger, M., & Zhu, J. (2025). Forest through the trees: Building cross-sections of stock returns. *Journal of Finance*. https://doi.org/10.1111/jofi.13477
- ＊Chen, L., Pelger, M., & Zhu, J. (2024). Deep learning in asset pricing. *Management Science*, 70(2).
- †Das, A., Kong, W., Sen, R., & Zhou, Y. (2024). A decoder-only foundation model for time-series forecasting. *Proceedings of the 41st International Conference on Machine Learning (ICML)*, PMLR 235. https://proceedings.mlr.press/v235/das24c.html
- †Feng, F., He, X., Wang, X., Luo, C., Liu, Y., & Chua, T.-S. (2019). Temporal relational ranking for stock prediction. *ACM Transactions on Information Systems*, 37(2). https://doi.org/10.1145/3309547
- ＊Gu, S., Kelly, B., & Xiu, D. (2021). Autoencoder asset pricing models. *Journal of Econometrics*, 222(1).
- Guijarro-Ordonez, J., Pelger, M., & Zanotti, G. (2026). Deep learning statistical arbitrage. *Management Science*. https://doi.org/10.1287/mnsc.2022.03132
- Heaton, J. B., Polson, N. G., & Witte, J. H. (2016). Deep learning for finance: Deep portfolios. *Applied Stochastic Models in Business and Industry*. https://doi.org/10.1002/asmb.2209
- †Hou, M., Xu, C., Liu, Y., Liu, W., Bian, J., Wu, L., Li, Z., Chen, E., & Liu, T.-Y. (2021). Stock trend prediction with multi-granularity data: A contrastive learning approach with adaptive fusion. *Proceedings of CIKM '21*, 700–709. https://doi.org/10.1145/3459637.3482483
- †Israel, R., Kelly, B. T., & Moskowitz, T. J. (2020). Can machines "learn" finance? *Journal of Investment Management*, 18(2), 23–36. https://doi.org/10.2139/ssrn.3624052
- †Kelly, B. T., Kuznetsov, B., Malamud, S., & Xu, T. A. (2025). Artificial intelligence asset pricing models. NBER Working Paper 33351. https://www.nber.org/papers/w33351
- ＊Kelly, B., Malamud, S., & Zhou, K. (2024). The virtue of complexity in return prediction. *Journal of Finance*, 79(1), 459–503.
- ＊Li, T., Liu, Z., Shen, Y., Wang, X., Chen, H., & Huang, S. (2024). MASTER: Market-guided stock transformer for stock price forecasting. *Proceedings of the AAAI Conference on Artificial Intelligence*, 38(1), 162–170. https://doi.org/10.1609/aaai.v38i1.27767
- †Nagel, S. (2025). Seemingly virtuous complexity in return prediction. NBER Working Paper 34104. https://www.nber.org/papers/w34104
- ＊Nie, Y., Nguyen, N. H., Sinthong, P., & Kalagnanam, J. (2023). A time series is worth 64 words: Long-term forecasting with transformers. *International Conference on Learning Representations (ICLR)*.
- †Rahimikia, E., Ni, H., & Wang, W. (2025). Re(Visiting) time series foundation models in finance. arXiv:2511.18578.
- †Xu, W., Liu, W., Wang, L., Xia, Y., Bian, J., Yin, J., & Liu, T.-Y. (2021). HIST: A graph-based framework for stock trend forecasting via mining concept-oriented shared information. arXiv:2110.13716.
- ＊Yue, Z., et al. (2022). TS2Vec: Towards universal representation of time series. *Proceedings of the AAAI Conference on Artificial Intelligence*.

### 方向 G：強化學習、執行與避險

- Almgren, R., & Chriss, N. (2001). Optimal execution of portfolio transactions. *Journal of Risk*. https://doi.org/10.21314/jor.2001.041
- ＊Buehler, H., Gonon, L., Teichmann, J., & Wood, B. (2019). Deep hedging. *Quantitative Finance*, 19(8), 1271–1291.
- Fjellavli, M., Oliveira, C., Pimentel, R., & Schiøtz, D. (2025). Mean–variance-liquidity portfolio optimization with reinforcement learning. *Journal of Financial Data Science*. https://doi.org/10.3905/jfds.2025.1.183
- †Gort, B. J. D., Liu, X.-Y., Sun, X., Gao, J., Chen, S., & Wang, C. D. (2022). Deep reinforcement learning for cryptocurrency trading: Practical approach to address backtest overfitting. arXiv:2209.05559.
- ＊Hambly, B., Xu, R., & Yang, H. (2023). Recent advances in reinforcement learning in finance. *Mathematical Finance*, 33(3), 437–503. https://doi.org/10.1111/mafi.12382
- †Imaki, S., Imajo, K., Ito, K., Minami, K., & Nakagawa, K. (2021). No-transaction band network: A neural network architecture for efficient deep hedging. arXiv:2103.01775.
- ＊Jiang, Z., Xu, D., & Liang, J. (2017). A deep reinforcement learning framework for the financial portfolio management problem. arXiv:1706.10059.
- ＊Kolm, P. N., & Ritter, G. (2019). Dynamic replication and hedging: A reinforcement learning approach. *Journal of Financial Data Science*, 1(1), 159–171.
- †Kolm, P. N., & Ritter, G. (2019). Modern perspectives on reinforcement learning in finance. SSRN 3449401. https://doi.org/10.2139/ssrn.3449401
- †Li, X., & Mulvey, J. M. (2021). Portfolio optimization under regime switching and transaction costs: Combining neural networks and dynamic programs. *INFORMS Journal on Optimization*, 3(4), 398–417. https://doi.org/10.1287/ijoo.2021.0053
- †Liu, X.-Y., Yang, H., Gao, J., & Wang, C. D. (2021). FinRL: Deep reinforcement learning framework to automate trading in quantitative finance. *Proceedings of the 2nd ACM International Conference on AI in Finance (ICAIF '21)*. https://doi.org/10.1145/3490354.3494366
- ＊Moody, J., & Saffell, M. (2001). Learning to trade via direct reinforcement. *IEEE Transactions on Neural Networks*, 12(4), 875–889.
- †Nevmyvaka, Y., Feng, Y., & Kearns, M. (2006). Reinforcement learning for optimized trade execution. *Proceedings of the 23rd International Conference on Machine Learning (ICML)*, 673–680. https://doi.org/10.1145/1143844.1143929
- †Ning, B., Lin, F. H. T., & Jaimungal, S. (2021). Double deep Q-learning for optimal execution. *Applied Mathematical Finance*, 28(4), 361–380. https://doi.org/10.1080/1350486X.2022.2077783
- Wang, H., & Zhou, X. Y. (2020). Continuous-time mean–variance portfolio selection: A reinforcement learning framework. *Mathematical Finance*. https://doi.org/10.1111/mafi.12281
- Wang, M., & Ku, H. (2022). Risk-sensitive policies for portfolio management. *Expert Systems with Applications*. https://doi.org/10.1016/j.eswa.2022.116807

### 驗證方法

- ＊Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management*, 40(5).
- DeMiguel, V., Garlappi, L., & Uppal, R. (2009). Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy? *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhm075
- Lo, A. W., & MacKinlay, A. C. (1990). Data-snooping biases in tests of financial asset pricing models. *Review of Financial Studies*. https://doi.org/10.1093/rfs/3.3.431
- Soebhag, A., Van Vliet, B., & Verwijmeren, P. (2024). Non-standard errors in asset pricing: Mind your sorts. *Journal of Empirical Finance*. https://doi.org/10.1016/j.jempfin.2024.101517
- Yan, X., & Zheng, L. (2017). Fundamental analysis and the cross-section of stock returns: A data-mining approach. *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhx001
