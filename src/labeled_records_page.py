from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LabeledRecordsPage(QWidget):
    back_requested = Signal()
    open_record_requested = Signal(str)

    CLASS_NAMES = {
        0: "Чистый",
        1: "Небольшой шум",
        2: "Сильный шум",
        3: "Нечитаемый",
    }

    def __init__(self, project_store):
        super().__init__()

        self.project_store = project_store

        self.setStyleSheet(
            """
            QWidget {
                background-color: white;
                color: #222222;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("Размеченные записи")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 600;
            """
        )

        layout.addWidget(title)

        self.count_label = QLabel()
        self.count_label.setStyleSheet(
            "color: #777777; font-size: 14px;"
        )

        layout.addWidget(self.count_label)

        # Таблица
        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "ID записи",
                "Класс",
                "Последнее изменение",
            ]
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.doubleClicked.connect(
            self.open_selected_record
        )

        layout.addWidget(self.table)

        # Кнопки
        buttons_layout = QHBoxLayout()

        back_button = QPushButton("← Назад")

        open_button = QPushButton(
            "Открыть запись"
        )

        remove_button = QPushButton(
            "Удалить разметку"
        )

        for button in (
            back_button,
            open_button,
            remove_button,
        ):
            button.setMinimumHeight(40)
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

        open_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 7px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #2563EB;
            }
            """
        )

        remove_button.setStyleSheet(
            """
            QPushButton {
                background-color: #FDECEC;
                color: #C62828;
                border: 1px solid #C62828;
                border-radius: 8px;
                padding: 7px 18px;
            }

            QPushButton:hover {
                background-color: #F8DADA;
            }
            """
        )

        back_button.clicked.connect(
            self.back_requested.emit
        )

        open_button.clicked.connect(
            self.open_selected_record
        )

        remove_button.clicked.connect(
            self.remove_selected_record
        )

        buttons_layout.addWidget(back_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(remove_button)
        buttons_layout.addWidget(open_button)

        layout.addLayout(buttons_layout)

        self.refresh()

    def refresh(self):
        records = (
            self.project_store
            .get_labeled_records()
        )

        self.table.setRowCount(
            len(records)
        )

        for row, (
            record_id,
            class_id,
            updated_at,
        ) in enumerate(records):

            class_name = (
                f"{class_id} — "
                f"{self.CLASS_NAMES[class_id]}"
            )

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(record_id),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(class_name),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(updated_at),
            )

        self.count_label.setText(
            f"Всего размечено: {len(records)}"
        )

        self.table.resizeColumnsToContents()

    def get_selected_record_id(self):
        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return None

        return item.text()

    def open_selected_record(self):
        record_id = (
            self.get_selected_record_id()
        )

        if record_id is None:
            QMessageBox.information(
                self,
                "Запись не выбрана",
                "Сначала выберите запись.",
            )
            return

        self.open_record_requested.emit(
            record_id
        )

    def remove_selected_record(self):
        record_id = (
            self.get_selected_record_id()
        )

        if record_id is None:
            QMessageBox.information(
                self,
                "Запись не выбрана",
                "Сначала выберите запись.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Удалить разметку",
            f"Снять разметку с записи "
            f"'{record_id}'?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.project_store.remove_label(
            record_id
        )

        self.refresh()