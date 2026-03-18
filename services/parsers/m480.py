# ==========================================
# Parseur pour modèle HP M480
# ==========================================

import re
from services.parsers.base import BasePrinterParser


class M480Parser(BasePrinterParser):
    """Parseur pour le modèle M480."""
    
    def parse(self, html):
        """Extraire les niveaux d'encre du modèle M480."""
        soup = self.parse_html(html)
        consumables_data = []
        seen_refs = set()
        divs = soup.find_all("div", class_="consumable")

        for div in divs:
            try:
                text = div.get_text(" ", strip=True)

                color_name = "Black"
                if "Cyan" in text:
                    color_name = "Cyan"
                elif "Magenta" in text:
                    color_name = "Magenta"
                elif "Yellow" in text:
                    color_name = "Yellow"

                ref_match = re.search(r'\(([^)]+)\)', text)
                reference = ref_match.group(1) if ref_match else ""

                if reference in seen_refs:
                    continue
                seen_refs.add(reference)

                percent_match = re.search(r'([<]?\d+)%\*?\s*(\d+)%', text)
                if percent_match:
                    percent_value = int(percent_match.group(2))
                else:
                    percent_match = re.search(r'(\d+)%', text)
                    if percent_match:
                        percent_value = int(percent_match.group(1))
                    else:
                        continue

                percent_text = f"{percent_value}%"
                consumables_data.append((color_name, reference, percent_text, percent_value, color_name))
            except Exception:
                continue

        return consumables_data
