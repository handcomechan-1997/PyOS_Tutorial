"""
命令解析器模块 - 解析Shell命令
"""

import re
from typing import List, Dict, Optional, Tuple

class CommandParser:
    """命令解析器"""
    
    def __init__(self):
        """初始化命令解析器"""
        # 重定向模式
        self.redirect_pattern = re.compile(r'([0-9]*)([><])(.*)')
        # 管道模式
        self.pipe_pattern = re.compile(r'\s*\|\s*')
        # 引号模式
        self.quote_pattern = re.compile(r'["\'](.*?)["\']')
    
    def parse(self, command: str) -> Optional[Tuple[str, List[str], Dict[str, str]]]:
        """解析命令字符串"""
        if not command.strip():
            return None
        
        try:
            # 分离命令和重定向
            parts = self._split_command_and_redirects(command)
            if not parts:
                return None
            
            command_part, redirects = parts
            
            # 解析命令和参数
            cmd_parts = self._parse_command_parts(command_part)
            if not cmd_parts:
                return None
            
            command_name = cmd_parts[0]
            args = cmd_parts[1:]
            
            return command_name, args, redirects
            
        except Exception as e:
            print(f"命令解析错误: {e}")
            return None
    
    def _split_command_and_redirects(self, command: str) -> Optional[Tuple[str, Dict[str, str]]]:
        """分离命令和重定向"""
        redirects = {}
        command_parts = []
        
        # 分割命令
        parts = command.split()
        i = 0
        
        while i < len(parts):
            part = parts[i]
            
            # 检查是否是重定向
            match = self.redirect_pattern.match(part)
            if match:
                fd, operator, filename = match.groups()
                
                # 处理文件描述符
                if fd == '':
                    fd = '1' if operator == '>' else '0'
                else:
                    fd = fd
                
                # 处理文件名
                if not filename:
                    # 重定向符号和文件名分开的情况
                    if i + 1 < len(parts):
                        filename = parts[i + 1]
                        i += 1
                    else:
                        print("错误: 重定向缺少文件名")
                        return None
                
                # 移除引号
                filename = filename.strip('"\'')
                
                # 存储重定向信息
                if operator == '>':
                    redirects[f'{fd}>'] = filename
                elif operator == '<':
                    redirects[f'{fd}<'] = filename
                elif operator == '>>':
                    redirects[f'{fd}>>'] = filename
                elif operator == '2>':
                    redirects['2>'] = filename
                elif operator == '2>>':
                    redirects['2>>'] = filename
                
            else:
                command_parts.append(part)
            
            i += 1
        
        return ' '.join(command_parts), redirects
    
    def _parse_command_parts(self, command: str) -> List[str]:
        """解析命令部分"""
        # 处理引号
        parts = []
        current_part = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(command):
            char = command[i]
            
            if char in ['"', "'"]:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                else:
                    # 引号内的其他引号
                    current_part += char
            elif char.isspace() and not in_quotes:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char
            
            i += 1
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    def parse_pipeline(self, command: str) -> List[Tuple[str, List[str], Dict[str, str]]]:
        """解析管道命令"""
        if '|' not in command:
            # 没有管道，直接解析
            result = self.parse(command)
            return [result] if result else []
        
        # 分割管道
        pipeline_parts = self.pipe_pattern.split(command)
        pipeline = []
        
        for part in pipeline_parts:
            if part.strip():
                result = self.parse(part.strip())
                if result:
                    pipeline.append(result)
        
        return pipeline
    
    def parse_conditional(self, command: str) -> List[Tuple[str, List[Tuple[str, List[str], Dict[str, str]]]]]:
        """解析条件命令 (&&, ||)"""
        # TODO: 实现条件命令解析
        # 1. 分割 && 和 ||
        # 2. 解析每个子命令
        # 3. 返回条件结构
        pass
    
    def expand_variables(self, text: str, environment: Dict[str, str]) -> str:
        """展开环境变量"""
        # TODO: 实现环境变量展开
        # 1. 查找 $VAR 模式
        # 2. 替换为环境变量值
        # 3. 处理默认值 ${VAR:-default}
        return text
    
    def expand_wildcards(self, pattern: str) -> List[str]:
        """展开通配符"""
        # TODO: 实现通配符展开
        # 1. 处理 * 和 ? 通配符
        # 2. 匹配文件系统
        # 3. 返回匹配的文件列表
        return [pattern]
    
    def validate_command(self, command_name: str, args: List[str]) -> bool:
        """验证命令"""
        # TODO: 实现命令验证
        # 1. 检查命令是否存在
        # 2. 验证参数数量
        # 3. 检查参数类型
        return True
    
    def get_command_help(self, command_name: str) -> str:
        """获取命令帮助"""
        help_texts = {
            'ls': '列出文件和目录\n用法: ls [选项] [目录]\n选项: -l 详细列表, -a 显示隐藏文件',
            'cd': '切换目录\n用法: cd [目录]\n不带参数时切换到主目录',
            'pwd': '显示当前目录\n用法: pwd',
            'mkdir': '创建目录\n用法: mkdir [目录名]',
            'rm': '删除文件或目录\n用法: rm [选项] 文件...\n选项: -r 递归删除',
            'cat': '显示文件内容\n用法: cat [文件]',
            'echo': '输出文本\n用法: echo [文本]',
            'ps': '显示进程信息\n用法: ps [选项]',
            'kill': '终止进程\n用法: kill [PID]',
            'help': '显示帮助信息\n用法: help [命令]',
            'exit': '退出系统\n用法: exit',
        }
        
        return help_texts.get(command_name, f"命令 '{command_name}' 没有帮助信息") 