"""
品質管控模組
Quality Control Module

此模組提供對話品質檢查、連貫性驗證、內容分析等功能。
確保生成的對話腳本具有高品質和邏輯連貫性。
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QualityReport:
    """品質檢查報告"""
    overall_score: float  # 0-100 分
    coherence_score: float
    character_consistency_score: float
    content_richness_score: float
    format_compliance_score: float
    issues: List[str]
    suggestions: List[str]


class DialogueQualityChecker:
    """對話品質檢查器"""
    
    def __init__(self):
        self.speaker_patterns = {
            'speaker-1': r'speaker-1:\s*',
            'speaker-2': r'speaker-2:\s*'
        }
        
    def check_dialogue_quality(self, dialogue: str, expected_speakers: List[str] = None) -> QualityReport:
        """
        全面檢查對話品質
        
        Args:
            dialogue: 對話文本
            expected_speakers: 預期的發言者列表
            
        Returns:
            QualityReport: 品質檢查報告
        """
        if expected_speakers is None:
            expected_speakers = ['speaker-1', 'speaker-2']
            
        logger.info("開始進行對話品質檢查")
        
        # 執行各項檢查
        coherence_score = self._check_coherence(dialogue)
        character_score = self._check_character_consistency(dialogue, expected_speakers)
        content_score = self._check_content_richness(dialogue)
        format_score = self._check_format_compliance(dialogue, expected_speakers)
        
        # 計算總分
        overall_score = (coherence_score + character_score + content_score + format_score) / 4
        
        # 收集問題和建議
        issues, suggestions = self._generate_feedback(
            dialogue, coherence_score, character_score, content_score, format_score
        )
        
        report = QualityReport(
            overall_score=overall_score,
            coherence_score=coherence_score,
            character_consistency_score=character_score,
            content_richness_score=content_score,
            format_compliance_score=format_score,
            issues=issues,
            suggestions=suggestions
        )
        
        logger.info(f"品質檢查完成，總分: {overall_score:.1f}")
        return report
    
    def _check_coherence(self, dialogue: str) -> float:
        """檢查對話的邏輯連貫性"""
        lines = [line.strip() for line in dialogue.split('\n') if line.strip()]
        if len(lines) < 5:
            return 30.0  # 對話太短
            
        # 檢查主題切換的自然度
        topic_transitions = 0
        abrupt_changes = 0
        
        for i in range(1, len(lines)):
            prev_line = lines[i-1].lower()
            curr_line = lines[i].lower()
            
            # 簡單的主題連貫性檢查
            if self._is_topic_transition(prev_line, curr_line):
                topic_transitions += 1
                if self._is_abrupt_change(prev_line, curr_line):
                    abrupt_changes += 1
        
        if topic_transitions == 0:
            return 60.0  # 沒有主題變化可能表示內容單調
            
        coherence_ratio = 1 - (abrupt_changes / topic_transitions)
        return max(50.0, coherence_ratio * 100)
    
    def _check_character_consistency(self, dialogue: str, expected_speakers: List[str]) -> float:
        """檢查角色一致性"""
        score = 100.0
        issues = []
        
        # 檢查發言者格式
        for speaker in expected_speakers:
            pattern = self.speaker_patterns.get(speaker, f'{speaker}:\\s*')
            matches = re.findall(pattern, dialogue, re.IGNORECASE)
            
            if not matches:
                score -= 30.0
                issues.append(f"未找到發言者 {speaker}")
        
        # 檢查是否有無效的發言者標記
        valid_patterns = '|'.join([f'{speaker}:' for speaker in expected_speakers])
        invalid_speakers = re.findall(rf'(\w+):\s*(?!{valid_patterns})', dialogue, re.IGNORECASE)
        
        if invalid_speakers:
            score -= len(set(invalid_speakers)) * 10
            issues.append(f"發現無效的發言者標記: {set(invalid_speakers)}")
        
        return max(0.0, score)
    
    def _check_content_richness(self, dialogue: str) -> float:
        """檢查內容豐富度"""
        # 計算對話輪數
        turns = len(re.findall(r'speaker-[12]:', dialogue, re.IGNORECASE))
        
        # 計算平均每輪長度
        lines = dialogue.split('\n')
        content_lines = [line for line in lines if re.match(r'speaker-[12]:', line, re.IGNORECASE)]
        
        if not content_lines:
            return 0.0
            
        avg_length = sum(len(line) for line in content_lines) / len(content_lines)
        
        # 評分標準
        turn_score = min(100, (turns / 50) * 100)  # 50輪為滿分
        length_score = min(100, (avg_length / 200) * 100)  # 200字為滿分
        
        return (turn_score + length_score) / 2
    
    def _check_format_compliance(self, dialogue: str, expected_speakers: List[str]) -> float:
        """檢查格式規範性"""
        score = 100.0
        
        # 檢查是否以正確的開場白開始
        if 'speaker-1:' in dialogue:
            first_speaker_line = re.search(r'speaker-1:\s*(.+)', dialogue, re.IGNORECASE)
            if first_speaker_line:
                first_content = first_speaker_line.group(1).strip()
                if '歡迎收聽' not in first_content or 'David888 Podcast' not in first_content:
                    score -= 20.0
        
        # 檢查是否有不當的格式標記
        if re.search(r'\[Host\]|\[Guest\]|\[.*?\]', dialogue):
            score -= 30.0
        
        # 檢查行格式
        lines = dialogue.split('\n')
        malformed_lines = 0
        for line in lines:
            line = line.strip()
            if line and not re.match(r'speaker-[12]:', line, re.IGNORECASE) and line not in expected_speakers:
                if ':' in line and not line.startswith('#'):  # 可能是格式錯誤的發言
                    malformed_lines += 1
        
        if malformed_lines > 0:
            score -= min(40.0, malformed_lines * 5)
        
        return max(0.0, score)
    
    def _is_topic_transition(self, prev_line: str, curr_line: str) -> bool:
        """判斷是否為主題轉換"""
        transition_keywords = [
            '另外', '接下來', '說到', '談到', '回到', '轉個話題',
            '順便提一下', '相關地', '類似地', '相比之下'
        ]
        
        return any(keyword in curr_line for keyword in transition_keywords)
    
    def _is_abrupt_change(self, prev_line: str, curr_line: str) -> bool:
        """判斷是否為突兀的主題變化"""
        # 簡單的突兀變化檢測
        if len(prev_line) < 10 or len(curr_line) < 10:
            return False
            
        # 這裡可以實現更複雜的語義分析
        # 目前使用簡單的關鍵詞檢查
        common_words = set(prev_line.split()) & set(curr_line.split())
        return len(common_words) < 2
    
    def _generate_feedback(self, dialogue: str, coherence: float, character: float, 
                          content: float, format_score: float) -> Tuple[List[str], List[str]]:
        """生成問題和建議"""
        issues = []
        suggestions = []
        
        if coherence < 70:
            issues.append("對話邏輯連貫性較低")
            suggestions.append("建議增加更自然的主題過渡和銜接詞")
        
        if character < 70:
            issues.append("角色一致性有問題")
            suggestions.append("確保發言者標記格式正確，避免使用無效的角色名稱")
        
        if content < 70:
            issues.append("內容豐富度不足")
            suggestions.append("建議增加對話輪數或每輪的內容深度")
        
        if format_score < 70:
            issues.append("格式規範性不符合要求")
            suggestions.append("檢查開場白格式，移除不當的標記符號")
        
        return issues, suggestions


class ContentCoherenceAnalyzer:
    """內容連貫性分析器"""
    
    def __init__(self):
        self.topic_keywords = {}
        
    def analyze_content_flow(self, dialogue: str) -> Dict[str, float]:
        """分析內容流暢度"""
        lines = [line.strip() for line in dialogue.split('\n') if line.strip()]
        
        # 提取主要話題
        topics = self._extract_topics(dialogue)
        
        # 分析話題分布
        topic_distribution = self._analyze_topic_distribution(lines, topics)
        
        # 計算流暢度分數
        flow_score = self._calculate_flow_score(topic_distribution)
        
        return {
            'flow_score': flow_score,
            'topic_count': len(topics),
            'topic_distribution': topic_distribution
        }
    
    def _extract_topics(self, dialogue: str) -> List[str]:
        """提取對話中的主要話題"""
        # 簡單的關鍵詞提取
        # 在實際應用中可以使用更精密的NLP技術
        common_topics = [
            '技術', '科學', '研究', '發現', '材料', '實驗',
            '理論', '應用', '未來', '發展', '創新', '挑戰'
        ]
        
        found_topics = []
        for topic in common_topics:
            if topic in dialogue:
                found_topics.append(topic)
        
        return found_topics
    
    def _analyze_topic_distribution(self, lines: List[str], topics: List[str]) -> Dict[str, int]:
        """分析話題分布"""
        distribution = {topic: 0 for topic in topics}
        
        for line in lines:
            for topic in topics:
                if topic in line:
                    distribution[topic] += 1
        
        return distribution
    
    def _calculate_flow_score(self, topic_distribution: Dict[str, int]) -> float:
        """計算流暢度分數"""
        if not topic_distribution:
            return 50.0
        
        # 話題分布的均勻度
        values = list(topic_distribution.values())
        if max(values) == 0:
            return 50.0
        
        uniformity = 1 - (max(values) - min(values)) / max(values)
        return uniformity * 100


def validate_dialogue_structure(dialogue: str, template_type: str = 'podcast') -> bool:
    """
    驗證對話結構是否符合模板要求
    
    Args:
        dialogue: 對話文本
        template_type: 模板類型
        
    Returns:
        bool: 是否符合結構要求
    """
    if template_type == 'podcast':
        # 檢查是否有兩個發言者
        has_speaker1 = 'speaker-1:' in dialogue
        has_speaker2 = 'speaker-2:' in dialogue
        
        # 檢查開場白
        has_opening = '歡迎收聽' in dialogue and 'David888 Podcast' in dialogue
        
        return has_speaker1 and has_speaker2 and has_opening
    
    elif template_type == 'podcast-single':
        # 檢查是否只有一個發言者
        has_speaker1 = 'speaker-1:' in dialogue
        has_speaker2 = 'speaker-2:' in dialogue
        
        # 檢查開場白
        has_opening = '歡迎收聽' in dialogue and 'David888 Podcast' in dialogue
        
        return has_speaker1 and not has_speaker2 and has_opening
    
    return True  # 其他模板暫不檢查


def suggest_improvements(quality_report: QualityReport) -> List[str]:
    """
    根據品質報告提供改進建議
    
    Args:
        quality_report: 品質檢查報告
        
    Returns:
        List[str]: 改進建議列表
    """
    suggestions = quality_report.suggestions.copy()
    
    if quality_report.overall_score < 60:
        suggestions.append("整體品質較低，建議重新生成並調整提示詞")
    
    if quality_report.coherence_score < 60:
        suggestions.append("增加內容規劃步驟，確保邏輯流暢")
    
    if quality_report.character_consistency_score < 60:
        suggestions.append("檢查角色定義，確保發言風格一致")
    
    if quality_report.content_richness_score < 60:
        suggestions.append("增加內容深度和對話互動性")
    
    return list(set(suggestions))  # 去重