import argparse
import sys

def parse_and_validate_args():
    """
    解析和验证命令行参数
    """
    parser = argparse.ArgumentParser(description="文本转语音 CLI 工具", add_help=False)

    # 自定义 help 参数
    parser.add_argument(
        '-h', '--help', action='help', default=argparse.SUPPRESS,
        help='显示此帮助信息并退出'
    )

    # API 和通用参数
    parser.add_argument('--api', type=str, required=True, help='指定调用的API地址 (必须提供)')

    # 功能分支参数
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--list', action='store_true', help='获取并显示支持的声音列表')
    group.add_argument('-f', '--file', type=str, help='指定需要转换的单个文本文件')
    group.add_argument('-d', '--dir', type=str, help='指定需要批量处理的文件夹')

    # file 和 dir 分支的附加参数
    parser.add_argument('-o', '--out', type=str, default='.', help='指定输出文件夹 (默认为当前目录)')
    parser.add_argument('--voice', type=str, help='指定发声的声音ID')
    parser.add_argument('--volume', type=int, choices=range(0, 101), metavar="[0-100]", help='指定音量 (0-100)')
    parser.add_argument('--speed', type=int, choices=range(0, 101), metavar="[0-100]", help='指定语速 (0-100)')
    parser.add_argument('--pitch', type=int, choices=range(0, 101), metavar="[0-100]", help='指定音高 (0-100)')
    
    # --- 优化点 2: 修改 --sub 参数 ---
    parser.add_argument(
        '-s', '--sub',
        nargs='?',
        type=int,
        const=15,  # 如果只写 -s 而没有提供数字，则使用此默认值
        default=None, # 如果不使用 -s 参数，则值为 None
        choices=range(10, 101),
        metavar="[10-100]",
        help='为处理的文件生成LRC歌词文件。可选择提供每句最大字符数 (10-100)，若不提供数字则默认为 15。'
    )
    
    parser.add_argument('-b', '--blacklist', type=str, help='指定不参与处理的黑名单字/词 (支持正则, 可为文件、URL或字符串)')

    args = parser.parse_args()

    # --- 参数合法性检查 ---
    # help 分支：argparse 默认处理，无需额外检查

    # list 分支检查
    if args.list:
        allowed_args = ['api', 'list']
        for arg, value in vars(args).items():
            # 检查 args.sub 是否为默认值 None
            if arg == 'sub' and value is None:
                continue
            if arg not in allowed_args and value is not None and value is not False and value != '.':
                 parser.error("使用 --list 参数时, 只允许提供 --api 参数")

    # file 或 dir 分支检查
    if args.file or args.dir:
        allowed_args = ['api', 'file', 'dir', 'out', 'voice', 'volume', 'speed', 'pitch', 'sub', 'blacklist']
        for arg, value in vars(args).items():
             if arg not in allowed_args and value is not None and value is not False and value != '.':
                parser.error(f"使用 --file 或 --dir 时, 不允许使用 --{arg} 参数")
    
    # 检查是否指定了操作
    if not args.list and not args.file and not args.dir:
        # 如果除了 --api 之外还有其他参数, 则视为错误
        other_args_present = any(
            val is not None and val is not False
            for key, val in vars(args).items() if key not in ['api', 'out'] # 'out' 有默认值，需排除
        )
        if other_args_present:
             parser.error("提供了无效的参数组合 (使用 -h 获取帮助)")


    return args
