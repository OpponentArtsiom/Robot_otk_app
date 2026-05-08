import sys
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from db import init_db
from ui import RobotTable

# 📄 Настройка логгирования в файл
logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def show_error_dialog(error_message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Ошибка")
    msg_box.setText("Произошла критическая ошибка!")
    msg_box.setDetailedText(error_message)
    msg_box.exec_()

def main():
    try:
        init_db()  # Инициализация БД
        app = QApplication(sys.argv)

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        


        window = RobotTable()
        window.showMaximized()

        sys.exit(app.exec_())

    except Exception as e:
        # 🐞 Сохраняем трейсбек и лог
        error_message = traceback.format_exc()
        logging.error(error_message)

        # 🔔 Показываем пользователю
        show_error_dialog(error_message)

        # 💥 Завершаем принудительно
        sys.exit(1)

if __name__ == "__main__":
    main()
