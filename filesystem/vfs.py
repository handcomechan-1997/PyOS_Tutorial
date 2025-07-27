"""
虚拟文件系统 (VFS) - 提供一个简单的内存文件系统
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from utils.logger import Logger

class VFSNodeType(Enum):
    """文件系统节点类型"""
    FILE = "file"
    DIRECTORY = "directory"

class VFSNode:
    """文件系统节点"""
    
    def __init__(self, name: str, node_type: VFSNodeType, content: str = "", 
                 parent: Optional['VFSNode'] = None, size: int = 0, 
                 permissions: int = 0o644, created_time: float = 0.0,
                 modified_time: float = 0.0, accessed_time: float = 0.0):
        self.name = name
        self.node_type = node_type
        self.content = content
        self.parent = parent
        self.children: Dict[str, 'VFSNode'] = {}
        self.size = size
        self.permissions = permissions
        self.created_time = created_time
        self.modified_time = modified_time
        self.accessed_time = accessed_time
        
        # 设置默认时间
        if self.created_time == 0.0:
            self.created_time = time.time()
        if self.modified_time == 0.0:
            self.modified_time = time.time()
        if self.accessed_time == 0.0:
            self.accessed_time = time.time()
        if self.node_type == VFSNodeType.FILE:
            self.size = len(self.content)

class VirtualFileSystem:
    """虚拟文件系统"""
    
    def __init__(self):
        """初始化虚拟文件系统"""
        self.logger = Logger()
        self.lock = threading.Lock()
        self._init_mode = True  # 初始化模式，减少日志记录
        
        # 创建根目录
        self.root = VFSNode(
            name="/",
            node_type=VFSNodeType.DIRECTORY,
            permissions=0o755
        )
        
        # 创建一些基本目录
        self._create_basic_structure()
        
        self._init_mode = False  # 初始化完成，恢复正常日志记录
        self.logger.info("虚拟文件系统初始化完成")
    
    def _create_basic_structure(self):
        """创建基本的目录结构"""
        self.logger.info("创建虚拟文件系统基础结构...")
        
        basic_dirs = [
            "/home",
            "/home/user",
            "/bin",
            "/usr",
            "/usr/bin",
            "/tmp",
            "/etc",
            "/var",
            "/dev"
        ]
        
        # 批量创建目录
        for dir_path in basic_dirs:
            self._create_directory_silent(dir_path)
        
        # 批量创建示例文件
        files_to_create = [
            ("/etc/os_version", "PyOS 1.0.0"),
            ("/home/user/welcome.txt", "欢迎使用PyOS虚拟文件系统！"),
            ("/home/user/readme.md", "# PyOS 说明文档\n\n这是一个Python实现的简单操作系统。")
        ]
        
        for file_path, content in files_to_create:
            self._create_file_silent(file_path, content)
        
        self.logger.info(f"已创建 {len(basic_dirs)} 个目录和 {len(files_to_create)} 个文件")
    
    def _normalize_path(self, path: str) -> str:
        """规范化路径"""
        if not path.startswith("/"):
            return f"/{path}"
        
        # 处理 . 和 ..
        parts = []
        for part in path.split("/"):
            if part == "" or part == ".":
                continue
            elif part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        
        return "/" + "/".join(parts) if parts else "/"
    
    def _find_node(self, path: str) -> Optional[VFSNode]:
        """查找节点"""
        path = self._normalize_path(path)
        
        if path == "/":
            return self.root
        
        parts = path.strip("/").split("/")
        current = self.root
        
        for part in parts:
            if part not in current.children:
                return None
            current = current.children[part]
        
        return current
    
    def _find_parent_node(self, path: str) -> Tuple[Optional[VFSNode], str]:
        """查找父节点和文件名"""
        path = self._normalize_path(path)
        
        if path == "/":
            return None, "/"
        
        parts = path.strip("/").split("/")
        filename = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        
        parent = self._find_node(parent_path)
        return parent, filename
    
    def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        with self.lock:
            return self._find_node(path) is not None
    
    def is_file(self, path: str) -> bool:
        """检查是否为文件"""
        with self.lock:
            node = self._find_node(path)
            return node is not None and node.node_type == VFSNodeType.FILE
    
    def is_directory(self, path: str) -> bool:
        """检查是否为目录"""
        with self.lock:
            node = self._find_node(path)
            return node is not None and node.node_type == VFSNodeType.DIRECTORY
    
    def create_file(self, path: str, content: str = "") -> bool:
        """创建文件"""
        with self.lock:
            try:
                parent, filename = self._find_parent_node(path)
                
                if parent is None:
                    self.logger.error(f"父目录不存在: {path}")
                    return False
                
                if parent.node_type != VFSNodeType.DIRECTORY:
                    self.logger.error(f"父路径不是目录: {path}")
                    return False
                
                if filename in parent.children:
                    self.logger.warning(f"文件已存在: {path}")
                    return False
                
                # 创建文件节点
                file_node = VFSNode(
                    name=filename,
                    node_type=VFSNodeType.FILE,
                    content=content,
                    parent=parent,
                    size=len(content)
                )
                
                parent.children[filename] = file_node
                parent.modified_time = time.time()
                
                # 只在非初始化模式下记录详细日志
                if not self._init_mode:
                    self.logger.log_file_event(f"创建文件: {path}")
                return True
                
            except Exception as e:
                self.logger.error(f"创建文件失败 {path}: {e}")
                return False
    
    def _create_file_silent(self, path: str, content: str = "") -> bool:
        """静默创建文件（不记录日志）"""
        try:
            parent, filename = self._find_parent_node(path)
            
            if parent is None or parent.node_type != VFSNodeType.DIRECTORY:
                return False
            
            if filename in parent.children:
                return False
            
            # 创建文件节点
            file_node = VFSNode(
                name=filename,
                node_type=VFSNodeType.FILE,
                content=content,
                parent=parent,
                size=len(content)
            )
            
            parent.children[filename] = file_node
            parent.modified_time = time.time()
            return True
            
        except Exception:
            return False
    
    def create_directory(self, path: str) -> bool:
        """创建目录"""
        with self.lock:
            try:
                # 如果目录已存在，返回True
                if self.exists(path):
                    return True
                
                parent, dirname = self._find_parent_node(path)
                
                if parent is None:
                    self.logger.error(f"父目录不存在: {path}")
                    return False
                
                if parent.node_type != VFSNodeType.DIRECTORY:
                    self.logger.error(f"父路径不是目录: {path}")
                    return False
                
                # 创建目录节点
                dir_node = VFSNode(
                    name=dirname,
                    node_type=VFSNodeType.DIRECTORY,
                    parent=parent,
                    permissions=0o755
                )
                
                parent.children[dirname] = dir_node
                parent.modified_time = time.time()
                
                # 只在非初始化模式下记录详细日志
                if not self._init_mode:
                    self.logger.log_file_event(f"创建目录: {path}")
                return True
                
            except Exception as e:
                self.logger.error(f"创建目录失败 {path}: {e}")
                return False
    
    def _create_directory_silent(self, path: str) -> bool:
        """静默创建目录（不记录日志）"""
        try:
            # 如果目录已存在，返回True
            if self.exists(path):
                return True
            
            parent, dirname = self._find_parent_node(path)
            
            if parent is None or parent.node_type != VFSNodeType.DIRECTORY:
                return False
            
            # 创建目录节点
            dir_node = VFSNode(
                name=dirname,
                node_type=VFSNodeType.DIRECTORY,
                parent=parent,
                permissions=0o755
            )
            
            parent.children[dirname] = dir_node
            parent.modified_time = time.time()
            return True
            
        except Exception:
            return False
    
    def read_file(self, path: str) -> Optional[str]:
        """读取文件内容"""
        with self.lock:
            try:
                node = self._find_node(path)
                
                if node is None:
                    self.logger.error(f"文件不存在: {path}")
                    return None
                
                if node.node_type != VFSNodeType.FILE:
                    self.logger.error(f"不是文件: {path}")
                    return None
                
                node.accessed_time = time.time()
                self.logger.log_file_event(f"读取文件: {path}")
                return node.content
                
            except Exception as e:
                self.logger.error(f"读取文件失败 {path}: {e}")
                return None
    
    def write_file(self, path: str, content: str) -> bool:
        """写入文件内容"""
        with self.lock:
            try:
                node = self._find_node(path)
                
                if node is None:
                    # 文件不存在，创建新文件
                    return self.create_file(path, content)
                
                if node.node_type != VFSNodeType.FILE:
                    self.logger.error(f"不是文件: {path}")
                    return False
                
                node.content = content
                node.size = len(content)
                node.modified_time = time.time()
                node.accessed_time = time.time()
                
                self.logger.log_file_event(f"写入文件: {path}")
                return True
                
            except Exception as e:
                self.logger.error(f"写入文件失败 {path}: {e}")
                return False
    
    def delete_file(self, path: str) -> bool:
        """删除文件"""
        with self.lock:
            try:
                node = self._find_node(path)
                
                if node is None:
                    self.logger.error(f"文件不存在: {path}")
                    return False
                
                if node.node_type != VFSNodeType.FILE:
                    self.logger.error(f"不是文件: {path}")
                    return False
                
                parent = node.parent
                if parent:
                    del parent.children[node.name]
                    parent.modified_time = time.time()
                
                self.logger.log_file_event(f"删除文件: {path}")
                return True
                
            except Exception as e:
                self.logger.error(f"删除文件失败 {path}: {e}")
                return False
    
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """删除目录"""
        with self.lock:
            try:
                node = self._find_node(path)
                
                if node is None:
                    self.logger.error(f"目录不存在: {path}")
                    return False
                
                if node.node_type != VFSNodeType.DIRECTORY:
                    self.logger.error(f"不是目录: {path}")
                    return False
                
                if node == self.root:
                    self.logger.error("不能删除根目录")
                    return False
                
                if node.children and not recursive:
                    self.logger.error(f"目录不为空: {path}")
                    return False
                
                parent = node.parent
                if parent:
                    del parent.children[node.name]
                    parent.modified_time = time.time()
                
                self.logger.log_file_event(f"删除目录: {path}")
                return True
                
            except Exception as e:
                self.logger.error(f"删除目录失败 {path}: {e}")
                return False
    
    def list_directory(self, path: str = "/", silent: bool = True) -> List[Dict[str, Any]]:
        """列出目录内容"""
        with self.lock:
            try:
                node = self._find_node(path)
                
                if node is None:
                    if not silent:
                        self.logger.error(f"目录不存在: {path}")
                    return []
                
                if node.node_type != VFSNodeType.DIRECTORY:
                    if not silent:
                        self.logger.error(f"不是目录: {path}")
                    return []
                
                node.accessed_time = time.time()
                
                entries = []
                for child_name, child_node in node.children.items():
                    entries.append({
                        'name': child_name,
                        'type': child_node.node_type.value,
                        'size': child_node.size,
                        'permissions': oct(child_node.permissions),
                        'created_time': child_node.created_time,
                        'modified_time': child_node.modified_time,
                        'accessed_time': child_node.accessed_time
                    })
                
                # 按名称排序
                entries.sort(key=lambda x: x['name'])
                
                if not silent:
                    self.logger.log_file_event(f"列出目录: {path}")
                return entries
                
            except Exception as e:
                if not silent:
                    self.logger.error(f"列出目录失败 {path}: {e}")
                return []
    
    def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """获取文件/目录信息"""
        with self.lock:
            try:
                node = self._find_node(path)
                
                if node is None:
                    return None
                
                return {
                    'name': node.name,
                    'type': node.node_type.value,
                    'size': node.size,
                    'permissions': oct(node.permissions),
                    'created_time': node.created_time,
                    'modified_time': node.modified_time,
                    'accessed_time': node.accessed_time,
                    'is_directory': node.node_type == VFSNodeType.DIRECTORY,
                    'is_file': node.node_type == VFSNodeType.FILE
                }
                
            except Exception as e:
                self.logger.error(f"获取文件信息失败 {path}: {e}")
                return None
    
    def get_absolute_path(self, current_dir: str, relative_path: str) -> str:
        """获取绝对路径"""
        if relative_path.startswith("/"):
            return self._normalize_path(relative_path)
        
        if current_dir == "/":
            full_path = f"/{relative_path}"
        else:
            full_path = f"{current_dir}/{relative_path}"
        
        return self._normalize_path(full_path)
    
    def get_stats(self) -> Dict[str, int]:
        """获取文件系统统计信息"""
        with self.lock:
            def count_nodes(node: VFSNode) -> Tuple[int, int, int]:
                """递归统计节点数量"""
                files = 1 if node.node_type == VFSNodeType.FILE else 0
                dirs = 1 if node.node_type == VFSNodeType.DIRECTORY else 0
                total_size = node.size
                
                for child in node.children.values():
                    child_files, child_dirs, child_size = count_nodes(child)
                    files += child_files
                    dirs += child_dirs
                    total_size += child_size
                
                return files, dirs, total_size
            
            total_files, total_dirs, total_size = count_nodes(self.root)
            
            return {
                'total_files': total_files,
                'total_directories': total_dirs - 1,  # 不计算根目录
                'total_size': total_size
            }
    
    def print_tree(self, path: str = "/", prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        """打印目录树"""
        if current_depth >= max_depth:
            return
        
        node = self._find_node(path)
        if not node or node.node_type != VFSNodeType.DIRECTORY:
            return
        
        print(f"{prefix}{node.name}/")
        
        children = list(node.children.items())
        children.sort(key=lambda x: (x[1].node_type.value, x[0]))
        
        for i, (name, child) in enumerate(children):
            is_last = i == len(children) - 1
            child_prefix = prefix + ("└── " if is_last else "├── ")
            next_prefix = prefix + ("    " if is_last else "│   ")
            
            if child.node_type == VFSNodeType.DIRECTORY:
                print(f"{child_prefix}{name}/")
                if current_depth < max_depth - 1:
                    child_path = self.get_absolute_path(path, name)
                    self.print_tree(child_path, next_prefix, max_depth, current_depth + 1)
            else:
                print(f"{child_prefix}{name} ({child.size} bytes)") 