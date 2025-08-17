#!/usr/bin/env python3

import sys
from args import parse_and_validate_args
from process import handle_list_voices, process_file, process_directory

def main():
    """
    程序主入口函数
    """
    if len(sys.argv) == 1:
        print("错误：没有指定操作 (使用 -h 获取帮助)")
        sys.exit(1)
        
    try:
        args = parse_and_validate_args()

        if args.list:
            handle_list_voices(args.api)
        elif args.file:
            process_file(
                api_url=args.api,
                file_path=args.file,
                output_dir=args.out,
                voice_params={
                    'voice': args.voice,
                    'volume': args.volume,
                    'speed': args.speed,
                    'pitch': args.pitch
                },
                lrc_max_len=args.sub, # 传递 lrc 字符数或 None
                blacklist_source=args.blacklist
            )
        elif args.dir:
            process_directory(
                api_url=args.api,
                input_dir=args.dir,
                output_dir=args.out,
                voice_params={
                    'voice': args.voice,
                    'volume': args.volume,
                    'speed': args.speed,
                    'pitch': args.pitch
                },
                lrc_max_len=args.sub, # 传递 lrc 字符数或 None
                blacklist_source=args.blacklist
            )
        # 如果没有匹配到任何分支 (由argparse处理，这里作为保险)
        else:
             print("错误：没有指定操作 (使用 -h 获取帮助)")


    except (ValueError, FileNotFoundError, ConnectionError) as e:
        print(f"程序执行出错: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"发生未知错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
