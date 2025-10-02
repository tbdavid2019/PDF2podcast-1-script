"""
內容規劃模組
Content Planning Module

此模組提供智能內容分析、主題提取、對話結構規劃等功能。
幫助生成更連貫、有組織的長篇對話內容。
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class ContentSegment:
    """內容片段"""
    title: str
    content: str
    keywords: List[str]
    estimated_length: int
    priority: int  # 1-10, 10為最重要


@dataclass
class ContentOutline:
    """內容大綱"""
    main_topic: str
    segments: List[ContentSegment]
    total_estimated_length: int
    suggested_parts: int


class ContentAnalyzer:
    """內容分析器"""
    
    def __init__(self):
        self.stopwords = {
            '的', '了', '和', '是', '在', '有', '這', '個', '一', '我', '你', '他',
            '她', '它', '們', '我們', '你們', '他們', '也', '都', '很', '更', '最',
            '可以', '能夠', '應該', '需要', '必須', '會', '將', '要', '來', '去',
            '說', '講', '談', '看', '聽', '想', '覺得', '認為', '以為', '知道'
        }
    
    def analyze_content(self, text: str) -> Dict[str, any]:
        """
        分析文本內容，提取關鍵信息
        
        Args:
            text: 輸入文本
            
        Returns:
            Dict: 分析結果
        """
        logger.info("開始分析文本內容")
        
        # 基本統計
        word_count = len(text)
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # 提取關鍵詞
        keywords = self._extract_keywords(text)
        
        # 識別主題
        main_topics = self._identify_main_topics(text, keywords)
        
        # 分析文本結構
        structure = self._analyze_structure(text)
        
        # 估算適合的對話長度
        estimated_rounds = self._estimate_dialogue_rounds(word_count)
        
        result = {
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'keywords': keywords[:20],  # 取前20個關鍵詞
            'main_topics': main_topics,
            'structure': structure,
            'estimated_rounds': estimated_rounds,
            'complexity_score': self._calculate_complexity(text)
        }
        
        logger.info(f"內容分析完成：{word_count}字，{paragraph_count}段落，{len(keywords)}個關鍵詞")
        return result
    
    def _extract_keywords(self, text: str, top_k: int = 50) -> List[str]:
        """提取關鍵詞"""
        # 簡單的關鍵詞提取（基於詞頻）
        words = re.findall(r'[\u4e00-\u9fff]+', text)  # 提取中文詞彙
        words = [word for word in words if len(word) >= 2 and word not in self.stopwords]
        
        word_freq = Counter(words)
        return [word for word, freq in word_freq.most_common(top_k)]
    
    def _identify_main_topics(self, text: str, keywords: List[str]) -> List[str]:
        """識別主要主題"""
        # 基於關鍵詞聚類的簡單主題識別
        topic_patterns = {
            '科技': ['技術', '科學', '研究', '創新', '發明', '實驗', '理論', '方法'],
            '商業': ['公司', '市場', '產品', '服務', '客戶', '銷售', '營收', '策略'],
            '教育': ['學習', '教學', '知識', '學生', '老師', '課程', '教育', '培訓'],
            '健康': ['健康', '醫療', '疾病', '治療', '藥物', '醫生', '病人', '醫院'],
            '環境': ['環境', '氣候', '污染', '保護', '生態', '自然', '能源', '綠色'],
            '社會': ['社會', '文化', '政治', '經濟', '人民', '國家', '法律', '制度'],
            '歷史': ['歷史', '古代', '傳統', '文化', '事件', '人物', '時代', '發展']
        }
        
        topics = []
        for topic, patterns in topic_patterns.items():
            score = sum(1 for keyword in keywords if any(pattern in keyword for pattern in patterns))
            if score > 0:
                topics.append((topic, score))
        
        # 按分數排序並返回前5個主題
        topics.sort(key=lambda x: x[1], reverse=True)
        return [topic for topic, score in topics[:5]]
    
    def _analyze_structure(self, text: str) -> Dict[str, int]:
        """分析文本結構"""
        lines = text.split('\n')
        
        # 計算不同類型的內容
        headers = len([line for line in lines if self._is_header(line)])
        lists = len([line for line in lines if self._is_list_item(line)])
        tables = text.count('|')  # 簡單的表格檢測
        
        return {
            'headers': headers,
            'lists': lists,
            'tables': tables,
            'sections': max(1, headers)  # 至少有一個章節
        }
    
    def _is_header(self, line: str) -> bool:
        """判斷是否為標題行"""
        line = line.strip()
        return (line.startswith('#') or 
                (len(line) < 50 and line.endswith('：')) or
                re.match(r'^\d+\.', line) or
                re.match(r'^[一二三四五六七八九十]+、', line))
    
    def _is_list_item(self, line: str) -> bool:
        """判斷是否為列表項"""
        line = line.strip()
        return (line.startswith('•') or 
                line.startswith('-') or 
                line.startswith('*') or
                re.match(r'^\d+\)', line))
    
    def _estimate_dialogue_rounds(self, word_count: int) -> int:
        """估算對話輪數"""
        # 假設每輪對話平均300-500字
        avg_words_per_round = 400
        return max(10, min(200, word_count // avg_words_per_round))
    
    def _calculate_complexity(self, text: str) -> float:
        """計算文本複雜度 (0-100)"""
        # 基於多個因素計算複雜度
        factors = []
        
        # 詞彙豐富度
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        unique_words = len(set(words))
        total_words = len(words)
        vocab_richness = unique_words / max(1, total_words) if total_words > 0 else 0
        factors.append(vocab_richness * 100)
        
        # 句子長度變化
        sentences = re.split(r'[。！？]', text)
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            length_variance = sum((l - avg_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
            factors.append(min(100, length_variance / 10))
        
        # 專業術語密度
        technical_terms = self._count_technical_terms(text)
        term_density = (technical_terms / max(1, total_words)) * 1000
        factors.append(min(100, term_density))
        
        return sum(factors) / len(factors) if factors else 50.0
    
    def _count_technical_terms(self, text: str) -> int:
        """計算專業術語數量"""
        technical_patterns = [
            r'[A-Z]{2,}',  # 縮寫
            r'\d+\.?\d*%',  # 百分比
            r'\d+\.?\d*[A-Za-z]+',  # 帶單位的數字
            r'[a-zA-Z]+tion',  # -tion結尾的詞
            r'[a-zA-Z]+ism',  # -ism結尾的詞
        ]
        
        count = 0
        for pattern in technical_patterns:
            count += len(re.findall(pattern, text))
        
        return count


class ContentPlanner:
    """內容規劃器"""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
    
    def create_content_outline(self, text: str, target_rounds: int = None) -> ContentOutline:
        """
        創建內容大綱
        
        Args:
            text: 輸入文本
            target_rounds: 目標對話輪數
            
        Returns:
            ContentOutline: 內容大綱
        """
        logger.info("開始創建內容大綱")
        
        # 分析內容
        analysis = self.analyzer.analyze_content(text)
        
        if target_rounds is None:
            target_rounds = analysis['estimated_rounds']
        
        # 提取主要主題
        main_topic = analysis['main_topics'][0] if analysis['main_topics'] else "一般主題"
        
        # 分割內容為段落
        segments = self._create_content_segments(text, analysis, target_rounds)
        
        # 計算總長度和建議部分數
        total_length = sum(seg.estimated_length for seg in segments)
        suggested_parts = self._calculate_suggested_parts(target_rounds)
        
        outline = ContentOutline(
            main_topic=main_topic,
            segments=segments,
            total_estimated_length=total_length,
            suggested_parts=suggested_parts
        )
        
        logger.info(f"內容大綱創建完成：{len(segments)}個片段，建議{suggested_parts}個部分")
        return outline
    
    def _create_content_segments(self, text: str, analysis: Dict, target_rounds: int) -> List[ContentSegment]:
        """創建內容片段"""
        # 根據段落和主題分割內容
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            paragraphs = [text]
        
        segments = []
        keywords = analysis['keywords']
        avg_rounds_per_segment = max(1, target_rounds // max(1, len(paragraphs)))
        
        for i, paragraph in enumerate(paragraphs):
            # 提取段落關鍵詞
            para_keywords = [kw for kw in keywords if kw in paragraph][:5]
            
            # 生成標題
            title = self._generate_segment_title(paragraph, para_keywords, i + 1)
            
            # 估算長度（以對話輪數計算）
            estimated_length = max(1, min(len(paragraph) // 200, avg_rounds_per_segment * 2))
            
            # 計算優先級
            priority = self._calculate_segment_priority(paragraph, keywords)
            
            segment = ContentSegment(
                title=title,
                content=paragraph,
                keywords=para_keywords,
                estimated_length=estimated_length,
                priority=priority
            )
            
            segments.append(segment)
        
        return segments
    
    def _generate_segment_title(self, content: str, keywords: List[str], index: int) -> str:
        """生成段落標題"""
        # 嘗試從內容中提取現有標題
        lines = content.split('\n')
        for line in lines[:3]:  # 檢查前3行
            if self.analyzer._is_header(line):
                return line.strip().replace('#', '').replace('：', '').strip()
        
        # 如果沒有標題，根據關鍵詞生成
        if keywords:
            main_keyword = keywords[0]
            return f"關於{main_keyword}的討論"
        
        return f"第{index}部分討論"
    
    def _calculate_segment_priority(self, content: str, global_keywords: List[str]) -> int:
        """計算段落優先級 (1-10)"""
        # 基於關鍵詞密度和內容長度
        keyword_count = sum(1 for kw in global_keywords[:10] if kw in content)
        length_score = min(5, len(content) // 500)
        
        priority = min(10, max(1, keyword_count + length_score))
        return priority
    
    def _calculate_suggested_parts(self, target_rounds: int) -> int:
        """計算建議的生成部分數"""
        # 基於目標輪數計算最佳部分數
        # 每部分理想輪數約50-80輪
        if target_rounds <= 50:
            return 1
        elif target_rounds <= 100:
            return 2
        elif target_rounds <= 150:
            return 3
        elif target_rounds <= 200:
            return 4
        else:
            return max(4, min(8, target_rounds // 50))


class SmartContentSplitter:
    """智能內容分割器"""
    
    def __init__(self):
        self.planner = ContentPlanner()
    
    def split_for_generation(self, outline: ContentOutline, num_parts: int) -> List[Dict]:
        """
        為生成過程分割內容
        
        Args:
            outline: 內容大綱
            num_parts: 分割部分數
            
        Returns:
            List[Dict]: 每個部分的生成指令
        """
        logger.info(f"將內容分割為{num_parts}個部分")
        
        segments = outline.segments
        total_segments = len(segments)
        
        if total_segments == 0:
            return [{"segments": [], "focus": "一般討論", "rounds": 67}]
        
        # 計算每部分的段落分配
        segments_per_part = max(1, total_segments // num_parts)
        parts = []
        
        for i in range(num_parts):
            start_idx = i * segments_per_part
            
            if i == num_parts - 1:  # 最後一部分包含所有剩餘段落
                end_idx = total_segments
            else:
                end_idx = min((i + 1) * segments_per_part, total_segments)
            
            part_segments = segments[start_idx:end_idx]
            
            if not part_segments:  # 如果沒有分配到段落，跳過
                continue
            
            # 計算這部分的焦點主題
            focus_keywords = []
            total_rounds = 0
            
            for segment in part_segments:
                focus_keywords.extend(segment.keywords)
                total_rounds += segment.estimated_length
            
            # 確定主要焦點
            if focus_keywords:
                keyword_counts = Counter(focus_keywords)
                main_focus = keyword_counts.most_common(1)[0][0]
                focus = f"重點討論{main_focus}相關內容"
            else:
                focus = f"第{i+1}部分的深入討論"
            
            # 確保每部分至少有合理的輪數
            rounds = max(30, min(80, total_rounds))
            
            part_info = {
                "segments": part_segments,
                "focus": focus,
                "rounds": rounds,
                "part_index": i,
                "is_first": i == 0,
                "is_last": i == num_parts - 1,
                "content_summary": self._create_content_summary(part_segments)
            }
            
            parts.append(part_info)
        
        logger.info(f"內容分割完成，共{len(parts)}個有效部分")
        return parts
    
    def _create_content_summary(self, segments: List[ContentSegment]) -> str:
        """創建內容摘要"""
        if not segments:
            return "一般討論內容"
        
        main_keywords = []
        for segment in segments:
            main_keywords.extend(segment.keywords[:2])  # 每個段落取前2個關鍵詞
        
        # 去重並取前5個
        unique_keywords = list(dict.fromkeys(main_keywords))[:5]
        
        if unique_keywords:
            return f"主要討論：{', '.join(unique_keywords)}"
        else:
            return f"討論{segments[0].title}等相關主題"


def create_adaptive_prompts(outline: ContentOutline, part_info: Dict, base_template: Dict) -> Dict[str, str]:
    """
    根據內容大綱創建自適應提示詞
    
    Args:
        outline: 內容大綱
        part_info: 部分信息
        base_template: 基礎模板
        
    Returns:
        Dict: 調整後的提示詞
    """
    adapted_prompts = base_template.copy()
    
    # 根據內容調整對話指令
    if part_info["is_first"]:
        # 第一部分：完整開場
        adapted_prompts["dialog"] += f"""
        
特別注意：這是對話的開始部分，請確保：
1. 以標準開場白開始：「歡迎收聽 David888 Podcast，我是 David...」
2. 主要討論內容：{part_info['focus']}
3. 生成約{part_info['rounds']}輪對話
4. 為後續討論建立良好基礎
"""
    
    elif part_info["is_last"]:
        # 最後部分：總結收尾
        adapted_prompts["dialog"] += f"""
        
特別注意：這是對話的最後部分，請確保：
1. 繼續前面的對話，不要重複開場白
2. 主要討論內容：{part_info['focus']}
3. 生成約{part_info['rounds']}輪對話
4. 在最後幾輪自然總結整個討論
5. 以適當的告別語結束
"""
    
    else:
        # 中間部分：承上啟下
        adapted_prompts["dialog"] += f"""
        
特別注意：這是對話的中間部分，請確保：
1. 自然承接前面的討論
2. 主要討論內容：{part_info['focus']}
3. 生成約{part_info['rounds']}輪對話
4. 為後續討論預留空間，不要過早總結
"""
    
    return adapted_prompts