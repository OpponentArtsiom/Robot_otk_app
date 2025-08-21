from PyQt5.QtWidgets import (
    QWidget, QComboBox, QTableWidget, QVBoxLayout, QPushButton,
    QPlainTextEdit, QMessageBox, QHBoxLayout, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextOption, QPalette, QColor
from db import get_all_robots, update_robot, add_robot, delete_robot
from openpyxl import Workbook

# 🔧 Кастомный ComboBox, отключающий прокрутку мыши
class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

# 🧩 Основной класс интерфейса
class RobotTable(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учёт роботов ОТК")
        self.resize(1000, 400)

        # 🏷️ Заголовки таблицы и поля БД
        self.headers = [
            "Модель", "Серийный № робота", "Серийный № контроллера",
            "Текущий статус", "Описание неисправности",
            "Проблемный узел/модуль", "Причина поломки", "Проведенные работы",
            "Планируемые работы", "Необходимые запчасти"
        ]
        self.db_fields = [
            "model", "robot_sn", "controller_sn",
            "status", "fault_description",
            "fault_module", "fault_reason", "tasks_done",
            "tasks_required", "required_parts"
        ]
        self.field_map = {i: field for i, field in enumerate(self.db_fields)}

        # 🔍 Поле поиска
        self.search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст...")
        self.search_input.textChanged.connect(self.filter_table)

        search_layout = QHBoxLayout()
        search_layout.addStretch()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)

        # 📊 Таблица
        self.table = QTableWidget()

        # 🔘 Кнопки
        self.add_button = QPushButton("➕ Добавить робота")
        self.delete_button = QPushButton("🗑️ Удалить робота")
        self.save_button = QPushButton("💾 Сохранить изменения")
        self.export_button = QPushButton("📄 Экспорт в Excel")
        self.refresh_button = QPushButton("🔄 Обновить таблицу")

        # 🔗 Привязка кнопок
        self.add_button.clicked.connect(self.add_robot)
        self.delete_button.clicked.connect(self.delete_robot)
        self.save_button.clicked.connect(self.save_changes)
        self.export_button.clicked.connect(self.export_to_excel)
        self.refresh_button.clicked.connect(self.load_data)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.refresh_button)

        # 📐 Основной layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.load_data()

    # 🔍 Фильтрация таблицы по тексту
    def filter_table(self):
        query = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                widget = self.table.cellWidget(row, col)
                if isinstance(widget, QComboBox):
                    text = widget.currentText().lower()
                elif isinstance(widget, QPlainTextEdit):
                    text = widget.toPlainText().lower()
                else:
                    continue
                if query in text:
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def create_model_cell(self, value):
        combo = NoScrollComboBox()
        combo.addItems(["RC3", "RC5", "RC10", "-"])
        combo.setCurrentText(str(value))
        return combo

    def create_status_cell(self, value):
        combo = NoScrollComboBox()
        combo.setEditable(True)
        statuses = ["Необходим ремонт", "Тестируется", "Протестирован", "Откалиброван", "Упакован", "-"]
        combo.addItems(statuses)
        combo.setCurrentText(str(value))
        self.update_status_color(combo, value)
        combo.currentTextChanged.connect(lambda text: self.update_status_color(combo, text))

         # 🔧 Устанавливаем минимальную ширину по самому длинному статусу
        max_width = max([combo.fontMetrics().width(s) for s in statuses]) + 30
        combo.setMinimumWidth(max_width)

        return combo

    def update_status_color(self, combo, status):
        color_map = {
            "Необходим ремонт": QColor("#ffcccc"),     # светло-красный
            "Откалиброван": QColor("#ccffcc"),         # светло-зелёный
            "Тестируется": QColor("#ffffcc"),          # светло-жёлтый
            "Протестирован": QColor("#ccffff"),        # светло-голубой
            "Упакован": QColor("#e0e0e0"),             # серый
            "-": QColor("#ffffff")                     # белый
        }

        color = color_map.get(status, QColor("#ffffff"))
        palette = combo.palette()
        palette.setColor(QPalette.Base, color)
        combo.setPalette(palette)

    def create_multiline_cell(self, value):
        editor = QPlainTextEdit()
        editor.setPlainText(str(value))
        editor.setMaximumHeight(50)
        editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        editor.setWordWrapMode(QTextOption.WordWrap)
        return editor

    def load_data(self):
        self.table.blockSignals(True)
        robots = get_all_robots()
        robots.sort(key=lambda x: x['id'])

        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(robots))

        for row_idx, robot in enumerate(robots):
            for col_idx, field in enumerate(self.db_fields):
                value = robot.get(field, "")
                if field == "model":
                    self.table.setCellWidget(row_idx, col_idx, self.create_model_cell(value))
                elif field == "status":
                    self.table.setCellWidget(row_idx, col_idx, self.create_status_cell(value))
                else:
                    self.table.setCellWidget(row_idx, col_idx, self.create_multiline_cell(value))

        self.table.setWordWrap(True)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.blockSignals(False)

        # После self.table.setRowCount(len(robots))
        status_column_index = self.db_fields.index("status")
        self.table.setColumnWidth(status_column_index, 160)  # или max_width, если хочешь динамически


    def add_robot(self):
        reply = QMessageBox.question(self, "Несохранённые данные",
            "Вы хотите сохранить изменения перед добавлением нового робота?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            self.save_changes()

        add_robot()
        self.load_data()

    def delete_robot(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        robot_id = get_all_robots()[selected]['id']
        reply = QMessageBox.question(self, "Подтверждение удаления",
                                     f"Удалить робота с ID {robot_id}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_robot(robot_id)
            self.load_data()

    def save_changes(self):
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Сохранить все изменения?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        robots = get_all_robots()
        for row in range(self.table.rowCount()):
            robot_id = robots[row]['id']
            for col in range(self.table.columnCount()):
                field = self.db_fields[col]
                widget = self.table.cellWidget(row, col)
                if isinstance(widget, QComboBox):
                    value = widget.currentText()
                elif isinstance(widget, QPlainTextEdit):
                    value = widget.toPlainText()
                else:
                    continue
                update_robot(robot_id, field, value)
        QMessageBox.information(self, "Готово", "✅ Изменения сохранены.")
        self.load_data()

    def export_to_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "Роботы ОТК"
        ws.append(self.headers)
        robots = get_all_robots()
        for robot in robots:
            row_data = [robot.get(field, "") for field in self.db_fields]
            ws.append(row_data)
        wb.save("robots_export.xlsx")
        print("✅ Данные успешно экспортированы в robots_export.xlsx")
