# GitHub Actions Workflows

## Build Executables

這個工作流程會在每次推送到 master 分支、PR 到 master 分支或手動觸發時，為以下平台預先編譯可執行檔案：

### 支援的平台

- **Linux** (amd64)
- **macOS** (amd64, arm64/Apple Silicon)
- **Windows** (amd64)

### 產生的可執行檔案

1. **baka-invade** - 用於建置網站頁面和封面的工具
2. **invade-mcp-server** - Model Context Protocol (MCP) 伺服器

### 使用方式

#### 手動觸發建置

1. 前往 [Actions](../../actions/workflows/build.yml) 頁面
2. 點擊 "Run workflow" 按鈕
3. 選擇分支並執行

#### 自動建置

- 當推送程式碼到 `master` 分支時會自動觸發
- 當建立 PR 到 `master` 分支時會自動觸發

#### 下載可執行檔案

建置完成後，可以在 Actions 執行頁面的 "Artifacts" 區域下載編譯好的可執行檔案。

### 版本發布

當推送 `v*` 格式的標籤時（例如：`v1.0.0`），工作流程會自動建立 GitHub Release，並將所有平台的可執行檔案附加到 Release 中。

#### 建立發布

```bash
git tag v1.0.0
git push origin v1.0.0
```

發布會自動建立，包含所有平台的可執行檔案。
