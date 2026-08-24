def calculate_cvss3_base_score(vector: str) -> float:
    """
    Parses a CVSSv3 vector and calculates a rough base score.
    In a real system, you'd want to use the 'cvss' PyPI package for accurate calculations.
    """
    if not vector.startswith("CVSS:3"):
        return 0.0

    # Simplified mock for demonstration
    if "C:H" in vector and "I:H" in vector and "A:H" in vector:
        return 9.8
    elif "C:L" in vector and "I:N" in vector and "A:N" in vector:
        return 3.3
    
    return 5.0  # Default fallback score

def get_severity_from_score(score: float) -> str:
    """Maps CVSS score to qualitative severity ratings."""
    if score == 0.0:
        return "INFO"
    elif 0.1 <= score <= 3.9:
        return "LOW"
    elif 4.0 <= score <= 6.9:
        return "MEDIUM"
    elif 7.0 <= score <= 8.9:
        return "HIGH"
    elif 9.0 <= score <= 10.0:
        return "CRITICAL"
    return "UNKNOWN"
