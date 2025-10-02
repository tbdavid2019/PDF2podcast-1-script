---
title: PDF2podcast 1 Script
emoji: 🔥
colorFrom: pink
colorTo: indigo
sdk: gradio
sdk_version: 5.23.2
app_file: app.py
pinned: false
short_description: 原tbdavid2019/PDF2podcast拆出的劇本生成(1)
---
---
title: PDF2podcast 1 Script
emoji: 🔥
colorFrom: pink
colorTo: indigo
sdk: gradio
sdk_version: 5.23.2
app_file: app.py
pinned: false
short_description: 原tbdavid2019/PDF2podcast拆出的劇本生成(1)
---

# PDF2Podcast 腳本生成器 (重構版)

PDF2Podcast 是一個強大的文件轉換工具，能夠將 PDF、TXT 和 EPUB 檔案轉換成生動的對話腳本。此工具特別適合創建 podcast、講座、教學內容或摘要，透過大型語言模型 (LLM) 將靜態文字轉換為引人入勝的對話或演講稿。

## 🚀 最新更新 (2025-10-02)

### 重大架構重構
- **模組化設計**：將原本複雜的單一檔案拆分為多個專業模組
  - `prompts.py`：現代化提示詞管理，採用簡潔高效的設計
  - `quality_control.py`：對話品質檢查和連貫性驗證
  - `content_planner.py`：智能內容規劃和主題導向分段
- **簡化提示詞**：摒棄複雜的多段式提示詞，採用現代 AI 系統最佳實踐

### 核心功能優化
- **解決文稿斷裂問題**：
  - 大幅提升 `max_tokens` 至 65,536 (支援 Gemini Flash 2.5)
  - 智能截斷檢測，自動啟用分批生成備用機制
  - 品質檢查針對完整文稿進行，而非逐批檢查
- **可調整參數**：
  - 最大輸出 Token 數可調整 (1,024 - 131,072)
  - 最大輸入文本長度可調整 (50,000 - 2,000,000 字符)
  - 適配不同模型的限制 (Gemini: 65536, GPT-4: 4096, Claude: 8192)

### 全新摘要功能 📝
- **Podcast Summary 生成**：專為 podcast 上架準備
  - **博客式摘要**：適合搜索引擎收錄的 Markdown 格式文章
  - **極簡摘要**：200 字以內的節目介紹，適合平台描述
- **一鍵生成**：從腳本直接生成多種格式的摘要內容

### 介面優化
- **簡化設計**：隱藏複雜的多段式提示詞欄位
- **專注核心**：保留模板選擇和自定義提示詞功能
- **雙輸出區域**：腳本生成 + 摘要生成並行操作

## 功能特點

- **多種檔案格式支援**：可處理 PDF、TXT 和 EPUB 檔案
- **現代化模板系統**：
  - Podcast 對話（兩位主持人 David 和 Cordelia）
  - 單人播客獨白
  - 科學材料發現摘要（教授與學生對話）
  - 講座腳本（單一演講者）
  - 一般摘要和簡短摘要
  - **新增**：博客式摘要和極簡摘要
- **智能品質控制**：自動檢測對話品質和連貫性
- **彈性 API 整合**：支援 OpenAI API 及其他相容的 API 端點
- **模型選擇**：可從連接的 API 獲取並選擇可用的語言模型
- **繁體中文輸出**：預設生成繁體中文腳本
- **現代化介面**：基於 Gradio 的直觀操作界面

## 技術架構

### 核心模組
```
PDF2podcast-1-script/
├── app.py                 # 主應用程式 (Gradio 介面)
├── prompts.py            # 現代化提示詞管理
├── quality_control.py    # 品質檢查系統
├── content_planner.py    # 內容規劃器
├── requirements.txt      # 依賴清單
└── README.md            # 專案說明
```

### 提示詞設計原則
- **簡潔高效**：摒棄複雜的多段式設計
- **現代化**：採用最新 AI 系統最佳實踐
- **可擴展**：易於添加新模板和自定義內容
- **向後兼容**：保持與舊版本的相容性

## 安裝指南

### 前置需求
- Python 3.7 或更高版本
- pip 套件管理器

### 安裝步驟

1. 複製此專案到本地：
   ```bash
   git clone https://github.com/tbdavid2019/PDF2podcast-1-script.git
   cd PDF2podcast-1-script
   ```

2. 安裝所需依賴：
   ```bash
   pip install -r requirements.txt
   ```

3. 設定 API 金鑰（可選）：
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，添加您的 API 金鑰
   ```

## 使用方法

### 基本操作流程

1. **啟動應用程式**：
   ```bash
   python app.py
   ```

2. **設定 API 參數**：
   - 輸入 API Base URL（預設為 Gemini API）
   - 輸入您的 LLM API 金鑰
   - 點擊「獲取模型列表」按鈕

3. **上傳文件**：支援 PDF、TXT 或 EPUB 格式

4. **選擇模板**：從下拉選單選擇適合的提示詞模板

5. **調整參數**：
   - 最大輸出 Token 數 (建議 Gemini: 65536)
   - 最大輸入文本長度
   - 分批生成部分數量 (通常設為 1)

6. **生成腳本**：點擊「生成腳本」按鈕

7. **生成摘要**：
   - 選擇摘要類型（博客式 / 極簡）
   - 點擊「生成摘要」按鈕

### 進階功能

#### 自定義提示詞
- 在「自定義提示詞」欄位添加特殊要求
- 系統會自動將其整合到主要提示詞中

#### 模型適配建議
- **Gemini Flash 2.5**: max_tokens = 65536 (推薦)
- **GPT-4**: max_tokens = 4096
- **Claude**: max_tokens = 8192
- **其他模型**: 請參考官方文檔

## 提示詞模板說明

### 主要模板

#### Podcast 模板 (推薦)
生成兩位主持人（David 和 Cordelia）之間的對話：
- 開場：「歡迎收聽 David888 Podcast，我是 David...」
- 風格：類似 All-In-Podcast，輕鬆專業
- 長度：50-200 輪對話，根據內容自動調整

#### 單人播客模板
生成單一主持人的播客獨白：
- 風格親切專業，適合深度講解
- 內容豐富且易懂

#### 摘要模板 (新增)
- **博客式摘要**：適合 SEO 的 Markdown 格式文章
- **極簡摘要**：200 字以內的節目介紹

### 科學專用模板
- **SciAgents 材料發現**：專門介紹 AI 材料發現成果
- **講座模板**：費曼風格的教學內容

## 品質控制系統

### 自動檢測功能
- **截斷檢測**：智能識別內容是否被提前截斷
- **連貫性檢查**：驗證對話的邏輯一致性
- **格式驗證**：確保 speaker-1/speaker-2 格式正確
- **品質評分**：提供整體品質評估 (0-100分)

### 備用機制
- 當單次生成被截斷時，自動啟用分批生成
- 智能內容規劃，確保主題連貫性
- 全局品質檢查，而非逐批檢查

## 故障排除

### 常見問題

#### 文稿被截斷
- **解決方案**：提高 max_tokens 設定至模型支援上限
- **Gemini Flash 2.5**: 可設定至 65536
- **自動備用**：系統會自動偵測並啟用分批生成

#### API 連接問題
- 檢查 API 金鑰是否正確
- 確認 API Base URL 格式
- 查看錯誤日誌獲取詳細資訊

#### 品質評分偏低
- 檢查原始內容品質
- 考慮調整提示詞模板
- 嘗試不同的 temperature 設定

## 技術規格

### 支援的模型
- **推薦**: Gemini Flash 2.5 (65536 tokens)
- **相容**: OpenAI GPT 系列、Claude、其他 OpenAI API 相容模型

### 效能規格
- **最大輸入**: 2,000,000 字符
- **最大輸出**: 131,072 tokens (視模型而定)
- **處理速度**: 視模型 API 回應時間而定
- **記憶體需求**: 約 500MB (含依賴)

### 依賴套件
主要依賴套件：
- gradio：Web 介面框架
- pymupdf：PDF 文件處理
- ebooklib：EPUB 文件處理
- beautifulsoup4：HTML 內容解析
- requests：API 通訊
- python-dotenv：環境變數管理

完整依賴列表請參見 `requirements.txt` 檔案。

## 版本歷史

### v2.0.0 (2025-10-02) - 重構版
- 🎯 **重大重構**：模組化架構，分離關注點
- 🚀 **解決斷裂**：提升 token 限制，修復文稿截斷問題  
- 📝 **新增摘要**：Podcast 上架專用的摘要生成功能
- 🎨 **介面優化**：簡化複雜設定，專注核心功能
- ⚙️ **參數化**：可調整輸出 token 限制，適配不同模型
- 🔧 **品質提升**：智能品質檢查和截斷偵測

### v1.x - 初始版本
- 基本的 PDF/EPUB 轉 Podcast 功能
- 複雜的多段式提示詞設計
- 固定的 token 限制

## 貢獻指南

歡迎提交 Issues 和 Pull Requests！

### 開發環境設置
1. Fork 此專案
2. 創建功能分支：`git checkout -b feature/新功能`
3. 提交變更：`git commit -am '添加新功能'`
4. 推送分支：`git push origin feature/新功能`
5. 創建 Pull Request

### 程式碼規範
- 使用 Python PEP 8 風格
- 添加適當的註釋和文檔字符串
- 確保向後相容性

## 授權條款

[在此添加授權資訊]

## 聯絡資訊

- GitHub: https://github.com/tbdavid2019/PDF2podcast-1-script
- Issues: https://github.com/tbdavid2019/PDF2podcast-1-script/issues

## 注意事項

- 處理大型檔案可能需要較長時間
- API 使用可能會產生費用，請查閱您使用的 API 提供商的計費政策
- 生成的內容質量取決於所選模型和提供的提示詞
- 建議在生產環境使用前進行充分測試

