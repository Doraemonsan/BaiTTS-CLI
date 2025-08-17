import os
import glob
import sys
from api import get_voices, text_to_speech
from tts import convert_text_to_audio_file
from utils import load_blacklist_patterns, apply_blacklist, convert_file_to_utf8

def handle_list_voices(api_url):
    """
    处理 --list 分支, 获取并格式化显示声音列表
    """
    try:
        data = get_voices(api_url)
        if not data.get("success") or 'data' not in data or 'catalog' not in data['data']:
            raise ValueError("API返回的声音列表格式不正确")

        all_voices = []
        for key in data['data']['catalog']:
            all_voices.extend(data['data']['catalog'][key])
        
        if not all_voices:
            print("未找到可用的声音。")
            return

        print("\n可用的声音列表：")
        separator = "=" * 50
        for voice in all_voices:
            print(separator)
            print(f"ID: {voice.get('id', 'N/A')},")
            print(f"名称: {voice.get('name', 'N/A')},")
            print(f"性别: {voice.get('gender', 'N/A')},")
            print(f"语言: {voice.get('locale', 'N/A')},")
            print(f"类型: {voice.get('type', 'N/A')}")
        print(separator)

    except Exception as e:
        raise RuntimeError(f"获取声音列表失败: {e}")


def process_file(api_url, file_path, output_dir, voice_params, lrc_max_len, blacklist_source):
    """
    处理单个文本文件
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")

    print(f"\n--- 开始处理文件: {os.path.basename(file_path)} ---")
    
    os.makedirs(output_dir, exist_ok=True)
    
    lines = []
    # --- 新增：带重试和转换逻辑的文件读取 ---
    while True:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            break # 读取成功，跳出循环
        except UnicodeDecodeError:
            print(f"\n警告: 文件 '{os.path.basename(file_path)}' 不是UTF-8编码。")
            prompt = "是否尝试将其转换为UTF-8编码后重试？ (这将覆盖原文件) [y/n]: "
            user_choice = input(prompt).lower()
            
            if user_choice in ['y', 'yes']:
                print("正在尝试转换...")
                if convert_file_to_utf8(file_path):
                    print("转换成功，正在重试读取...")
                    continue # 回到循环开头，再次尝试读取
                else:
                    raise ValueError(f"文件 {os.path.basename(file_path)} 转换失败，任务已终止。")
            else:
                raise ValueError(f"用户取消操作，文件 {os.path.basename(file_path)} 未处理。")
        
    # 加载黑名单
    blacklist_patterns = load_blacklist_patterns(blacklist_source)

    # 预处理文本行
    processed_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line: # 忽略空行
            blacklisted_line = apply_blacklist(stripped_line, blacklist_patterns)
            processed_lines.append(blacklisted_line)
    
    if not processed_lines:
        print(f"文件 {os.path.basename(file_path)} 内容为空或只包含空白行, 已跳过。")
        return
        
    # 为文档最后一行添加静音标记
    processed_lines[-1] = processed_lines[-1] + "[[PAUSE:1000]]"
    
    # 设置输出文件名
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_wav_path = os.path.join(output_dir, f"{base_filename}.wav")
    output_lrc_path = os.path.join(output_dir, f"{base_filename}.lrc") if lrc_max_len is not None else None

    # 调用核心TTS转换函数
    convert_text_to_audio_file(
        api_url=api_url,
        lines=processed_lines,
        voice_params=voice_params,
        output_wav_path=output_wav_path,
        output_lrc_path=output_lrc_path,
        lrc_max_len=lrc_max_len
    )
    print(f"--- 文件处理完成: {os.path.basename(file_path)} ---")


def process_directory(api_url, input_dir, output_dir, voice_params, lrc_max_len, blacklist_source):
    """
    处理指定目录下的所有 .txt 文件
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    txt_files = sorted(glob.glob(os.path.join(input_dir, '*.txt')))
    
    if not txt_files:
        print(f"目录 {input_dir} 中没有找到 .txt 文件。")
        return
    
    # --- 新增：批量处理前的编码预检查 ---
    print("正在进行文件编码预检查...")
    files_to_convert = []
    for file_path in txt_files:
        try:
            # 只尝试打开，不读取内容，以快速检查编码
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1) 
        except UnicodeDecodeError:
            files_to_convert.append(file_path)
    
    if files_to_convert:
        print("\n警告: 检测到以下文件不是UTF-8编码:")
        for f in files_to_convert:
            print(f" - {os.path.basename(f)}")
        
        prompt = "\n是否尝试将以上所有文件转换为UTF-8编码后继续？ (这将覆盖原文件) [y/n]: "
        user_choice = input(prompt).lower()
        
        if user_choice in ['y', 'yes']:
            print("正在批量转换文件...")
            success_count = 0
            for file_path in files_to_convert:
                if convert_file_to_utf8(file_path):
                    success_count += 1
            if success_count != len(files_to_convert):
                raise ValueError("部分文件转换失败，任务已终止。请检查上方日志。")
            print("所有文件转换完成，继续执行任务。")
        else:
            raise ValueError("用户取消操作，批量任务未执行。")

    # --- 预检查结束，开始正式处理 ---
    print(f"\n即将处理目录 '{input_dir}' 中的 {len(txt_files)} 个文件...")

    for file_path in txt_files:
        try:
            process_file(api_url, file_path, output_dir, voice_params, lrc_max_len, blacklist_source)
        except Exception as e:
            print(f"处理文件 {os.path.basename(file_path)} 时发生错误: {e}", file=sys.stderr)
            # 选择继续处理下一个文件
            continue
            
    print("\n所有文件处理完毕。")

