# ==========================================
# Page À commander
# Affiche les cartouches dont le stock est inférieur au minimum
# ==========================================

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QMessageBox,
    QFileDialog
)

from PySide6.QtCore import Qt
from database.cartridges import get_cartridges_to_order
from utils.pdf_export import export_cartridges_to_pdf


class ToOrderPage(QWidget):
    """
    Page affichant la liste des cartouches à commander.
    Affiche les cartouches dont le stock est en dessous du minimum requis.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants de la page À commander"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Barre supérieure avec boutons et résumé
        top_bar = QHBoxLayout()

        # Bouton Actualiser
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("mainButton")
        self.refresh_button.clicked.connect(self.refresh_cartridges_to_order)

        # Bouton Export PDF
        self.export_button = QPushButton("Download PDF")
        self.export_button.setObjectName("mainButton")
        self.export_button.clicked.connect(self.export_to_pdf)

        # Label du résumé
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("summaryLabel")

        top_bar.addWidget(self.refresh_button)
        top_bar.addWidget(self.export_button)
        top_bar.addStretch()
        top_bar.addWidget(self.summary_label)

        layout.addLayout(top_bar)

        # Tableau des cartouches à commander
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Name",
            "Color",
            "In stock",
            "Min stock",
            "To order"
        ])

        # Configuration du tableau
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)

        # Configuration de la taille des colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        # Appliquer les styles CSS
        self.table.setStyleSheet("""
        QTableWidget {
            background: white;
            border-radius: 8px;
            font-size: 13px;
            padding: 6px;
            selection-background-color: transparent;
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

        QTableWidget::item:selected {
            background: #e8f4f8;
            color: black;
        }
        """)

        layout.addWidget(self.table)
        self.setLayout(layout)

        # Appliquer les styles CSS à la page
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

        QPushButton#mainButton:disabled {
            background-color: #b2bec3;
        }

        QLabel#summaryLabel {
            font-size: 13px;
            font-weight: bold;
            color: #2d3436;
        }
        """)

        # Charger les données initiales
        self.refresh_cartridges_to_order()

    def refresh_cartridges_to_order(self):
        """
        Rafraîchir et afficher les cartouches à commander.
        Récupère les cartouches dont le stock est en dessous du minimum.
        """
        try:
            # Récupérer les cartouches à commander
            cartridges = get_cartridges_to_order()
            self.table.setRowCount(0)

            # Remplir le tableau avec les données
            for row, cartridge in enumerate(cartridges):
                self.table.insertRow(row)

                # Créer les items du tableau
                name_item = QTableWidgetItem(cartridge["name"])
                color_item = QTableWidgetItem(cartridge["color"])
                stock_item = QTableWidgetItem(str(cartridge["inStock"]))
                min_item = QTableWidgetItem(str(cartridge["minStock"]))
                missing_item = QTableWidgetItem(str(cartridge["missing"]))

                # Centrer le texte dans toutes les cellules
                name_item.setTextAlignment(Qt.AlignCenter)
                color_item.setTextAlignment(Qt.AlignCenter)
                stock_item.setTextAlignment(Qt.AlignCenter)
                min_item.setTextAlignment(Qt.AlignCenter)
                missing_item.setTextAlignment(Qt.AlignCenter)

                # Ajouter les items au tableau
                self.table.setItem(row, 0, name_item)
                self.table.setItem(row, 1, color_item)
                self.table.setItem(row, 2, stock_item)
                self.table.setItem(row, 3, min_item)
                self.table.setItem(row, 4, missing_item)

                # Définir la hauteur de la ligne
                self.table.setRowHeight(row, 34)

            # Afficher un résumé des cartouches à commander
            if cartridges:
                total_to_order = sum(item["missing"] for item in cartridges)
                self.summary_label.setText(
                    f"{len(cartridges)} cartridge(s) to order - {total_to_order} unit(s) total"
                )
            else:
                self.summary_label.setText("No cartridge needs ordering.")

        except Exception as e:
            # Afficher un message d'erreur en cas de problème
            QMessageBox.critical(
                self,
                "Error loading cartridges",
                f"Failed to load cartridges to order: {str(e)}"
            )

    def export_to_pdf(self):
        """
        Exporte les cartouches à commander en fichier PDF.
        Affiche un dialogue pour choisir le lieu de sauvegarde.
        """
        try:
            # Récupérer les cartouches actuelles
            cartridges = get_cartridges_to_order()
            
            if not cartridges:
                QMessageBox.information(
                    self,
                    "No data to export",
                    "There are no cartridges to order at the moment."
                )
                return
            
            # Ouvrir un dialogue de sauvegarde
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export cartridges to PDF",
                "cartridges_to_order.pdf",
                "PDF Files (*.pdf)"
            )
            
            # Si l'utilisateur a sélectionné un fichier
            if file_path:
                # Exporter en PDF
                success = export_cartridges_to_pdf(cartridges, file_path)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Export successful",
                        f"Cartridges have been exported to:\n{file_path}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Export failed",
                        "An error occurred while exporting the cartridges to PDF."
                    )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export error",
                f"An error occurred while exporting: {str(e)}"
            )