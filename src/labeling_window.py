import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.signal_record import SignalRecord


class LabelingWindow(QWidget):
    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        # Пока тестовые записи.
        # Потом вместо этого здесь будет настоящий Loader.
        self.records = self.create_test_records()

        self.current_index = 0

        # Здесь пока только временно храним разметку в памяти.
        # Например:
        # "test_0001": 2
        self.labels = {}

        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
          
        main_layout.setContentsMargins(30, 22, 30, 25)
        main_layout.setSpacing(14)

        # ---------------- Заголовок ----------------

        title_label = QLabel("Оценка качества биосигнала")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: 600;
                color: #222222;
            }
            """
        )

        main_layout.addWidget(title_label)

        # ---------------- Информация о записи ----------------

        info_layout = QHBoxLayout()

        self.record_label = QLabel()
        self.record_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: 600;
                color: #333333;
            }
            """
        )

        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.progress_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #777777;
            }
            """
        )

        info_layout.addWidget(self.record_label)
        info_layout.addStretch()
        info_layout.addWidget(self.progress_label)

        main_layout.addLayout(info_layout)

        self.details_label = QLabel()
        self.details_label.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                color: #777777;
            }
            """
        )

        main_layout.addWidget(self.details_label)

        self.current_class_label = QLabel()
        self.current_class_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #555555;
            }
            """
        )

        main_layout.addWidget(self.current_class_label)

        # ---------------- График ----------------

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("white")

        self.plot_widget.setMinimumHeight(220)
        self.plot_widget.setMaximumHeight(250)

        self.plot_widget.setLabel(
            "bottom",
            "Время",
            units="с",
        )

        self.plot_widget.setLabel(
            "left",
            "Амплитуда",
        )

        self.plot_widget.showGrid(
            x=True,
            y=True,
            alpha=0.15,
        )

        self.plot_widget.setMouseEnabled(
            x=False,
            y=False,
        )

        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setCursor(Qt.CursorShape.ArrowCursor)

        main_layout.addWidget(self.plot_widget)

        # ---------------- Кнопки классов ----------------

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.class_buttons = []

        class_data = [
            ("0\nЧистый", "#E8F5E9", "#2E7D32"),
            ("1\nНебольшой шум", "#FFF8E1", "#B7791F"),
            ("2\nСильный шум", "#FFF0E6", "#D76A03"),
            ("3\nНечитаемый", "#FDECEC", "#C62828"),
        ]

        for class_id, (text, background, text_color) in enumerate(class_data):
            button = QPushButton(text)

            button.setMinimumHeight(70)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.setStyleSheet(
                self.button_style(
                    background,
                    text_color,
                )
            )

            button.clicked.connect(
                lambda checked=False, value=class_id: self.assign_class(value)
            )

            self.class_buttons.append(button)
            buttons_layout.addWidget(button)

        main_layout.addLayout(buttons_layout)

        # ---------------- Навигация ----------------

        navigation_layout = QHBoxLayout()

        self.previous_button = QPushButton("← Назад")
        self.skip_button = QPushButton("Пропустить")

        for button in [
            self.previous_button,
            self.skip_button,
        ]:
            button.setMinimumHeight(38)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(self.secondary_button_style())

        self.previous_button.clicked.connect(self.previous_record)
        self.skip_button.clicked.connect(self.skip_record)

        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addStretch()
        navigation_layout.addWidget(self.skip_button)

        main_layout.addLayout(navigation_layout)

        # ---------------- Переход по ID ----------------

        goto_layout = QHBoxLayout()

        goto_label = QLabel("Перейти к записи:")

        self.goto_edit = QLineEdit()
        self.goto_edit.setPlaceholderText("Например: test_0003")
        self.goto_edit.setMinimumHeight(36)

        self.goto_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 7px;
                padding: 4px 9px;
            }

            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            """
        )

        goto_button = QPushButton("Перейти")
        goto_button.setMinimumHeight(36)
        goto_button.setCursor(Qt.CursorShape.PointingHandCursor)
        goto_button.setStyleSheet(self.secondary_button_style())

        goto_button.clicked.connect(self.go_to_record)
        self.goto_edit.returnPressed.connect(self.go_to_record)

        goto_layout.addWidget(goto_label)
        goto_layout.addWidget(self.goto_edit)
        goto_layout.addWidget(goto_button)

        main_layout.addLayout(goto_layout)

        self.show_current_record()

    def create_test_records(self):
        fs = self.settings["fs"]
        duration = self.settings["window_seconds"]

        time = np.arange(
            int(fs * duration)
        ) / fs

        records = []

        for index in range(10):
            frequency = 1.0 + index * 0.1

            signal = np.sin(
                2 * np.pi * frequency * time
            )

            record = SignalRecord(
                record_id=f"test_{index + 1:04d}",
                signal=signal,
                fs=fs,
                channel_name="test",
            )

            records.append(record)

        return records

    def show_current_record(self):
        record = self.records[self.current_index]

        self.record_label.setText(
            f"Запись: {record.record_id}"
        )

        self.progress_label.setText(
            f"{self.current_index + 1} / {len(self.records)}"
        )

        duration = len(record.signal) / record.fs

        self.details_label.setText(
            f"Канал: {record.channel_name}   "
            f"Частота: {record.fs:g} Гц   "
            f"Длительность: {duration:g} с"
        )

        self.update_class_label()

        time = np.arange(
            len(record.signal)
        ) / record.fs

        self.plot_widget.clear()

        pen = pg.mkPen(
            color="#3B82F6",
            width=2,
        )

        self.plot_widget.plot(
            time,
            record.signal,
            pen=pen,
        )

        self.previous_button.setEnabled(
            self.current_index > 0
        )

    def assign_class(self, class_id):
        record = self.records[self.current_index]

        # Если запись уже была размечена,
        # значение просто заменится.
        self.labels[record.record_id] = class_id

        self.next_record()

    def skip_record(self):
        self.next_record()

    def next_record(self):
        if self.current_index < len(self.records) - 1:
            self.current_index += 1
            self.show_current_record()
        else:
            QMessageBox.information(
                self,
                "Конец",
                "Вы дошли до последней записи.",
            )

            self.update_class_label()

    def previous_record(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_record()

    def go_to_record(self):
        record_id = self.goto_edit.text().strip()

        for index, record in enumerate(self.records):
            if record.record_id == record_id:
                self.current_index = index
                self.show_current_record()
                self.goto_edit.clear()
                return

        QMessageBox.warning(
            self,
            "Запись не найдена",
            f"Запись с ID '{record_id}' не найдена.",
        )

    def update_class_label(self):
        record = self.records[self.current_index]

        class_names = {
            0: "0 — Чистый",
            1: "1 — Небольшой шум",
            2: "2 — Сильный шум",
            3: "3 — Нечитаемый",
        }

        if record.record_id in self.labels:
            class_id = self.labels[record.record_id]

            self.current_class_label.setText(
                f"Текущий класс: {class_names[class_id]}"
            )
        else:
            self.current_class_label.setText(
                "Текущий класс: не размечен"
            )

    @staticmethod
    def button_style(background, text_color):
        return f"""
            QPushButton {{
                background-color: {background};
                color: {text_color};

                border: 1px solid {text_color};
                border-radius: 10px;

                font-size: 14px;
                font-weight: 600;

                padding: 8px;
            }}

            QPushButton:hover {{
                border-width: 2px;
            }}

            QPushButton:pressed {{
                background-color: #EEEEEE;
            }}
        """

    @staticmethod
    def secondary_button_style():
        return """
            QPushButton {
                background-color: #F3F4F6;
                color: #333333;

                border: 1px solid #D1D5DB;
                border-radius: 7px;

                padding: 5px 14px;
            }

            QPushButton:hover {
                background-color: #E5E7EB;
            }

            QPushButton:disabled {
                color: #AAAAAA;
                background-color: #F8F8F8;
            }
        """