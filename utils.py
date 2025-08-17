import re
import requests
import os
import string
import locale

def convert_file_to_utf8(file_path):
    """
    尝试用常见编码读取文件，然后用UTF-8编码覆盖保存。
    :param file_path: 文件路径
    :return: True表示转换成功, False表示失败
    """
    # 备选编码列表，优先使用系统默认编码，然后是中文场景常用编码
    encodings_to_try = [locale.getpreferredencoding(False), 'gbk', 'big5','utf16']
    
    content = None
    original_encoding = None

    # 尝试用备选编码读取文件内容
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            original_encoding = encoding
            print(f"成功使用 '{encoding}' 编码读取文件: {os.path.basename(file_path)}")
            break # 读取成功，跳出循环
        except (UnicodeDecodeError, TypeError):
            continue # 编码不匹配，尝试下一个
    
    # 如果所有备选编码都失败
    if content is None:
        print(f"错误: 无法使用任何备选编码 ({', '.join(encodings_to_try)}) 解码文件 {os.path.basename(file_path)}。")
        return False
        
    # 用UTF-8编码写回文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"文件已成功从 '{original_encoding}' 转换为 UTF-8。")
        return True
    except Exception as e:
        print(f"错误: 写入UTF-8文件时失败: {e}")
        return False


def load_blacklist_patterns(source):
    """
    从文件、URL或字符串加载黑名单规则
    :param source: 来源 (None, 文件路径, URL, 或带'|'的字符串)
    :return: 正则表达式模式列表
    """
    if not source:
        return []

    patterns = []
    try:
        if source.startswith(('http://', 'https://')):
            print(f"正在从URL加载黑名单: {source}")
            response = requests.get(source)
            response.raise_for_status()
            lines = response.text.splitlines()
            patterns = [line.strip() for line in lines if line.strip()]
        elif os.path.exists(source):
            print(f"正在从本地文件加载黑名单: {source}")
            with open(source, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                patterns = [line.strip() for line in lines if line.strip()]
        else:
            print("将黑名单参数作为正则表达式处理")
            # 假设是直接的正则表达式字符串
            patterns = [source]
    except UnicodeDecodeError:
        print(f"警告: 黑名单文件 {source} 不是UTF-8编码，请转换后重试。将不使用黑名单。")
        return []
    except Exception as e:
        print(f"警告: 加载黑名单失败: {e}。将不使用黑名单。")
        return []
    
    print(f"成功加载 {len(patterns)} 条黑名单规则。")
    return patterns

def apply_blacklist(text, patterns):
    """
    将文本中匹配黑名单模式的部分用 `[[...]]` 包裹
    :param text: 原始文本
    :param patterns: 正则表达式模式列表
    :return: 处理后的文本
    """
    if not patterns:
        return text
        
    # 将多个模式合并为一个，提高效率
    combined_pattern = "|".join(patterns)
    
    try:
        return re.sub(f"({combined_pattern})", r"[[\1]]", text)
    except re.error as e:
        print(f"警告: 黑名单正则表达式错误: {e}。该规则将被忽略。")
        # 如果组合模式出错，可以尝试逐个应用，但这会降低性能
        processed_text = text
        for pattern in patterns:
            try:
                processed_text = re.sub(f"({pattern})", r"[[\1]]", processed_text)
            except re.error:
                continue # 跳过错误的单个模式
        return processed_text


def split_text_for_lrc(text, max_len):
    """
    为生成LRC将长文本切分为短句, 同时保持 [[...]] 标记的完整性。
    每行最多 max_len 个非标点符号字符。
    """
    # 定义标点符号集
    punctuation = string.punctuation + "，。！？；：、…—·《》“”‘’"
    
    # 正则表达式，用于分割文本，同时捕获标记作为分隔符
    # 这会将文本分割成一个列表，其中普通文本和标记交替出现
    segments = re.split(r'(\[\[.*?\]\])', text)
    segments = [s for s in segments if s]  # 移除可能产生的空字符串

    final_chunks = []
    current_chunk = ""
    char_count = 0

    for segment in segments:
        # 如果段落是一个标记，直接附加到当前块，它不计入字符数
        if segment.startswith('[[') and segment.endswith(']]'):
            current_chunk += segment
            continue

        # 如果段落是普通文本，则逐字处理
        for char in segment:
            current_chunk += char
            # 仅当字符不是标点或空白时，才增加计数
            if char not in punctuation and not char.isspace():
                char_count += 1
            
            # 当达到最大长度时，完成当前块的分割
            if char_count >= max_len:
                final_chunks.append(current_chunk.strip())
                # 重置当前块和计数器
                current_chunk = ""
                char_count = 0
    
    # 循环结束后，如果当前块中还有剩余内容，将其作为最后一块
    if current_chunk.strip():
        final_chunks.append(current_chunk.strip())

    # 如果处理后没有任何块（例如，输入为空），则返回原始文本以避免错误
    return final_chunks if final_chunks else [text]
