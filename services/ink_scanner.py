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
    
def run_scanner():
    """Fonction principale de scan des imprimantes.
    
    Configure une session HTTPS avec support des certificats auto-signés,
    initialise les définitions de couleurs et les fonctions de parsage spécifiques
    à chaque modèle d'imprimante, puis déclenche le scan parallèle.
    
    Returns:
        dict: Dictionnaire avec les résultats du scan par adresse IP
    """
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

            self.poolmanager = PoolManager(
                *args,
                ssl_context=ctx,
                **kwargs
            )

    https_session = requests.Session()
    https_session.mount("https://", TLSAdapter())

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    hexa_colors = {
        "Black": "#000000",
        "Cyan": "#00aeef",
        "Magenta": "#ec008c",
        "Yellow": "#ffd100",
        "Gray": "#808080"
    }

    def extract_percentage(text):
        """Extraire une valeur numérique représentant un pourcentage d'un texte.
        
        Args:
            text (str): Texte contenant un pourcentage
            
        Returns:
            int: Valeur numérique extraite (0 si aucune valeur trouvée)
        """
        match = re.search(r'\d+', text)
        if match:
            return int(match.group())
        return 0


    def get_printer_page(ip):
        """Récupérer la page de statut d'une imprimante via plusieurs URL de secours.
        
        Essaie plusieurs chemins HTTP(S) courants pour les imprimantes HP.
        Retourne le contenu HTML de la première réponse réussie.
        
        Args:
            ip (str): Adresse IP de l'imprimante
            
        Returns:
            str or None: Contenu HTML de la page, ou None si aucune URL réussit
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }

        urls = [
            f"https://{ip}/hp/device/info_deviceStatus.html",
            f"https://{ip}/hp/device/",
            f"http://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}/hp/device/",
            f"http://{ip}"
        ]

        for url in urls:
            try:
                session = https_session if url.startswith("https://") else requests.Session()
                r = session.get(url, timeout=3, verify=False, headers=headers)

                if r.status_code == 200:
                    return r.text

            except:
                pass

        return None


    ################################
    # MODERN HP (M575 / M776)
    ################################
    # Parseur pour les modèles modernes d'HP avec interface web HTML5

    def parse_modern_hp(soup):
        """Extraire les niveaux de consommables des modèles modernes HP (M575, M776).
        
        Args:
            soup (BeautifulSoup): Objet analysé contenant le HTML de la page
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        consumables_data = []

        consumables = soup.find_all("div", class_="consumable")

        for consumable in consumables:

            color = consumable.find("h2").text.strip()

            reference = consumable.find("span", class_="partNumber").text.strip()

            ink_percentage = consumable.find("span", class_="plr").text.strip()
            ink_percentage = ink_percentage.replace("*", "").strip()

            percent_value = extract_percentage(ink_percentage)

            gauge = consumable.find("div", class_="gauge")
            classes = gauge.get("class")

            color_name = None
            for c in classes:
                if c in hexa_colors:
                    color_name = c

            consumables_data.append(
                (color, reference, ink_percentage, percent_value, color_name)
            )

        return consumables_data


    ################################
    # M402N
    ################################
    # Parseur spécifique pour le modèle M402N (monochrome)

    def parse_m402n(soup):
        """Extraire les niveaux de consommables du modèle M402N.
        
        Args:
            soup (BeautifulSoup): Objet analysé contenant le HTML de la page
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

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

            reference = ""
            for line in lines:
                if "Order" in line:
                    reference = line.replace("Order", "").strip()

            if reference in seen_refs:
                continue
            seen_refs.add(reference)

            percent_text = percent_cell.get_text(" ", strip=True)
            percent_text = percent_text.replace("*", "").replace("\n", "").strip()

            percent_value = extract_percentage(percent_text)

            consumables_data.append(
                (color, reference, percent_text, percent_value, "Black")
            )

        return consumables_data


    ################################
    # M451DN
    ################################
    # Parseur spécifique pour le modèle M451DN (couleur)

    def parse_m451(soup):
        """Extraire les niveaux de consommables du modèle M451DN.
        
        Args:
            soup (BeautifulSoup): Objet analysé contenant le HTML de la page
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        consumables_data = []
        seen_refs = set()

        rows = soup.find_all("tr")

        for row in rows:

            cells = row.find_all("td")

            if len(cells) != 2:
                continue

            name_cell = cells[0]
            percent_cell = cells[1]

            # ignorer les lignes gauge
            if percent_cell.find("table"):
                continue

            text = name_cell.get_text("\n", strip=True)

            if "Cartridge" not in text:
                continue

            lines = text.split("\n")

            color = lines[0].strip()

            reference = ""
            for line in lines:
                if "Order" in line:
                    reference = line.replace("Order", "").strip()

            if reference == "" or reference in seen_refs:
                continue

            seen_refs.add(reference)

            percent_text = percent_cell.get_text(" ", strip=True)
            percent_text = percent_text.replace("*", "").strip()

            percent_value = extract_percentage(percent_text)

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

            consumables_data.append(
                (color, reference, percent_text, percent_value, color_name)
            )

        return consumables_data


    ################################
    # M404N (XML API)
    ################################
    # Parseur pour M404N utilisant l'API XML de l'imprimante

    def parse_m404n(ip):
        """Extraire les niveaux de consommables du modèle M404N via API XML.
        
        Args:
            ip (str): Adresse IP de l'imprimante
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        url = f"https://{ip}/DevMgmt/ConsumableConfigDyn.xml"

        try:
            r = https_session.get(url, timeout=3, verify=False)
            if r.status_code != 200:
                return []
        except:
            return []

        soup = BeautifulSoup(r.text, "xml")
        consumables_data = []

        items = soup.find_all("ccdyn:ConsumableInfo")

        for item in items:

            color = item.find("dd:ConsumableLabelCode")
            color = color.text if color else "K"

            color_map = {
                "K": "Black",
                "C": "Cyan",
                "M": "Magenta",
                "Y": "Yellow"
            }

            color_name = color_map.get(color, "Black")

            reference = item.find("dd:ProductNumber")
            reference = reference.text if reference else "N/A"

            percent = item.find("dd:ConsumablePercentageLevelRemaining")

            if percent:
                percent_value = int(percent.text)
                percent_text = f"{percent_value}%"
            else:
                percent_value = 0
                percent_text = "0%"

            consumables_data.append(
                (color_name, reference, percent_text, percent_value, color_name)
            )

        return consumables_data
    

    def parse_m404_family(html):
        """Extraire les niveaux de consommables de la famille M404/4002 via HTML.
        
        Fallback HTML si l'API XML n'est pas disponible.
        
        Args:
            html (str): Contenu HTML de la page de statut
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        soup = BeautifulSoup(html, "html.parser")

        consumables_data = []

        spans = soup.find_all("span", class_="off-screen-text-cls")

        for s in spans:

            text = s.get_text()

            match = re.search(r"(\d+)%", text)

            if not match:
                continue

            percent_value = int(match.group(1))
            percent_text = f"{percent_value}%"

            if "Black" in text:
                color = "Black"

            elif "Cyan" in text:
                color = "Cyan"

            elif "Magenta" in text:
                color = "Magenta"

            elif "Yellow" in text:
                color = "Yellow"

            else:
                continue

            consumables_data.append(
                (color, "", percent_text, percent_value, color)
            )

        return consumables_data


    ################################
    # M506
    ################################
    # Parseur spécifique pour le modèle M506 (haute performance)
    
    def parse_m506(soup):
        """Extraire les niveaux de consommables du modèle M506.
        
        Args:
            soup (BeautifulSoup): Objet analysé contenant le HTML de la page
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        consumables_data = []

        blocks = soup.find_all("div", class_="consumable-block-header")

        for block in blocks:

            color = block.find("h2").text.strip()

            percent_text = block.find("p", class_="data percentage").text.strip()
            percent_text = percent_text.replace("*", "")

            percent_value = extract_percentage(percent_text)

            ref_text = block.find("span").text.strip()

            ref_match = re.search(r'\((.*?)\)', ref_text)
            reference = ref_match.group(1) if ref_match else ref_text

            consumables_data.append(
                (color, reference, percent_text, percent_value, "Black")
            )

        return consumables_data
    

    def get_m506_page(ip):
        """Récupérer la page de statut spécifique au modèle M506.
        
        Args:
            ip (str): Adresse IP de l'imprimante
            
        Returns:
            str or None: Contenu HTML de la page, ou None si la requête échoue
        """
        url = f"https://{ip}/hp/device/InternalPages/Index?id=SuppliesStatus"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            r = https_session.get(url, timeout=3, verify=False, headers=headers)
            if r.status_code == 200:
                return r.text
        except:
            pass

        return None


    ################################
    # P3015DN
    ################################
    # Parseur spécifique pour le modèle P3015DN (ancien LaserJet)
    
    def parse_3015dn(soup):
        """Extraire les niveaux de consommables du modèle P3015DN.
        
        Args:
            soup (BeautifulSoup): Objet analysé contenant le HTML de la page
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        consumables_data = []
        seen_refs = set()

        # Look for divs with class="hpGasGaugeBlock"
        blocks = soup.find_all("div", class_="hpGasGaugeBlock")

        for block in blocks:

            span = block.find("span")
            if not span:
                continue

            # Get full text: "Black Cartridge  10%*" or similar
            full_text = span.get_text(" ", strip=True)
            lines = full_text.split("\n") if "\n" in full_text else [full_text]

            # First line has color + percent
            first_line = lines[0].strip()

            # Extract percentage
            percent_match = re.search(r'(\d+)%', first_line)
            if not percent_match:
                continue

            percent_value = int(percent_match.group(1))
            percent_text = f"{percent_value}%"

            # Extract color (usually first word or word before "Cartridge")
            color_name = "Black"
            if "Cyan" in first_line:
                color_name = "Cyan"
            elif "Magenta" in first_line:
                color_name = "Magenta"
            elif "Yellow" in first_line:
                color_name = "Yellow"
            elif "Black" in first_line:
                color_name = "Black"

            # Extract cartridge reference number (second line or after <br>)
            reference = ""
            if len(lines) > 1:
                reference = lines[1].strip()
            else:
                # Try to find after percentage
                ref_match = re.search(r'%\*?[\s\n]*(.+)', first_line)
                if ref_match:
                    reference = ref_match.group(1).strip()

            if reference in seen_refs:
                continue

            seen_refs.add(reference)

            consumables_data.append(
                (color_name, reference, percent_text, percent_value, color_name)
            )

        return consumables_data
    

    def get_3015dn_page(ip):
        """Récupérer la page de statut du modèle P3015DN (HTTP uniquement).
        
        Le P3015DN ne supporte pas HTTPS, seul HTTP est utilisé.
        
        Args:
            ip (str): Adresse IP de l'imprimante
            
        Returns:
            str or None: Contenu HTML de la page, ou None si la requête échoue
        """
        # P3015DN doesn't support HTTPS, try HTTP only
        urls = [
            f"http://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}/hp/device/",
            f"http://{ip}"
        ]

        for url in urls:
            try:
                r = https_session.get(url, timeout=3, verify=False)
                if r.status_code == 200:
                    return r.text
            except:
                pass

        return None


    ################################
    # M480 (COLOR LASERJET)
    ################################
    # Parseur spécifique pour le modèle M480 (LaserJet couleur)
    
    def parse_m480(soup):
        """Extraire les niveaux de consommables du modèle M480.
        
        Args:
            soup (BeautifulSoup): Objet analysé contenant le HTML de la page
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        consumables_data = []
        seen_refs = set()

        # Look for divs with class="consumable"
        divs = soup.find_all("div", class_="consumable")

        for div in divs:

            text = div.get_text(" ", strip=True)
            
            # Text format: "Black Cartridge Order 415A (W2030A) 50%* 50%"
            # Extract color
            color_name = "Black"
            if "Cyan" in text:
                color_name = "Cyan"
            elif "Magenta" in text:
                color_name = "Magenta"
            elif "Yellow" in text:
                color_name = "Yellow"

            # Extract reference from parentheses
            reference = ""
            ref_match = re.search(r'\(([^)]+)\)', text)
            if ref_match:
                reference = ref_match.group(1)

            if reference in seen_refs:
                continue

            seen_refs.add(reference)

            # Extract percentage - look for pattern like "50%*" or "<10%*"
            # The actual percentage value comes after the asterisk pattern
            percent_match = re.search(r'([<]?\d+)%\*?\s*(\d+)%', text)
            if percent_match:
                # Take the second number (the clean percentage)
                percent_value = int(percent_match.group(2))
            else:
                # Fallback: try to find just a number with %
                percent_match = re.search(r'(\d+)%', text)
                if percent_match:
                    percent_value = int(percent_match.group(1))
                else:
                    continue

            percent_text = f"{percent_value}%"

            consumables_data.append(
                (color_name, reference, percent_text, percent_value, color_name)
            )

        return consumables_data
    

    ######################
    # M521
    ######################
    # Récupération de page spécifique au modèle M521 (LaserJet monochrome)
    
    def get_m521_page(ip):
        """Récupérer la page de statut du modèle M521.
        
        Args:
            ip (str): Adresse IP de l'imprimante
            
        Returns:
            str or None: Contenu HTML de la page, ou None si la requête échoue
        """
        urls = [
            f"https://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}/hp/device/info_deviceStatus.html",
            f"http://{ip}"
        ]

        for url in urls:
            try:
                session = https_session if url.startswith("https://") else requests.Session()
                r = session.get(url, timeout=3, verify=False)
                if r.status_code == 200:
                    return r.text
            except:
                pass

        return None


    ################################
    # CHOOSE PARSER
    ################################
    # Routeur pour sélectionner le parseur approprié selon le modèle d'imprimante

    def parse_by_type(html, printer_type):
        """Sélectionner et appliquer le parseur approprié selon le modèle d'imprimante.
        
        Args:
            html (str): Contenu HTML de la page de statut
            printer_type (str): Modèle de l'imprimante (ex: 'M575', 'M402N')
            
        Returns:
            list: Liste de tuples (couleur, référence, pourcentage_texte, pourcentage_valeur, nom_couleur)
        """

        soup = BeautifulSoup(html, "html.parser")

        printer_type = printer_type.upper()

        if "M575" in printer_type or "M776" in printer_type or "M725" in printer_type or "M4555" in printer_type:
            return parse_modern_hp(soup)

        if "M402" in printer_type:
            return parse_m402n(soup)

        if "M451" in printer_type:
            return parse_m451(soup)

        if "M506" in printer_type:
            return parse_m506(soup)

        if "3015" in printer_type:
            return parse_3015dn(soup)

        if "M480" in printer_type:
            return parse_m480(soup)

        return []


    def fetch_printer_data(printer):
        """Récupérer les données de consommables d'une imprimante spécifique.
        
        Gère les appels API XML et les fallbacks HTML selon le modèle,
        avec des URL spécifiques pour certains modèles.
        
        Args:
            printer (dict): Dictionnaire avec clés 'ip', 'name', 'owner', 'model'
            
        Returns:
            tuple: (ip, info_dict, consumables_list)
        """
        ip = printer["ip"]
        name = printer["name"]
        owner = printer["owner"]
        model = printer["model"]

        info = {
            "name": name,
            "user": owner
        }

        ptype = model.upper()

        # HP M404 / 4002 family - Essayer d'abord l'API XML, puis fallback HTML
        if "M404" in ptype or "4002" in ptype:
            # 1. Essayer l'API XML
            consumables = parse_m404n(ip)
            if consumables:
                return ip, info, consumables
            # 2. Fallback sur l'analyse HTML si l'API échoue
            html = get_printer_page(ip)
            if html:
                consumables = parse_m404_family(html)
                return ip, info, consumables
            return ip, info, []
        
        # HP M521 - Utilise la même analyse HTML que M402
        if "M521" in ptype:
            html = get_m521_page(ip)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                consumables = parse_m402n(soup)
                return ip, info, consumables
            return ip, info, []

        # HP M506 - Utilise une URL spécifique pour le M506
        if "M506" in ptype:
            html = get_m506_page(ip)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                consumables = parse_m506(soup)
                return ip, info, consumables
            return ip, info, []

        # HP P3015DN - Modèle ancien, HTTP uniquement
        if "3015" in ptype:
            html = get_3015dn_page(ip)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                consumables = parse_3015dn(soup)
                return ip, info, consumables
            return ip, info, []

        # Fallback pour les autres modèles - essayer URLs génériques
        html = get_printer_page(ip)
        if html is None:
            return ip, info, []
        # Utiliser le routeur pour sélectionner le bon parseur
        consumables = parse_by_type(html, ptype)
        return ip, info, consumables



    ################################
    # SCAN PRINTERS
    ################################
    # Scannage parallèle de tous les imprimantes

    def scan_printers():
        """Scanner parallèlement toutes les imprimantes de la base de données.
        
        Utilise ThreadPoolExecutor pour requêtes parallèles avec max 40 workers.
        Chaque imprimante est traitée indépendamment et le résultat est collecté.
        
        Returns:
            dict: Dictionnaire avec résultats indexés par adresse IP
                  Format: {"ip": {"info": {...}, "consumables": [...]}}
        """
        # Récupérer la liste complète des imprimantes depuis la base de données
        printers = get_printers()
        results = {}
        # Exécution parallèle avec 40 workers maximum pour ne pas surcharger le réseau
        with ThreadPoolExecutor(max_workers=40) as executor:
            # Soumettre tous les appels de fetch parallèlement
            futures = {
                executor.submit(fetch_printer_data, printer): printer
                for printer in printers
            }
            # Collecter les résultats au fur et à mesure que les futures se terminent
            for future in futures:
                printer = futures[future]
                ip, info, consumables = future.result()
                # Structurer les résultats avec métadonnées
                results[ip] = {
                    "info": info,
                    "consumables": consumables,
                    "db_name": printer["name"],
                    "db_owner": printer["owner"],
                    "db_model": printer["model"]
                }
        return results
    
    return scan_printers()

