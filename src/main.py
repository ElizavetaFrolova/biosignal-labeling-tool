import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
)

from labeling_window import LabelingWindow
from setup_window import SetupWindow
from start_page import StartPage
from storage.project_store import ProjectStore


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Biosignal Labeling Tool"
        )

        self.resize(
            900,
            570,
        )

        self.project_store = None
        self.labeling_page = None

        self.stack = QStackedWidget()
        self.setCentralWidget(
            self.stack
        )

        self.start_page = StartPage()
        self.setup_page = SetupWindow()

        self.stack.addWidget(
            self.start_page
        )

        self.stack.addWidget(
            self.setup_page
        )

        self.start_page.new_project_requested.connect(
            self.show_new_project
        )

        self.start_page.open_project_requested.connect(
            self.open_project
        )

        self.setup_page.back_requested.connect(
            self.show_start_page
        )

        self.setup_page.create_project.connect(
            self.create_project
        )

        self.show_start_page()

    def show_start_page(self):
        self.stack.setCurrentWidget(
            self.start_page
        )

    def show_new_project(self):
        self.stack.setCurrentWidget(
            self.setup_page
        )

    def create_project(self, settings):
        settings = dict(settings)

        parent_dir = settings.pop(
            "project_parent"
        )

        project_name = settings[
            "project_name"
        ]

        try:
            store = ProjectStore.create(
                parent_dir,
                project_name,
                settings,
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Не удалось создать проект",
                str(error),
            )
            return

        self.open_labeling_page(
            store
        )

    def open_project(self, project_dir):
        try:
            store = ProjectStore.open(
                project_dir
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Не удалось открыть проект",
                str(error),
            )
            return

        self.open_labeling_page(
            store
        )

    def open_labeling_page(self, store):
        if self.project_store is not None:
            self.project_store.close()

        self.project_store = store

        settings = (
            self.project_store
            .get_settings()
        )

        if self.labeling_page is not None:
            self.stack.removeWidget(
                self.labeling_page
            )

            self.labeling_page.deleteLater()

        self.labeling_page = LabelingWindow(
            settings,
            self.project_store,
        )

        self.stack.addWidget(
            self.labeling_page
        )

        self.stack.setCurrentWidget(
            self.labeling_page
        )

    def closeEvent(self, event):
        if self.project_store is not None:
            self.project_store.close()

        event.accept()


app = QApplication(
    sys.argv
)

window = MainWindow()
window.show()

sys.exit(
    app.exec()
)