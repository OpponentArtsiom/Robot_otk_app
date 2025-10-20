# main.py
import sys
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# ✅ Импортируем новые классы
from db import Database, RobotRepository, HistoryRepository, DB_DEFAULT
from services import RobotService
from ui import RobotTable


# 📄 Настройка логгирования в файл
logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def show_error_dialog(error_message: str):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Ошибка")
    msg_box.setText("Произошла критическая ошибка!")
    msg_box.setDetailedText(error_message)
    msg_box.exec_()


def main():
    try:
        # --- 🗄️ Настройка базы данных и сервисов ---
        db = Database(DB_DEFAULT)
        robot_repo = RobotRepository(db)
        history_repo = HistoryRepository(db)
        service = RobotService(robot_repo, history_repo)

        # Создание таблиц (если не существуют)
        service.init_db()

        # --- 🚀 Запуск приложения ---
        app = QApplication(sys.argv)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Создание основного окна и передача сервиса
        window = RobotTable(service=service)
        window.showMaximized()

        sys.exit(app.exec_())

    except Exception:
        # 🐞 Логирование и показ ошибки пользователю
        error_message = traceback.format_exc()
        logging.error(error_message)
        show_error_dialog(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()
