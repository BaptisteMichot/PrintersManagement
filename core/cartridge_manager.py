# ==========================================
# Gestionnaire de logique métier pour les cartouches
# Wrapper autour des fonctions de base de données
# ==========================================

from database.cartridges import (
    get_cartridges as db_get_cartridges,
    get_cartridges_to_order as db_get_cartridges_to_order,
    update_cartridge_stock as db_update_cartridge_stock,
    add_cartridge as db_add_cartridge,
    delete_cartridge as db_delete_cartridge,
    link_cartridge_to_model as db_link_cartridge_to_model
)


class CartridgeManager:
    """Gestionnaire centralisé pour les opérations sur les cartouches."""
    
    @staticmethod
    def get_all_cartridges():
        """Récupère toutes les cartouches."""
        return db_get_cartridges()
    
    @staticmethod
    def get_cartridges_to_order():
        """Récupère les cartouches à commander (stock < minimum)."""
        return db_get_cartridges_to_order()
    
    @staticmethod
    def update_stock(name, quantity, min_stock):
        """Met à jour le stock d'une cartouche."""
        return db_update_cartridge_stock(name, quantity, min_stock)
    
    @staticmethod
    def add_cartridge(name, color, initial_stock=0, min_stock=5):
        """Ajoute une nouvelle cartouche."""
        return db_add_cartridge(name, color, initial_stock, min_stock)
    
    @staticmethod
    def delete_cartridge(name):
        """Supprime une cartouche."""
        return db_delete_cartridge(name)
    
    @staticmethod
    def link_to_model(cartridge_name, model_name):
        """Lie une cartouche à un modèle d'imprimante."""
        return db_link_cartridge_to_model(cartridge_name, model_name)
