import sys

from PySide6.QtWidgets import QApplication
import qdarkstyle
from qdarkstyle.light.palette import LightPalette

from core.views.main_window import MainWindow
from core.models.recording import Recording
from core.controllers.main_controller import MainController
from core.config import NUM_SENSORS

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply light theme
    style_sheet = qdarkstyle.load_stylesheet(palette=LightPalette)
    app.setStyleSheet(style_sheet)
    
    # Create main window
    main_window = MainWindow()
    
    # Create recording state (data model)
    recording_state = Recording(num_sensors=NUM_SENSORS)
    
    # Create controller (connects UI to business logic)
    controller = MainController(main_window, recording_state)
    
    main_window.show()
    sys.exit(app.exec())