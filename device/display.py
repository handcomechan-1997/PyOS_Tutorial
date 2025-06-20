"""
Display Device Module

This module provides display device functionality for the operating system.
It handles screen output and display management.
"""

from typing import List, Tuple, Optional
from .device_manager import Device
from utils.logger import Logger


class Display(Device):
    """Display device for handling screen output."""
    
    def __init__(self, device_id: str = "display_0"):
        super().__init__(device_id, "display", "System Display")
        self.logger = Logger(__name__)
        self.width = 80  # Default terminal width
        self.height = 24  # Default terminal height
        self.screen_buffer: List[List[str]] = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.foreground_color = "white"
        self.background_color = "black"
        self.is_cursor_visible = True
        
    def initialize(self) -> bool:
        """Initialize the display device."""
        try:
            self.is_active = True
            self._initialize_screen_buffer()
            self.logger.info(f"Display {self.device_id} initialized ({self.width}x{self.height})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the display device."""
        try:
            self.is_active = False
            self.logger.info(f"Display {self.device_id} shutdown")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown display: {e}")
            return False
    
    def _initialize_screen_buffer(self):
        """Initialize the screen buffer with empty characters."""
        self.screen_buffer = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(' ')
            self.screen_buffer.append(row)
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set the display resolution.
        
        Args:
            width: Screen width in characters
            height: Screen height in characters
            
        Returns:
            bool: True if resolution set successfully, False otherwise
        """
        if width <= 0 or height <= 0:
            return False
        
        try:
            self.width = width
            self.height = height
            self._initialize_screen_buffer()
            self.logger.info(f"Display resolution set to {width}x{height}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting resolution: {e}")
            return False
    
    def clear_screen(self) -> bool:
        """
        Clear the entire screen.
        
        Returns:
            bool: True if clear successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            self._initialize_screen_buffer()
            self.cursor_x = 0
            self.cursor_y = 0
            self.logger.debug("Screen cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing screen: {e}")
            return False
    
    def write_char(self, char: str, x: int = None, y: int = None) -> bool:
        """
        Write a character to the screen at specified position.
        
        Args:
            char: Character to write
            x: X coordinate (uses cursor position if None)
            y: Y coordinate (uses cursor position if None)
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            if x is None:
                x = self.cursor_x
            if y is None:
                y = self.cursor_y
            
            if 0 <= x < self.width and 0 <= y < self.height:
                self.screen_buffer[y][x] = char
                self.cursor_x = x + 1
                if self.cursor_x >= self.width:
                    self.cursor_x = 0
                    self.cursor_y += 1
                    if self.cursor_y >= self.height:
                        self._scroll_up()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error writing character: {e}")
            return False
    
    def write_string(self, text: str, x: int = None, y: int = None) -> bool:
        """
        Write a string to the screen at specified position.
        
        Args:
            text: String to write
            x: X coordinate (uses cursor position if None)
            y: Y coordinate (uses cursor position if None)
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            if x is None:
                x = self.cursor_x
            if y is None:
                y = self.cursor_y
            
            success = True
            for i, char in enumerate(text):
                if char == '\n':
                    x = 0
                    y += 1
                    if y >= self.height:
                        self._scroll_up()
                        y = self.height - 1
                else:
                    if not self.write_char(char, x, y):
                        success = False
                        break
                    x += 1
                    if x >= self.width:
                        x = 0
                        y += 1
                        if y >= self.height:
                            self._scroll_up()
                            y = self.height - 1
            
            self.cursor_x = x
            self.cursor_y = y
            return success
        except Exception as e:
            self.logger.error(f"Error writing string: {e}")
            return False
    
    def _scroll_up(self):
        """Scroll the screen up by one line."""
        try:
            # Remove top line and add empty line at bottom
            self.screen_buffer.pop(0)
            new_line = [' ' for _ in range(self.width)]
            self.screen_buffer.append(new_line)
        except Exception as e:
            self.logger.error(f"Error scrolling screen: {e}")
    
    def set_cursor_position(self, x: int, y: int) -> bool:
        """
        Set the cursor position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            bool: True if position set successfully, False otherwise
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cursor_x = x
            self.cursor_y = y
            return True
        return False
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get the current cursor position.
        
        Returns:
            Tuple[int, int]: Current (x, y) cursor position
        """
        return (self.cursor_x, self.cursor_y)
    
    def set_cursor_visibility(self, visible: bool) -> bool:
        """
        Set cursor visibility.
        
        Args:
            visible: True to show cursor, False to hide
            
        Returns:
            bool: True if visibility set successfully, False otherwise
        """
        self.is_cursor_visible = visible
        return True
    
    def set_colors(self, foreground: str = None, background: str = None) -> bool:
        """
        Set text colors.
        
        Args:
            foreground: Foreground color name
            background: Background color name
            
        Returns:
            bool: True if colors set successfully, False otherwise
        """
        if foreground:
            self.foreground_color = foreground
        if background:
            self.background_color = background
        return True
    
    def get_screen_content(self) -> List[List[str]]:
        """
        Get the current screen content.
        
        Returns:
            List[List[str]]: Screen buffer content
        """
        return [row[:] for row in self.screen_buffer]
    
    def refresh(self) -> bool:
        """
        Refresh the display (in a real implementation, this would update the screen).
        
        Returns:
            bool: True if refresh successful, False otherwise
        """
        if not self.is_active:
            return False
        
        try:
            # In a real implementation, this would update the actual display
            # For now, we'll just log that refresh was called
            self.logger.debug("Display refresh requested")
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing display: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get display status information."""
        status = super().get_status()
        status.update({
            'width': self.width,
            'height': self.height,
            'cursor_x': self.cursor_x,
            'cursor_y': self.cursor_y,
            'cursor_visible': self.is_cursor_visible,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        })
        return status 