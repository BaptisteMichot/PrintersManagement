# ==========================================
# Dialogue pour ajouter une imprimante
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QDialogButtonBox,
    QMessageBox
)

from database.printers import get_printer_models, add_printer_model
from utils.validators import validate_ip


class AddPrinterDialog(QDialog):
    """Dialogue pour ajouter une nouvelle imprimante."""

    selection = "Select a model"

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add printer")

        # Créer le formulaire
        layout = QFormLayout()

        # Champs du formulaire
        self.name = QLineEdit()
        self.owner = QLineEdit()
        self.model = QComboBox()
        self.model.addItem(self.selection)
        self.model.addItems(get_printer_models())
        self.model.setCurrentIndex(0)
        self.ip = QLineEdit()
        self.ip.setInputMask("000.000.000.000;_")

        # Ajouter les champs au formulaire
        layout.addRow("IP:", self.ip)
        layout.addRow("Printer name:", self.name)
        layout.addRow("User:", self.owner)
        layout.addRow("Model:", self.model)

        # Bouton pour créer un nouveau modèle
        self.create_model_button = QPushButton("Create new model")
        self.create_model_button.setObjectName("secondaryButton")
        self.create_model_button.clicked.connect(self.create_new_model)
        layout.addRow("", self.create_model_button)

        # Ajouter les boutons OK et Annuler
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

    def create_new_model(self):
        """Ouvrir le dialogue de création d'un nouveau modèle d'imprimante"""
        from ui.dialogs.create_model_dialog import CreatePrinterModelDialog
        
        create_dialog = CreatePrinterModelDialog()
        
        if create_dialog.exec():
            # Ajouter le nouveau modèle à la combo box
            new_model = create_dialog.get_model_name()
            self.model.addItem(new_model)
            self.model.setCurrentText(new_model)

    def get_data(self):
        """Récupérer les données du formulaire."""
        return {
            "name": self.name.text().strip(),
            "owner": self.owner.text().strip(),
            "model": self.model.currentText(),
            "ip": self.ip.text().strip()
        }
    
    def validate(self):
        """Valider les données avant de fermer le dialogue."""
        # Récupérer les données
        name = self.name.text().strip()
        owner = self.owner.text().strip()
        model = self.model.currentText()
        ip = self.ip.text().strip()

        # Vérifier que tous les champs sont remplis
        if not name or not owner or not ip:
            QMessageBox.warning(
                self,
                "Missing information",
                "All fields must be filled."
            )
            return

        # Vérifier qu'un modèle valide est sélectionné
        if model == self.selection:
            QMessageBox.warning(
                self,
                "Model required",
                "Please select a printer model."
            )
            return

        # Valider le format de l'IP
        if not validate_ip(ip):
            QMessageBox.warning(
                self,
                "Invalid IP",
                "Please enter a valid IP address."
            )
            return

        # Fermer le dialogue avec succès
        self.accept()
