# ==========================================
# Dialogue pour créer un nouveau modèle d'imprimante
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
    QHeaderView
)

from database.printers import add_printer_model, delete_printer_model
from database.cartridges import add_cartridge, link_cartridge_to_model, get_cartridges
from ui.dialogs.add_cartridge_dialog import AddCartridgeDialog


class CreatePrinterModelDialog(QDialog):
    """Dialogue pour créer un nouveau modèle d'imprimante avec ses cartouches."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create new printer model")
        self.setMinimumWidth(500)
        self.model_name = None
        self.cartridges = []
        self.available_cartridges = self._load_available_cartridges()
        self.init_ui()

    def _load_available_cartridges(self):
        """Charger la liste des cartouches disponibles depuis la DB"""
        try:
            cartridges = get_cartridges()
            return [f"{c['name']} ({c['color']})" for c in cartridges]
        except:
            return []

    def init_ui(self):
        """Initialiser les composants du dialogue"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Section 1: Nom du modèle
        form_layout = QFormLayout()
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("e.g. HP LaserJet Pro 4002dn")
        form_layout.addRow("Model name:", self.model_input)
        layout.addLayout(form_layout)

        # Section 2: Cartouches
        title = QLabel("Cartridges for this model:")
        layout.addWidget(title)

        # Tableau des cartouches
        self.cartridge_table = QTableWidget()
        self.cartridge_table.setColumnCount(2)
        self.cartridge_table.setHorizontalHeaderLabels(["Cartridge", "Min Stock"])
        self.cartridge_table.verticalHeader().setVisible(False)
        self.cartridge_table.setShowGrid(False)
        self.cartridge_table.setSelectionMode(QTableWidget.SingleSelection)
        
        header = self.cartridge_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.cartridge_table)

        # Boutons pour gérer les cartouches
        cartridge_buttons = QHBoxLayout()
        
        self.add_cartridge_btn = QPushButton("Add cartridge")
        self.add_cartridge_btn.setObjectName("secondaryButton")
        self.add_cartridge_btn.clicked.connect(self.add_cartridge_row)
        
        self.create_cartridge_btn = QPushButton("Create new cartridge")
        self.create_cartridge_btn.setObjectName("secondaryButton")
        self.create_cartridge_btn.clicked.connect(self.create_new_cartridge)
        
        self.remove_cartridge_btn = QPushButton("Remove selected")
        self.remove_cartridge_btn.setObjectName("secondaryButton")
        self.remove_cartridge_btn.clicked.connect(self.remove_cartridge_row)
        
        cartridge_buttons.addWidget(self.add_cartridge_btn)
        cartridge_buttons.addWidget(self.create_cartridge_btn)
        cartridge_buttons.addWidget(self.remove_cartridge_btn)
        cartridge_buttons.addStretch()
        layout.addLayout(cartridge_buttons)

        # Boutons OK et Annuler
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.apply_styles()

    def add_cartridge_row(self):
        """Ajouter une nouvelle ligne de cartouche à partir des existantes"""
        row = self.cartridge_table.rowCount()
        self.cartridge_table.insertRow(row)
        
        # ComboBox pour sélectionner une cartouche existante
        cartridge_combo = QComboBox()
        cartridge_combo.addItem("Select a cartridge")
        cartridge_combo.addItems(self.available_cartridges)
        
        # Stock minimum (défaut 5)
        minstock_item = QTableWidgetItem()
        minstock_item.setText("5")
        
        self.cartridge_table.setCellWidget(row, 0, cartridge_combo)
        self.cartridge_table.setItem(row, 1, minstock_item)
        self.cartridge_table.setRowHeight(row, 34)

    def create_new_cartridge(self):
        """Ouvrir le dialogue pour créer une nouvelle cartouche"""
        dialog = AddCartridgeDialog()
        
        if dialog.exec():
            # Récupérer les données de la nouvelle cartouche
            cartridge_info = dialog.get_cartridge_info()
            
            # Créer la cartouche dans la DB
            if not add_cartridge(cartridge_info['name'], cartridge_info['color'], 0, cartridge_info.get("minstock", 5)):
                QMessageBox.warning(
                    self,
                    "Cartridge Error",
                    f"Cartridge '{cartridge_info['name']}' already exists in the database."
                )
                return
            
            # Ajouter au format "name (color)"
            display_name = f"{cartridge_info['name']} ({cartridge_info['color']})"
            
            # Ajouter à la liste disponible
            if display_name not in self.available_cartridges:
                self.available_cartridges.append(display_name)
            
            # Ajouter une nouvelle ligne avec cette cartouche sélectionnée
            row = self.cartridge_table.rowCount()
            self.cartridge_table.insertRow(row)
            
            # ComboBox avec la nouvelle cartouche sélectionnée
            cartridge_combo = QComboBox()
            cartridge_combo.addItem("Select a cartridge")
            cartridge_combo.addItems(self.available_cartridges)
            cartridge_combo.setCurrentText(display_name)
            
            # Stock minimum
            minstock_item = QTableWidgetItem()
            minstock_item.setText(str(cartridge_info.get("minstock", 5)))
            
            self.cartridge_table.setCellWidget(row, 0, cartridge_combo)
            self.cartridge_table.setItem(row, 1, minstock_item)
            self.cartridge_table.setRowHeight(row, 34)
            
            QMessageBox.information(
                self,
                "Cartridge Created",
                f"Cartridge '{cartridge_info['name']}' has been created and added to the model."
            )

    def remove_cartridge_row(self):
        """Supprimer la ligne de cartouche sélectionnée"""
        current_row = self.cartridge_table.currentRow()
        if current_row >= 0:
            self.cartridge_table.removeRow(current_row)

    def validate_and_accept(self):
        """Valider les données avant d'ajouter à la base de données"""
        model_name = self.model_input.text().strip()
        
        if not model_name:
            QMessageBox.warning(
                self,
                "Missing model name",
                "Please enter a printer model name."
            )
            return

        if self.cartridge_table.rowCount() == 0:
            QMessageBox.warning(
                self,
                "No cartridges",
                "Please add at least one cartridge."
            )
            return

        # Collecter les données des cartouches depuis les ComboBox
        cartridges = []
        for row in range(self.cartridge_table.rowCount()):
            combo_widget = self.cartridge_table.cellWidget(row, 0)
            minstock_item = self.cartridge_table.item(row, 1)
            
            if not isinstance(combo_widget, QComboBox):
                continue
            
            cartridge_display = combo_widget.currentText()
            
            if cartridge_display == "Select a cartridge":
                QMessageBox.warning(
                    self,
                    "Incomplete cartridge",
                    f"Please select a cartridge for row {row + 1}."
                )
                return
            
            # Parser "NAME (COLOR)" pour extraire le nom
            try:
                name = cartridge_display.rsplit(" (", 1)[0]
                minstock = int(minstock_item.text()) if minstock_item else 5
            except (ValueError, IndexError):
                minstock = 5
            
            cartridges.append({
                "name": name,
                "minstock": minstock
            })

        # Sauveg arder les données et lier dans la base
        if self.create_in_database(model_name, cartridges):
            self.model_name = model_name
            self.cartridges = cartridges
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Database error",
                "Failed to create model and link cartridges. Model may already exist."
            )

    def create_in_database(self, model_name, cartridges):
        """Créer le modèle et lier les cartouches existantes à la base de données"""
        try:
            # 1. Créer le modèle
            if not add_printer_model(model_name):
                QMessageBox.warning(
                    self,
                    "Model already exists",
                    f"Model '{model_name}' already exists in the database."
                )
                return False
            
            # 2. Lier les cartouches existantes au modèle
            for i, cartridge in enumerate(cartridges):
                # Lier la cartouche au modèle
                if not link_cartridge_to_model(cartridge["name"], model_name):
                    # ERREUR : erreur de lien (cartouche n'existe pas ou autre problème)
                    # Rollback COMPLET : supprimer le modèle
                    delete_printer_model(model_name)
                    QMessageBox.warning(
                        self,
                        "Link error",
                        f"Cartridge '{cartridge['name']}' not found or failed to link to model '{model_name}'.\nModel creation has been rolled back."
                    )
                    return False
            
            QMessageBox.information(
                self,
                "Success",
                f"Model '{model_name}' with {len(cartridges)} cartridge(s) has been created successfully!"
            )
            return True
            
        except Exception as e:
            print(f"Error creating model: {e}")
            # Rollback COMPLET en cas d'exception
            try:
                delete_printer_model(model_name)
            except:
                pass
            QMessageBox.critical(
                self,
                "Critical error",
                f"An unexpected error occurred: {str(e)}\nModel creation has been rolled back."
            )
            return False

    def get_model_name(self):
        """Retourner le nom du modèle créé"""
        return self.model_name

    def apply_styles(self):
        """Appliquer les styles CSS"""
        self.setStyleSheet("""
        QPushButton#secondaryButton {
            background-color: #6c5ce7;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }
        
        QPushButton#secondaryButton:hover {
            background-color: #a29bfe;
        }
        
        QTableWidget {
            background: white;
            border-radius: 8px;
            font-size: 12px;
            padding: 6px;
        }
        
        QHeaderView::section {
            background-color: #f1f2f6;
            padding: 8px;
            border: none;
            font-weight: bold;
            font-size: 12px;
        }
        """)
