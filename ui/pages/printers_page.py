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
    QMessageBox,
    QCheckBox,
    QLabel
)

from PySide6.QtCore import Qt, QTimer
from ui.workers import ScanWorker, ScanProgressDialog
from ui.dialogs.printer_cartridges_dialog import PrinterCartridgesDialog
from ui.dialogs.add_printer_wizard import AddPrinterWizard
from database.printers import delete_printer


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
            value (int or None): Pourcentage de remplissage (0-100) ou None si cartouche inexistante
            color (str): Couleur hexadécimale de la barre
            
        Returns:
            QWidget: Widget contenant la barre de progression (ou vide si value est None)
        """
        # Si la cartouche n'existe pas (None), retourner un widget vide
        if value is None:
            empty_container = QWidget()
            empty_layout = QHBoxLayout(empty_container)
            empty_layout.setContentsMargins(0, 0, 0, 0)
            empty_layout.setSpacing(0)
            return empty_container
        
        value = int(value or 0)

        # Créer la barre de progression
        bar = QProgressBar()
        bar.setValue(value)
        bar.setTextVisible(True)
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bar.setFixedHeight(18)

        # Définir le texte à afficher
        text = f"{value}%"

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

        # Ajouter une flèche clignotante si cartouche à 10% ou moins
        if value is not None and value <= 10:
            arrow = QLabel("→")
            arrow.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 14px;")
            arrow.setMinimumWidth(20)
            arrow.setAlignment(Qt.AlignCenter)
            
            # Créer une animation de clignotement
            timer = QTimer()
            
            def toggle_arrow():
                # Alterner la visibilité chaque 2 secondes (mais on change à chaque appel du timer)
                if arrow.isVisible():
                    arrow.hide()
                else:
                    arrow.show()
            
            timer.timeout.connect(toggle_arrow)
            timer.start(1200)  # Basculer toutes les 1,2 seconde (visible + invisible)
            
            # Stocker la référence du timer pour éviter qu'il soit garbage collected
            container.timer = timer
            
            layout.addWidget(arrow)

        layout.addWidget(bar)

        # Supprimer les marges (IMPORTANT pour l'affichage dans les cellules du tableau)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        return container

    def create_offline_label(self):
        """
        Crée un label pour afficher le statut 'Printer offline or inaccessible'.
        
        Returns:
            QWidget: Widget contenant le label "Printer offline or inaccessible"
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        
        label = QLabel("Printer offline or inaccessible")
        label.setStyleSheet("""
            color: #ff6b6b;
            font-weight: bold;
            font-size: 12px;
        """)
        label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label)
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
            is_offline = data.get("is_offline", False)

            # Utiliser les données de la base ou celles scannées
            name = data.get("db_name") or info.get("name") or ""
            user = data.get("db_owner") or info.get("user") or ""
            model = data.get("db_model") or ""

            # Initialiser les niveaux d'encre (None = cartouche inexistante)
            levels = {
                "Black": None,
                "Cyan": None,
                "Magenta": None,
                "Yellow": None
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

            # Ajouter les barres de progression ou le message offline selon le statut
            if is_offline:
                # Afficher "Printer offline" dans la première colonne d'encre uniquement
                self.table.setCellWidget(row, 4, self.create_offline_label())
                # Les autres colonnes restent vides
                self.table.setCellWidget(row, 5, QWidget())
                self.table.setCellWidget(row, 6, QWidget())
                self.table.setCellWidget(row, 7, QWidget())
            else:
                # Afficher les barres de progression normales
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
        from database.printers import add_printer
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

    def delete_printer_from_db(self, ip):
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
            self.delete_printer_from_db(ip)
