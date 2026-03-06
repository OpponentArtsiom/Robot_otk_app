from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QPlainTextEdit, QFormLayout, QDateEdit
)
from PyQt5.QtCore import Qt, QDate


class RobotDialog(QDialog):
    def __init__(self, robot_data=None, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(500)

        self.fields = {}
        self.robot_data = robot_data or {}
        self.is_edit_mode = bool(robot_data)

        self.setWindowTitle(
            "Редактирование робота" if self.is_edit_mode else "Добавление нового робота"
        )

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        field_defs = [
            ("model", "Модель", ["RC3", "RC5", "RC10","RC16", "Без робота"]),
            ("robot_sn", "Серийный № робота"),
            ("controller_sn", "Серийный № контроллера"),
            ("arrival_date", "Дата поступления"),  # новая дата
            ("status", "Статус", ["Необходим ремонт", "Тестируется", "Протестирован", "Откалиброван", "Упакован","Отгружен", "Простаивает"]),
            ("fault_description", "Описание неисправности", "multiline"),
            ("fault_reason", "Причина поломки"),
            ("tasks_done", "Проведенные работы", "multiline"),
            ("tasks_required", "Планируемые работы", "multiline"),
            ("required_parts", "Необходимые запчасти", "multiline"),
            ("notes", "Примечания", "multiline")
        ]

        for field_id, label_text, *extra in field_defs:
            value = self.robot_data.get(field_id, "")
            if field_id == "arrival_date":
                # QDateEdit с календарём
                widget = QDateEdit()
                widget.setDisplayFormat("dd.MM.yy")
                widget.setCalendarPopup(True)
                if value:
                    try:
                        # если в базе YYYY-MM-DD
                        dt = QDate.fromString(value, "yyyy-MM-dd")
                        widget.setDate(dt)
                    except Exception:
                        widget.setDate(QDate.currentDate())
                else:
                    widget.setDate(QDate.currentDate())
            elif extra and isinstance(extra[0], list):
                widget = QComboBox()
                widget.addItems(extra[0])
                widget.setCurrentText(value)
            elif extra and extra[0] == "multiline":
                widget = QPlainTextEdit()
                widget.setPlainText(value)
                widget.setMaximumHeight(60)
            else:
                widget = QLineEdit()
                widget.setText(value)
            self.fields[field_id] = widget
            form_layout.addRow(QLabel(label_text), widget)

        # кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.cancel_button)
        main_layout.addLayout(btn_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_data(self):
        data = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()
            elif isinstance(widget, QPlainTextEdit):
                data[key] = widget.toPlainText().strip()
            elif key == "arrival_date" and isinstance(widget, QDateEdit):
                # сохраняем в формате YYYY-MM-DD
                data[key] = widget.date().toString("dd.MM.yyyy")
        return data