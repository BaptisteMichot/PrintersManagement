# ==========================================
# Dialog Formulaire de Commande
# Permet de créer une nouvelle commande avec saisie manuelle
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
    QFileDialog,
    QFrame,
    QScrollArea,
    QWidget,
    QCheckBox
)

from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from utils.excel_export import export_order_to_excel


class OrderLineWidget(QWidget):
    """Widget pour une ligne de commande avec saisie manuelle"""
    
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.setMaximumWidth(30)
        layout.addWidget(self.checkbox, 0)
        
        # Cartridge Type
        self.cartridge_type_input = QLineEdit()
        self.cartridge_type_input.setPlaceholderText("e.g., HP W1490X")
        self.cartridge_type_input.textChanged.connect(self.on_value_changed)
        layout.addWidget(self.cartridge_type_input, 1)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Cartridge description")
        self.description_input.textChanged.connect(self.on_value_changed)
        layout.addWidget(self.description_input, 2)
        
        layout.addStretch()
        
        # Quantity container (label + input) - Fixed width
        qty_container = QWidget()
        qty_container.setMinimumWidth(100)
        qty_container.setMaximumWidth(100)
        qty_layout = QHBoxLayout()
        qty_layout.setContentsMargins(0, 0, 0, 0)
        qty_layout.setSpacing(10)
        qty_layout.addWidget(QLabel("Qty:"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("0")
        self.quantity_input.setMaximumWidth(40)
        self.quantity_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d*$")))
        self.quantity_input.textChanged.connect(self.on_value_changed)
        qty_layout.addWidget(self.quantity_input)
        qty_container.setLayout(qty_layout)
        layout.addWidget(qty_container, 0)
        
        # Price container (label + input) - Fixed width
        price_container = QWidget()
        price_container.setMinimumWidth(140)
        price_container.setMaximumWidth(140)
        price_layout = QHBoxLayout()
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(10)
        price_layout.addWidget(QLabel("Price:"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("0.00")
        self.price_input.setMaximumWidth(70)
        self.price_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d+(\.\d{0,2})?$")))
        self.price_input.textChanged.connect(self.on_value_changed)
        price_layout.addWidget(self.price_input)
        price_container.setLayout(price_layout)
        layout.addWidget(price_container, 0)
        
        # Total container (label + total_label) - Fixed width
        total_container = QWidget()
        total_container.setMinimumWidth(110)
        total_container.setMaximumWidth(110)
        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(0, 0, 0, 0)
        total_layout.setSpacing(10)
        total_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("0.00")
        self.total_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_layout.addWidget(self.total_label)
        total_container.setLayout(total_layout)
        layout.addWidget(total_container, 0)
        
        self.setLayout(layout)
    
    def on_value_changed(self):
        """Recalculer le total de la ligne"""
        try:
            quantity = float(self.quantity_input.text()) if self.quantity_input.text() else 0.0
            price = float(self.price_input.text()) if self.price_input.text() else 0.0
            total = quantity * price
            self.total_label.setText(f"{total:.2f}")
        except ValueError:
            self.total_label.setText("0.00")
    
    def is_empty(self):
        """Vérifier si la ligne est vide"""
        return (self.cartridge_type_input.text().strip() == "" and
                self.description_input.text().strip() == "" and 
                self.quantity_input.text().strip() == "" and 
                self.price_input.text().strip() == "")
    
    def get_data(self):
        """Récupérer les données de la ligne"""
        try:
            quantity = float(self.quantity_input.text()) if self.quantity_input.text() else 0.0
            price = float(self.price_input.text()) if self.price_input.text() else 0.0
            total = quantity * price
        except ValueError:
            quantity = 0.0
            price = 0.0
            total = 0.0
        
        return {
            'cartridge_type': self.cartridge_type_input.text().strip(),
            'description': self.description_input.text().strip(),
            'quantity': quantity,
            'unit_price': price,
            'total': total
        }


class OrderFormDialog(QDialog):
    """
    Dialog pour créer une nouvelle commande avec saisie manuelle.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Order")
        self.setGeometry(100, 100, 1100, 700)
        self.order_lines = []
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants du dialog"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Section Informations de la commande
        info_layout = QHBoxLayout()
        
        # Purchase Order Number
        info_layout.addWidget(QLabel("Purchase Order Number:"))
        self.po_number_input = QLineEdit()
        self.po_number_input.setPlaceholderText("e.g., RO4315")
        self.po_number_input.setMaximumWidth(150)
        info_layout.addWidget(self.po_number_input)
        
        # Date
        info_layout.addWidget(QLabel("Date:"))
        self.date_input = QLineEdit()
        today = QDate.currentDate().toString("dd/MM/yyyy")
        self.date_input.setText(today)
        self.date_input.setMaximumWidth(120)
        info_layout.addWidget(self.date_input)
        
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout)

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator)

        # Section Destinataire (commenté - ces informations sont fixes sur le modèle)
        # recipient_layout = QHBoxLayout()
        # recipient_layout.addWidget(QLabel("Recipient:"))
        # self.recipient_input = QLineEdit()
        # self.recipient_input.setPlaceholderText("e.g., Discorp NV")
        # recipient_layout.addWidget(self.recipient_input)
        # 
        # recipient_layout.addWidget(QLabel("Contact:"))
        # self.contact_input = QLineEdit()
        # self.contact_input.setPlaceholderText("e.g., Ibrahima DIARRA")
        # recipient_layout.addWidget(self.contact_input)
        # 
        # main_layout.addLayout(recipient_layout)

        # Séparateur

        # Séparateur
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator2)

        # Section Lignes de commande
        lines_label = QLabel("Order Lines:")
        lines_font = QFont()
        lines_font.setBold(True)
        lines_label.setFont(lines_font)
        main_layout.addWidget(lines_label)

        # Headers pour les colonnes
        headers_layout = QHBoxLayout()
        headers_layout.setSpacing(10)
        headers_layout.setContentsMargins(0, 0, 0, 0)
        
        headers_layout.addWidget(QLabel("Cartridge Type"), 1)
        headers_layout.addWidget(QLabel("Description"), 2)
        headers_layout.addStretch()
        
        # Qty header - Fixed width
        qty_header = QWidget()
        qty_header.setMinimumWidth(100)
        qty_header.setMaximumWidth(100)
        qty_header_layout = QHBoxLayout()
        qty_header_layout.setContentsMargins(0, 0, 0, 0)
        qty_header_layout.setSpacing(10)
        qty_header_layout.addWidget(QLabel("Qty:"))
        qty_spacer = QWidget()
        qty_spacer.setMaximumWidth(40)
        qty_header_layout.addWidget(qty_spacer)
        qty_header.setLayout(qty_header_layout)
        headers_layout.addWidget(qty_header, 0)
        
        # Price EUR header - Fixed width
        price_header = QWidget()
        price_header.setMinimumWidth(140)
        price_header.setMaximumWidth(140)
        price_header_layout = QHBoxLayout()
        price_header_layout.setContentsMargins(0, 0, 0, 0)
        price_header_layout.setSpacing(10)
        price_header_layout.addWidget(QLabel("Price:"))
        price_spacer = QWidget()
        price_spacer.setMaximumWidth(70)
        price_header_layout.addWidget(price_spacer)
        price_header.setLayout(price_header_layout)
        headers_layout.addWidget(price_header, 0)
        
        # Total header - Fixed width
        total_header = QWidget()
        total_header.setMinimumWidth(110)
        total_header.setMaximumWidth(110)
        total_header_layout = QHBoxLayout()
        total_header_layout.setContentsMargins(0, 0, 0, 0)
        total_header_layout.setSpacing(10)
        total_header_layout.addWidget(QLabel("Total:"))
        total_spacer = QWidget()
        total_spacer.setMaximumWidth(50)
        total_header_layout.addWidget(total_spacer)
        total_header.setLayout(total_header_layout)
        headers_layout.addWidget(total_header, 0)
        
        main_layout.addLayout(headers_layout)

        # ScrollArea pour les lignes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dfe6e9;
                border-radius: 4px;
            }
        """)
        
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # Créer 1 ligne vide au départ
        for i in range(1):
            line_widget = OrderLineWidget()
            self.order_lines.append(line_widget)
            self.scroll_layout.addWidget(line_widget)
            line_widget.quantity_input.textChanged.connect(self.calculate_grand_total)
            line_widget.price_input.textChanged.connect(self.calculate_grand_total)
        
        self.scroll_layout.addStretch()
        scroll_widget.setLayout(self.scroll_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Layout pour les boutons Add Line et Remove
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        add_line_button = QPushButton("Add Line")
        add_line_button.setObjectName("mainButton")
        add_line_button.setMaximumWidth(120)
        add_line_button.clicked.connect(self.add_line)
        buttons_layout.addWidget(add_line_button)

        remove_selected_button = QPushButton("Remove")
        remove_selected_button.setObjectName("mainButton")
        remove_selected_button.setMaximumWidth(120)
        remove_selected_button.clicked.connect(self.remove_selected)
        buttons_layout.addWidget(remove_selected_button)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # Séparateur
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator3)

        # Section Totaux
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        
        totals_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("0.00 EUR")
        total_font = QFont()
        total_font.setBold(True)
        total_font.setPointSize(11)
        self.total_label.setFont(total_font)
        self.total_label.setStyleSheet("color: #0984e3; min-width: 100px;")
        self.total_label.setAlignment(Qt.AlignVCenter)
        totals_layout.addWidget(self.total_label)
        
        main_layout.addLayout(totals_layout)

        # Boutons d'action
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("Generate Excel")
        export_button.setObjectName("mainButton")
        export_button.clicked.connect(self.generate_excel)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("mainButton")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(export_button)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)

        # Appliquer les styles CSS
        self.setStyleSheet("""
        QDialog {
            background-color: #f5f6fa;
        }

        QPushButton#mainButton {
            background-color: #0984e3;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            border: none;
        }

        QPushButton#mainButton:hover {
            background-color: #74b9ff;
        }

        QPushButton#secondaryButton {
            background-color: #95a5a6;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            border: none;
        }

        QPushButton#secondaryButton:hover {
            background-color: #bdc3c7;
        }

        QLineEdit {
            padding: 6px;
            border: 1px solid #dfe6e9;
            border-radius: 4px;
            background: white;
        }

        QSpinBox, QDoubleSpinBox {
            padding: 4px;
            border: 1px solid #dfe6e9;
            border-radius: 4px;
            background: white;
        }
        """)

        self.setLayout(main_layout)

    def calculate_grand_total(self):
        """Calculer le grand total de la commande"""
        grand_total = 0.0
        
        for line in self.order_lines:
            grand_total += line.get_data()['total']
        
        self.total_label.setText(f"{grand_total:.2f} EUR")

    def add_line(self):
        """Ajouter une nouvelle ligne de commande"""
        line_widget = OrderLineWidget()
        self.order_lines.append(line_widget)
        
        # Connecter les signaux
        line_widget.quantity_input.textChanged.connect(self.calculate_grand_total)
        line_widget.price_input.textChanged.connect(self.calculate_grand_total)
        
        # Insérer avant le stretch (qui est le dernier item)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, line_widget)

    def remove_selected(self):
        """Supprimer les lignes sélectionnées"""
        lines_to_remove = []
        
        # Trouvez toutes les lignes cochées
        for line in self.order_lines:
            if line.checkbox.isChecked():
                lines_to_remove.append(line)
        
        # Vérifier qu'au moins une ligne est sélectionnée
        if len(lines_to_remove) == 0:
            QMessageBox.warning(self, "Warning", "Please select at least one line to remove.")
            return
        
        # Vérifier qu'il reste au moins une ligne
        if len(lines_to_remove) == len(self.order_lines):
            QMessageBox.warning(self, "Warning", "You must keep at least one line.")
            return
        
        # Supprimer les lignes sélectionnées
        for line in lines_to_remove:
            self.order_lines.remove(line)
            line.deleteLater()
        
        self.calculate_grand_total()

    def get_order_data(self):
        """Récupérer les données de la commande"""
        order_lines = []
        
        for line in self.order_lines:
            data = line.get_data()
            # Ne garder que les lignes non vides
            if data['description'] or data['quantity'] > 0 or data['unit_price'] > 0:
                order_lines.append(data)
        
        return {
            'po_number': self.po_number_input.text() or "N/A",
            'date': self.date_input.text(),
            'lines': order_lines,
            'total': float(self.total_label.text().split()[0])
        }

    def generate_excel(self):
        """Générer et sauvegarder l'Excel"""
        # Valider PO Number
        if not self.po_number_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a PO Number.")
            return

        # Valider Date
        if not self.date_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a Date.")
            return

        # Vérifier qu'au moins une ligne est remplie et que tous les champs obligatoires sont présents
        has_complete_lines = False
        incomplete_lines = []
        invalid_quantity_lines = []
        
        for idx, line in enumerate(self.order_lines, 1):
            if line.is_empty():
                continue
            
            # Vérifier que tous les champs sont remplis
            cartridge_type = line.cartridge_type_input.text().strip()
            description = line.description_input.text().strip()
            quantity = line.quantity_input.text().strip()
            price = line.price_input.text().strip()
            
            if not cartridge_type or not description or not quantity or not price:
                incomplete_lines.append(idx)
            else:
                # Vérifier que la quantité est > 0
                try:
                    qty_value = float(quantity)
                    if qty_value <= 0:
                        invalid_quantity_lines.append(idx)
                    else:
                        has_complete_lines = True
                except ValueError:
                    incomplete_lines.append(idx)
        
        # Afficher les erreurs de quantité invalide
        if invalid_quantity_lines:
            line_numbers = ", ".join(str(n) for n in invalid_quantity_lines)
            QMessageBox.warning(
                self, 
                "Validation Error", 
                f"Quantity must be greater than 0 for line(s): {line_numbers}"
            )
            return
        
        # Afficher les erreurs de champs manquants
        if incomplete_lines:
            line_numbers = ", ".join(str(n) for n in incomplete_lines)
            QMessageBox.warning(
                self, 
                "Validation Error", 
                f"Please fill in all fields for line(s): {line_numbers}\n\nAll fields are required: Cartridge Type, Description, Qty, and Price."
            )
            return
        
        if not has_complete_lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one complete order line with all fields filled.")
            return

        # Demander le chemin de sauvegarde
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Order Excel",
            f"Order_{self.po_number_input.text()}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            order_data = self.get_order_data()
            export_order_to_excel(order_data, file_path)
            QMessageBox.information(self, "Success", f"Order Excel generated successfully!\n\n{file_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating Excel:\n{str(e)}")
