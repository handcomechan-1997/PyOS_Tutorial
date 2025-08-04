"""
启动动画模块 - 提供酷炫的系统启动界面
"""

import sys
import os
import time
import threading
from colorama import Fore, Back, Style

class BootAnimation:
    """启动动画类"""
    
    def __init__(self):
        self.running = False
        self.animation_thread = None
        
    def show_boot_screen(self):
        """显示启动界面"""
        self.running = True
        
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 显示PyOS Logo
        self._show_logo()
        
        # 显示系统信息
        self._show_system_info()
        
        # 启动动画线程
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        
        # 等待动画完成
        time.sleep(3)
        self.running = False
        
        # 清屏准备进入系统
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _show_logo(self):
        """显示PyOS Logo"""
        logo = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                  ║
║  {Fore.YELLOW}██████╗ ██╗   ██╗ ██████╗ ███████╗{Fore.CYAN}                          ║
║  {Fore.YELLOW}██╔══██╗╚██╗ ██╔╝██╔═══██╗██╔════╝{Fore.CYAN}                          ║
║  {Fore.YELLOW}██████╔╝ ╚████╔╝ ██║   ██║███████╗{Fore.CYAN}                          ║
║  {Fore.YELLOW}██╔═══╝   ╚██╔╝  ██║   ██║╚════██║{Fore.CYAN}                          ║
║  {Fore.YELLOW}██║        ██║   ╚██████╔╝███████║{Fore.CYAN}                          ║
║  {Fore.YELLOW}╚═╝        ╚═╝    ╚═════╝ ╚══════╝{Fore.CYAN}                          ║
║                                                                  ║
║  {Fore.WHITE}Python Operating System{Fore.CYAN}                                    ║
║  {Fore.WHITE}Version 1.0.0 - HandsomeChen{Fore.CYAN}                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(logo)
    
    def _show_system_info(self):
        """显示系统信息"""
        info = f"""
{Fore.GREEN}╔══════════════════════════════════════════════════════════════╗
║                    {Fore.WHITE}系统信息{Fore.GREEN}                                    ║
╠══════════════════════════════════════════════════════════════╣
║  {Fore.WHITE}操作系统: {Fore.CYAN}PyOS 1.0.0{Fore.GREEN}                              ║
║  {Fore.WHITE}Python版本: {Fore.CYAN}{sys.version.split()[0]}{Fore.GREEN}                    ║
║  {Fore.WHITE}平台: {Fore.CYAN}{sys.platform}{Fore.GREEN}                              ║
║  {Fore.WHITE}架构: {Fore.CYAN}{sys.maxsize > 2**32 and '64-bit' or '32-bit'}{Fore.GREEN}                    ║
║  {Fore.WHITE}启动时间: {Fore.CYAN}{time.strftime('%Y-%m-%d %H:%M:%S')}{Fore.GREEN}              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(info)
    
    def _animation_loop(self):
        """动画循环"""
        frames = [
            "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"
        ]
        i = 0
        
        while self.running:
            frame = frames[i % len(frames)]
            print(f"\r{Fore.YELLOW}{frame} {Fore.WHITE}正在启动PyOS系统...{Style.RESET_ALL}", end="", flush=True)
            time.sleep(0.1)
            i += 1
        
        print(f"\r{Fore.GREEN}✓ {Fore.WHITE}PyOS系统启动完成!{Style.RESET_ALL}")

def show_progress_bar(title, duration=2):
    """显示进度条"""
    print(f"\n{Fore.CYAN}{title}{Style.RESET_ALL}")
    for i in range(101):
        bar_length = 50
        filled_length = int(bar_length * i // 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        percentage = i
        print(f'\r{Fore.GREEN}[{bar}]{Style.RESET_ALL} {percentage}%', end='', flush=True)
        time.sleep(duration / 100)
    print()

def show_startup_sequence():
    """显示启动序列"""
    startup_steps = [
        ("初始化系统核心", 1.5),
        ("加载内存管理器", 1.0),
        ("初始化文件系统", 1.2),
        ("启动设备管理器", 0.8),
        ("创建进程管理器", 1.0),
        ("启动调度器", 0.5),
        ("初始化Shell环境", 0.8)
    ]
    
    for step, duration in startup_steps:
        show_progress_bar(step, duration)

def show_welcome_message():
    """显示欢迎信息"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}    🎉 欢迎使用 PyOS 操作系统! 🎉")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}") 