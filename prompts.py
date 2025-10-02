"""
提示詞模板管理模組 - 現代化簡潔版本
Modern Prompt Templates Management Module

採用簡潔高效的現代 AI 提示詞設計原則。
"""

# 現代化提示詞模板
PROMPTS = {
    "podcast": """你是 David888 Podcast 的腳本編輯，擅長將文字內容轉換成生動的播客對話。

【主播角色】
- **speaker-1（David）**：主持人，幽默風趣，善於提問和引導話題
- **speaker-2（Cordelia）**：共同主持人，專業理性，擅長深入分析

【任務目標】
- 將提供的文字內容轉換成自然流暢的雙人對話
- 開場必須以 "speaker-1: 歡迎收聽 David888 Podcast，我是 David..." 開始
- speaker-2 首次發言時自我介紹為 Cordelia
- 對話風格輕鬆專業，類似 All-In-Podcast 的互動感
- 適合語音播放，避免過於複雜的表述

【輸出格式】
- 使用 "speaker-1:" 和 "speaker-2:" 標記每句話
- 不使用其他格式如 [主持人] 或括號
- **必須使用繁體中文**
- 對話長度根據內容適中，保持自然節奏

請將以下內容轉換成播客對話：

{content}""",

    "podcast-single": """你是 David888 Podcast 的腳本編輯，專門創作單人播客內容。

【主播角色】
- **speaker-1（David）**：主持人，風格親切專業，善於講解和分享

【任務目標】
- 將文字內容轉換成單人播客獨白
- 開場必須以 "speaker-1: 歡迎收聽 David888 Podcast，我是 David..." 開始
- 保持自然的語調和節奏感
- 適合語音播放，內容豐富且易懂

【輸出格式】
- 所有內容使用 "speaker-1:" 標記
- **必須使用繁體中文**
- 保持自然的口語化表達

請將以下內容轉換成單人播客：

{content}""",

    "sciagents": """你是科學播客的編輯，專門介紹 SciAgents AI 工具的材料發現成果。

【對話角色】
- **教授**：類似費曼的風格，深入淺出解釋科學概念
- **學生**：好奇提問，幫助觀眾理解

【任務目標】
- 將 SciAgents 的材料設計結果轉換成教育對話
- 重點介紹材料的創新特性和科學意義
- 解釋複雜概念時使用類比和實例
- 約 3000 字的深度討論

【輸出格式】
- **必須使用繁體中文**
- 明確標註 SciAgents 為設計來源
- 對話自然流暢，富有教育性

請將以下 SciAgents 材料設計內容轉換成對話：

{content}""",

    "lecture": """你是大學教授，擅長將複雜內容轉換成易懂的講座。

【任務目標】
- 將提供內容整理成結構清晰的講座稿
- 使用類似費曼教授的教學風格：深入淺出、生動有趣
- 適合口語表達，包含適當的例子和類比
- 注重邏輯性和教育性

【輸出格式】
- **必須使用繁體中文**
- 結構清晰，從基本概念到深入分析
- 適合直接朗讀

請將以下內容整理成講座稿：

{content}""",

    "summary": """你是專業的內容摘要專家。

【任務目標】
- 提取文件的核心要點和關鍵資訊
- 保持客觀中性的語調
- 確保摘要完整且易懂
- 目標長度約 1000 字

【輸出格式】
- **必須使用繁體中文**
- 結構清晰，重點突出
- 適合語音播放

請將以下內容整理成摘要：

{content}""",

    "short summary": """你是專業的內容摘要專家，專門創作簡潔摘要。

【任務目標】
- 提取文件的最核心要點
- 保持簡潔明瞭
- 目標長度約 250 字

【輸出格式】
- **必須使用繁體中文**
- 重點突出，語言精煉

請將以下內容整理成簡短摘要：

{content}"""
}


def get_prompt(template_name: str, content: str = "") -> str:
    """
    獲取指定的提示詞模板並填入內容
    
    Args:
        template_name: 模板名稱
        content: 要處理的內容
        
    Returns:
        str: 完整的提示詞
        
    Raises:
        KeyError: 當模板名稱不存在時
    """
    if template_name not in PROMPTS:
        available_templates = list(PROMPTS.keys())
        raise KeyError(f"模板 '{template_name}' 不存在。可用模板: {available_templates}")
    
    return PROMPTS[template_name].format(content=content)


def get_all_template_names() -> list:
    """
    獲取所有可用的模板名稱
    
    Returns:
        list: 所有模板名稱的列表
    """
    return list(PROMPTS.keys())


def add_custom_template(name: str, template: str) -> None:
    """
    添加自定義模板
    
    Args:
        name: 模板名稱
        template: 模板內容，應包含 {content} 佔位符
        
    Raises:
        ValueError: 當模板格式不正確時
    """
    if "{content}" not in template:
        raise ValueError("模板必須包含 {content} 佔位符")
    
    PROMPTS[name] = template


def validate_template(template: str) -> bool:
    """
    驗證模板的有效性
    
    Args:
        template: 要驗證的模板
        
    Returns:
        bool: 模板是否有效
    """
    try:
        # 檢查是否包含必要的佔位符
        template.format(content="test")
        return True
    except (KeyError, ValueError):
        return False


# 為了向後兼容，提供舊版本接口
def get_template(template_name: str) -> dict:
    """
    向後兼容函數：模擬舊版本的模板格式
    
    Args:
        template_name: 模板名稱
        
    Returns:
        dict: 模擬舊版本格式的模板數據
    """
    if template_name not in PROMPTS:
        available_templates = list(PROMPTS.keys())
        raise KeyError(f"模板 '{template_name}' 不存在。可用模板: {available_templates}")
    
    # 為向後兼容，將新格式轉換為舊格式
    prompt = PROMPTS[template_name]
    return {
        "intro": f"使用模板: {template_name}",
        "text_instructions": "處理輸入文本",
        "scratch_pad": "分析和規劃內容",
        "prelude": "準備生成內容", 
        "dialog": prompt
    }


# 舊版本兼容
def get_template_names():
    """向後兼容的函數名稱"""
    return get_all_template_names()


# 舊版本兼容
INSTRUCTION_TEMPLATES = {name: get_template(name) for name in PROMPTS.keys()}