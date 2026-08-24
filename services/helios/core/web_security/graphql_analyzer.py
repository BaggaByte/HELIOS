from typing import Dict, Any, List

def analyze_graphql_schema(schema_json: str) -> List[Dict[str, Any]]:
    findings = []
    
    if "__schema" in schema_json or "IntrospectionQuery" in schema_json:
        findings.append({
            "title": "GraphQL Introspection Enabled",
            "description": "GraphQL Introspection is enabled. This exposes the entire API schema to attackers, making it trivial to map out the attack surface.",
            "severity": "medium",
            "confidence": "high",
            "cwe_id": "CWE-200"
        })
        
    return findings
