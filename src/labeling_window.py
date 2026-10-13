import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt, Signal
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

    show_labeled_requested = Signal()

    def __init__(self, settings, project_store, loader,):
        super().__init__()

        self.settings = settings

        self.project_store = project_store

        self.loader = loader


        self.current_index = self.project_store.get_current_index()

        if self.current_index >= len(self.loader):
            self.current_index = 0



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

        self.previous_button = QPushButton(
            "← Назад"
        )

        labeled_button = QPushButton(
            "Размеченные записи"
        )

        self.skip_button = QPushButton(
            "Пропустить"
        )

        for button in [
            self.previous_button,
            labeled_button,
            self.skip_button,
        ]:
            button.setMinimumHeight(38)

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.setStyleSheet(
                self.secondary_button_style()
            )

        self.previous_button.clicked.connect(
            self.previous_record
        )

        labeled_button.clicked.connect(
            self.show_labeled_requested.emit
        )

        self.skip_button.clicked.connect(
            self.skip_record
        )

        navigation_layout.addWidget(
            self.previous_button
        )

        navigation_layout.addWidget(
            labeled_button
        )

        navigation_layout.addStretch()

        navigation_layout.addWidget(
            self.skip_button
        )

        main_layout.addLayout(
            navigation_layout
        )

        # ---------------- Переход по ID ----------------

        goto_layout = QHBoxLayout()

        goto_label = QLabel("Перейти к записи:")

        self.goto_edit = QLineEdit()
        self.goto_edit.setPlaceholderText("Введите ID записи")
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

    def show_current_record(self):

        self.project_store.set_current_index(
        self.current_index
        )

        record = self.loader.load(
            self.current_index
        )

        self.current_record = record

        self.record_label.setText(
            f"Запись: {record.record_id}"
        )

        self.progress_label.setText(
            f"{self.current_index + 1} / {len(self.loader)}"
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
        record = self.current_record

        self.project_store.assign_label(
            record.record_id,
            record.signal,
            class_id,
        )

        self.next_record()

    def skip_record(self):
        record = self.current_record

        self.project_store.mark_skipped(
            record.record_id
        )

        self.next_record()

    def next_record(self):
        if self.current_index < len(self.loader) - 1:
            self.current_index += 1

            self.project_store.set_current_index(
                self.current_index
            )

            self.show_current_record()
        else:
            QMessageBox.information(
                self,
                "Конец",
                "Вы дошли до последней записи.",
            )

    def previous_record(self):
        if self.current_index > 0:
            self.current_index -= 1

            self.project_store.set_current_index(
                self.current_index
            )

            self.show_current_record()

    def go_to_record(self):
        record_id = (
            self.goto_edit.text().strip()
        )

        index = self.loader.find_index(
            record_id
        )

        if index is None:
            QMessageBox.warning(
                self,
                "Запись не найдена",
                f"Запись с ID "
                f"'{record_id}' не найдена.",
            )
            return

        self.current_index = index

        self.project_store.set_current_index(
            index
        )

        self.show_current_record()
        self.goto_edit.clear()

    def update_class_label(self):
        record = self.current_record

        class_names = {
            0: "0 — Чистый",
            1: "1 — Небольшой шум",
            2: "2 — Сильный шум",
            3: "3 — Нечитаемый",
        }

        class_id = self.project_store.get_label(
            record.record_id
        )

        status = self.project_store.get_status(
            record.record_id
        )

        if class_id is not None:
            text = (
                "Текущий класс: "
                f"{class_names[class_id]}"
            )

        elif status == "skipped":
            text = "Текущий статус: пропущен"

        else:
            text = "Текущий класс: не размечен"

        progress = self.project_store.get_progress()

        text += (
            f"    |    Размечено: "
            f"{progress['labeled']}"
            f"    Пропущено: "
            f"{progress['skipped']}"
        )

        self.current_class_label.setText(
            text
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



    def open_record(self, record_id):
        index = self.loader.find_index(
            record_id
        )

        if index is None:
            QMessageBox.warning(
                self,
                "Запись не найдена",
                f"Запись '{record_id}' "
                "не найдена в исходном датасете.",
            )
            return

        self.current_index = index

        self.project_store.set_current_index(
            index
        )

        self.show_current_record()