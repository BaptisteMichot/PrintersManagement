# ==========================================
# Export par Mail
# Utilitaires pour envoyer les données par email via Outlook
# ==========================================

import os
import platform
import win32com.client  # type: ignore


def send_cartridges_by_mail(pdf_path):
    """
    Envoie un PDF par email via Outlook.
    
    Args:
        pdf_path (str): Chemin vers le fichier PDF à envoyer
        
    Returns:
        bool: True si l'email a été ouvert correctement, False sinon
    """
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return False
        
        # Vérifier que nous sommes sur Windows
        if platform.system() != "Windows":
            print("Mail functionality is only available on Windows")
            return False
        
        # Initialiser Outlook
        outlook = win32com.client.Dispatch("Outlook.Application")
        
        # Créer un nouvel email
        mail = outlook.CreateItem(0)  # 0 = olMailItem
        mail.Subject = "Cartridges to Order"
        mail.Body = ""
        
        # Ajouter la pièce jointe
        mail.Attachments.Add(pdf_path)
        
        # Afficher le mail pour que l'utilisateur puisse le modifier et l'envoyer
        mail.Display()
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
