from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    TextRequest,
    AudioRequest,
    DetailedSentimentResponse,
    BatchRequest,
    BatchResponse
)
from .sentiment_analyzer import SentimentAnalyzer
import aiohttp
import io
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="中文情感分析 API",
    description="基于百度 AI 的中文文本和语音情感分析服务",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化分析器
analyzer = SentimentAnalyzer()


@app.get("/")
async def home():
    """主页"""
    return {
        "message": "欢迎使用中文情感分析 API",
        "version": "2.0.0",
        "docs_url": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.post("/analyze/text", response_model=DetailedSentimentResponse)
async def analyze_text(request: TextRequest):
    """
    分析文本情感
    - text: 要分析的中文文本
    """
    try:
        result = await analyzer.analyze_sentiment(request.text)
        return result
    except Exception as e:
        logger.error(f"Text analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/audio", response_model=DetailedSentimentResponse)
async def analyze_audio(
        file: UploadFile = File(...),
        format: str = "wav",
        rate: int = 16000
):
    """
    分析语音情感
    - file: 语音文件 (WAV/PCM/AMR格式)
    - format: 音频格式 (wav/pcm/amr)
    - rate: 采样率 (默认16000)
    """
    try:
        contents = await file.read()
        result = await analyzer.process_audio(contents, format, rate)
        return result
    except Exception as e:
        logger.error(f"Audio analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/audio/url", response_model=DetailedSentimentResponse)
async def analyze_audio_url(request: AudioRequest):
    """
    通过URL分析语音情感
    - audio_url: 语音文件URL
    - format: 音频格式 (wav/pcm/amr)
    - rate: 采样率 (默认16000)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(request.audio_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to download audio")
                contents = await response.read()

        result = await analyzer.process_audio(
            contents,
            request.format,
            request.rate
        )
        return result
    except Exception as e:
        logger.error(f"Audio URL analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/batch", response_model=BatchResponse)
async def analyze_batch(request: BatchRequest):
    """
    批量分析文本情感
    - texts: 要分析的中文文本列表
    """
    try:
        results = []
        for text in request.texts:
            result = await analyzer.analyze_sentiment(text)
            results.append(result)

        # 计算平均情感极性
        avg_sentiment = sum(r.sentiment for r in results) / len(results)

        return BatchResponse(
            results=results,
            total=len(results),
            average_sentiment=avg_sentiment,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """获取API使用统计"""
    try:
        stats = analyzer.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# 启动时的日志
logger.info("Initialized Chinese Sentiment Analysis API v2.0.0")