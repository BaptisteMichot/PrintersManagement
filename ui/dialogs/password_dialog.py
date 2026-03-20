# ==========================================
# Dialogue de mot de passe
# Authentification au lancement de l'application
# ==========================================

import os
from dotenv import load_dotenv
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)
from PySide6.QtCore import Qt


# Charger les variables d'environnement
load_dotenv()


class PasswordDialog(QDialog):
    """Dialogue pour l'authentification par mot de passe au lancement."""

    def __init__(self):
        super().__init__()

        # Charger le mot de passe depuis les variables d'environnement
        self.PASSWORD = os.getenv("APP_PASSWORD", "printer")

        self.setWindowTitle("Authentication Required")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(300, 150)

        # Créer le layout principal
        layout = QVBoxLayout(self)

        # Label
        label = QLabel("Enter password to access the application:")
        layout.addWidget(label)

        # Champ de mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.verify_password)
        layout.addWidget(self.password_input)

        # Boutons
        button_layout = QHBoxLayout()
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.verify_password)
        button_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)

        # Focus sur le champ de mot de passe
        self.password_input.setFocus()

    def verify_password(self):
        """Vérifier le mot de passe saisi."""
        if self.password_input.text() == self.PASSWORD:
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Authentication Failed",
                "Incorrect password. Please try again."
            )
            self.password_input.clear()
            self.password_input.setFocus()
