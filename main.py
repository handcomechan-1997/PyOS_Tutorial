#!/usr/bin/env python3
"""
Python简单操作系统 (PyOS) - 主程序入口
"""

import sys
import os
from colorama import init, Fore, Style

# 初始化colorama，用于在终端输出彩色文本
init()

# 为方便模块导入，将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel.system import System
from utils.logger import Logger
from utils.boot_animation import BootAnimation, show_startup_sequence, show_welcome_message

def main():
    """主程序入口"""
    logger = Logger()
    boot_anim = BootAnimation()

    try:
        boot_anim.show_boot_screen()
        show_startup_sequence(boot_anim)
        logger.info("PyOS系统启动中...")

        system = System()
        system.boot()

        show_welcome_message()

        from shell.shell import Shell
        shell = Shell(system)
        shell.run()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}系统被用户中断{Style.RESET_ALL}")
        logger.info("系统被用户中断")
    except Exception as e:
        print(f"\n{Fore.RED}系统错误: {e}{Style.RESET_ALL}")
        logger.error(f"系统错误: {e}")
    finally:
        print(f"\n{Fore.GREEN}感谢使用PyOS！{Style.RESET_ALL}")
        logger.info("PyOS系统关闭")

if __name__ == "__main__":
    main()