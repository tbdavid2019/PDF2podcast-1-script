import concurrent.futures as cf
import glob
import io
import os
import time
import warnings
from pathlib import Path
from typing import List, Literal
import gradio as gr
import requests
from dotenv import load_dotenv
import pymupdf
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

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
    
    The dialogue must proceed for at least 100 rounds (one round is completed after speaker A finishes speaking and speaker B responds). In each round, at least one speaker must deliver detailed content (around 300-500 words), offering 2-3 subtopics for the other speaker to explore further. At the end of a turn, pass the conversation with a question, rebuttal, or topic extension, for example:
        - \"Cordelia, 你同意我的觀點嗎？還是你有不同看法？\"
        - \"David, 你覺得這個還有什麼隱藏的機會？\"
    Speakers can interrupt each other, insert personal experiences, or present challenges to simulate a genuine spontaneous discussion, maintaining a relaxed yet insightful atmosphere.
    After every 5 rounds,  briefly summarize key points discussed so far before naturally transitioning to a new topic.
    Design the dialogue for audio conversion (it will be directly read aloud), maintaining the humor, sharpness, and interactive feel typical of the  All-In-Podcast .
    
    At the end of the dialogue, have the two speakers naturally summarize the main insights and takeaways. 
    Avoid making it sound like an obvious recap; the goal is to gently reinforce the central ideas one last time before signing off.
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
    user_feedback: str = None
) -> str:
    """
    Generate dialogue by making a direct request to the LLM API.
    """
    merged_content = f"""
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

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": merged_content
            }
        ],
        "temperature": 0.7,
        "max_tokens": 999999
    }

    base_url = api_base.rstrip("/")
    url = f"{base_url}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

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
    user_feedback
):
    """驗證輸入並生成腳本"""
    if not files:
        return None, "Please upload at least one PDF file before generating script."

    try:
        # 從檔案中提取文字
        combined_text = ""
        for file in files:
            filename = file.name.lower()

            if filename.endswith(".pdf"):
                doc = pymupdf.open(file.name)
                for page in doc:
                    combined_text += page.get_text() + "\n\n"

            elif filename.endswith(".txt"):
                with open(file.name, "r", encoding="utf-8", errors="ignore") as f:
                    combined_text += f.read() + "\n\n"

            elif filename.endswith(".epub"):
                book = epub.read_epub(file.name)
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                        combined_text += soup.get_text() + "\n\n"
            else:
                print(f"Skipping unsupported file format: {filename}")

        # 生成對話腳本
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
            user_feedback=user_feedback
        )

        return script, None

    except Exception as e:
        return None, str(e)

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
            
            
        
        with gr.Column(scale=1):
            # 輸出區
            generate_button = gr.Button("生成腳本 | Generate Script", , elem_id="generate-btn")
            
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
        if not key:
            return gr.update(choices=[], value=None), gr.update(visible=True, value="Error: API key is required")
        models = fetch_models(key, base)
        if isinstance(models, list) and models and not models[0].startswith("Error"):
            return gr.update(choices=models, value=models[0]), gr.update(visible=False)
        return gr.update(choices=[], value=None), gr.update(visible=True, value=models[0])
    
    def update_template(template):
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
        script, error = validate_and_generate_script(*args)
        if error:
            return None, gr.update(visible=True, value=error)
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
            custom_prompt  # user_feedback
        ],
        outputs=[output_text, error_output]
    )

if __name__ == "__main__":
    demo.launch()