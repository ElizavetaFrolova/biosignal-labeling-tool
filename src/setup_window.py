from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SetupWindow(QWidget):
    start_labeling = Signal(dict)

    def __init__(self):
        super().__init__()



        self.setStyleSheet(
            """
            QWidget {
                background-color: white;
                color: #222222;
                font-size: 14px;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                min-height: 34px;
                border: 1px solid #CCCCCC;
                border-radius: 7px;
                padding: 2px 8px;
                background-color: white;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #3B82F6;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 30, 35, 30)
        main_layout.setSpacing(20)

        title = QLabel("Настройка датасета")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 600;
            """
        )

        description = QLabel(
            "Выберите источник данных и параметры отображения сигнала"
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #777777;")

        main_layout.addWidget(title)
        main_layout.addWidget(description)

        # -------- Выбор датасета --------

        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Путь к датасету...")

        browse_button = QPushButton("Обзор")
        browse_button.setMinimumHeight(38)
        browse_button.setCursor(Qt.CursorShape.PointingHandCursor)

        browse_button.setStyleSheet(
            """
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                padding: 6px 14px;
            }

            QPushButton:hover {
                background-color: #E5E7EB;
            }
            """
        )

        browse_button.clicked.connect(self.select_dataset)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)

        main_layout.addLayout(path_layout)

        # -------- Настройки --------

        form = QFormLayout()
        form.setSpacing(15)

        self.format_combo = QComboBox()
        self.format_combo.addItems(
            [
                "Определить автоматически",
                "WFDB",
                "CSV",
                "NPY / NPZ",
                "EDF",
                "MAT",
            ]
        )

        self.channel_combo = QComboBox()
        self.channel_combo.addItem("Автоматически")

        self.fs_spin = QSpinBox()
        self.fs_spin.setRange(1, 10000)
        self.fs_spin.setValue(500)
        self.fs_spin.setSuffix(" Гц")

        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(0.1, 3600.0)
        self.window_spin.setValue(10.0)
        self.window_spin.setSuffix(" с")

        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(0.1, 3600.0)
        self.step_spin.setValue(10.0)
        self.step_spin.setSuffix(" с")

        form.addRow("Формат:", self.format_combo)
        form.addRow("Канал:", self.channel_combo)
        form.addRow("Частота дискретизации:", self.fs_spin)
        form.addRow("Длина окна:", self.window_spin)
        form.addRow("Шаг окна:", self.step_spin)

        main_layout.addLayout(form)

        main_layout.addStretch()

        # -------- Кнопка начала --------

        start_button = QPushButton("Начать разметку")
        start_button.setMinimumHeight(48)
        start_button.setCursor(Qt.CursorShape.PointingHandCursor)

        start_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 9px;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #2563EB;
            }

            QPushButton:pressed {
                background-color: #1D4ED8;
            }
            """
        )

        start_button.clicked.connect(self.start)

        main_layout.addWidget(start_button)

    def select_dataset(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с датасетом"
        )

        if directory:
            self.path_edit.setText(directory)

    def start(self):
        settings = {
            "path": self.path_edit.text(),
            "format": self.format_combo.currentText(),
            "channel": self.channel_combo.currentText(),
            "fs": self.fs_spin.value(),
            "window_seconds": self.window_spin.value(),
            "step_seconds": self.step_spin.value(),
        }

        self.start_labeling.emit(settings)