"""
Chinese Sentiment Analysis API
~~~~~~~~~~~~~~~~~~~~~
一个基于 FastAPI 的中文情感分析 API 服务。
"""

__version__ = '2.0.0'
__author__ = 'Your Name'
__license__ = 'MIT'

from .sentiment_analyzer import SentimentAnalyzer
from .models import (
    TextRequest,
    BatchRequest,
    SentimentResponse,
    BatchResponse
)

# 导出主要的类和函数
__all__ = [
    'SentimentAnalyzer',
    'TextRequest',
    'BatchRequest',
    'SentimentResponse',
    'BatchResponse',
]

# 配置信息
CONFIG = {
    'API_VERSION': __version__,
    'API_TITLE': '中文情感分析 API',
    'API_DESCRIPTION': '基于深度学习的中文文本情感分析服务',
    'DOCS_URL': '/docs',
    'REDOC_URL': '/redoc',

    # API 限制配置
    'RATE_LIMIT': {
        'calls': 100,
        'period': 60  # 秒
    },

    # 分析器配置
    'ANALYZER_CONFIG': {
        'sentiment_threshold': 0.1,
        'max_text_length': 5000,
        'batch_size': 100
    }
}

# 初始化日志配置
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f'Initialized Chinese Sentiment Analysis API v{__version__}')


# 异常类定义
class SentimentAnalysisError(Exception):
    """情感分析基础异常类"""
    pass


class TextTooLongError(SentimentAnalysisError):
    """文本过长异常"""
    pass


class InvalidTextError(SentimentAnalysisError):
    """无效文本异常"""
    pass


class BatchSizeTooLargeError(SentimentAnalysisError):
    """批量大小过大异常"""
    pass


# 导出异常类
__all__ += [
    'SentimentAnalysisError',
    'TextTooLongError',
    'InvalidTextError',
    'BatchSizeTooLargeError'
]


# 工具函数
def validate_text(text: str) -> bool:
    """验证文本是否有效"""
    if not text or not isinstance(text, str):
        return False
    if len(text.strip()) == 0:
        return False
    if len(text) > CONFIG['ANALYZER_CONFIG']['max_text_length']:
        raise TextTooLongError(
            f"Text length exceeds maximum allowed length of "
            f"{CONFIG['ANALYZER_CONFIG']['max_text_length']} characters"
        )
    return True


def validate_batch(texts: list) -> bool:
    """验证批量文本是否有效"""
    if not texts or not isinstance(texts, list):
        return False
    if len(texts) > CONFIG['ANALYZER_CONFIG']['batch_size']:
        raise BatchSizeTooLargeError(
            f"Batch size exceeds maximum allowed size of "
            f"{CONFIG['ANALYZER_CONFIG']['batch_size']}"
        )
    return all(validate_text(text) for text in texts)


# 导出工具函数
__all__ += [
    'validate_text',
    'validate_batch'
]


# 中间件函数
async def rate_limit_middleware():
    """速率限制中间件"""
    # TODO: 实现速率限制逻辑
    pass


# 导出中间件
__all__ += [
    'rate_limit_middleware'
]