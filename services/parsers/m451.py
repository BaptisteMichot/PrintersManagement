# ==========================================
# Parseur pour modèle HP M451DN
# ==========================================

from services.parsers.base import BasePrinterParser


class M451DNParser(BasePrinterParser):
    """Parseur pour le modèle M451DN."""
    
    def parse(self, html):
        """Extraire les niveaux d'encre du modèle M451DN."""
        soup = self.parse_html(html)
        consumables_data = []
        seen_refs = set()
        rows = soup.find_all("tr")

        for row in rows:
            try:
                cells = row.find_all("td")
                if len(cells) != 2:
                    continue

                name_cell, percent_cell = cells

                if percent_cell.find("table"):
                    continue

                text = name_cell.get_text("\n", strip=True)
                if "Cartridge" not in text:
                    continue

                lines = text.split("\n")
                color = lines[0].strip()
                reference = next((line.replace("Order", "").strip() for line in lines if "Order" in line), "")

                if reference == "" or reference in seen_refs:
                    continue
                seen_refs.add(reference)

                percent_text = percent_cell.get_text(" ", strip=True).replace("*", "").strip()
                percent_value = self.extract_percentage(percent_text)

                if percent_value > 100:
                    continue

                color_lower = color.lower()
                if "cyan" in color_lower:
                    color_name = "Cyan"
                elif "magenta" in color_lower:
                    color_name = "Magenta"
                elif "yellow" in color_lower:
                    color_name = "Yellow"
                else:
                    color_name = "Black"

                consumables_data.append((color, reference, percent_text, percent_value, color_name))
            except Exception:
                continue

        return consumables_data
