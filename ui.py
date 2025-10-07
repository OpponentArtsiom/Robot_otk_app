from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget,
    QPushButton
)

from robot_logic import RobotLogic


class RobotTable(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учёт роботов ОТК")
        self.resize(1000, 400)

        # 📊 Таблица
        self.table = QTableWidget()

        # Инициализация логики
        self.logic = RobotLogic(self)

        # 🔍 Поиск
        self.search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст...")
        self.search_input.textChanged.connect(self.logic.filter_table)

        search_layout = QHBoxLayout()
        search_layout.addStretch()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)

        # 🔘 Кнопки
        self.add_button = QPushButton("➕ Добавить робота")
        self.edit_button = QPushButton("✏️ Изменить робота")
        self.delete_button = QPushButton("🗑️ Удалить робота")
        self.save_button = QPushButton("💾 Сохранить изменения")
        self.export_button = QPushButton("📄 Экспорт в Excel")
        self.history_button = QPushButton("📜 История")  # новая кнопка

        # 🔗 Связи
        self.add_button.clicked.connect(self.logic.add_robot)
        self.edit_button.clicked.connect(self.logic.edit_robot)
        self.delete_button.clicked.connect(self.logic.delete_robot)
        self.save_button.clicked.connect(self.logic.save_changes)
        self.export_button.clicked.connect(self.logic.export_to_excel)
        self.history_button.clicked.connect(self.logic.show_history)  # открывает историю

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

        # ⏬ Загрузка данных
        self.logic.load_data()
