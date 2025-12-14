import sys
from backend import db
from PySide6.QtWidgets import QApplication
from frontend.frontend import ContaIDE   # importa dalla folder frontend

if __name__ == "__main__":
    db.init_db()
    app = QApplication(sys.argv)
    window = ContaIDE()
    window.show()
    sys.exit(app.exec())
