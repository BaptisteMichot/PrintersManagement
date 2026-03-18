# ==========================================
# Dialogue pour afficher les cartouches d'une imprimante
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView
)

from PySide6.QtCore import Qt
from database.printers import get_cartridges_for_printer


class PrinterCartridgesDialog(QDialog):
    """Dialogue affichant les cartouches compatibles avec une imprimante."""

    def __init__(self, ip, model):
        super().__init__()
        self.ip = ip
        self.model = model
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants du dialogue"""
        self.setWindowTitle(f"Cartridges for {self.model}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Label de titre
        title = QLabel(f"Cartridges compatible with {self.model}:")
        layout.addWidget(title)

        # Tableau des cartouches
        try:
            # Récupérer les cartouches compatibles
            cartridges = get_cartridges_for_printer(self.ip)

            if cartridges:
                # Créer le tableau
                table = QTableWidget()
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["Name", "Color", "In stock"])
                table.verticalHeader().setVisible(False)
                table.setShowGrid(False)
                table.setSelectionMode(QTableWidget.NoSelection)

                # Configurer la taille des colonnes
                header = table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.Stretch)
                header.setSectionResizeMode(1, QHeaderView.Stretch)
                header.setSectionResizeMode(2, QHeaderView.Stretch)

                # Appliquer les styles CSS
                table.setStyleSheet("""
                QTableWidget {
                    background: white;
                    border-radius: 8px;
                    font-size: 13px;
                    padding: 6px;
                }

                QHeaderView::section {
                    background-color: #f1f2f6;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                }

                QTableWidget::item {
                    padding-left: 6px;
                }
                """)

                # Remplir le tableau avec les cartouches
                for i, cartridge in enumerate(cartridges):
                    table.insertRow(i)
                    
                    # Ajouter le nom de la cartouche
                    name_item = QTableWidgetItem(cartridge["name"])
                    name_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(i, 0, name_item)
                    
                    # Ajouter la couleur
                    color_item = QTableWidgetItem(cartridge["color"])
                    color_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(i, 1, color_item)
                    
                    # Ajouter le stock
                    stock_item = QTableWidgetItem(str(cartridge["inStock"]))
                    stock_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(i, 2, stock_item)
                    
                    # Définir la hauteur de ligne
                    table.setRowHeight(i, 34)

                layout.addWidget(table)
            else:
                # Afficher un message si aucune cartouche trouvée
                no_cartridges = QLabel("No cartridges found for this printer.")
                layout.addWidget(no_cartridges)

        except Exception as e:
            # Afficher un message d'erreur
            error_label = QLabel(f"Error loading cartridges: {str(e)}")
            layout.addWidget(error_label)

        # Bouton Fermer
        close_button = QPushButton("Close")
        close_button.setObjectName("mainButton")
        close_button.clicked.connect(self.accept)

        layout.addStretch()
        layout.addWidget(close_button)

        self.setLayout(layout)

        # Appliquer les styles CSS
        self.setStyleSheet("""
        QPushButton#mainButton {
            background-color: #0984e3;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }

        QPushButton#mainButton:hover {
            background-color: #74b9ff;
        }
        """)
