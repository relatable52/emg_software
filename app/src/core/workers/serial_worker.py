import serial
import time
import struct

import numpy as np
from PySide6.QtCore import Signal, QObject

from core.services.signal_processing_service import EMGFilterAndEstimator
from core.models.types import Sample, SerialConfig, RecordingSettings
from core.config import NUM_SENSORS, RECORDING_TIMEOUT

class SerialWorker(QObject):
    data_received = Signal(Sample)
    log_message = Signal(str)
    finished = Signal()

    def __init__(self, serial_config: SerialConfig, recording_settings: RecordingSettings):
        super().__init__()
        # Initialize serial connection parameters
        self.serial_config = serial_config
        self.recording_settings = recording_settings
        self.filter_and_estimator = EMGFilterAndEstimator(recording_settings.sampling_rate)
        # Define packet structure    
        self.PACKET_SIZE = 4 + (2 * NUM_SENSORS) + 2 # uint32 + int16[] + uint16
        self.PACKET_FORMAT = f'<I{NUM_SENSORS}hH'  # Little-endian: uint32, int16[], uint16
        # Initialize filters for each sensor
        self.filters = [
            EMGFilterAndEstimator(fs=recording_settings.sampling_rate)
            for _ in range(NUM_SENSORS)
        ]
        # Control flag and timing
        self.is_running = True
        self.start_time = None
        self.timeout_limit = recording_settings.duration_sec + RECORDING_TIMEOUT

    def run(self):
        try:
            # Open Serial Port
            self.ser = serial.Serial(
                port=self.serial_config.port,
                baudrate=self.serial_config.baudrate,
                timeout=1
            )
            self.ser.reset_input_buffer()
            time.sleep(2)  # Wait for the serial connection to initialize
            self.log_message.emit(
                f"Connected to {self.serial_config.port} at {self.serial_config.baudrate} baud."
            )
            # Send start command
            cmd = struct.pack(
                '<BBII', 0xAA, 0x01,
                self.recording_settings.sampling_rate,
                self.recording_settings.duration_sec*1000 # The device expects ms
            )
            self.ser.write(cmd)
            self.log_message.emit(
                f"Recording for {self.recording_settings.duration_sec} seconds @ {self.recording_settings.sampling_rate} Hz."
            )
            # Start timing
            self.start_time = time.time()
            
            # Main Loop
            while self.is_running:
                # Check for timeout
                elapsed = time.time() - self.start_time
                if elapsed > self.timeout_limit:
                    self.log_message.emit(f"Recording timeout reached ({self.timeout_limit}s). Stopping...")
                    self.is_running = False
                    break
                    
                self.record_loop()
            # Clean up
            self.ser.close()
        except serial.SerialException as e:
            self.log_message.emit(f"Serial Error: {e}")
        # Emit finished signal
        self.finished.emit()

    def record_loop(self):
        if self.ser.in_waiting >= self.PACKET_SIZE:
            # 1. Read Binary Packet
            raw_bytes = self.ser.read(self.PACKET_SIZE)

            # 2. Validation (Check for 0xAAAA at end)
            if raw_bytes[-2:] != b'\xaa\xaa':
                self.ser.read(1) # Re-align
                return
            # 3. Unpack
            try:
                # I = uint32 (time), 8H = 8 uint16 (sensors)
                unpacked = struct.unpack(self.PACKET_FORMAT, raw_bytes)
                t_raw = unpacked[0]

                if t_raw == 0xFFFFFFFF:
                    # End of Recording Signal
                    self.log_message.emit("Received end of recording signal.")
                    self.is_running = False
                    return

                t_sec = t_raw / 1e6
                raw_vals = list(unpacked[1:1 + NUM_SENSORS])
                
                # 4. Filter
                filt_vals = []
                for i, val in enumerate(raw_vals):
                    filt_vals.append(self.filters[i].process_sample(val))
                
                # 5. Create Sample Object
                sample = Sample(
                    timestamp=t_sec,
                    raw_values=raw_vals,
                    filt_values=filt_vals
                )

                # 6. Emit to Controller
                self.data_received.emit(sample)
            except struct.error as e:
                self.log_message.emit(f"Struct Unpack Error: {e}")

    def request_stop(self):
        """Send stop command to ESP32 and stop recording"""
        try:
            if hasattr(self, 'ser') and self.ser.is_open:
                # Send stop command: header (0xAA), type (0x02), sampleRate (0), duration (0)
                stop_cmd = struct.pack('<BBII', 0xAA, 0x02, 0, 0)
                self.ser.write(stop_cmd)
                self.log_message.emit("Sent stop command to device.")
        except Exception as e:
            self.log_message.emit(f"Error sending stop command: {e}")
        
        self.is_running = False