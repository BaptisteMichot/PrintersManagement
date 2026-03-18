# ==========================================
# ABB Printers Management Application
# Point d'entrée principal de l'application
# ==========================================

import sys
import os
import warnings

# Supprimer les warnings non critiques de PySide6
warnings.filterwarnings("ignore", message=".*QFont::setPointSize.*")

from database.connection import connect_db
from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont


def main():
    """
    Initialise et lance l'application principale.
    
    Cette fonction effectue les étapes suivantes :
    1. Teste la connexion à la base de données
    2. Crée l'application Qt
    3. Affiche la fenêtre principale en plein écran
    """
    
    # Vérifier la connexion à la base de données
    conn = connect_db()
    conn.close()

    # Créer l'application Qt
    app = QApplication(sys.argv)

    # Créer et afficher la fenêtre principale en plein écran
    window = MainWindow()
    window.showMaximized()

    # Lancer la boucle événementielle Qt
    sys.exit(app.exec())


# Point d'entrée du script
if __name__ == "__main__":
    main()