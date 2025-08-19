from PyQt5.QtWidgets import (
    QWidget, QComboBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QPushButton, QPlainTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextOption
from db import get_all_robots, update_robot, add_robot, delete_robot
from openpyxl import Workbook

# 🔧 Кастомный ComboBox, отключающий прокрутку мыши
class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Игнорируем колесо мыши, чтобы не менять значение случайно

# 🧩 Основной класс интерфейса
class RobotTable(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учёт роботов ОТК")
        self.resize(1000, 400)

        # 📊 Таблица и кнопки управления
        self.table = QTableWidget()
        self.add_button = QPushButton("➕ Добавить робота")
        self.delete_button = QPushButton("🗑️ Удалить робота")
        self.save_button = QPushButton("💾 Сохранить изменения")
        self.export_button = QPushButton("📄 Экспорт в Excel")
        self.refresh_button = QPushButton("🔄 Обновить таблицу")  # Кнопка обновления
        #############################################

        # 🔗 Привязка кнопок к методам
        self.add_button.clicked.connect(self.add_robot)
        self.delete_button.clicked.connect(self.delete_robot)
        self.save_button.clicked.connect(self.save_changes)
        self.export_button.clicked.connect(self.export_to_excel)
        self.refresh_button.clicked.connect(self.load_data)
        ##############################################

        # Расположение кнопок горизонтально
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.refresh_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        ################################################


        # 🏷️ Заголовки таблицы и соответствующие поля в базе
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
        self.field_map = {i: field for i, field in enumerate(self.db_fields)}  # Сопоставление индексов и полей
        self.load_data()  # Загрузка данных при запуске

    # 🔧 Создание ячейки с выбором модели
    def create_model_cell(self, value):
        combo = NoScrollComboBox()
        combo.addItems(["RC3", "RC5", "RC10", "-"])
        combo.setCurrentText(str(value))
        return combo

    # 🔧 Создание ячейки с выбором статуса
    def create_status_cell(self, value):
        combo = NoScrollComboBox()
        combo.addItems(["Необходим ремонт", "Тестируется", "Протестирован", "Откалиброван", "Упакован", "-"])
        combo.setCurrentText(str(value))
        return combo

    # 🔧 Создание многострочной текстовой ячейки
    def create_multiline_cell(self, value):
        editor = QPlainTextEdit()
        editor.setPlainText(str(value))
        editor.setMaximumHeight(50)
        editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        editor.setWordWrapMode(QTextOption.WordWrap)
        return editor

    # 📥 Загрузка данных из базы и отображение в таблице
    def load_data(self):
        self.table.blockSignals(True)  # Отключаем сигналы на время загрузки
        robots = get_all_robots()
        robots.sort(key=lambda x: x['id'])  # Сортировка по ID

        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(robots))

        # Заполнение таблицы
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
        self.table.blockSignals(False)  # Включаем сигналы обратно

    # ➕ Добавление нового робота
    def add_robot(self):
        add_robot()  # Добавление в БД
        self.load_data()  # Перезагрузка таблицы

    # 🗑️ Удаление выбранного робота
    def delete_robot(self):
        selected = self.table.currentRow()
        if selected < 0:
            return  # Ничего не выбрано
        robot_id = get_all_robots()[selected]['id']
        reply = QMessageBox.question(self, "Подтверждение удаления",
                                     f"Удалить робота с ID {robot_id}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_robot(robot_id)
            self.load_data()

    # 💾 Сохранение всех изменений
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
                # Получаем значение из виджета
                if isinstance(widget, QComboBox):
                    value = widget.currentText()
                elif isinstance(widget, QPlainTextEdit):
                    value = widget.toPlainText()
                else:
                    continue
                update_robot(robot_id, field, value)  # Обновляем в БД
        QMessageBox.information(self, "Готово", "✅ Изменения сохранены.")
        self.load_data()

    # 📤 Экспорт данных в Excel
    def export_to_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "Роботы ОТК"
        ws.append(self.headers)  # Заголовки
        robots = get_all_robots()
        for row_idx, robot in enumerate(robots):
            row_data = []
            for field in self.db_fields:
                row_data.append(robot.get(field, ""))
            ws.append(row_data)
        wb.save("robots_export.xlsx")  # Сохраняем файл
        print("✅ Данные успешно экспортированы в robots_export.xlsx")
