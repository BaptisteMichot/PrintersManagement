# ==========================================
# Page Commande
# Permet de créer et gérer les commandes de cartouches
# ==========================================

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.dialogs.order_form_dialog import OrderFormDialog


class OrderPage(QWidget):
    """
    Page pour gérer les commandes de cartouches.
    Permet de créer une nouvelle commande avec plusieurs lignes de produits.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants de la page"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Barre supérieure avec bouton
        top_bar = QHBoxLayout()

        # Bouton Créer une nouvelle commande
        new_order_button = QPushButton("Create New Order")
        new_order_button.setObjectName("mainButton")
        new_order_button.clicked.connect(self.create_new_order)
        top_bar.addWidget(new_order_button)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # Contenu principal
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Espace pour actions futures
        actions_label = QLabel("Recent Orders:")
        actions_label_font = QFont()
        actions_label_font.setBold(True)
        actions_label.setFont(actions_label_font)

        content_layout.addWidget(actions_label)
        
        no_orders_label = QLabel("No recent orders yet. Create your first order!")
        no_orders_label.setStyleSheet("""
        QLabel {
            color: #636e72;
            font-size: 11px;
            padding: 20px;
            background-color: #f5f6fa;
            border-radius: 6px;
            border: 1px dashed #bdc3c7;
        }
        """)
        content_layout.addWidget(no_orders_label)

        layout.addLayout(content_layout)
        layout.addStretch()

        # Appliquer les styles à la page
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

        QPushButton#mainButton:disabled {
            background-color: #b2bec3;
        }
        """)

        self.setLayout(layout)

    def create_new_order(self):
        """Ouvrir le dialog pour créer une nouvelle commande"""
        dialog = OrderFormDialog(self)
        dialog.exec()
