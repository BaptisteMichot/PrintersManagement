# ==========================================
# Gestion des cartouches
# Fonctions pour interroger et modifier les cartouches dans la base de données
# ==========================================

from database.connection import connect_db

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
                WHERE c.instock < c.minstock
                ORDER BY c.cartsn ASC
            """)

            return [
                {
                    "name": row[0],
                    "color": row[1],
                    "inStock": row[2],
                    "minStock": row[3],
                    "missing": row[3] - row[2]
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