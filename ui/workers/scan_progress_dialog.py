# ==========================================
# Dialogue de progression pour le scan
# ==========================================

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar
)

from PySide6.QtCore import Qt


class ScanProgressDialog(QDialog):
    """Dialogue affichant la progression du scan des imprimantes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scanning Printers")
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(20)

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
