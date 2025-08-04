#!/usr/bin/env python3
"""
PyOS Tutorial 安装脚本

这个脚本可以帮助用户快速安装PyOS Tutorial包到开发环境中。
"""

import os
import sys
import subprocess
from pathlib import Path

def install_package():
    """安装PyOS Tutorial包"""
    print("正在安装 PyOS Tutorial...")
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.absolute()
    
    try:
        # 使用pip安装当前目录作为可编辑包
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-e", str(current_dir)
        ])
        print("✅ PyOS Tutorial 安装成功！")
        print("\n现在你可以这样使用:")
        print("  from pyos_tutorial import VirtualMemory, PageReplacementAlgorithm")
        print("  vm = VirtualMemory(replacement_algorithm=PageReplacementAlgorithm.LRU)")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False
    
    return True

def test_import():
    """测试导入是否成功"""
    print("\n测试导入...")
    try:
        from pyos_tutorial import VirtualMemory, PageReplacementAlgorithm
        print("✅ 导入测试成功！")
        return True
    except ImportError as e:
        print(f"❌ 导入测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("PyOS Tutorial 安装程序")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return
    
    print(f"Python版本: {sys.version}")
    
    # 安装包
    if install_package():
        # 测试导入
        test_import()
        
        print("\n" + "=" * 50)
        print("安装完成！")
        print("=" * 50)
        print("\n使用示例:")
        print("  python -c \"from pyos_tutorial import VirtualMemory; print('成功!')\"")
        print("  python main.py")
    else:
        print("\n安装失败，请检查错误信息。")

if __name__ == "__main__":
    main() 