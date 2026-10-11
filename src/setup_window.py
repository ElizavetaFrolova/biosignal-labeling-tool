from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pathlib import Path

import wfdb


class SetupWindow(QWidget):
    create_project = Signal(dict)
    back_requested = Signal()

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

        main_layout.setContentsMargins(
            40,
            25,
            40,
            30,
        )

        main_layout.setSpacing(17)

        title = QLabel(
            "Новый проект разметки"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 600;
            """
        )

        main_layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(13)

        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText(
            "Например: ptbxl_quality"
        )

        # Папка, где создадим проект.
        project_path_layout = QHBoxLayout()

        self.project_parent_edit = QLineEdit()
        self.project_parent_edit.setPlaceholderText(
            "Куда сохранить проект..."
        )

        project_browse = QPushButton(
            "Обзор"
        )

        project_browse.clicked.connect(
            self.select_project_parent
        )

        project_path_layout.addWidget(
            self.project_parent_edit
        )

        project_path_layout.addWidget(
            project_browse
        )

        # Исходный датасет.
        dataset_layout = QHBoxLayout()

        self.dataset_edit = QLineEdit()
        self.dataset_edit.setPlaceholderText(
            "Путь к исходным данным..."
        )

        self.dataset_edit.editingFinished.connect(
            self.inspect_dataset
        )

        dataset_folder_button = QPushButton(
            "Папка"
        )

        dataset_file_button = QPushButton(
            "Файл"
        )

        dataset_folder_button.clicked.connect(
            self.select_dataset_folder
        )

        dataset_file_button.clicked.connect(
            self.select_dataset_file
        )

        dataset_layout.addWidget(
            self.dataset_edit
        )

        dataset_layout.addWidget(
            dataset_folder_button
        )

        dataset_layout.addWidget(
            dataset_file_button
        )

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
        self.channel_combo.addItem(
            "Автоматически"
        )

        self.fs_spin = QSpinBox()
        self.fs_spin.setRange(
            1,
            10000,
        )

        self.fs_spin.setValue(500)
        self.fs_spin.setSuffix(" Гц")

        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(
            0.1,
            3600,
        )

        self.window_spin.setValue(10)
        self.window_spin.setSuffix(" с")

        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(
            0.1,
            3600,
        )

        self.step_spin.setValue(10)
        self.step_spin.setSuffix(" с")

        form.addRow(
            "Название проекта:",
            self.project_name_edit,
        )

        form.addRow(
            "Папка проекта:",
            project_path_layout,
        )

        form.addRow(
            "Исходные данные:",
            dataset_layout,
        )

        form.addRow(
            "Формат:",
            self.format_combo,
        )

        form.addRow(
            "Канал:",
            self.channel_combo,
        )

        form.addRow(
            "Частота:",
            self.fs_spin,
        )

        form.addRow(
            "Длина окна:",
            self.window_spin,
        )

        form.addRow(
            "Шаг окна:",
            self.step_spin,
        )

        main_layout.addLayout(form)
        main_layout.addStretch()

        navigation = QHBoxLayout()

        back_button = QPushButton(
            "← Назад"
        )

        create_button = QPushButton(
            "Создать проект"
        )

        create_button.setMinimumHeight(45)

        create_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 20px;
            }

            QPushButton:hover {
                background-color: #2563EB;
            }
            """
        )

        back_button.clicked.connect(
            self.back_requested.emit
        )

        create_button.clicked.connect(
            self.create
        )

        navigation.addWidget(back_button)
        navigation.addStretch()
        navigation.addWidget(create_button)

        main_layout.addLayout(navigation)

    def select_project_parent(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Куда сохранить проект",
        )

        if directory:
            self.project_parent_edit.setText(
                directory
            )

    def select_dataset_folder(self):
        directory = (
            QFileDialog.getExistingDirectory(
                self,
                "Выберите папку с данными",
            )
        )

        if directory:
            self.dataset_edit.setText(
                directory
            )

            self.inspect_dataset()

    def select_dataset_file(self):
        file_name, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Выберите файл",
            )
        )

        if file_name:
            self.dataset_edit.setText(
                file_name
            )

            self.inspect_dataset()

    def create(self):
        project_name = (
            self.project_name_edit
            .text()
            .strip()
        )

        project_parent = (
            self.project_parent_edit
            .text()
            .strip()
        )

        dataset_path = (
            self.dataset_edit
            .text()
            .strip()
        )

        if not project_name:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Введите название проекта.",
            )
            return

        if not project_parent:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите папку для проекта.",
            )
            return

        if not dataset_path:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите исходные данные.",
            )
            return

        settings = {
            "project_name": project_name,
            "project_parent": project_parent,
            "dataset_path": dataset_path,
            "format": self.format_combo.currentText(),
            "channel": self.channel_combo.currentText(),
            "fs": self.fs_spin.value(),
            "window_seconds": self.window_spin.value(),
            "step_seconds": self.step_spin.value(),
        }

        self.create_project.emit(
            settings
        )


    def inspect_dataset(self):
        dataset_path = self.dataset_edit.text().strip()

        if not dataset_path:
            return

        path = Path(dataset_path)

        header_file = None

        if path.is_dir():
            header_file = next(
                path.rglob("*.hea"),
                None,
            )

        elif path.suffix.lower() == ".hea":
            header_file = path

        if header_file is None:
            return

        try:
            record_path = header_file.with_suffix("")

            header = wfdb.rdheader(
                str(record_path)
            )

        except Exception:
            return

        self.format_combo.blockSignals(True)
        self.format_combo.setCurrentText("WFDB")
        self.format_combo.blockSignals(False)

        self.fs_spin.setValue(
            int(round(header.fs))
        )

        self.channel_combo.clear()

        self.channel_combo.addItems(
            header.sig_name
        )

        if "II" in header.sig_name:
            self.channel_combo.setCurrentText("II")

    