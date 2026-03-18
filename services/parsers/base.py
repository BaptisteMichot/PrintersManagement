# ==========================================
# Classe de base abstraite pour les parseurs d'imprimantes
# Tous les parseurs spécifiques héritent de cette classe
# ==========================================

import re
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class BasePrinterParser(ABC):
    """Classe de base abstraite pour tous les parseurs d'imprimantes."""
    
    # Couleurs hexadécimales pour l'affichage
    COLOR_MAP_HEX = {
        "Black": "#000000",
        "Cyan": "#00aeef",
        "Magenta": "#ec008c",
        "Yellow": "#ffd100",
        "Gray": "#808080"
    }
    
    # Mappage modèle -> couleur pour les modèles monochrome
    COLOR_MAPPING = {
        "K": "Black",
        "C": "Cyan",
        "M": "Magenta",
        "Y": "Yellow"
    }
    
    @staticmethod
    def extract_percentage(text):
        """Extraire une valeur numérique représentant un pourcentage d'un texte.
        
        Args:
            text (str): Texte contenant un pourcentage
            
        Returns:
            int: Valeur numérique extraite (0 si aucune valeur trouvée)
        """
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0
    
    @abstractmethod
    def parse(self, html):
        """Parseur principal - à implémenter par chaque sous-classe.
        
        Args:
            html (str): Contenu HTML à parser
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """
        pass
    
    def parse_html(self, html):
        """Helper pour parser HTML avec BeautifulSoup.
        
        Args:
            html (str): Contenu HTML
            
        Returns:
            BeautifulSoup: Objet soup parsé
        """
        return BeautifulSoup(html, "html.parser")
    
    def parse_xml(self, xml):
        """Helper pour parser XML avec BeautifulSoup.
        
        Args:
            xml (str): Contenu XML
            
        Returns:
            BeautifulSoup: Objet soup parsé
        """
        return BeautifulSoup(xml, "xml")
