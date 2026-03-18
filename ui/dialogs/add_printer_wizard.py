# ==========================================
# Wizard pour ajouter une imprimante
# ==========================================

import ipaddress
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QStackedWidget,
    QMessageBox,
    QInputDialog,
    QHeaderView
)
from PySide6.QtCore import Qt
from database.printers import get_printers, get_printer_models, add_printer_model, delete_printer_model
from database.cartridges import get_cartridges, add_cartridge, delete_cartridge, link_cartridge_to_model
from ui.dialogs.add_cartridge_dialog import AddCartridgeDialog


class AddPrinterWizard(QDialog):
    """
    Wizard pour ajouter une imprimante en plusieurs étapes.
    Page 1: Sélectionner ou créer un modèle
    Page 2 (optionnelle): Gérer les cartouches du nouveau modèle
    Page 3: Remplir les détails de l'imprimante
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Printer - Wizard")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self.setModal(True)

        # Variables d'état
        self.current_page = 0
        self.new_model_name = None
        self.new_model_cartridges = []
        self.new_cartridges = []
        self.selected_model = None
        self.printer_data = {}

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Titre et description
        self.title_label = QLabel()
        self.description_label = QLabel()
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.description_label)

        # Stacked widget pour les pages
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # Créer les pages
        self.page_model = self.create_page_model()
        self.page_cartridges = self.create_page_cartridges()
        self.page_printer = self.create_page_printer()

        self.pages.addWidget(self.page_model)
        self.pages.addWidget(self.page_cartridges)
        self.pages.addWidget(self.page_printer)

        # Boutons de navigation
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        self.btn_prev = QPushButton("< Previous")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_prev.setMinimumWidth(100)

        self.btn_next = QPushButton("Next >")
        self.btn_next.clicked.connect(self.next_page)
        self.btn_next.setMinimumWidth(100)

        self.btn_finish = QPushButton("Finish")
        self.btn_finish.clicked.connect(self.finish)
        self.btn_finish.setMinimumWidth(100)
        self.btn_finish.setVisible(False)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setMinimumWidth(100)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_finish)
        nav_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(nav_layout)
        self.setLayout(main_layout)

        # Appliquer styles
        self.apply_styles()
        
        # Afficher la première page
        self.show_page(0)

    def create_page_model(self):
        """Créer la page 1 : sélectionner ou créer un modèle"""
        page = QWidget()
        layout = QFormLayout()
        layout.setSpacing(15)

        self.model_combo = QComboBox()
        self.model_combo.addItem("Select a model")
        self.model_combo.addItems(get_printer_models())
        layout.addRow("Printer Model:", self.model_combo)

        self.btn_create_model = QPushButton("Create new model")
        self.btn_create_model.setObjectName("secondaryButton")
        self.btn_create_model.clicked.connect(self.create_new_model_inline)
        layout.addRow("", self.btn_create_model)

        page.setLayout(layout)
        return page

    def create_page_cartridges(self):
        """Créer la page 2 : gérer les cartouches du nouveau modèle"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Titre
        title = QLabel("Configure cartridges for the new model")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # Table des cartouches
        self.cartridge_wizard_table = QTableWidget()
        self.cartridge_wizard_table.setColumnCount(1)
        self.cartridge_wizard_table.setHorizontalHeaderLabels(["Cartridge(s)"])
        self.cartridge_wizard_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.cartridge_wizard_table)

        # Boutons pour ajouter/supprimer cartouches
        btn_layout = QHBoxLayout()
        self.btn_add_cartridge_wizard = QPushButton("Add cartridge")
        self.btn_add_cartridge_wizard.clicked.connect(self.add_cartridge_wizard_row)
        self.btn_remove_cartridge_wizard = QPushButton("Remove selected")
        self.btn_remove_cartridge_wizard.clicked.connect(self.remove_cartridge_wizard_row)
        self.btn_create_cartridge_wizard = QPushButton("Create new cartridge")
        self.btn_create_cartridge_wizard.clicked.connect(self.create_new_cartridge_wizard)

        btn_layout.addWidget(self.btn_add_cartridge_wizard)
        btn_layout.addWidget(self.btn_remove_cartridge_wizard)
        btn_layout.addWidget(self.btn_create_cartridge_wizard)
        layout.addLayout(btn_layout)

        # Cartouches disponibles
        self.available_cartridges_wizard = self._load_available_cartridges()

        page.setLayout(layout)
        return page

    def create_page_printer(self):
        """Créer la page 3 : remplir les détails de l'imprimante"""
        page = QWidget()
        layout = QFormLayout()
        layout.setSpacing(15)

        self.wizard_ip = QLineEdit()
        self.wizard_ip.setInputMask("000.000.000.000;_")
        self.wizard_ip.setPlaceholderText("e.g., 10.60.7.1")
        self.wizard_ip.textChanged.connect(self.update_printer_name)
        layout.addRow("IP Address:", self.wizard_ip)

        self.wizard_name = QLineEdit()
        self.wizard_name.setReadOnly(True)
        self.wizard_name.setPlaceholderText("Auto-generated from IP")
        layout.addRow("Printer Name:", self.wizard_name)

        self.wizard_owner = QLineEdit()
        self.wizard_owner.setPlaceholderText("e.g., IT")
        layout.addRow("Owner:", self.wizard_owner)

        page.setLayout(layout)
        return page

    def update_printer_name(self):
        """Mettre à jour le nom de l'imprimante basé sur l'IP"""
        ip = self.wizard_ip.text().strip()
        
        if ip and "." in ip:
            try:
                parts = ip.split(".")
                last_octet = int(parts[-1])
                printer_name = f"BEHGG-Q-{last_octet:06d}"
                self.wizard_name.setText(printer_name)
            except (ValueError, IndexError):
                self.wizard_name.setText("")
        else:
            self.wizard_name.setText("")

    def show_page(self, page_num):
        """Afficher une page spécifique"""
        self.current_page = page_num
        self.pages.setCurrentIndex(page_num)

        titles = ["Step 1: Select Printer Model", "Step 2: Configure Cartridges", "Step 3: Printer Details"]
        descriptions = [
            "Choose an existing model or create a new one",
            "Add cartridges to the new model",
            "Enter printer information"
        ]

        self.title_label.setText(titles[page_num])
        self.description_label.setText(descriptions[page_num])
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.description_label.setStyleSheet("color: #666; font-size: 11px;")

        self.btn_prev.setVisible(page_num > 0)
        self.btn_next.setVisible(page_num < 2)
        self.btn_finish.setVisible(page_num == 2)

    def prev_page(self):
        """Aller à la page précédente avec rollback si nouveau modèle"""
        if self.current_page > 0:
            if self.current_page == 1 and self.new_model_name:
                reply = QMessageBox.warning(
                    self,
                    "Discard Model",
                    f"If you go back, the model '{self.new_model_name}' will be deleted.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                delete_printer_model(self.new_model_name)
                self.model_combo.removeItem(self.model_combo.findText(self.new_model_name))
                self.new_model_name = None
                self.cartridge_wizard_table.setRowCount(0)
            
            self.show_page(self.current_page - 1)

    def next_page(self):
        """Aller à la page suivante"""
        if self.current_page == 0:
            model = self.model_combo.currentText()
            if model == "Select a model":
                QMessageBox.warning(self, "Model required", "Please select or create a model")
                return
            
            self.selected_model = model
            
            if self.new_model_name:
                self.show_page(1)
            else:
                self.show_page(2)
        
        elif self.current_page == 1:
            if self.cartridge_wizard_table.rowCount() == 0:
                QMessageBox.warning(self, "No cartridges", "Please add at least one cartridge")
                return
            
            if self.create_model_with_cartridges():
                self.show_page(2)

    def create_new_model_inline(self):
        """Créer un nouveau modèle"""
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("New Model Name")
        input_dialog.setLabelText("Enter the new printer model name:")
        input_dialog.setOkButtonText("OK")
        input_dialog.setCancelButtonText("Cancel")
        
        line_edit = input_dialog.findChild(QLineEdit)
        if line_edit:
            line_edit.setPlaceholderText("e.g., HP LaserJet Pro 4002dn")
        
        ok = input_dialog.exec()
        model_name = input_dialog.textValue()

        if not ok or not model_name.strip():
            return

        model_name = model_name.strip()

        existing_models = get_printer_models()
        if model_name in existing_models:
            QMessageBox.warning(self, "Error", f"Model '{model_name}' already exists")
            return
        
        self.new_model_name = model_name
        self.model_combo.addItem(model_name)
        self.model_combo.setCurrentText(model_name)
        
        self.cartridge_wizard_table.setRowCount(0)
        self.new_model_cartridges = []
        self.new_cartridges = []
        QMessageBox.information(
            self,
            "Model Name Set",
            f"Model '{model_name}' will be created.\n\nNow add cartridges for this model."
        )
        self.next_page()

    def _load_available_cartridges(self):
        """Charger les cartouches disponibles"""
        cartridges = get_cartridges()
        return [f"{c['name']} ({c['color']})" for c in cartridges]

    def add_cartridge_wizard_row(self):
        """Ajouter une nouvelle ligne de cartouche"""
        row = self.cartridge_wizard_table.rowCount()
        self.cartridge_wizard_table.insertRow(row)

        cartridge_combo = QComboBox()
        cartridge_combo.addItem("Select a cartridge")
        cartridge_combo.addItems(self.available_cartridges_wizard)

        self.cartridge_wizard_table.setCellWidget(row, 0, cartridge_combo)
        self.cartridge_wizard_table.setRowHeight(row, 34)

    def remove_cartridge_wizard_row(self):
        """Supprimer la ligne de cartouche sélectionnée"""
        current_row = self.cartridge_wizard_table.currentRow()
        if current_row >= 0:
            self.cartridge_wizard_table.removeRow(current_row)

    def create_new_cartridge_wizard(self):
        """Créer une nouvelle cartouche"""
        dialog = AddCartridgeDialog(self)

        if dialog.exec():
            cartridge_info = dialog.get_cartridge_info()

            existing_cartridges = get_cartridges()
            existing_names = [c['name'] for c in existing_cartridges]
            
            if cartridge_info['name'] in existing_names:
                QMessageBox.warning(
                    self,
                    "Cartridge Error",
                    f"Cartridge '{cartridge_info['name']}' already exists in the database."
                )
                return

            new_names = [c['name'] for c in self.new_cartridges]
            if cartridge_info['name'] in new_names:
                QMessageBox.warning(
                    self,
                    "Cartridge Error",
                    f"Cartridge '{cartridge_info['name']}' already exists."
                )
                return

            self.new_cartridges.append(cartridge_info)

            display_name = f"{cartridge_info['name']} ({cartridge_info['color']})"

            if display_name not in self.available_cartridges_wizard:
                self.available_cartridges_wizard.append(display_name)

            row = self.cartridge_wizard_table.rowCount()
            self.cartridge_wizard_table.insertRow(row)

            cartridge_combo = QComboBox()
            cartridge_combo.addItem("Select a cartridge")
            cartridge_combo.addItems(self.available_cartridges_wizard)
            cartridge_combo.setCurrentText(display_name)

            self.cartridge_wizard_table.setCellWidget(row, 0, cartridge_combo)
            self.cartridge_wizard_table.setRowHeight(row, 34)

            QMessageBox.information(
                self,
                "Cartridge Queued",
                f"Cartridge '{cartridge_info['name']}' created successfully."
            )

    def create_model_with_cartridges(self):
        """Collecter les cartouches à lier"""
        try:
            cartridges = []
            for row in range(self.cartridge_wizard_table.rowCount()):
                combo_widget = self.cartridge_wizard_table.cellWidget(row, 0)

                if not isinstance(combo_widget, QComboBox):
                    continue

                cartridge_display = combo_widget.currentText()

                if cartridge_display == "Select a cartridge":
                    QMessageBox.warning(
                        self,
                        "Incomplete cartridge",
                        f"Please select a cartridge for row {row + 1}."
                    )
                    return False

                name = cartridge_display.rsplit(" (", 1)[0]

                cartridges.append({"name": name})

            self.new_model_cartridges = cartridges
            return True

        except Exception as e:
            print(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return False

    def finish(self):
        """Terminer le wizard"""
        ip = self.wizard_ip.text().strip()
        name = self.wizard_name.text().strip()
        owner = self.wizard_owner.text().strip()

        if not ip:
            QMessageBox.warning(self, "Missing IP", "Please enter an IP address")
            return

        if not owner:
            QMessageBox.warning(self, "Missing Owner", "Please enter an owner")
            return

        if not name:
            QMessageBox.warning(self, "Invalid IP", "The IP address is invalid")
            return

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            QMessageBox.warning(self, "Invalid IP", "Please enter a valid IP address")
            return

        existing_ips = [p['ip'] for p in get_printers()]
        if ip in existing_ips:
            QMessageBox.warning(
                self,
                "IP Already Exists",
                f"A printer with IP {ip} already exists."
            )
            return

        try:
            if self.new_model_name:
                if not add_printer_model(self.new_model_name):
                    QMessageBox.warning(self, "Model Error", f"Failed to create model")
                    return
                self.selected_model = self.new_model_name
            
            for cartridge_info in self.new_cartridges:
                if not add_cartridge(cartridge_info['name'], cartridge_info['color'], 0, cartridge_info.get("minstock", 1)):
                    QMessageBox.warning(self, "Cartridge Error", f"Failed to create cartridge")
                    if self.new_model_name:
                        delete_printer_model(self.new_model_name)
                    return
            
            if self.new_model_name:
                for cartridge in self.new_model_cartridges:
                    if not link_cartridge_to_model(cartridge["name"], self.new_model_name):
                        QMessageBox.warning(self, "Link Error", f"Failed to link cartridge")
                        delete_printer_model(self.new_model_name)
                        for cart_to_delete in self.new_cartridges:
                            delete_cartridge(cart_to_delete['name'])
                        return
            
            self.printer_data = {
                "ip": ip,
                "name": name,
                "owner": owner,
                "model": self.selected_model
            }

            self.accept()
            
        except Exception as e:
            print(f"Error during finish: {e}")
            QMessageBox.critical(self, "Critical Error", f"An unexpected error occurred: {str(e)}")
            return

    def get_data(self):
        """Retourner les données"""
        return self.printer_data

    def apply_styles(self):
        """Appliquer les styles CSS"""
        self.setStyleSheet("""
        QDialog {
            background-color: #f5f6fa;
        }

        QLabel {
            color: #2f3640;
        }

        QLineEdit, QComboBox {
            border: 1px solid #dfe6e9;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            color: #2f3640;
        }

        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #0984e3;
        }

        QPushButton {
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            background-color: #0984e3;
            color: white;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton#secondaryButton {
            background-color: #6c5ce7;
        }

        QPushButton#secondaryButton:hover {
            background-color: #a29bfe;
        }
        """)
