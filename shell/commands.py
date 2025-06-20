"""
命令模块 - 实现Shell内置命令
"""

import os
import time
from typing import List, Optional
from colorama import Fore, Back, Style

from .shell import Shell
from utils.logger import Logger

class Commands:
    """Shell命令处理器"""
    
    def __init__(self, shell: Shell):
        """初始化命令处理器"""
        self.shell = shell
        self.logger = Logger()
    
    def ls(self, args: List[str]) -> str:
        """列出文件和目录"""
        # TODO: 实现ls命令
        # 1. 解析参数 (-l, -a, -la等)
        # 2. 获取目录内容
        # 3. 格式化输出
        print(f"{Fore.BLUE}ls{Style.RESET_ALL} 命令 - 参数: {args}")
        print("文件列表功能待实现...")
        return ""
    
    def cd(self, args: List[str]) -> str:
        """切换目录"""
        if not args:
            # 切换到用户主目录
            home = self.shell.get_environment('HOME')
            return self.shell.change_directory(home)
        
        path = args[0]
        # TODO: 实现目录切换逻辑
        # 1. 解析路径（相对/绝对）
        # 2. 验证目录是否存在
        # 3. 更新当前目录
        print(f"{Fore.BLUE}cd{Style.RESET_ALL} 命令 - 切换到: {path}")
        return self.shell.change_directory(path)
    
    def pwd(self, args: List[str]) -> str:
        """显示当前目录"""
        current_dir = self.shell.get_current_directory()
        print(f"{Fore.GREEN}当前目录: {current_dir}{Style.RESET_ALL}")
        return current_dir
    
    def mkdir(self, args: List[str]) -> str:
        """创建目录"""
        if not args:
            print(f"{Fore.RED}错误: 请指定目录名{Style.RESET_ALL}")
            return ""
        
        dir_name = args[0]
        # TODO: 实现目录创建
        # 1. 检查目录是否已存在
        # 2. 创建目录
        # 3. 更新文件系统
        print(f"{Fore.BLUE}mkdir{Style.RESET_ALL} 命令 - 创建目录: {dir_name}")
        return ""
    
    def rm(self, args: List[str]) -> str:
        """删除文件或目录"""
        if not args:
            print(f"{Fore.RED}错误: 请指定要删除的文件或目录{Style.RESET_ALL}")
            return ""
        
        target = args[0]
        recursive = '-r' in args or '-R' in args
        
        # TODO: 实现删除功能
        # 1. 检查文件/目录是否存在
        # 2. 检查权限
        # 3. 执行删除
        print(f"{Fore.BLUE}rm{Style.RESET_ALL} 命令 - 删除: {target} {'(递归)' if recursive else ''}")
        return ""
    
    def cat(self, args: List[str]) -> str:
        """显示文件内容"""
        if not args:
            print(f"{Fore.RED}错误: 请指定文件名{Style.RESET_ALL}")
            return ""
        
        filename = args[0]
        # TODO: 实现文件读取
        # 1. 检查文件是否存在
        # 2. 读取文件内容
        # 3. 显示内容
        print(f"{Fore.BLUE}cat{Style.RESET_ALL} 命令 - 显示文件: {filename}")
        print("文件内容功能待实现...")
        return ""
    
    def echo(self, args: List[str]) -> str:
        """输出文本"""
        text = " ".join(args) if args else ""
        print(text)
        return text
    
    def ps(self, args: List[str]) -> str:
        """显示进程信息"""
        # TODO: 实现进程列表
        # 1. 获取所有进程
        # 2. 格式化显示
        # 3. 支持参数过滤
        print(f"{Fore.BLUE}ps{Style.RESET_ALL} 命令 - 显示进程信息")
        print("进程列表功能待实现...")
        return ""
    
    def kill(self, args: List[str]) -> str:
        """终止进程"""
        if not args:
            print(f"{Fore.RED}错误: 请指定进程ID{Style.RESET_ALL}")
            return ""
        
        try:
            pid = int(args[0])
            # TODO: 实现进程终止
            # 1. 检查进程是否存在
            # 2. 发送终止信号
            # 3. 等待进程结束
            print(f"{Fore.BLUE}kill{Style.RESET_ALL} 命令 - 终止进程: {pid}")
        except ValueError:
            print(f"{Fore.RED}错误: 无效的进程ID{Style.RESET_ALL}")
        
        return ""
    
    def clear(self, args: List[str]) -> str:
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
        return ""
    
    def help(self, args: List[str]) -> str:
        """显示帮助信息"""
        self.shell.print_help()
        return ""
    
    def exit(self, args: List[str]) -> str:
        """退出系统"""
        print(f"{Fore.YELLOW}正在退出PyOS...{Style.RESET_ALL}")
        self.shell.stop()
        self.shell.system.shutdown()
        return ""
    
    def info(self, args: List[str]) -> str:
        """显示系统信息"""
        self.shell.print_system_info()
        return ""
    
    def history(self, args: List[str]) -> str:
        """显示命令历史"""
        count = 10
        if args:
            try:
                count = int(args[0])
            except ValueError:
                pass
        
        history = self.shell.get_history(count)
        print(f"\n{Fore.CYAN}命令历史 (最近 {len(history)} 条):{Style.RESET_ALL}")
        for i, cmd in enumerate(history, 1):
            print(f"{i:3d}  {cmd}")
        return ""
    
    def env(self, args: List[str]) -> str:
        """显示环境变量"""
        print(f"\n{Fore.CYAN}环境变量:{Style.RESET_ALL}")
        for key, value in self.shell.environment.items():
            print(f"{key}={value}")
        return ""
    
    def date(self, args: List[str]) -> str:
        """显示当前日期时间"""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.GREEN}当前时间: {current_time}{Style.RESET_ALL}")
        return current_time
    
    def whoami(self, args: List[str]) -> str:
        """显示当前用户"""
        user = self.shell.get_environment('USER')
        print(f"{Fore.GREEN}当前用户: {user}{Style.RESET_ALL}")
        return user
    
    def grep(self, args: List[str]) -> str:
        """文本搜索"""
        if len(args) < 2:
            print(f"{Fore.RED}错误: 用法: grep <模式> <文件>{Style.RESET_ALL}")
            return ""
        
        pattern = args[0]
        filename = args[1]
        
        # TODO: 实现grep功能
        # 1. 读取文件
        # 2. 搜索模式
        # 3. 显示匹配行
        print(f"{Fore.BLUE}grep{Style.RESET_ALL} 命令 - 搜索 '{pattern}' 在文件 '{filename}' 中")
        return ""
    
    def head(self, args: List[str]) -> str:
        """显示文件开头"""
        if not args:
            print(f"{Fore.RED}错误: 请指定文件名{Style.RESET_ALL}")
            return ""
        
        filename = args[0]
        lines = 10
        if len(args) > 1 and args[0].startswith('-'):
            try:
                lines = int(args[0][1:])
                filename = args[1]
            except ValueError:
                pass
        
        # TODO: 实现head功能
        print(f"{Fore.BLUE}head{Style.RESET_ALL} 命令 - 显示文件 '{filename}' 的前 {lines} 行")
        return ""
    
    def tail(self, args: List[str]) -> str:
        """显示文件结尾"""
        if not args:
            print(f"{Fore.RED}错误: 请指定文件名{Style.RESET_ALL}")
            return ""
        
        filename = args[0]
        lines = 10
        if len(args) > 1 and args[0].startswith('-'):
            try:
                lines = int(args[0][1:])
                filename = args[1]
            except ValueError:
                pass
        
        # TODO: 实现tail功能
        print(f"{Fore.BLUE}tail{Style.RESET_ALL} 命令 - 显示文件 '{filename}' 的后 {lines} 行")
        return "" 