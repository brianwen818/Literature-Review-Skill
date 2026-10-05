# Literature Review Skill

讓 AI agent 幫你做文獻蒐集：給它你的論文（或幾篇關鍵文獻）和一份種子文獻清單，它會在你指定的期刊裡找出相關文章、逐篇閱讀摘要並說明理由，最後交給你兩份 Excel 和一份總結。你在 Excel 裡勾選要保留的文章後，它可以把這些文章加進 Zotero。

*An agent skill for literature collection: from your manuscript and seed references, it searches the journals you choose (via Crossref), ranks and reads the candidates, and hands you two Excel workbooks and a summary. After you mark the articles you want, it adds them to Zotero or exports them. The agent instructions are in English ([SKILL.md](.claude/skills/lit-review/SKILL.md)); this README is in Traditional Chinese.*

## 它會做什麼

1. 把你的主要文件（PDF 或 Markdown）轉成文字，並整理種子文獻、查出每筆的 DOI。
2. 從文件中抽出關鍵詞，由 agent 篩選後請你確認。
3. 用每個關鍵詞檢索每本期刊（資料來源是 [Crossref](https://www.crossref.org/)，免費、不需帳號）。
4. 為每篇候選文章計算相關度，並排除書評、勘誤等非研究論文。
5. Agent 逐篇閱讀分數最高的文章（標題與摘要），給 1–5 分並寫下理由。
6. 往回追「最相關的文章都引用了誰」，找出期刊檢索找不到的專書與經典文獻。
7. 產出結果，等你標記，再寫入 Zotero 或匯出。

## 你會得到什麼

| 檔案 | 內容 |
|---|---|
| `all-relevant-articles.xlsx` | 所有通過相關度門檻的文章，依期刊、再依相關度排序 |
| `shortlist.xlsx` | 最相關的 n 篇（`shortlist` 分頁）與引文回溯找到的文獻（`snowball` 分頁）。每篇有一欄 `add-zotero-or-not` 讓你選 yes / no，以及一欄圖書館檢索連結 |
| `summary.md` | 這次蒐集的數量、各期刊結果、主題分布、最相關的文章與理由、資料品質提醒，以及 agent 寫的分析 |
| `zotero-added.xlsx` | 你標記要保留的文章（標記完成後產生） |
| `zotero-export.rdf` 或 `zotero-import.ris` | 有上傳 Zotero 時是從 Zotero 匯出的 RDF；沒上傳時是可直接匯入 Zotero 的 RIS |

## 開始使用

需要 Python 3.10 以上（開發時以 3.12 測試），以及一個能執行指令的 AI agent（例如 [Claude Code](https://claude.com/claude-code)）。

```bash
git clone https://github.com/brianwen818/Literature-Review-Skill.git
cd Literature-Review-Skill
pip install -r requirements.txt
```

在這個資料夾裡開啟 agent，然後直接告訴它你要做什麼，例如：

> 幫我建立一個叫 my-paper 的文獻蒐集專案。我的論文草稿在 D:\papers\draft.pdf，想在政治學前 20 本期刊裡找 50 篇相關文章。

Agent 會依照 [SKILL.md](.claude/skills/lit-review/SKILL.md) 的流程一步步進行，並在兩個地方停下來等你：

- **檢索之前**：請你確認關鍵詞與期刊清單。
- **產出短名單之後**：請你在 `shortlist.xlsx` 勾選要保留的文章。

## 你需要準備的東西

Agent 建立專案後，資料放在 `projects/<專案名>/inputs/`：

| 項目 | 說明 | 必要 |
|---|---|---|
| `main-docs/` | 你的論文草稿或重要參考文獻全文，PDF 或 `.md`。一個或多個檔案 | 是 |
| `seed-references.csv` | 種子文獻。`reference` 欄貼上引用文字，或 `doi` 欄填 DOI，擇一即可；也可以直接放 Zotero 匯出的 CSV | 否。留空時改用主要文件的參考文獻 |
| `journal-lists.csv` | 要檢索的期刊。只填期刊名稱也可以，ISSN 會自動查 | 是，但可以請 agent 建議 |
| `config.yaml` | 篇數 n、短名單模式、年份範圍、圖書館連結等設定 | 有預設值 |
| `zotero-info/.env` | Zotero 金鑰，設定方式見同資料夾的 `README.md` | 只有要上傳 Zotero 時 |

[references/journal-lists/](references/journal-lists/) 有 16 個領域的期刊清單可以當起點。

### 常用設定

`config.yaml` 裡每個設定都有說明，最常改的是：

- `n_articles`：短名單要幾篇。
- `shortlist_mode`：`global` 取全部期刊中最相關的 n 篇；`per-journal` 每本期刊各取 n ÷ 期刊數 篇（不夠相關的不會硬湊，空出的名額預設讓給其他期刊）。
- `year_from`、`year_to`：出版年份範圍。
- `library_link_template`：圖書館檢索連結的網址格式。預設是政大圖書館；換成你學校的 Primo 網址即可，`{title}` 會被換成文章標題。
- `use_specter`：是否啟用額外的語意相似訊號，見下一節。

## 相關度是怎麼算的

每篇候選文章有最多三個訊號，各自換算成百分位後加權平均：

| 訊號 | 意義 | 預設權重 |
|---|---|---|
| 引文重疊 | 它引用了幾篇你的種子文獻，以及它的參考文獻和種子文獻的參考文獻重疊多少 | 0.40 |
| 用詞相似 | 它的標題與摘要，和你的主要文件用詞有多像（TF-IDF） | 0.20 |
| 語意相似（選用） | 用 SPECTER 模型比較語意，用詞不同也認得出主題相近 | 0.40 |

缺少某個訊號時，權重由其餘訊號重新分配。沒有摘要的文章在自己的群組內排名，避免被系統性低估。

分數只用來決定「哪些文章值得 agent 細讀」。最後的排序以 agent 閱讀後給的 1–5 分為主。

### 選用的 SPECTER

SPECTER 需要另外安裝 PyTorch，檔案很大，沒有顯示卡時也比較慢，所以預設關閉。想知道你的電腦適不適合開啟：

```bash
python codes/scripts/07_check_specter.py
```

它會檢查是否有可用的顯示卡、是否已下載過模型（有的話會直接重用），並給出建議。要啟用時執行 `pip install -r requirements-specter.txt`，並把 `config.yaml` 的 `use_specter` 設為 `on` 或 `auto`。

## 範例：tw-150-portfolio

[example/](example/) 是一次完整執行的紀錄。研究主題是一個台股價量機器學習選股專案（[研究報告](example/project_report.md)），目標是為它的[四個研究所研究方向](example/tw-150-portfolio_改善目標與研究所研究方向.md)蒐集文獻：

- **A 因子曝險**：模型學到的是新東西，還是已知因子？
- **B 成本感知學習**：把交易成本放進學習目標。
- **F 表示學習**：預訓練為什麼沒用？
- **G 強化學習**：換股的時機和幅度能不能用學的？

> 這次執行從建立專案到匯出 RIS，**所有步驟與原本需要真人做的決定**（確認關鍵詞與期刊、接受種子文獻比對、在短名單勾選 yes／no）都由 **Claude Opus 5.5（medium effort）** 在 Claude Code 中代為完成，沒有人工介入。逐篇閱讀分給 4 個（期刊檢索）與 3 個（引文回溯）平行的子 agent。
>
> **完整流程總時間：11 分 24 秒**（2026-10-05 17:53:01 – 18:04:25，含 Crossref 檢索、SPECTER 計算、240 篇的閱讀評分與總結撰寫）。

### 代為做的決定

| 項目 | 決定 |
|---|---|
| 主要文件 | 研究方向文件（中文）。研究報告只供 agent 理解背景，不放進相似度計算，以免拉向 v1 的實作細節 |
| 種子文獻 | 研究方向文件列出的 24 篇；21 篇解析出 DOI，3 篇是會議論文或比對到別篇，保持未解析 |
| 期刊 | 20 本財務、計量、作業研究與機器學習期刊，另存為 [finance_quant.csv](references/journal-lists/finance_quant.csv) |
| 關鍵詞 | 自動抽取只得到 1 個（文件是中文），改由 agent 依四個方向寫了 28 個英文片語 |
| 設定 | n = 60、`global`、2005–2026 年、`use_specter: on`（RTX 4070，py312 環境） |
| 短名單勾選 | 相關度 4–5 一律 yes；3 分只在補足 F、G 與驗證這些薄弱主題時 yes |
| 最後一步 | 不上傳 Zotero，只匯出 RIS |

### 結果

| 階段 | 數量 |
|---|---|
| 查詢（28 關鍵詞 × 20 期刊） | 560 |
| 檢索命中 → 不重複文章 → 進入評分 | 9,157 → 5,785 → 5,704 |
| 過門檻（all-relevant-articles） | 1,131 |
| agent 細讀（期刊檢索／引文回溯） | 180 ／ 60 |
| 短名單／引文回溯列出 | 60 ／ 30 |
| 勾選 yes，匯出 RIS | 78 |

短名單的主題分布：A 方向 33 篇、B 方向 20 篇、F 與 G 合計 5 篇、驗證 2 篇。F 與 G 偏少，是因為這兩個方向的主要文獻發表在機器學習會議，Crossref 收錄很少；[summary.md](example/tw-150-portfolio/outputs/summary.md) 的分析一節列出了補救的檢索建議。

產出檔案：

- [summary.md](example/tw-150-portfolio/outputs/summary.md)：數量漏斗、各期刊結果、最相關文章與理由，以及 agent 的分析
- [shortlist.xlsx](example/tw-150-portfolio/outputs/shortlist.xlsx)、[all-relevant-articles.xlsx](example/tw-150-portfolio/outputs/all-relevant-articles.xlsx)
- [zotero-added.xlsx](example/tw-150-portfolio/outputs/zotero-added.xlsx)、[zotero-import.ris](example/tw-150-portfolio/outputs/zotero-import.ris)
- [literature-review.md](example/tw-150-portfolio/outputs/literature-review.md)：事後另外請 agent 以蒐集到的文獻（並上網補充 F、G 方向）撰寫的四方向文獻回顧，不屬於 skill 的標準產出

`intermediate-data/` 保留了關鍵詞、種子比對、每批的閱讀判斷（`judging/*/judged-*.json`）與評分結果；三個體積較大的原始快取（約 50 MB）沒有提交，重跑步驟 6、8、10 會重新產生。

## 已知限制

- **中文文獻**：Crossref 幾乎不收錄中文期刊，中文文獻需要另外檢索。
- **摘要不齊全**：有些出版社不提供摘要給 Crossref（測試時 Elsevier 的 Electoral Studies 就完全沒有），這些文章 agent 只能憑標題判斷。
- **專書**：期刊檢索只找得到期刊論文。專書靠引文回溯找，而且要有多篇相關文章引用它才會出現；沒有 DOI 的專書只有書名、作者、年份。
- **種子文獻的 DOI 比對**：只有在標題、第一作者、年份都吻合時才採用，寧可漏掉也不配錯。專書、新聞、非英文文獻通常配不到，這是正常的。
- **圖書館連結**：連結是依網址格式產生的檢索結果頁，不保證館藏一定有該文章。
- **結果會隨時間變動**：Crossref 的資料持續更新，agent 的閱讀判斷也不是完全可重現的。

## 資料夾結構

```
.claude/skills/lit-review/SKILL.md   agent 的操作流程
codes/modules/                       函式庫
codes/scripts/                       各階段的執行腳本（01–12）
codes/tests/                         單元測試
templates/                           新專案的模板
references/journal-lists/            各領域期刊清單
example/                             一次完整執行的範例（見上方「範例」）
projects/<專案名>/                    你的資料與結果（不會進版本控制）
    inputs/  intermediate-data/  outputs/
```

`projects/` 底下的所有內容（論文草稿、金鑰、結果）都被 `.gitignore` 排除，不會被提交。

## 開發

```bash
pip install -r requirements-dev.txt
python -m pytest codes/tests
```

也可以不透過 agent 手動執行各階段，每支腳本都有 `--help`。其中關鍵詞篩選與逐篇閱讀是設計給 agent 做的：略過閱讀時，結果會只依計算出的分數排序。

## 授權

[MIT](LICENSE)
