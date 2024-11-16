import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"


def test_text_analysis():
    """测试文本情感分析"""
    print("\n测试文本情感分析...")

    # 单条文本分析
    text_data = {"text": "这个产品非常好用，我很喜欢！"}
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=text_data
    )
    print("\n单条文本分析结果:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

    # 批量文本分析
    batch_data = {
        "texts": [
            "这个产品非常好用，我很喜欢！",
            "服务态度差，不推荐购买。",
            "一般般，没什么特别的。"
        ]
    }
    response = requests.post(
        f"{BASE_URL}/analyze/batch",
        json=batch_data
    )
    print("\n批量文本分析结果:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))


def test_audio_analysis():
    """测试音频情感分析"""
    print("\n测试音频情感分析...")

    # 通过文件上传测试
    try:
        with open('test_audio.wav', 'rb') as f:
            files = {'audio': ('test_audio.wav', f, 'audio/wav')}
            response = requests.post(
                f"{BASE_URL}/analyze/audio",
                files=files,
                data={'format': 'wav', 'rate': '16000'}
            )
        print("\n音频文件分析结果:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except FileNotFoundError:
        print("未找到测试音频文件 test_audio.wav")

    # 通过URL测试
    audio_url_data = {
        "audio_url": "https://example.com/test_audio.wav",
        "format": "wav",
        "rate": 16000
    }
    response = requests.post(
        f"{BASE_URL}/analyze/audio/url",
        json=audio_url_data
    )
    print("\n音频URL分析结果:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))


def test_health():
    """测试健康检查接口"""
    print("\n测试健康检查...")

    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))


def main():
    """主测试函数"""
    print("开始API测试...\n")

    try:
        # 测试健康检查
        test_health()

        # 测试文本分析
        test_text_analysis()

        # 测试音频分析
        test_audio_analysis()

    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main()