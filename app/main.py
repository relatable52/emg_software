import tkinter as tk
from serial import Serial, SerialException
from serial.tools import list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import butter, iirnotch, lfilter
import pywt
import time
from collections import deque

BAUDRATES = ["9600", "19200", "38400", "57600", "115200"]

# Performance monitoring
class PerformanceStats:
    def __init__(self, window_size=100):
        self.filter_times = deque(maxlen=window_size)
        self.plot_times = deque(maxlen=window_size)
        self.last_sample_time = None
    
    def add_filter_time(self, t):
        self.filter_times.append(t)
    
    def add_plot_time(self, t):
        self.plot_times.append(t)
    
    def set_sample_timestamp(self, t):
        self.last_sample_time = t
    
    def get_stats(self):
        if not self.filter_times or not self.plot_times:
            return "No timing data yet"
        
        avg_filter = sum(self.filter_times) / len(self.filter_times) * 1000
        max_filter = max(self.filter_times) * 1000
        avg_plot = sum(self.plot_times) / len(self.plot_times) * 1000
        max_plot = max(self.plot_times) * 1000
        
        return (f"Filter: avg={avg_filter:.2f}ms max={max_filter:.2f}ms\n"
                f"Plot: avg={avg_plot:.2f}ms max={max_plot:.2f}ms")


class InputField(tk.Frame):
    def __init__(self, master, label_text, default_value=""):
        super().__init__(master)
        self.label = tk.Label(self, text=label_text)
        self.entry = tk.Entry(self)
        self.entry.insert(0, default_value)
        self.label.pack(side=tk.LEFT)
        self.entry.pack(side=tk.RIGHT)
        self.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

    def get_value(self):
        return self.entry.get()
    
    def set_value(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)


class DropdownMenu(tk.Frame):
    def __init__(self, master, label_text, options):
        super().__init__(master)
        self.label = tk.Label(self, text=label_text)
        self.variable = tk.StringVar(self)
        self.variable.set(options[0] if len(options)>0 else "")  # default value
        self.dropdown = tk.OptionMenu(self, self.variable, self.variable.get(), *options)
        self.label.pack(side=tk.LEFT)
        self.dropdown.pack(side=tk.RIGHT)
        self.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

    def get_value(self):
        return self.variable.get()
    
    def set_value(self, value):
        self.variable.set(value)
    
    def get_options(self):
        return self.dropdown['menu'].entrycget(0, 'label')
    
    def set_options(self, options):
        menu = self.dropdown['menu']
        menu.delete(0, 'end')
        for option in options:
            menu.add_command(label=option, command=tk._setit(self.variable, option))


class ActionButton(tk.Button):
    def __init__(self, master, button_text, command):
        super().__init__(master, text=button_text, command=command)
        self.pack(side=tk.LEFT, padx=5, pady=5)

    def set_state(self, state):
        self.config(state=state)


class ScrollableTextArea(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.text_area = tk.Text(self, wrap=tk.WORD)
        self.scrollbar = tk.Scrollbar(self, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=self.scrollbar.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def append_text(self, text):
        self.text_area.insert(tk.END, text + '\n')
        self.text_area.see(tk.END)

    def clear(self):
        self.text_area.delete(1.0, tk.END)


class PlotArea(tk.Frame):
    def __init__(self, master, fs=500):
        super().__init__(master)
        self.fs = fs
        self.figure, self.ax = plt.subplots(3, 2, figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def plot_data(self, data):
        self.ax[0, 0].clear()
        self.ax[1, 0].clear()
        self.ax[2, 0].clear()
        self.ax[0, 1].clear()
        self.ax[1, 1].clear()
        self.ax[2, 1].clear()

        t = data["time_stamp"]
        s1 = np.array(data["sensor_1"])
        s2 = np.array(data["sensor_2"])

        kalman_1 = np.array(data.get("kalman_1", []))
        kalman_2 = np.array(data.get("kalman_2", []))
        band_1 = np.array(data.get("filtered_1", []))
        band_2 = np.array(data.get("filtered_2", []))

        # Raw signals
        self.ax[0, 0].plot(t, s1, label="Sensor 1 Raw", color='b')
        self.ax[0, 0].set_title("Raw Signals")

        self.ax[0, 1].plot(t, s2, label="Sensor 2 Raw", color='r')
        self.ax[0, 1].set_title("Raw Signals")

        # Bandpass Filtered Signals
        if len(band_1) > 0:
            self.ax[2, 0].plot(t, band_1, label="Sensor 1 Bandpass", color='c')
            self.ax[2, 0].set_title("Bandpass Filtered Sensor 1")
        if len(band_2) > 0:
            self.ax[2, 1].plot(t, band_2, label="Sensor 2 Bandpass", color='orange')
            self.ax[2, 1].set_title("Bandpass Filtered Sensor 2")

        # Kalman Estimates
        if len(kalman_1) > 0:
            self.ax[1, 0].plot(t, kalman_1, label="Sensor 1 Kalman", color='g')
            self.ax[1, 0].set_title("Kalman Estimate Sensor 1")
        if len(kalman_2) > 0:
            self.ax[1, 1].plot(t, kalman_2, label="Sensor 2 Kalman", color='m')
            self.ax[1, 1].set_title("Kalman Estimate Sensor 2")

        self.canvas.draw()

    def clear_plots(self):
        for a in self.ax:
            a.clear()
        self.canvas.draw()


class SerialConnectionManager:
    def __init__(self, port_dropdown, baudrate_dropdown):
        self.ser = None
        self.port_dropdown = port_dropdown
        self.baudrate_dropdown = baudrate_dropdown
    
    def connect(self):
        port = self.port_dropdown.get_value()
        baudrate = int(self.baudrate_dropdown.get_value())
        try:
            self.ser = Serial(port, baudrate, timeout=1)
            print(f"Connected to {port} at {baudrate} baud.")
            return self.ser
        except SerialException as e:
            print(f"Error connecting to serial port: {e}")
            return None
        
    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port disconnected.")

    def read_data(self):
        try:
            if self.ser and self.ser.is_open:
                data = self.ser.readline().decode('utf-8').strip()
                # print(f"Received: {data}")
                return data
            else:
                print("Serial port is not open.")
                return None
        except SerialException as e:
            print(f"Error reading from serial port: {e}")
            return None
        
    def write_data(self, message):
        try:
            if self.ser and self.ser.is_open:
                self.ser.write((message + '\n').encode('utf-8'))
                print(f"Sent: {message}")
            else:
                print("Serial port is not open.")
        except SerialException as e:
            print(f"Error writing to serial port: {e}")
    

def create_window():
    recorded_data = {}
    # Create the main application window
    window = tk.Tk()
    window.title("Sample Tkinter Window")
    window.geometry("800x600")
    # Initialize real-time estimator objects with default sampling rate.
    # They will be updated automatically when the Sample Rate field changes.
    emg_filter_1 = EMGFilterAndEstimator(fs=500, hum_freq=50)
    emg_filter_2 = EMGFilterAndEstimator(fs=500, hum_freq=50)

    # Create frames for organizing the layout
    control_frame = tk.Frame(master=window)
    info_frame = tk.Frame(master=window)

    serial_config_frame = tk.Frame(master=control_frame)
    serial_ports_dropdown = DropdownMenu(master=serial_config_frame, label_text="Serial Port:", options=get_serial_ports())
    baudrate_dropdown = DropdownMenu(master=serial_config_frame, label_text="Baudrate:", options=BAUDRATES)
    serial_connection_manager = SerialConnectionManager(serial_ports_dropdown, baudrate_dropdown)
    connect_serial_button = ActionButton(master=serial_config_frame, button_text="Connect", command=lambda: serial_connection_manager.connect())

    save_file_frame = tk.Frame(master=control_frame)                         
    filename_field = InputField(master=save_file_frame, label_text="Filename:", default_value="data.csv")
    save_file_button = ActionButton(master=save_file_frame, button_text="Save Data", command=lambda: save_data(recorded_data, filename_field.get_value()))
    save_file_button.set_state(tk.DISABLED)

    serial_monitor = ScrollableTextArea(master=info_frame)
    clear_monitor_button = ActionButton(master=info_frame, button_text="Clear Monitor", command=lambda: serial_monitor.clear())
    plot_area = PlotArea(master=info_frame)
    clear_plots_button = ActionButton(master=info_frame, button_text="Clear Plots", command=lambda: plot_area.clear_plots())
    
    send_cmd_frame = tk.Frame(master=control_frame)
    sample_rate_field = InputField(master=send_cmd_frame, label_text="Sample Rate:", default_value="500")
    measurement_duration_field = InputField(master=send_cmd_frame, label_text="Measurement Duration (s):", default_value="10")
    send_cmd_button = ActionButton(
        master=send_cmd_frame, button_text="Start Measurement", 
        command=lambda: start_measurement(
            serial_connection_manager, 
            sample_rate_field.get_value(), 
            measurement_duration_field.get_value(), 
            recorded_data, 
            save_file_button,
            serial_monitor,
            plot_area, 
            window,
            emg_filter_1,
            emg_filter_2
        )
    )

    # Auto-update filters when the sample rate field is changed (on focus out or Enter)
    def on_sample_rate_change(event=None):
        try:
            fs_val = int(sample_rate_field.get_value())
            if fs_val <= 0:
                raise ValueError("fs must be positive")
        except Exception as e:
            print(f"Invalid sample rate: {e}")
            return

        # Update filters to use the new sampling rate
        emg_filter_1.update_fs(fs_val)
        emg_filter_2.update_fs(fs_val)
        plot_area.fs = fs_val

    sample_rate_field.entry.bind("<FocusOut>", on_sample_rate_change)
    sample_rate_field.entry.bind("<Return>", on_sample_rate_change)
    serial_config_frame.pack(side=tk.TOP, fill=tk.X)
    send_cmd_frame.pack(side=tk.TOP, fill=tk.X) 
    save_file_frame.pack(side=tk.TOP, fill=tk.X)

    serial_monitor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    clear_monitor_button.pack(side=tk.TOP, fill=tk.X)
    plot_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    clear_plots_button.pack(side=tk.TOP, fill=tk.X)

    control_frame.pack(side=tk.TOP, fill=tk.X)
    info_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
    return window

def start_measurement(serial_manager, sample_rate, duration, recorded_data, save_file_button, serial_monitor, plot_area, window, emg_filter_1, emg_filter_2):
    # Reset filter states and recorded data
    recorded_data["sensor_1"] = []
    recorded_data["sensor_2"] = []
    recorded_data["time_stamp"] = []
    recorded_data["kalman_1"] = [] 
    recorded_data["kalman_2"] = [] 
    recorded_data["filtered_1"] = []
    recorded_data["filtered_2"] = []

    # Create performance monitor
    perf_stats = PerformanceStats()
    
    # NOTE: You might want to re-initialize or reset the internal state (zi_notch, kf_state, etc.) of 
    # emg_filter_1 and emg_filter_2 here if they are reused for multiple runs!
    emg_filter_1.reset()
    emg_filter_2.reset()
    
    save_file_button.set_state(tk.DISABLED)
    serial_manager.write_data(f"START, {sample_rate}, {duration}")
    mesage = ""
    count = 0
    while mesage != "DONE":
        mesage = serial_manager.read_data()
        count = (count + 1)%500
        serial_monitor.append_text(mesage)
        
        if ',' in mesage:
            try:
                timestamp, sensor_1, sensor_2 = [int(i.strip()) for i in mesage.split(',')]
                
                # Time the filter processing
                t_filter_start = time.perf_counter()
                
                # --- NEW REAL-TIME PROCESSING ---
                # Process the new raw sample through the causal filters and Kalman
                # The returned values are the *current* filtered/estimated values.
                band_out_1, env_1 = emg_filter_1.process_sample(sensor_1)
                band_out_2, env_2 = emg_filter_2.process_sample(sensor_2)

                # Record filter processing time
                filter_time = time.perf_counter() - t_filter_start
                perf_stats.add_filter_time(filter_time)

                # Append raw data and the new estimates
                recorded_data["sensor_1"].append(sensor_1)
                recorded_data["sensor_2"].append(sensor_2)
                recorded_data["kalman_1"].append(env_1) # Append Kalman estimate
                recorded_data["kalman_2"].append(env_2) # Append Kalman estimate
                recorded_data["filtered_1"].append(band_out_1)  # Optionally store filtered data
                recorded_data["filtered_2"].append(band_out_2)  # Optionally store filtered data
                recorded_data["time_stamp"].append(timestamp / 1_000_000)
                
                if count == 0:
                    # Time the plotting
                    t_plot_start = time.perf_counter()
                    plot_area.plot_data(recorded_data)
                    window.update()
                    plot_time = time.perf_counter() - t_plot_start
                    perf_stats.add_plot_time(plot_time)
                    
                    # Show timing stats every 200 samples
                    serial_monitor.append_text("\n=== Performance Stats ===")
                    serial_monitor.append_text(perf_stats.get_stats())
                    serial_monitor.append_text("=====================\n")
            except ValueError:
                # Handle cases where data format is incorrect
                continue

    save_file_button.set_state(tk.NORMAL)

def save_data(data, file_name):
    df = pd.DataFrame(data)
    print(f"Saving data to {file_name}")
    df.to_csv(file_name)

def get_serial_ports():
    ports = list_ports.comports()
    return [port.device for port in ports]

def causal_filter(b, a, data, z_hist):
    """
    Applies a causal digital filter (IIR or FIR) using lfilter and manages 
    the filter state for continuous, real-time processing.
    """
    if len(data) == 0:
        return np.array([]), z_hist

    # Apply the filter and update the state
    filtered_data, z_new = lfilter(b, a, data, zi=z_hist)
    
    # Store the new state for the next chunk of data
    return filtered_data, z_new

# --- EMG Preprocessor with Causal Filters and Kalman Filter ---
class EMGFilterAndEstimator:
    def __init__(self, fs=500, hum_freq=50):
        # Store parameters
        self.fs = fs
        self.hum_freq = hum_freq

        # design all filters based on current sampling rate
        self._design_filters()

        # 4. Kalman Filter for Motion State Estimation
        # State: [Envelope Value]
        # A=1 (simple model: value stays the same unless acted upon)
        # H=1 (we measure the envelope directly)
        self.kf_A = np.array([[1.0]]) # State Transition Matrix
        self.kf_H = np.array([[1.0]]) # Measurement Matrix
        self.kf_Q = 1e-3 # Process Noise Covariance (Trust in the model)
        self.kf_R = 1e-1 # Measurement Noise Covariance (Trust in the measurement)

        # Initial State and Covariance
        self.kf_state = np.array([[0.0]]) # x_hat_k-1
        self.kf_P = np.array([[1.0]])     # P_k-1

    def _design_filters(self):
        """
        Design bandpass, envelope lowpass, and multi-harmonic notch filters
        for the current sampling rate and hum frequency.
        """
        nyq = 0.5 * self.fs

        # Notch filters for hum and its harmonics (50, 100, 150, ...)
        self.notches = []
        if self.hum_freq is not None and self.hum_freq > 0:
            max_harm = int(nyq // self.hum_freq)
            for k in range(1, max_harm + 1):
                f_h = self.hum_freq * k
                if f_h >= nyq:
                    break
                # design a narrow notch at f_h
                b_n, a_n = iirnotch(f_h / nyq, Q=30)
                zi_n = np.zeros(max(len(a_n), len(b_n)) - 1)
                self.notches.append({"b": b_n, "a": a_n, "zi": zi_n, "f": f_h})

        # Bandpass Filter (20-450 Hz for raw EMG - Causal)
        low_cut = 20 / nyq
        high_cut = min(450 / nyq, 0.999)
        if low_cut >= high_cut:
            # fallback to sensible defaults if sample rate is too low
            low_cut = max(0.001, 20 / (0.5 * self.fs))
            high_cut = min(0.499, high_cut)
        self.b_band, self.a_band = butter(2, [low_cut, high_cut], btype='bandpass', output='ba')
        self.zi_band = np.zeros(max(len(self.a_band), len(self.b_band)) - 1)

        # Lowpass Filter for Envelope (4th order, 5 Hz cutoff - Causal)
        env_cut = min(5 / nyq, 0.499)
        self.b_env, self.a_env = butter(4, env_cut, btype='low', output='ba')
        self.zi_env = np.zeros(max(len(self.a_env), len(self.b_env)) - 1)

    def process_sample(self, raw_sample):
        # 1. Hum Removal: apply each designed notch filter in cascade
        notch_signal = np.array([raw_sample])
        for notch in self.notches:
            notch_signal, zi_new = causal_filter(notch["b"], notch["a"], notch_signal, notch["zi"])
            notch["zi"] = zi_new

        # 2. Bandpass Filtering (Causal)
        band_out, self.zi_band = causal_filter(self.b_band, self.a_band, notch_signal, self.zi_band)
        
        # 3. Rectification
        rectified = np.abs(band_out)
        
        # 4. Lowpass Filtering for Envelope (Causal)
        env_out, self.zi_env = causal_filter(
            self.b_env, self.a_env, rectified, self.zi_env
        )
        measurement = env_out[0]

        # # --- Kalman Filter Steps ---
        # # 5. Predict
        # x_pred = self.kf_A @ self.kf_state
        # P_pred = self.kf_A @ self.kf_P @ self.kf_A.T + self.kf_Q
        
        # # 6. Update (Incorporate measurement)
        # y = measurement - self.kf_H @ x_pred
        # S = self.kf_H @ P_pred @ self.kf_H.T + self.kf_R
        # K = P_pred @ self.kf_H.T @ np.linalg.inv(S) # Kalman Gain
        
        # self.kf_state = x_pred + K @ y
        # self.kf_P = P_pred - K @ self.kf_H @ P_pred
        
        # # The Kalman state is the final, smoothed, real-time motion estimate
        # real_time_estimate = self.kf_state[0, 0]
        
        return band_out[0], measurement

    def update_fs(self, fs):
        """
        Update the sampling rate and redesign all filters. This will reset
        filter internal states (zi) to zeros to match the new designs.
        """
        try:
            fs_val = int(fs)
            if fs_val <= 0:
                raise ValueError("fs must be positive")
        except Exception as e:
            raise

        self.fs = fs_val
        # redesign filters and reset states
        self._design_filters()

    def reset(self):
        """
        Reset filter states and Kalman filter state.
        """
        # redesign filters and reset states
        self._design_filters()

def main():
    window = create_window()
    window.mainloop()

if __name__ == "__main__":
    main()