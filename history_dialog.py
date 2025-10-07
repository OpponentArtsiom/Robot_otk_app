import json
import os
from PyQt5.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QPushButton, QHBoxLayout, QHeaderView,
    QInputDialog, QLineEdit, QMessageBox
)
from db import get_history, clear_history

FIELD_LABELS = {
    "model": "Модель",
    "robot_sn": "Серийный номер робота",
    "controller_sn": "Серийный номер контроллера",
    "status": "Статус",
    "fault_description": "Описание неисправности",
    "fault_reason": "Причина неисправности",
    "tasks_done": "Выполненные задачи",
    "tasks_required": "Требуемые задачи",
    "required_parts": "Необходимые детали",
    "notes": "Заметки"
}


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


class HistoryDialog(QDialog):
    def __init__(self, robot_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История изменений")
        self.resize(1000, 500)

        self.robot_id = robot_id
        self.config = load_config()

        # таблица
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # кнопка очистки
        self.clear_button = QPushButton("🧹 Очистить историю")
        self.clear_button.clicked.connect(self.handle_clear)

        # компоновка
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.load_history()

    def load_history(self):
        history = get_history(self.robot_id)
        headers = ["ID", "Серийный номер", "Действие", "Поле",
                   "Старое значение", "Новое значение", "Время"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(history))

        for row_idx, row in enumerate(history):
            for col_idx, key in enumerate(
                ["id", "robot_sn", "action", "field", "old_value", "new_value", "timestamp"]
            ):
                value = row.get(key, "")
                if key == "field":
                    value = FIELD_LABELS.get(value, value)
                elif key == "timestamp" and value:
                    try:
                        value = value.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def handle_clear(self):
        # Запрашиваем пароль
        password, ok = QInputDialog.getText(
            self, "Пароль", "Введите пароль для очистки истории:",
            QLineEdit.Password
        )
        if not ok:
            return

        expected = self.config.get("history_clear_password")
        if not expected:
            QMessageBox.critical(self, "Ошибка", "Пароль не задан в config.json")
            return

        if password != expected:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            return

        # Если пароль верный — подтверждаем
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите очистить всю историю?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            clear_history()
            self.load_history()
            QMessageBox.information(self, "История", "🧹 История успешно очищена.")
