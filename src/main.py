import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
)

from setup_window import SetupWindow
from labeling_window import LabelingWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Biosignal Labeling Tool")
        self.resize(900, 570)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Первый экран
        self.setup_page = SetupWindow()

        self.stack.addWidget(self.setup_page)

        self.setup_page.start_labeling.connect(
            self.open_labeling_page
        )

    def open_labeling_page(self, settings):
        self.labeling_page = LabelingWindow(settings)

        self.stack.addWidget(self.labeling_page)
        self.stack.setCurrentWidget(self.labeling_page)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())