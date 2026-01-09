#!/usr/bin/env python3
"""
Simple CLI script to record EMG data from Arduino/ESP32
No UI, just serial communication and CSV saving
"""

import serial
from serial.tools import list_ports
import pandas as pd
import sys
import time

NUM_SENSORS = 8

def get_serial_ports():
    """List available serial ports"""
    ports = list_ports.comports()
    return [port.device for port in ports]

def record_emg(port, baudrate, sample_rate, duration_sec, output_file="emg_data.csv"):
    """
    Record EMG data from serial port
    
    Args:
        port: Serial port (e.g., 'COM5', '/dev/ttyUSB0')
        baudrate: Baud rate (e.g., 230400)
        sample_rate: Sampling rate in Hz (e.g., 500)
        duration_sec: Recording duration in seconds (e.g., 10)
        output_file: Output CSV filename
    """
    
    print(f"Connecting to {port} at {baudrate} baud...")
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for board to initialize
        print(f"Connected!")
    except serial.SerialException as e:
        print(f"Error: Could not open {port}: {e}")
        return False
    
    # Initialize data storage
    recorded_data = {f"sensor_{i}": [] for i in range(1, NUM_SENSORS + 1)}
    recorded_data["time_stamp"] = []
    
    # Clear buffer
    print("Clearing serial buffer...")
    start_time = time.time()
    while time.time() - start_time < 0.5:
        if ser.readline() is None:
            break
    
    # Send START command
    print(f"Starting measurement: {sample_rate}Hz for {duration_sec}s")
    command = f"START, {sample_rate}, {duration_sec}\n"
    ser.write(command.encode('utf-8'))
    
    # Wait for initial messages
    time.sleep(1)
    
    # Record data
    print("Recording... (press Ctrl+C to stop)")
    message_count = 0
    
    try:
        while True:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                message_count += 1
                
                # Print progress every 50 samples
                if message_count % 50 == 0:
                    print(f"  {message_count} samples received...")
                
                # Check for DONE
                if line == "DONE":
                    print(f"Recording complete! ({message_count} samples)")
                    break
                
                # Parse sensor data
                if ',' in line:
                    try:
                        values = [int(i.strip()) for i in line.split(',')]
                        timestamp = values[0]
                        sensors = values[1:]
                        
                        if len(sensors) != NUM_SENSORS:
                            continue
                        
                        recorded_data["time_stamp"].append(timestamp / 1_000_000)
                        for i, sensor_value in enumerate(sensors, start=1):
                            recorded_data[f"sensor_{i}"].append(sensor_value)
                    except ValueError:
                        continue
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
    
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    
    finally:
        ser.close()
        print("Serial connection closed")
    
    # Save to CSV
    if recorded_data["time_stamp"]:
        df = pd.DataFrame(recorded_data)
        df.to_csv(output_file, index=False)
        print(f"Data saved to: {output_file}")
        print(f"Total samples: {len(df)}")
        return True
    else:
        print("No data recorded!")
        return False

def main():
    """Main CLI interface"""
    
    # List ports
    ports = get_serial_ports()
    if not ports:
        print("Error: No serial ports found!")
        return
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"  {i}: {port}")
    
    # Get user input
    port_idx = input("Enter port number: ").strip()
    try:
        port = ports[int(port_idx)]
    except (ValueError, IndexError):
        print("Invalid port selection")
        return
    
    baudrate = input("Enter baudrate (default 230400): ").strip()
    baudrate = int(baudrate) if baudrate else 230400
    
    sample_rate = input("Enter sample rate in Hz (default 500): ").strip()
    sample_rate = int(sample_rate) if sample_rate else 500
    
    duration = input("Enter duration in seconds (default 10): ").strip()
    duration = int(duration) if duration else 10
    
    filename = input("Enter output filename (default emg_data.csv): ").strip()
    filename = filename if filename else "emg_data.csv"
    
    # Record
    record_emg(port, baudrate, sample_rate, duration, filename)

if __name__ == "__main__":
    main()
