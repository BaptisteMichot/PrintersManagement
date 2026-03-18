# ==========================================
# Page du tableau de bord (Dashboard)
# Affiche la page d'accueil avec navigation vers les autres pages
# ==========================================

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame
)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QColor
from utils.resource_path import get_resource_path


class DashboardPage(QWidget):
    """
    Page tableau de bord / Accueil avec navigation vers les autres pages.
    Affiche des cartes interactives pour accéder aux différentes fonctionnalités.
    """
    
    # Signaux pour la navigation vers les autres pages
    navigate_to_printers = Signal()
    navigate_to_cartridges = Signal()
    navigate_to_to_order = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialiser les composants UI du tableau de bord"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Section d'en-tête
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        # Logo
        logo_label = QLabel()
        logo_path = get_resource_path("assets/abb_logo.png")
        logo_pixmap = QPixmap(logo_path)
        scaled_logo = logo_pixmap.scaledToWidth(150, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_logo)
        logo_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(logo_label)

        # Titre
        title = QLabel("ABB Printers")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1a1a1a; font-weight: bold;")

        header_layout.addWidget(title)

        # Sous-titre
        subtitle = QLabel("Manage EDC's printers and cartridges")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #555; font-weight: 500;")

        header_layout.addWidget(subtitle)
        
        main_layout.addLayout(header_layout)

        # Ligne de séparation
        separator = QFrame()
        separator.setStyleSheet("background-color: #e0e0e0; height: 2px;")
        separator.setFixedHeight(2)
        main_layout.addWidget(separator)

        # Espacement
        main_layout.addSpacing(10)

        # Cartes de navigation
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # Carte Imprimantes
        printers_card = self.create_card(
            "Printers",
            "Manage printers, view ink levels and corresponding cartridges.",
            self.navigate_to_printers.emit,
            "#006064"
        )
        cards_layout.addWidget(printers_card)

        # Carte Cartouches
        cartridges_card = self.create_card(
            "Cartridges",
            "Manage cartridge inventory.\nUpdate stock levels and view compatible printers.",
            self.navigate_to_cartridges.emit,
            "#006064"
        )
        cards_layout.addWidget(cartridges_card)

        # Carte À commander
        to_order_card = self.create_card(
            "To Order",
            "See cartridges to order when stock is below minimum stock.",
            self.navigate_to_to_order.emit,
            "#006064"
        )
        cards_layout.addWidget(to_order_card)

        main_layout.addLayout(cards_layout)

        # Espacement
        main_layout.addSpacing(20)

        self.setLayout(main_layout)

        self.setStyleSheet("""
        QWidget {
            background-color: #fafafa;
        }

        QLabel {
            color: #333;
        }
        """)

    def create_card(self, title, description, callback, color):
        """
        Crée une carte de navigation avec style amélioré.
        
        Args:
            title (str): Titre de la carte
            description (str): Description de la carte
            callback (callable): Fonction à appeler au clic sur le bouton
            color (str): Code couleur hexadécimale pour la carte
            
        Returns:
            QFrame: Widget de la carte créée
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border-left: 5px solid {color};
                border: 1px solid #e8e8e8;
            }}

            QFrame:hover {{
                border-left: 5px solid {color};
                background-color: #fff;
                border: 1px solid {color};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Ajouter une barre d'en-tête colorée
        header_strip = QFrame()
        header_strip.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        header_strip.setFixedHeight(3)
        layout.addWidget(header_strip)

        # Titre de la carte
        card_title = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        card_title.setFont(title_font)
        card_title.setStyleSheet(f"color: {color};")

        layout.addWidget(card_title)

        # Description de la carte
        card_desc = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(10)
        card_desc.setFont(desc_font)
        card_desc.setStyleSheet("color: #666; line-height: 1.5;")
        card_desc.setWordWrap(True)

        layout.addWidget(card_desc)

        # Espacement
        layout.addSpacing(15)

        # Bouton d'accès
        button = QPushButton(f"Open {title}")
        button.setObjectName("cardButton")
        button_font = QFont()
        button_font.setPointSize(10)
        button_font.setBold(True)
        button.setFont(button_font)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(40)
        button.setStyleSheet(f"""
            QPushButton#cardButton {{
                background-color: {color};
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }}

            QPushButton#cardButton:hover {{
                background-color: {self.lighten_color(color)};
            }}

            QPushButton#cardButton:pressed {{
                background-color: {self.darken_color(color)};
            }}
        """)
        button.clicked.connect(callback)

        layout.addWidget(button)

        card.setLayout(layout)

        # Définir la taille de la carte
        card.setMinimumHeight(280)

        return card

    def lighten_color(self, color_hex):
        """
        Éclaircir une couleur de 15%.
        
        Args:
            color_hex (str): Code couleur hexadécimale
            
        Returns:
            str: Code couleur éclaircié
        """
        color = QColor(color_hex)
        color.setHsv(color.hue(), max(0, color.saturation() - 20), min(255, color.value() + 30))
        return color.name()

    def darken_color(self, color_hex):
        """
        Assombrir une couleur de 15%.
        
        Args:
            color_hex (str): Code couleur hexadécimale
            
        Returns:
            str: Code couleur assombrie
        """
        color = QColor(color_hex)
        color.setHsv(color.hue(), color.saturation(), max(0, color.value() - 30))
        return color.name()

    def set_stylesheet_for_buttons(self):
        """Définir le style pour les boutons des cartes (méthode de compatibilité)"""
        # Le style est maintenant appliqué dans la méthode create_card
        pass
