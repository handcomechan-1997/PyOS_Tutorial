"""
Keyboard Device Module

This module provides keyboard device functionality for the operating system.
It handles keyboard input events and key processing.
"""

from typing import Optional, List, Callable
from .device_manager import Device
from utils.logger import Logger


class Keyboard(Device):
    """Keyboard device for handling key input events."""
    
    def __init__(self, device_id: str = "keyboard_0"):
        super().__init__(device_id, "keyboard", "System Keyboard")
        self.logger = Logger(__name__)
        self.key_buffer: List[str] = []
        self.max_buffer_size = 100
        self.key_handlers: List[Callable[[str], None]] = []
        self.is_caps_lock = False
        self.is_num_lock = True
        
    def initialize(self) -> bool:
        """Initialize the keyboard device."""
        try:
            self.is_active = True
            self.logger.info(f"Keyboard {self.device_id} initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize keyboard: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the keyboard device."""
        try:
            self.is_active = False
            self.logger.info(f"Keyboard {self.device_id} shutdown")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown keyboard: {e}")
            return False
    
    def read_key(self) -> Optional[str]:
        """
        Read a key from the keyboard buffer.
        
        Returns:
            str: Key character or None if no key available
        """
        if not self.is_active or not self.key_buffer:
            return None
        
        try:
            key = self.key_buffer.pop(0)
            self.logger.debug(f"Read key: {key}")
            return key
        except Exception as e:
            self.logger.error(f"Error reading key: {e}")
            return None
    
    def write_key(self, key: str) -> bool:
        """
        Write a key to the keyboard buffer.
        
        Args:
            key: Key character to add to buffer
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            if len(self.key_buffer) < self.max_buffer_size:
                self.key_buffer.append(key)
                self.logger.debug(f"Added key to buffer: {key}")
                
                # Notify key handlers
                for handler in self.key_handlers:
                    try:
                        handler(key)
                    except Exception as e:
                        self.logger.error(f"Error in key handler: {e}")
                
                return True
            else:
                self.logger.warning("Keyboard buffer full")
                return False
        except Exception as e:
            self.logger.error(f"Error writing key: {e}")
            return False
    
    def add_key_handler(self, handler: Callable[[str], None]) -> bool:
        """
        Add a key event handler.
        
        Args:
            handler: Function to call when a key is pressed
            
        Returns:
            bool: True if handler added successfully, False otherwise
        """
        try:
            self.key_handlers.append(handler)
            self.logger.debug("Key handler added")
            return True
        except Exception as e:
            self.logger.error(f"Error adding key handler: {e}")
            return False
    
    def remove_key_handler(self, handler: Callable[[str], None]) -> bool:
        """
        Remove a key event handler.
        
        Args:
            handler: Function to remove
            
        Returns:
            bool: True if handler removed successfully, False otherwise
        """
        try:
            if handler in self.key_handlers:
                self.key_handlers.remove(handler)
                self.logger.debug("Key handler removed")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing key handler: {e}")
            return False
    
    def clear_buffer(self) -> bool:
        """
        Clear the keyboard buffer.
        
        Returns:
            bool: True if clear successful, False otherwise
        """
        try:
            self.key_buffer.clear()
            self.logger.debug("Keyboard buffer cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing keyboard buffer: {e}")
            return False
    
    def get_buffer_size(self) -> int:
        """
        Get the current buffer size.
        
        Returns:
            int: Number of keys in buffer
        """
        return len(self.key_buffer)
    
    def toggle_caps_lock(self) -> bool:
        """
        Toggle caps lock state.
        
        Returns:
            bool: True if toggle successful, False otherwise
        """
        try:
            self.is_caps_lock = not self.is_caps_lock
            self.logger.debug(f"Caps lock {'on' if self.is_caps_lock else 'off'}")
            return True
        except Exception as e:
            self.logger.error(f"Error toggling caps lock: {e}")
            return False
    
    def toggle_num_lock(self) -> bool:
        """
        Toggle num lock state.
        
        Returns:
            bool: True if toggle successful, False otherwise
        """
        try:
            self.is_num_lock = not self.is_num_lock
            self.logger.debug(f"Num lock {'on' if self.is_num_lock else 'off'}")
            return True
        except Exception as e:
            self.logger.error(f"Error toggling num lock: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get keyboard status information."""
        status = super().get_status()
        status.update({
            'buffer_size': len(self.key_buffer),
            'max_buffer_size': self.max_buffer_size,
            'key_handlers_count': len(self.key_handlers),
            'caps_lock': self.is_caps_lock,
            'num_lock': self.is_num_lock
        })
        return status 