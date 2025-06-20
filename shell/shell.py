"""
Shell核心模块 - 实现命令行界面
"""

import threading
from typing import List, Optional, Dict, Any
from colorama import Fore, Back, Style

from kernel.system import System
from .commands import Commands
from .parser import CommandParser
from utils.logger import Logger

class Shell:
    """Shell核心类"""
    
    def __init__(self, system: System):
        """初始化Shell"""
        self.system = system
        self.running = False
        self.current_directory = "/"
        self.command_history: List[str] = []
        self.history_index = 0
        self.max_history = 100
        
        # 命令处理
        self.commands = Commands(self)
        self.parser = CommandParser()
        
        # 环境变量
        self.environment: Dict[str, str] = {
            'PATH': '/bin:/usr/bin',
            'HOME': '/home',
            'USER': 'user',
            'SHELL': '/bin/pyos'
        }
        
        self.logger = Logger()
        self.logger.info("Shell初始化完成")
    
    def run(self):
        """运行Shell"""
        self.running = True
        self.logger.info("Shell启动")
        
        print(f"{Fore.GREEN}欢迎使用PyOS Shell!{Style.RESET_ALL}")
        print(f"输入 'help' 查看可用命令，输入 'exit' 退出系统")
        print()
        
        while self.running:
            try:
                # 显示提示符
                prompt = self._get_prompt()
                command = input(prompt)
                
                # 处理命令
                if command.strip():
                    self._execute_command(command)
                    
            except KeyboardInterrupt:
                print("\n使用 'exit' 命令退出系统")
            except EOFError:
                print("\n使用 'exit' 命令退出系统")
            except Exception as e:
                print(f"{Fore.RED}Shell错误: {e}{Style.RESET_ALL}")
                self.logger.error(f"Shell错误: {e}")
    
    def _get_prompt(self) -> str:
        """获取命令提示符"""
        # 获取系统信息
        system_info = self.system.get_system_info()
        uptime = int(system_info.get('uptime', 0))
        
        # 格式化提示符
        prompt = f"{Fore.CYAN}PyOS{Style.RESET_ALL}:{Fore.YELLOW}{self.current_directory}{Style.RESET_ALL} "
        
        # 可选：显示系统状态
        if system_info.get('process_count', 0) > 0:
            prompt += f"[{system_info['process_count']}进程] "
        
        return prompt
    
    def _execute_command(self, command: str):
        """执行命令"""
        # 添加到历史记录
        self._add_to_history(command)
        
        # 解析命令
        try:
            parsed = self.parser.parse(command)
            if parsed:
                cmd_name, args, redirects = parsed
                self._run_command(cmd_name, args, redirects)
            else:
                print(f"{Fore.RED}命令解析错误{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}命令执行错误: {e}{Style.RESET_ALL}")
            self.logger.error(f"命令执行错误: {e}")
    
    def _run_command(self, command: str, args: List[str], redirects: Dict[str, str]):
        """运行具体命令"""
        # 检查是否是内置命令
        if hasattr(self.commands, command):
            try:
                method = getattr(self.commands, command)
                result = method(args)
                
                # 处理重定向
                if redirects:
                    self._handle_redirects(result, redirects)
                    
            except Exception as e:
                print(f"{Fore.RED}命令 '{command}' 执行失败: {e}{Style.RESET_ALL}")
                self.logger.error(f"命令执行失败: {command} - {e}")
        else:
            print(f"{Fore.RED}未知命令: {command}{Style.RESET_ALL}")
            print(f"输入 'help' 查看可用命令")
    
    def _handle_redirects(self, output: str, redirects: Dict[str, str]):
        """处理输出重定向"""
        # TODO: 实现输出重定向
        # 1. 处理标准输出重定向 (>)
        # 2. 处理标准错误重定向 (2>)
        # 3. 处理追加重定向 (>>)
        pass
    
    def _add_to_history(self, command: str):
        """添加命令到历史记录"""
        if command.strip() and (not self.command_history or command != self.command_history[-1]):
            self.command_history.append(command)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
            self.history_index = len(self.command_history)
    
    def get_history(self, count: int = 10) -> List[str]:
        """获取命令历史"""
        return self.command_history[-count:] if count > 0 else self.command_history.copy()
    
    def set_environment(self, key: str, value: str):
        """设置环境变量"""
        self.environment[key] = value
        self.logger.info(f"设置环境变量: {key}={value}")
    
    def get_environment(self, key: str) -> Optional[str]:
        """获取环境变量"""
        return self.environment.get(key)
    
    def change_directory(self, path: str) -> bool:
        """切换当前目录"""
        # TODO: 实现目录切换
        # 1. 验证路径是否存在
        # 2. 更新当前目录
        # 3. 更新环境变量PWD
        old_dir = self.current_directory
        self.current_directory = path
        self.set_environment('PWD', path)
        self.logger.info(f"切换目录: {old_dir} -> {path}")
        return True
    
    def get_current_directory(self) -> str:
        """获取当前目录"""
        return self.current_directory
    
    def stop(self):
        """停止Shell"""
        self.running = False
        self.logger.info("Shell停止")
    
    def print_system_info(self):
        """打印系统信息"""
        info = self.system.get_system_info()
        print(f"\n{Fore.CYAN}系统信息:{Style.RESET_ALL}")
        print(f"版本: {info.get('version', 'Unknown')}")
        print(f"运行时间: {int(info.get('uptime', 0))} 秒")
        print(f"进程数: {info.get('process_count', 0)}")
        print(f"内存使用: {info.get('memory_usage', 0):.1f}%")
        print(f"CPU使用: {info.get('cpu_usage', 0):.1f}%")
        print(f"当前目录: {self.current_directory}")
        print(f"用户: {self.get_environment('USER')}")
    
    def print_help(self):
        """打印帮助信息"""
        print(f"\n{Fore.CYAN}PyOS Shell 帮助{Style.RESET_ALL}")
        print("=" * 40)
        print("基本命令:")
        print("  ls              - 列出文件和目录")
        print("  cd <目录>       - 切换目录")
        print("  pwd             - 显示当前目录")
        print("  mkdir <目录>    - 创建目录")
        print("  rm <文件>       - 删除文件")
        print("  cat <文件>      - 显示文件内容")
        print("  echo <文本>     - 输出文本")
        print("  ps              - 显示进程信息")
        print("  kill <PID>      - 终止进程")
        print("  clear           - 清屏")
        print("  help            - 显示此帮助")
        print("  exit            - 退出系统")
        print()
        print("系统命令:")
        print("  info            - 显示系统信息")
        print("  history         - 显示命令历史")
        print("  env             - 显示环境变量")
        print()
        print("示例:")
        print("  ls -la          - 详细列出文件")
        print("  echo hello > file.txt  - 重定向输出")
        print("  ps | grep python       - 管道操作") 