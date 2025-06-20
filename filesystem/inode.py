"""
索引节点模块 - 管理文件的元数据
"""

import time
from typing import Dict, List, Optional
from enum import Enum

from utils.logger import Logger

class FileType(Enum):
    """文件类型枚举"""
    REGULAR = "regular"
    DIRECTORY = "directory"
    SYMBOLIC_LINK = "symlink"
    FIFO = "fifo"
    SOCKET = "socket"

class Inode:
    """索引节点"""
    
    def __init__(self, inode_number: int, file_type: FileType = FileType.REGULAR):
        """初始化索引节点"""
        self.inode_number = inode_number
        self.file_type = file_type
        
        # 文件属性
        self.size = 0
        self.blocks = 0
        self.permissions = 0o644  # 默认权限
        
        # 时间戳
        self.created_time = time.time()
        self.modified_time = time.time()
        self.accessed_time = time.time()
        
        # 所有者信息
        self.owner_id = 0
        self.group_id = 0
        
        # 直接块指针 (前12个直接块)
        self.direct_blocks: List[int] = [-1] * 12
        
        # 间接块指针
        self.single_indirect = -1
        self.double_indirect = -1
        self.triple_indirect = -1
        
        # 链接计数
        self.link_count = 1
        
        # 文件系统特定信息
        self.fs_specific = {}
        
        self.logger = Logger()
    
    def get_size(self) -> int:
        """获取文件大小"""
        return self.size
    
    def set_size(self, size: int):
        """设置文件大小"""
        self.size = size
        self.modified_time = time.time()
        self.logger.log_file_event(f"更新inode {self.inode_number} 大小: {size}")
    
    def get_blocks(self) -> int:
        """获取块数"""
        return self.blocks
    
    def set_blocks(self, blocks: int):
        """设置块数"""
        self.blocks = blocks
        self.modified_time = time.time()
    
    def add_direct_block(self, block_number: int) -> bool:
        """添加直接块"""
        for i, block in enumerate(self.direct_blocks):
            if block == -1:
                self.direct_blocks[i] = block_number
                self.blocks += 1
                self.modified_time = time.time()
                return True
        return False
    
    def remove_direct_block(self, block_number: int) -> bool:
        """移除直接块"""
        for i, block in enumerate(self.direct_blocks):
            if block == block_number:
                self.direct_blocks[i] = -1
                self.blocks -= 1
                self.modified_time = time.time()
                return True
        return False
    
    def get_direct_blocks(self) -> List[int]:
        """获取所有直接块"""
        return [block for block in self.direct_blocks if block != -1]
    
    def set_permissions(self, permissions: int):
        """设置权限"""
        self.permissions = permissions
        self.modified_time = time.time()
    
    def get_permissions(self) -> int:
        """获取权限"""
        return self.permissions
    
    def update_access_time(self):
        """更新访问时间"""
        self.accessed_time = time.time()
    
    def update_modification_time(self):
        """更新修改时间"""
        self.modified_time = time.time()
    
    def increment_link_count(self):
        """增加链接计数"""
        self.link_count += 1
        self.modified_time = time.time()
    
    def decrement_link_count(self) -> int:
        """减少链接计数"""
        if self.link_count > 0:
            self.link_count -= 1
            self.modified_time = time.time()
        return self.link_count
    
    def get_link_count(self) -> int:
        """获取链接计数"""
        return self.link_count
    
    def is_free(self) -> bool:
        """检查inode是否空闲"""
        return self.link_count == 0
    
    def get_info(self) -> Dict:
        """获取inode信息"""
        return {
            'inode_number': self.inode_number,
            'file_type': self.file_type.value,
            'size': self.size,
            'blocks': self.blocks,
            'permissions': oct(self.permissions),
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'accessed_time': self.accessed_time,
            'owner_id': self.owner_id,
            'group_id': self.group_id,
            'link_count': self.link_count,
            'direct_blocks': self.get_direct_blocks(),
            'single_indirect': self.single_indirect,
            'double_indirect': self.double_indirect,
            'triple_indirect': self.triple_indirect
        }
    
    def print_info(self):
        """打印inode信息"""
        info = self.get_info()
        print(f"\nInode {self.inode_number} 信息:")
        print("-" * 40)
        print(f"文件类型: {info['file_type']}")
        print(f"大小: {info['size']} bytes")
        print(f"块数: {info['blocks']}")
        print(f"权限: {info['permissions']}")
        print(f"所有者: {info['owner_id']}")
        print(f"组: {info['group_id']}")
        print(f"链接数: {info['link_count']}")
        print(f"创建时间: {time.ctime(info['created_time'])}")
        print(f"修改时间: {time.ctime(info['modified_time'])}")
        print(f"访问时间: {time.ctime(info['accessed_time'])}")
        print(f"直接块: {info['direct_blocks']}")
        if info['single_indirect'] != -1:
            print(f"一级间接块: {info['single_indirect']}")
        if info['double_indirect'] != -1:
            print(f"二级间接块: {info['double_indirect']}")
        if info['triple_indirect'] != -1:
            print(f"三级间接块: {info['triple_indirect']}")

class InodeTable:
    """索引节点表"""
    
    def __init__(self, max_inodes: int = 1024):
        """初始化索引节点表"""
        self.max_inodes = max_inodes
        self.inodes: Dict[int, Inode] = {}
        self.free_inodes: List[int] = list(range(1, max_inodes + 1))
        self.next_inode_number = 1
        
        self.logger = Logger()
        self.logger.info(f"索引节点表初始化: 最大 {max_inodes} 个inode")
    
    def allocate_inode(self, file_type: FileType = FileType.REGULAR) -> Optional[Inode]:
        """分配新的索引节点"""
        if not self.free_inodes:
            self.logger.warning("没有可用的inode")
            return None
        
        inode_number = self.free_inodes.pop(0)
        inode = Inode(inode_number, file_type)
        self.inodes[inode_number] = inode
        
        self.logger.log_file_event(f"分配inode: {inode_number}, 类型: {file_type.value}")
        return inode
    
    def free_inode(self, inode_number: int) -> bool:
        """释放索引节点"""
        if inode_number not in self.inodes:
            return False
        
        inode = self.inodes[inode_number]
        if inode.link_count > 0:
            self.logger.warning(f"无法释放inode {inode_number}: 链接计数 > 0")
            return False
        
        del self.inodes[inode_number]
        self.free_inodes.append(inode_number)
        self.free_inodes.sort()
        
        self.logger.log_file_event(f"释放inode: {inode_number}")
        return True
    
    def get_inode(self, inode_number: int) -> Optional[Inode]:
        """获取索引节点"""
        return self.inodes.get(inode_number)
    
    def get_free_inode_count(self) -> int:
        """获取空闲inode数量"""
        return len(self.free_inodes)
    
    def get_used_inode_count(self) -> int:
        """获取已使用inode数量"""
        return len(self.inodes)
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'max_inodes': self.max_inodes,
            'used_inodes': self.get_used_inode_count(),
            'free_inodes': self.get_free_inode_count(),
            'utilization': (self.get_used_inode_count() / self.max_inodes) * 100
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        print(f"\n索引节点表统计:")
        print(f"最大inode数: {stats['max_inodes']}")
        print(f"已使用: {stats['used_inodes']}")
        print(f"空闲: {stats['free_inodes']}")
        print(f"利用率: {stats['utilization']:.1f}%") 