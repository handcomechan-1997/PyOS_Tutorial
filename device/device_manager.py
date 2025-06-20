"""
Device Manager Module

This module manages hardware devices in the operating system.
It provides an interface for device registration, discovery, and control.
"""

from typing import Dict, List, Optional, Any
from utils.logger import Logger


class Device:
    """Base class for all devices in the system."""
    
    def __init__(self, device_id: str, device_type: str, name: str):
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.is_active = False
        self.properties: Dict[str, Any] = {}
    
    def initialize(self) -> bool:
        """Initialize the device."""
        self.is_active = True
        return True
    
    def shutdown(self) -> bool:
        """Shutdown the device."""
        self.is_active = False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get device status."""
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'name': self.name,
            'is_active': self.is_active,
            'properties': self.properties
        }


class DeviceManager:
    """
    Manages all hardware devices in the system.
    
    This class provides device registration, discovery, and control functionality.
    It maintains a registry of all devices and provides methods to interact with them.
    """
    
    def __init__(self):
        self.logger = Logger(__name__)
        self.devices: Dict[str, Device] = {}
        self.device_types: Dict[str, List[str]] = {}
        self.logger.info("Device Manager initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the device manager and register default devices.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing Device Manager...")
            
            # Register default devices
            from .terminal import Terminal
            from .keyboard import Keyboard
            from .display import Display
            
            # Create and register terminal device
            terminal = Terminal()
            if not self.register_device(terminal):
                self.logger.error("Failed to register terminal device")
                return False
            
            # Create and register keyboard device
            keyboard = Keyboard()
            if not self.register_device(keyboard):
                self.logger.error("Failed to register keyboard device")
                return False
            
            # Create and register display device
            display = Display()
            if not self.register_device(display):
                self.logger.error("Failed to register display device")
                return False
            
            # Initialize all registered devices
            for device_id in list(self.devices.keys()):
                if not self.initialize_device(device_id):
                    self.logger.warning(f"Failed to initialize device {device_id}")
            
            self.logger.info("Device Manager initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Device Manager: {e}")
            return False
    
    def register_device(self, device: Device) -> bool:
        """
        Register a new device in the system.
        
        Args:
            device: The device to register
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            if device.device_id in self.devices:
                self.logger.warning(f"Device {device.device_id} already registered")
                return False
            
            self.devices[device.device_id] = device
            
            # Add to device type registry
            if device.device_type not in self.device_types:
                self.device_types[device.device_type] = []
            self.device_types[device.device_type].append(device.device_id)
            
            self.logger.info(f"Device {device.device_id} ({device.name}) registered")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register device {device.device_id}: {e}")
            return False
    
    def unregister_device(self, device_id: str) -> bool:
        """
        Unregister a device from the system.
        
        Args:
            device_id: The ID of the device to unregister
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        try:
            if device_id not in self.devices:
                self.logger.warning(f"Device {device_id} not found")
                return False
            
            device = self.devices[device_id]
            
            # Remove from device type registry
            if device.device_type in self.device_types:
                if device_id in self.device_types[device.device_type]:
                    self.device_types[device.device_type].remove(device_id)
                
                # Remove empty device type
                if not self.device_types[device.device_type]:
                    del self.device_types[device.device_type]
            
            del self.devices[device_id]
            self.logger.info(f"Device {device_id} unregistered")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister device {device_id}: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """
        Get a device by its ID.
        
        Args:
            device_id: The ID of the device to retrieve
            
        Returns:
            Device: The device if found, None otherwise
        """
        return self.devices.get(device_id)
    
    def get_devices_by_type(self, device_type: str) -> List[Device]:
        """
        Get all devices of a specific type.
        
        Args:
            device_type: The type of devices to retrieve
            
        Returns:
            List[Device]: List of devices of the specified type
        """
        device_ids = self.device_types.get(device_type, [])
        return [self.devices[device_id] for device_id in device_ids if device_id in self.devices]
    
    def get_all_devices(self) -> List[Device]:
        """
        Get all registered devices.
        
        Returns:
            List[Device]: List of all registered devices
        """
        return list(self.devices.values())
    
    def initialize_device(self, device_id: str) -> bool:
        """
        Initialize a specific device.
        
        Args:
            device_id: The ID of the device to initialize
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        device = self.get_device(device_id)
        if not device:
            self.logger.error(f"Device {device_id} not found")
            return False
        
        try:
            success = device.initialize()
            if success:
                self.logger.info(f"Device {device_id} initialized")
            else:
                self.logger.error(f"Failed to initialize device {device_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error initializing device {device_id}: {e}")
            return False
    
    def shutdown_device(self, device_id: str) -> bool:
        """
        Shutdown a specific device.
        
        Args:
            device_id: The ID of the device to shutdown
            
        Returns:
            bool: True if shutdown successful, False otherwise
        """
        device = self.get_device(device_id)
        if not device:
            self.logger.error(f"Device {device_id} not found")
            return False
        
        try:
            success = device.shutdown()
            if success:
                self.logger.info(f"Device {device_id} shutdown")
            else:
                self.logger.error(f"Failed to shutdown device {device_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error shutting down device {device_id}: {e}")
            return False
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific device.
        
        Args:
            device_id: The ID of the device
            
        Returns:
            Dict: Device status information or None if device not found
        """
        device = self.get_device(device_id)
        if not device:
            return None
        
        return device.get_status()
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of all devices in the system.
        
        Returns:
            Dict: System-wide device status information
        """
        return {
            'total_devices': len(self.devices),
            'device_types': list(self.device_types.keys()),
            'devices_by_type': {
                device_type: len(device_ids) 
                for device_type, device_ids in self.device_types.items()
            },
            'active_devices': len([d for d in self.devices.values() if d.is_active]),
            'inactive_devices': len([d for d in self.devices.values() if not d.is_active])
        }
    
    def discover_devices(self) -> List[str]:
        """
        Discover available devices in the system.
        
        This is a placeholder for device discovery functionality.
        In a real implementation, this would scan for hardware devices.
        
        Returns:
            List[str]: List of discovered device IDs
        """
        # Placeholder implementation
        self.logger.info("Device discovery not implemented yet")
        return []
    
    def shutdown_all_devices(self) -> bool:
        """
        Shutdown all devices in the system.
        
        Returns:
            bool: True if all devices shutdown successfully, False otherwise
        """
        success = True
        for device_id in list(self.devices.keys()):
            if not self.shutdown_device(device_id):
                success = False
        
        return success 