"""
目录管理模块 - 实现目录结构管理
"""

import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .inode import Inode, FileType
from utils.logger import Logger

class DirectoryEntry:
    """目录项"""
    
    def __init__(self, name: str, inode_number: int, entry_type: FileType = FileType.REGULAR):
        self.name = name
        self.inode_number = inode_number
        self.entry_type = entry_type
        self.entry_length = 0
        self.name_length = len(name)
        self.created_time = time.time()
    
    def get_info(self) -> Dict:
        """获取目录项信息"""
        return {
            'name': self.name,
            'inode_number': self.inode_number,
            'entry_type': self.entry_type.value,
            'name_length': self.name_length,
            'created_time': self.created_time
        }

class Directory:
    """目录类"""
    
    def __init__(self, name: str, parent: Optional['Directory'] = None):
        """初始化目录"""
        self.name = name
        self.parent = parent
        self.path = self._build_path()
        
        # 目录项
        self.entries: Dict[str, DirectoryEntry] = {}
        
        # 目录inode
        self.inode = None  # 将在文件系统中设置
        
        # 时间戳
        self.created_time = time.time()
        self.modified_time = time.time()
        self.accessed_time = time.time()
        
        self.logger = Logger()
        
        # 添加 . 和 .. 目录项
        if parent:
            self.entries['.'] = DirectoryEntry('.', 0, FileType.DIRECTORY)
            self.entries['..'] = DirectoryEntry('..', 0, FileType.DIRECTORY)
    
    def _build_path(self) -> str:
        """构建完整路径"""
        if self.parent is None:
            return self.name
        else:
            parent_path = self.parent.path
            if parent_path == '/':
                return f"/{self.name}"
            else:
                return f"{parent_path}/{self.name}"
    
    def add_entry(self, name: str, inode_number: int, entry_type: FileType = FileType.REGULAR) -> bool:
        """添加目录项"""
        if name in self.entries:
            self.logger.warning(f"目录项已存在: {name}")
            return False
        
        entry = DirectoryEntry(name, inode_number, entry_type)
        self.entries[name] = entry
        self.modified_time = time.time()
        
        self.logger.log_file_event(f"添加目录项: {self.path}/{name} -> inode {inode_number}")
        return True
    
    def remove_entry(self, name: str) -> bool:
        """移除目录项"""
        if name not in self.entries:
            self.logger.warning(f"目录项不存在: {name}")
            return False
        
        if name in ['.', '..']:
            self.logger.warning(f"无法删除特殊目录项: {name}")
            return False
        
        del self.entries[name]
        self.modified_time = time.time()
        
        self.logger.log_file_event(f"移除目录项: {self.path}/{name}")
        return True
    
    def get_entry(self, name: str) -> Optional[DirectoryEntry]:
        """获取目录项"""
        return self.entries.get(name)
    
    def has_entry(self, name: str) -> bool:
        """检查目录项是否存在"""
        return name in self.entries
    
    def list_entries(self) -> List[DirectoryEntry]:
        """列出所有目录项"""
        return list(self.entries.values())
    
    def get_entry_names(self) -> List[str]:
        """获取所有目录项名称"""
        return list(self.entries.keys())
    
    def get_subdirectories(self) -> List[str]:
        """获取子目录名称"""
        subdirs = []
        for name, entry in self.entries.items():
            if entry.entry_type == FileType.DIRECTORY and name not in ['.', '..']:
                subdirs.append(name)
        return subdirs
    
    def get_files(self) -> List[str]:
        """获取文件名称"""
        files = []
        for name, entry in self.entries.items():
            if entry.entry_type == FileType.REGULAR:
                files.append(name)
        return files
    
    def get_entry_count(self) -> int:
        """获取目录项数量"""
        return len(self.entries)
    
    def is_empty(self) -> bool:
        """检查目录是否为空"""
        return len(self.entries) <= 2  # 只有 . 和 ..
    
    def get_size(self) -> int:
        """获取目录大小"""
        return len(self.entries) * 64  # 假设每个目录项64字节
    
    def update_access_time(self):
        """更新访问时间"""
        self.accessed_time = time.time()
    
    def update_modification_time(self):
        """更新修改时间"""
        self.modified_time = time.time()
    
    def get_info(self) -> Dict:
        """获取目录信息"""
        return {
            'name': self.name,
            'path': self.path,
            'parent': self.parent.name if self.parent else None,
            'entry_count': self.get_entry_count(),
            'subdirectories': self.get_subdirectories(),
            'files': self.get_files(),
            'size': self.get_size(),
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'accessed_time': self.accessed_time,
            'is_empty': self.is_empty()
        }
    
    def print_info(self):
        """打印目录信息"""
        info = self.get_info()
        print(f"\n目录信息: {info['path']}")
        print("-" * 50)
        print(f"名称: {info['name']}")
        print(f"路径: {info['path']}")
        print(f"父目录: {info['parent']}")
        print(f"目录项数: {info['entry_count']}")
        print(f"子目录: {info['subdirectories']}")
        print(f"文件: {info['files']}")
        print(f"大小: {info['size']} bytes")
        print(f"是否为空: {info['is_empty']}")
        print(f"创建时间: {time.ctime(info['created_time'])}")
        print(f"修改时间: {time.ctime(info['modified_time'])}")
        print(f"访问时间: {time.ctime(info['accessed_time'])}")
    
    def print_contents(self, show_hidden: bool = False):
        """打印目录内容"""
        print(f"\n目录内容: {self.path}")
        print("-" * 60)
        print(f"{'类型':<8} {'名称':<20} {'Inode':<8} {'大小':<10}")
        print("-" * 60)
        
        for name, entry in sorted(self.entries.items()):
            if not show_hidden and name.startswith('.'):
                continue
            
            entry_type = entry.entry_type.value[:7]
            print(f"{entry_type:<8} {name:<20} {entry.inode_number:<8} {'N/A':<10}")
        
        print("-" * 60)
        print(f"总计: {len(self.entries)} 项")

class DirectoryTree:
    """目录树"""
    
    def __init__(self):
        """初始化目录树"""
        self.root = Directory("/")
        self.current_directory = self.root
        self.logger = Logger()
    
    def create_directory(self, path: str) -> Optional[Directory]:
        """创建目录"""
        # 解析路径
        parts = self._parse_path(path)
        if not parts:
            return None
        
        # 查找父目录
        parent = self._find_parent_directory(parts[:-1])
        if not parent:
            self.logger.error(f"父目录不存在: {path}")
            return None
        
        dir_name = parts[-1]
        if parent.has_entry(dir_name):
            self.logger.warning(f"目录已存在: {path}")
            return None
        
        # 创建新目录
        new_dir = Directory(dir_name, parent)
        parent.add_entry(dir_name, 0, FileType.DIRECTORY)  # inode号将在文件系统中设置
        
        self.logger.log_file_event(f"创建目录: {path}")
        return new_dir
    
    def remove_directory(self, path: str) -> bool:
        """删除目录"""
        # 解析路径
        parts = self._parse_path(path)
        if not parts:
            return False
        
        # 查找目录
        directory = self._find_directory(parts)
        if not directory:
            self.logger.error(f"目录不存在: {path}")
            return False
        
        if not directory.is_empty():
            self.logger.error(f"目录不为空: {path}")
            return False
        
        # 从父目录移除
        parent = directory.parent
        if parent:
            parent.remove_entry(directory.name)
            self.logger.log_file_event(f"删除目录: {path}")
            return True
        
        return False
    
    def change_directory(self, path: str) -> bool:
        """切换目录"""
        if path == "/":
            self.current_directory = self.root
            return True
        
        # 解析路径
        parts = self._parse_path(path)
        if not parts:
            return False
        
        # 查找目录
        directory = self._find_directory(parts)
        if not directory:
            self.logger.error(f"目录不存在: {path}")
            return False
        
        self.current_directory = directory
        self.logger.log_file_event(f"切换目录: {path}")
        return True
    
    def get_current_path(self) -> str:
        """获取当前路径"""
        return self.current_directory.path
    
    def list_directory(self, path: str = None) -> List[DirectoryEntry]:
        """列出目录内容"""
        if path is None:
            directory = self.current_directory
        else:
            parts = self._parse_path(path)
            if not parts:
                return []
            directory = self._find_directory(parts)
            if not directory:
                return []
        
        return directory.list_entries()
    
    def _parse_path(self, path: str) -> List[str]:
        """解析路径"""
        if not path:
            return []
        
        # 处理绝对路径和相对路径
        if path.startswith('/'):
            parts = path.split('/')[1:]  # 移除开头的空字符串
        else:
            # 相对路径，从当前目录开始
            current_parts = self.current_directory.path.split('/')[1:]
            relative_parts = path.split('/')
            parts = current_parts + relative_parts
        
        # 处理 . 和 ..
        result = []
        for part in parts:
            if part == '.':
                continue
            elif part == '..':
                if result:
                    result.pop()
            elif part:
                result.append(part)
        
        return result
    
    def _find_directory(self, parts: List[str]) -> Optional[Directory]:
        """根据路径部分查找目录"""
        current = self.root
        
        for part in parts:
            if not current.has_entry(part):
                return None
            
            entry = current.get_entry(part)
            if entry.entry_type != FileType.DIRECTORY:
                return None
            
            # 这里需要从文件系统获取实际的目录对象
            # 临时实现：返回None
            return None
        
        return current
    
    def _find_parent_directory(self, parts: List[str]) -> Optional[Directory]:
        """查找父目录"""
        if not parts:
            return self.root
        
        return self._find_directory(parts)
    
    def print_tree(self, directory: Directory = None, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        """打印目录树"""
        if directory is None:
            directory = self.root
        
        if current_depth >= max_depth:
            return
        
        entries = directory.list_entries()
        for i, entry in enumerate(entries):
            if entry.name in ['.', '..']:
                continue
            
            is_last = i == len(entries) - 1
            current_prefix = prefix + ("└── " if is_last else "├── ")
            
            print(f"{current_prefix}{entry.name}")
            
            if entry.entry_type == FileType.DIRECTORY:
                # 递归打印子目录
                next_prefix = prefix + ("    " if is_last else "│   ")
                # 这里需要获取实际的子目录对象
                # 临时实现：跳过子目录
                pass 