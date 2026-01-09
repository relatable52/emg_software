from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtGui import QFont
import pyqtgraph as pg

from core.config import NUM_SENSORS

class SerialMonitor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        font = QFont("Consolas", 10)
        self.setFont(font)

        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setMaximumBlockCount(1000)  # Limit to last 1000 lines

    def log(self, message: str):
        """
        Appends a message.
        Auto-scrolls to the bottom.
        """
        self.appendPlainText(message)
        
        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        
        scrollbar.setValue(scrollbar.maximum())


class EMGGraphGrid(pg.GraphicsLayoutWidget):
    """
    A custom widget that renders 8 EMG channels in a 4x2 grid.
    Inherits from GraphicsLayoutWidget for direct PyQTGraph integration.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_sensors = NUM_SENSORS
        self.curves = []
        
        # Visual Settings
        self.setBackground("#FFFFFF") # Gray background
        self.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.ci.layout.setSpacing(5)
        
        self._init_plots()

    def _init_plots(self):
        for i in range(self.num_sensors):
            # Create Plot Item
            p = self.addPlot(title=f"Sensor {i+1}")
            
            # Styles
            p.showGrid(x=True, y=True, alpha=0.5)
            p.setYRange(0, 4096)
            p.setMouseEnabled(x=False, y=True) # Allow Y-zoom, lock X
            p.hideButtons() # Hide the 'A' auto-scale button for cleanliness
            
            # Create Curve (Yellow line)
            curve = p.plot(pen=pg.mkPen("#0047A5", width=1.5))
            self.curves.append(curve)
            
            # Grid Layout Logic: 2 Columns
            # Row 0: [0], [1]
            # Row 1: [2], [3]
            if (i + 1) % 2 == 0:
                self.nextRow()

    def update_plots(self, buffers):
        """
        Efficiently updates all 8 lines.
        Expected input: List of 8 lists [ [ch1_data...], [ch2_data...] ... ]
        """
        if not buffers or len(buffers) != self.num_sensors:
            return

        # Optimization: Only draw the last N points to keep FPS high
        MAX_POINTS = 1000 
        
        for i in range(self.num_sensors):
            data = buffers[i]
            if len(data) > 0:
                # Slice the last N points
                view_data = data[-MAX_POINTS:]
                self.curves[i].setData(view_data)