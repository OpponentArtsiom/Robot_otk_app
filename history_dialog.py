# history_dialog.py
import json
import os
from time import strftime

from PyQt5.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QPushButton, QHBoxLayout, QHeaderView,
    QInputDialog, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt

FIELD_LABELS = {
    "model": "Модель",
    "robot_sn": "Серийный номер робота",
    "controller_sn": "Серийный номер контроллера",
    "arrival_date": "Дата поступления",
    "status": "Статус",
    "fault_description": "Описание неисправности",
    "fault_reason": "Причина неисправности",
    "tasks_done": "Выполненные задачи",
    "tasks_required": "Требуемые задачи",
    "required_parts": "Необходимые детали",
    "notes": "Заметки"
}


class HistoryDialog(QDialog):
    """Диалог для просмотра и очистки истории изменений роботов."""

    def __init__(self, service, robot_id=None, parent=None):
        """
        :param service: экземпляр RobotService
        :param robot_id: ID конкретного робота (или None — показать всю историю)
        :param parent: родительский виджет
        """
        super().__init__(parent)
        self._service = service
        self._robot_id = robot_id
        self._config = self._load_config()

        self.setWindowTitle("История изменений")
        self.resize(1000, 500)

        self._setup_ui()
        self._load_history()

    # =================== Приватные методы ===================

    def _load_config(self):
        """Загружает конфигурацию из config.json."""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _setup_ui(self):
        """Создание виджетов и компоновки."""
        # Таблица
        self._table = QTableWidget()
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Кнопка очистки
        self._clear_button = QPushButton("🧹 Очистить историю")
        self._clear_button.clicked.connect(self._on_clear_clicked)

        # Компоновка кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self._clear_button)

        # Главная компоновка
        layout = QVBoxLayout()
        layout.addWidget(self._table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_history(self):
        """Загрузка истории из сервиса и отображение в таблице."""
        history = self._service.get_history(self._robot_id)
        headers = ["ID", "Серийный номер", "Действие", "Поле",
                   "Старое значение", "Новое значение", "Время"]

        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(history))

        for row_idx, record in enumerate(history):
            for col_idx, key in enumerate(
                ["id", "robot_sn", "action", "field", "old_value", "new_value", "timestamp"]
            ):
                value = record.get(key, "")
                if key == "field":
                    value = FIELD_LABELS.get(value, value)
                # elif key == "old_value":
                #     value = self._format_old_data_value(value)
                elif key == "timestamp" and value:
                    value = self._format_timestamp(value)
                self._table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def _on_clear_clicked(self):
        """Обработка нажатия кнопки очистки истории."""
        if not self._verify_password():
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите очистить всю историю?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._service.clear_history()
            self._load_history()
            QMessageBox.information(self, "История", "🧹 История успешно очищена.")

    def _verify_password(self):
        """Запрос пароля и проверка соответствия конфигурации."""
        password, ok = QInputDialog.getText(
            self, "Пароль", "Введите пароль для очистки истории:",
            QLineEdit.Password
        )
        if not ok:
            return False

        expected = self._config.get("history_clear_password")
        if not expected:
            QMessageBox.critical(self, "Ошибка", "Пароль не задан в config.json")
            return False

        if password != expected:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            return False

        return True

    # ============== Приватные статические методы ============

    @staticmethod
    def _format_timestamp(ts):
        """
        Форматирование времени изменения поля БД в строку.
        Проверяет объект на наличие метода "strftime" класса datetime. При его
        наличии форматирует объект к виду "%d.%m.%Y %H:%M". Иначе выводит строковой представление объекта
        """
        if hasattr(ts, "strftime"):
            return ts.strftime("%d.%m.%Y %H:%M")
        else:
            return str(ts)

    @staticmethod
    def _format_old_data_value(old_data):
        """
        Форматирование времени к виду "%d.%m.%Y".
        Проверяет является ли поданный объект представлением времени в текстовом формате и виде "%Y-%m-%d" или
        объектом класса datetime. После чего преобразует объект к виду "%d.%m.%Y" и формату str
        """
        if hasattr(old_data, "strftime"):
            return old_data.strftime("%d.%m.%Y %H:%M")


    # =================== Публичные методы ===================

    def refresh(self):
        """Обновляет таблицу истории (публичный метод для вызова извне)."""
        self._load_history()
