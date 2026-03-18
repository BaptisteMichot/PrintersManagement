# ==========================================
# Validateurs utilitaires
# Validation d'adresses IP, etc.
# ==========================================

import ipaddress


def validate_ip(ip: str) -> bool:
    """
    Valide le format d'une adresse IP.
    
    Args:
        ip (str): Adresse IP à valider
        
    Returns:
        bool: True si l'IP est valide, False sinon
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
