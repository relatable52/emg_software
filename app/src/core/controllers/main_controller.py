from PySide6.QtCore import QObject, QThread, QTimer, Slot
from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtSerialPort import QSerialPortInfo

# Import Data Models
from core.models.types import SerialConfig, RecordingSettings
from core.models.recording import Recording

# Import Worker
from core.workers.serial_worker import SerialWorker

# Import Config Constants
from core.config import BAUDRATES, DEFAULT_BAUDRATE, DEFAULT_FS, DEFAULT_DURATION

class MainController(QObject):
    def __init__(self, main_window, recording_state: Recording):
        super().__init__()
        self.window = main_window
        self.ui = main_window.ui  # Access to widgets
        self.state = recording_state
        
        # Threading references
        self.thread = None
        self.worker = None
        self.is_recording = False

        # 1. SETUP DEFAULT VALUES
        self._setup_defaults()

        # 2. CONNECT UI SIGNALS
        self.ui.pushButton_toggleRecording.clicked.connect(self.toggle_recording)
        self.ui.pushButton_saveData.clicked.connect(self.save_recording)
        
        # Initial Button State
        self.ui.pushButton_saveData.setEnabled(False)

        # 3. SETUP VIEW REFRESH TIMER (10 FPS)
        # We process data at 500Hz, but only draw at 10Hz to save CPU.
        self.view_timer = QTimer()
        self.view_timer.timeout.connect(self.update_view)
        self.view_timer.start(100) # 100ms ~= 10 FPS

    def _setup_defaults(self):
        """Initialize control frame with default values"""
        # Populate available serial ports
        ports = QSerialPortInfo.availablePorts()
        self.ui.comboBox_port.clear()
        for port in ports:
            self.ui.comboBox_port.addItem(port.portName())
        
        # Setup baudrate options from config
        self.ui.comboBox_baudrate.clear()
        self.ui.comboBox_baudrate.addItems([str(b) for b in BAUDRATES])
        self.ui.comboBox_baudrate.setCurrentText(str(DEFAULT_BAUDRATE))
        
        # Set default sampling rate and duration from config
        self.ui.doubleSpinBox_samplingRate.setRange(100, 10000)
        self.ui.doubleSpinBox_samplingRate.setValue(DEFAULT_FS)
        self.ui.doubleSpinBox_samplingRate.setSuffix(" Hz")
        
        self.ui.doubleSpinBox_duration.setRange(1, 3600)
        self.ui.doubleSpinBox_duration.setValue(DEFAULT_DURATION)
        self.ui.doubleSpinBox_duration.setSuffix(" s")

    # --- RECORDING LOGIC ---

    def toggle_recording(self):
        """Toggle between start and stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start the recording process"""
        # Get Config from UI
        port = self.ui.comboBox_port.currentText()
        if not port:
            QMessageBox.warning(self.window, "Port Error", "Please select a serial port.")
            return
            
        try:
            baud = int(self.ui.comboBox_baudrate.currentText())
        except ValueError:
            baud = 921600  # Default fallback

        # Get Recording Parameters
        try:
            fs = int(self.ui.doubleSpinBox_samplingRate.value())
            dur = int(self.ui.doubleSpinBox_duration.value())
        except ValueError:
            QMessageBox.warning(self.window, "Input Error", "Check sampling rate and duration.")
            return

        # Prepare Config Objects
        serial_conf = SerialConfig(port=port, baudrate=baud)
        settings = RecordingSettings(sampling_rate=fs, duration_sec=dur)

        # Reset State
        self.state.clear()

        # Setup Thread & Worker
        self.thread = QThread()
        self.worker = SerialWorker(serial_conf, settings)
        self.worker.moveToThread(self.thread)

        # Connect Worker Signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_recording_stopped)
        
        # Data & Logging (worker handles connection/start messages)
        self.worker.data_received.connect(self.handle_sample)
        self.worker.log_message.connect(self.log)

        # Start Thread (worker will connect to serial and start recording)
        self.thread.start()
        
        # Update UI
        self.is_recording = True
        self.ui.pushButton_toggleRecording.setText("Stop Recording")
        self.ui.comboBox_port.setEnabled(False)
        self.ui.comboBox_baudrate.setEnabled(False)
        self.ui.doubleSpinBox_samplingRate.setEnabled(False)
        self.ui.doubleSpinBox_duration.setEnabled(False)

    def stop_recording(self):
        """Stop the recording process"""
        if self.worker:
            # Update state to stop updating plots
            self.state.is_recording = False
            # Signal the worker to stop
            self.worker.request_stop()
            # Update ports
            ports = QSerialPortInfo.availablePorts()
            self.ui.comboBox_port.clear()
            for port in ports:
                self.ui.comboBox_port.addItem(port.portName())

    def on_recording_stopped(self):
        """Called automatically when the recording thread finishes"""
        self.worker = None
        self.thread = None
        self.is_recording = False
        
        # Update UI
        self.ui.pushButton_toggleRecording.setText("Start Recording")
        self.ui.comboBox_port.setEnabled(True)
        self.ui.comboBox_baudrate.setEnabled(True)
        self.ui.doubleSpinBox_samplingRate.setEnabled(True)
        self.ui.doubleSpinBox_duration.setEnabled(True)
        self.ui.pushButton_saveData.setEnabled(True)
        self.log("Recording stopped.")

    def save_recording(self):
        """Save the recorded data to file"""
        # Check if there's data to save
        if not self.state.time or len(self.state.time) == 0:
            QMessageBox.warning(self.window, "No Data", "No recording data to save.")
            return
        
        # Open file dialog to choose save location
        filepath, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save Recording",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        # User cancelled the dialog
        if not filepath:
            return
        
        # Ensure .csv extension
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        
        try:
            self.state.save_to_csv(filepath)
            self.log(f"Recording saved to: {filepath}")
            QMessageBox.information(self.window, "Success", f"Recording saved to:\n{filepath}")
        except Exception as e:
            self.log(f"Error saving file: {e}")
            QMessageBox.critical(self.window, "Save Error", f"Failed to save recording:\n{e}")

    # --- DATA HANDLING ---

    @Slot(object)
    def handle_sample(self, sample):
        """
        Called by Worker (High Speed).
        Only updates the Data Model.
        """
        self.state.add_sample(sample)
        self.log(f"{sample.timestamp:.2f}, {sample.raw_values}")

    def update_view(self):
        """
        Called by QTimer (10 FPS).
        Updates the Visual Components.
        """
        # Only update plots when recording and data is available
        if self.is_recording and self.state.filt and len(self.state.filt[0]) > 0:
            # Pass the filtered data buffer (List[List[float]])
            # The widget will handle slicing to last N points
            self.ui.widget_plots.update_plots(self.state.filt)

    def log(self, msg):
        """Updates the Custom Serial Monitor Component"""
        self.ui.plainTextEdit_serial.log(msg)