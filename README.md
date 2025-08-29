# BaiTTS-CLI

一个基于 [MultiTTS](https://t.me/MultiTTS) API 的命令行工具，用于将文本文档（.txt）转换为有声书音频（.wav），并可选择生成同步的 LRC 歌词文件。

# 注意：本项目已暂停维护，现已推出使用 Rust 语言编写的 _[BaiTTS-CLI-rs](https://github.com/Doraemonsan/BaiTTS-CLI-rs)_ ：更好的性能与兼容性，二进制单文件使用更方便，还增加了进度显示和更智能的歌词生成与同步逻辑，以及更多特性，需要使用的用户请移步 _[BaiTTS-CLI-rs](https://github.com/Doraemonsan/BaiTTS-CLI-rs)_

## 功能特性

- ✅ 支持单个文本文件转语音
- ✅ 支持批量处理文件夹中的文本文件
- ✅ 可生成 LRC 歌词文件（支持自定义每句最大字符数）
- ✅ 支持声音参数调节（音量、语速、音高）
- ✅ 提供黑名单功能过滤特定内容
- ✅ 可查询 API 支持的声音列表

## 安装要求

- Python 3.12.11
- 依赖：requests 2.32.4

## 使用方法

### 基本语法

```bash
python main.py --api <API地址> [选项]
```

### 参数说明

#### 必需参数
- `--api`：指定调用的 API 地址（必须提供）

#### 功能模式（三选一）
- `-l, --list`：获取并显示支持的声音列表
- `-f, --file`：指定需要转换的单个文本文件
- `-d, --dir`：指定需要批量处理的文件夹

#### 输出选项
- `-o, --out`：指定输出文件夹（默认为当前目录）

#### 自定义声音参数
- `--voice`：指定发声的声音 ID （使用 `-l` 获取当前API可用声音列表）
- `--volume`：指定音量（0-100）
- `--speed`：指定语速（0-100）
- `--pitch`：指定音高（0-100）

#### 歌词生成
- `-s, --sub`：为处理的文件生成 LRC 歌词文件
  - 单独使用 `-s`：默认每句最大字符数为 15
  - `-s <数字>`：自定义每句最大字符数（10-100）

#### 内容过滤
- `-b, --blacklist`：指定不参与处理的黑名单字/词（支持正则表达式，可为文件、URL 或字符串，多个字词使用管道符 `|` 分割，支持正则，当输入为文件时，每行视为一个参数）

### 使用示例

#### 1. 查询 API 支持的声音列表
```bash
python script.py --api http://127.0.0.1:8774 -l
```

#### 2. 转换单个文件
```bash
python script.py --api http://127.0.0.1:8774 -f ./input.txt --voice voice1 -o ./output
```

#### 3. 批量处理文件夹并生成歌词
```bash
python script.py --api http://127.0.0.1:8774 -d ./texts --voice v2 -s 20 -o ./output
```

#### 4. 使用高级参数
```bash
python script.py --api http://127.0.0.1:8774 -f story.txt \
                 --voice v3 --volume 80 --speed 90 --pitch 75 \
                 -b "敏感词1|敏感词2" -s -o audio_output
```

## 注意事项

1. **参数互斥规则**：
   - `--list`、`--file`、`--dir` 三个参数不能同时使用
   - 使用 `--list` 时，只能配合 `--api` 参数，其他参数将被拒绝

2. **参数范围限制**：
   - `--volume`、`--speed`、`--pitch`、`--sub` 使用这些参数需要 API 支持，不提供则使用默认值，超出范围的数值将导致错误
   
3. **黑名单功能**：
   - 支持正则表达式匹配
   - 可以从文件、URL 或直接字符串读取黑名单内容

## 帮助信息

查看完整帮助：
```bash
python script.py --api <API地址> -h
```
