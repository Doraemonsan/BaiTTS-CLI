import requests
import time
from urllib.parse import urljoin, urlencode

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def get_request_with_retry(url, params=None):
    """
    发起带重试逻辑的GET请求
    :param url: 请求的完整URL
    :param params: URL查询参数
    :return: 成功时返回 Response 对象
    :raises: ConnectionError 如果重试3次后仍然失败
    """
    last_error_message = ""
    
    # --- 优化点 2 START ---
    # 为了在日志中清晰地展示完整的请求URL
    full_url = url
    if params:
        full_url += "?" + urlencode(params)
    # --- 优化点 2 END ---

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()  # 如果状态码是 4xx 或 5xx, 抛出 HTTPError
            return response
        # --- 优化点 2 START ---
        # 捕获更具体的HTTP错误以获取状态码
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            request_url = e.response.url
            last_error_message = f"API返回错误状态码 {status_code} (URL: {request_url})"
            print(f"警告: 请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {last_error_message}")
        # 捕获其他所有请求相关的错误 (如超时、DNS问题等)
        except requests.exceptions.RequestException as e:
            last_error_message = f"请求时发生网络错误: {e}"
            print(f"警告: 请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {last_error_message}")
        # --- 优化点 2 END ---
            
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        else:
            # --- 优化点 2 START ---
            # 在最终的异常信息中包含更详细的错误
            raise ConnectionError(f"API请求在{MAX_RETRIES}次尝试后彻底失败。最后一次错误: {last_error_message}")
            # --- 优化点 2 END ---

def get_voices(api_url):
    """
    获取声音列表
    :param api_url: API基础地址
    :return: 声音列表的JSON数据
    """
    voices_url = urljoin(api_url, "/voices")
    print(f"正在从 {voices_url} 获取声音列表...")
    response = get_request_with_retry(voices_url)
    return response.json()


def text_to_speech(api_url, text, voice_params):
    """
    调用文本转语音接口
    :param api_url: API基础地址
    :param text: 要转换的文本
    :param voice_params: 声音相关参数 (voice, volume, speed, pitch)
    :return: WAV音频二进制数据
    """
    forward_url = urljoin(api_url, "/forward")
    
    # 过滤掉值为None的参数
    params = {k: v for k, v in voice_params.items() if v is not None}
    params['text'] = text

    # 为了日志清晰, 只显示部分文本
    log_text = (text[:30] + '...') if len(text) > 30 else text
    print(f"正在合成文本: \"{log_text.strip()}\"")
    
    response = get_request_with_retry(forward_url, params=params)
    return response.content
