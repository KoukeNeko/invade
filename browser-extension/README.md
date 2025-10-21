# 笨他侵略：支語提示器 Chrome 擴充套件

此擴充套件會在瀏覽網頁時，標示常見的中國用語（支語），並提供對應的替代詞與描述，協助你快速辨識可疑詞彙。

## 功能總覽

- 自動掃描頁面文字並標示支語
- 游標移到標示上方可顯示詳細資訊、建議用法與例句
- 底色與底線可分別啟用，並自動依文字顏色切換底色
- 報章雜誌風格的設定頁與懸浮資訊卡
- 可選擇忽略輸入框或停用提示浮窗

## 資料生成

擴充套件使用 `database/vocabs` 目錄的 YAML 檔案作為資料來源。安裝前請先確保語境模型與詞彙資料都是最新版本：

```bash
# 先輸出語境權重（含 TF-IDF 分類器等）
cd tools/menu_classifier
python3 train_all.py

# 再生成瀏覽器擴充套件所需的 JSON 資料
cd cmd/build
BAKAINVADE_DIR=$(pwd)/../.. go run . extension
```

執行後會在 `browser-extension/chrome/data/vocabs.json` 生成最新的詞彙資料。

## 詞彙欄位補充

在 `database/vocabs/*.yml` 的詞彙資料中，可額外帶有 `matchOptions` 來細調比對行為，重新執行 `go run . extension` 後就會被帶入 `vocabs.json`：

- `matchMode: "standalone"`：要求詞彙需出現在標點或空白邊界之間，適合英數縮寫或需獨立顯示的詞彙。
- `skipPhrases`: `string[]`：列出遇到特定片語時要忽略的情境，例如 `"海內存知己"`。
- `context`: 指定上下文加權規則，例如遇到特定前後詞時扣分（可用於排除常見誤判）。
- `uncertainRange`: 讓規則評分落在某段區間時視為「需要模型進一步判斷」。
- `classifier`: 載入離線訓練的權重（例如 TF-IDF + Logistic Regression）以強化邊界案例。
- `semantic`: 設定語意 embedding（ONNX + WASM）門檻與原型向量，僅在高風險詞觸發。

```yaml
# database/vocabs/內存.yml
matchOptions:
  skipPhrases:
    - 海內存知己
  context:
    threshold: 0
    features:
      - position: next
        tokens: ["海內存", "海內", "內存"]
        weight: -1
```

### 上下文加權規則詳細

`matchOptions.context` 屬性用於根據詞彙周遭的字詞給分或扣分，以避免單靠片語列舉仍會誤判的情境。支援以下設定：

- `baseScore`: 初始分數（預設為 `0`）。
- `threshold`: 達到此分數才視為命中（預設 `0`，若分數低於門檻視為忽略）。
- `requireSegments`: 若為 `true`、而目前瀏覽器沒有 `Intl.Segmenter`，則直接忽略這項規則（預設 `false`）。
- `maxTokens`: 取用的前後文 token 數量上限（預設 5）。
- `features`: 由多個加權規則構成的陣列，每條規則說明如下：
  - `position` / `positions`: 指定觀察的相對位置，支援 `prev`（前一個 token）、`next`（下一個 token）、`any`／`window`（回顧前後各數個 token）。
  - `distance`: 向前或向後搜尋的距離（以 token 為單位，預設 1，被套用時會以 `distance - 1` 的索引取值）。
  - `tokens`: 觸發本規則的詞彙清單。
  - `weight`: 命中時調整的分數，可為負值（扣分）或正值（加分）。

例如以下設定會在「寄」後面緊接「寄送服務／寄送資料」時扣 1 分，使整體分數低於 `threshold` 因而跳過標記：

```yaml
matchOptions:
  context:
    threshold: 0
    features:
      - position: next
        tokens: ["寄送", "寄送服務", "寄送資料"]
        weight: -1
    uncertainRange:
      min: -0.5
      max: 0.5
    classifier:
      strategy: logreg
      window: 3
      bias: -0.12
      threshold: 0.55
      features:
        token:next:1:寄送: -1.1
        token:prev:1:請: 0.4
```

### 詞彙 YAML 欄位一覽

每筆詞彙資料的主要欄位如下：

- `word`：詞彙本體（必填），需為唯一鍵。
- `bopomofo`：注音，可提高瀏覽器提示卡的辨識度。
- `category`：所屬分類，對應 `cmd/build/entity.VocabCategory`。
- `explicit`：粗暴語言或性相關標記，可選 (`LANGUAGE` 或 `SEXUAL`)。
- `notice`：提示卡會額外顯示的注意事項。
- `description`：詞彙說明，支援多行文字。
- `examples`：建議替換與錯誤範例，結構為：

  ```yaml
  examples:
    - words: [建議詞, …]
      correct: |
        正確例句
      incorrect: |
        錯誤例句
  ```

- `matchOptions`：比對細節。常用欄位：
  - `matchMode`: `"standalone"` 或 `"default"`。
  - `skipPhrases`: 遇到指定片語時跳過標記。
  - `context`: 規則層的上下文加權設定（詳見下節）。
  - `uncertainRange`: `{ min, max }`，將規則分數落在區間內的案例交給模型。
  - `classifier`: 離線訓練輸出的權重，欄位與 `tools/menu_classifier/build_model.py` 輸出一致：
    - `strategy`: 目前為 `logreg`。
    - `window`: 取用前後文 token 數。
    - `bias`、`threshold`: 決策邏輯參數。
    - `features`: 鍵為 `token:<position>:<index>:<word>`，值為權重。
    - `positiveLabel`、`labels`: 標記正負類別。
    - `requireSegments`: 是否僅在 `Intl.Segmenter` 可用時生效。
    - `allowUnknown`: 若規則未命中，是否回傳未知而非直接拒絕。
  - `semantic`: 深層語意分析設定：
    - `model`: ONNX 模型代號。
    - `enabled`: 控制是否啟用。
    - `window`: 語境取樣長度。
    - `threshold`: 餘弦相似度門檻。
    - `highRiskOnly`: 僅在邊界案例啟用。
    - `prototypes`: 參考向量清單，每筆包含 `label`、`vector`、`weight`。

## 斷詞與比對流程

Content script 會優先透過 `Intl.Segmenter('zh-Hant', { granularity: 'word' })` 斷詞，僅針對分出的 token 嘗試比對詞庫，以降低「海內存知己 → 內存」這類誤判。瀏覽器若不支援 `Intl.Segmenter`，才會回退至既有的正則比對邏輯。需要支援的最低版本：Chrome 87、Firefox 114、Edge 87。

## 偵錯工具

若要分析誤判情形，可在選項頁面啟用以下開關：

- **記錄略過片語**：在 Console（需開啟 Verbose Level）輸出 `[invade] skipPhrases`，包含組合後的片語與是否被忽略。
- **記錄斷詞結果**：輸出 `[invade] segments`，揭露每個文字節點的斷詞切分方式。
- **記錄語境權重**：輸出 `[invade] weights`，顯示每個語境特徵的加減分情況與最終分數。
- **在懸浮視窗顯示偵錯資訊**：提示卡會額外列出決策、分數與觸發規則，無須開啟 Console 即可檢視判斷依據。

建議僅在排查時短暫開啟，以免大量輸出或額外資訊影響瀏覽體驗。

## 在 Chrome 載入

1. 開啟 `chrome://extensions`
2. 開啟「開發人員模式」
3. 選擇「載入未封裝項目」
4. 指定 `browser-extension/chrome` 目錄

## 在 Firefox 載入

1. 開啟 `about:debugging#/runtime/this-firefox`
2. 點選「臨時載入附加元件」
3. 選擇 `browser-extension/chrome/manifest.json`
4. 之後可在 `about:addons` 內調整權限或重新載入（Firefox 109 以上）

## 設定項目

擴充套件提供簡易設定頁（`chrome://extensions` → 擴充套件詳細資料 → **擴充功能選項**）：

- **啟用支語標記**：快速開啟或停用整體功能
- **顯示懸浮資訊**：控制是否顯示報章式提示卡
- **套用底色 / 保留底線**：可獨立開關，打造最順眼的標記效果
- **深色／淺色文字底色**：針對不同頁面主題分別設定色調
- **底線樣式**：細調線型以符合版面風格
- **忽略輸入區**：避免在編輯器或表單內干擾
- **忽略詞彙列表**：自訂不需標記的詞彙，每行輸入一個詞彙（大小寫視為相同）

按下「恢復預設值」可以隨時回到原始設定。

## 檔案結構

```
browser-extension/
└── chrome/
    ├── data/              # 由 Go 指令產生的詞彙資料
    ├── icons/             # 擴充套件使用的圖示
    ├── scripts/           # content script 與共用設定
    ├── styles/            # 樣式檔（標示與提示框）
    ├── manifest.json
    ├── options.html/.css/.js
```

歡迎依實際需求調整樣式與提示內容。若要更新詞彙資料，修改 `database/vocabs` 後重新執行資料生成指令即可。
