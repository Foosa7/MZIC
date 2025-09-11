# app/utils/switch_measurements.py

from app.imports import *
import time
from typing import List, Optional, Union
import logging
# from app.devices.thorlabs_device import ThorlabsDevice

class SwitchMeasurements:
    """Utility class for switch-based power measurements"""
    
    @staticmethod
    def parse_switch_channels(channel_string: str) -> List[int]:
        """
        Parse channel string input to get list of channel numbers.
        Supports formats like "1,2,3,4" or "1-4" or "1-4,7,9-12"
        
        Args:
            channel_string (str): User input for channels
            
        Returns:
            list: List of channel numbers
        """
        channels = []
        
        try:
            # Split by comma first
            parts = channel_string.replace(" ", "").split(",")
            
            for part in parts:
                if "-" in part:
                    # Handle range like "1-4"
                    start, end = part.split("-")
                    channels.extend(range(int(start), int(end) + 1))
                else:
                    # Handle single channel
                    channels.append(int(part))
            
            # Remove duplicates and sort
            channels = sorted(list(set(channels)))
            
            # Validate channel numbers (assuming 1-12 for your switch)
            valid_channels = [ch for ch in channels if 1 <= ch <= 12]
            
            if len(valid_channels) != len(channels):
                logging.warning(f"Warning: Some channels were out of range (1-12). Using: {valid_channels}")
                
            return valid_channels
            
        except Exception as e:
            raise ValueError(f"Invalid channel format: {channel_string}. Use format like '1,2,3,4' or '1-8'")
    
    @staticmethod
    def measure_with_switch(switch, thorlabs_device, channels: List[int], unit: str = "uW", settling_time: float = 0.05) -> List[float]:
        """
        Measure power using the optical switch for specified channels.
        
        Args:
            switch: Switch device object
            thorlabs_device: Thorlabs power meter device
            channels: List of channel numbers to measure
            unit: Power unit (uW, mW, W)
            settling_time: Time to wait after switching (seconds)
            
        Returns:
            list: Power measurements for each channel
        """
        measurements = []
        
        if not switch or not thorlabs_device:
            logging.error("Switch or Thorlabs device not available")
            return measurements
        
        # Measure only the specified switch channels
        for channel in channels:
            try:
                # Set switch to channel
                switch.set_channel(channel)
                
                # Small delay to allow switch to settle
                time.sleep(settling_time)
                
                # Read power
                power = thorlabs_device.read_power(unit=unit)
                measurements.append(power)
                
            except Exception as e:
                logging.error(f"Measuring channel {channel}: {e}")
                measurements.append(0.0)
        
        return measurements
    
    @staticmethod
    def measure_thorlabs_direct(thorlabs_devices: Union[list, object], unit: str = "uW") -> List[float]:
        """
        Measure power directly from Thorlabs devices (no switch).
        
        Args:
            thorlabs_devices: Single device or list of Thorlabs devices
            unit: Power unit (uW, mW, W)
            
        Returns:
            list: Power measurements
        """
        measurements = []
        
        if not thorlabs_devices:
            logging.error("No Thorlabs devices available")
            return measurements
        
        devices = thorlabs_devices if isinstance(thorlabs_devices, list) else [thorlabs_devices]
        
        for i, device in enumerate(devices):
            try:
                power = device.read_power(unit=unit)
                measurements.append(power)
            except Exception as e:
                logging.error(f"Reading Thorlabs {i}: {e}")
                measurements.append(0.0)
        
        return measurements
    
    @staticmethod
    def create_headers_with_switch(channels: List[int], unit: str = "uW", prefix: str = "ch") -> List[str]:
        """
        Create headers for switch-based measurements.
        
        Args:
            channels: List of channel numbers
            unit: Power unit
            prefix: Prefix for channel names
            
        Returns:
            list: Headers for each channel
        """
        return [f"{prefix}{ch}_{unit}" for ch in channels]
    
    @staticmethod
    def create_headers_thorlabs(num_devices: int, unit: str = "uW", prefix: str = "thorlabs") -> List[str]:
        """
        Create headers for direct Thorlabs measurements.
        
        Args:
            num_devices: Number of Thorlabs devices
            unit: Power unit
            prefix: Prefix for device names
            
        Returns:
            list: Headers for each device
        """
        return [f"{prefix}{i}_{unit}" for i in range(num_devices)]