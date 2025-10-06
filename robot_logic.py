from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from openpyxl import Workbook

from robot_dialog import RobotDialog
from db import get_all_robots, add_robot_with_data, update_robot, delete_robot


class RobotLogic:
    def __init__(self, ui):
        self.ui = ui

        self.headers = [
            "Модель", "Серийный № робота", "Серийный № контроллера",
            "Текущий статус", "Описание неисправности",
            "Причина поломки", "Проведенные работы",
            "Планируемые работы", "Необходимые запчасти", "Примечания"
        ]
        self.db_fields = [
            "model", "robot_sn", "controller_sn",
            "status", "fault_description",
            "fault_reason", "tasks_done",
            "tasks_required", "required_parts", "notes"
        ]

    def create_table_item(self, value, field=None):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        if field == "status":
            color_map = {
                "Необходим ремонт": QColor("#ffcccc"),
                "Откалиброван": QColor("#ccffcc"),
                "Тестируется": QColor("#ffffcc"),
                "Протестирован": QColor("#ccffff"),
                "Упакован": QColor("#e0e0e0"),
                "Отгружен": QColor("#d0d0d0"),  # серый цвет для "Отгружен"
                "-": QColor("#ffffff")
            }
            color = color_map.get(value, QColor("#ffffff"))
            item.setBackground(color)

        return item

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
                item = self.create_table_item(value, field)
                self.ui.table.setItem(row_idx, col_idx, item)

        self.ui.table.resizeColumnsToContents()
        self.ui.table.resizeRowsToContents()
        self.ui.table.blockSignals(False)

        status_column_index = self.db_fields.index("status")

        # Блокируем визуально строки со статусом "Отгружен"
        self.ui.table.setColumnWidth(status_column_index, 170)
        for row_idx, robot in enumerate(robots):
            # окрашивание уже сделано в create_table_item, здесь можно оставить фокус
            if robot.get("status") == "Отгружен":
                for col_idx in range(self.ui.table.columnCount()):
                    cell = self.ui.table.item(row_idx, col_idx)
                    if cell:
                        cell.setBackground(QColor(200, 200, 200))  # серый цвет

    def filter_table(self):
        query = self.ui.search_input.text().lower()
        for row in range(self.ui.table.rowCount()):
            match = False
            for col in range(self.ui.table.columnCount()):
                item = self.ui.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.ui.table.setRowHidden(row, not match)

    def add_robot(self):
        dialog = RobotDialog(parent=self.ui)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            add_robot_with_data(data)
            self.load_data()

    def edit_robot(self):
        selected_row = self.ui.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.ui, "Нет выбора", "Выберите строку для редактирования")
            return

        robots = get_all_robots()
        if selected_row >= len(robots):
            QMessageBox.warning(self.ui, "Ошибка", "Выбранная строка вне диапазона")
            return

        robot = robots[selected_row]
        dialog = RobotDialog(robot_data=robot, parent=self.ui)

        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            robot_id = robot['id']
            for field, value in updated_data.items():
                update_robot(robot_id, field, value)
            self.load_data()
            QMessageBox.information(self.ui, "Готово", "✅ Робот обновлён.")

    def delete_robot(self):
        selected_row = self.ui.table.currentRow()
        if selected_row < 0:
            return
        robots = get_all_robots()
        if selected_row >= len(robots):
            return
        robot_id = robots[selected_row]['id']
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
                item = self.ui.table.item(row, col)
                if item:
                    value = item.text()
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
