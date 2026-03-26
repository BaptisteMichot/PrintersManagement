# ==========================================
# ABB Printers Management Application
# Point d'entrée principal de l'application
# ==========================================

import sys
import warnings

# Supprimer les warnings non critiques de PySide6
warnings.filterwarnings("ignore", message=".*QFont::setPointSize.*")

from database.connection import connect_db
from ui.main_window import MainWindow
from ui.dialogs.password_dialog import PasswordDialog
from PySide6.QtWidgets import QApplication, QDialog


def main():
    """
    Initialise et lance l'application principale.
    
    Cette fonction effectue les étapes suivantes :
    1. Crée l'application Qt
    2. Affiche le dialog d'authentification par mot de passe
    3. Teste la connexion à la base de données
    4. Affiche la fenêtre principale en plein écran
    """
    
    # Créer l'application Qt
    app = QApplication(sys.argv)

    # Afficher le dialog d'authentification
    password_dialog = PasswordDialog()
    if password_dialog.exec() != QDialog.Accepted:
        # Si l'utilisateur n'a pas entré le bon mot de passe, quitter
        sys.exit(0)

    # Vérifier la connexion à la base de données
    conn = connect_db()
    conn.close()

    # Créer et afficher la fenêtre principale en plein écran
    window = MainWindow()
    window.showMaximized()

    # Lancer la boucle événementielle Qt
    sys.exit(app.exec())


# Point d'entrée du script
if __name__ == "__main__":
    main()