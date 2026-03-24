# ==========================================
# Page Commande
# Permet de créer et gérer les commandes de cartouches
# ==========================================

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
    QFrame,
    QFileDialog
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.dialogs.order_form_dialog import OrderFormDialog
from database.orders import get_recent_orders, get_order_details, delete_order
from utils.excel_export import export_order_to_excel
from utils.pdf_export import convert_excel_to_pdf
from utils.mail_export import send_by_mail
import tempfile
import os


class OrderCardWidget(QFrame):
    """Widget carte pour afficher une commande"""
    
    def __init__(self, order, view_callback, delete_callback, export_callback, mail_callback):
        super().__init__()
        self.order = order
        self.view_callback = view_callback
        self.delete_callback = delete_callback
        self.export_callback = export_callback
        self.mail_callback = mail_callback
        self.init_ui()
    
    def init_ui(self):
        """Initialiser la carte de commande"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #dfe6e9;
                border-radius: 8px;
                background-color: white;
                padding: 15px;
                margin: 5px 0px;
            }
            QFrame:hover {
                border: 1px solid #0984e3;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # En-tête : Purchase Order Number et Date
        header_layout = QHBoxLayout()
        
        po_label = QLabel(f"Purchase Order Number: <b>{self.order['po_number']}</b>")
        po_label.setFont(QFont("Arial", 11))
        header_layout.addWidget(po_label)
        
        date_label = QLabel(self.order['order_date'])
        date_label.setFont(QFont("Arial", 11))
        date_label.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Infos : Total et Items count
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        total_label = QLabel(f"<b>Total:</b> {self.order['total']:.2f} EUR")
        total_label.setStyleSheet("color: #0984e3; font-weight: bold;")
        info_layout.addWidget(total_label)
        
        items_label = QLabel(f"<b>Items:</b> {self.order['item_count']}")
        items_label.setStyleSheet("color: #636e72;")
        info_layout.addWidget(items_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        view_button = QPushButton("View Details")
        view_button.setMinimumWidth(120)
        view_button.setObjectName("mainButton")
        view_button.clicked.connect(self.on_view_clicked)
        actions_layout.addWidget(view_button)
        
        export_button = QPushButton("Download PDF")
        export_button.setMinimumWidth(120)
        export_button.setObjectName("mainButton")
        export_button.clicked.connect(self.on_export_clicked)
        actions_layout.addWidget(export_button)
        
        mail_button = QPushButton("Send by mail")
        mail_button.setMinimumWidth(120)
        mail_button.setObjectName("mainButton")
        mail_button.clicked.connect(self.on_mail_clicked)
        actions_layout.addWidget(mail_button)
        
        delete_button = QPushButton("Delete Order")
        delete_button.setMinimumWidth(120)
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.on_delete_clicked)
        actions_layout.addWidget(delete_button)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
    
    def on_view_clicked(self):
        """Callback pour le bouton View"""
        self.view_callback(self.order['id'])
    
    def on_export_clicked(self):
        """Callback pour le bouton Download PDF"""
        self.export_callback(self.order['id'], self.order['po_number'])
    
    def on_mail_clicked(self):
        """Callback pour le bouton Send by mail"""
        self.mail_callback(self.order['id'], self.order['po_number'])
    
    def on_delete_clicked(self):
        """Callback pour le bouton Delete"""
        self.delete_callback(self.order['id'], self.order['po_number'])


class OrderPage(QWidget):
    """
    Page pour gérer les commandes de cartouches.
    Permet de créer une nouvelle commande avec plusieurs lignes de produits.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_recent_orders()

    def init_ui(self):
        """Initialiser les composants de la page"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Barre supérieure avec boutons
        top_bar = QHBoxLayout()

        # Bouton Créer une nouvelle commande
        new_order_button = QPushButton("Create New Order")
        new_order_button.setObjectName("mainButton")
        new_order_button.clicked.connect(self.create_new_order)
        top_bar.addWidget(new_order_button)
        
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # Section Commandes récentes
        orders_label = QLabel("Recent Orders:")
        orders_label_font = QFont()
        orders_label_font.setBold(True)
        orders_label_font.setPointSize(12)
        orders_label.setFont(orders_label_font)
        layout.addWidget(orders_label)

        # ScrollArea pour les cartes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f9f9f9;
            }
        """)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(5)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addStretch()
        
        self.scroll_widget.setLayout(self.scroll_layout)
        scroll_area.setWidget(self.scroll_widget)
        
        layout.addWidget(scroll_area)

        # Placeholder pour absence de commandes
        self.no_orders_label = QLabel("No recent orders yet. Create your first order!")
        self.no_orders_label.setStyleSheet("""
        QLabel {
            color: #636e72;
            font-size: 11px;
            padding: 20px;
            background-color: #f5f6fa;
            border-radius: 6px;
            border: 1px dashed #bdc3c7;
        }
        """)
        self.no_orders_label.setVisible(False)
        layout.addWidget(self.no_orders_label)

        # Appliquer les styles à la page
        self.setStyleSheet("""
        QPushButton#mainButton {
            background-color: #0984e3;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            border: none;
            min-width: 100px;
        }

        QPushButton#mainButton:hover {
            background-color: #74b9ff;
        }

        QPushButton#mainButton:pressed {
            background-color: #0670c4;
        }

        QPushButton#mainButton:disabled {
            background-color: #b2bec3;
        }

        QPushButton#dangerButton {
            background-color: #e74c3c;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            border: none;
            min-width: 100px;
        }

        QPushButton#dangerButton:hover {
            background-color: #ec7063;
        }

        QPushButton#dangerButton:pressed {
            background-color: #c0392b;
        }
        """)

        self.setLayout(layout)

    def load_recent_orders(self):
        """Charger et afficher les commandes récentes"""
        orders = get_recent_orders()
        
        # Nettoyer le layout
        while self.scroll_layout.count() > 1:  # Garder le stretch
            item = self.scroll_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        if not orders:
            self.scroll_widget.setVisible(False)
            self.no_orders_label.setVisible(True)
            return
        
        self.scroll_widget.setVisible(True)
        self.no_orders_label.setVisible(False)
        
        # Ajouter les cartes de commandes
        for order in orders:
            card = OrderCardWidget(
                order,
                view_callback=self.view_order_details,
                export_callback=self.export_order_action,
                mail_callback=self.mail_order_action,
                delete_callback=self.delete_order_action
            )
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)

    def create_new_order(self):
        """Ouvrir le dialog pour créer une nouvelle commande"""
        dialog = OrderFormDialog(self)
        if dialog.exec():
            # Rafraîchir la liste après la création
            self.load_recent_orders()

    def view_order_details(self, order_id):
        """Afficher les détails d'une commande"""
        order = get_order_details(order_id)
        if not order:
            QMessageBox.warning(self, "Error", "Could not load order details.")
            return
        
        # Créer un message détaillé avec les informations de commande
        details = f"""
        <b>Purchase Order Number:</b> {order['po_number']}<br>
        <b>Date:</b> {order['order_date']}<br>
        <b>Total:</b> {order['total']:.2f} EUR<br>
        <br>
        <b>Order Items:</b><br>
        """
        
        for item in order['items']:
            details += f"""
            • {item['cartridge_type']} - {item['description']}<br>
            &nbsp;&nbsp;Qty: {item['quantity']}, Price: {item['unit_price']:.2f} EUR, Total: {item['total']:.2f} EUR<br>
            """
        
        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"Order Details - {order['po_number']}")
        dialog.setText("Order Information")
        dialog.setInformativeText(details)
        dialog.setTextFormat(Qt.RichText)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec()

    def delete_order_action(self, order_id, po_number):
        """Supprimer une commande après confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete order {po_number}?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if delete_order(order_id):
                QMessageBox.information(self, "Success", "Order deleted successfully.")
                self.load_recent_orders()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete order.")

    def export_order_action(self, order_id, po_number):
        """
        Exporte une commande en fichier PDF.
        Affiche un dialogue pour choisir le lieu de sauvegarde.
        """
        try:
            # Récupérer les détails de la commande
            order = get_order_details(order_id)
            if not order:
                QMessageBox.warning(self, "Error", "Could not load order details.")
                return
            
            order_data = {
                'po_number': order['po_number'],
                'date': order['order_date'],
                'lines': order['items'],
                'total': order['total']
            }
            
            # Demander le dossier de sauvegarde
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "Select folder to save Order PDF",
                ""
            )

            if not folder_path:
                return

            # Créer un fichier Excel temporaire pour la conversion
            temp_dir = tempfile.gettempdir()
            temp_excel_path = os.path.join(temp_dir, f"Order_{po_number}_temp.xlsx")
            
            # Générer l'Excel temporaire
            export_order_to_excel(order_data, temp_excel_path)
            
            # Convertir l'Excel temporaire en PDF
            pdf_path = os.path.join(folder_path, f"Order_{po_number}.pdf")
            convert_excel_to_pdf(temp_excel_path, pdf_path)
            
            # Supprimer le fichier Excel temporaire
            try:
                os.remove(temp_excel_path)
            except Exception:
                pass
            
            QMessageBox.information(
                self,
                "Export successful",
                f"Order has been exported to:\n{pdf_path}"
            )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export error",
                f"An error occurred while exporting: {str(e)}"
            )

    def mail_order_action(self, order_id, po_number):
        """
        Envoie une commande par email via Outlook.
        Génère un PDF temporaire et l'attache au message.
        """
        try:
            # Récupérer les détails de la commande
            order = get_order_details(order_id)
            if not order:
                QMessageBox.warning(self, "Error", "Could not load order details.")
                return
            
            order_data = {
                'po_number': order['po_number'],
                'date': order['order_date'],
                'lines': order['items'],
                'total': order['total']
            }
            
            # Créer un fichier temporaire pour le PDF
            temp_dir = tempfile.gettempdir()
            temp_excel_path = os.path.join(temp_dir, f"Order_{po_number}_temp.xlsx")
            pdf_path = os.path.join(temp_dir, f"Order_{po_number}.pdf")
            
            # Générer l'Excel temporaire
            export_order_to_excel(order_data, temp_excel_path)
            
            # Convertir l'Excel temporaire en PDF
            convert_excel_to_pdf(temp_excel_path, pdf_path)
            
            # Supprimer le fichier Excel temporaire
            try:
                os.remove(temp_excel_path)
            except Exception:
                pass
            
            # Envoyer par mail via Outlook
            send_success = send_by_mail(
                pdf_path,
                subject=f"Purchase Order {po_number}",
                body=""
            )
            
            if send_success:
                # Nettoyer le fichier temporaire
                try:
                    os.remove(pdf_path)
                except:
                    pass
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "An error occurred while opening Outlook."
                )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Send email error",
                f"An error occurred while sending the email: {str(e)}"
            )
