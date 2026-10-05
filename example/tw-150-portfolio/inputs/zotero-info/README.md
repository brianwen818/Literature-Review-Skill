# Zotero 設定

最後一步可以把你標記的文章直接加入 Zotero（只加書目資料，不含 PDF）。這一步是選用的；不設定也能得到可匯入 Zotero 的 `.ris` 檔。

## 步驟

1. 把本資料夾的 `.env.example` 複製一份，改名為 `.env`。
2. 填入下面三個值。
3. 在專案的 `config.yaml` 的 `zotero.collection` 填入要放進去的 collection（選填）。

`.env` 含有金鑰，已被 `.gitignore` 排除。不要把它貼到文件、聊天或提交到版本控制。

## 取得 API key（`ZOTERO_API_KEY`）

1. 登入 <https://www.zotero.org/settings/keys>。
2. 點 **Create new private key**，取一個名稱。
3. 權限設定：
   - 用個人文獻庫：勾選 **Allow library access** 與 **Allow write access**。
   - 用群組文獻庫：在 Default Group Permissions（或個別群組）選 **Read/Write**。
4. 按 **Save Key**。金鑰只會顯示一次，請立刻複製到 `.env`。

本工具需要寫入權限才能新增條目；唯讀的金鑰只能用來排除文獻庫裡已有的文章。

## 取得 library ID（`ZOTERO_LIBRARY_ID`）與類型（`ZOTERO_LIBRARY_TYPE`）

- **群組文獻庫**（`ZOTERO_LIBRARY_TYPE=group`）：在 zotero.org 的 Groups 頁面打開該群組，網址形如 `https://www.zotero.org/groups/1234567/group_name`，中間的數字就是 ID。
- **個人文獻庫**（`ZOTERO_LIBRARY_TYPE=user`）：在 <https://www.zotero.org/settings/keys> 頁面上方會顯示「Your userID for use in API calls is …」。

## 加入之後

- 每筆新增的條目都會帶兩個標籤：`config.yaml` 裡的 `zotero.tag`，以及含日期時間的批次標籤。在 Zotero 裡點批次標籤就能選出並刪除整批。
- 文獻庫裡已有的文章（以 DOI 或標題比對）不會重複新增。
- 重跑同一步驟不會產生重複條目。
