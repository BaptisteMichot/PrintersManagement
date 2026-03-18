# ==========================================
# Parseur pour modèle HP M402N
# ==========================================

from services.parsers.base import BasePrinterParser


class M402NParser(BasePrinterParser):
    """Parseur pour le modèle M402N."""
    
    def parse(self, html):
        """Extraire les niveaux d'encre du modèle M402N."""
        soup = self.parse_html(html)
        consumables_data = []
        seen_refs = set()
        tables = soup.find_all("table", class_="width100")

        for table in tables:
            try:
                name_cell = table.find("td")
                percent_cell = table.find("td", class_="alignRight")

                if not name_cell or not percent_cell:
                    continue

                lines = name_cell.get_text("\n", strip=True).split("\n")
                color = lines[0].strip()
                reference = next((line.replace("Order", "").strip() for line in lines if "Order" in line), "")

                if reference in seen_refs:
                    continue
                seen_refs.add(reference)

                percent_text = percent_cell.get_text(" ", strip=True).replace("*", "").replace("\n", "").strip()
                percent_value = self.extract_percentage(percent_text)

                consumables_data.append((color, reference, percent_text, percent_value, "Black"))
            except Exception:
                continue

        return consumables_data
