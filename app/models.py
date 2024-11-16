from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union
from datetime import datetime
import re

class TextRequest(BaseModel):
    """文本请求模型"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="要分析的中文文本",
        example="这个产品非常好用，我很喜欢！"
    )

    @validator('text')
    def validate_text(cls, v):
        """验证文本是否包含中文"""
        if not re.search('[\u4e00-\u9fff]', v):
            raise ValueError('文本必须包含中文字符')
        return v

class AudioRequest(BaseModel):
    """语音请求模型"""
    audio_url: Optional[str] = Field(
        None,
        description="语音文件URL",
        example="http://example.com/audio.wav"
    )
    audio_base64: Optional[str] = Field(
        None,
        description="Base64编码的语音数据"
    )
    format: str = Field(
        "wav",
        description="音频格式(wav/pcm/amr)",
        example="wav"
    )
    rate: int = Field(
        16000,
        description="采样率",
        example=16000,
        ge=8000,
        le=48000
    )

    @validator('format')
    def validate_format(cls, v):
        allowed_formats = {'wav', 'pcm', 'amr'}
        if v.lower() not in allowed_formats:
            raise ValueError(f'音频格式必须是 {", ".join(allowed_formats)} 之一')
        return v.lower()

class BatchRequest(BaseModel):
    """批量文本请求模型"""
    texts: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="要分析的中文文本列表",
        example=["这个产品非常好用！", "服务态度很差"]
    )

    @validator('texts')
    def validate_texts(cls, v):
        if not all(re.search('[\u4e00-\u9fff]', text) for text in v):
            raise ValueError('所有文本都必须包含中文字符')
        return v

class EmotionWeight(BaseModel):
    """情感权重模型"""
    emotion: str = Field(
        ...,
        description="情感类型",
        example="喜悦"
    )
    weight: float = Field(
        ...,
        description="情感权重",
        ge=0,
        le=1,
        example=0.85
    )
    keywords: List[str] = Field(
        ...,
        description="触发该情感的关键词列表",
        example=["开心", "喜欢", "快乐"]
    )

class AcousticFeatures(BaseModel):
    """语音特征模型"""
    pitch: float = Field(
        ...,
        description="音高特征",
        example=220.0
    )
    volume: float = Field(
        ...,
        description="音量特征",
        example=0.75
    )
    speed: float = Field(
        ...,
        description="语速特征",
        example=1.2
    )
    energy: float = Field(
        ...,
        description="能量特征",
        example=0.85
    )
    rhythm: Optional[float] = Field(
        None,
        description="节奏特征",
        example=0.65
    )

class SentimentResponse(BaseModel):
    """基础情感分析响应模型"""
    sentiment: int = Field(
        ...,
        description="情感极性（0:消极，1:中性，2:积极）",
        example=2,
        ge=0,
        le=2
    )
    confidence: float = Field(
        ...,
        description="分类置信度",
        example=0.95,
        ge=0,
        le=1
    )
    positive_prob: float = Field(
        ...,
        description="积极情感概率",
        example=0.92,
        ge=0,
        le=1
    )
    negative_prob: float = Field(
        ...,
        description="消极情感概率",
        example=0.08,
        ge=0,
        le=1
    )
    text: str = Field(
        ...,
        description="原始文本",
        example="这个产品非常好用，我很喜欢！"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="分析时间戳",
        example="2024-11-16T15:50:00.123456"
    )

class DetailedSentimentResponse(SentimentResponse):
    """详细情感分析响应模型"""
    emotion_weights: List[EmotionWeight] = Field(
        ...,
        description="各种情感的权重分析"
    )
    acoustic_features: Optional[AcousticFeatures] = Field(
        None,
        description="语音特征分析（仅在语音分析时存在）"
    )
    sentences: Optional[List[Dict[str, Union[str, float]]]] = Field(
        None,
        description="分句情感分析结果",
        example=[
            {
                "text": "这个产品非常好用",
                "sentiment": 2,
                "confidence": 0.95
            },
            {
                "text": "我很喜欢",
                "sentiment": 2,
                "confidence": 0.98
            }
        ]
    )

class BatchResponse(BaseModel):
    """批量分析响应模型"""
    results: List[DetailedSentimentResponse] = Field(
        ...,
        description="每条文本的详细分析结果"
    )
    total: int = Field(
        ...,
        description="分析的文本总数",
        example=2,
        ge=1
    )
    average_sentiment: float = Field(
        ...,
        description="平均情感极性",
        example=1.5
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="批量分析的时间戳",
        example="2024-11-16T15:50:00.123456"
    )

class ComparisonResult(BaseModel):
    """文本和语音对比结果模型"""
    text_analysis: DetailedSentimentResponse = Field(
        ...,
        description="文本分析结果"
    )
    audio_analysis: DetailedSentimentResponse = Field(
        ...,
        description="语音分析结果"
    )
    comparison: Dict[str, any] = Field(
        ...,
        description="对比分析结果",
        example={
            "sentiment_difference": {
                "value": 0.5,
                "description": "情感极性差异"
            },
            "confidence_difference": {
                "value": 0.1,
                "description": "置信度差异"
            },
            "emotion_correlation": {
                "text_emotions": ["喜悦", "满意"],
                "audio_emotions": ["喜悦", "兴奋"],
                "common_emotions": ["喜悦"]
            },
            "acoustic_analysis": {
                "energy_level": "高",
                "speed_indication": "快速",
                "pitch_variation": "显著"
            }
        }
    )
    conclusion: str = Field(
        ...,
        description="对比分析结论",
        example="文本和语音情感基本一致，但语音表现出更强的情感强度"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="分析时间戳"
    )

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(
        ...,
        description="错误类型",
        example="ValidationError"
    )
    detail: str = Field(
        ...,
        description="错误详细信息",
        example="文本必须包含中文字符"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="错误发生时间",
        example="2024-11-16T15:50:00.123456"
    )

class WSRequest(BaseModel):
    """WebSocket请求模型"""
    type: str = Field(
        ...,
        description="请求类型(text/audio)",
        example="text"
    )
    data: Union[str, bytes] = Field(
        ...,
        description="文本内容或音频数据"
    )
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="请求时间戳"
    )

class WSResponse(BaseModel):
    """WebSocket响应模型"""
    type: str = Field(
        ...,
        description="响应类型(text_result/audio_result/error)",
        example="text_result"
    )
    data: Union[DetailedSentimentResponse, ErrorResponse] = Field(
        ...,
        description="分析结果或错误信息"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="响应时间戳"
    )

class AnalysisStatistics(BaseModel):
    """分析统计模型"""
    total_requests: int = Field(
        ...,
        description="总请求数",
        example=1000
    )
    average_processing_time: float = Field(
        ...,
        description="平均处理时间（毫秒）",
        example=150.5
    )
    sentiment_distribution: Dict[str, int] = Field(
        ...,
        description="情感分布统计",
        example={
            "积极": 500,
            "中性": 300,
            "消极": 200
        }
    )
    common_emotions: List[Dict[str, Union[str, int]]] = Field(
        ...,
        description="常见情感统计",
        example=[
            {"emotion": "喜悦", "count": 300},
            {"emotion": "满意", "count": 200}
        ]
    )
    update_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="统计更新时间"
    )

class SentimentTrend(BaseModel):
    """情感趋势分析模型"""
    period: str = Field(
        ...,
        description="统计周期",
        example="hourly"
    )
    data_points: List[Dict[str, Union[str, float]]] = Field(
        ...,
        description="趋势数据点",
        example=[
            {
                "timestamp": "2024-11-16T14:00:00",
                "sentiment": 1.8,
                "volume": 120
            }
        ]
    )
    summary: Dict[str, any] = Field(
        ...,
        description="趋势总结",
        example={
            "average_sentiment": 1.5,
            "trend_direction": "上升",
            "peak_time": "2024-11-16T15:00:00"
        }
    )

class RealTimeAnalysis(BaseModel):
    """实时分析结果模型"""
    current_sentiment: float = Field(
        ...,
        description="当前情感值",
        example=1.8
    )
    sentiment_change: float = Field(
        ...,
        description="情感变化值",
        example=0.2
    )
    active_emotions: List[str] = Field(
        ...,
        description="当前活跃的情感",
        example=["喜悦", "期待"]
    )
    acoustic_status: Optional[Dict[str, float]] = Field(
        None,
        description="实时声学特征状态"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="分析时间戳"
    )

class APIUsageStats(BaseModel):
    """API使用统计模型"""
    total_calls: int = Field(
        ...,
        description="总调用次数"
    )
    text_analysis_count: int = Field(
        ...,
        description="文本分析次数"
    )
    audio_analysis_count: int = Field(
        ...,
        description="语音分析次数"
    )
    comparison_count: int = Field(
        ...,
        description="对比分析次数"
    )
    average_response_time: float = Field(
        ...,
        description="平均响应时间"
    )
    error_rate: float = Field(
        ...,
        description="错误率"
    )
    peak_usage_time: str = Field(
        ...,
        description="峰值使用时间"
    )