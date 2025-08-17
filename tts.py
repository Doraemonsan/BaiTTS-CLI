import os
import wave
import tempfile
import shutil
import time
import io
from api import text_to_speech
from lrc import generate_lrc_content
from utils import split_text_for_lrc

def convert_text_to_audio_file(api_url, lines, voice_params, output_wav_path, output_lrc_path=None, lrc_max_len=None):
    """
    将文本行列表转换为单个WAV文件, 并可选择生成LRC文件。
    - 如果不生成LRC，则每行文本调用一次API合成音频。
    - 如果生成LRC，则每行文本也只调用一次API合成音频，然后根据音频总时长为分割后的短句分配时间戳。
    """
    temp_dir = tempfile.mkdtemp(prefix="tts_cli_")
    print(f"创建临时缓存目录: {temp_dir}")
    
    main_audio_paths = []
    
    try:
        if not output_lrc_path:
            # --- 逻辑分支1: 不生成LRC ---
            print("模式: 仅合成音频")
            for i, line in enumerate(lines):
                audio_data = text_to_speech(api_url, line, voice_params)
                chunk_path = os.path.join(temp_dir, f"main_audio_{i}.wav")
                with open(chunk_path, 'wb') as f:
                    f.write(audio_data)
                main_audio_paths.append(chunk_path)
        else:
            # --- 逻辑分支2: 生成LRC ---
            print(f"模式: 合成音频并生成LRC字幕 (每句最大 {lrc_max_len} 字符)")
            lrc_timestamps = []
            lrc_texts = []
            total_duration_ms = 0

            for i, line in enumerate(lines):
                # 步骤1: 合成完整的单行音频，用于最终的WAV文件和时长计算
                print(f"合成主音频 (第 {i+1}/{len(lines)} 行)...")
                main_audio_data = text_to_speech(api_url, line, voice_params)
                main_chunk_path = os.path.join(temp_dir, f"main_audio_{i}.wav")
                with open(main_chunk_path, 'wb') as f:
                    f.write(main_audio_data)
                main_audio_paths.append(main_chunk_path)

                # 步骤2: 计算该完整音频行的总时长
                line_duration_ms = 0
                try:
                    with wave.open(io.BytesIO(main_audio_data), 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        line_duration_ms = int((frames / float(rate)) * 1000)
                except wave.Error:
                    print(f"警告: 无法读取主音频行 '{line[:20]}...' 的时长, 该行LRC时间轴可能不准。")

                # 步骤3: 将该行文本分割成LRC短句
                lrc_chunks = split_text_for_lrc(line, lrc_max_len)
                
                print(f"为第 {i+1} 行的 {len(lrc_chunks)} 个LRC短句分配时间戳...")
                
                # 步骤4: 将总时长均分给每个短句
                if lrc_chunks:
                    # 防止除以零错误
                    duration_per_chunk = line_duration_ms / len(lrc_chunks) if len(lrc_chunks) > 0 else 0
                    for chunk_index, lrc_chunk in enumerate(lrc_chunks):
                        # 计算当前短句的开始时间
                        chunk_start_time = total_duration_ms + int(chunk_index * duration_per_chunk)
                        
                        # 记录LRC数据
                        lrc_timestamps.append(chunk_start_time)
                        lrc_texts.append(lrc_chunk.strip())
                
                # 累加总时长，为下一行做准备
                total_duration_ms += line_duration_ms

            # 步骤5: 生成LRC文件内容
            lrc_content = generate_lrc_content(lrc_timestamps, lrc_texts)
            with open(output_lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_content)
            print(f"LRC歌词文件已保存: {output_lrc_path}")

        # --- 通用逻辑: 合并主音频文件 ---
        if not main_audio_paths:
             print("警告: 没有生成任何音频数据, 跳过文件合成。")
             return

        print(f"正在合并 {len(main_audio_paths)} 个主音频块到 {os.path.basename(output_wav_path)}...")
        combine_wav_files(main_audio_paths, output_wav_path)
        print(f"音频文件已保存: {output_wav_path}")

    finally:
        print(f"清理临时缓存目录: {temp_dir}")
        shutil.rmtree(temp_dir)


def combine_wav_files(input_files, output_file):
    """
    将多个WAV文件合并成一个。
    """
    if not input_files:
        return
        
    outfile = None
    try:
        # 使用第一个有效的WAV文件作为输出文件的参数模板
        params = None
        for file_path in input_files:
            try:
                with wave.open(file_path, 'rb') as infile:
                    params = infile.getparams()
                    break
            except (wave.Error, EOFError):
                print(f"警告: 读取音频块 {os.path.basename(file_path)} 参数失败, 已跳过。")
                continue # 如果文件损坏，尝试下一个
        
        if params is None:
            raise RuntimeError("所有音频块均无效，无法合并。")

        with wave.open(output_file, 'wb') as outfile:
            outfile.setparams(params)
            for file_path in input_files:
                try:
                    with wave.open(file_path, 'rb') as infile:
                        outfile.writeframes(infile.readframes(infile.getnframes()))
                except (wave.Error, EOFError):
                     print(f"警告: 读取音频块 {os.path.basename(file_path)} 数据失败, 已跳过。")
    except Exception as e:
        raise RuntimeError(f"合并WAV文件失败: {e}")
