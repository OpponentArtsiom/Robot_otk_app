import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from db import init_db
from ui import RobotTable

def main():
    init_db()  # Инициализация базы данных
    app = QApplication(sys.argv)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    window = RobotTable()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
