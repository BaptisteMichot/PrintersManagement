# ==========================================
# Worker thread pour scanner les imprimantes
# ==========================================

from PySide6.QtCore import QThread, Signal
from services.ink_scanner import run_scanner


class ScanWorker(QThread):
    """Thread worker pour scanner les imprimantes sur le réseau en arrière-plan."""

    # Signal émis quand le scan est terminé
    finished = Signal(dict)

    def run(self):
        """Exécuter le scan des imprimantes en arrière-plan."""
        # Appeler la fonction de scan
        results = run_scanner()

        # Retourner un dictionnaire vide si le scan a échoué
        if results is None:
            results = {}

        # Émettre le signal avec les résultats
        self.finished.emit(results)
