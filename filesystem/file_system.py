"""
文件系统核心模块 - 实现基本的文件系统功能
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from utils.logger import Logger

class FileType(Enum):
    """文件类型枚举"""
    REGULAR = "regular"
    DIRECTORY = "directory"
    SYMBOLIC_LINK = "symlink"

class FileSystem:
    """文件系统核心

    提供一个极简的文件系统接口，重点在于演示路径解析、文件打开/关闭
    等基本概念。实际的数据存储由学习者根据需要自行实现。
    """
    
    def __init__(self):
        """初始化文件系统"""
        self.logger = Logger()
        self.root_directory = None  # 将在Directory类中实现
        self.current_directory = None
        self.open_files: Dict[int, 'File'] = {}
        self.next_file_descriptor = 1
        self.lock = threading.Lock()
        
        # 文件系统统计
        self.total_files = 0
        self.total_directories = 0
        self.total_size = 0
        
        self.logger.info("文件系统初始化")
    
    def initialize(self):
        """初始化文件系统

        教学项目中可以逐步实现真正的目录结构。当前实现仅记录日志以
        表明初始化流程。
        """
        # TODO: 创建根目录并设置当前目录
        # self.root_directory = Directory("/", None)
        # self.current_directory = self.root_directory
        self.logger.info("文件系统初始化完成")
    
    def create_file(self, path: str, content: str = "") -> bool:
        """创建文件

        该方法展示了创建文件的一般步骤，具体逻辑可作为练习完成。
        """
        # TODO: 实现文件创建
        # 1. 解析路径
        # 2. 检查父目录是否存在
        # 3. 创建文件并写入初始内容
        # 4. 更新统计信息
        self.logger.log_file_event(f"创建文件: {path}")
        return True
    
    def read_file(self, path: str) -> str:
        """读取文件内容

        返回指定文件的文本内容，如果文件不存在应抛出异常或返回空
        字符串，具体行为由学习者决定。
        """
        # TODO: 实现文件读取
        # 1. 解析路径
        # 2. 检查文件是否存在
        # 3. 读取文件内容
        self.logger.log_file_event(f"读取文件: {path}")
        return ""
    
    def write_file(self, path: str, content: str) -> bool:
        """写入文件内容

        将数据写入已有文件并更新统计信息。
        """
        # TODO: 实现文件写入
        # 1. 解析路径
        # 2. 检查文件是否存在
        # 3. 写入文件内容
        self.logger.log_file_event(f"写入文件: {path}")
        return True
    
    def delete_file(self, path: str) -> bool:
        """删除文件

        删除指定路径的文件并更新统计信息。
        """
        # TODO: 实现文件删除
        # 1. 解析路径
        # 2. 检查文件是否存在
        # 3. 删除文件
        # 4. 更新统计信息
        self.logger.log_file_event(f"删除文件: {path}")
        return True
    
    def create_directory(self, path: str) -> bool:
        """创建目录

        与 ``mkdir`` 命令类似，需要检查父目录并在结构中添加新目录。
        """
        # TODO: 实现目录创建
        # 1. 解析路径
        # 2. 检查父目录是否存在
        # 3. 创建目录
        self.logger.log_file_event(f"创建目录: {path}")
        return True
    
    def delete_directory(self, path: str) -> bool:
        """删除目录

        删除目录前需要确保其为空，以防止数据丢失。
        """
        # TODO: 实现目录删除
        # 1. 解析路径
        # 2. 检查目录是否为空
        # 3. 删除目录
        self.logger.log_file_event(f"删除目录: {path}")
        return True
    
    def list_directory(self, path: str = ".") -> List[str]:
        """列出目录内容

        返回给定目录下的文件和子目录名称列表。
        """
        # TODO: 实现目录列表
        # 1. 解析路径
        # 2. 获取目录内容
        # 3. 返回文件列表
        self.logger.log_file_event(f"列出目录: {path}")
        return []
    
    def change_directory(self, path: str) -> bool:
        """切换目录

        修改 ``current_directory`` 指针以表示用户当前所在的位置。
        """
        # TODO: 实现目录切换
        # 1. 解析路径
        # 2. 检查目录是否存在
        # 3. 更新当前目录
        self.logger.log_file_event(f"切换目录: {path}")
        return True
    
    def get_current_directory(self) -> str:
        """获取当前目录

        返回当前工作目录的路径字符串。
        """
        # TODO: 返回当前目录路径
        return "/"
    
    def open_file(self, path: str, mode: str = "r") -> int:
        """打开文件

        返回一个简化的文件描述符，后续操作通过该描述符进行。
        """
        # TODO: 实现文件打开
        # 1. 解析路径
        # 2. 检查文件是否存在或根据模式创建
        # 3. 创建文件描述符并保存到 ``open_files``
        fd = self.next_file_descriptor
        self.next_file_descriptor += 1
        self.logger.log_file_event(f"打开文件: {path}, 模式: {mode}, 描述符: {fd}")
        return fd
    
    def close_file(self, fd: int) -> bool:
        """关闭文件

        释放与文件描述符关联的资源。
        """
        # TODO: 实现文件关闭
        # 1. 检查文件描述符是否有效
        # 2. 关闭文件
        # 3. 释放资源
        if fd in self.open_files:
            del self.open_files[fd]
            self.logger.log_file_event(f"关闭文件: 描述符 {fd}")
            return True
        return False
    
    def read_file_descriptor(self, fd: int, size: int) -> str:
        """通过文件描述符读取文件

        返回读取到的数据字符串。
        """
        # TODO: 实现文件描述符读取
        # 1. 检查文件描述符是否有效
        # 2. 读取指定大小的数据
        if fd in self.open_files:
            self.logger.log_file_event(f"通过描述符读取: {fd}, 大小: {size}")
            return ""
        return ""
    
    def write_file_descriptor(self, fd: int, data: str) -> int:
        """通过文件描述符写入文件

        返回写入的字节数，便于调用者确认写入是否成功。
        """
        # TODO: 实现文件描述符写入
        # 1. 检查文件描述符是否有效
        # 2. 写入数据
        # 3. 返回写入的字节数
        if fd in self.open_files:
            self.logger.log_file_event(f"通过描述符写入: {fd}, 数据长度: {len(data)}")
            return len(data)
        return 0
    
    def _parse_path(self, path: str) -> Tuple[str, str]:
        """解析路径，返回目录路径和文件名

        支持处理绝对路径和相对路径，便于在其他方法中重用。
        """
        # TODO: 实现路径解析
        # 1. 处理绝对路径和相对路径
        # 2. 分离目录路径和文件名
        if path.endswith("/"):
            return path, ""
        else:
            parts = path.rsplit("/", 1)
            if len(parts) == 1:
                return ".", parts[0]
            else:
                return parts[0] or "/", parts[1]
    
    def get_file_system_stats(self) -> Dict[str, int]:
        """获取文件系统统计信息"""
        return {
            'total_files': self.total_files,
            'total_directories': self.total_directories,
            'total_size': self.total_size,
            'open_files': len(self.open_files)
        }
    
    def print_file_system_info(self):
        """打印文件系统信息"""
        stats = self.get_file_system_stats()
        print(f"\n文件系统信息:")
        print(f"总文件数: {stats['total_files']}")
        print(f"总目录数: {stats['total_directories']}")
        print(f"总大小: {stats['total_size']} bytes")
        print(f"打开文件数: {stats['open_files']}")
        print(f"当前目录: {self.get_current_directory()}")
    
    def cleanup(self):
        """清理文件系统"""
        # 关闭所有打开的文件
        for fd in list(self.open_files.keys()):
            self.close_file(fd)
        self.logger.info("文件系统清理完成")

class File:
    """文件类"""
    
    def __init__(self, name: str, path: str, file_type: FileType = FileType.REGULAR):
        self.name = name
        self.path = path
        self.type = file_type
        self.size = 0
        self.content = ""
        self.created_time = time.time()
        self.modified_time = time.time()
        self.accessed_time = time.time()
        self.permissions = 0o644  # 默认权限 