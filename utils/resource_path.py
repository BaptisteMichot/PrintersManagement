# ==========================================
# Gestion des chemins de ressources
# Fonctionne en développement et avec PyInstaller
# ==========================================

import sys
import os


def get_resource_path(relative_path):
    """
    Récupère le chemin correct vers un fichier de ressource.
    Fonctionne à la fois en développement et en tant qu'exécutable compilé (PyInstaller).
    
    Args:
        relative_path (str): Chemin relatif du fichier de ressource
        
    Returns:
        str: Chemin complet du fichier de ressource
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Exécuté comme exécutable compilé (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Exécuté comme script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)
