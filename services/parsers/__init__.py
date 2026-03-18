# Parsers package
from services.parsers.modern_hp import ModernHPParser
from services.parsers.m402 import M402NParser
from services.parsers.m451 import M451DNParser
from services.parsers.m404 import M404NParser
from services.parsers.m506 import M506Parser
from services.parsers.p3015 import P3015DNParser
from services.parsers.m480 import M480Parser
from services.parsers.m521 import M521Parser
from services.parsers.generic import GenericPrinterParser

__all__ = [
    'ModernHPParser',
    'M402NParser',
    'M451DNParser',
    'M404NParser',
    'M506Parser',
    'P3015DNParser',
    'M480Parser',
    'M521Parser',
    'GenericPrinterParser'
]
