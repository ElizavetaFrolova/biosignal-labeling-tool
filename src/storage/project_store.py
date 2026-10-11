import csv
import json
import re
import sqlite3
from pathlib import Path

import numpy as np


class ProjectStore:
    DATABASE_NAME = "project.db"

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.db_path = self.project_dir / self.DATABASE_NAME

        self.connection = sqlite3.connect(self.db_path)

        self._create_tables()

    @classmethod
    def create(cls, parent_dir, project_name, settings):
        project_dir = Path(parent_dir) / project_name

        if project_dir.exists():
            raise FileExistsError(
                f"Проект '{project_name}' уже существует."
            )

        project_dir.mkdir(parents=True)

        labeled_dir = project_dir / "labeled"

        for class_id in range(4):
            (labeled_dir / f"class_{class_id}").mkdir(
                parents=True
            )

        store = cls(project_dir)

        store.save_settings(settings)
        store.set_current_index(0)

        return store

    @classmethod
    def open(cls, project_dir):
        project_dir = Path(project_dir)
        db_path = project_dir / cls.DATABASE_NAME

        if not db_path.exists():
            raise FileNotFoundError(
                "В выбранной папке нет project.db"
            )

        return cls(project_dir)

    def _create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS labels (
                record_id TEXT PRIMARY KEY,
                class_id INTEGER,
                status TEXT NOT NULL,
                file_name TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.connection.commit()

    def save_settings(self, settings):
        cursor = self.connection.cursor()

        for key, value in settings.items():
            cursor.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key)
                DO UPDATE SET value = excluded.value
                """,
                (
                    key,
                    json.dumps(
                        value,
                        ensure_ascii=False,
                    ),
                ),
            )

        self.connection.commit()

    def get_settings(self):
        cursor = self.connection.cursor()

        rows = cursor.execute(
            "SELECT key, value FROM settings"
        ).fetchall()

        settings = {}

        for key, value in rows:
            settings[key] = json.loads(value)

        return settings

    def set_current_index(self, index):
        self.save_settings(
            {
                "current_index": index,
            }
        )

    def get_current_index(self):
        settings = self.get_settings()

        return int(
            settings.get(
                "current_index",
                0,
            )
        )

    def assign_label(
        self,
        record_id,
        signal,
        class_id,
    ):
        cursor = self.connection.cursor()

        old_row = cursor.execute(
            """
            SELECT class_id, file_name
            FROM labels
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()

        # Если запись раньше лежала в другом классе,
        # удаляем старую копию.
        if old_row is not None:
            _, old_file_name = old_row

            if old_file_name:
                old_file = (
                    self.project_dir
                    / old_file_name
                )

                if old_file.exists():
                    old_file.unlink()

        safe_name = self._safe_file_name(
            record_id
        )

        relative_path = (
            Path("labeled")
            / f"class_{class_id}"
            / f"{safe_name}.npy"
        )

        output_path = (
            self.project_dir
            / relative_path
        )

        # Сохраняем как 1 x N.
        signal_array = np.asarray(
            signal
        ).reshape(1, -1)

        np.save(
            output_path,
            signal_array,
        )

        cursor.execute(
            """
            INSERT INTO labels (
                record_id,
                class_id,
                status,
                file_name,
                updated_at
            )
            VALUES (?, ?, 'labeled', ?, CURRENT_TIMESTAMP)

            ON CONFLICT(record_id)
            DO UPDATE SET
                class_id = excluded.class_id,
                status = 'labeled',
                file_name = excluded.file_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                record_id,
                class_id,
                str(relative_path),
            ),
        )

        self.connection.commit()

        self._write_labels_csv()

    def mark_skipped(self, record_id):
        cursor = self.connection.cursor()

        row = cursor.execute(
            """
            SELECT status
            FROM labels
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()

        # Если сигнал уже размечен, "Пропустить"
        # его метку не уничтожает.
        if row is not None and row[0] == "labeled":
            return

        cursor.execute(
            """
            INSERT INTO labels (
                record_id,
                class_id,
                status,
                file_name,
                updated_at
            )
            VALUES (?, NULL, 'skipped', NULL, CURRENT_TIMESTAMP)

            ON CONFLICT(record_id)
            DO UPDATE SET
                class_id = NULL,
                status = 'skipped',
                file_name = NULL,
                updated_at = CURRENT_TIMESTAMP
            """,
            (record_id,),
        )

        self.connection.commit()

    def get_label(self, record_id):
        row = self.connection.execute(
            """
            SELECT class_id
            FROM labels
            WHERE record_id = ?
              AND status = 'labeled'
            """,
            (record_id,),
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def get_status(self, record_id):
        row = self.connection.execute(
            """
            SELECT status
            FROM labels
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()

        if row is None:
            return "unlabeled"

        return row[0]

    def remove_label(self, record_id):
        cursor = self.connection.cursor()

        row = cursor.execute(
            """
            SELECT file_name
            FROM labels
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()

        if row is not None and row[0]:
            file_path = (
                self.project_dir
                / row[0]
            )

            if file_path.exists():
                file_path.unlink()

        cursor.execute(
            """
            DELETE FROM labels
            WHERE record_id = ?
            """,
            (record_id,),
        )

        self.connection.commit()

        self._write_labels_csv()

    def get_progress(self):
        cursor = self.connection.cursor()

        labeled = cursor.execute(
            """
            SELECT COUNT(*)
            FROM labels
            WHERE status = 'labeled'
            """
        ).fetchone()[0]

        skipped = cursor.execute(
            """
            SELECT COUNT(*)
            FROM labels
            WHERE status = 'skipped'
            """
        ).fetchone()[0]

        return {
            "labeled": labeled,
            "skipped": skipped,
        }

    def _write_labels_csv(self):
        rows = self.connection.execute(
            """
            SELECT record_id, class_id, file_name
            FROM labels
            WHERE status = 'labeled'
            ORDER BY record_id
            """
        ).fetchall()

        csv_path = (
            self.project_dir
            / "labels.csv"
        )

        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    "record_id",
                    "class_id",
                    "file",
                ]
            )

            writer.writerows(rows)

    @staticmethod
    def _safe_file_name(record_id):
        return re.sub(
            r"[^a-zA-Z0-9_.-]",
            "_",
            record_id,
        )

    def close(self):
        self.connection.close()