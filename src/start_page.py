from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class StartPage(QWidget):
    new_project_requested = Signal()
    open_project_requested = Signal(str)

    def __init__(self):
        super().__init__()

        self.setStyleSheet(
            "background-color: white;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            120,
            80,
            120,
            80,
        )

        layout.setSpacing(25)

        title = QLabel(
            "Biosignal Labeling Tool"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: 600;
                color: #222222;
            }
            """
        )

        subtitle = QLabel(
            "Ручная разметка качества биосигналов"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                color: #777777;
            }
            """
        )

        new_button = QPushButton(
            "Создать новый проект"
        )

        open_button = QPushButton(
            "Открыть существующий проект"
        )

        for button in (
            new_button,
            open_button,
        ):
            button.setMinimumHeight(55)

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

        new_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #2563EB;
            }
            """
        )

        open_button.setStyleSheet(
            """
            QPushButton {
                background-color: #F3F4F6;
                color: #333333;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #E5E7EB;
            }
            """
        )

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        layout.addWidget(new_button)
        layout.addWidget(open_button)

        layout.addStretch()

        new_button.clicked.connect(
            self.new_project_requested.emit
        )

        open_button.clicked.connect(
            self.open_project
        )

    def open_project(self):
        project_dir = (
            QFileDialog.getExistingDirectory(
                self,
                "Выберите папку проекта",
            )
        )

        if not project_dir:
            return

        database = (
            Path(project_dir)
            / "project.db"
        )

        if not database.exists():
            QMessageBox.warning(
                self,
                "Это не проект",
                "В выбранной папке нет project.db.",
            )
            return

        self.open_project_requested.emit(
            project_dir
        )