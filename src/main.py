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

from loaders.loader_factory import create_loader

from labeled_records_page import LabeledRecordsPage


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

        self.labeled_records_page = None

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

        # Сначала проверяем датасет.
        try:
            loader = create_loader(
                settings
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка датасета",
                str(error),
            )
            return

        if len(loader) == 0:
            QMessageBox.warning(
                self,
                "Нет сигналов",
                "В выбранных данных не найдено "
                "подходящих сигналов.",
            )
            return

        # И только если датасет нормальный,
        # создаём проект и базу.
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
            store,
            loader,
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

    def open_labeling_page(self, store, loader=None,):
        if self.project_store is not None:
            self.project_store.close()

        self.project_store = store

        settings = (
            self.project_store
            .get_settings()
        )

        # При открытии существующего проекта
        # loader ещё не создан.
        if loader is None:
            try:
                loader = create_loader(
                    settings
                )

            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Ошибка загрузки датасета",
                    str(error),
                )

                self.project_store.close()
                self.project_store = None

                self.show_start_page()
                return

        if len(loader) == 0:
            QMessageBox.warning(
                self,
                "Нет сигналов",
                "В выбранном датасете "
                "не найдено подходящих сигналов.",
            )

            self.project_store.close()
            self.project_store = None

            self.show_start_page()
            return

        if self.labeling_page is not None:
            self.stack.removeWidget(
                self.labeling_page
            )

            self.labeling_page.deleteLater()

        self.labeling_page = LabelingWindow(
            settings,
            self.project_store,
            loader,
        )

        self.labeling_page.show_labeled_requested.connect(
        self.show_labeled_records
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

    def show_labeled_records(self):
        if self.labeled_records_page is not None:
            self.stack.removeWidget(
                self.labeled_records_page
            )

            self.labeled_records_page.deleteLater()

        self.labeled_records_page = (
            LabeledRecordsPage(
                self.project_store
            )
        )

        self.labeled_records_page.back_requested.connect(
            self.show_labeling_page
        )

        self.labeled_records_page.open_record_requested.connect(
            self.open_labeled_record
        )

        self.stack.addWidget(
            self.labeled_records_page
        )

        self.stack.setCurrentWidget(
            self.labeled_records_page
        )


    def show_labeling_page(self):
        self.labeling_page.show_current_record()

        self.stack.setCurrentWidget(
            self.labeling_page
        )


    def open_labeled_record(
        self,
        record_id,
    ):
        self.labeling_page.open_record(
            record_id
        )

        self.stack.setCurrentWidget(
            self.labeling_page
        )


app = QApplication(
    sys.argv
)

window = MainWindow()
window.show()

sys.exit(
    app.exec()
)