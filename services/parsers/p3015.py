# ==========================================
# Parseur pour modèle HP P3015DN
# ==========================================

import re
from services.parsers.base import BasePrinterParser


class P3015DNParser(BasePrinterParser):
    """Parseur pour le modèle P3015DN."""
    
    def parse(self, html):
        """Extraire les niveaux d'encre du modèle P3015DN."""
        soup = self.parse_html(html)
        consumables_data = []
        seen_refs = set()
        blocks = soup.find_all("div", class_="hpGasGaugeBlock")

        for block in blocks:
            try:
                span = block.find("span")
                if not span:
                    continue

                full_text = span.get_text(" ", strip=True)
                lines = full_text.split("\n") if "\n" in full_text else [full_text]
                first_line = lines[0].strip()

                percent_match = re.search(r'(\d+)%', first_line)
                if not percent_match:
                    continue

                percent_value = int(percent_match.group(1))
                percent_text = f"{percent_value}%"

                color_name = "Black"
                if "Cyan" in first_line:
                    color_name = "Cyan"
                elif "Magenta" in first_line:
                    color_name = "Magenta"
                elif "Yellow" in first_line:
                    color_name = "Yellow"

                reference = lines[1].strip() if len(lines) > 1 else ""
                if "%" in first_line:
                    ref_match = re.search(r'%\*?[\s\n]*(.+)', first_line)
                    if ref_match:
                        reference = ref_match.group(1).strip()

                if reference in seen_refs:
                    continue
                seen_refs.add(reference)

                consumables_data.append((color_name, reference, percent_text, percent_value, color_name))
            except Exception:
                continue

        return consumables_data
