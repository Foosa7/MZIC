# daq_test.py

from app.imports import *   

def test_daq_connection():
    try:
        # Try to get the first available DAQ device
        daq = DAQ.get_device()

        if daq is None:
            print("❌ No DAQ device connected or available.")
            return

        # Show basic status
        daq.show_status()

        # Optionally read from the first AI channel
        channels = daq.list_ai_channels()
        if channels:
            print(f"📡 Reading voltage from channel: {channels[0]}")
            voltage = daq.read_voltage(channels=[channels[0]], samples_per_channel=5)
            print(f"📈 Voltage readings: {voltage}")
        else:
            print("⚠️ No analog input channels found.")

        # Clean up
        daq.disconnect()

    except DaqNotFoundError:
        print("❌ NI-DAQmx is not installed or no DAQ device driver found.")
    except DaqError as e:
        print(f"⚠️ DAQ Error: {e}")
    except Exception as e:
        print(f"❗ Unexpected error: {e}")

if __name__ == "__main__":
    test_daq_connection()
