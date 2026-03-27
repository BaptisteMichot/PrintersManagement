# ==========================================
# Dialog Affichage Détails de Commande
# Permet de visualiser les détails d'une commande avec texte sélectionnable
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QApplication
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class OrderDetailsDialog(QDialog):
    """
    Dialog pour afficher les détails d'une commande.
    Le texte est entièrement sélectionnable.
    """

    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.order = order
        self.setWindowTitle(f"Order Details - {order['po_number']}")
        self.resize(700, 500)
        self.init_ui()
        
        # Centrer le dialog sur l'écran du parent
        if parent and parent.isVisible():
            parent_screen = QApplication.screenAt(parent.mapToGlobal(parent.rect().center()))
            if parent_screen:
                screen_geometry = parent_screen.geometry()
                dialog_width = self.width()
                dialog_height = self.height()
                
                center_x = screen_geometry.left() + (screen_geometry.width() - dialog_width) // 2
                center_y = screen_geometry.top() + (screen_geometry.height() - dialog_height) // 2
                
                self.move(int(center_x), int(center_y))

    def init_ui(self):
        """Initialiser les composants du dialog"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # TextEdit pour afficher les détails avec texte sélectionnable
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dfe6e9;
                border-radius: 4px;
                padding: 10px;
                background-color: white;
                color: #2d3436;
            }
        """)
        
        # Générer le contenu formaté
        details_html = self._generate_html_content()
        self.text_edit.setHtml(details_html)
        
        layout.addWidget(self.text_edit)

        # Boutons d'action
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setMinimumWidth(100)
        close_button.setObjectName("mainButton")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _generate_html_content(self):
        """Générer le contenu HTML des détails de la commande"""
        html = """<style>
* { margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #333; }
.header { 
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    margin: 0 0 20px 0;
    border-bottom: 3px solid #34495e;
}
.po-number { 
    font-weight: 700;
    font-size: 20px;
    margin-bottom: 5px;
    letter-spacing: 0.3px;
}
.po-subtext { 
    font-size: 12px;
    opacity: 0.85;
    font-weight: 400;
}
.info-section { 
    background: #f8f9fa;
    margin: 0 0 20px 0;
    padding: 15px 20px;
    border-radius: 5px;
    border-left: 4px solid #34495e;
}
.info-row { 
    display: flex;
    margin-bottom: 12px;
    align-items: center;
    line-height: 1.4;
}
.info-row:last-child { margin-bottom: 0; }
.label { 
    font-weight: 600;
    color: #2c3e50;
    min-width: 140px;
    font-size: 13px;
}
.value { 
    color: #555;
    flex: 1;
    font-size: 13px;
}
.value.highlight { 
    color: #2c3e50;
    font-weight: 700;
}
.items-section { margin: 0; }
.section-title { 
    font-weight: 700;
    font-size: 15px;
    color: white;
    background-color: #34495e;
    margin: 0 0 15px 0;
    padding: 12px 15px;
    border-radius: 4px;
    border-left: 4px solid #2c3e50;
}
.item { 
    margin-bottom: 12px;
    padding: 15px;
    background: white;
    border: 1px solid #ddd;
    border-left: 4px solid #34495e;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}
.item-number {
    display: inline-block;
    background-color: #34495e;
    color: white;
    padding: 3px 10px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 700;
}
.item-title { 
    font-weight: 600;
    color: #2c3e50;
    font-size: 13px;
    flex: 1;
    margin-left: 12px;
}
.item-row { 
    display: flex;
    margin-bottom: 8px;
    font-size: 12px;
    align-items: flex-start;
    line-height: 1.4;
}
.item-row:last-child { margin-bottom: 0; }
.item-label { 
    font-weight: 600;
    color: #2c3e50;
    min-width: 110px;
    flex-shrink: 0;
}
.item-value { 
    color: #555;
    flex: 1;
}
.item-value.highlight {
    color: #2c3e50;
    font-weight: 700;
}
</style>
"""
        
        html += f"""
<div class="header">
    <div class="po-number">Purchase Order {self.order['po_number']}</div>
    <div class="po-subtext">Placed on {self.order['order_date']}</div>
</div>

<div class="info-section">
    <div class="info-row">
        <span class="label">Date:</span>
        <span class="value">{self.order['order_date']}</span>
    </div>
    <div class="info-row">
        <span class="label">Total:</span>
        <span class="value highlight">{self.order['total']:.2f} EUR</span>
    </div>
    <div class="info-row">
        <span class="label">Ordered by:</span>
        <span class="value">{self.order.get('originator_name', 'Ibrahima DIARRA')}</span>
    </div>
</div>

<div class="items-section">
    <div class="section-title">Order Items ({len(self.order['items'])} items)</div>
"""
        
        for i, item in enumerate(self.order['items'], 1):
            html += f"""
    <div class="item">
        <div class="item-header">
            <div style="display: flex; align-items: center;">
                <span class="item-number">#{i}</span>
                <span class="item-title">{item['cartridge_type']}</span>
            </div>
        </div>
        <div class="item-row">
            <span class="item-label">Description:</span>
            <span class="item-value">{item['description']}</span>
        </div>
        <div class="item-row">
            <span class="item-label">Quantity:</span>
            <span class="item-value">{int(item['quantity'])} pcs</span>
        </div>
        <div class="item-row">
            <span class="item-label">Unit Price:</span>
            <span class="item-value">{item['unit_price']:.2f} EUR</span>
        </div>
        <div class="item-row">
            <span class="item-label">Subtotal:</span>
            <span class="item-value highlight">{item['total']:.2f} EUR</span>
        </div>
    </div>
"""
        
        html += """
</div>
"""
        
        return html
