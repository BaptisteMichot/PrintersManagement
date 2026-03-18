# ==========================================
# Parseur pour modèle HP M521
# (réutilise le parseur M402N pour le corps)
# ==========================================

from services.parsers.m402 import M402NParser


class M521Parser(M402NParser):
    """Parseur pour le modèle M521 (hérite de M402N)."""
    pass
