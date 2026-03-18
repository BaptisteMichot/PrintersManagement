# ==========================================
# Parseur pour modèle HP M404N
# ==========================================

import re
import requests
from services.parsers.base import BasePrinterParser


class M404NParser(BasePrinterParser):
    """Parseur pour le modèle M404N (support XML et HTML fallback)."""
    
    def __init__(self, tls_session=None):
        """Initialiser le parseur avec une session TLS optionnelle."""
        self.session = tls_session
    
    def parse(self, html):
        """Extraire les niveaux d'encre du modèle M404N via HTML."""
        soup = self.parse_html(html)
        consumables_data = []
        spans = soup.find_all("span", class_="off-screen-text-cls")

        for span in spans:
            try:
                text = span.get_text()
                match = re.search(r"(\d+)%", text)

                if not match:
                    continue

                percent_value = int(match.group(1))
                percent_text = f"{percent_value}%"

                color = "Black"
                if "Cyan" in text:
                    color = "Cyan"
                elif "Magenta" in text:
                    color = "Magenta"
                elif "Yellow" in text:
                    color = "Yellow"
                else:
                    continue

                consumables_data.append((color, "", percent_text, percent_value, color))
            except Exception:
                continue

        return consumables_data
    
    def parse_xml(self, ip):
        """Extraire les niveaux d'encre du modèle M404N via API XML."""
        url = f"https://{ip}/DevMgmt/ConsumableConfigDyn.xml"

        try:
            if not self.session:
                return []
            response = self.session.get(url, timeout=3, verify=False)
            if response.status_code != 200:
                return []
        except Exception:
            return []

        soup = super().parse_xml(response.text)
        consumables_data = []
        items = soup.find_all("ccdyn:ConsumableInfo")

        for item in items:
            try:
                color_elem = item.find("dd:ConsumableLabelCode")
                color = color_elem.text if color_elem else "K"
                color_name = self.COLOR_MAPPING.get(color, "Black")

                reference_elem = item.find("dd:ProductNumber")
                reference = reference_elem.text if reference_elem else "N/A"

                percent_elem = item.find("dd:ConsumablePercentageLevelRemaining")
                if percent_elem:
                    percent_value = int(percent_elem.text)
                    percent_text = f"{percent_value}%"
                else:
                    percent_value = 0
                    percent_text = "0%"

                consumables_data.append((color_name, reference, percent_text, percent_value, color_name))
            except Exception:
                continue

        return consumables_data
