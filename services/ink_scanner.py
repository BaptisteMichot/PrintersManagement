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
import urllib3
from concurrent.futures import ThreadPoolExecutor
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from database.printers import get_printers

# Import des parseurs modulaires
from services.parsers import (
    ModernHPParser,
    M402NParser,
    M451DNParser,
    M404NParser,
    M506Parser,
    P3015DNParser,
    M480Parser,
    M521Parser,
    GenericPrinterParser
)

# ==========================================
# CONSTANTES
# ==========================================

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
        
        # Initialiser les parseurs
        self.modern_hp_parser = ModernHPParser()
        self.m402_parser = M402NParser()
        self.m451_parser = M451DNParser()
        self.m404_parser = M404NParser(self.https_session)
        self.m506_parser = M506Parser()
        self.p3015_parser = P3015DNParser()
        self.m480_parser = M480Parser()
        self.m521_parser = M521Parser()
        self.generic_parser = GenericPrinterParser()

    
    # ==========================================
    # MÉTHODES UTILITAIRES
    # ==========================================

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
        printer_type = printer_type.upper()

        # Mapper modèles vers parseurs
        if any(model in printer_type for model in ["M575", "M776", "M725", "M4555"]):
            return self.modern_hp_parser.parse(html)
        elif "M402" in printer_type:
            return self.m402_parser.parse(html)
        elif "M451" in printer_type:
            return self.m451_parser.parse(html)
        elif "M506" in printer_type:
            return self.m506_parser.parse(html)
        elif "3015" in printer_type:
            return self.p3015_parser.parse(html)
        elif "M480" in printer_type:
            return self.m480_parser.parse(html)
        else:
            # Fallback: parseur générique pour modèles inconnus
            return self.generic_parser.parse(html)

    def fetch_printer_data(self, printer):
        """Récupérer les données de consommables d'une imprimante spécifique."""
        ip = printer["ip"]
        name = printer["name"]
        owner = printer["owner"]
        model = printer["model"]

        info = {"name": name, "user": owner}
        ptype = model.upper()

        try:
            # HP M404 / 4002: API XML en priorité, fallback HTML
            if "M404" in ptype or "4002" in ptype:
                consumables = self.m404_parser.parse_xml(ip)
                if consumables:
                    return ip, info, consumables
                html = self.get_printer_page(ip)
                if html:
                    consumables = self.m404_parser.parse(html)
                    if consumables:
                        return ip, info, consumables
                return ip, info, []

            # HP M521: URL spécifique
            if "M521" in ptype:
                html = self.get_m521_page(ip)
                if html:
                    consumables = self.m521_parser.parse(html)
                    if consumables:
                        return ip, info, consumables
                return ip, info, []

            # HP M506: URL spécifique
            if "M506" in ptype:
                html = self.get_m506_page(ip)
                if html:
                    consumables = self.m506_parser.parse(html)
                    if consumables:
                        return ip, info, consumables
                return ip, info, []

            # HP P3015DN: HTTP uniquement
            if "3015" in ptype:
                html = self.get_3015dn_page(ip)
                if html:
                    consumables = self.p3015_parser.parse(html)
                    if consumables:
                        return ip, info, consumables
                return ip, info, []

            # Autres modèles: URLs génériques + parseur générique comme fallback
            html = self.get_printer_page(ip)
            if html is None:
                return ip, info, []
            consumables = self.parse_by_type(html, ptype)
            return ip, info, consumables
        
        except Exception as e:
            print(f"Error scanning printer {ip} ({model}): {e}")
            return ip, info, []

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

