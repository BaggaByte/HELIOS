import re
from typing import List

ENDPOINT_REGEX = re.compile(
    r"""(?i)(?:(?:https?|ftp)://[^\s"'<>]+|(?:/[a-z0-9\-._~%!$&'()*+,;=:@]+)+/?)"""
)

def find_endpoints(js_code: str) -> List[str]:
    """
    Extracts URLs and absolute/relative paths from JS code that might be API endpoints.
    """
    matches = ENDPOINT_REGEX.findall(js_code)
    
    # Filter out obvious false positives
    filtered = []
    for match in matches:
        # Ignore common non-endpoint strings
        if len(match) < 4: continue
        if match.startswith('//'): continue # Likely a comment or protocol relative (too noisy)
        if match in ['/div', '/span', '/a', '/p', '/li', '/ul', 'http://www.w3.org/2000/svg']: continue
        
        filtered.append(match)
        
    return list(set(filtered))
