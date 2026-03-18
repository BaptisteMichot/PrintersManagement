# ==========================================
# Gestion des imprimantes
# Fonctions pour interroger et modifier les imprimantes dans la base de données
# ==========================================

from database.connection import connect_db


def get_printers():
    """
    Récupère la liste de toutes les imprimantes avec leurs informations.
    
    Returns:
        list: Liste de dictionnaires contenant:
            - name: Nom de l'imprimante
            - owner: Propriétaire/utilisateur de l'imprimante
            - model: Modèle de l'imprimante
            - ip: Adresse IP de l'imprimante
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    p.printername,
                    p.printerowner,
                    m.model_name,
                    p.printerip
                FROM printers p
                JOIN printer_models m ON p.model_id = m.id
                ORDER BY p.printerip
            """)

            return [
                {
                    "name": row[0],
                    "owner": row[1],
                    "model": row[2],
                    "ip": row[3]
                }
                for row in cursor.fetchall()
            ]


def get_printer_models():
    """
    Récupère la liste de tous les modèles d'imprimantes disponibles.
    
    Returns:
        list: Liste des noms de modèles d'imprimantes
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT model_name
                FROM printer_models
                ORDER BY model_name
            """)

            return [row[0] for row in cursor.fetchall()]


def add_printer(name, owner, model, ip):
    """
    Ajoute une nouvelle imprimante à la base de données.
    
    Args:
        name (str): Nom de l'imprimante
        owner (str): Propriétaire/utilisateur de l'imprimante
        model (str): Modèle de l'imprimante
        ip (str): Adresse IP de l'imprimante
        
    Returns:
        bool: True si l'imprimante a été ajoutée, False sinon (ex: IP déjà existante)
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            # Vérifier si l'IP existe déjà dans la base
            cursor.execute(
                "SELECT id FROM printers WHERE printerip=%s",
                (ip,)
            )

            if cursor.fetchone():
                # IP déjà utilisée, impossible d'ajouter
                return False

            # Récupérer l'ID du modèle d'imprimante
            cursor.execute(
                "SELECT id FROM printer_models WHERE model_name=%s",
                (model,)
            )

            result = cursor.fetchone()

            if not result:
                return False

            model_id = result[0]

            cursor.execute("""
                INSERT INTO printers (printername, printerowner, printerip, model_id)
                VALUES (%s, %s, %s, %s)
            """, (name, owner, ip, model_id))

        conn.commit()

    return True


def delete_printer(ip):
    """
    Supprime une imprimante de la base de données.
    
    Args:
        ip (str): Adresse IP de l'imprimante à supprimer
        
    Returns:
        bool: True si l'imprimante a été supprimée, False sinon
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            # Supprimer l'imprimante avec cette IP
            cursor.execute(
                "DELETE FROM printers WHERE printerip=%s",
                (ip,)
            )

            # Vérifier qu'au moins une ligne a été supprimée
            deleted = cursor.rowcount > 0

        # Valider la suppression
        conn.commit()

    return deleted


def get_cartridges_for_printer(ip):
    """
    Récupère toutes les cartouches compatibles avec une imprimante spécifique.
    
    Args:
        ip (str): Adresse IP de l'imprimante
        
    Returns:
        list: Liste de dictionnaires des cartouches compatibles contenant:
            - name: Numéro de série de la cartouche
            - color: Couleur de la cartouche
            - inStock: Quantité en stock
            - minStock: Stock minimum
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT 
                    c.cartsn,
                    c.color,
                    c.instock,
                    c.minstock
                FROM cartridges c
                JOIN cartridge_models cm ON cm.cartridge_id = c.id
                JOIN printer_models pm ON pm.id = cm.model_id
                JOIN printers p ON p.model_id = pm.id
                WHERE p.printerip = %s
                GROUP BY c.id
                ORDER BY c.color
            """, (ip,))

            return [
                {
                    "name": row[0],
                    "color": row[1],
                    "inStock": row[2],
                    "minStock": row[3]
                }
                for row in cursor.fetchall()
            ]