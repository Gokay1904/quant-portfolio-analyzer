from PyQt5.QtWidgets import QApplication
import sys
from app.finance_app import FinanceApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceApp()
    window.show()
    sys.exit(app.exec_())