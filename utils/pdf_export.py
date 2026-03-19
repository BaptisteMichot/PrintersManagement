# ==========================================
# Export PDF
# Utilitaires pour exporter les données en PDF
# ==========================================

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def _format_printer_models(printer_models):
    """
    Formate les modèles d'imprimante pour affichage dans le PDF.
    
    Args:
        printer_models: Liste ou valeur des modèles d'imprimante
        
    Returns:
        str: Texte formaté avec sauts de ligne si nécessaire
    """
    if not printer_models:
        return ""
    
    if isinstance(printer_models, list):
        models = [m for m in printer_models if m]  # Filter None values
    else:
        models = [str(printer_models)]
    
    # Joindre avec des sauts de ligne pour meilleure lisibilité
    return "\n".join(models)


def export_cartridges_to_pdf(cartridges, filepath):
    """
    Exporte une liste de cartouches à commander en fichier PDF.
    
    Args:
        cartridges (list): Liste de dictionnaires contenant les données des cartouches
        filepath (str): Chemin où sauvegarder le fichier PDF
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    try:
        # Créer le document PDF en mode paysage
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
            title="Cartridges to Order",
            subject="Cartridges to Order - ABB Printers Management",
            author="ABB Printers Management System"
        )
        
        # Liste pour contenir les éléments du document
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0984e3'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Titre
        title = Paragraph("Cartridges to Order", title_style)
        story.append(title)
        
        # Date et résumé
        date_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %H:%M:%S')}"
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        story.append(Paragraph(date_text, date_style))
        
        # Résumé
        if cartridges:
            total_units = sum(item["missing"] for item in cartridges)
            summary_text = f"<b>{len(cartridges)} cartridge(s) to order - {total_units} unit(s) total</b>"
        else:
            summary_text = "<b>No cartridge needs ordering.</b>"
        
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2d3436'),
            alignment=TA_CENTER,
            spaceAfter=14
        )
        story.append(Paragraph(summary_text, summary_style))
        
        # Créer la table avec les données
        if cartridges:
            # Headers
            data = [["Name", "Color", "Printer Models", "To Order"]]
            
            # Ajouter les cartouches
            for cartridge in cartridges:
                # Formater les modèles d'imprimante
                models_text = _format_printer_models(cartridge.get("printer_model", []))
                
                data.append([
                    cartridge["name"],
                    cartridge["color"],
                    models_text,
                    str(cartridge["missing"])
                ])
            
            # Créer la table avec des proportions ajustées
            table = Table(data, colWidths=[1.5*inch, 1.0*inch, 3.0*inch, 1.0*inch])
            
            # Variable pour stocker les hauteurs dynamiques
            table_height = None
            
            # Appliquer les styles à la table
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f2f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 1), (-1, -1), 'TOP'),  # Align text to top for multi-line cells
                
                # Align columns appropriately
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Name centered
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Color centered
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Printer Models left-aligned
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # To Order centered
                
                # Ensure text wraps in cells
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(table)
        
        # Construire le PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error exporting PDF: {str(e)}")
        return False
