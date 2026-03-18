# ==========================================
# Parseur générique pour modèles inconnus
# ==========================================

import re
from services.parsers.base import BasePrinterParser


class GenericPrinterParser(BasePrinterParser):
    """Parseur générique pour les modèles d'imprimantes non reconnus."""
    
    def parse(self, html):
        """Parcourir les niveaux d'encre en cherchant des patterns courants."""
        soup = self.parse_html(html)
        consumables_data = []
        seen_combinations = set()

        # Stratégie 1: Chercher les divs/tables qui matchent "consumable"
        for div in soup.find_all(["div", "table"], class_=re.compile(r"consumable|supply|toner|cartridge|ink", re.I)):
            text = div.get_text(" ", strip=True)
            
            # Extraire le pourcentage
            percent_match = re.search(r'(\d+)%', text)
            if not percent_match:
                continue
            
            percent_value = int(percent_match.group(1))
            percent_text = f"{percent_value}%"
            
            # Détecter la couleur
            color_name = "Black"
            if re.search(r'cyan', text, re.I):
                color_name = "Cyan"
            elif re.search(r'magenta', text, re.I):
                color_name = "Magenta"
            elif re.search(r'yellow', text, re.I):
                color_name = "Yellow"
            elif re.search(r'gray|grey', text, re.I):
                color_name = "Gray"
            
            # Extraire une référence (optionnel)
            reference_match = re.search(r'\(([A-Z0-9]+)\)', text)
            reference = reference_match.group(1) if reference_match else ""
            
            # Éviter les doublons
            combo = (color_name, percent_value)
            if combo in seen_combinations:
                continue
            seen_combinations.add(combo)
            
            consumables_data.append((color_name, reference, percent_text, percent_value, color_name))

        # Stratégie 2 (fallback): Si rien trouvé, chercher n'importe quel pourcentage
        if not consumables_data:
            spans = soup.find_all(["span", "td", "div"])
            for elem in spans:
                text = elem.get_text(strip=True)
                
                percent_match = re.search(r'(\d+)%', text)
                if not percent_match:
                    continue
                
                percent_value = int(percent_match.group(1))
                if percent_value > 100 or percent_value < 0:
                    continue
                
                percent_text = f"{percent_value}%"
                
                # Détecter couleur dans le contexte large
                parent_text = elem.get_text(" ", strip=True)
                color_name = "Black"
                if re.search(r'cyan', parent_text, re.I):
                    color_name = "Cyan"
                elif re.search(r'magenta', parent_text, re.I):
                    color_name = "Magenta"
                elif re.search(r'yellow', parent_text, re.I):
                    color_name = "Yellow"
                
                combo = (color_name, percent_value)
                if combo not in seen_combinations:
                    seen_combinations.add(combo)
                    consumables_data.append((color_name, "", percent_text, percent_value, color_name))

        return consumables_data
