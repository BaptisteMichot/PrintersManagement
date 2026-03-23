# ==========================================
# Export Excel
# Utilitaires pour exporter les commandes en Excel basé sur le modèle
# ==========================================

from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import os


def export_order_to_excel(order_data, filepath):
    """
    Exporte une commande en fichier Excel basé exactement sur le modèle ABB.
    Remplir seulement le numéro de commande, la date et les lignes de commande.
    
    Args:
        order_data (dict): Dictionnaire contenant:
            - po_number: Numéro de commande
            - date: Date de la commande
            - lines: Liste de dictionnaires avec cartridge_type, description, quantity, unit_price, total
        filepath (str): Chemin où sauvegarder le fichier Excel
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    try:
        # Charger le modèle
        template_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'order_model.xlsx')
        wb = load_workbook(template_path)
        ws = wb.active
        
        # Remplir seulement les informations variables
        ws['C12'] = order_data.get('po_number', 'N/A')
        
        # Date
        ws['C15'] = order_data.get('date', datetime.now().strftime('%d/%m/%Y'))
        
        # Effacer les anciennes lignes (gardez seulement les 4 premières données du modèle)
        for row_idx in range(23, 35):
            ws[f'A{row_idx}'].value = None
            ws[f'B{row_idx}'].value = None
            ws[f'H{row_idx}'].value = None
            ws[f'I{row_idx}'].value = None
        
        # Ajouter les lignes de commande
        current_row = 23
        total_amount = 0
        
        for line in order_data.get('lines', []):
            quantity = float(line.get('quantity', 0))
            unit_price = float(line.get('unit_price', 0))
            total = float(line.get('total', 0))
            
            # Sauter les lignes vides
            if quantity == 0 and not line.get('description'):
                continue
            
            # Construire la description avec cartridge_type
            description = f"{line.get('cartridge_type', '')} {line.get('description', '')}".strip()
            
            ws[f'A{current_row}'] = int(quantity) if quantity == int(quantity) else quantity
            ws[f'B{current_row}'] = description
            ws[f'H{current_row}'] = unit_price
            
            # Ajouter la formule de total
            ws[f'I{current_row}'] = f'=IF(H{current_row}="","",H{current_row}*A{current_row})'
            
            # Préserver l'alignement vertical du modèle tout en appliquant wrap_text
            cell_b = ws[f'B{current_row}']
            existing_alignment = cell_b.alignment
            cell_b.alignment = Alignment(
                wrap_text=True, 
                vertical=existing_alignment.vertical if existing_alignment else 'center',
                horizontal=existing_alignment.horizontal if existing_alignment else 'left'
            )
            ws.row_dimensions[current_row].height = 30
            
            total_amount += total
            current_row += 1
        
        # Sauvegarder
        wb.save(filepath)
        return True
        
    except Exception as e:
        print(f"Error exporting order to Excel: {str(e)}")
        raise
