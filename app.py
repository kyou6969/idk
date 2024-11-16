"""
情感分析系统后端API
提供文本和语音情感分析服务
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
import numpy as np
from datetime import datetime
import os
from pathlib import Path

# 配置日志
log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"api_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="情感分析系统API",
    description="提供文本和语音的情感分析服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class TextRequest(BaseModel):
    text: str
    options: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    text: str
    sentiment: int
    confidence: float
    positive_prob: float
    negative_prob: float
    emotion_weights: List[Dict[str, Any]]
    timestamp: str


# 模拟情感分析功能
def analyze_sentiment(text: str) -> Dict:
    """
    模拟情感分析，返回分析结果
    实际项目中需要替换为真实的情感分析模型
    """
    try:
        # 生成模拟的分析结果
        sentiment = np.random.choice([0, 1, 2])  # 0:消极, 1:中性, 2:积极
        confidence = np.random.random()
        positive_prob = np.random.random()
        negative_prob = 1 - positive_prob

        # 生成情感权重
        emotions = ['喜悦', '愤怒', '悲伤', '恐惧', '惊讶']
        emotion_weights = []
        keywords = ['好', '棒', '差', '糟', '一般']

        for emotion in emotions:
            weight = np.random.random()
            emotion_weights.append({
                'emotion': emotion,
                'weight': weight,
                'keywords': np.random.choice(keywords, size=np.random.randint(0, 3)).tolist()
            })

        result = {
            'text': text,
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_prob': positive_prob,
            'negative_prob': negative_prob,
            'emotion_weights': emotion_weights,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Analysis completed for text: {text[:50]}...")
        return result

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        raise


def analyze_audio_features(audio_data: bytes, format: str, rate: int) -> Dict:
    """
    模拟音频特征分析，返回分析结果
    实际项目中需要替换为真实的音频分析模型
    """
    try:
        return {
            'pitch': np.random.normal(100, 20),
            'volume': np.random.random() * 100,
            'speed': np.random.normal(1.0, 0.2),
            'energy': np.random.random() * 100
        }
    except Exception as e:
        logger.error(f"Error in audio analysis: {str(e)}")
        raise


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "情感分析系统API服务正在运行",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: TextRequest):
    """
    分析文本情感
    :param request: 包含文本内容的请求
    :return: 情感分析结果
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="文本内容不能为空")

        logger.info(f"Received text analysis request: {request.text[:100]}...")
        result = analyze_sentiment(request.text)
        return result

    except Exception as e:
        logger.error(f"Error processing text analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/audio")
async def analyze_audio(
        file: UploadFile = File(...),
        format: str = Form(...),
        rate: int = Form(...)
):
    """
    分析音频情感
    :param file: 音频文件
    :param format: 音频格式
    :param rate: 采样率
    :return: 情感分析结果
    """
    try:
        logger.info(f"Received audio analysis request: {file.filename}")

        # 验证音频格式
        allowed_formats = ['wav', 'pcm', 'amr']
        if format.lower() not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的音频格式。支持的格式: {', '.join(allowed_formats)}"
            )

        # 验证采样率
        allowed_rates = [8000, 16000, 44100, 48000]
        if rate not in allowed_rates:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的采样率。支持的采样率: {', '.join(map(str, allowed_rates))}"
            )

        # 读取音频数据
        audio_data = await file.read()

        # 分析音频特征
        acoustic_features = analyze_audio_features(audio_data, format, rate)

        # 模拟文本转写和情感分析
        # 实际项目中需要添加语音识别功能
        text = f"音频文件 {file.filename} 的转写文本"
        sentiment_result = analyze_sentiment(text)

        # 合并结果
        result = {
            **sentiment_result,
            'acoustic_features': acoustic_features,
            'audio_info': {
                'filename': file.filename,
                'format': format,
                'sample_rate': rate,
                'size': len(audio_data)
            }
        }

        logger.info(f"Completed audio analysis for {file.filename}")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        return {
            "status": "active",
            "uptime": "0:00:00",  # 实际项目中需要实现
            "total_requests": 0,  # 实际项目中需要实现
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)