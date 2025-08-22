from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QPlainTextEdit, QFormLayout
)
from PyQt5.QtCore import Qt

class AddRobotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление нового робота")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.fields = {}

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        # 🔧 Поля формы
        field_defs = [
            ("model", "Модель", ["RC3", "RC5", "RC10", "-"]),
            ("robot_sn", "Серийный № робота"),
            ("controller_sn", "Серийный № контроллера"),
            ("status", "Статус", ["Необходим ремонт", "Тестируется", "Протестирован", "Откалиброван", "Упакован", "-"]),
            ("fault_description", "Описание неисправности", "multiline"),
            ("fault_module", "Проблемный узел/модуль"),
            ("fault_reason", "Причина поломки"),
            ("tasks_done", "Проведенные работы", "multiline"),
            ("tasks_required", "Планируемые работы", "multiline"),
            ("required_parts", "Необходимые запчасти", "multiline"),
        ]

        for field_id, label_text, *extra in field_defs:
            if extra and isinstance(extra[0], list):  # ComboBox
                widget = QComboBox()
                widget.addItems(extra[0])
            elif extra and extra[0] == "multiline":
                widget = QPlainTextEdit()
                widget.setMaximumHeight(60)
            else:
                widget = QLineEdit()
            self.fields[field_id] = widget
            form_layout.addRow(QLabel(label_text), widget)

        # 🔘 Кнопки
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
        return data
