from typing import Dict, Any, List
from helios.core.web_security.jwt_analyzer import analyze_jwt
from helios.core.web_security.http_analyzer import analyze_http_response
from helios.core.web_security.oauth_analyzer import analyze_oauth_request
from helios.core.web_security.saml_analyzer import analyze_saml_response
from helios.core.web_security.graphql_analyzer import analyze_graphql_schema
from helios.core.web_security.openapi_analyzer import analyze_openapi_spec


class WebSecurityDetector:
    """
    Orchestrates web security analyzers for various payloads.
    """

    def detect_jwt(self, token: str) -> List[Dict[str, Any]]:
        return analyze_jwt(token)

    def detect_http(
        self, headers: Dict[str, str], url: str = ""
    ) -> List[Dict[str, Any]]:
        return analyze_http_response(headers, url)

    def detect_oauth(
        self, url: str, params: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        return analyze_oauth_request(url, params)

    def detect_saml(self, xml_data: str) -> List[Dict[str, Any]]:
        return analyze_saml_response(xml_data)

    def detect_graphql(self, schema_json: str) -> List[Dict[str, Any]]:
        return analyze_graphql_schema(schema_json)

    def detect_openapi(self, spec_content: str) -> List[Dict[str, Any]]:
        return analyze_openapi_spec(spec_content)


detector = WebSecurityDetector()
