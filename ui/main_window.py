# ==========================================
# Fenêtre principale de l'application
# Interface UI avec menu de navigation et zone de contenu
# ==========================================

from ui.pages.printers_page import PrintersPage
from ui.pages.cartridges_page import CartridgesPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.to_order_page import ToOrderPage

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
    QApplication
)

from PySide6.QtGui import QCloseEvent


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application.
    Contient le menu de navigation à gauche et les pages principales au centre.
    """

    def __init__(self):
        super().__init__()

        # Configurer la fenêtre principale
        self.setWindowTitle("Printers ABB")
        self.resize(1100, 650)

        # Créer le layout principal (menu + pages)
        main_layout = QHBoxLayout()
        menu_layout = QVBoxLayout()

        # Créer le titre du menu
        title = QLabel("ABB Printers")
        title.setObjectName("menuTitle")

        # Créer les boutons de navigation
        btn_dashboard = QPushButton("Dashboard")
        btn_printers = QPushButton("Printers")
        btn_cartridges = QPushButton("Cartridges")
        btn_to_order = QPushButton("To order")

        # Appliquer le style à tous les boutons du menu
        for btn in [btn_dashboard, btn_printers, btn_cartridges, btn_to_order]:
            btn.setObjectName("menuButton")

        # Ajouter les éléments au menu
        menu_layout.addWidget(title)
        menu_layout.addSpacing(20)
        menu_layout.addWidget(btn_dashboard)
        menu_layout.addWidget(btn_printers)
        menu_layout.addWidget(btn_cartridges)
        menu_layout.addWidget(btn_to_order)
        menu_layout.addStretch()

        # Créer le widget pour afficher les pages (pages empilées)
        self.pages = QStackedWidget()

        # Créer les instances des différentes pages
        page_dashboard = DashboardPage()
        page_printers = PrintersPage()
        page_cartridges = CartridgesPage()
        page_to_order = ToOrderPage()

        # Ajouter les pages au widget empilé
        self.pages.addWidget(page_dashboard)
        self.pages.addWidget(page_printers)
        self.pages.addWidget(page_cartridges)
        self.pages.addWidget(page_to_order)

        # Connecter les boutons à la navigation entre les pages
        btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        btn_printers.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        btn_cartridges.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        btn_to_order.clicked.connect(lambda: self.pages.setCurrentIndex(3))

        # Connecter les signaux du tableau de bord pour la navigation
        page_dashboard.navigate_to_printers.connect(lambda: self.pages.setCurrentIndex(1))
        page_dashboard.navigate_to_cartridges.connect(lambda: self.pages.setCurrentIndex(2))
        page_dashboard.navigate_to_to_order.connect(lambda: self.pages.setCurrentIndex(3))

        # Appliquer le style aux boutons du tableau de bord
        page_dashboard.set_stylesheet_for_buttons()

        # Créer le widget du menu avec son layout
        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)
        menu_widget.setObjectName("sideMenu")

        # Ajouter le menu et les pages au layout principal
        main_layout.addWidget(menu_widget)
        main_layout.addWidget(self.pages)

        # Créer le conteneur principal et le définir comme widget central
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Appliquer les styles CSS
        self.setStyleSheet("""
        
        QMainWindow {
            background-color: #f5f6fa;
        }

        #sideMenu {
            background-color: #2f3640;
            min-width: 180px;
            max-width: 180px;
            padding: 15px;
        }

        #menuTitle {
            color: white;
            font-size: 18px;
            font-weight: bold;
        }

        #menuButton {
            background-color: transparent;
            color: white;
            text-align: left;
            padding: 10px;
            border-radius: 6px;
        }

        #menuButton:hover {
            background-color: #40739e;
        }

        #menuButton:pressed {
            background-color: #273c75;
        }

        QLabel {
            font-size: 14px;
        }

        """)

    def closeEvent(self, event: QCloseEvent):
        """Capturer la fermeture de l'application et fermer les dialogues en cours"""
        # Trouver et fermer les wizards AddPrinterWizard en cours
        from ui.pages.printers_page import AddPrinterWizard
        
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, AddPrinterWizard) and widget.isVisible():
                widget.reject()  # Déclenche le rollback
        
        event.accept()