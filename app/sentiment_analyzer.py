import requests
import json
import time
import base64
import numpy as np
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from fastapi import HTTPException
from .config import settings, SENTIMENT_CONFIG
from .models import (
    EmotionWeight,
    AcousticFeatures,
    DetailedSentimentResponse,
    SentimentResponse,
    ComparisonResult,
    SentimentTrend,
    RealTimeAnalysis
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self):
        self.API_KEY = settings.BAIDU_API_KEY
        self.SECRET_KEY = settings.BAIDU_SECRET_KEY
        self.TOKEN_URL = settings.BAIDU_TOKEN_URL
        self.SENTIMENT_URL = settings.BAIDU_SENTIMENT_URL
        self.ASR_URL = settings.BAIDU_ASR_URL

        # API 配置
        self.API_KEY = "nI8a6PreTcBcVmjEdhbBCqEK"
        self.SECRET_KEY = "kwGUqAm3F87ieBWO4EHtsvIL1LFAs5NU"

        # 请求URL
        self.TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
        self.SENTIMENT_URL = "https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify"
        self.ASR_URL = "https://vop.baidu.com/pro_api"

        # 情感词典初始化
        self.emotion_dict = self._init_emotion_dict()

        # Token管理
        self.access_token = None
        self.token_expire_time = 0

        # 初始化统计数据
        self.stats = {
            'total_requests': 0,
            'processing_times': [],
            'sentiment_counts': {0: 0, 1: 0, 2: 0},
            'emotion_counts': {},
            'last_sentiment': 1  # 用于实时分析
        }

        logger.info("Initialized Chinese Sentiment Analysis API v2.0.0")

    def _init_emotion_dict(self) -> Dict[str, Dict[str, Union[List[str], float]]]:
        """初始化情感词典，包含情感词和其权重"""
        return {
            "喜悦": {
                "keywords": ["开心", "快乐", "高兴", "欣喜", "愉快", "兴奋", "开怀", "喜悦"],
                "intensity": 1.0,
                "modifiers": ["很", "非常", "特别", "超级"]
            },
            "愤怒": {
                "keywords": ["生气", "愤怒", "恼火", "暴躁", "发火", "气愤", "火大", "怒不可遏"],
                "intensity": 0.9,
                "modifiers": ["极其", "特别", "非常", "超级"]
            },
            "悲伤": {
                "keywords": ["难过", "伤心", "痛苦", "悲伤", "忧愁", "沮丧", "哀伤", "消沉"],
                "intensity": 0.8,
                "modifiers": ["很", "非常", "特别", "极度"]
            },
            "担忧": {
                "keywords": ["担心", "焦虑", "忧虑", "烦恼", "不安", "紧张", "忐忑", "困扰"],
                "intensity": 0.7,
                "modifiers": ["有点", "有些", "比较", "相当"]
            },
            "满意": {
                "keywords": ["满意", "称心", "如意", "满足", "称愿", "满意", "好评", "推荐"],
                "intensity": 1.0,
                "modifiers": ["很", "非常", "特别", "相当"]
            },
            "失望": {
                "keywords": ["失望", "不满", "遗憾", "气馁", "灰心", "丧气", "差评", "垃圾"],
                "intensity": 0.8,
                "modifiers": ["有点", "有些", "比较", "非常"]
            }
        }

    async def get_access_token(self) -> str:
        """获取百度AI访问令牌"""
        current_time = time.time()
        if self.access_token and current_time < self.token_expire_time:
            return self.access_token

        try:
            params = {
                'grant_type': 'client_credentials',
                'client_id': self.API_KEY,
                'client_secret': self.SECRET_KEY
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.TOKEN_URL, params=params) as response:
                    result = await response.json()

                    if 'access_token' in result:
                        self.access_token = result['access_token']
                        self.token_expire_time = current_time + 29 * 24 * 3600
                        return self.access_token
                    else:
                        raise HTTPException(status_code=500, detail="Failed to get access token")
        except Exception as e:
            logger.error(f"Token error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Token error: {str(e)}")

    async def analyze_emotion_weights(self, text: str) -> List[EmotionWeight]:
        """分析文本中的情感权重"""
        weights = []
        for emotion, data in self.emotion_dict.items():
            count = 0
            found_keywords = []
            intensity = data['intensity']
            keywords = data['keywords']
            modifiers = data['modifiers']

            # 检查关键词
            for keyword in keywords:
                if keyword in text:
                    count += 1
                    found_keywords.append(keyword)
                    # 检查情感强度修饰词
                    for modifier in modifiers:
                        if f"{modifier}{keyword}" in text:
                            count += 0.5

            if count > 0:
                weight = min(1.0, (count * intensity) / len(keywords))
                weights.append(EmotionWeight(
                    emotion=emotion,
                    weight=round(weight, 3),
                    keywords=found_keywords
                ))

        return sorted(weights, key=lambda x: x.weight, reverse=True)

    def _analyze_acoustic_features(self, audio_data: bytes, rate: int) -> AcousticFeatures:
        """分析语音特征"""
        try:
            # 将字节数据转换为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # 计算音量特征
            volume = float(np.abs(audio_array).mean()) / 32768.0

            # 计算能量特征
            energy = float(np.square(audio_array).mean()) / (32768.0 ** 2)

            # 简单的音高估计
            pitch = 0.0
            if len(audio_array) >= rate:
                zero_crossings = np.where(np.diff(np.signbit(audio_array)))[0]
                if len(zero_crossings) > 0:
                    pitch = float(len(zero_crossings)) * rate / (2 * len(audio_array))

            # 计算语速特征
            duration = len(audio_array) / rate
            speed = float(np.sum(np.abs(np.diff(audio_array)) > 1000)) / duration / rate

            # 计算节奏特征
            if len(audio_array) >= rate:
                envelope = np.abs(audio_array).reshape(-1, rate).mean(axis=1)
                rhythm = float(np.std(envelope)) / 32768.0
            else:
                rhythm = 0.0

            return AcousticFeatures(
                pitch=round(pitch, 2),
                volume=round(volume, 3),
                speed=round(speed, 3),
                energy=round(energy, 3),
                rhythm=round(rhythm, 3)
            )

        except Exception as e:
            logger.error(f"Error in acoustic analysis: {str(e)}")
            return AcousticFeatures(
                pitch=0.0,
                volume=0.0,
                speed=0.0,
                energy=0.0,
                rhythm=0.0
            )

    async def process_audio(
            self,
            audio_data: bytes,
            format: str,
            rate: int
    ) -> DetailedSentimentResponse:
        """处理语音数据：语音识别 + 情感分析"""
        start_time = time.time()

        try:
            # 获取访问令牌
            access_token = await self.get_access_token()

            # 转换音频数据为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # 语音识别请求
            async with aiohttp.ClientSession() as session:
                headers = {'Content-Type': 'application/json'}
                data = {
                    'format': format,
                    'rate': rate,
                    'channel': 1,
                    'token': access_token,
                    'speech': audio_base64,
                    'len': len(audio_data)
                }

                async with session.post(self.ASR_URL, json=data, headers=headers) as response:
                    result = await response.json()

                    if 'result' not in result:
                        raise HTTPException(status_code=500, detail="Speech recognition failed")

                    recognized_text = result['result'][0]

            # 分析转录文本的情感
            sentiment_result = await self.analyze_sentiment(recognized_text)

            # 分析语音特征
            acoustic_features = self._analyze_acoustic_features(audio_data, rate)

            # 更新统计数据
            self._update_stats(sentiment_result, time.time() - start_time)

            return DetailedSentimentResponse(
                **sentiment_result.dict(),
                acoustic_features=acoustic_features
            )

        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")

    async def analyze_sentiment(self, text: str) -> DetailedSentimentResponse:
        """完整的情感分析"""
        start_time = time.time()

        try:
            # 获取基础情感分析
            base_sentiment = await self._get_base_sentiment(text)

            # 获取情感权重分析
            emotion_weights = await self.analyze_emotion_weights(text)

            # 分句分析
            sentences = await self._analyze_sentences(text)

            # 更新统计数据
            self._update_stats(base_sentiment, time.time() - start_time)

            return DetailedSentimentResponse(
                **base_sentiment.dict(),
                emotion_weights=emotion_weights,
                sentences=sentences
            )

        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Sentiment analysis error: {str(e)}")

    async def _get_base_sentiment(self, text: str) -> SentimentResponse:
        """获取基础情感分析"""
        try:
            access_token = await self.get_access_token()

            async with aiohttp.ClientSession() as session:
                headers = {'Content-Type': 'application/json'}
                params = {'access_token': access_token}
                data = {'text': text}

                async with session.post(
                        self.SENTIMENT_URL,
                        params=params,
                        json=data,
                        headers=headers
                ) as response:
                    result = await response.json()

                    if 'items' in result and result['items']:
                        item = result['items'][0]
                        return SentimentResponse(
                            sentiment=item['sentiment'],
                            confidence=item['confidence'],
                            positive_prob=item['positive_prob'],
                            negative_prob=item['negative_prob'],
                            text=text,
                            timestamp=datetime.now().isoformat()
                        )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Invalid API response: {json.dumps(result)}"
                        )
        except Exception as e:
            logger.error(f"Base sentiment analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

    async def _analyze_sentences(self, text: str) -> List[Dict[str, Union[str, float]]]:
        """分句分析"""
        sentences = [s.strip() for s in text.split('。') if s.strip()]
        results = []

        for sentence in sentences:
            if not sentence:
                continue

            try:
                sentiment_result = await self._get_base_sentiment(sentence)
                results.append({
                    "text": sentence,
                    "sentiment": sentiment_result.sentiment,
                    "confidence": sentiment_result.confidence
                })
            except Exception as e:
                logger.warning(f"Error analyzing sentence: {sentence}, error: {str(e)}")
                continue

        return results

    async def compare_text_and_audio(
            self,
            text: str,
            audio_data: bytes,
            format: str,
            rate: int
    ) -> ComparisonResult:
        """比较文本和语音的情感分析结果"""
        try:
            # 分析文本
            text_result = await self.analyze_sentiment(text)

            # 分析音频
            audio_result = await self.process_audio(audio_data, format, rate)

            # 计算差异
            comparison = await self._calculate_comparison(text_result, audio_result)

            # 生成结论
            conclusion = await self._generate_comparison_conclusion(
                text_result,
                audio_result,
                comparison
            )

            return ComparisonResult(
                text_analysis=text_result,
                audio_analysis=audio_result,
                comparison=comparison,
                conclusion=conclusion,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Comparison analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _calculate_comparison(
            self,
            text_result: DetailedSentimentResponse,
            audio_result: DetailedSentimentResponse
    ) -> Dict:
        """计算文本和语音分析结果的差异"""
        return {
            "sentiment_difference": {
                "value": abs(text_result.sentiment - audio_result.sentiment),
                "description": "情感极性差异"
            },
            "confidence_difference": {
                "value": abs(text_result.confidence - audio_result.confidence),
                "description": "置信度差异"
            },
            "emotion_correlation": {
                "text_emotions": [e.emotion for e in text_result.emotion_weights],
                "audio_emotions": [e.emotion for e in audio_result.emotion_weights],
                "common_emotions": list(
                    set([e.emotion for e in text_result.emotion_weights]) &
                    set([e.emotion for e in audio_result.emotion_weights])
                )
            },
            "acoustic_analysis": {
                "energy_level": "高" if audio_result.acoustic_features.energy > 0.7 else "中" if audio_result.acoustic_features.energy > 0.3 else "低",
                "speed_indication": "快速" if audio_result.acoustic_features.speed > 1.2 else "正常" if audio_result.acoustic_features.speed > 0.8 else "缓慢",
                "pitch_variation": "显著" if audio_result.acoustic_features.pitch > 200 else "适中" if audio_result.acoustic_features.pitch > 150 else "平缓"
            }
        }

    async def _generate_comparison_conclusion(
            self,
            text_result: DetailedSentimentResponse,
            audio_result: DetailedSentimentResponse,
            comparison: Dict
    ) -> str:
        """生成对比分析结论"""
        conclusions = []

        # 情感极性对比
        if text_result.sentiment == audio_result.sentiment:
            conclusions.append("文本和语音表达的情感极性一致")
        else:
            conclusions.append(
                f"文本显示{'积极' if text_result.sentiment == 2 else '消极' if text_result.sentiment == 0 else '中性'}情感，"
                f"而语音显示{'积极' if audio_result.sentiment == 2 else '消极' if audio_result.sentiment == 0 else '中性'}情感"
            )

        # 情感强度对比
        text_intensity = text_result.positive_prob if text_result.sentiment == 2 else text_result.negative_prob
        audio_intensity = audio_result.positive_prob if audio_result.sentiment == 2 else audio_result.negative_prob

        if abs(text_intensity - audio_intensity) > 0.2:
            conclusions.append(
                f"{'文本' if text_intensity > audio_intensity else '语音'}表现出更强的情感强度"
            )

        # 声学特征分析
        if audio_result.acoustic_features:
            af = audio_result.acoustic_features
            if af.energy > 0.7:
                conclusions.append("语音情感表达较为强烈")
            if af.speed > 1.2:
                conclusions.append("语速较快，可能表示紧张或兴奋")
            elif af.speed < 0.8:
                conclusions.append("语速较慢，可能表示犹豫或沮丧")

        return "；".join(conclusions)

    async def analyze_sentiment_trend(
            self,
            texts: List[str],
            time_window: str = "hour"
    ) -> SentimentTrend:
        """分析情感趋势"""
        try:
            results = []
            for text in texts:
                sentiment_result = await self.analyze_sentiment(text)
                results.append(sentiment_result)

            # 计算趋势数据
            data_points = []
            current_time = datetime.now()

            for i, result in enumerate(results):
                time_offset = i * (3600 if time_window == "hour" else 86400)
                data_points.append({
                    "timestamp": (current_time - timedelta(seconds=time_offset)).isoformat(),
                    "sentiment": result.sentiment,
                    "volume": 1
                })

            # 计算趋势摘要
            average_sentiment = sum(r.sentiment for r in results) / len(results)
            trend_direction = "上升" if results[-1].sentiment > results[0].sentiment else "下降" if results[
                                                                                                        -1].sentiment < \
                                                                                                    results[
                                                                                                        0].sentiment else "平稳"

            return SentimentTrend(
                period=time_window,
                data_points=data_points,
                summary={
                    "average_sentiment": average_sentiment,
                    "trend_direction": trend_direction,
                    "peak_time": max(data_points, key=lambda x: x["sentiment"])["timestamp"]
                }
            )

        except Exception as e:
            logger.error(f"Trend analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def analyze_real_time(
            self,
            text: Optional[str] = None,
            audio_data: Optional[bytes] = None,
            format: str = "wav",
            rate: int = 16000
    ) -> RealTimeAnalysis:
        """实时分析文本或语音"""
        try:
            current_result = None
            if text:
                current_result = await self.analyze_sentiment(text)
            elif audio_data:
                current_result = await self.process_audio(audio_data, format, rate)

            if not current_result:
                raise ValueError("Must provide either text or audio data")

            # 计算情感变化
            previous_sentiment = self.stats.get('last_sentiment', current_result.sentiment)
            sentiment_change = current_result.sentiment - previous_sentiment

            # 更新最后的情感值
            self.stats['last_sentiment'] = current_result.sentiment

            return RealTimeAnalysis(
                current_sentiment=current_result.sentiment,
                sentiment_change=sentiment_change,
                active_emotions=[e.emotion for e in current_result.emotion_weights],
                acoustic_status=current_result.acoustic_features.dict() if current_result.acoustic_features else None,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Real-time analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _update_stats(self, result: SentimentResponse, processing_time: float):
        """更新统计数据"""
        self.stats['total_requests'] += 1
        self.stats['processing_times'].append(processing_time * 1000)  # 转换为毫秒
        self.stats['sentiment_counts'][result.sentiment] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        if not self.stats['processing_times']:
            return {
                'total_requests': 0,
                'average_processing_time': 0,
                'sentiment_distribution': {
                    '消极': 0,
                    '中性': 0,
                    '积极': 0
                }
            }

        return {
            'total_requests': self.stats['total_requests'],
            'average_processing_time': sum(self.stats['processing_times']) / len(self.stats['processing_times']),
            'sentiment_distribution': {
                '消极': self.stats['sentiment_counts'][0],
                '中性': self.stats['sentiment_counts'][1],
                '积极': self.stats['sentiment_counts'][2]
            }
        }