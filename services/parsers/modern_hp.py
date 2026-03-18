# ==========================================
# Parseur pour modèles HP modernes (M575, M776, M725, M4555)
# ==========================================

from services.parsers.base import BasePrinterParser


class ModernHPParser(BasePrinterParser):
    """Parseur pour les modèles modernes HP (M575, M776, M725, M4555)."""
    
    def parse(self, html):
        """Extraire les niveaux d'encre des modèles modernes HP."""
        soup = self.parse_html(html)
        consumables_data = []
        consumables = soup.find_all("div", class_="consumable")

        for consumable in consumables:
            try:
                color = consumable.find("h2").text.strip()
                reference = consumable.find("span", class_="partNumber").text.strip()
                ink_percentage = consumable.find("span", class_="plr").text.strip().replace("*", "").strip()
                percent_value = self.extract_percentage(ink_percentage)

                gauge = consumable.find("div", class_="gauge")
                classes = gauge.get("class", [])
                color_name = next((c for c in classes if c in self.COLOR_MAP_HEX), "Black")

                consumables_data.append((color, reference, ink_percentage, percent_value, color_name))
            except Exception:
                continue

        return consumables_data
