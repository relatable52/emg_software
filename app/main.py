import tkinter as tk
from serial import Serial, SerialException
from serial.tools import list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch
import pywt

BAUDRATES = ["9600", "19200", "38400", "57600", "115200"]


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
    def __init__(self, master, fs=1000):
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

        # Filter and get envelopes
        if len(s1) > 200:
            fil1, env1 = filter_emg(s1, self.fs)
            fil2, env2 = filter_emg(s2, self.fs)
        else:
            fil1, env1, fil2, env2 = s1, s1, s2, s2

        # Raw signals
        self.ax[0, 0].plot(t, s1, label="Sensor 1 Raw", color='b')
        # self.ax[0, 0].plot(t, s2, label="Sensor 2 Raw", color='r')
        self.ax[0, 0].set_title("Raw Signals")

        # self.ax[0, 1].plot(t, s1, label="Sensor 1 Raw", color='b')
        self.ax[0, 1].plot(t, s2, label="Sensor 2 Raw", color='r')
        self.ax[0, 1].set_title("Raw Signals")

        # Filtered signals
        self.ax[1, 0].plot(t, fil1, label="Sensor 1 Filtered", color='b')
        # self.ax[1, 0].plot(t, fil2, label="Sensor 2 Filtered", color='r')
        self.ax[1, 0].set_title("Filtered EMG")

        # self.ax[1, 1].plot(t, fil1, label="Sensor 1 Filtered", color='b')
        self.ax[1, 1].plot(t, fil2, label="Sensor 2 Filtered", color='r')
        self.ax[1, 1].set_title("Filtered EMG")

        # Envelopes
        self.ax[2, 0].plot(t, env1, label="Sensor 1 Envelope", color='b')
        # self.ax[2, 0].plot(t, env2, label="Sensor 2 Envelope", color='r')
        self.ax[2, 0].set_title("Envelope")

        # self.ax[2, 1].plot(t, env1, label="Sensor 1 Envelope", color='b')
        self.ax[2, 1].plot(t, env2, label="Sensor 2 Envelope", color='r')
        self.ax[2, 1].set_title("Envelope")

        # for a in self.ax:
        #     a.legend()
        #     a.grid(True)

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
    recorded_data = {
        "sensor_1": [],
        "sensor_2": [],
        "time_stamp": []
    }
    # Create the main application window
    window = tk.Tk()
    window.title("Sample Tkinter Window")
    window.geometry("800x600")
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
    sample_rate_field = InputField(master=send_cmd_frame, label_text="Sample Rate:", default_value="1000")
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
            window
        )
    )
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

def start_measurement(serial_manager, sample_rate, duration, recorded_data, save_file_button, serial_monitor, plot_area, window):
    recorded_data = {
        "sensor_1": [],
        "sensor_2": [],
        "time_stamp": []
    }
    save_file_button.set_state(tk.DISABLED)
    serial_manager.write_data(f"START, {sample_rate}, {duration}")
    mesage = ""
    count = 0
    while mesage != "DONE":
        mesage = serial_manager.read_data()
        count = (count + 1)%100
        serial_monitor.append_text(mesage)
        if ',' in mesage:
            timestamp, sensor_1, sensor_2 = [int(i.strip()) for i in mesage.split(',')]
            if sensor_1 is not None and sensor_2 is not None:
                recorded_data["sensor_1"].append(sensor_1)
                recorded_data["sensor_2"].append(sensor_2)
                recorded_data["time_stamp"].append(timestamp / 1_000_000)  # Convert microseconds to seconds
                if count == 0:
                    plot_area.plot_data(recorded_data)
                    window.update()

    save_file_button.set_state(tk.NORMAL)

def save_data(data, file_name):
    df = pd.DataFrame(data)
    print(f"Saving data to {file_name}")
    df.to_csv(file_name)

def get_serial_ports():
    ports = list_ports.comports()
    return [port.device for port in ports]

def lowpass_env(x, fs):
    nyq = 0.5 * fs
    w = 5 / nyq
    b, a = butter(4, w, btype='low')
    return filtfilt(b, a, np.abs(x))

def filter_emg(signal, fs):
    if len(signal) < 100:  # Too short for filtfilt
        return signal, np.abs(signal)

    # --- Bandpass 20–200 Hz ---
    cut_low = 20 / (fs / 2)
    cut_high = 200 / (fs / 2)
    b1, a1 = butter(4, [cut_low, cut_high], btype='bandpass')
    try:
        emg1 = filtfilt(b1, a1, signal)
    except ValueError:
        return signal, np.abs(signal)

    # --- Notch filters at 50, 100, 150 Hz ---
    for notch_freq in [50, 100, 150]:
        Q = notch_freq / 10  # bandwidth = 10 Hz
        b_notch, a_notch = iirnotch(notch_freq / (fs / 2), Q)
        try:
            emg1 = filtfilt(b_notch, a_notch, emg1)
        except Exception as e:
            # skip unstable filter for short signals
            continue

    # --- Wavelet denoising ---
    coeffs = pywt.wavedec(emg1, 'db8', level=4)
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    uthresh = sigma * np.sqrt(2 * np.log(len(signal)))
    coeffs_thresh = [pywt.threshold(c, value=uthresh, mode='soft') for c in coeffs]
    denoised = pywt.waverec(coeffs_thresh, 'db8')
    denoised = denoised[:len(signal)]

    # --- Envelope ---
    envelope = lowpass_env(denoised, 1000)
    return denoised, envelope

def main():
    window = create_window()
    window.mainloop()

if __name__ == "__main__":
    main()