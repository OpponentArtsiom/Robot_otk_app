from PyQt5.QtWidgets import (
    QComboBox, QPlainTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextOption, QPalette, QColor
from openpyxl import Workbook

from db import get_all_robots, update_robot, add_robot, delete_robot


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class RobotLogic:
    def __init__(self, ui):
        self.ui = ui

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

    def filter_table(self):
        query = self.ui.search_input.text().lower()
        for row in range(self.ui.table.rowCount()):
            match = False
            for col in range(self.ui.table.columnCount()):
                widget = self.ui.table.cellWidget(row, col)
                if isinstance(widget, QComboBox):
                    text = widget.currentText().lower()
                elif isinstance(widget, QPlainTextEdit):
                    text = widget.toPlainText().lower()
                else:
                    continue
                if query in text:
                    match = True
                    break
            self.ui.table.setRowHidden(row, not match)

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
        max_width = max([combo.fontMetrics().width(s) for s in statuses]) + 40
        combo.setMinimumWidth(max_width)
        return combo

    def update_status_color(self, combo, status):
        color_map = {
            "Необходим ремонт": QColor("#ffcccc"),
            "Откалиброван": QColor("#ccffcc"),
            "Тестируется": QColor("#ffffcc"),
            "Протестирован": QColor("#ccffff"),
            "Упакован": QColor("#e0e0e0"),
            "-": QColor("#ffffff")
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
        self.ui.table.blockSignals(True)
        robots = get_all_robots()
        robots.sort(key=lambda x: x['id'])

        self.ui.table.setColumnCount(len(self.headers))
        self.ui.table.setHorizontalHeaderLabels(self.headers)
        self.ui.table.setRowCount(len(robots))

        for row_idx, robot in enumerate(robots):
            for col_idx, field in enumerate(self.db_fields):
                value = robot.get(field, "")
                if field == "model":
                    self.ui.table.setCellWidget(row_idx, col_idx, self.create_model_cell(value))
                elif field == "status":
                    self.ui.table.setCellWidget(row_idx, col_idx, self.create_status_cell(value))
                else:
                    self.ui.table.setCellWidget(row_idx, col_idx, self.create_multiline_cell(value))

        self.ui.table.setWordWrap(True)
        self.ui.table.resizeColumnsToContents()
        self.ui.table.resizeRowsToContents()
        self.ui.table.blockSignals(False)

        status_column_index = self.db_fields.index("status")
        self.ui.table.setColumnWidth(status_column_index, 170)

    def add_robot(self):
        reply = QMessageBox.question(self.ui, "Несохранённые данные",
            "Вы хотите сохранить изменения перед добавлением нового робота?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            self.save_changes()

        add_robot()
        self.load_data()

    def delete_robot(self):
        selected = self.ui.table.currentRow()
        if selected < 0:
            return
        robot_id = get_all_robots()[selected]['id']
        reply = QMessageBox.question(self.ui, "Подтверждение удаления",
                                     f"Удалить робота с ID {robot_id}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_robot(robot_id)
            self.load_data()

    def save_changes(self):
        reply = QMessageBox.question(self.ui, "Подтверждение",
                                     "Сохранить все изменения?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        robots = get_all_robots()
        for row in range(self.ui.table.rowCount()):
            robot_id = robots[row]['id']
            for col in range(self.ui.table.columnCount()):
                field = self.db_fields[col]
                widget = self.ui.table.cellWidget(row, col)
                if isinstance(widget, QComboBox):
                    value = widget.currentText()
                elif isinstance(widget, QPlainTextEdit):
                    value = widget.toPlainText()
                else:
                    continue
                update_robot(robot_id, field, value)
        QMessageBox.information(self.ui, "Готово", "✅ Изменения сохранены.")
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

