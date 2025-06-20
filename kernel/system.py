"""
系统核心类 - 操作系统的主要控制中心
"""

import time
import threading
from typing import Dict, Any

from .scheduler import Scheduler
from .memory_manager import MemoryManager
from .interrupt import InterruptHandler
from .system_call import SystemCall
from process.process_manager import ProcessManager
from filesystem.file_system import FileSystem
from device.device_manager import DeviceManager
from utils.logger import Logger

class System:
    """操作系统核心类"""
    
    def __init__(self):
        """初始化系统"""
        self.logger = Logger()
        self.running = False
        self.start_time = None
        
        # 初始化系统组件
        self.scheduler = Scheduler()
        self.memory_manager = MemoryManager()
        self.interrupt_handler = InterruptHandler()
        self.system_call = SystemCall()
        self.process_manager = ProcessManager()
        self.file_system = FileSystem()
        self.device_manager = DeviceManager()
        
        # 系统状态
        self.system_info = {
            'version': '1.0.0',
            'uptime': 0,
            'process_count': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        
        self.logger.info("系统核心初始化完成")
    
    def boot(self):
        """系统启动"""
        self.logger.info("系统启动中...")
        self.start_time = time.time()
        self.running = True
        
        # 初始化各个子系统
        self._init_subsystems()
        
        # 启动系统监控线程
        self._start_monitor()
        
        self.logger.info("系统启动完成")
        print("系统启动成功！")
    
    def shutdown(self):
        """系统关闭"""
        self.logger.info("系统关闭中...")
        self.running = False
        
        # 保存系统状态
        self._save_system_state()
        
        # 清理资源
        self._cleanup()
        
        self.logger.info("系统关闭完成")
    
    def _init_subsystems(self):
        """初始化子系统"""
        try:
            # 初始化内存管理
            self.memory_manager.initialize()
            
            # 初始化文件系统
            self.file_system.initialize()
            
            # 初始化设备管理
            self.device_manager.initialize()
            
            # 初始化进程管理
            self.process_manager.initialize(self.scheduler, self.memory_manager)
            
            # 启动调度器
            self.scheduler.start()
            
            self.logger.info("所有子系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"子系统初始化失败: {e}")
            raise
    
    def _start_monitor(self):
        """启动系统监控"""
        def monitor():
            while self.running:
                try:
                    # 更新系统信息
                    self._update_system_info()
                    time.sleep(1)  # 每秒更新一次
                except Exception as e:
                    self.logger.error(f"系统监控错误: {e}")
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.logger.info("系统监控启动")
    
    def _update_system_info(self):
        """更新系统信息"""
        if self.start_time:
            self.system_info['uptime'] = time.time() - self.start_time
        
        self.system_info['process_count'] = self.process_manager.get_process_count()
        self.system_info['memory_usage'] = self.memory_manager.get_memory_usage()
        self.system_info['cpu_usage'] = self.scheduler.get_cpu_usage()
    
    def _save_system_state(self):
        """保存系统状态"""
        # 这里可以保存系统状态到文件
        pass
    
    def _cleanup(self):
        """清理系统资源"""
        # 停止调度器
        self.scheduler.stop()
        
        # 清理进程
        self.process_manager.cleanup()
        
        # 清理内存
        self.memory_manager.cleanup()
        
        # 清理文件系统
        self.file_system.cleanup()
        
        # 清理设备
        self.device_manager.cleanup()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return self.system_info.copy()
    
    def is_running(self) -> bool:
        """检查系统是否运行"""
        return self.running 