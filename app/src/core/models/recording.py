from typing import List

import pandas as pd

from core.models.types import Sample

class Recording:
    def __init__(self, num_sensors:int=8):
        self.num_sensors = num_sensors
        self.is_recording = False
        self.start_time = 0.0
        
        # Column-based storage is better for Plotting (PyQtGraph loves arrays)
        self.time: List[float] = []
        self.raw: List[List[int]] = [[] for _ in range(num_sensors)]
        self.filt: List[List[float]] = [[] for _ in range(num_sensors)]

    def clear(self):
        self.time.clear()
        self.raw = [[] for _ in range(self.num_sensors)]
        self.filt = [[] for _ in range(self.num_sensors)]
        self.is_recording = False

    def add_sample(self, sample: Sample):
        """
        Updates the state with a new sample. 
        This is the ONLY way data enters the application.
        """
        self.is_recording = True
        self.time.append(sample.timestamp)
        for i in range(self.num_sensors):
            self.raw[i].append(sample.raw_values[i])
            self.filt[i].append(sample.filt_values[i])

    def save_to_csv(self, filepath:str):
        """Saves the recording to a CSV file"""
        data = {"Time": self.time}
        for i in range(self.num_sensors):
            data[f"Raw_Sensor_{i+1}"] = self.raw[i]
            data[f"Filt_Sensor_{i+1}"] = self.filt[i]
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
            
    def get_plotting_data(self, sensor_index:int, window_size:int=1000):
        """Helper to get just the last N points for the graph"""
        if len(self.filt[sensor_index]) == 0:
            return [], []
            
        y_data = self.filt[sensor_index][-window_size:]
        # Generate X axis relative to current view (or use timestamp)
        x_data = self.time[-window_size:]
        return x_data, y_data