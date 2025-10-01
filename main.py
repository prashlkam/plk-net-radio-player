import sys
from PyQt6.QtWidgets import QApplication
from plknetradioplayer import RadioApp

def main():
    app = QApplication(sys.argv)
    window = RadioApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
