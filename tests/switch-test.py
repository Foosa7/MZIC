#!/usr/bin/env python3
"""
Test script for Switch device
Located at: tests/switch-test.py
Tests connection, channel setting, and channel reading
"""

import sys
import os
import time

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only what we need to avoid matplotlib backend issues
import serial
import serial.tools.list_ports

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'devices')))
    
# Create a minimal import that just has what Switch needs
from switch_device import Switch


def list_serial_ports():
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found!")
        return []
    
    print("\nAvailable serial ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    return ports


def select_port():
    """Let user select a serial port"""
    ports = list_serial_ports()
    if not ports:
        return None
    
    while True:
        try:
            choice = input("\nSelect port number (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
            
            port_idx = int(choice) - 1
            if 0 <= port_idx < len(ports):
                return ports[port_idx].device
            else:
                print("Invalid port number!")
        except ValueError:
            print("Please enter a valid number!")


def test_switch_connection(port):
    """Test basic connection to switch"""
    print(f"\n=== Testing connection to switch on {port} ===")
    try:
        switch = Switch(port)
        
        # Try to get current channel as connection test
        print("Attempting to read current channel...")
        channel = switch.get_channel()
        
        if channel is not None:
            print(f"✓ Connection successful! Current channel: {channel}")
            return switch
        else:
            print("✗ Connection failed - no valid response from device")
            return None
            
    except serial.SerialException as e:
        print(f"✗ Serial port error: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def test_channel_operations(switch):
    """Test setting and reading channels"""
    print("\n=== Testing Channel Operations ===")
    
    # Test channels including the ones from your examples
    test_channels = [1, 2, 3, 10, 0]  # Test various channels including 0 (block)
    
    for ch in test_channels:
        print(f"\n--- Testing channel {ch} ---")
        
        # Set channel
        print(f"Setting channel to {ch}...")
        try:
            switch.set_channel(ch)
            time.sleep(0.5)  # Wait for switch to settle
            
            # Read back channel
            print(f"Reading current channel...")
            current = switch.get_channel()
            
            if current == ch:
                print(f"✓ Channel {ch} verified successfully!")
            else:
                print(f"✗ Channel mismatch! Set: {ch}, Read: {current}")
                
        except Exception as e:
            print(f"✗ Error testing channel {ch}: {e}")


def verify_hex_commands(switch):
    """Verify the specific hex commands from the examples"""
    print("\n=== Verifying Hex Commands ===")
    print("Testing the example commands:")
    print("- Channel 1: ef ef 06 ff 0d 00 00 01 f1")
    print("- Channel 2: ef ef 06 ff 0d 00 00 02 f2")
    print("- Channel 3: ef ef 06 ff 0d 00 00 03 f3")
    
    for channel in [1, 2, 3]:
        print(f"\nTesting channel {channel}...")
        switch.set_channel(channel)
        time.sleep(0.5)
        
        current = switch.get_channel()
        if current == channel:
            print(f"✓ Channel {channel} hex command verified!")
        else:
            print(f"✗ Channel {channel} verification failed")


def interactive_mode(switch):
    """Interactive mode for manual testing"""
    print("\n=== Interactive Mode ===")
    print("Commands:")
    print("  s <channel> - Set channel (0-64)")
    print("  r           - Read current channel")
    print("  t           - Run test sequence")
    print("  v           - Verify hex commands")
    print("  q           - Quit")
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'r':
            channel = switch.get_channel()
            if channel is not None:
                print(f"Current channel: {channel}")
        elif cmd.startswith('s '):
            try:
                channel = int(cmd.split()[1])
                switch.set_channel(channel)
            except (ValueError, IndexError):
                print("Usage: s <channel>")
            except ValueError as e:
                print(f"Error: {e}")
        elif cmd == 't':
            test_channel_operations(switch)
        elif cmd == 'v':
            verify_hex_commands(switch)
        else:
            print("Unknown command. Type 'q' to quit.")


def run_all_tests(switch):
    """Run all automated tests"""
    test_channel_operations(switch)
    verify_hex_commands(switch)
    
    print("\n=== Test Summary ===")
    print("All automated tests completed.")
    print("Check the output above for any failures.")


def main():
    print("=== Switch Device Test Utility ===")
    print(f"Testing Switch class from: app.devices.switch_device")
    
    # Select port
    port = select_port()
    if not port:
        print("No port selected. Exiting.")
        return
    
    # Test connection
    switch = test_switch_connection(port)
    if not switch:
        print("\nFailed to connect to switch. Please check:")
        print("- The device is powered on")
        print("- The correct port is selected")
        print("- The baud rate is correct (115200)")
        return
    
    # Ask what to do
    print("\nWhat would you like to do?")
    print("1. Run all automatic tests")
    print("2. Test channel operations only")
    print("3. Verify hex commands only")
    print("4. Enter interactive mode")
    print("5. Exit")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        run_all_tests(switch)
    elif choice == '2':
        test_channel_operations(switch)
    elif choice == '3':
        verify_hex_commands(switch)
    elif choice == '4':
        interactive_mode(switch)
    
    print("\nTest complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)