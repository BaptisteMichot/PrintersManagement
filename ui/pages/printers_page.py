# ==========================================
# Page Imprimantes
# Gère l'affichage et l'interaction avec les imprimantes
# ==========================================

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QHeaderView,
    QHBoxLayout,
    QSizePolicy,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QLabel,
    QStackedWidget,
    QInputDialog
)

from PySide6.QtCore import QThread, Signal, Qt, QSize, QTimer
from services.ink_scanner import run_scanner
from database.printers import add_printer, get_printer_models, delete_printer, get_cartridges_for_printer, add_printer_model, delete_printer_model
from database.cartridges import add_cartridge, link_cartridge_to_model, delete_cartridge, get_cartridges
import ipaddress
from PySide6.QtGui import QIcon


class ScanWorker(QThread):
    """Thread worker pour scanner les imprimantes sur le réseau"""

    # Signal émis quand le scan est terminé
    finished = Signal(dict)

    def run(self):
        """Exécuter le scan des imprimantes en arrière-plan"""
        # Appeler la fonction de scan
        results = run_scanner()

        # Retourner un dictionnaire vide si le scan a échoué
        if results is None:
            results = {}

        # Émettre le signal avec les résultats
        self.finished.emit(results)


class PrintersPage(QWidget):
    """
    Page de gestion des imprimantes.
    Permet de scanner les imprimantes, afficher leurs niveaux d'encre,
    ajouter et supprimer des imprimantes.
    """

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Barre supérieure avec boutons d'action
        top_bar = QHBoxLayout()

        # Bouton Scan
        self.button = QPushButton("Scan printers")
        self.button.setObjectName("mainButton")
        self.button.clicked.connect(self.scan)

        # Bouton Ajouter
        self.add_button = QPushButton("Add printer")
        self.add_button.setObjectName("mainButton")
        self.add_button.clicked.connect(self.open_add_dialog)

        # Bouton Supprimer
        self.delete_button = QPushButton("Delete printer")
        self.delete_button.setObjectName("mainButton")
        self.delete_button.setVisible(False)
        self.delete_button.clicked.connect(self.delete_selected_printer)

        # Bouton Voir les cartouches
        self.view_cartridges_button = QPushButton("View cartridges")
        self.view_cartridges_button.setObjectName("mainButton")
        self.view_cartridges_button.setVisible(False)
        self.view_cartridges_button.clicked.connect(self.show_printer_cartridges)

        top_bar.addWidget(self.button)
        top_bar.addWidget(self.add_button)
        top_bar.addWidget(self.delete_button)
        top_bar.addWidget(self.view_cartridges_button)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # Tableau des imprimantes
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "",
            "IP",
            "Printer",
            "User",
            "Black",
            "Cyan",
            "Magenta",
            "Yellow"
        ])

        # Configuration du tableau
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)

        header = self.table.horizontalHeader()

        # Colonne checkbox (taille fixe)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # Colonnes texte (taille fixe)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Colonnes encre (prennent toute la place restante)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)

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
            background: transparent;
            color: black;
        }

        """)

        layout.addWidget(self.table)

        self.setLayout(layout)

        # Appliquer les styles à la page
        self.setStyleSheet("""

        /* boutons principaux */

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
                           
        QPushButton#deleteButton {
            border: none;
            background: transparent;
        }

        QPushButton#deleteButton:hover {
            background-color: #ffe6e6;
            border-radius: 6px;
        }

        QPushButton#deleteButton:pressed {
            background-color: #ffcccc;
        }

        """)

    def create_bar(self, value, color):
        """
        Crée une barre de progression pour afficher le niveau d'encre/toner.
        
        Args:
            value (int): Pourcentage de remplissage (0-100)
            color (str): Couleur hexadécimale de la barre
            
        Returns:
            QWidget: Widget contenant la barre de progression
        """
        value = int(value or 0)

        # Créer la barre de progression
        bar = QProgressBar()
        bar.setValue(value)
        bar.setTextVisible(True)
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bar.setFixedHeight(18)

        # Définir le texte à afficher
        text = "" if value == 0 else f"{value}%"

        # Choisir la couleur du texte en fonction de la couleur et de la valeur
        text_color = "black"

        if color == "#000000" and value >= 50:
            text_color = "white"

        bar.setFormat(text)

        # Appliquer les styles CSS
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 6px;
                background-color: #ecf0f1;
                text-align: center;
                color: {text_color};
                font-weight: bold;
            }}

            QProgressBar::chunk {{
                border-radius: 6px;
                background-color: {color};
            }}
        """)

        # Créer un conteneur pour la barre
        container = QWidget()

        layout = QHBoxLayout(container)
        layout.addWidget(bar)

        # Supprimer les marges (IMPORTANT pour l'affichage dans les cellules du tableau)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        return container

    def scan(self):
        """
        Lancer un scan des imprimantes sur le réseau.
        Exécute le scan en arrière-plan et affiche une boîte de progression.
        """
        # Désactiver le bouton scan
        self.button.setEnabled(False)

        # Créer et afficher le dialogue de progression
        self.progress_dialog = ScanProgressDialog(self)
        
        # Créer et configurer le worker du thread
        self.worker = ScanWorker()
        self.worker.finished.connect(self.scan_finished)
        self.worker.finished.connect(self.progress_dialog.accept)

        # Démarrer le scan en arrière-plan
        self.worker.start()
        self.progress_dialog.exec()

    def _ip_sort_key(self, ip: str):
        """
        Créer une clé de tri pour les adresses IP (tri numérique).
        
        Args:
            ip (str): Adresse IP à trier
            
        Returns:
            tuple: Tuple de nombres pour le tri correct
        """
        parts = []

        # Convertir chaque partie de l'IP en nombre
        for part in str(ip).strip().split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(float('inf'))

        # Remplir avec des 0 si nécessaire
        while len(parts) < 4:
            parts.append(0)

        return tuple(parts)

    def scan_finished(self, results):
        """
        Appelé quand le scan des imprimantes est terminé.
        Remplit le tableau avec les résultats du scan.
        
        Args:
            results (dict): Dictionnaire avec les résultats du scan
        """
        # Vider le tableau
        self.table.setRowCount(0)

        row = 0

        # Parcourir les résultats triés par IP
        for ip, data in sorted(results.items(), key=lambda item: self._ip_sort_key(item[0])):

            # Extraire les informations
            info = data.get("info", {})
            consumables = data.get("consumables", [])

            # Utiliser les données de la base ou celles scannées
            name = data.get("db_name") or info.get("name") or ""
            user = data.get("db_owner") or info.get("user") or ""
            model = data.get("db_model") or ""

            # Initialiser les niveaux d'encre
            levels = {
                "Black": 0,
                "Cyan": 0,
                "Magenta": 0,
                "Yellow": 0
            }

            # Remplir les niveaux d'encre à partir de consumables
            for c in consumables:

                try:
                    color, ref, percent_text, percent_value, color_name = c
                except:
                    continue

                if color_name in levels:
                    levels[color_name] = int(percent_value or 0)

            # Ajouter une nouvelle ligne au tableau
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

            # Ajouter les items du tableau
            ip_item = QTableWidgetItem(ip or "")
            name_item = QTableWidgetItem(name)
            user_item = QTableWidgetItem(user)

            ip_item.setTextAlignment(Qt.AlignCenter)
            
            # Stocker le modèle et l'IP comme attributs pour utilisation ultérieure
            name_item.model = model
            name_item.ip = ip

            self.table.setItem(row, 1, ip_item)
            self.table.setItem(row, 2, name_item)
            self.table.setItem(row, 3, user_item)

            # Ajouter les barres de progression pour les niveaux d'encre
            self.table.setCellWidget(row, 4, self.create_bar(levels["Black"], "#000000"))
            self.table.setCellWidget(row, 5, self.create_bar(levels["Cyan"], "#00aeef"))
            self.table.setCellWidget(row, 6, self.create_bar(levels["Magenta"], "#ec008c"))
            self.table.setCellWidget(row, 7, self.create_bar(levels["Yellow"], "#ffd100"))

            # Définir la hauteur de la ligne
            self.table.setRowHeight(row, 34)

            row += 1

        # Réactiver le bouton scan et afficher les boutons supplémentaires
        self.button.setEnabled(True)
        self.delete_button.setVisible(True)
        self.view_cartridges_button.setVisible(True)

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

    def delete_selected_printer(self):
        """Supprimer l'imprimante sélectionnée"""
        # Trouver la checkbox cochée
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break
        
        # Afficher un warning si aucune imprimante n'est sélectionnée
        if checked_row is None:
            QMessageBox.warning(self, "No selection", "Please select a printer to delete")
            return

        # Récupérer l'IP de la ligne sélectionnée
        ip = self.table.item(checked_row, 1).text()
        self.confirm_delete(ip)

    def show_printer_cartridges(self):
        """Afficher les cartouches compatibles avec l'imprimante sélectionnée"""
        # Trouver la checkbox cochée
        checked_row = None
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                checked_row = row
                break
        
        # Afficher un warning si aucune imprimante n'est sélectionnée
        if checked_row is None:
            QMessageBox.warning(self, "No selection", "Please select a printer")
            return

        # Récupérer les info de l'imprimante depuis la ligne sélectionnée
        ip = self.table.item(checked_row, 1).text()
        name_item = self.table.item(checked_row, 2)
        model = name_item.model

        # Afficher le dialogue avec les cartouches
        dialog = PrinterCartridgesDialog(ip, model)
        dialog.exec()

    def add_printer_to_db(self, data):
        """
        Ajouter une imprimante à la base de données.
        
        Args:
            data (dict): Dictionnaire avec les données de l'imprimante
        """
        # Appeler la fonction d'ajout à la base de données
        success = add_printer(
            data["name"],
            data["owner"],
            data["model"],
            data["ip"]
        )

        # Afficher un message de succès ou d'erreur
        if success:
            QMessageBox.information(
                self,
                "Printer added",
                "The printer was successfully added."
            )
            # Rafraîchir le tableau
            self.scan()
        else:
            QMessageBox.warning(
                self,
                "Printer already exists",
                f"A printer with IP {data['ip']} already exists in the database."
            )

    def open_add_dialog(self):
        """Ouvrir le wizard pour ajouter une nouvelle imprimante"""
        wizard = AddPrinterWizard(self)

        # Si le wizard est complété, ajouter l'imprimante
        if wizard.exec():
            data = wizard.get_data()
            self.add_printer_to_db(data)

    def delete_printer(self, ip):
        """
        Supprimer une imprimante de la base de données.
        
        Args:
            ip (str): IP de l'imprimante à supprimer
        """
        # Appeler la fonction de suppression
        success = delete_printer(ip)

        # Afficher un message et rafraîchir si succès
        if success:
            QMessageBox.information(
                self,
                "Printer deleted",
                f"Printer {ip} was deleted."
            )
            # Rafraîchir le tableau
            self.scan()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Printer could not be deleted."
            )

    def confirm_delete(self, ip):
        """
        Afficher un dialogue de confirmation avant de supprimer une imprimante.
        
        Args:
            ip (str): IP de l'imprimante à supprimer
        """
        # Afficher une boîte de dialogue de confirmation
        reply = QMessageBox.question(
            self,
            "Delete printer",
            f"Are you sure you want to delete printer {ip} ?",
            QMessageBox.Yes | QMessageBox.No
        )

        # Supprimer si l'utilisateur confirme
        if reply == QMessageBox.Yes:
            self.delete_printer(ip)


class AddPrinterDialog(QDialog):
    """
    Dialogue pour ajouter une nouvelle imprimante.
    Permet à l'utilisateur d'entrer les détails de l'imprimante.
    """

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
        create_dialog = CreatePrinterModelDialog()
        
        if create_dialog.exec():
            # Ajouter le nouveau modèle à la combo box
            new_model = create_dialog.get_model_name()
            self.model.addItem(new_model)
            self.model.setCurrentText(new_model)

    def get_data(self):
        """
        Récupérer les données du formulaire.
        
        Returns:
            dict: Dictionnaire avec les données de l'imprimante
        """
        return {
            "name": self.name.text().strip(),
            "owner": self.owner.text().strip(),
            "model": self.model.currentText(),
            "ip": self.ip.text().strip()
        }
    
    def validate(self):
        """
        Valider les données du formulaire avant de fermer le dialogue.
        Vérifie que tous les champs sont remplis et que l'IP est valide.
        """
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
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid IP",
                "Please enter a valid IP address."
            )
            return

        # Fermer le dialogue avec succès
        self.accept()


class PrinterCartridgesDialog(QDialog):
    """
    Dialogue affichant les cartouches compatibles avec une imprimante.
    """

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


class CreatePrinterModelDialog(QDialog):
    """
    Dialogue pour créer un nouveau modèle d'imprimante avec ses cartouches.
    Permet l'ajout complet d'un modèle inconnu.
    """

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

        # Sauvegarder les données et lier dans la base
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
        """Créer le modèle et lier les cartouches existantes à la base de données avec rollback complet en cas d'erreur"""
        linked_cartridges = []  # Tracker les cartouches liées avec succès
        
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
                    # ERREUR : erreur de lien (cartouche n'existe pas ou autre problem)
                    # Rollback COMPLET : supprimer le modèle
                    self._rollback_creation(model_name, [])
                    QMessageBox.warning(
                        self,
                        "Link error",
                        f"Cartridge '{cartridge['name']}' not found or failed to link to model '{model_name}'.\nModel creation has been rolled back."
                    )
                    return False
                
                # Ajouter à la liste des cartouches liées
                linked_cartridges.append(cartridge["name"])
            
            QMessageBox.information(
                self,
                "Success",
                f"Model '{model_name}' with {len(cartridges)} cartridge(s) has been created successfully!"
            )
            return True
            
        except Exception as e:
            print(f"Error creating model: {e}")
            # Rollback COMPLET en cas d'exception
            self._rollback_creation(model_name, [])
            QMessageBox.critical(
                self,
                "Critical error",
                f"An unexpected error occurred: {str(e)}\nModel creation has been rolled back."
            )
            return False

    def _rollback_creation(self, model_name, created_cartridges):
        """
        Supprimer le modèle et toutes les cartouches en cas d'erreur.
        
        Args:
            model_name (str): Nom du modèle à supprimer
            created_cartridges (list): Liste des noms de cartouches créées à supprimer
        """
        # Supprimer toutes les cartouches créées
        for cartridge_name in created_cartridges:
            try:
                delete_cartridge(cartridge_name)
            except Exception as e:
                print(f"Warning: Failed to delete cartridge {cartridge_name}: {e}")
        
        # Supprimer le modèle
        try:
            delete_printer_model(model_name)
        except Exception as e:
            print(f"Warning: Failed to delete model {model_name}: {e}")

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


class ScanProgressDialog(QDialog):
    """Dialogue affichant la progression du scan des imprimantes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scanning Printers")
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Message de statut
        message = QLabel("Scanning printers on network...\nThis may take a moment.")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)

        # Barre de progression (indéterminée)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Mode indéterminé
        layout.addWidget(self.progress_bar)

        # Espacement
        layout.addStretch()

        self.setLayout(layout)

        # Appliquer les styles CSS
        self.setStyleSheet("""
        QDialog {
            background-color: #f5f6fa;
        }

        QLabel {
            color: #2f3640;
            font-size: 13px;
        }

        QProgressBar {
            border: none;
            border-radius: 6px;
            background-color: #ecf0f1;
            height: 20px;
        }

        QProgressBar::chunk {
            background-color: #0984e3;
            border-radius: 6px;
        }
        """)


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
                "Min Stock must be a positive number.",
            )
            return

        self.cartridge_name = name
        self.cartridge_color = self.color_combo.currentText()
        self.minstock = minstock
        self.accept()

    def get_cartridge_info(self):
        """Retourner les informations de la cartouche"""
        return {
            "name": self.cartridge_name,
            "color": self.cartridge_color,
            "minstock": self.minstock
        }


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
        self.new_model_cartridges = []  # Cartouches à lier au nouveau modèle (en mémoire)
        self.new_cartridges = []  # Cartouches à créer en DB (dicts avec name, color, minstock)
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

    def reject(self):
        """Annuler le wizard sans créer rien en BD (tout était en mémoire)"""
        # Les données n'ont été créées en BD que si on a cliqué Finish
        # Sinon tout était en mémoire et on n'a rien à supprimer
        super().reject()

    def closeEvent(self, event):
        """Capturer l'événement de fermeture (croix en haut à droite) et faire le rollback"""
        self.reject()
        event.accept()

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

        # Cartouches disponibles (caché mais utilisé)
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
        
        # Extraire la dernière partie de l'IP (après le dernier point)
        if ip and "." in ip:
            try:
                parts = ip.split(".")
                last_octet = int(parts[-1])
                # Format : BEHGG-Q- + 6 chiffres zéro-padded
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

        # Mettre à jour le titre et la description
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

        # Mettre à jour les boutons
        self.btn_prev.setVisible(page_num > 0)
        self.btn_next.setVisible(page_num < 2)
        self.btn_finish.setVisible(page_num == 2)

    def prev_page(self):
        """Aller à la page précédente avec rollback si nouveau modèle"""
        if self.current_page > 0:
            # Si on revient de la page 2 après avoir créé un nouveau modèle
            if self.current_page == 1 and self.new_model_name:
                reply = QMessageBox.warning(
                    self,
                    "Discard Model",
                    f"If you go back, the model '{self.new_model_name}' will be deleted.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # Supprimer le modèle créé
                delete_printer_model(self.new_model_name)
                self.model_combo.removeItem(self.model_combo.findText(self.new_model_name))
                self.new_model_name = None
                self.cartridge_wizard_table.setRowCount(0)
            
            self.show_page(self.current_page - 1)

    def next_page(self):
        """Aller à la page suivante"""
        if self.current_page == 0:
            # Valider la sélection du modèle
            model = self.model_combo.currentText()
            if model == "Select a model":
                QMessageBox.warning(self, "Model required", "Please select or create a model")
                return
            
            self.selected_model = model
            
            # Si c'est un nouveau modèle, aller à la page de cartouches
            if self.new_model_name:
                self.show_page(1)
            else:
                # Sinon aller directement aux détails de l'imprimante
                self.show_page(2)
        
        elif self.current_page == 1:
            # Valider les cartouches
            if self.cartridge_wizard_table.rowCount() == 0:
                QMessageBox.warning(self, "No cartridges", "Please add at least one cartridge")
                return
            
            # Créer les cartouches et le modèle
            if self.create_model_with_cartridges():
                self.show_page(2)

    def create_new_model_inline(self):
        """Créer un nouveau modèle dans la page actuelle (en mémoire, pas en BD)"""
        # Créer un dialogue d'entrée personnalisé avec placeholder
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("New Model Name")
        input_dialog.setLabelText("Enter the new printer model name:")
        input_dialog.setOkButtonText("OK")
        input_dialog.setCancelButtonText("Cancel")
        
        # Accéder à la ligne d'édition et ajouter le placeholder
        line_edit = input_dialog.findChild(QLineEdit)
        if line_edit:
            line_edit.setPlaceholderText("e.g., HP LaserJet Pro 4002dn")
        
        ok = input_dialog.exec()
        model_name = input_dialog.textValue()

        if not ok or not model_name.strip():
            return

        model_name = model_name.strip()

        # Vérifier que le modèle n'existe pas déjà en BD
        existing_models = get_printer_models()
        if model_name in existing_models:
            QMessageBox.warning(self, "Error", f"Model '{model_name}' already exists")
            return
        
        # Stocker le nom en mémoire (sera créé en BD seulement à Finish)
        self.new_model_name = model_name
        self.model_combo.addItem(model_name)
        self.model_combo.setCurrentText(model_name)
        
        # Vider la table des cartouches et aller directement à la page 2
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
        """Créer une nouvelle cartouche dans le wizard (en mémoire, pas en BD)"""
        dialog = AddCartridgeDialog(self)

        if dialog.exec():
            cartridge_info = dialog.get_cartridge_info()

            # Vérifier que la cartouche n'existe pas déjà en BD
            existing_cartridges = get_cartridges()
            existing_names = [c['name'] for c in existing_cartridges]
            
            if cartridge_info['name'] in existing_names:
                QMessageBox.warning(
                    self,
                    "Cartridge Error",
                    f"Cartridge '{cartridge_info['name']}' already exists in the database."
                )
                return

            # Vérifier qu'on ne va pas créer deux fois la même en mémoire
            new_names = [c['name'] for c in self.new_cartridges]
            if cartridge_info['name'] in new_names:
                QMessageBox.warning(
                    self,
                    "Cartridge Error",
                    f"Cartridge '{cartridge_info['name']}' already exists."
                )
                return

            # Stocker en mémoire pour créer à Finish
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
        """Collecter les cartouches à lier en mémoire (sera créé à Finish)"""
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

            # Stocker les cartouches en mémoire pour créer les liens à Finish
            self.new_model_cartridges = cartridges
            return True

        except Exception as e:
            print(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return False

    def finish(self):
        """Terminer le wizard et ajouter l'imprimante (créer tout en BD atomiquement)"""
        ip = self.wizard_ip.text().strip()
        name = self.wizard_name.text().strip()
        owner = self.wizard_owner.text().strip()

        # Valider
        if not ip:
            QMessageBox.warning(self, "Missing IP", "Please enter an IP address")
            return

        if not owner:
            QMessageBox.warning(self, "Missing Owner", "Please enter an owner")
            return

        if not name:
            QMessageBox.warning(self, "Invalid IP", "The IP address is invalid. Printer name could not be generated")
            return

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            QMessageBox.warning(self, "Invalid IP", "Please enter a valid IP address")
            return

        # VÉRIFIER QUE L'IP N'EXISTE PAS AVANT DE CRÉER QUOI QUE CE SOIT
        from database.printers import get_printers
        existing_ips = [p['ip'] for p in get_printers()]
        if ip in existing_ips:
            QMessageBox.warning(
                self,
                "IP Already Exists",
                f"A printer with IP {ip} already exists in the database.\nPlease enter a different IP address or delete the existing printer with this IP."
            )
            return

        # CRÉER TOUT D'UN COUP EN BD
        try:
            # 1. Créer le nouveau modèle s'il y en a un
            if self.new_model_name:
                if not add_printer_model(self.new_model_name):
                    QMessageBox.warning(self, "Model Error", f"Failed to create model '{self.new_model_name}'")
                    return
                self.selected_model = self.new_model_name
            
            # 2. Créer les nouvelles cartouches s'il y en a
            for cartridge_info in self.new_cartridges:
                if not add_cartridge(cartridge_info['name'], cartridge_info['color'], 0, cartridge_info.get("minstock", 1)):
                    QMessageBox.warning(self, "Cartridge Error", f"Failed to create cartridge '{cartridge_info['name']}'")
                    # Rollback du modèle si créé
                    if self.new_model_name:
                        delete_printer_model(self.new_model_name)
                    return
            
            # 3. Lier les cartouches au modèle s'il y en a
            if self.new_model_name:
                for cartridge in self.new_model_cartridges:
                    if not link_cartridge_to_model(cartridge["name"], self.new_model_name):
                        QMessageBox.warning(self, "Link Error", f"Failed to link cartridge '{cartridge['name']}'")
                        # Rollback complet
                        delete_printer_model(self.new_model_name)
                        for cart_to_delete in self.new_cartridges:
                            delete_cartridge(cart_to_delete['name'])
                        return
            
            # 4. Sauvegarder les données et fermer
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
        """Retourner les données de l'imprimante"""
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

        QPushButton:pressed {
            background-color: #1c5d99;
        }
        """)