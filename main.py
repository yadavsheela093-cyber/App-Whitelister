"""
main.py
Entry point for Application Whitelisting Tool.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from core import database as db
from core import security
from ui.main_window import MainWindow
from ui.dialogs import LoginDialog


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AppWhitelister")

    db.init_db()

    # Show login dialog if password is set
    if security.admin_password_is_set():
        login = LoginDialog()
        if login.exec_() != LoginDialog.Accepted:
            sys.exit(0)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
