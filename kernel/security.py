"""
安全与保护模块 - ACL、权限管理

本模块实现：
1. 访问控制列表 (ACL)
2. 用户/组权限管理
3. 能力列表 (Capability)
"""

import time
from typing import Optional, Dict, List, Set
from enum import Enum, auto
from collections import defaultdict
from utils.logger import Logger


class Permission(Enum):
    """权限枚举"""
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    DELETE = auto()
    ADMIN = auto()


class User:
    """用户类"""

    _next_uid = 1

    def __init__(self, name: str, is_admin: bool = False):
        self.uid = User._next_uid
        User._next_uid += 1
        self.name = name
        self.is_admin = is_admin
        self.groups: Set[int] = set()
        self.created_time = time.time()

    def add_group(self, gid: int) -> None:
        """添加到组"""
        self.groups.add(gid)

    def remove_group(self, gid: int) -> None:
        """从组移除"""
        self.groups.discard(gid)


class Group:
    """组类"""

    _next_gid = 1

    def __init__(self, name: str):
        self.gid = Group._next_gid
        Group._next_gid += 1
        self.name = name
        self.members: Set[int] = set()
        self.created_time = time.time()

    def add_member(self, uid: int) -> None:
        """添加成员"""
        self.members.add(uid)

    def remove_member(self, uid: int) -> None:
        """移除成员"""
        self.members.discard(uid)


class ACLEntry:
    """ACL条目"""

    def __init__(self, principal_id: int, is_user: bool,
                 permissions: Set[Permission]):
        """
        初始化ACL条目

        Args:
            principal_id: 用户或组ID
            is_user: True表示用户，False表示组
            permissions: 权限集合
        """
        self.principal_id = principal_id
        self.is_user = is_user
        self.permissions = permissions

    def has_permission(self, perm: Permission) -> bool:
        """检查是否有权限"""
        return perm in self.permissions

    def add_permission(self, perm: Permission) -> None:
        """添加权限"""
        self.permissions.add(perm)

    def remove_permission(self, perm: Permission) -> None:
        """移除权限"""
        self.permissions.discard(perm)


class ACL:
    """
    访问控制列表

    管理资源的访问权限。
    """

    def __init__(self, resource_id: str):
        """
        初始化ACL

        Args:
            resource_id: 资源ID
        """
        self.resource_id = resource_id
        self._entries: List[ACLEntry] = []
        self._owner_uid: Optional[int] = None
        self._owner_permissions: Set[Permission] = set()
        self._group_permissions: Set[Permission] = set()
        self._other_permissions: Set[Permission] = set()
        self._logger = Logger()

    def set_owner(self, uid: int, permissions: Set[Permission] = None) -> None:
        """设置所有者"""
        self._owner_uid = uid
        if permissions:
            self._owner_permissions = permissions

    def set_group_permissions(self, permissions: Set[Permission]) -> None:
        """设置组权限"""
        self._group_permissions = permissions

    def set_other_permissions(self, permissions: Set[Permission]) -> None:
        """设置其他用户权限"""
        self._other_permissions = permissions

    def add_entry(self, principal_id: int, is_user: bool,
                  permissions: Set[Permission]) -> None:
        """添加ACL条目"""
        entry = ACLEntry(principal_id, is_user, permissions)
        self._entries.append(entry)

    def remove_entry(self, principal_id: int, is_user: bool) -> bool:
        """移除ACL条目"""
        for i, entry in enumerate(self._entries):
            if entry.principal_id == principal_id and entry.is_user == is_user:
                self._entries.pop(i)
                return True
        return False

    def check_permission(self, uid: int, gid: int, perm: Permission) -> bool:
        """
        检查权限

        Args:
            uid: 用户ID
            gid: 组ID
            perm: 要检查的权限

        Returns:
            bool: 是否有权限
        """
        # 检查所有者权限
        if uid == self._owner_uid:
            if perm in self._owner_permissions:
                return True

        # 检查ACL条目
        for entry in self._entries:
            if entry.is_user and entry.principal_id == uid:
                if entry.has_permission(perm):
                    return True
            elif not entry.is_user and entry.principal_id == gid:
                if entry.has_permission(perm):
                    return True

        # 检查组权限
        if perm in self._group_permissions:
            return True

        # 检查其他用户权限
        if perm in self._other_permissions:
            return True

        return False

    def get_mode_string(self) -> str:
        """获取类似Unix的权限字符串"""
        def perm_set_to_str(perms):
            s = 'r' if Permission.READ in perms else '-'
            s += 'w' if Permission.WRITE in perms else '-'
            s += 'x' if Permission.EXECUTE in perms else '-'
            return s

        return (perm_set_to_str(self._owner_permissions) +
                perm_set_to_str(self._group_permissions) +
                perm_set_to_str(self._other_permissions))

    def get_entries(self) -> List[dict]:
        """获取所有条目"""
        result = []
        for entry in self._entries:
            result.append({
                'principal_id': entry.principal_id,
                'is_user': entry.is_user,
                'permissions': [p.name for p in entry.permissions]
            })
        return result


class Capability:
    """
    能力

    表示主体对客体的访问权限。
    """

    def __init__(self, resource_id: str, permissions: Set[Permission]):
        """
        初始化能力

        Args:
            resource_id: 资源ID
            permissions: 权限集合
        """
        self.resource_id = resource_id
        self.permissions = permissions
        self.created_time = time.time()

    def has_permission(self, perm: Permission) -> bool:
        """检查权限"""
        return perm in self.permissions


class CapabilityList:
    """
    能力列表

    每个用户拥有的能力列表。
    """

    def __init__(self, uid: int):
        """
        初始化能力列表

        Args:
            uid: 用户ID
        """
        self.uid = uid
        self._capabilities: Dict[str, Capability] = {}

    def grant(self, resource_id: str, permissions: Set[Permission]) -> None:
        """授予权限"""
        self._capabilities[resource_id] = Capability(resource_id, permissions)

    def revoke(self, resource_id: str) -> bool:
        """撤销权限"""
        if resource_id in self._capabilities:
            del self._capabilities[resource_id]
            return True
        return False

    def check(self, resource_id: str, perm: Permission) -> bool:
        """检查权限"""
        cap = self._capabilities.get(resource_id)
        if cap:
            return cap.has_permission(perm)
        return False

    def get_capabilities(self) -> List[dict]:
        """获取所有能力"""
        return [
            {'resource': res, 'permissions': [p.name for p in cap.permissions]}
            for res, cap in self._capabilities.items()
        ]


class SecurityManager:
    """
    安全管理器

    管理用户、组、ACL和能力。
    """

    def __init__(self):
        """初始化安全管理器"""
        self._users: Dict[int, User] = {}
        self._groups: Dict[int, Group] = {}
        self._acls: Dict[str, ACL] = {}
        self._capability_lists: Dict[int, CapabilityList] = {}
        self._logger = Logger()

        # 创建默认用户和组
        self._create_defaults()

    def _create_defaults(self) -> None:
        """创建默认用户和组"""
        # root用户
        root = User("root", is_admin=True)
        self._users[root.uid] = root

        # 用户组
        users_group = Group("users")
        self._groups[users_group.gid] = users_group

        self._logger.info(f"创建默认用户: root (UID: {root.uid})")
        self._logger.info(f"创建默认组: users (GID: {users_group.gid})")

    def create_user(self, name: str, is_admin: bool = False) -> User:
        """创建用户"""
        user = User(name, is_admin)
        self._users[user.uid] = user
        self._capability_lists[user.uid] = CapabilityList(user.uid)
        self._logger.info(f"创建用户: {name} (UID: {user.uid})")
        return user

    def create_group(self, name: str) -> Group:
        """创建组"""
        group = Group(name)
        self._groups[group.gid] = group
        self._logger.info(f"创建组: {name} (GID: {group.gid})")
        return group

    def add_user_to_group(self, uid: int, gid: int) -> bool:
        """将用户添加到组"""
        user = self._users.get(uid)
        group = self._groups.get(gid)
        if user and group:
            user.add_group(gid)
            group.add_member(uid)
            return True
        return False

    def create_resource_acl(self, resource_id: str, owner_uid: int,
                           mode: str = "rw-r--r--") -> ACL:
        """
        创建资源ACL

        Args:
            resource_id: 资源ID
            owner_uid: 所有者UID
            mode: 权限模式字符串

        Returns:
            ACL: 创建的ACL
        """
        acl = ACL(resource_id)
        acl.set_owner(owner_uid, self._parse_mode(mode[:3]))
        acl.set_group_permissions(self._parse_mode(mode[3:6]))
        acl.set_other_permissions(self._parse_mode(mode[6:9]))
        self._acls[resource_id] = acl
        return acl

    def _parse_mode(self, mode_str: str) -> Set[Permission]:
        """解析权限字符串"""
        perms = set()
        if len(mode_str) >= 1 and mode_str[0] == 'r':
            perms.add(Permission.READ)
        if len(mode_str) >= 2 and mode_str[1] == 'w':
            perms.add(Permission.WRITE)
        if len(mode_str) >= 3 and mode_str[2] == 'x':
            perms.add(Permission.EXECUTE)
        return perms

    def check_access(self, uid: int, resource_id: str,
                    perm: Permission) -> bool:
        """
        检查访问权限

        Args:
            uid: 用户ID
            resource_id: 资源ID
            perm: 权限

        Returns:
            bool: 是否有权限
        """
        user = self._users.get(uid)
        if user and user.is_admin:
            return True

        acl = self._acls.get(resource_id)
        if not acl:
            return False

        user = self._users.get(uid)
        gid = next(iter(user.groups)) if user and user.groups else 0

        return acl.check_permission(uid, gid, perm)

    def grant_capability(self, uid: int, resource_id: str,
                        permissions: Set[Permission]) -> bool:
        """授予能力"""
        cap_list = self._capability_lists.get(uid)
        if cap_list:
            cap_list.grant(resource_id, permissions)
            return True
        return False

    def check_capability(self, uid: int, resource_id: str,
                        perm: Permission) -> bool:
        """检查能力"""
        cap_list = self._capability_lists.get(uid)
        if cap_list:
            return cap_list.check(resource_id, perm)
        return False

    def get_user(self, uid: int) -> Optional[User]:
        """获取用户"""
        return self._users.get(uid)

    def get_group(self, gid: int) -> Optional[Group]:
        """获取组"""
        return self._groups.get(gid)

    def list_users(self) -> List[dict]:
        """列出所有用户"""
        return [{'uid': u.uid, 'name': u.name, 'is_admin': u.is_admin}
                for u in self._users.values()]

    def list_groups(self) -> List[dict]:
        """列出所有组"""
        return [{'gid': g.gid, 'name': g.name, 'members': list(g.members)}
                for g in self._groups.values()]


# 使用示例
if __name__ == "__main__":
    print("=== 安全与保护演示 ===\n")

    sm = SecurityManager()

    # 1. 创建用户和组
    print("1. 创建用户和组")
    alice = sm.create_user("alice")
    bob = sm.create_user("bob")
    developers = sm.create_group("developers")
    sm.add_user_to_group(alice.uid, developers.gid)
    sm.add_user_to_group(bob.uid, developers.gid)

    print(f"  用户: {sm.list_users()}")
    print(f"  组: {sm.list_groups()}")

    # 2. 创建资源ACL
    print("\n2. 创建资源ACL")
    sm.create_resource_acl("/project/code", alice.uid, "rwxr-x---")
    sm.create_resource_acl("/project/docs", alice.uid, "rw-rw-r--")

    # 3. 检查ACL权限
    print("\n3. 检查ACL权限")
    print(f"  Alice读取code: {sm.check_access(alice.uid, '/project/code', Permission.READ)}")
    print(f"  Bob读取code: {sm.check_access(bob.uid, '/project/code', Permission.READ)}")
    print(f"  Bob写入code: {sm.check_access(bob.uid, '/project/code', Permission.WRITE)}")
    print(f"  Bob读取docs: {sm.check_access(bob.uid, '/project/docs', Permission.READ)}")

    # 4. 能力列表
    print("\n4. 能力列表")
    sm.grant_capability(bob.uid, "/project/admin", {Permission.READ, Permission.WRITE, Permission.ADMIN})
    print(f"  Bob对admin的READ权限: {sm.check_capability(bob.uid, '/project/admin', Permission.READ)}")
    print(f"  Alice对admin的READ权限: {sm.check_capability(alice.uid, '/project/admin', Permission.READ)}")

    cap_list = sm._capability_lists.get(bob.uid)
    print(f"  Bob的能力: {cap_list.get_capabilities()}")

    print("\n演示完成！")
