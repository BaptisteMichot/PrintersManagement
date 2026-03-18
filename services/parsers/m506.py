# ==========================================
# Parseur pour modèle HP M506
# ==========================================

import re
from services.parsers.base import BasePrinterParser


class M506Parser(BasePrinterParser):
    """Parseur pour le modèle M506."""
    
    def parse(self, html):
        """Extraire les niveaux d'encre du modèle M506."""
        soup = self.parse_html(html)
        consumables_data = []
        blocks = soup.find_all("div", class_="consumable-block-header")

        for block in blocks:
            try:
                color = block.find("h2").text.strip()
                percent_text = block.find("p", class_="data percentage").text.strip().replace("*", "")
                percent_value = self.extract_percentage(percent_text)

                ref_text = block.find("span").text.strip()
                ref_match = re.search(r'\((.*?)\)', ref_text)
                reference = ref_match.group(1) if ref_match else ref_text

                consumables_data.append((color, reference, percent_text, percent_value, "Black"))
            except Exception:
                continue

        return consumables_data
