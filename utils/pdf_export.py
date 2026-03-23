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
import os


def convert_excel_to_pdf(excel_path, pdf_path):
    """
    Convertit un fichier Excel en PDF en utilisant Excel COM.
    Garantit une ressemblance exacte entre le fichier Excel et le PDF.
    
    Args:
        excel_path (str): Chemin complet vers le fichier Excel à convertir
        pdf_path (str): Chemin complet où sauvegarder le fichier PDF
        
    Returns:
        bool: True si la conversion a réussi, False sinon
    """
    try:
        import win32com.client
        
        # Initialiser Excel
        excel_app = win32com.client.Dispatch('Excel.Application')
        excel_app.Visible = False
        excel_app.DisplayAlerts = False
        
        # Ouvrir le classeur
        workbook = excel_app.Workbooks.Open(os.path.abspath(excel_path))
        
        try:
            # Convertir en PDF (0 = xlTypePDF)
            workbook.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
            return True
        finally:
            # Fermer le classeur sans sauvegarder
            workbook.Close(False)
            excel_app.Quit()
            
    except ImportError:
        print("Error: win32com.client not available. Please install pywin32.")
        return False
    except Exception as e:
        print(f"Error converting Excel to PDF: {str(e)}")
        raise


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


def export_order_to_pdf(order_data, filepath):
    """
    Exporte une commande en fichier PDF basé exactement sur le modèle ABB.
    
    Args:
        order_data (dict): Dictionnaire contenant:
            - po_number: Numéro de commande
            - date: Date de la commande
            - recipient: Destinataire
            - contact: Personne de contact
            - lines: Liste de dictionnaires avec cartridge_type, description, quantity, unit_price, total
            - total: Montant total
        filepath (str): Chemin où sauvegarder le fichier PDF
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    try:
        # Créer le document PDF en mode portrait
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
            title="Purchase Order",
            subject="Purchase Order - ABB Printers Management",
            author="ABB Printers Management System"
        )
        
        # Liste pour contenir les éléments du document
        story = []
        styles = getSampleStyleSheet()
        
        # ===== HEADER =====
        header_data = [[
            "ABB Installation Products European Centre NV\nHoge Wei 27\nB – 1930 Zaventem\nBelgium\nTVA / BTW : BE 0454.460.440\nTel. 0032/2/718.67.19\nSend invoices electronically to: rsg_invoicing@be.abb.com",
            f"To: {order_data.get('recipient', '')}"
        ]]
        
        header_table = Table(header_data, colWidths=[3.5*inch, 3.0*inch])
        header_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        # ===== PURCHASE ORDER INFO =====
        po_data = [
            ['PURCHASE ORDER No:', order_data.get('po_number', '')],
            ['Date:', order_data.get('date', datetime.now().strftime('%d/%m/%Y'))],
        ]
        
        po_table = Table(po_data, colWidths=[2.0*inch, 4.5*inch])
        po_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(po_table)
        story.append(Spacer(1, 0.2*inch))
        
        # ===== TITLE =====
        title = Paragraph("Please supply:", styles['Heading2'])
        story.append(title)
        story.append(Spacer(1, 0.1*inch))
        
        # ===== ORDER LINES TABLE =====
        if order_data.get('lines'):
            # Headers
            lines_data = [['QUANTITY', 'DESCRIPTION / DETAILS', 'Unit price', 'Total']]
            
            # Add order lines
            for line in order_data['lines']:
                description = f"{line['cartridge_type']} - {line['description']}" if line.get('cartridge_type') else line['description']
                lines_data.append([
                    str(line['quantity']),
                    description,
                    f"€ {float(line['unit_price']):.2f}",
                    f"€ {float(line['total']):.2f}"
                ])
            
            # Create table with proper column widths
            lines_table = Table(lines_data, colWidths=[1.0*inch, 3.5*inch, 1.2*inch, 1.3*inch])
            
            # Apply styles matching the model
            lines_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                
                # Alignment
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),    # Quantity
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),      # Description
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),    # Prices
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ]))
            
            story.append(lines_table)
            
            # Currency and Total
            story.append(Spacer(1, 0.05*inch))
            currency_text = Paragraph("Currency: EUR", styles['Normal'])
            story.append(currency_text)
            
            # Total line
            total_data = [['', '', 'Total', f"EUR {float(order_data['total']):.2f}"]]
            total_table = Table(total_data, colWidths=[1.0*inch, 3.5*inch, 1.2*inch, 1.3*inch])
            total_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(total_table)
        
        story.append(Spacer(1, 0.3*inch))
        
        # ===== FOOTER SECTION =====
        footer_data = [[
            f"Invoice to: ABB Instal. Prod. European Centre NV\nMark for the attention of: {order_data.get('contact', '')}\nOriginator: {order_data.get('contact', '')}",
            "DELIVERY / SPECIAL INSTRUCTIONS\n\nDelivery address:\nABB Installation Products European Centre SA\nBoulevard Millenium, 8\nB-7110 Houdeng-Goegnies\nBelgique"
        ]]
        
        footer_table = Table(footer_data, colWidths=[3.25*inch, 3.25*inch])
        footer_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(footer_table)
        
        story.append(Spacer(1, 0.15*inch))
        
        # ===== BOTTOM SECTION =====
        bottom_data = [[
            "Approved: ",
            "BUDGET REFERENCE\n\nPROFIT CENTER\n\nMER No:\n\n☐ Mktg - Elec.\n☐ Sales\n☐ Cust.Service\n☐ Advertising"
        ]]
        
        bottom_table = Table(bottom_data, colWidths=[1.5*inch, 5.0*inch])
        bottom_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        story.append(bottom_table)
        
        # Construire le PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error exporting order PDF: {str(e)}")
        raise
