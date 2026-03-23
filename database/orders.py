# ==========================================
# Gestion des commandes
# Fonctions pour interroger et modifier les commandes en base de données
# ==========================================

from database.connection import connect_db
from datetime import datetime


def save_order(po_number, order_date, total, order_lines):
    """
    Sauvegarde une nouvelle commande et ses lignes en base de données.
    
    Args:
        po_number (str): Numéro de bon de commande
        order_date (str): Date de la commande (format: dd/mm/yyyy)
        total (float): Montant total de la commande
        order_lines (list): Liste des lignes avec:
            - cartridge_type: Type de cartouche
            - description: Description
            - quantity: Quantité
            - unit_price: Prix unitaire
            - total: Total de la ligne
    
    Returns:
        int: ID de la commande créée, ou None en cas d'erreur
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cursor:
                # Inserrer la commande
                cursor.execute("""
                    INSERT INTO orders (po_number, order_date, total, created_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (po_number, order_date, total, datetime.now()))
                
                order_id = cursor.fetchone()[0]
                
                # Insérer les lignes de commande
                for line in order_lines:
                    cursor.execute("""
                        INSERT INTO order_items 
                        (order_id, cartridge_type, description, quantity, unit_price, total)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        order_id,
                        line['cartridge_type'],
                        line['description'],
                        line['quantity'],
                        line['unit_price'],
                        line['total']
                    ))
                
                conn.commit()
                return order_id
    
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la commande: {e}")
        return None


def get_recent_orders(limit=10):
    """
    Récupère les commandes récentes (par défaut, les 10 dernières).
    
    Returns:
        list: Liste de dictionnaires contenant:
            - id: ID de la commande
            - po_number: Numéro de bon de commande
            - order_date: Date de la commande
            - total: Montant total
            - created_at: Date de création en base de données
            - item_count: Nombre de lignes dans la commande
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        o.id,
                        o.po_number,
                        o.order_date,
                        o.total,
                        o.created_at,
                        COUNT(oi.id) as item_count
                    FROM orders o
                    LEFT JOIN order_items oi ON oi.order_id = o.id
                    GROUP BY o.id
                    ORDER BY o.created_at DESC
                    LIMIT %s
                """, (limit,))
                
                return [
                    {
                        "id": row[0],
                        "po_number": row[1],
                        "order_date": row[2],
                        "total": row[3],
                        "created_at": row[4],
                        "item_count": row[5]
                    }
                    for row in cursor.fetchall()
                ]
    
    except Exception as e:
        print(f"Erreur lors de la récupération des commandes: {e}")
        return []


def get_order_details(order_id):
    """
    Récupère les détails complets d'une commande incluant ses lignes.
    
    Args:
        order_id (int): ID de la commande
    
    Returns:
        dict: Dictionnaire contenant:
            - id: ID de la commande
            - po_number: Numéro de bon de commande
            - order_date: Date de la commande
            - total: Montant total
            - created_at: Date de création
            - items: Liste des lignes de commande
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cursor:
                # Récupérer l'en-tête de la commande
                cursor.execute("""
                    SELECT id, po_number, order_date, total, created_at
                    FROM orders
                    WHERE id = %s
                """, (order_id,))
                
                order = cursor.fetchone()
                if not order:
                    return None
                
                # Récupérer les lignes de la commande
                cursor.execute("""
                    SELECT id, cartridge_type, description, quantity, unit_price, total
                    FROM order_items
                    WHERE order_id = %s
                    ORDER BY id
                """, (order_id,))
                
                items = [
                    {
                        "id": row[0],
                        "cartridge_type": row[1],
                        "description": row[2],
                        "quantity": row[3],
                        "unit_price": row[4],
                        "total": row[5]
                    }
                    for row in cursor.fetchall()
                ]
                
                return {
                    "id": order[0],
                    "po_number": order[1],
                    "order_date": order[2],
                    "total": order[3],
                    "created_at": order[4],
                    "items": items
                }
    
    except Exception as e:
        print(f"Erreur lors de la récupération des détails de la commande: {e}")
        return None


def delete_order(order_id):
    """
    Supprime une commande et ses lignes associées.
    
    Args:
        order_id (int): ID de la commande à supprimer
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cursor:
                # Supprimer d'abord les lignes
                cursor.execute("""
                    DELETE FROM order_items
                    WHERE order_id = %s
                """, (order_id,))
                
                # Supprimer la commande
                cursor.execute("""
                    DELETE FROM orders
                    WHERE id = %s
                """, (order_id,))
                
                conn.commit()
                return True
    
    except Exception as e:
        print(f"Erreur lors de la suppression de la commande: {e}")
        return False
