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
    QLabel
)

from PySide6.QtCore import QThread, Signal, Qt, QSize, QTimer
from services.ink_scanner import run_scanner
from database.printers import add_printer, get_printer_models, delete_printer, get_cartridges_for_printer
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
        else:
            QMessageBox.warning(
                self,
                "Printer already exists",
                f"A printer with IP {data['ip']} already exists in the database."
            )

    def open_add_dialog(self):
        """Ouvrir le dialogue d'ajout d'une nouvelle imprimante"""
        dialog = AddPrinterDialog()

        # Si le dialogue est accepté, ajouter l'imprimante
        if dialog.exec():
            data = dialog.get_data()
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

        # Ajouter les boutons OK et Annuler
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

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