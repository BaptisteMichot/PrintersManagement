# ==========================================
# Page Cartouches
# Gère l'affichage et la modification des cartouches
# ==========================================

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QHBoxLayout,
    QDialog,
    QMessageBox,
    QLabel,
    QCheckBox,
    QFormLayout,
    QSpinBox,
    QDialogButtonBox
)

from PySide6.QtCore import Qt
from database.cartridges import get_cartridges, update_cartridge_stock


class CartridgesPage(QWidget):
    """
    Page de gestion des cartouches.
    Permet d'afficher, modifier et gérer les cartouches en stock.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants de la page"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Barre supérieure avec boutons
        top_bar = QHBoxLayout()

        # Bouton Voir les modèles
        self.view_models_button = QPushButton("View printer models")
        self.view_models_button.setObjectName("mainButton")
        self.view_models_button.clicked.connect(self.show_printer_models)

        # Bouton Modifier le stock
        self.edit_stock_button = QPushButton("Edit stock")
        self.edit_stock_button.setObjectName("mainButton")
        self.edit_stock_button.clicked.connect(self.edit_cartridge_stock)

        top_bar.addWidget(self.view_models_button)
        top_bar.addWidget(self.edit_stock_button)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # Tableau des cartouches
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "",
            "Name",
            "Color",
            "In stock",
            "Min Stock"
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
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        # Appliquer les styles CSS au tableau
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

        # Appliquer les styles à la page
        self.setStyleSheet("""
        /* Boutons principaux */
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
        """)

        # Charger les cartouches
        self.refresh_cartridges()

    def refresh_cartridges(self):
        """Charger les cartouches de la base de données et remplir le tableau"""
        try:
            # Récupérer les cartouches
            cartridges = get_cartridges()
            self.table.setRowCount(0)

            # Remplir le tableau
            for row, cartridge in enumerate(cartridges):
                self.table.insertRow(row)

                # Colonne checkbox
                checkbox = QCheckBox()
                checkbox.toggled.connect(lambda checked, r=row: self.on_checkbox_toggled(r, checked))
                checkbox_container = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_container)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(row, 0, checkbox_container)

                # Colonne Nom
                name_item = QTableWidgetItem(cartridge["name"])
                name_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, name_item)

                # Colonne Couleur
                color_item = QTableWidgetItem(cartridge["color"])
                color_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, color_item)

                # Colonne Quantité
                quantity_item = QTableWidgetItem(str(cartridge["inStock"]))
                quantity_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, quantity_item)

                # Colonne Stock minimum
                min_stock_item = QTableWidgetItem(str(cartridge["minStock"]))
                min_stock_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, min_stock_item)

                # Stocker les données de la cartouche pour utilisation ultérieure
                self.table.item(row, 1).cartridge_data = cartridge

                # Définir la hauteur de la ligne
                self.table.setRowHeight(row, 34)

        except Exception as e:
            # Afficher un message d'erreur
            QMessageBox.critical(
                self,
                "Error loading cartridges",
                f"Failed to load cartridges: {str(e)}"
            )

    def on_checkbox_toggled(self, row, checked):
        """Gérer le toggle de la checkbox - décocher les autres quand une est cochée"""
        if checked:
            # Décocher toutes les autres checkboxes
            for r in range(self.table.rowCount()):
                if r != row:
                    checkbox = self.table.cellWidget(r, 0).findChild(QCheckBox)
                    if checkbox:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)

    def show_printer_models(self):
        """Afficher un dialogue avec les modèles d'imprimantes dans la cartouche sélectionnée"""
        # Trouver la checkbox cochée
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break
        
        # Afficher un warning si aucune cartouche n'est sélectionnée
        if checked_row is None:
            QMessageBox.warning(self, "No selection", "Please select a cartridge")
            return

        # Récupérer les données de la cartouche
        cartridge_data = self.table.item(checked_row, 1).cartridge_data

        # Afficher le dialogue
        dialog = PrinterModelsDialog(cartridge_data)
        dialog.exec()

    def edit_cartridge_stock(self):
        """Afficher le dialogue pour modifier le stock de la cartouche sélectionnée"""
        # Trouver la checkbox cochée
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break
        
        # Afficher un warning si aucune cartouche n'est sélectionnée
        if checked_row is None:
            QMessageBox.warning(self, "No selection", "Please select a cartridge")
            return

        # Récupérer les données de la cartouche
        cartridge_data = self.table.item(checked_row, 1).cartridge_data

        # Afficher le dialogue d'édition
        dialog = EditStockDialog(cartridge_data, self.refresh_cartridges)
        dialog.exec()


class PrinterModelsDialog(QDialog):
    """Dialogue affichant les modèles d'imprimantes pour une cartouche"""

    def __init__(self, cartridge_data):
        super().__init__()
        self.cartridge_data = cartridge_data
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants du dialogue"""
        self.setWindowTitle(f"Printer models for {self.cartridge_data['name']}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Label de titre
        title = QLabel(f"Printer models using {self.cartridge_data['name']}:")
        layout.addWidget(title)

        # Liste des modèles
        models = self.cartridge_data.get("printer_model", [])

        if models and models[0] is not None:
            # Créer le tableau des modèles
            table = QTableWidget()
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Model"])
            table.verticalHeader().setVisible(False)
            table.setShowGrid(False)
            table.setSelectionMode(QTableWidget.NoSelection)

            # Configurer la taille des colonnes
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)

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

            # Remplir le tableau
            for i, model in enumerate(models):
                if model:  # Ajouter seulement les valeurs non-nulles
                    table.insertRow(i)
                    item = QTableWidgetItem(model)
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(i, 0, item)
                    table.setRowHeight(i, 34)

            layout.addWidget(table)
        else:
            # Message si aucun modèle trouvé
            no_models = QLabel("No printer models found for this cartridge.")
            layout.addWidget(no_models)

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


class EditStockDialog(QDialog):
    """Dialogue pour modifier le stock d'une cartouche"""

    def __init__(self, cartridge_data, refresh_callback):
        super().__init__()
        self.cartridge_data = cartridge_data
        self.refresh_callback = refresh_callback
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants du dialogue"""
        self.setWindowTitle(f"Edit stock for {self.cartridge_data['name']}")
        self.setMinimumWidth(400)

        layout = QFormLayout()

        # Label de titre
        title = QLabel(f"Updating {self.cartridge_data['name']}")
        layout.addRow(title)

        # Affichage des valeurs actuelles
        current_label = QLabel(
            f"Current Stock: {self.cartridge_data['inStock']} | Min Stock: {self.cartridge_data['minStock']}"
        )
        layout.addRow(current_label)

        # Espacement
        layout.addRow("", QLabel(""))

        # Champ Stock
        self.stock_spinbox = QSpinBox()
        self.stock_spinbox.setMinimum(0)
        self.stock_spinbox.setMaximum(999)
        self.stock_spinbox.setValue(self.cartridge_data['inStock'])
        
        # Contrôles pour augmenter/diminuer le stock
        stock_controls = QHBoxLayout()
        stock_controls.addWidget(self.stock_spinbox, 1)
        
        # Bouton -
        stock_minus = QPushButton("-")
        stock_minus.setMaximumWidth(40)
        stock_minus.setObjectName("adjustButton")
        stock_minus.clicked.connect(lambda: self.stock_spinbox.setValue(max(0, self.stock_spinbox.value() - 1)))
        
        # Bouton +
        stock_plus = QPushButton("+")
        stock_plus.setMaximumWidth(40)
        stock_plus.setObjectName("adjustButton")
        stock_plus.clicked.connect(lambda: self.stock_spinbox.setValue(min(999, self.stock_spinbox.value() + 1)))
        
        stock_controls.addWidget(stock_minus)
        stock_controls.addWidget(stock_plus)
        
        layout.addRow("In stock:", stock_controls)

        # Champ Stock minimum
        self.min_stock_spinbox = QSpinBox()
        self.min_stock_spinbox.setMinimum(0)
        self.min_stock_spinbox.setMaximum(999)
        self.min_stock_spinbox.setValue(self.cartridge_data['minStock'])
        
        # Contrôles pour augmenter/diminuer le stock minimum
        min_stock_controls = QHBoxLayout()
        min_stock_controls.addWidget(self.min_stock_spinbox, 1)
        
        # Bouton -
        min_stock_minus = QPushButton("-")
        min_stock_minus.setMaximumWidth(40)
        min_stock_minus.setObjectName("adjustButton")
        min_stock_minus.clicked.connect(lambda: self.min_stock_spinbox.setValue(max(0, self.min_stock_spinbox.value() - 1)))
        
        # Bouton +
        min_stock_plus = QPushButton("+")
        min_stock_plus.setMaximumWidth(40)
        min_stock_plus.setObjectName("adjustButton")
        min_stock_plus.clicked.connect(lambda: self.min_stock_spinbox.setValue(min(999, self.min_stock_spinbox.value() + 1)))
        
        min_stock_controls.addWidget(min_stock_minus)
        min_stock_controls.addWidget(min_stock_plus)
        
        layout.addRow("Min stock:", min_stock_controls)

        # Boutons OK et Annuler
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.validate_and_save)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

        # Appliquer les styles CSS
        self.setStyleSheet("""
        QSpinBox {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        QSpinBox::up-button {
            width: 0px;
        }

        QSpinBox::down-button {
            width: 0px;
        }

        QPushButton {
            background-color: #0984e3;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            border: none;
        }

        QPushButton:hover {
            background-color: #74b9ff;
        }

        QPushButton#adjustButton {
            background-color: #27ae60;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            border: none;
            min-width: 40px;
            max-width: 40px;
            font-size: 14px;
        }

        QPushButton#adjustButton:hover {
            background-color: #229954;
        }

        QPushButton#adjustButton:pressed {
            background-color: #1e8449;
        }
        """)

    def validate_and_save(self):
        """Valider et sauvegarder les modifications"""
        # Récupérer les nouvelles valeurs
        new_stock = self.stock_spinbox.value()
        new_min_stock = self.min_stock_spinbox.value()

        # Mettre à jour la base de données
        try:
            success = update_cartridge_stock(
                self.cartridge_data['name'],
                new_stock,
                new_min_stock
            )

            # Afficher un message et actualiser si succès
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Stock updated for {self.cartridge_data['name']}"
                )
                # Actualiser le tableau des cartouches
                self.refresh_callback()
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to update stock"
                )

        except Exception as e:
            # Afficher un message d'erreur
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update stock: {str(e)}"
            )
