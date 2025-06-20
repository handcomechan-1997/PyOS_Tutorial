"""
Terminal Device Module

This module provides terminal device functionality for the operating system.
It handles input/output operations for the command line interface.
"""

from typing import Optional, List
from .device_manager import Device
from utils.logger import Logger


class Terminal(Device):
    """Terminal device for handling I/O operations."""
    
    def __init__(self, device_id: str = "terminal_0"):
        super().__init__(device_id, "terminal", "System Terminal")
        self.logger = Logger(__name__)
        self.input_buffer: List[str] = []
        self.output_buffer: List[str] = []
        self.cursor_position = 0
        self.is_interactive = True
        
    def initialize(self) -> bool:
        """Initialize the terminal device."""
        try:
            self.is_active = True
            self.logger.info(f"Terminal {self.device_id} initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize terminal: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the terminal device."""
        try:
            self.is_active = False
            self.logger.info(f"Terminal {self.device_id} shutdown")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown terminal: {e}")
            return False
    
    def read_input(self) -> Optional[str]:
        """
        Read input from the terminal.
        
        Returns:
            str: Input string or None if no input available
        """
        if not self.is_active:
            return None
        
        try:
            # In a real implementation, this would read from stdin
            # For now, we'll use Python's input function
            if self.is_interactive:
                return input()
            return None
        except Exception as e:
            self.logger.error(f"Error reading input: {e}")
            return None
    
    def write_output(self, text: str) -> bool:
        """
        Write output to the terminal.
        
        Args:
            text: Text to write to the terminal
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            print(text, end='')
            self.output_buffer.append(text)
            return True
        except Exception as e:
            self.logger.error(f"Error writing output: {e}")
            return False
    
    def write_line(self, text: str) -> bool:
        """
        Write a line to the terminal with newline.
        
        Args:
            text: Text to write to the terminal
            
        Returns:
            bool: True if write successful, False otherwise
        """
        return self.write_output(text + '\n')
    
    def clear_screen(self) -> bool:
        """
        Clear the terminal screen.
        
        Returns:
            bool: True if clear successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            # Clear screen by printing multiple newlines
            print('\n' * 50)
            return True
        except Exception as e:
            self.logger.error(f"Error clearing screen: {e}")
            return False
    
    def get_cursor_position(self) -> int:
        """
        Get the current cursor position.
        
        Returns:
            int: Current cursor position
        """
        return self.cursor_position
    
    def set_cursor_position(self, position: int) -> bool:
        """
        Set the cursor position.
        
        Args:
            position: New cursor position
            
        Returns:
            bool: True if set successful, False otherwise
        """
        if position < 0:
            return False
        
        self.cursor_position = position
        return True
    
    def get_status(self) -> dict:
        """Get terminal status information."""
        status = super().get_status()
        status.update({
            'input_buffer_size': len(self.input_buffer),
            'output_buffer_size': len(self.output_buffer),
            'cursor_position': self.cursor_position,
            'is_interactive': self.is_interactive
        })
        return status 