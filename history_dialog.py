# history_dialog.py
import json
import os
import re
from typing import Any
from hashlib import sha256
from PyQt5.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QPushButton, QHBoxLayout, QHeaderView,
    QInputDialog, QLineEdit, QMessageBox, QLabel, QComboBox
)

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

    __REGEX_DATA_OLD_VALUE = re.compile(r"(\d{4})-(\d\d)-(\d\d)")

    __HEADERS = ["ID", "Серийный номер", "Действие", "Поле", "Старое значение", "Новое значение", "Время"]

    def __init__(self, service, robot_id=None, parent=None):
        """
        :param service: экземпляр RobotService
        :param robot_id: ID конкретного робота (или None — показать всю историю)
        :param parent: родительский виджет
        """
        super().__init__(parent)
        self._service = service
        self._robot_id = robot_id
        self._password = self._load_password()
        self._row_count = 0
        self._column_count = 0

        self.setWindowTitle("История изменений")
        self.resize(1200, 500)

        self._setup_ui()
        self._load_history()

    # =================== Приватные методы ===================

    def _setup_ui(self):
        """Создание виджетов и компоновки."""
        # Таблица
        self._table = QTableWidget()

        # Кнопка очистки
        self._clear_button = QPushButton("🧹 Очистить историю")
        self._clear_button.clicked.connect(self._on_clear_clicked)

        # Компоновка кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self._clear_button)

        # 🔍 Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст...")
        self.search_field = QComboBox()
        self.search_field.addItems(["Все"] + self.__HEADERS)

        search_layout = QHBoxLayout()
        search_layout.addStretch()
        search_layout.addWidget(QLabel("Поле поиска:"))
        search_layout.addWidget(self.search_field)
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_input)

        # Подключение функции поиска к изменению текста поиска или к изменению поля поиска
        self.search_input.textChanged.connect(self._searching_on_history)
        self.search_field.currentIndexChanged.connect(self._searching_on_history)

        # Главная компоновка
        layout = QVBoxLayout()
        layout.addLayout(search_layout)
        layout.addWidget(self._table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_history(self):
        """Загрузка истории из сервиса и отображение в таблице."""
        history = self._service.get_history(self._robot_id)

        self._row_count = len(history)
        self._column_count = len(self.__HEADERS)

        self._table.setColumnCount(self._column_count)
        self._table.setHorizontalHeaderLabels(self.__HEADERS)
        self._table.setRowCount(self._row_count)

        for header_idx, header in enumerate(self.__HEADERS):
            self._table.setColumnWidth(header_idx, (15 * len(header)) + 70 * (2 < len(header) < 6))

        for row_idx, record in enumerate(history):
            for col_idx, key in enumerate(
                ["id", "robot_sn", "action", "field", "old_value", "new_value", "timestamp"]
            ):
                value = record.get(key, "")
                if key == "field":
                    value = FIELD_LABELS.get(value, value)
                elif key == "old_value" or key == "new_value":
                    value = self._format_data_value(value)
                elif key == "timestamp" and value:
                    value = self._format_timestamp(value)
                self._table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def _on_clear_clicked(self):
        """Обработка нажатия кнопки очистки истории."""
        if not self._verify_password():
            return None

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

        if not self._password:
            QMessageBox.critical(self, "Ошибка", "Пароль не задан в config.json")
            return False

        if sha256(password.encode()).hexdigest() != self._password:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            return False

        return True

    def _format_data_value(self, data:Any) -> str:
        """
        Форматирование времени к виду "%d.%m.%Y".
        Проверяет является ли поданный объект представлением времени в текстовом формате и виде "%Y-%m-%d" или
        объектом класса datetime. После чего преобразует объект к виду "%d.%m.%Y" и формату str. Так же пере-
        писывает поля со значением "None" на "Не известно"
        """
        if data is None or not data:
            return "Не известно"
        elif hasattr(data, "strftime"):
            return data.strftime("%d.%m.%Y")
        elif self.__REGEX_DATA_OLD_VALUE.fullmatch(data):
            return self.__REGEX_DATA_OLD_VALUE.sub(r'\3.\2.\1', data)
        else:
            return str(data)


    def _searching_on_history(self):
        """Поиск введенного текста по истории"""
        query = self.search_input.text().lower()
        index_col = self.search_field.currentIndex() - 1

        for row in range(self._row_count):
            hidden = False
            # 🔍 Поиск
            if query:
                if index_col == -1:
                    hidden = not any(query in self._table.item(row, col).text().lower() for col in range(self._column_count))
                else:
                    hidden = query not in self._table.item(row, index_col).text().lower()

            self._table.setRowHidden(row, hidden)

    # ============== Приватные статические методы ============

    @staticmethod
    def _format_timestamp(ts:Any) -> str:
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
    def _load_password():
        """Загружает пароль для удаления истории из config.json."""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)["history_clear_password"]
        except Exception:
            return None
    # =================== Публичные методы ===================

    def refresh(self):
        """Обновляет таблицу истории (публичный метод для вызова извне)."""
        self._load_history()
