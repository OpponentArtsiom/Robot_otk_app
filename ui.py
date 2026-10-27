# ui.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QPushButton, QCheckBox, QComboBox, QMenu, QAction
)
from PyQt5.QtCore import Qt
from robot_logic import RobotLogic


class RobotTable(QWidget):
    def __init__(self, service=None):
        """
        service — экземпляр RobotService (из services.py), который передаётся из main.py
        """
        super().__init__()
        self.setWindowTitle("Учёт роботов ОТК")
        self.resize(1000, 400)

        # 📊 Таблица
        self.table = TableWithCustomMenu()

        # Логика пока None, чтобы задать позже через set_logic
        self.logic = None

        # 🔍 Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст...")
        self.search_field = QComboBox()

        # ☑️ Чекбокс скрытия отгруженных
        self.hide_shipped_checkbox = QCheckBox("Скрыть отгруженные")
        self.hide_shipped_checkbox.setChecked(False)
        self.hide_not_shipped_checkbox = QCheckBox("Скрыть неотгруженные")
        self.hide_not_shipped_checkbox.setChecked(False)

        search_layout = QHBoxLayout()
        search_layout.addStretch()
        search_layout.addWidget(QLabel("Поле поиска:"))
        search_layout.addWidget(self.search_field)
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.hide_shipped_checkbox)
        search_layout.addWidget(self.hide_not_shipped_checkbox)

        # 🔘 Кнопки
        self.add_button = QPushButton("➕ Добавить робота")
        self.edit_button = QPushButton("✏️ Изменить робота")
        self.delete_button = QPushButton("🗑️ Удалить робота")
        self.save_button = QPushButton("💾 Сохранить изменения")
        self.export_button = QPushButton("📄 Экспорт в Excel")
        self.history_button = QPushButton("📜 История")


        # Кнопки в одну линию
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.history_button)


        # 📐 Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Если сервис передан — создаём сразу логику
        if service:
            self.set_logic(RobotLogic(self, service))

    def set_logic(self, logic):
        self.logic = logic

        self.search_input.textChanged.connect(self.logic.apply_filters)
        self.hide_shipped_checkbox.stateChanged.connect(self.logic.check_hidden_shipped_checkbox_state)
        self.hide_not_shipped_checkbox.stateChanged.connect(self.logic.check_hidden_not_shipped_checkbox_state)
        self.search_field.currentIndexChanged.connect(self.logic.apply_filters)

        self.add_button.clicked.connect(self.logic.add_robot)
        self.edit_button.clicked.connect(self.logic.edit_robot)
        self.delete_button.clicked.connect(self.logic.delete_robot)
        self.save_button.clicked.connect(self.logic.save_changes)
        self.export_button.clicked.connect(self.logic.export_to_excel)
        self.history_button.clicked.connect(self.logic.show_history)

        self.logic.load_data()

        self.table.logic = self.logic.edit_robot_status_context_menu

        self.search_field.addItems(["Все"] + self.logic.headers)


class TableWithCustomMenu(QTableWidget):

    def __init__(self):
        super().__init__()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # Контекстное меню для изменения статуса робота
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.logic = None

    def show_context_menu(self, pos):
        # Контекстное меню
        menu = QMenu(self)
        item = self.itemAt(pos)
        fields = ["Необходим ремонт", "Тестируется", "Протестирован", "Откалиброван", "Упакован", "Отгружен", "Простаивает"]

        # Добавляем действия
        for field in sorted(fields, key=lambda text: text == item.text(), reverse=True):
            if field == item.text():
                field = '✔ ' + field
                menu.addAction(QAction(field, self))
            else:
                menu.addAction(QAction(field, self))

        # Показываем меню в глобальных координатах
        # pos — это координаты внутри таблицы, mapToGlobal переводит их в координаты экрана
        chosen = menu.exec_(self.mapToGlobal(pos))
        if chosen and self.logic:
            self.logic(item.row(), chosen.text())