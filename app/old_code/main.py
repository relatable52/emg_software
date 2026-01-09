import tkinter as tk
from serial import Serial, SerialException
from serial.tools import list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import butter, iirnotch, lfilter
from ppadb.client import Client as AdbClient
import time

BAUDRATES = ["230400", "460800", "921600", "115200", "57600", "38400", "19200", "9600"]
NUM_SENSORS = 8


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
    
    def set_text(self, text):
        self.config(text=text)


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
    def __init__(self, master, fs=500, num_sensors=8):
        super().__init__(master)
        self.fs = fs
        self.num_sensors = num_sensors
        
        # Create subplots for 8 sensors (4x2 grid)
        self.figure, self.ax = plt.subplots(4, 2, figsize=(12, 12))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Prepare empty lines for filtered data of 8 sensors
        self.lines = {}
        colors = ["red", "orange", "yellow", "green", "blue", "purple", "cyan", "magenta"]
        
        ax_flat = self.ax.flatten()
        for i in range(num_sensors):
            self.lines[f"filtered_{i+1}"] = ax_flat[i].plot(
                [], [], color=colors[i], label=f"Sensor {i+1} Filtered"
            )[0]
            ax_flat[i].set_xlim(0, 5)
            ax_flat[i].set_ylim(-700, 700)
            ax_flat[i].grid(True)
            ax_flat[i].legend(loc='upper right', fontsize=8)

        self.figure.tight_layout()
        self.canvas.draw()

    def reset_plot(self):
        for line in self.lines.values():
            line.set_data([], [])
        
        ax_flat = self.ax.flatten()
        for a in ax_flat:
            a.set_xlim(0, 5)
            a.set_ylim(-700, 700)
            a.relim()
            a.autoscale_view()
        self.canvas.draw_idle()

    def update_data(self, data, window_sec=5):
        t = np.array(data["time_stamp"])
        if len(t) == 0:
            return

        t_max = t[-1]
        t_min = max(0, t_max - window_sec)

        ax_flat = self.ax.flatten()
        for i in range(self.num_sensors):
            filtered_key = f"filtered_{i+1}"
            filtered_data = np.array(data.get(filtered_key, []))
            
            mask = t >= t_max - window_sec
            t_masked = t[mask]
            filtered_masked = filtered_data[mask] if len(filtered_data) else filtered_data
            
            self.lines[filtered_key].set_data(t_masked, filtered_masked)
            ax_flat[i].set_xlim(t_min, t_max)
            ax_flat[i].relim()
            ax_flat[i].autoscale_view(scaley=True)

        self.canvas.draw_idle()

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
            time.sleep(2)  # Wait for ESP32 to initialize
            # print(f"Connected to {port} at {baudrate} baud.")
            return self.ser
        except SerialException as e:
            # print(f"Error connecting to serial port: {e}")
            return None
        
    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            # print("Serial port disconnected.")

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def read_data(self):
        try:
            if self.ser and self.ser.is_open:
                data = self.ser.readline().decode('utf-8').strip()
                # # print(f"Received: {data}")
                return data
            else:
                # print("Serial port is not open.")
                return None
        except SerialException as e:
            # print(f"Error reading from serial port: {e}")
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
    window.title("EMG Data Acquisition - 8 Sensors")
    window.geometry("1400x900")
    
    # Initialize real-time estimator objects for 8 sensors
    emg_filters = [EMGFilterAndEstimator(fs=500, hum_freq=50) for _ in range(NUM_SENSORS)]

    # Create frames for organizing the layout
    control_frame = tk.Frame(master=window)
    
    # Create tab control
    notebook = tk.Frame(master=window)
    
    # Serial Monitor Tab
    monitor_tab = tk.Frame(notebook)
    serial_monitor = ScrollableTextArea(master=monitor_tab)
    
    # Plots Tab
    plot_tab = tk.Frame(notebook)
    plot_area = PlotArea(master=plot_tab, fs=500, num_sensors=NUM_SENSORS)
    
    # Create tab buttons
    tab_button_frame = tk.Frame(master=window)
    
    def show_monitor():
        plot_tab.pack_forget()
        monitor_tab.pack(fill=tk.BOTH, expand=True)
        monitor_button.config(bg="lightblue")
        plot_button.config(bg="lightgray")
    
    def show_plots():
        monitor_tab.pack_forget()
        plot_tab.pack(fill=tk.BOTH, expand=True)
        plot_button.config(bg="lightblue")
        monitor_button.config(bg="lightgray")
    
    monitor_button = tk.Button(tab_button_frame, text="Serial Monitor", command=show_monitor, bg="lightblue")
    monitor_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    plot_button = tk.Button(tab_button_frame, text="Plots", command=show_plots, bg="lightgray")
    plot_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    # Show monitor tab by default
    monitor_tab.pack(fill=tk.BOTH, expand=True)
    
    # Monitor controls
    monitor_control_frame = tk.Frame(master=monitor_tab)
    monitor_control_frame.pack(side=tk.BOTTOM, fill=tk.X)
    clear_monitor_button = ActionButton(master=monitor_control_frame, button_text="Clear Monitor", command=lambda: serial_monitor.clear())

    serial_config_frame = tk.Frame(master=control_frame)
    serial_ports_dropdown = DropdownMenu(master=serial_config_frame, label_text="Serial Port:", options=get_serial_ports())
    baudrate_dropdown = DropdownMenu(master=serial_config_frame, label_text="Baudrate:", options=BAUDRATES)
    serial_connection_manager = SerialConnectionManager(serial_ports_dropdown, baudrate_dropdown)
    connect_serial_button = ActionButton(master=serial_config_frame, button_text="Connect", command=lambda: None)

    def _toggle_serial():
        try:
            if serial_connection_manager.ser and serial_connection_manager.ser.is_open:
                serial_connection_manager.disconnect()
                connect_serial_button.set_text("Connect")
                serial_ports_dropdown.set_options(get_serial_ports())
                serial_monitor.append_text("Serial disconnected.")
            else:
                ser = serial_connection_manager.connect()
                if ser is not None and ser.is_open:
                    connect_serial_button.set_text("Disconnect")
                    serial_monitor.append_text(f"Connected to {ser.port} at {ser.baudrate}.")
                else:
                    serial_monitor.append_text("Failed to connect to serial port.")
        except Exception as e:
            serial_monitor.append_text(f"Serial toggle error: {e}")

    connect_serial_button.config(command=_toggle_serial)

    save_file_frame = tk.Frame(master=control_frame)                         
    filename_field = InputField(master=save_file_frame, label_text="Filename:", default_value="data.csv")
    save_file_button = ActionButton(master=save_file_frame, button_text="Save Data", command=lambda: save_data(recorded_data, filename_field.get_value()))
    save_file_button.set_state(tk.DISABLED)
    
    # Plot controls
    plot_control_frame = tk.Frame(master=plot_tab)
    plot_control_frame.pack(side=tk.BOTTOM, fill=tk.X)
    clear_plots_button = ActionButton(master=plot_control_frame, button_text="Clear Plots", command=lambda: plot_area.reset_plot())

    send_cmd_frame = tk.Frame(master=control_frame)
    sample_rate_field = InputField(master=send_cmd_frame, label_text="Sample Rate:", default_value="500")
    measurement_duration_field = InputField(master=send_cmd_frame, label_text="Measurement Duration (s):", default_value="10")
    video_option_button = tk.Checkbutton(master=send_cmd_frame, text="Record Video")
    video_option_button.var = tk.IntVar(value=0)
    video_option_button.config(variable=video_option_button.var)
    video_option_button.pack(side=tk.LEFT, padx=5, pady=5)
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
            emg_filters,
            video_option_button
        )
    )

    # Auto-update filters when the sample rate field is changed
    def on_sample_rate_change(event=None):
        try:
            fs_val = int(sample_rate_field.get_value())
            if fs_val <= 0:
                raise ValueError("fs must be positive")
        except Exception as e:
            serial_monitor.append_text(f"Invalid sample rate: {e}")
            return

        for emg_filter in emg_filters:
            emg_filter.update_fs(fs_val)
        plot_area.fs = fs_val
        serial_monitor.append_text(f"Updated sampling rate to {fs_val} Hz and redesigned filters.")

    sample_rate_field.entry.bind("<FocusOut>", on_sample_rate_change)
    sample_rate_field.entry.bind("<Return>", on_sample_rate_change)
    
    serial_config_frame.pack(side=tk.TOP, fill=tk.X)
    send_cmd_frame.pack(side=tk.TOP, fill=tk.X) 
    save_file_frame.pack(side=tk.TOP, fill=tk.X)

    control_frame.pack(side=tk.TOP, fill=tk.X)
    tab_button_frame.pack(side=tk.TOP, fill=tk.X)
    notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    return window

def start_measurement(serial_manager, sample_rate, duration, recorded_data, save_file_button, serial_monitor, plot_area, window, emg_filters, video_option_button):
    # Reset recorded data for all 8 sensors
    for i in range(1, NUM_SENSORS + 1):
        recorded_data[f"sensor_{i}"] = []
        recorded_data[f"filtered_{i}"] = []
    recorded_data["time_stamp"] = []

    # Reset filters
    for emg_filter in emg_filters:
        emg_filter._design_filters()
    plot_area.reset_plot()

    save_file_button.set_state(tk.DISABLED)
    
    # Clear any stale data in the buffer with timeout
    # print("[DEBUG] Clearing serial buffer...")
    start_time = time.time()
    while time.time() - start_time < 0.5:  # Only clear for 0.5 seconds max
        if serial_manager.read_data() is None:
            break
    
    # print(f"[DEBUG] Sending START command: START, {sample_rate}, {duration}")
    serial_monitor.append_text("Sending START command...")
    serial_manager.write_data(f"START, {sample_rate}, {duration}")
    
    # Give ESP32 time to process and start sending
    time.sleep(1)
    # print("[DEBUG] Waiting for measurement data...")
    serial_monitor.append_text("Waiting for measurement data...")
    message = ""
    count = 0
    messages = []
    start_time = time.time()

    if video_option_button.var.get():
        start_stop_camera()
    while message != "DONE":
        message = serial_manager.read_data()
        # print(f"[DEBUG] Received: {message}")
        
        if message is None:
            # print("[DEBUG] Read returned None, continuing...")
            window.update()
            continue
            
        count = (count + 1) % 1000  
        messages.append(message)
        
        if ',' in message:
            try:
                values = [int(i.strip()) for i in message.split(',')]
                timestamp = values[0]
                sensors = values[1:]

                if len(sensors) != NUM_SENSORS:
                    # print(f"[DEBUG] Expected {NUM_SENSORS} sensors, got {len(sensors)}")
                    continue

                recorded_data["time_stamp"].append(timestamp / 1_000_000)

                for i, sensor_value in enumerate(sensors, start=1):
                    # band_out, _ = emg_filters[i - 1].process_sample(sensor_value)
                    recorded_data[f"sensor_{i}"].append(sensor_value)
                    recorded_data[f"filtered_{i}"].append(0)
            except ValueError as e:
                # print(f"[DEBUG] ValueError: {e}")
                continue

        if count == 0:
            # plot_area.update_data(recorded_data, window_sec=5)
            time_elapsed = time.time() - start_time
            print(f"[DEBUG] Time elapsed: {time_elapsed:.2f} seconds")
            serial_monitor.append_text('\n'.join(messages))
            messages.clear()
            window.update()
    
    # print("Measurement complete - DONE received")
    serial_monitor.append_text("Measurement complete.")
    if video_option_button.var.get():
        start_stop_camera()
    save_file_button.set_state(tk.NORMAL)

def start_stop_camera():
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    if (len(devices) < 0):
        # print("0 device")
        return 0
    device = devices[0]
    device.input_keyevent(25)  # KEYCODE_CAMERA

def save_data(data, file_name):
    # Find the maximum length of all lists in the dictionary
    max_length = max(len(v) for v in data.values())

    # Ensure all lists are of the same length by padding with None
    for key in data:
        if len(data[key]) < max_length:
            data[key].extend([None] * (max_length - len(data[key])))

    # Create and save the DataFrame
    df = pd.DataFrame(data)
    # print(f"Saving data to {file_name}")
    df.to_csv(file_name, index=False)

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

        # Design all filters based on current sampling rate
        self._design_filters()

        # Kalman Filter for Motion State Estimation
        self.kf_A = np.array([[1.0]])  # State Transition Matrix
        self.kf_H = np.array([[1.0]])  # Measurement Matrix
        self.kf_Q = 1e-3  # Process Noise Covariance (Trust in the model)
        self.kf_R = 1e-1  # Measurement Noise Covariance (Trust in the measurement)

        # Initial State and Covariance
        self.kf_state = np.array([[0.0]])  # x_hat_k-1
        self.kf_P = np.array([[1.0]])     # P_k-1

    def _design_filters(self):
        """
        Design bandpass, band-stop, envelope lowpass, and multi-harmonic notch filters
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
                # Design a narrow notch at f_h
                b_n, a_n = iirnotch(f_h / nyq, Q=30)
                zi_n = np.zeros(max(len(a_n), len(b_n)) - 1)
                self.notches.append({"b": b_n, "a": a_n, "zi": zi_n, "f": f_h})

        # Bandpass Filter (20-250 Hz for raw EMG - Causal)
        low_cut = 20 / nyq
        high_cut = min(350 / nyq, 0.999)
        if low_cut >= high_cut:
            # Fallback to sensible defaults if sample rate is too low
            low_cut = max(0.001, 20 / (0.5 * self.fs))
            high_cut = min(0.499, high_cut)
        self.b_band, self.a_band = butter(2, [low_cut, high_cut], btype='bandpass', output='ba')
        self.zi_band = np.zeros(max(len(self.a_band), len(self.b_band)) - 1)

        # Band-stop Filter (1.5-3.5 Hz)
        stop_low = 1.5 / nyq
        stop_high = 3.5 / nyq
        self.b_stop, self.a_stop = butter(1, [stop_low, stop_high], btype='bandstop', output='ba')
        self.zi_stop = np.zeros(max(len(self.a_stop), len(self.b_stop)) - 1)

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

        # 3. Band-stop Filtering (Causal)
        stop_out, self.zi_stop = causal_filter(self.b_stop, self.a_stop, band_out, self.zi_stop)

        # 4. Rectification
        rectified = np.abs(stop_out)

        # 5. Lowpass Filtering for Envelope (Causal)
        env_out, self.zi_env = causal_filter(self.b_env, self.a_env, rectified, self.zi_env)
        measurement = env_out[0]

        return stop_out[0], measurement

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

def main():
    window = create_window()
    window.mainloop()

if __name__ == "__main__":
    main()