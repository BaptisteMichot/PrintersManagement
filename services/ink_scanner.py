"""Module de scan des imprimantes réseau pour récupérer les niveaux de toner/encre.

Ce module utilise des requêtes HTTP(S) pour interroger les imprimantes HP sur le réseau
et extraire les informations de consommables (toner/encre). Il supporte plusieurs modèles
d'imprimantes avec des parseurs HTML/XML spécifiques.

Fonctionnalités principales:
- Connexion HTTPS avec certificats auto-signés
- Support de multiples modèles d'imprimantes HP (M575, M776, M402, M451, M404, M506, P3015DN, M480, M521)
- Scannage parallèle avec ThreadPoolExecutor pour performance
- Extraction des pourcentages de toner/encre par couleur
"""

import requests
from bs4 import BeautifulSoup
import urllib3
import re
from concurrent.futures import ThreadPoolExecutor
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from database.printers import get_printers

# ==========================================
# CONFIGURATIONS & CONSTANTES
# ==========================================

# Couleurs hexadécimales pour l'affichage
COLOR_MAP_HEX = {
    "Black": "#000000",
    "Cyan": "#00aeef",
    "Magenta": "#ec008c",
    "Yellow": "#ffd100",
    "Gray": "#808080"
}

# User-Agent standard
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# URLs pour accéder aux imprimantes (par ordre de priorité)
PRINTER_DEFAULT_URLS = [
    "https://{ip}/hp/device/info_deviceStatus.html",
    "https://{ip}/hp/device/",
    "http://{ip}/hp/device/info_deviceStatus.html",
    "http://{ip}/hp/device/",
    "http://{ip}"
]

# Mappage modèle -> couleur pour les modèles monochrome
COLOR_MAPPING = {
    "K": "Black",
    "C": "Cyan",
    "M": "Magenta",
    "Y": "Yellow"
}
# ==========================================
# ADAPTATEUR TLS POUR CERTIFICATS AUTO-SIGNÉS
# ==========================================

class TLSAdapter(HTTPAdapter):
    """Adaptateur personnalisé pour gérer les certificats SSL auto-signés.
    
    Permet les connexions HTTPS vers les imprimantes avec certificats auto-signés
    en désactivant la vérification de nom d'hôte et en utilisant le niveau de sécurité TLS minimal.
    """

    def init_poolmanager(self, *args, **kwargs):
        """Initialiser le gestionnaire de pool avec contexte SSL personnalisé."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        self.poolmanager = PoolManager(*args, ssl_context=ctx, **kwargs)


# ==========================================
# CLASSE PRINCIPALE: PRINT SCANNER
# ==========================================

class PrinterScanner:
    """Gestionnaire centralisé pour scanner les imprimantes réseau."""

    def __init__(self):
        """Initialiser le scanner avec une session HTTPS configurée."""
        self.https_session = requests.Session()
        self.https_session.mount("https://", TLSAdapter())
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    
    # ==========================================
    # MÉTHODES UTILITAIRES
    # ==========================================

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

    def get_printer_page(self, ip, urls=None):
        """Récupérer la page de statut d'une imprimante via plusieurs URL de secours.
        
        Args:
            ip (str): Adresse IP de l'imprimante
            urls (list, optional): URLs à essayer (utilise PRINTER_DEFAULT_URLS par défaut)
            
        Returns:
            str or None: Contenu HTML de la page, ou None si aucune URL réussit
        """
        if urls is None:
            urls = [url.format(ip=ip) for url in PRINTER_DEFAULT_URLS]

        headers = {"User-Agent": USER_AGENT}

        for url in urls:
            try:
                session = self.https_session if url.startswith("https://") else requests.Session()
                response = session.get(url, timeout=3, verify=False, headers=headers)

                if response.status_code == 200:
                    return response.text
            except Exception:
                continue

        return None


    
    # ==========================================
    # PARSEURS PAR MODÈLE D'IMPRIMANTE
    # ==========================================

    def parse_modern_hp(self, soup):
        """Extraire les niveaux d'encre des modèles modernes HP (M575, M776, M725, M4555)."""
        consumables_data = []
        consumables = soup.find_all("div", class_="consumable")

        for consumable in consumables:
            color = consumable.find("h2").text.strip()
            reference = consumable.find("span", class_="partNumber").text.strip()
            ink_percentage = consumable.find("span", class_="plr").text.strip().replace("*", "").strip()
            percent_value = self.extract_percentage(ink_percentage)

            gauge = consumable.find("div", class_="gauge")
            classes = gauge.get("class", [])
            color_name = next((c for c in classes if c in COLOR_MAP_HEX), "Black")

            consumables_data.append((color, reference, ink_percentage, percent_value, color_name))

        return consumables_data

    def parse_m402n(self, soup):
        """Extraire les niveaux d'encre du modèle M402N."""
        consumables_data = []
        seen_refs = set()
        tables = soup.find_all("table", class_="width100")

        for table in tables:
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

        return consumables_data

    def parse_m451(self, soup):
        """Extraire les niveaux d'encre du modèle M451DN."""
        consumables_data = []
        seen_refs = set()
        rows = soup.find_all("tr")

        for row in rows:
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

        return consumables_data

    def parse_m404n_xml(self, ip):
        """Extraire les niveaux d'encre du modèle M404N via API XML."""
        url = f"https://{ip}/DevMgmt/ConsumableConfigDyn.xml"

        try:
            response = self.https_session.get(url, timeout=3, verify=False)
            if response.status_code != 200:
                return []
        except Exception:
            return []

        soup = BeautifulSoup(response.text, "xml")
        consumables_data = []
        items = soup.find_all("ccdyn:ConsumableInfo")

        for item in items:
            color_elem = item.find("dd:ConsumableLabelCode")
            color = color_elem.text if color_elem else "K"
            color_name = COLOR_MAPPING.get(color, "Black")

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

        return consumables_data

    def parse_m404_family_html(self, html):
        """Extraire les niveaux d'encre de la famille M404/4002 via HTML (fallback)."""
        soup = BeautifulSoup(html, "html.parser")
        consumables_data = []
        spans = soup.find_all("span", class_="off-screen-text-cls")

        for span in spans:
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

        return consumables_data

    def parse_m506(self, soup):
        """Extraire les niveaux d'encre du modèle M506."""
        consumables_data = []
        blocks = soup.find_all("div", class_="consumable-block-header")

        for block in blocks:
            color = block.find("h2").text.strip()
            percent_text = block.find("p", class_="data percentage").text.strip().replace("*", "")
            percent_value = self.extract_percentage(percent_text)

            ref_text = block.find("span").text.strip()
            ref_match = re.search(r'\((.*?)\)', ref_text)
            reference = ref_match.group(1) if ref_match else ref_text

            consumables_data.append((color, reference, percent_text, percent_value, "Black"))

        return consumables_data

    def parse_p3015dn(self, soup):
        """Extraire les niveaux d'encre du modèle P3015DN."""
        consumables_data = []
        seen_refs = set()
        blocks = soup.find_all("div", class_="hpGasGaugeBlock")

        for block in blocks:
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

        return consumables_data

    def parse_m480(self, soup):
        """Extraire les niveaux d'encre du modèle M480."""
        consumables_data = []
        seen_refs = set()
        divs = soup.find_all("div", class_="consumable")

        for div in divs:
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

        return consumables_data

    def parse_generic(self, soup):
        """Parseur générique pour les modèles d'imprimantes non reconnus.
        
        Essaie d'extraire les consommables en cherchant des patterns courants :
        - Pourcentages (ex: 50%, 100%, etc.)
        - Noms de couleurs (Cyan, Magenta, Yellow, Black)
        - Divs/spans contenant des infos de consommables
        
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
                 ou liste vide si aucune donnée trouvée
        """
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
    

    
    # ==========================================
    # ROUTEUR DE PARSEURS & SÉLECTION
    # ==========================================

    def get_m506_page(self, ip):
        """Récupérer la page de statut spécifique au modèle M506."""
        url = f"https://{ip}/hp/device/InternalPages/Index?id=SuppliesStatus"
        return self.get_printer_page(ip, urls=[url])

    def get_3015dn_page(self, ip):
        """Récupérer la page de statut du modèle P3015DN (HTTP uniquement)."""
        urls = [
            f"http://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}/hp/device/",
            f"http://{ip}"
        ]
        return self.get_printer_page(ip, urls=urls)

    def get_m521_page(self, ip):
        """Récupérer la page de statut du modèle M521."""
        urls = [
            f"https://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}"
        ]
        return self.get_printer_page(ip, urls=urls)

    def parse_by_type(self, html, printer_type):
        """Sélectionner et appliquer le parseur approprié selon le modèle d'imprimante."""
        soup = BeautifulSoup(html, "html.parser")
        printer_type = printer_type.upper()

        model_parsers = {
            ("M575", "M776", "M725", "M4555"): self.parse_modern_hp,
            ("M402", ): self.parse_m402n,
            ("M451", ): self.parse_m451,
            ("M506", ): self.parse_m506,
            ("3015", ): self.parse_p3015dn,
            ("M480", ): self.parse_m480,
        }

        for models, parser in model_parsers.items():
            if any(model in printer_type for model in models):
                return parser(soup)

        # Fallback: parseur générique pour modèles inconnus
        return self.parse_generic(soup)

    def fetch_printer_data(self, printer):
        """Récupérer les données de consommables d'une imprimante spécifique."""
        ip = printer["ip"]
        name = printer["name"]
        owner = printer["owner"]
        model = printer["model"]

        info = {"name": name, "user": owner}
        ptype = model.upper()

        # HP M404 / 4002: API XML en priorité, fallback HTML
        if "M404" in ptype or "4002" in ptype:
            consumables = self.parse_m404n_xml(ip)
            if consumables:
                return ip, info, consumables
            html = self.get_printer_page(ip)
            if html:
                consumables = self.parse_m404_family_html(html)
                if consumables:
                    return ip, info, consumables
            return ip, info, []

        # HP M521: URL spécifique
        if "M521" in ptype:
            html = self.get_m521_page(ip)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                consumables = self.parse_m402n(soup)
                if consumables:
                    return ip, info, consumables
            return ip, info, []

        # HP M506: URL spécifique
        if "M506" in ptype:
            html = self.get_m506_page(ip)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                consumables = self.parse_m506(soup)
                if consumables:
                    return ip, info, consumables
            return ip, info, []

        # HP P3015DN: HTTP uniquement
        if "3015" in ptype:
            html = self.get_3015dn_page(ip)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                consumables = self.parse_p3015dn(soup)
                if consumables:
                    return ip, info, consumables
            return ip, info, []

        # Autres modèles: URLs génériques + parseur générique comme fallback
        html = self.get_printer_page(ip)
        if html is None:
            return ip, info, []
        consumables = self.parse_by_type(html, ptype)
        return ip, info, consumables

    def scan_printers(self):
        """Scanner parallèlement toutes les imprimantes de la base de données.
        
        Utilise ThreadPoolExecutor pour requêtes parallèles avec max 40 workers.
        
        Returns:
            dict: Dictionnaire avec résultats indexés par adresse IP
        """
        printers = get_printers()
        results = {}

        with ThreadPoolExecutor(max_workers=40) as executor:
            futures = {
                executor.submit(self.fetch_printer_data, printer): printer
                for printer in printers
            }
            for future in futures:
                printer = futures[future]
                ip, info, consumables = future.result()
                results[ip] = {
                    "info": info,
                    "consumables": consumables,
                    "db_name": printer["name"],
                    "db_owner": printer["owner"],
                    "db_model": printer["model"]
                }

        return results


# ==========================================
# FONCTION PUBLIQUE
# ==========================================

def run_scanner():
    """Fonction principale de scan des imprimantes.
    
    Returns:
        dict: Dictionnaire avec les résultats du scan par adresse IP
    """
    scanner = PrinterScanner()
    return scanner.scan_printers()

