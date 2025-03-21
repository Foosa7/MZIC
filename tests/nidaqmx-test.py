import nidaqmx
import numpy as np

def find_daq_device():
    """
    Find and return the name (e.g. 'Dev1') of the first USB-6000 device detected.
    Returns None if no USB-6000 is found.
    """
    system = nidaqmx.system.System.local()
    for device in system.devices:
        if device.product_type == "USB-6000":
            return device.name
    return None

def list_ai_channels(device_name):
    """
    List and return all AI channel names of the DAQ device.
    """
    system = nidaqmx.system.System.local()
    for device in system.devices:
        if device.name == device_name:
            return [chan.name for chan in device.ai_physical_chans]
    return []

def acquire_samples(
    channels,
    samples_per_channel=100,
    min_val=-10.0,
    max_val=10.0
):
    """
    Acquire multiple samples (software-timed) from the given list of channel names.
    
    :param channels: A list of physical channel strings, e.g. ['Dev1/ai0', 'Dev1/ai1'].
    :param samples_per_channel: How many samples to read from each channel in one shot.
    :param min_val: Minimum voltage range
    :param max_val: Maximum voltage range
    :return: The data read from all channels, typically a list of lists if multiple channels.
    """
    with nidaqmx.Task() as task:
        # Add each requested channel to the task
        for ch in channels:
            task.ai_channels.add_ai_voltage_chan(ch, min_val=min_val, max_val=max_val)
        
        # Read multiple samples from each channel at once
        data = task.read(number_of_samples_per_channel=samples_per_channel)
        return data

def main():
    # Find the DAQ device
    device_name = find_daq_device()
    if not device_name:
        print("No USB-6000 device found.")
        return
    
    print(f"Found USB-6000 device: {device_name}")
    
    # List AI channels available on this device
    ai_channels = list_ai_channels(device_name)
    print(f"Available AI Channels: {ai_channels}")

    # Choose which channels to read
    # For example, let's pick ai0 and ai2. 
    # Adjust or prompt the user as needed.
    channels_to_read = [
        f"{device_name}/ai0",
        f"{device_name}/ai2",
    ]
    print(f"Reading from these channels: {channels_to_read}")
    
    # Acquire samples from each channel
    data = acquire_samples(channels_to_read, samples_per_channel=100)

    # Show results
    # If multiple channels are present, 'data' is a list of lists.
    # data[i] will be the samples for the i-th channel in channels_to_read
    print("Raw Data:", data)

    # Convert to a NumPy array for easier manipulation:
    # shape = (#channels, #samples)
    data_array = np.array(data)
    print("Data as NumPy array shape:", data_array.shape)

    # For example, compute average (mean) across samples for each channel
    # axis=1 -> average over the sample dimension
    means = np.mean(data_array, axis=1)
    for ch_name, mean_val in zip(channels_to_read, means):
        print(f"Channel {ch_name} average: {mean_val:.4f} V")

if __name__ == "__main__":
    main()
