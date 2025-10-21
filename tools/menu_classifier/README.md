# Menu Classifier Toolkit

This folder contains the offline tooling that produces learned weights for ambiguous vocabularies (e.g. `菜單`). The workflow:

1. Collect labelled sentences that contain the target vocab in different contexts and store them in JSONL (`data/*.jsonl`).
2. Run `train_all.py` to train balanced logistic regression classifiers and export the weights to `output/context_models.json`.
3. Execute `go run ./cmd/build extension` so the build step merges the generated weights into `browser-extension/chrome/data/vocabs.json`.

## Requirements

- Python 3.9+
- `pip install jieba scikit-learn numpy`

## Training

所有語料一次處理即可：

```bash
python3 train_all.py
```

可用 `--only 菜單 質量` 指定部分目標，或用 `--output some/path.json` 改寫輸出位置。若需忽略檔案內的 `meta` 設定，可加 `--ignore-meta`。

> 若只想處理特定詞彙，請使用 `--only` 篩選。

## Data Format

每個 `*_contexts.jsonl` 檔案的第一行可以提供 `meta` 設定：

```json
{"meta":{"target":"菜單","positive_label":"technology","window":3,"threshold":0.55,"uncertain_min":-0.5,"uncertain_max":0.5}}
```

後續行則為帶有 `label`、`text`、`source` 的樣本，例如：

```json
{"label":"technology","text":"按下右上角的菜單列展開系統控制。","source":"sample"}
```

其中 `label` 代表語境類別、`text` 是原始句子內容，`source` 可以紀錄資料來源（可省略）。

## Output Payload

`build_model.py` writes a structure compatible with `cmd/build/entity.VocabMatchContext`:

```json
{
  "菜單": {
    "classifier": {
      "strategy": "logreg",
      "window": 3,
      "bias": -0.184732,
      "threshold": 0.5,
      "features": {
        "token:prev:1:設定": 1.02413,
        "token:next:1:選單": 0.84271,
        "token:window:餐廳": -0.90321
      },
      "labels": ["food", "technology"],
      "positiveLabel": "technology",
      "featureNorm": "binary",
      "requireSegments": true,
      "allowUnknown": true,
      "metadata": {
        "...": "..."
      }
    },
    "uncertainRange": {
      "min": -0.5,
      "max": 0.5
    }
  }
}
```

The build stage merges this payload into the matching vocab entry. The content script then evaluates the classifier whenever the rule-based context score falls within the `uncertainRange`.

## Semantic Embeddings

The current script only handles the TF‑IDF/logistic regression layer. A follow-up tool will export quantised sentence-transformer prototypes (`semantic` payload) once the ONNX model is finalised.
