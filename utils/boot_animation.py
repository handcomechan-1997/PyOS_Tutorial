# -*- coding: utf-8 -*-
"""
PyOS 启动动画（统一风格版）
- 采用与 Algorithm Learning Platform 相同的盒框样式与配色
- 5×5 等宽字库大字 LOGO（PYOS）
- 统一的进度条（█ / ░）、标题配色、居中排版
"""

import os
import sys
import time
from colorama import Fore, Style

# ----------------------------- 工具函数 -----------------------------

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# ----------------------------- 启动动画类 -----------------------------

class BootAnimation:
    """启动动画类（风格统一版）"""

    def __init__(self):
        # 盒内宽度（与上一个示例一致）
        self.inner_w = 62

        # 5×5 等宽字库
        self.font = {
            'P': ["█████", "█   █", "█████", "█    ", "█    "],
            'Y': ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
            'O': [" ███ ", "█   █", "█   █", "█   █", " ███ "],
            'S': [" ████", "█    ", " ███ ", "    █", "████ "],
        }

        # 生成 LOGO
        word = "PYOS"
        rows = [" ".join(self.font[ch][r] for ch in word) for r in range(5)]

        top    = "╔" + "═" * self.inner_w + "╗"
        blank  = "║" + " " * self.inner_w + "║"
        body   = "\n".join("║" + row.center(self.inner_w) + "║" for row in rows)
        footer = [
            blank,
            "║" + "Python Operating System".center(self.inner_w) + "║",
            blank,
            "║" + "Version 1.0.0 - HandsomeChen".center(self.inner_w) + "║",
            blank,
        ]
        bottom = "╚" + "═" * self.inner_w + "╝"

        self.logo_box = "\n".join([top, blank, body, *footer, bottom])

    # ----------------------------- 盒子渲染 -----------------------------

    def _boxed_lines(self, lines, color=Fore.CYAN):
        """将多行文本包裹为统一风格的盒子"""
        top    = "╔" + "═" * self.inner_w + "╗"
        bottom = "╚" + "═" * self.inner_w + "╝"
        content = "\n".join("║" + line.ljust(self.inner_w)[:self.inner_w] + "║" for line in lines)
        return f"{color}{top}\n{content}\n{bottom}{Style.RESET_ALL}"

    # ----------------------------- 展示函数 -----------------------------

    def show_boot_screen(self):
        """显示启动 LOGO 盒"""
        print(Fore.CYAN + self.logo_box + Style.RESET_ALL)
        time.sleep(1)

    def show_system_info_box(self):
        """显示系统信息（统一盒框 + 左对齐）"""
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        bit = '64-bit' if sys.maxsize > 2**32 else '32-bit'
        lines = [
            " 系统信息".center(self.inner_w),
            "─" * self.inner_w,
            f" 操作系统 : PyOS 1.0.0",
            f" Python版本 : {sys.version.split()[0]}",
            f" 平台     : {sys.platform}",
            f" 架构     : {bit}",
            f" 启动时间 : {now}",
        ]
        print(self._boxed_lines(lines, color=Fore.GREEN))

    def show_progress_bar(self, title: str, duration: float = 2.0):
        """显示进度条（与上个示例一致的样式）"""
        print(f"\n{Fore.YELLOW}{title}{Style.RESET_ALL}")
        steps = 50
        for i in range(steps + 1):
            progress = i / steps
            bar_len = 50
            filled = int(bar_len * progress)
            bar = '█' * filled + '░' * (bar_len - filled)
            pct = int(progress * 100)
            print(f"\r[{bar}] {pct}%", end='', flush=True)
            time.sleep(duration / steps)
        print()

# ----------------------------- 启动流程 -----------------------------

def show_startup_sequence(animation: BootAnimation):
    """显示启动序列（进度条风格统一）"""
    steps = [
        "初始化系统核心",
        "加载内存管理器",
        "初始化文件系统",
        "启动设备管理器",
        "创建进程管理器",
        "启动调度器",
        "初始化 Shell 环境",
    ]
    total_duration = 3.0  # 总时长可按需调整
    per = total_duration / len(steps)
    for s in steps:
        animation.show_progress_bar(s, per)

def show_welcome_message():
    """显示欢迎信息（与上个示例的版式一致）"""
    msg = """
============================================================
    🎉 欢迎使用 PyOS 操作系统！🎉
============================================================

这是一个用于学习与演示的 Python 迷你操作系统界面。

🎯 学习目标：
• 理解启动流程各模块的职责
• 观察组件初始化的先后与依赖关系
• 通过可视化进度条把握系统加载进度
• 为后续 Shell/驱动/调度实验打基础

📚 推荐路径：
1. 进程与调度 → 2. 内存管理 → 3. 文件系统 → 4. 设备与驱动

🚀 祝你玩得开心，学有所获！
============================================================
    """
    print(Fore.GREEN + msg + Style.RESET_ALL)

# -------------
