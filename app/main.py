from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    TextRequest,
    AudioRequest,
    DetailedSentimentResponse,
    BatchRequest,
    BatchResponse,
    ComparisonResult
)
from .sentiment_analyzer import SentimentAnalyzer
import aiohttp
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="中文情感分析系统",
    description="基于深度学习的中文文本和语音情感分析服务",
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
        "message": "欢迎使用中文情感分析系统",
        "version": "2.0.0",
        "docs_url": "/docs",
        "timestamp": datetime.now().isoformat()
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
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")

        if len(request.text) > 1000:
            raise HTTPException(status_code=400, detail="文本长度不能超过1000字")

        logger.info(f"Analyzing text: {request.text[:100]}...")
        result = await analyzer.analyze_sentiment(request.text)
        logger.info(f"Text analysis completed: sentiment={result.sentiment}")
        return result

    except Exception as e:
        logger.error(f"Text analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/audio", response_model=DetailedSentimentResponse)
async def analyze_audio(
        file: UploadFile = File(...),
        format: str = Form("wav"),
        rate: int = Form(16000)
):
    """
    分析语音情感
    - file: 语音文件 (WAV/PCM/AMR格式)
    - format: 音频格式
    - rate: 采样率
    """
    try:
        if not file:
            raise HTTPException(status_code=400, detail="未提供音频文件")

        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:  # 5MB限制
            raise HTTPException(status_code=400, detail="音频文件大小不能超过5MB")

        logger.info(f"Analyzing audio file: {file.filename}")
        result = await analyzer.process_audio(contents, format, rate)
        logger.info(f"Audio analysis completed: sentiment={result.sentiment}")
        return result

    except Exception as e:
        logger.error(f"Audio analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/audio/url", response_model=DetailedSentimentResponse)
async def analyze_audio_url(request: AudioRequest):
    """
    通过URL分析语音情感
    - audio_url: 语音文件URL
    - format: 音频格式
    - rate: 采样率
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(request.audio_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="无法下载音频文件")
                contents = await response.read()
                if len(contents) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="音频文件大小不能超过5MB")

        logger.info(f"Analyzing audio from URL: {request.audio_url}")
        result = await analyzer.process_audio(contents, request.format, request.rate)
        logger.info(f"Audio URL analysis completed: sentiment={result.sentiment}")
        return result

    except Exception as e:
        logger.error(f"Audio URL analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/compare", response_model=ComparisonResult)
async def compare_text_and_audio(
        text: str = Form(...),
        file: UploadFile = File(...),
        format: str = Form("wav"),
        rate: int = Form(16000)
):
    """
    对比文本和语音的情感分析结果
    - text: 文本内容
    - file: 语音文件
    - format: 音频格式
    - rate: 采样率
    """
    try:
        logger.info(f"Starting comparison analysis for text and audio")

        # 分析文本
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        text_result = await analyzer.analyze_sentiment(text)

        # 分析音频
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="音频文件大小不能超过5MB")
        audio_result = await analyzer.process_audio(contents, format, rate)

        # 计算差异并生成对比结果
        comparison = {
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
            "analysis": {
                "text_unique_emotions": [
                    e.emotion for e in text_result.emotion_weights
                    if e.emotion not in [ae.emotion for ae in audio_result.emotion_weights]
                ],
                "audio_unique_emotions": [
                    e.emotion for e in audio_result.emotion_weights
                    if e.emotion not in [te.emotion for te in text_result.emotion_weights]
                ],
                "conclusion": await _generate_comparison_conclusion(text_result, audio_result)
            }
        }

        logger.info("Comparison analysis completed")
        return ComparisonResult(
            text_analysis=text_result,
            audio_analysis=audio_result,
            comparison=comparison
        )

    except Exception as e:
        logger.error(f"Comparison analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/batch", response_model=BatchResponse)
async def analyze_batch(request: BatchRequest):
    """
    批量分析文本情感
    - texts: 要分析的中文文本列表
    """
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="文本列表不能为空")

        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="每次最多处理100条文本")

        logger.info(f"Batch analyzing {len(request.texts)} texts")
        results = []

        for text in request.texts:
            try:
                result = await analyzer.analyze_sentiment(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing text: {text[:100]}... Error: {str(e)}")
                results.append(None)

        valid_results = [r for r in results if r is not None]
        avg_sentiment = sum(r.sentiment for r in valid_results) / len(valid_results) if valid_results else 0

        return BatchResponse(
            results=results,
            total=len(results),
            average_sentiment=avg_sentiment,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_comparison_conclusion(text_result, audio_result) -> str:
    """生成文本和语音分析的对比结论"""
    try:
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
        if hasattr(audio_result, 'acoustic_features') and audio_result.acoustic_features:
            if audio_result.acoustic_features.energy > 0.7:
                conclusions.append("语音情感表达较为强烈")
            if audio_result.acoustic_features.speed > 1.2:
                conclusions.append("语速较快，可能表示紧张或兴奋")
            elif audio_result.acoustic_features.speed < 0.8:
                conclusions.append("语速较慢，可能表示犹豫或沮丧")

        return "；".join(conclusions)

    except Exception as e:
        logger.error(f"Error generating comparison conclusion: {str(e)}")
        return "无法生成对比结论"


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
logger.info("Chinese Sentiment Analysis API v2.0.0 initialized")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)