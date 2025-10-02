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

# 導入自定義模組
from prompts import INSTRUCTION_TEMPLATES, get_template, get_all_template_names
from quality_control import DialogueQualityChecker, validate_dialogue_structure, suggest_improvements
from content_planner import ContentPlanner, SmartContentSplitter, create_adaptive_prompts

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

# 初始化品質控制和內容規劃器
quality_checker = DialogueQualityChecker()
content_planner = ContentPlanner()
content_splitter = SmartContentSplitter()


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
    progress_callback=None,
    template_type: str = "podcast"
) -> str:
    """
    Generate dialogue by making a direct request to the LLM API.
    使用簡化版本，暫時不使用複雜的內容規劃
    """
    logger.info(f"準備生成對話，使用模型: {model}")
    
    # 限制輸入文本長度
    original_length = len(pdf_text)
    if len(pdf_text) > max_input_length:
        pdf_text = pdf_text[:max_input_length]
        logger.info(f"輸入文本已截斷: {original_length} -> {max_input_length} 字符")
    
    logger.info(f"輸入文本長度: {len(pdf_text)} 字符")
    
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
    retry_delay = 5

    # 暫時使用簡化的單次生成
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": base_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 8192
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"發送 API 請求 (嘗試 {attempt+1}/{max_retries})...")
            if progress_callback:
                progress_callback(f"API 請求中 (嘗試 {attempt+1}/{max_retries})...")
                
            response = requests.post(url, headers=headers, json=payload)
            
            # 處理速率限制錯誤
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
                if progress_callback:
                    progress_callback(f"API 錯誤: {response.status_code} {response.reason}")
            
            response.raise_for_status()
            result = response.json()
            generated_content = result['choices'][0]['message']['content']
            
            logger.info("API 請求成功，已收到回應")
            if progress_callback:
                progress_callback("已成功從 LLM 獲取回應")
            
            # 進行品質檢查
            try:
                quality_report = quality_checker.check_dialogue_quality(generated_content, ['speaker-1', 'speaker-2'])
                logger.info(f"品質檢查分數: {quality_report.overall_score:.1f}")
                if progress_callback:
                    progress_callback(f"品質檢查完成，分數: {quality_report.overall_score:.1f}/100")
            except Exception as e:
                logger.warning(f"品質檢查失敗: {e}")
            
            return generated_content
            
        except requests.exceptions.RequestException as e:
            error_msg = f"請求失敗: {str(e)}"
            logger.error(error_msg)
            
            if attempt < max_retries - 1:
                retry_msg = f"將在 {retry_delay} 秒後重試。嘗試 {attempt+1}/{max_retries}"
                logger.info(retry_msg)
                if progress_callback:
                    progress_callback(f"{error_msg} {retry_msg}")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                final_error = f"在 {max_retries} 次嘗試後失敗: {str(e)}"
                logger.error(final_error)
                if progress_callback:
                    progress_callback(final_error)
                return f"Error after {max_retries} attempts: {str(e)}"
    
    return "生成失敗"


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
                        if i % 10 == 0:
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
            progress_callback=progress_callback,
            template_type="podcast"
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
    gr.Markdown("# 腳本生成器 | Script Generator (重構版)", elem_id="header")
    
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
                placeholder="https://generativelanguage.googleapis.com/v1beta/openai",
                value="https://generativelanguage.googleapis.com/v1beta/openai"
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
                choices=get_all_template_names(),
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
                minimum=1,
                maximum=5,
                value=1,
                step=1,
                label="分批生成部分數量 | Number of Generation Parts",
                info="暫時設為1，未來版本將支援智能分批生成"
            )
            
            # 添加最大輸入文本長度的滑動條
            max_input_length_slider = gr.Slider(
                minimum=50000,
                maximum=2000000,
                value=1000000,
                step=50000,
                label="最大輸入文本長度 | Max Input Text Length",
                info="調整模型可處理的最大輸入文本長度（字符數）"
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
        try:
            template_data = get_template(template)
            return [
                template_data["intro"],
                template_data["text_instructions"],
                template_data["scratch_pad"],
                template_data["prelude"],
                template_data["dialog"]
            ]
        except KeyError:
            logger.error(f"模板 {template} 不存在")
            return ["", "", "", "", ""]
    
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
    logger.info("啟動腳本生成器應用 (重構版)")
    demo.launch()