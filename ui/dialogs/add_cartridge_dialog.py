# ==========================================
# Dialogue pour créer une nouvelle cartouche
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QMessageBox
)


class AddCartridgeDialog(QDialog):
    """Dialogue pour créer une nouvelle cartouche"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Cartridge")
        self.setMinimumWidth(400)
        self.setModal(True)

        self.cartridge_name = None
        self.cartridge_color = None

        layout = QFormLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Nom de la cartouche
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. HP W1490X")
        layout.addRow("Cartridge Name:", self.name_input)

        # Couleur de la cartouche
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Black", "Cyan", "Magenta", "Yellow", "Gray"])
        layout.addRow("Color:", self.color_combo)

        # Stock minimum
        self.minstock_input = QLineEdit()
        self.minstock_input.setText("1")
        self.minstock_input.setPlaceholderText("e.g., 10")
        layout.addRow("Min Stock:", self.minstock_input)

        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

        # Style CSS
        self.setStyleSheet("""
        QDialog {
            background-color: #f5f6fa;
        }

        QFormLayout {
            spacing: 15px;
        }

        QLabel {
            color: #2f3640;
            font-weight: bold;
            font-size: 12px;
        }

        QLineEdit {
            border: 1px solid #dfe6e9;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            color: #2f3640;
            font-size: 11px;
        }

        QLineEdit:focus {
            border: 2px solid #0984e3;
            outline: none;
        }

        QComboBox {
            border: 1px solid #dfe6e9;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            color: #2f3640;
            font-size: 11px;
        }

        QComboBox:focus {
            border: 2px solid #0984e3;
            outline: none;
        }

        QPushButton {
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            background-color: #0984e3;
            color: white;
            font-weight: bold;
            font-size: 11px;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #1c5d99;
        }
        """)

    def validate_and_accept(self):
        """Valider et accepter le dialogue"""
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a cartridge name.",
            )
            return

        if len(name) < 2:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Cartridge name must be at least 2 characters.",
            )
            return

        try:
            minstock = int(self.minstock_input.text())
            if minstock < 1:
                raise ValueError("Must be positive")
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Min stock must be a positive number.",
            )
            return

        self.cartridge_name = name
        self.cartridge_color = self.color_combo.currentText()
        self.accept()

    def get_cartridge_info(self):
        """Retourner les informations de la cartouche créée"""
        return {
            "name": self.cartridge_name,
            "color": self.cartridge_color,
            "minstock": int(self.minstock_input.text())
        }
