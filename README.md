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

# PDF2Podcast 腳本生成器

PDF2Podcast 是一個強大的文件轉換工具，能夠將 PDF、TXT 和 EPUB 檔案轉換成生動的對話腳本。此工具特別適合創建 podcast、講座、教學內容或摘要，透過大型語言模型 (LLM) 將靜態文字轉換為引人入勝的對話或演講稿。

## 功能特點

- **多種檔案格式支援**：可處理 PDF、TXT 和 EPUB 檔案
- **多種輸出模板**：
  - Podcast 對話（兩位主持人 David 和 Cordelia）
  - 科學材料發現摘要（教授與學生對話）
  - 講座腳本（單一演講者）
  - 一般摘要（約 1024 字）
  - 簡短摘要（約 256 字）
- **自定義提示詞**：可完全自定義所有提示詞模板
- **彈性 API 整合**：支援 OpenAI API 及其他相容的 API 端點
- **模型選擇**：可從連接的 API 獲取並選擇可用的語言模型
- **繁體中文輸出**：預設生成繁體中文腳本
- **友善的使用者介面**：基於 Gradio 的直觀操作界面

## 安裝指南

### 前置需求

- Python 3.7 或更高版本
- pip 套件管理器

### 安裝步驟

1. 複製此專案到本地：
   ```bash
   git clone https://github.com/yourusername/PDF2podcast.git
   cd PDF2podcast
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

1. 啟動應用程式：
   ```bash
   python app.py
   ```

2. 在瀏覽器中開啟顯示的 URL（通常是 http://127.0.0.1:7860）

3. 上傳您想要轉換的檔案（PDF、TXT 或 EPUB）

4. 設定 API 參數：
   - 輸入 API Base URL（預設為 https://gemini.david888.com/v1）
   - 輸入您的 LLM API 金鑰
   - 點擊「獲取模型列表」按鈕

5. 選擇提示詞模板或自定義提示詞

6. 點擊「生成腳本」按鈕

7. 複製或下載生成的腳本

## 提示詞模板說明

### Podcast 模板
生成兩位主持人（David 和 Cordelia）之間的對話，適合製作 podcast 節目。對話風格模仿 All-In-Podcast，內容豐富且互動性強。

### SciAgents 材料發現摘要
生成教授與學生之間的對話，專注於描述新材料的特性和發現。教授的風格類似理查德·費曼，深入淺出地解釋複雜概念。

### 講座模板
生成單一演講者的講座腳本，風格類似理查德·費曼教授，適合教學或演講場合。

### 摘要模板
生成約 1024 字的內容摘要，保留原文的關鍵點和重要概念。

### 簡短摘要模板
生成約 256 字的簡潔摘要，適合快速了解文件內容。

## 自定義選項

您可以自定義以下提示詞部分：
- **介紹提示詞**：設定整體任務和風格
- **文本分析提示詞**：指導如何分析輸入文本
- **腦力激盪提示詞**：引導創意思考過程
- **前導提示詞**：設定對話或講座的開場
- **對話提示詞**：定義對話的結構和風格
- **自定義提示詞**：添加額外的特定指令

## 依賴套件

主要依賴套件包括：
- gradio：用於創建 Web 介面
- pymupdf：用於 PDF 文件處理
- ebooklib：用於 EPUB 文件處理
- beautifulsoup4：用於 HTML 內容解析
- requests：用於 API 通訊
- python-dotenv：用於環境變數管理

完整依賴列表請參見 `requirements.txt` 檔案。

## 注意事項

- 處理大型檔案可能需要較長時間
- API 使用可能會產生費用，請查閱您使用的 API 提供商的計費政策
- 生成的內容質量取決於所選模型和提供的提示詞

