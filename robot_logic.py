# robot_logic.py
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QDialog, QInputDialog, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from openpyxl import Workbook
from robot_dialog import RobotDialog
from history_dialog import HistoryDialog


class RobotLogic:
    def __init__(self, ui, service):
        """
        ui: экземпляр окна/виджета (например, RobotTable из ui.py)
        service: экземпляр RobotService (services.RobotService)
        """
        self.ui = ui
        self.service = service

        self.headers = [
            "Модель", "Серийный № робота", "Серийный № контроллера", "Текущий статус",
            "Описание неисправности", "Причина поломки", "Проведенные работы",
            "Планируемые работы", "Необходимые запчасти", "Примечания"
        ]

        self.db_fields = [
            "model", "robot_sn", "controller_sn", "status",
            "fault_description", "fault_reason", "tasks_done",
            "tasks_required", "required_parts", "notes"
        ]

        self.start_auto_refresh()

    def start_auto_refresh(self):
        """Автообновление таблицы каждую минуту."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(60000)  # 60 секунд

    def show_history(self):
        """Открывает диалог истории."""
        dialog = HistoryDialog(service=self.service, parent=self.ui)
        dialog.exec_()

    def clear_history(self):
        """Очистка всей истории через сервис с подтверждением пароля."""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit

        password, ok = QInputDialog.getText(
            self.ui, "Пароль", "Введите пароль для очистки истории:", QLineEdit.Password
        )
        if not ok:
            return

        expected = self.service.get_history_clear_password()  # или self.service.config.get("history_clear_password")
        if expected is None:
            QMessageBox.critical(self.ui, "Ошибка", "Пароль не задан в config.json")
            return

        if password != expected:
            QMessageBox.warning(self.ui, "Ошибка", "Неверный пароль!")
            return

        reply = QMessageBox.question(
            self.ui, "Подтверждение",
            "Вы уверены, что хотите очистить всю историю?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.service.clear_history()
            self.load_data()  # или self.show_history()
            QMessageBox.information(self.ui, "История", "🧹 История успешно очищена.")


    def create_table_item(self, value, field=None):
        """Создаёт QTableWidgetItem с правильными флагами и раскраской по статусу."""
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        if field == "status":
            color_map = {
                "Необходим ремонт": QColor("#ffcccc"),
                "Откалиброван": QColor("#8FBC8F"),
                "Тестируется": QColor("#ffffcc"),
                "Протестирован": QColor("#ccffff"),
                "Упакован": QColor("#87CEEB"),
                "Отгружен": QColor("#d0d0d0"),
                "Простаивает": QColor("#DCDCDC")
            }
            color = color_map.get(value, QColor("#ffffff"))
            item.setBackground(color)

        return item

    def load_data(self):
        """Загружает данные из БД и заполняет таблицу UI."""
        try:
            self.ui.table.blockSignals(True)
        except Exception:
            pass

        robots = self.service.get_all_robots() or []
        robots.sort(key=lambda x: x.get('id', 0))

        self.ui.table.setColumnCount(len(self.headers))
        self.ui.table.setHorizontalHeaderLabels(self.headers)
        self.ui.table.setRowCount(len(robots))

        for row_idx, robot in enumerate(robots):
            for col_idx, field in enumerate(self.db_fields):
                value = robot.get(field, "")
                item = self.create_table_item(value, field)
                self.ui.table.setItem(row_idx, col_idx, item)

        try:
            self.ui.table.resizeColumnsToContents()
            self.ui.table.resizeRowsToContents()
        except Exception:
            pass

        try:
            self.ui.table.blockSignals(False)
        except Exception:
            pass

        # Настройка ширины колонки Статус и затемнение строк "Отгружен"
        if "status" in self.db_fields:
            status_column_index = self.db_fields.index("status")
            try:
                self.ui.table.setColumnWidth(status_column_index, 170)
            except Exception:
                pass

            for row_idx, robot in enumerate(robots):
                if robot.get("status") == "Отгружен":
                    for col_idx in range(self.ui.table.columnCount()):
                        cell = self.ui.table.item(row_idx, col_idx)
                        if cell:
                            cell.setBackground(QColor(200, 200, 200))

    def filter_table(self):
        """Фильтрация строк таблицы по вводу в поле поиска."""
        try:
            query = self.ui.search_input.text().lower()
        except Exception:
            query = ""
        for row in range(self.ui.table.rowCount()):
            match = False
            for col in range(self.ui.table.columnCount()):
                item = self.ui.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.ui.table.setRowHidden(row, not match)

    def add_robot(self):
        """Открывает диалог добавления робота и добавляет через сервис."""
        dialog = RobotDialog(parent=self.ui)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.service.add_robot(data)
            self.load_data()

    def edit_robot(self):
        """Редактирование выбранной строки через диалог."""
        selected_row = self.ui.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.ui, "Нет выбора", "Выберите строку для редактирования")
            return

        robots = self.service.get_all_robots() or []
        if selected_row >= len(robots):
            QMessageBox.warning(self.ui, "Ошибка", "Выбранная строка вне диапазона")
            return

        robot = robots[selected_row]
        dialog = RobotDialog(robot_data=robot, parent=self.ui)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            robot_id = robot.get('id')
            for field, value in updated_data.items():
                old_value = robot.get(field)
                if str(old_value or "") != str(value or ""):
                    self.service.update_robot(robot_id, field, value, old_value)
            self.load_data()
            QMessageBox.information(self.ui, "Готово", "✅ Робот обновлён.")

    def delete_robot(self):
        """Удаляет выбранного робота после подтверждения."""
        selected_row = self.ui.table.currentRow()
        if selected_row < 0:
            return

        robots = self.service.get_all_robots() or []
        if selected_row >= len(robots):
            return

        robot_id = robots[selected_row].get('id')
        reply = QMessageBox.question(
            self.ui, "Подтверждение удаления", f"Удалить робота с ID {robot_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.service.delete_robot(robot_id)
            self.load_data()

    def save_changes(self):
        """Подтверждение сохранения всех изменений (для будущей логики редактирования на месте)."""
        reply = QMessageBox.question(self.ui, "Подтверждение", "Сохранить все изменения?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        QMessageBox.information(self.ui, "Сохранено", "Изменения сохранены (если были).")

    def export_to_excel(self):
        """Экспорт таблицы роботов в Excel-файл robots_export.xlsx."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Роботы ОТК"
        ws.append(self.headers)

        robots = self.service.get_all_robots() or []
        for robot in robots:
            row_data = [robot.get(field, "") for field in self.db_fields]
            ws.append(row_data)

        try:
            wb.save("robots_export.xlsx")
            QMessageBox.information(self.ui, "Экспорт", "✅ Данные экспортированы в robots_export.xlsx")
        except Exception as e:
            QMessageBox.critical(self.ui, "Ошибка экспорта", f"Не удалось сохранить файл: {e}")
