from PySide6.QtWidgets import QMainWindow

from core.generated.main_window import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the ui from the generated code
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)