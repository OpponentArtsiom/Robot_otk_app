from PyQt5.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QPushButton, QHBoxLayout, QHeaderView
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


class HistoryDialog(QDialog):
    def __init__(self, robot_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История изменений")
        self.resize(1000, 500)

        self.robot_id = robot_id

        # таблица
        self.table = QTableWidget()
        # 🔑 растягиваем колонки на всю ширину окна
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
            for col_idx, key in enumerate(["id", "robot_sn", "action", "field", "old_value", "new_value", "timestamp"]):
                value = row.get(key, "")
                if key == "field":
                    value = FIELD_LABELS.get(value, value)
                elif key == "timestamp" and value:
                    # форматируем datetime → строка "YYYY-MM-DD HH:MM"
                    try:
                        value = value.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))


        # 🔑 если хочешь именно под содержимое, а не растягивание — раскомментируй:
        #self.table.resizeColumnsToContents()

    def handle_clear(self):
        clear_history()
        self.load_history()
