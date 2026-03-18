# ==========================================
# Gestionnaire de logique métier pour les imprimantes
# Wrapper autour des fonctions de base de données
# ==========================================

from database.printers import (
    get_printers as db_get_printers,
    add_printer as db_add_printer,
    delete_printer as db_delete_printer,
    get_printer_models as db_get_printer_models,
    add_printer_model as db_add_printer_model,
    delete_printer_model as db_delete_printer_model,
    get_cartridges_for_printer as db_get_cartridges_for_printer
)


class PrinterManager:
    """Gestionnaire centralisé pour les opérations sur les imprimantes."""
    
    @staticmethod
    def get_all_printers():
        """Récupère toutes les imprimantes."""
        return db_get_printers()
    
    @staticmethod
    def add_printer(name, owner, model, ip):
        """Ajoute une nouvelle imprimante."""
        return db_add_printer(name, owner, model, ip)
    
    @staticmethod
    def delete_printer(ip):
        """Supprime une imprimante."""
        return db_delete_printer(ip)
    
    @staticmethod
    def get_models():
        """Récupère tous les modèles d'imprimantes."""
        return db_get_printer_models()
    
    @staticmethod
    def add_model(model_name):
        """Ajoute un nouveau modèle d'imprimante."""
        return db_add_printer_model(model_name)
    
    @staticmethod
    def delete_model(model_name):
        """Supprime un modèle d'imprimante."""
        return db_delete_printer_model(model_name)
    
    @staticmethod
    def get_cartridges_for_printer(ip):
        """Récupère les cartouches compatibles avec une imprimante."""
        return db_get_cartridges_for_printer(ip)
