# ==========================================
# Gestion des cartouches
# Fonctions pour interroger et modifier les cartouches dans la base de données
# ==========================================

from database.connection import connect_db

def get_all_cartridges():
    """
    Récupère la liste complète des cartouches avec leur ID pour la sélection dans les formulaires.
    
    Returns:
        list: Liste de dictionnaires contenant:
            - id: ID de la cartouche
            - name: Numéro de série de la cartouche
            - color: Couleur de la cartouche
            - inStock: Quantité en stock
            - minStock: Stock minimum
            - printer_model: Modèles d'imprimantes compatibles
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT 
                    c.id,
                    c.cartsn,
                    c.color,
                    c.instock,
                    c.minstock,
                    ARRAY_AGG(DISTINCT pm.model_name) AS printer_models
                FROM cartridges c
                LEFT JOIN cartridge_models cm ON cm.cartridge_id = c.id
                LEFT JOIN printer_models pm ON pm.id = cm.model_id
                GROUP BY c.id
                ORDER BY c.cartsn ASC
            """)

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "color": row[2],
                    "inStock": row[3],
                    "minStock": row[4],
                    "printer_model": row[5]
                }
                for row in cursor.fetchall()
            ]


def get_cartridges():
    """
    Récupère la liste complète des cartouches avec leurs propriétés et modèles d'imprimantes compatibles.
    
    Returns:
        list: Liste de dictionnaires contenant:
            - name: Numéro de série de la cartouche
            - color: Couleur de la cartouche
            - inStock: Quantité en stock
            - minStock: Stock minimum
            - printer_model: Modèles d'imprimantes compatibles
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT 
                    c.cartsn,
                    c.color,
                    c.instock,
                    c.minstock,
                    ARRAY_AGG(DISTINCT pm.model_name) AS printer_models
                FROM cartridges c
                LEFT JOIN cartridge_models cm ON cm.cartridge_id = c.id
                LEFT JOIN printer_models pm ON pm.id = cm.model_id
                GROUP BY c.id
                ORDER BY c.cartsn ASC
            """)

            return [
                {
                    "name": row[0],
                    "color": row[1],
                    "inStock": row[2],
                    "minStock": row[3],
                    "printer_model": row[4]
                }
                for row in cursor.fetchall()
            ]


def get_cartridges_to_order():
    """
    Récupère la liste des cartouches dont le stock est inférieur au minimum défini.
    Ces cartouches doivent être commandées.
    
    Returns:
        list: Liste de dictionnaires contenant:
            - name: Numéro de série de la cartouche
            - color: Couleur de la cartouche
            - inStock: Quantité actuelle en stock
            - minStock: Stock minimum requis
            - missing: Quantité manquante à commander
            - printer_model: Modèles d'imprimantes compatibles
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    c.cartsn,
                    c.color,
                    c.instock,
                    c.minstock,
                    ARRAY_AGG(DISTINCT pm.model_name) AS printer_models
                FROM cartridges c
                LEFT JOIN cartridge_models cm ON cm.cartridge_id = c.id
                LEFT JOIN printer_models pm ON pm.id = cm.model_id
                WHERE c.instock < c.minstock
                GROUP BY c.id
                ORDER BY c.cartsn ASC
            """)

            return [
                {
                    "name": row[0],
                    "color": row[1],
                    "inStock": row[2],
                    "minStock": row[3],
                    "missing": row[3] - row[2],
                    "printer_model": row[4]
                }
                for row in cursor.fetchall()
            ]


def update_cartridge_stock(cartridge_name, new_stock, new_min_stock):
    """
    Met à jour le stock et le stock minimum d'une cartouche.
    
    Cas spécial : La cartouche HP W1490A est supprimée automatiquement quand son stock atteint 0.
    
    Args:
        cartridge_name (str): Numéro de série de la cartouche
        new_stock (int): Nouvelle quantité en stock
        new_min_stock (int): Nouveau stock minimum
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            # Exécuter la mise à jour du stock
            cursor.execute("""
                UPDATE cartridges
                SET instock = %s, minstock = %s
                WHERE cartsn = %s
            """, (new_stock, new_min_stock, cartridge_name))

            # Vérifier si la mise à jour a affecté au moins une ligne
            updated = cursor.rowcount > 0

            # Cas spécial : supprimer HP W1490A quand son stock atteint 0
            if cartridge_name == "HP W1490A" and new_stock == 0:
                # Supprimer d'abord les associations dans cartridge_models (contrainte de clé étrangère)
                cursor.execute("""
                    DELETE FROM cartridge_models
                    WHERE cartridge_id = (
                        SELECT id FROM cartridges WHERE cartsn = %s
                    )
                """, (cartridge_name,))
                
                # Ensuite supprimer la cartouche elle-même
                cursor.execute("""
                    DELETE FROM cartridges
                    WHERE cartsn = %s
                """, (cartridge_name,))

        # Valider les modifications dans la base de données
        conn.commit()

    return updated


def add_cartridge(cartridge_name, color, initial_stock=0, min_stock=5):
    """
    Ajoute une nouvelle cartouche à la base de données.
    
    Args:
        cartridge_name (str): Numéro de série de la cartouche (ex: 'HP-999K')
        color (str): Couleur de la cartouche (Black, Cyan, Magenta, Yellow)
        initial_stock (int): Stock initial (par défaut 0)
        min_stock (int): Stock minimum (par défaut 5)
        
    Returns:
        bool: True si la cartouche a été ajoutée, False sinon (ex: déjà existante)
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            # Vérifier si la cartouche existe déjà
            cursor.execute(
                "SELECT id FROM cartridges WHERE cartsn=%s",
                (cartridge_name,)
            )

            if cursor.fetchone():
                return False

            # Ajouter la nouvelle cartouche
            cursor.execute("""
                INSERT INTO cartridges (cartsn, color, instock, minstock)
                VALUES (%s, %s, %s, %s)
            """, (cartridge_name, color, initial_stock, min_stock))

        conn.commit()

    return True


def link_cartridge_to_model(cartridge_name, model_name):
    """
    Lie une cartouche à un modèle d'imprimante.
    Crée une association entre les deux dans la table cartridge_models.
    
    Args:
        cartridge_name (str): Numéro de série de la cartouche
        model_name (str): Nom du modèle d'imprimante
        
    Returns:
        bool: True si le lien a été créé, False sinon
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            # Récupérer l'ID de la cartouche
            cursor.execute(
                "SELECT id FROM cartridges WHERE cartsn=%s",
                (cartridge_name,)
            )
            cartridge_result = cursor.fetchone()

            if not cartridge_result:
                return False

            cartridge_id = cartridge_result[0]

            # Récupérer l'ID du modèle d'imprimante
            cursor.execute(
                "SELECT id FROM printer_models WHERE model_name=%s",
                (model_name,)
            )
            model_result = cursor.fetchone()

            if not model_result:
                return False

            model_id = model_result[0]

            # Vérifier que le lien n'existe pas déjà (cartridge_models n'a pas de colonne 'id')
            cursor.execute("""
                SELECT COUNT(*) FROM cartridge_models
                WHERE cartridge_id=%s AND model_id=%s
            """, (cartridge_id, model_id))

            count = cursor.fetchone()[0]
            if count > 0:
                # Lien existe déjà
                return False

            # Créer l'association
            cursor.execute("""
                INSERT INTO cartridge_models (cartridge_id, model_id)
                VALUES (%s, %s)
            """, (cartridge_id, model_id))

        conn.commit()

    return True


def delete_cartridge(cartridge_name):
    """
    Supprime une cartouche de la base de données.
    Utilisé pour le rollback en cas d'erreur lors de la création.
    
    Args:
        cartridge_name (str): Numéro de série de la cartouche
        
    Returns:
        bool: True si la cartouche a été supprimée, False sinon
    """
    with connect_db() as conn:
        with conn.cursor() as cursor:

            # Supprimer d'abord les associations dans cartridge_models (contrainte de clé étrangère)
            cursor.execute("""
                DELETE FROM cartridge_models
                WHERE cartridge_id = (
                    SELECT id FROM cartridges WHERE cartsn = %s
                )
            """, (cartridge_name,))

            # Ensuite supprimer la cartouche elle-même
            cursor.execute("""
                DELETE FROM cartridges
                WHERE cartsn = %s
            """, (cartridge_name,))

            deleted = cursor.rowcount > 0

        conn.commit()

    return deleted