"""
命令模块 - 实现Shell内置命令
"""

import os
import time
from typing import List, Optional, TYPE_CHECKING
from colorama import Fore, Back, Style

from utils.logger import Logger

if TYPE_CHECKING:
    from .shell import Shell

class Commands:
    """Shell命令处理器"""
    
    def __init__(self, shell: 'Shell'):
        """初始化命令处理器"""
        self.shell = shell
        self.logger = Logger()
    
    def ls(self, args: List[str]) -> str:
        """列出文件和目录"""
        # 解析参数
        show_hidden = '-a' in args or '-la' in args or '-al' in args
        show_details = '-l' in args or '-la' in args or '-al' in args
        
        # 获取目标目录
        target_dir = self.shell.current_directory
        for arg in args:
            if not arg.startswith('-'):
                if arg.startswith("/"):
                    target_dir = arg
                else:
                    target_dir = self.shell.system.vfs.get_absolute_path(self.shell.current_directory, arg)
                break
        
        try:
            # 检查目录是否存在
            if not self.shell.system.vfs.exists(target_dir):
                print(f"{Fore.RED}错误: 目录 '{target_dir}' 不存在{Style.RESET_ALL}")
                return ''
            
            if not self.shell.system.vfs.is_directory(target_dir):
                print(f"{Fore.RED}错误: '{target_dir}' 不是一个目录{Style.RESET_ALL}")
                return ''
            
            # 获取目录内容
            entries = self.shell.system.vfs.list_directory(target_dir)
            
            # 过滤隐藏文件
            if not show_hidden:
                entries = [e for e in entries if not e['name'].startswith('.')]
                
            if show_details:
                # 详细模式
                output = []
                for entry in entries:
                    # 格式化权限
                    perms = entry['permissions']
                    file_type = 'd' if entry['type'] == 'directory' else '-'
                    
                    # 格式化大小和修改时间
                    size = entry['size']
                    mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(entry['modified_time']))
                    
                    # 格式化输出
                    color = Fore.BLUE if entry['type'] == 'directory' else Style.RESET_ALL
                    output.append(f"{file_type}rw-r--r--  {size:8d}  {mtime}  {color}{entry['name']}{Style.RESET_ALL}")
                    
                print('\n'.join(output))
            else:
                # 简单模式
                for entry in entries:
                    color = Fore.BLUE if entry['type'] == 'directory' else Style.RESET_ALL
                    print(f"{color}{entry['name']}{Style.RESET_ALL}", end='  ')
                print()
                
            return ''
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            return ''
    
    def cd(self, args: List[str]) -> str:
        """切换目录"""
        if not args:
            # 切换到用户主目录
            home = self.shell.get_environment('HOME')
            assert home is not None, "HOME 环境变量未设置"
            target_path = home
        else:
            target_path = args[0]
        
        try:
            # 使用Shell的change_directory方法
            result = self.shell.change_directory(target_path)
            if result:
                print(f"{Fore.GREEN}已切换到: {self.shell.current_directory}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}错误: 目录 '{target_path}' 不存在{Style.RESET_ALL}")
            return ''
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"cd命令异常: {str(e)}")
            return ''
    
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
        
        # 解析路径
        if dir_name.startswith("/"):
            dir_path = dir_name
        else:
            dir_path = self.shell.system.vfs.get_absolute_path(self.shell.current_directory, dir_name)
        
        try:
            # 创建目录
            result = self.shell.system.vfs.create_directory(dir_path)
            
            if result:
                print(f"{Fore.GREEN}已创建目录: {dir_path}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}错误: 无法创建目录 '{dir_path}'{Style.RESET_ALL}")
            return ""
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"mkdir命令异常: {str(e)}")
            return ""
    
    def rm(self, args: List[str]) -> str:
        """删除文件或目录"""
        if not args:
            print(f"{Fore.RED}错误: 请指定要删除的文件或目录{Style.RESET_ALL}")
            return ""
        
        target = args[0]
        recursive = '-r' in args or '-R' in args
        
        # 解析路径
        if target.startswith("/"):
            target_path = target
        else:
            target_path = self.shell.system.vfs.get_absolute_path(self.shell.current_directory, target)
        
        try:
            # 检查是否存在
            if not self.shell.system.vfs.exists(target_path):
                print(f"{Fore.RED}错误: '{target}' 不存在{Style.RESET_ALL}")
                return ""
            
            # 删除文件或目录
            if self.shell.system.vfs.is_file(target_path):
                result = self.shell.system.vfs.delete_file(target_path)
                if result:
                    print(f"{Fore.GREEN}已删除文件: {target_path}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}错误: 无法删除文件 '{target_path}'{Style.RESET_ALL}")
            elif self.shell.system.vfs.is_directory(target_path):
                result = self.shell.system.vfs.delete_directory(target_path, recursive)
                if result:
                    print(f"{Fore.GREEN}已删除目录: {target_path}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}错误: 无法删除目录 '{target_path}' (可能不为空，使用 -r 递归删除){Style.RESET_ALL}")
            
            return ""
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            return ""
    
    def cat(self, args: List[str]) -> str:
        """显示文件内容"""
        if not args:
            print(f"{Fore.RED}错误: 请指定文件名{Style.RESET_ALL}")
            return ""
        
        filename = args[0]
        
        # 解析路径
        if filename.startswith("/"):
            file_path = filename
        else:
            file_path = self.shell.system.vfs.get_absolute_path(self.shell.current_directory, filename)
        
        try:
            # 检查文件是否存在
            if not self.shell.system.vfs.exists(file_path):
                print(f"{Fore.RED}错误: 文件 '{filename}' 不存在{Style.RESET_ALL}")
                return ""
            
            if not self.shell.system.vfs.is_file(file_path):
                print(f"{Fore.RED}错误: '{filename}' 不是文件{Style.RESET_ALL}")
                return ""
            
            # 读取文件内容
            content = self.shell.system.vfs.read_file(file_path)
            if content is not None:
                print(content)
                return content
            else:
                print(f"{Fore.RED}错误: 无法读取文件 '{filename}'{Style.RESET_ALL}")
                return ""
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            return ""
    
    def echo(self, args: List[str]) -> str:
        """输出文本"""
        if not args:
            return ""

        # 简单输出文本，重定向由Shell层面处理
        text = " ".join(args)
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
        assert user is not None, "USER 环境变量未设置"
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
    
    def version(self, args: List[str]) -> str:
        """显示版本信息"""
        print(f"{Fore.CYAN}PyOS 版本 1.0.0{Style.RESET_ALL}")
        print("一个用Python实现的简单操作系统模拟器")
        return "PyOS 1.0.0"
    
    def tree(self, args: List[str]) -> str:
        """显示目录树"""
        # 解析参数
        max_depth = 3
        target_dir = self.shell.current_directory
        
        for i, arg in enumerate(args):
            if arg == '-d' and i + 1 < len(args):
                try:
                    max_depth = int(args[i + 1])
                except ValueError:
                    print(f"{Fore.RED}错误: 无效的深度值 '{args[i + 1]}'{Style.RESET_ALL}")
                    return ""
            elif not arg.startswith('-') and arg.isdigit() == False:
                if arg.startswith("/"):
                    target_dir = arg
                else:
                    target_dir = self.shell.system.vfs.get_absolute_path(self.shell.current_directory, arg)
        
        try:
            if not self.shell.system.vfs.exists(target_dir):
                print(f"{Fore.RED}错误: 目录 '{target_dir}' 不存在{Style.RESET_ALL}")
                return ""
            
            if not self.shell.system.vfs.is_directory(target_dir):
                print(f"{Fore.RED}错误: '{target_dir}' 不是目录{Style.RESET_ALL}")
                return ""
            
            print(f"{Fore.CYAN}目录树: {target_dir}{Style.RESET_ALL}")
            self.shell.system.vfs.print_tree(target_dir, "", max_depth)
            return ""
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            return ""
    
    def touch(self, args: List[str]) -> str:
        """创建空文件"""
        if not args:
            print(f"{Fore.RED}错误: 请指定文件名{Style.RESET_ALL}")
            return ""
        
        filename = args[0]
        
        # 解析路径
        if filename.startswith("/"):
            file_path = filename
        else:
            file_path = self.shell.system.vfs.get_absolute_path(self.shell.current_directory, filename)
        
        try:
            # 检查文件是否已存在
            if self.shell.system.vfs.exists(file_path):
                print(f"{Fore.YELLOW}文件 '{filename}' 已存在{Style.RESET_ALL}")
                return ""
            
            # 创建空文件
            result = self.shell.system.vfs.create_file(file_path, "")
            if result:
                print(f"{Fore.GREEN}已创建文件: {file_path}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}错误: 无法创建文件 '{filename}'{Style.RESET_ALL}")
            return ""
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            return ""
    
    def vfs_info(self, args: List[str]) -> str:
        """显示虚拟文件系统信息"""
        try:
            stats = self.shell.system.vfs.get_stats()
            
            print(f"\n{Fore.CYAN}虚拟文件系统信息:{Style.RESET_ALL}")
            print("-" * 40)
            print(f"总文件数: {stats['total_files']}")
            print(f"总目录数: {stats['total_directories']}")
            print(f"总大小: {stats['total_size']} bytes")
            print(f"当前目录: {self.shell.current_directory}")
            print("-" * 40)
            
            return ""
            
        except Exception as e:
            print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
            return ""