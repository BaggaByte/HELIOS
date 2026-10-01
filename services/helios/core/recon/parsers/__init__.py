# Register and expose all parsers here
from .nmap import parse_nmap_xml

# As we implement functional parsers, import them here
# from .gobuster import parse_gobuster
# from .ffuf import parse_ffuf
# from .masscan import parse_masscan

__all__ = ["parse_nmap_xml"]
