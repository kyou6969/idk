from typing import Dict, Any
from pydantic import BaseSettings


class Settings(BaseSettings):
    # API Keys
    BAIDU_API_KEY: str = "nI8a6PreTcBcVmjEdhbBCqEK"
    BAIDU_SECRET_KEY: str = "kwGUqAm3F87ieBWO4EHtsvIL1LFAs5NU"

    # API URLs
    BAIDU_TOKEN_URL: str = "https://aip.baidubce.com/oauth/2.0/token"
    BAIDU_SENTIMENT_URL: str = "https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify"
    BAIDU_ASR_URL: str = "https://vop.baidu.com/pro_api"

    # 应用配置
    APP_NAME: str = "中文情感分析系统"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 跨域配置
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # 音频处理配置
    ALLOWED_AUDIO_FORMATS: list = ["wav", "pcm", "amr"]
    MAX_AUDIO_SIZE: int = 5 * 1024 * 1024  # 5MB
    DEFAULT_SAMPLE_RATE: int = 16000

    # 文本处理配置
    MAX_TEXT_LENGTH: int = 1000
    MAX_BATCH_SIZE: int = 100

    # 缓存配置
    CACHE_ENABLED: bool = True
    CACHE_EXPIRE: int = 3600  # 1小时

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"


settings = Settings()

# 情感分析配置
SENTIMENT_CONFIG = {
    "情感级别": {
        0: "消极",
        1: "中性",
        2: "积极"
    },
    "情感阈值": {
        "high_confidence": 0.8,
        "medium_confidence": 0.5,
        "low_confidence": 0.3
    },
    "声学特征阈值": {
        "energy": {
            "high": 0.7,
            "medium": 0.3
        },
        "speed": {
            "fast": 1.2,
            "slow": 0.8
        },
        "pitch": {
            "high": 200,
            "medium": 150
        }
    }
}