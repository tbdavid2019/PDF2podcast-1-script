import concurrent.futures as cf
import glob
import io
import os
import time
import warnings
import logging
from pathlib import Path
from typing import List, Literal
import gradio as gr
import requests
from dotenv import load_dotenv
import pymupdf
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 忽略 ebooklib 的警告
warnings.filterwarnings('ignore', category=UserWarning, module='ebooklib.epub')
warnings.filterwarnings('ignore', category=FutureWarning, module='ebooklib.epub')

load_dotenv()

# Define multiple sets of instruction templates
INSTRUCTION_TEMPLATES = {
    "podcast": {
        "intro": """Your task is to take the input text provided and turn it into a lively, engaging, informative podcast dialogue in the style of All-In-Podcast. 
    The input text may be messy or unstructured, as it could come from a variety of sources like PDFs ePUBS or web pages.
    We have exactly two speakers in this conversation:
    - speaker-1 (he introduces himself as David)
    - speaker-2 (she introduces herself as Cordelia)
    The conversation must **open** with speaker-1 saying:
    「歡迎來到 David888 Podcast，我是 David...」
    After that, speaker-2 should introduce herself as Cordelia in her first speaking turn.
    Please label each statement or line with speaker-1: or speaker-2: (all lower case, followed by a colon).
    Do not use any other role or bracket placeholders like [Host] or [Guest].
    Don't worry about formatting issues or irrelevant information; your goal is to extract the key points, identify definitions, and interesting facts that could be discussed in a podcast.
    Define all terms used carefully for a broad audience of listeners.
    輸出文字為繁體中文，請注意。
    """,
        "text_instructions": "First, carefully read through the input text ...",
        "scratch_pad": """Brainstorm creative ways ...""",
        "prelude": """Now that you have brainstormed ...""",
        "dialog": """Write a very long, engaging, informative podcast dialogue here, based on the key points and creative ideas you came up with during the brainstorming session.
    Use a **two-speaker** conversational format with exactly:
    - "speaker-1:" (David)
    - "speaker-2:" (Cordelia)
    - The first line must begin with speaker-1: 歡迎來到 David888 Podcast，我是 David...
    - When speaker-2 first speaks, she should introduce herself as Cordelia.
    Alternate turns naturally to simulate an engaging back-and-forth conversation. 
    Do not include bracket placeholders like [Host] or [Guest]; only use speaker-1: or speaker-2: to start each line.
    Design your output to be read aloud, as it will be directly converted into audio. 
    
    The dialogue must proceed for at least 67 rounds (one round is completed after speaker A finishes speaking and speaker B responds). In each round, at least one speaker must deliver detailed content (around 300-500 words), offering 2-3 subtopics for the other speaker to explore further. At the end of a turn, pass the conversation with a question, rebuttal, or topic extension, for example:
        - \"Cordelia, 你同意我的觀點嗎？還是你有不同看法？\"
        - \"David, 你覺得這個還有什麼隱藏的機會？\"
    Speakers can interrupt each other, insert personal experiences, or present challenges to simulate a genuine spontaneous discussion, maintaining a relaxed yet insightful atmosphere.    
    Design the dialogue for audio conversion (it will be directly read aloud), maintaining the humor, sharpness, and interactive feel typical of the  All-In-Podcast .
    

    請使用繁體中文撰寫。
    """
    },
    "SciAgents material discovery summary": {
        "intro": """Your task is to take the input text provided and turn it into a lively, engaging conversation between a professor and a student in a panel discussion that describes a new material. The professor acts like Richard Feynman, but you never mention the name.
        The input text is the result of a design developed by SciAgents, an AI tool for scientific discovery that has come up with a detailed materials design.
        Don't worry about the formatting issues or any irrelevant information; your goal is to extract the key points, identify definitions, and interesting facts that could be discussed in a podcast.
        Define all terms used carefully for a broad audience of listeners.
        """,
        "text_instructions": "First, carefully read through the input text and identify the main topics, key points, and any interesting facts or anecdotes. Think about how you could present this information in a fun, engaging way that would be suitable for a high quality presentation.",
        "scratch_pad": """Brainstorm creative ways to discuss the main topics and key points you identified in the material design summary, especially paying attention to design features developed by SciAgents. Consider using analogies, examples, storytelling techniques, or hypothetical scenarios to make the content more relatable and engaging for listeners.
        Keep in mind that your description should be accessible to a general audience, so avoid using too much jargon or assuming prior knowledge of the topic. If necessary, think of ways to briefly explain any complex concepts in simple terms.
        Use your imagination to fill in any gaps in the input text or to come up with thought-provoking questions that could be explored in the podcast. The goal is to create an informative and entertaining dialogue, so feel free to be creative in your approach.
        Define all terms used clearly and spend effort to explain the background.
        Write your brainstorming ideas and a rough outline for the podcast dialogue here. Be sure to note the key insights and takeaways you want to reiterate at the end.
        Make sure to make it fun and exciting. You never refer to the podcast, you just discuss the discovery and you focus on the new material design only.
        """,
        "prelude": """Now that you have brainstormed ideas and created a rough outline, it's time to write the actual podcast dialogue. Aim for a natural, conversational flow between the host and any guest speakers. Incorporate the best ideas from your brainstorming session and make sure to explain any complex topics in an easy-to-understand way.
    """,
        "dialog": """Write a very long, engaging, informative dialogue here, based on the key points and creative ideas you came up with during the brainstorming session. The presentation must focus on the novel aspects of the material design, behavior, and all related aspects.
    Use a conversational tone and include any necessary context or explanations to make the content accessible to a general audience, but make it detailed, logical, and technical so that it has all necessary aspects for listeners to understand the material and its unexpected properties.
    Remember, this describes a design developed by SciAgents, and this must be explicitly stated for the listeners.
    Never use made-up names for the hosts and guests, but make it an engaging and immersive experience for listeners. Do not include any bracketed placeholders like [Host] or [Guest]. Design your output to be read aloud -- it will be directly converted into audio.
    Make the dialogue as long and detailed as possible with great scientific depth, while still staying on topic and maintaining an engaging flow. Aim to use your full output capacity to create the longest podcast episode you can, while still communicating the key information from the input text in an entertaining way.
    At the end of the dialogue, have the host and guest speakers naturally summarize the main insights and takeaways from their discussion. This should flow organically from the conversation, reiterating the key points in a casual, conversational manner. Avoid making it sound like an obvious recap - the goal is to reinforce the central ideas one last time before signing off.
    The conversation should have around 3000 words. 請用**繁體中文**輸出文稿
    """
    },
    "lecture": {
        "intro": """You are Professor Richard Feynman. Your task is to develop a script for a lecture. You never mention your name.
    The material covered in the lecture is based on the provided text.
    Don't worry about the formatting issues or any irrelevant information; your goal is to extract the key points, identify definitions, and interesting facts that need to be covered in the lecture.
    Define all terms used carefully for a broad audience of students.
    """,
        "text_instructions": "First, carefully read through the input text and identify the main topics, key points, and any interesting facts or anecdotes. Think about how you could present this information in a fun, engaging way that would be suitable for a high quality presentation.",
        "scratch_pad": """
    Brainstorm creative ways to discuss the main topics and key points you identified in the input text. Consider using analogies, examples, storytelling techniques, or hypothetical scenarios to make the content more relatable and engaging for listeners.
    Keep in mind that your lecture should be accessible to a general audience, so avoid using too much jargon or assuming prior knowledge of the topic. If necessary, think of ways to briefly explain any complex concepts in simple terms.
    Use your imagination to fill in any gaps in the input text or to come up with thought-provoking questions that could be explored in the podcast. The goal is to create an informative and entertaining dialogue, so feel free to be creative in your approach.
    Define all terms used clearly and spend effort to explain the background.
    Write your brainstorming ideas and a rough outline for the lecture here. Be sure to note the key insights and takeaways you want to reiterate at the end.
    Make sure to make it fun and exciting.
    """,
        "prelude": """Now that you have brainstormed ideas and created a rough outline, it's time to write the actual podcast dialogue. Aim for a natural, conversational flow between the host and any guest speakers. Incorporate the best ideas from your brainstorming session and make sure to explain any complex topics in an easy-to-understand way.
    """,
        "dialog": """Write a very long, engaging, informative script here, based on the key points and creative ideas you came up with during the brainstorming session. Use a conversational tone and include any necessary context or explanations to make the content accessible to the students.
    Include clear definitions and terms, and examples.
    Do not include any bracketed placeholders like [Host] or [Guest]. Design your output to be read aloud -- it will be directly converted into audio.
    There is only one speaker, you, the professor. Stay on topic and maintaining an engaging flow. Aim to use your full output capacity to create the longest lecture you can, while still communicating the key information from the input text in an engaging way.
    At the end of the lecture, naturally summarize the main insights and takeaways from the lecture. This should flow organically from the conversation, reiterating the key points in a casual, conversational manner.
    Avoid making it sound like an obvious recap - the goal is to reinforce the central ideas covered in this lecture one last time before class is over.
    請用**繁體中文**輸出文稿
    """
    },
    "summary": {
        "intro": """Your task is to develop a summary of a paper. You never mention your name.
        Don't worry about the formatting issues or any irrelevant information; your goal is to extract the key points, identify definitions, and interesting facts that need to be summarized.
        Define all terms used carefully for a broad audience.
        """,
        "text_instructions": "First, carefully read through the input text and identify the main topics, key points, and key facts. Think about how you could present this information in an accurate summary.",
        "scratch_pad": """Brainstorm creative ways to present the main topics and key points you identified in the input text. Consider using analogies, examples, or hypothetical scenarios to make the content more relatable and engaging for listeners.
        Keep in mind that your summary should be accessible to a general audience, so avoid using too much jargon or assuming prior knowledge of the topic. If necessary, think of ways to briefly explain any complex concepts in simple terms. Define all terms used clearly and spend effort to explain the background.
        Write your brainstorming ideas and a rough outline for the summary here. Be sure to note the key insights and takeaways you want to reiterate at the end.
        Make sure to make it engaging and exciting.
        """,
        "prelude": """Now that you have brainstormed ideas and created a rough outline, it is time to write the actual summary. Aim for a natural, conversational flow between the host and any guest speakers. Incorporate the best ideas from your brainstorming session and make sure to explain any complex topics in an easy-to-understand way.
        """,
        "dialog": """Write a a script here, based on the key points and creative ideas you came up with during the brainstorming session. Use a conversational tone and include any necessary context or explanations to make the content accessible to the the audience.
        Start your script by stating that this is a summary, referencing the title or headings in the input text. If the input text has no title, come up with a succinct summary of what is covered to open.
        Include clear definitions and terms, and examples, of all key issues.
        Do not include any bracketed placeholders like [Host] or [Guest]. Design your output to be read aloud -- it will be directly converted into audio.
        There is only one speaker, you. Stay on topic and maintaining an engaging flow.
        Naturally summarize the main insights and takeaways from the summary. This should flow organically from the conversation, reiterating the key points in a casual, conversational manner.
        The summary should have around 1024 words. 請用**繁體中文**輸出文稿
        """
    },
    "short summary": {
        "intro": """Your task is to develop a summary of a paper. You never mention your name.
        Don't worry about the formatting issues or any irrelevant information; your goal is to extract the key points, identify definitions, and interesting facts that need to be summarized.
        Define all terms used carefully for a broad audience.
        """,
        "text_instructions": "First, carefully read through the input text and identify the main topics, key points, and key facts. Think about how you could present this information in an accurate summary.",
        "scratch_pad": """Brainstorm creative ways to present the main topics and key points you identified in the input text. Consider using analogies, examples, or hypothetical scenarios to make the content more relatable and engaging for listeners.
        Keep in mind that your summary should be accessible to a general audience, so avoid using too much jargon or assuming prior knowledge of the topic. If necessary, think of ways to briefly explain any complex concepts in simple terms. Define all terms used clearly and spend effort to explain the background.
        Write your brainstorming ideas and a rough outline for the summary here. Be sure to note the key insights and takeaways you want to reiterate at the end.
        Make sure to make it engaging and exciting.
        """,
        "prelude": """Now that you have brainstormed ideas and created a rough outline, it is time to write the actual summary. Aim for a natural, conversational flow between the host and any guest speakers. Incorporate the best ideas from your brainstorming session and make sure to explain any complex topics in an easy-to-understand way.
        """,
        "dialog": """Write a a script here, based on the key points and creative ideas you came up with during the brainstorming session. Keep it concise, and use a conversational tone and include any necessary context or explanations to make the content accessible to the the audience.
        Start your script by stating that this is a summary, referencing the title or headings in the input text. If the input text has no title, come up with a succinct summary of what is covered to open.
        Include clear definitions and terms, and examples, of all key issues.
        Do not include any bracketed placeholders like [Host] or [Guest]. Design your output to be read aloud -- it will be directly converted into audio.
        There is only one speaker, you. Stay on topic and maintaining an engaging flow.
        Naturally summarize the main insights and takeaways from the short summary. This should flow organically from the conversation, reiterating the key points in a casual, conversational manner.
        The summary should have around 256 words. 請用**繁體中文**輸出文稿
        """
    }
}

def fetch_models(api_key, api_base=None):
    """
    Fetch the list of models from the given API base.
    """
    base_url = api_base.rstrip("/") + "/models" if api_base else "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            models = response.json().get('data', [])
            return [model['id'] for model in models]
        else:
            return [f"Error fetching models: {response.status_code} {response.reason}"]
    except requests.RequestException as e:
        return [f"Error fetching models: {str(e)}"]

def generate_dialogue_via_requests(
    pdf_text: str,
    intro_instructions: str,
    text_instructions: str,
    scratch_pad_instructions: str,
    prelude_dialog: str,
    podcast_dialog_instructions: str,
    model: str,
    llm_api_key: str,
    api_base: str,
    edited_transcript: str = None,
    user_feedback: str = None,
    num_parts: int = 3,
    max_input_length: int = 1000000,
    progress_callback=None
) -> str:
    """
    Generate dialogue by making a direct request to the LLM API.
    Includes retry logic for handling rate limits and supports long content generation.
    """
    logger.info(f"準備生成對話，使用模型: {model}")
    # 限制輸入文本長度
    original_length = len(pdf_text)
    if len(pdf_text) > max_input_length:
        pdf_text = pdf_text[:max_input_length]
        logger.info(f"輸入文本已截斷: {original_length} -> {max_input_length} 字符")
    
    logger.info(f"輸入文本長度: {len(pdf_text)} 字符")
    
    # 始終使用分批生成，因為模型可以處理大量輸入（990000 tokens）但輸出有限制（8192 tokens）
    use_continuation = True
    
    # 基於目標輸出長度（200輪對話）來確定部分數量
    # 假設每輪對話平均需要約100個標記，200輪對話約需要20,000個標記
    # 考慮到API的標記限制（通常為8,192），我們將200輪對話分成固定的部分數
    
    # 使用傳入的 num_parts 參數，每部分固定生成約67輪對話
    # 如果是其他類型的輸出（非podcast），則可能需要更少的部分
    if "podcast" not in podcast_dialog_instructions.lower():
        num_parts = min(2, num_parts)  # 非podcast最多使用2部分
    
    # 每部分固定生成約67輪對話
    rounds_per_part = 67
    
    # 計算總共會生成的對話輪數
    total_rounds = num_parts * rounds_per_part
    
    logger.info(f"將生成約 {total_rounds} 輪對話，分成 {num_parts} 個部分，每部分約 {rounds_per_part} 輪")
    
    # 基本提示詞
    base_prompt = f"""
以下是從 PDF 中擷取的文字內容，請參考並納入對話:
================================
{pdf_text}
================================
{intro_instructions}
{text_instructions}
<scratchpad>
{scratch_pad_instructions}
</scratchpad>
{prelude_dialog}
<podcast_dialogue>
{podcast_dialog_instructions}
</podcast_dialogue>
{edited_transcript or ""}
{user_feedback or ""}
"""

    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json"
    }

    base_url = api_base.rstrip("/")
    url = f"{base_url}/chat/completions"
    logger.info(f"準備發送請求到 API: {url}")
    
    if progress_callback:
        progress_callback("正在發送請求到 LLM API...")

    # 重試參數
    max_retries = 5
    retry_delay = 5  # 初始延遲秒數
    
    # 如果不需要分批生成，直接生成完整內容
    if not use_continuation:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": base_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 8192  # 增加 token 限制
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"發送 API 請求 (嘗試 {attempt+1}/{max_retries})...")
                if progress_callback:
                    progress_callback(f"API 請求中 (嘗試 {attempt+1}/{max_retries})...")
                    
                response = requests.post(url, headers=headers, json=payload)
                
                # 處理速率限制錯誤
                if response.status_code == 429:
                    # 獲取 Retry-After 頭信息，如果有的話
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    logger.warning(f"速率限制錯誤 (429)。將在 {retry_after} 秒後重試。嘗試 {attempt+1}/{max_retries}")
                    if progress_callback:
                        progress_callback(f"速率限制錯誤 (429)。將在 {retry_after} 秒後重試...")
                    time.sleep(retry_after)
                    # 增加下次重試的延遲（指數退避）
                    retry_delay *= 2
                    continue
                    
                # 記錄其他錯誤狀態碼
                if response.status_code != 200:
                    logger.error(f"API 請求失敗: 狀態碼 {response.status_code}, 原因: {response.reason}")
                    if progress_callback:
                        progress_callback(f"API 錯誤: {response.status_code} {response.reason}")
                
                response.raise_for_status()
                result = response.json()
                logger.info("API 請求成功，已收到回應")
                if progress_callback:
                    progress_callback("已成功從 LLM 獲取回應")
                return result['choices'][0]['message']['content']
                
            except requests.exceptions.RequestException as e:
                error_msg = f"請求失敗: {str(e)}"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    retry_msg = f"將在 {retry_delay} 秒後重試。嘗試 {attempt+1}/{max_retries}"
                    logger.info(retry_msg)
                    if progress_callback:
                        progress_callback(f"{error_msg} {retry_msg}")
                    time.sleep(retry_delay)
                    # 增加下次重試的延遲（指數退避）
                    retry_delay *= 2
                else:
                    final_error = f"在 {max_retries} 次嘗試後失敗: {str(e)}"
                    logger.error(final_error)
                    if progress_callback:
                        progress_callback(final_error)
                    return f"Error after {max_retries} attempts: {str(e)}"
    
    # 分批生成長對話
    else:
        logger.info("檢測到需要生成長對話，將使用分批生成方式")
        if progress_callback:
            progress_callback(f"檢測到需要生成長對話，將使用分批生成方式 (估計需要 {num_parts} 個部分)...")
        
        # 初始化對話部分列表
        dialogue_parts = []
        combined_dialogue = ""
        
        # 生成各個部分
        for part_index in range(num_parts):
            is_first_part = part_index == 0
            is_last_part = part_index == num_parts - 1
            
            # 根據部分索引生成適當的提示詞
            if is_first_part:
                # 第一部分：生成開場白和前面的對話
                part_prompt = base_prompt + f"""
請生成對話的開場白和約{rounds_per_part}輪對話。確保對話開始符合要求，並且內容連貫。

重要提示：
1. 這只是對話的開始部分，不是完整對話
2. 絕對不要在這部分結束對話或做總結
3. 不要出現任何形式的告別語或結束語，如「謝謝收聽」、「下次再見」等
4. 對話應該在一個開放的問題或討論點上暫停，表明還有更多內容要討論
"""
                part_description = f"第一部分（開場白和前{rounds_per_part}輪對話）"
            elif is_last_part:
                # 最後一部分：生成結尾和總結
                part_prompt = base_prompt + f"""
以下是已生成的對話前面部分，請繼續生成約{rounds_per_part}輪對話並在最後提供總結，確保對話自然結束：

{combined_dialogue[-8000:]}

重要提示：
1. 這是對話的最後一部分（第 {part_index+1}/{num_parts} 部分）
2. 請在此部分的最後（不是中間）結束對話
3. 在對話的最後幾輪中，兩位講者應該自然地總結主要見解和要點
4. 總結應該自然融入對話，避免讓它聽起來像明顯的總結
5. 目標是在結束前最後一次溫和地強調核心觀點
6. 最後可以適當地加入告別語，如「謝謝收聽」、「下次再見」等
7. 請確保在生成約{rounds_per_part}輪對話後才結束，不要過早結束
8. 不要重複開場白「歡迎來到 David888 Podcast，我是 David...」，直接繼續前面的對話
9. 忽略原始提示詞中關於開場白的指示，因為這不是對話的開始部分
"""
                part_description = f"最後部分（結尾和總結，約{rounds_per_part}輪）"
            else:
                # 中間部分：繼續對話，不要結束
                part_prompt = base_prompt + f"""
以下是已生成的對話前面部分，請繼續生成約{rounds_per_part}輪對話，保持內容連貫：

{combined_dialogue[-8000:]}

重要提示：
1. 這是對話的第 {part_index+1}/{num_parts} 部分，不是最後一部分
2. 絕對不要在這部分結束對話或做總結
3. 不要出現任何形式的告別語或結束語，如「謝謝收聽」、「下次再見」等
4. 不要有任何暗示對話即將結束的表述
5. 對話應該在一個開放的問題或討論點上暫停，表明還有更多內容要討論
6. 不要重複開場白「歡迎來到 David888 Podcast，我是 David...」，直接繼續前面的對話
7. 忽略原始提示詞中關於開場白的指示，因為這不是對話的開始部分
"""
                part_description = f"第 {part_index+1}/{num_parts} 部分（中間約{rounds_per_part}輪對話）"
            
            # 設置請求參數
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": part_prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 8192
            }
            
            # 獲取當前部分
            current_part = ""
            for attempt in range(max_retries):
                try:
                    logger.info(f"發送 {part_description} API 請求 (嘗試 {attempt+1}/{max_retries})...")
                    if progress_callback:
                        progress_callback(f"生成對話 {part_description} (嘗試 {attempt+1}/{max_retries})...")
                    
                    response = requests.post(url, headers=headers, json=payload)
                    
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', retry_delay))
                        logger.warning(f"速率限制錯誤 (429)。將在 {retry_after} 秒後重試。嘗試 {attempt+1}/{max_retries}")
                        if progress_callback:
                            progress_callback(f"速率限制錯誤 (429)。將在 {retry_after} 秒後重試...")
                        time.sleep(retry_after)
                        retry_delay *= 2
                        continue
                    
                    if response.status_code != 200:
                        logger.error(f"API 請求失敗: 狀態碼 {response.status_code}, 原因: {response.reason}")
                    
                    response.raise_for_status()
                    result = response.json()
                    current_part = result['choices'][0]['message']['content']
                    logger.info(f"成功獲取對話 {part_description}")
                    if progress_callback:
                        progress_callback(f"成功獲取對話 {part_description}")
                    break
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"請求失敗: {str(e)}")
                    if attempt < max_retries - 1:
                        logger.info(f"將在 {retry_delay} 秒後重試。嘗試 {attempt+1}/{max_retries}")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        error_msg = f"Error generating {part_description} after {max_retries} attempts: {str(e)}"
                        if combined_dialogue:
                            return combined_dialogue + "\n\n" + error_msg
                        else:
                            return error_msg
            
            # 添加當前部分到對話中
            dialogue_parts.append(current_part)
            if combined_dialogue:
                combined_dialogue += "\n\n" + current_part
            else:
                combined_dialogue = current_part
            
            # 記錄進度
            logger.info(f"已完成 {part_index+1}/{num_parts} 部分，當前總長度: {len(combined_dialogue)} 字符")
            if progress_callback:
                progress_callback(f"已完成 {part_index+1}/{num_parts} 部分，當前總長度: {len(combined_dialogue)} 字符")
        
        # 返回完整對話
        logger.info(f"成功生成完整對話，總長度: {len(combined_dialogue)} 字符，共 {num_parts} 個部分")
        if progress_callback:
            progress_callback(f"成功生成完整對話！總長度: {len(combined_dialogue)} 字符")
        
        return combined_dialogue

def validate_and_generate_script(
    files,
    openai_api_key,
    text_model,
    api_base_value,
    intro_instructions,
    text_instructions,
    scratch_pad_instructions,
    prelude_dialog,
    podcast_dialog_instructions,
    edited_transcript,
    user_feedback,
    num_parts=3,
    max_input_length=1000000,
    progress_callback=None
):
    """驗證輸入並生成腳本"""
    if not files:
        logger.warning("未上傳文件")
        if progress_callback:
            progress_callback("錯誤：請上傳至少一個文件")
        return None, "請在生成腳本前上傳至少一個文件。"

    try:
        logger.info(f"開始處理 {len(files)} 個文件")
        if progress_callback:
            progress_callback(f"開始處理 {len(files)} 個文件...")
        
        # 從檔案中提取文字
        combined_text = ""
        for file in files:
            filename = file.name.lower()
            logger.info(f"處理文件: {filename}")
            if progress_callback:
                progress_callback(f"處理文件: {os.path.basename(filename)}")

            if filename.endswith(".pdf"):
                try:
                    logger.info(f"使用 PyMuPDF 開啟 PDF: {filename}")
                    doc = pymupdf.open(file.name)
                    page_count = len(doc)
                    logger.info(f"PDF 頁數: {page_count}")
                    
                    for i, page in enumerate(doc):
                        page_text = page.get_text()
                        combined_text += page_text + "\n\n"
                        if i % 10 == 0:  # 每10頁記錄一次進度
                            logger.debug(f"已處理 PDF 第 {i+1}/{page_count} 頁")
                            if progress_callback and page_count > 10:
                                progress_callback(f"處理 PDF: {os.path.basename(filename)} - {i+1}/{page_count} 頁")
                    
                    logger.info(f"PDF 處理完成: {filename}")
                    if progress_callback:
                        progress_callback(f"PDF 處理完成: {os.path.basename(filename)}")
                except Exception as e:
                    error_msg = f"PDF 處理錯誤 ({filename}): {str(e)}"
                    logger.error(error_msg)
                    if progress_callback:
                        progress_callback(error_msg)

            elif filename.endswith(".txt"):
                try:
                    logger.info(f"處理文本文件: {filename}")
                    with open(file.name, "r", encoding="utf-8", errors="ignore") as f:
                        file_text = f.read()
                        combined_text += file_text + "\n\n"
                        logger.info(f"文本文件處理完成，長度: {len(file_text)} 字符")
                        if progress_callback:
                            progress_callback(f"文本文件處理完成: {os.path.basename(filename)}")
                except Exception as e:
                    error_msg = f"TXT 文件處理錯誤 ({filename}): {str(e)}"
                    logger.error(error_msg)
                    if progress_callback:
                        progress_callback(error_msg)

            elif filename.endswith(".epub"):
                try:
                    logger.info(f"處理 EPUB 文件: {filename}")
                    if progress_callback:
                        progress_callback(f"處理 EPUB 文件: {os.path.basename(filename)}")
                    
                    book = epub.read_epub(file.name)
                    item_count = len(list(book.get_items()))
                    processed_count = 0
                    
                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            try:
                                processed_count += 1
                                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                                item_text = soup.get_text()
                                combined_text += item_text + "\n\n"
                                logger.debug(f"已處理 EPUB 項目 {processed_count}/{item_count}")
                                if processed_count % 5 == 0 and progress_callback:
                                    progress_callback(f"處理 EPUB: {os.path.basename(filename)} - {processed_count}/{item_count} 項目")
                            except Exception as e:
                                logger.error(f"EPUB 項目處理錯誤: {str(e)}")
                    
                    logger.info(f"EPUB 處理完成: {filename}, 共處理 {processed_count} 個項目")
                    if progress_callback:
                        progress_callback(f"EPUB 處理完成: {os.path.basename(filename)}, 共處理 {processed_count} 個項目")
                except Exception as e:
                    error_msg = f"EPUB 處理錯誤 ({filename}): {str(e)}"
                    logger.error(error_msg)
                    if progress_callback:
                        progress_callback(error_msg)
            else:
                logger.warning(f"跳過不支持的文件格式: {filename}")
                if progress_callback:
                    progress_callback(f"跳過不支持的文件格式: {os.path.basename(filename)}")

        text_length = len(combined_text)
        logger.info(f"所有文件處理完成，合併文本長度: {text_length} 字符")
        if progress_callback:
            progress_callback(f"所有文件處理完成，合併文本長度: {text_length} 字符")

        # 生成對話腳本
        logger.info("開始生成腳本...")
        if progress_callback:
            progress_callback("開始生成腳本，正在發送請求到 LLM API...")
            
        script = generate_dialogue_via_requests(
            pdf_text=combined_text,
            intro_instructions=intro_instructions,
            text_instructions=text_instructions,
            scratch_pad_instructions=scratch_pad_instructions,
            prelude_dialog=prelude_dialog,
            podcast_dialog_instructions=podcast_dialog_instructions,
            model=text_model,
            llm_api_key=openai_api_key,
            api_base=api_base_value,
            edited_transcript=edited_transcript,
            user_feedback=user_feedback,
            num_parts=num_parts,
            max_input_length=max_input_length,
            progress_callback=progress_callback
        )

        logger.info("腳本生成完成")
        if progress_callback:
            progress_callback("腳本生成完成！")
        return script, None

    except Exception as e:
        error_msg = f"腳本生成過程中發生錯誤: {str(e)}"
        logger.error(error_msg)
        if progress_callback:
            progress_callback(error_msg)
        return None, error_msg

# Gradio 介面
with gr.Blocks(title="Script Generator", css="""
    #generate-btn {
        background-color: #FF9800 !important;
        color: white !important;
    }
    #header { text-align: center; margin-bottom: 20px; }
    .error { color: red; }
""") as demo:
    gr.Markdown("# 腳本生成器 | Script Generator", elem_id="header")
    
    with gr.Row():
        with gr.Column(scale=1):
            # 輸入區
            files = gr.Files(
                label="上傳檔案 | Upload Files",
                file_types=[".pdf", ".txt", ".epub"],
                file_count="multiple",
                interactive=True
            )
            
            api_base = gr.Textbox(
                label="API Base URL",
                placeholder="https://gemini.joinit.tw/v1",
                value="https://gemini.joinit.tw/v1"
            )
            
            api_key = gr.Textbox(
                label="LLM API Key",
                type="password"
            )
            
            model_dropdown = gr.Dropdown(
                label="選擇模型 | Select Model",
                choices=[],
                interactive=True
            )
            
            fetch_button = gr.Button("獲取模型列表 | Fetch Models")
            
            template_dropdown = gr.Dropdown(
                label="提示詞模板 | Prompt Template",
                choices=list(INSTRUCTION_TEMPLATES.keys()),
                value="podcast",
                interactive=True
            )
            
            intro_text = gr.Textbox(
                label="介紹提示詞 | Intro Instructions",
                lines=5,
                value=INSTRUCTION_TEMPLATES["podcast"]["intro"],
                interactive=True
            )
            
            text_instructions = gr.Textbox(
                label="文本分析提示詞 | Text Instructions",
                lines=5,
                value=INSTRUCTION_TEMPLATES["podcast"]["text_instructions"],
                interactive=True
            )
            
            scratch_pad = gr.Textbox(
                label="腦力激盪提示詞 | Scratch Pad",
                lines=5,
                value=INSTRUCTION_TEMPLATES["podcast"]["scratch_pad"],
                interactive=True
            )
            
            prelude = gr.Textbox(
                label="前導提示詞 | Prelude",
                lines=5,
                value=INSTRUCTION_TEMPLATES["podcast"]["prelude"],
                interactive=True
            )
            
            dialog = gr.Textbox(
                label="對話提示詞 | Dialog Instructions",
                lines=5,
                value=INSTRUCTION_TEMPLATES["podcast"]["dialog"],
                interactive=True
            )
            
            custom_prompt = gr.Textbox(
                label="自定義提示詞 | Custom Prompt",
                placeholder="Optional: Enter your custom prompt here",
                lines=5
            )
            
            # 添加分批生成部分數量的滑動條
            num_parts_slider = gr.Slider(
                minimum=2,
                maximum=9,
                value=3,
                step=1,
                label="分批生成部分數量 | Number of Generation Parts",
                info="調整生成部分的數量（2-9）。每部分生成約67輪對話，部分越多，總對話輪數越多。模型會讀取完整輸入文本（最多2000000 字符）。"
            )
            
            # 添加最大輸入文本長度的滑動條
            max_input_length_slider = gr.Slider(
                minimum=50000,
                maximum=2000000,
                value=1000000,
                step=50000,
                label="最大輸入文本長度 | Max Input Text Length",
                info="調整模型可處理的最大輸入文本長度（字符數）。增加此值可處理更長的文本，但可能需要更多資源。"
            )
            
        
        with gr.Column(scale=1):
            # 輸出區
            generate_button = gr.Button("生成腳本 | Generate Script", elem_id="generate-btn")
            
            output_text = gr.Textbox(
                label="生成的腳本 | Generated Script",
                lines=30,
                show_copy_button=True
            )
            
            error_output = gr.Markdown(
                visible=False,
                elem_classes=["error"]
            )
    
    # 事件處理
    def handle_model_fetch(key, base):
        logger.info(f"嘗試從 {base} 獲取模型列表")
        if not key:
            logger.warning("未提供 API 密鑰")
            return gr.update(choices=[], value=None), gr.update(visible=True, value="錯誤: 需要 API 密鑰")
        
        models = fetch_models(key, base)
        
        if isinstance(models, list) and models and not models[0].startswith("Error"):
            logger.info(f"成功獲取 {len(models)} 個模型")
            return gr.update(choices=models, value=models[0]), gr.update(visible=False)
        
        error_msg = models[0] if models else "未知錯誤"
        logger.error(f"獲取模型失敗: {error_msg}")
        return gr.update(choices=[], value=None), gr.update(visible=True, value=error_msg)
    
    def update_template(template):
        logger.info(f"切換模板至: {template}")
        template_data = INSTRUCTION_TEMPLATES[template]
        return [
            template_data["intro"],
            template_data["text_instructions"],
            template_data["scratch_pad"],
            template_data["prelude"],
            template_data["dialog"]
        ]
    
    fetch_button.click(
        fn=handle_model_fetch,
        inputs=[api_key, api_base],
        outputs=[model_dropdown, error_output]
    )
    
    template_dropdown.change(
        fn=update_template,
        inputs=[template_dropdown],
        outputs=[intro_text, text_instructions, scratch_pad, prelude, dialog]
    )
    
    def handle_script_generation(*args):
        logger.info("開始生成腳本")
        logger.info(f"使用分批生成部分數量: {args[11]}")  # num_parts_slider 的值
        logger.info(f"最大輸入文本長度: {args[12]} 字符")  # max_input_length_slider 的值
        script, error = validate_and_generate_script(*args)
        if error:
            logger.error(f"腳本生成失敗: {error}")
            return None, gr.update(visible=True, value=error)
        logger.info("腳本生成成功")
        return script, gr.update(visible=False)
    
    generate_button.click(
        fn=handle_script_generation,
        inputs=[
            files,
            api_key,
            model_dropdown,
            api_base,
            intro_text,
            text_instructions,
            scratch_pad,
            prelude,
            dialog,
            gr.Textbox(value=""),  # edited_transcript
            custom_prompt,  # user_feedback
            num_parts_slider,  # 添加滑動條參數
            max_input_length_slider  # 添加最大輸入文本長度參數
        ],
        outputs=[output_text, error_output]
    )

if __name__ == "__main__":
    logger.info("啟動腳本生成器應用")
    demo.launch()