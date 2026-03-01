"""
Amazon Nova Pro Integration - Real AI-Powered Security Analysis
Uses Amazon Nova Pro for intelligent vulnerability assessment
"""

import boto3
import logging
from typing import Dict, List, Optional
import asyncio
import httpx
import re
import ssl
import socket
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class NovaProClient:
    """
    Amazon Nova Pro Client for AI-powered security analysis
    Model: amazon.nova-pro-v1:0
    """
    
    def __init__(self):
        """Initialize Bedrock Runtime client for Nova Pro"""
        try:
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
            self.model_id = "amazon.nova-pro-v1:0"
            logger.info("Nova Pro client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Nova Pro client: {e}")
            raise
    
    async def analyze_with_ai(self, prompt: str) -> str:
        """
        Analyze security findings with Nova Pro AI
        
        Args:
            prompt: Security analysis prompt
            
        Returns:
            AI-generated analysis and recommendations
        """
        try:
            body = json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 1000,
                    "temperature": 0.3,  # Lower temperature for more focused security analysis
                    "top_p": 0.9
                }
            })
            
            response = await asyncio.to_thread(
                self.bedrock.invoke_model,
                modelId=self.model_id,
                body=body
            )
            
            result = json.loads(response['body'].read())
            text_response = result['output']['message']['content'][0]['text']
            
            logger.info(f"Nova Pro analysis completed ({result['usage']['totalTokens']} tokens)")
            return text_response
            
        except Exception as e:
            logger.error(f"Nova Pro analysis failed: {e}")
            return f"AI analysis unavailable: {str(e)}"


class SecurityAnalysisAgent:
    """
    Comprehensive security reconnaissance agent with AI-enhanced analysis
    """
    
    def __init__(self):
        self.ai_client = NovaProClient()
        self.session_id = None
        logger.info("Security Analysis Agent initialized with Nova Pro")
    
    async def start_session(self):
        """Initialize analysis session"""
        logger.info("Starting security analysis session")
        try:
            self.session_id = f"session-{int(asyncio.get_event_loop().time())}"
            return self.session_id
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise
    
    async def navigate_to(self, url: str) -> Dict:
        """Verify URL accessibility"""
        logger.info(f"Checking accessibility: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                return {
                    "success": True,
                    "url": url,
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200
                }
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def discover_endpoints(self, base_url: str) -> List[str]:
        """Discover common endpoints"""
        logger.info(f"Discovering endpoints for: {base_url}")
        
        base_url = base_url.rstrip('/')
        
        # Common endpoints to test
        endpoints = [
            # API endpoints
            f"{base_url}/api",
            f"{base_url}/api/v1",
            f"{base_url}/api/v2",
            f"{base_url}/graphql",
            f"{base_url}/rest",
            
            # Admin/Auth endpoints
            f"{base_url}/admin",
            f"{base_url}/login",
            f"{base_url}/dashboard",
            f"{base_url}/wp-admin",
            
            # Sensitive files
            f"{base_url}/.git/config",
            f"{base_url}/.env",
            f"{base_url}/config.php",
            f"{base_url}/wp-config.php",
            f"{base_url}/phpinfo.php",
            
            # Config/Info
            f"{base_url}/robots.txt",
            f"{base_url}/sitemap.xml",
            f"{base_url}/.well-known/security.txt",
        ]
        
        return endpoints
    
    async def capture_screenshot(self, url: str) -> str:
        """Placeholder for screenshot capture"""
        logger.info(f"Screenshot would be captured for: {url}")
        return f"/screenshots/placeholder.png"
    
    async def check_security_headers(self, url: str) -> Dict:
        """Analyze security headers"""
        logger.info(f"Checking security headers for: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                headers = response.headers
                
                required_headers = [
                    "Content-Security-Policy",
                    "X-Frame-Options",
                    "Strict-Transport-Security",
                    "X-Content-Type-Options",
                    "Referrer-Policy",
                    "Permissions-Policy"
                ]
                
                missing = [h for h in required_headers if h not in headers]
                
                weak = []
                if "X-XSS-Protection" in headers and headers["X-XSS-Protection"] == "0":
                    weak.append({
                        "header": "X-XSS-Protection",
                        "value": "0",
                        "issue": "XSS protection explicitly disabled"
                    })
                
                return {
                    "missing_headers": missing,
                    "weak_headers": weak,
                    "score": max(0, 100 - len(missing) * 15),
                    "all_headers": dict(headers)
                }
        except Exception as e:
            logger.error(f"Header analysis failed: {e}")
            return {"missing_headers": [], "weak_headers": [], "score": 0, "all_headers": {}}
    
    async def enhance_finding_with_ai(self, finding_data: Dict) -> Dict:
        """
        Use Nova Pro AI to enhance security finding with deeper analysis
        
        Args:
            finding_data: Basic finding information
            
        Returns:
            Enhanced finding with AI-generated insights
        """
        logger.info(f"Enhancing finding with Nova Pro AI: {finding_data.get('title', 'Unknown')}")
        
        prompt = f"""You are a security expert analyzing a vulnerability finding. Provide detailed analysis in plain text format (NO MARKDOWN, NO ASTERISKS, NO SPECIAL FORMATTING).

**Finding Title:** {finding_data.get('title', 'Unknown')}
**Category:** {finding_data.get('category', 'Unknown')}
**Description:** {finding_data.get('description', 'No description')}

Provide your analysis in this exact format:

IMPLICATIONS: Write 2-3 sentences explaining the real-world attack scenarios. Be specific about what attackers can do, what data is at risk, and the business impact. Use plain sentences without any markdown formatting or special characters.

RECOMMENDATIONS: Provide 3-5 specific, actionable steps to fix this issue. Include configuration examples where helpful. Write as numbered sentences (1. 2. 3.) but use plain text only - no asterisks, no bold, no markdown.

SEVERITY: State one word only - either Critical, High, Medium, or Low.

Remember: Use only plain text. No markdown. No asterisks. No bold. No special formatting.
"""
        
        try:
            ai_response = await self.ai_client.analyze_with_ai(prompt)
            
            # Clean up any remaining markdown formatting
            ai_response = self._clean_markdown(ai_response)
            
            # Parse AI response
            implications = "AI analysis in progress..."
            recommendations = "Review finding details and apply security best practices."
            severity = finding_data.get('severity', 'medium')
            
            # Extract structured data from AI response
            if "IMPLICATIONS:" in ai_response:
                parts = ai_response.split("IMPLICATIONS:")
                if len(parts) > 1:
                    impl_part = parts[1].split("RECOMMENDATIONS:")[0].strip()
                    implications = impl_part
            
            if "RECOMMENDATIONS:" in ai_response:
                parts = ai_response.split("RECOMMENDATIONS:")
                if len(parts) > 1:
                    rec_part = parts[1].split("SEVERITY:")[0].strip()
                    recommendations = rec_part
            
            if "SEVERITY:" in ai_response:
                parts = ai_response.split("SEVERITY:")
                if len(parts) > 1:
                    sev_part = parts[1].strip().lower()
                    if any(s in sev_part for s in ['critical', 'high', 'medium', 'low']):
                        for sev in ['critical', 'high', 'medium', 'low']:
                            if sev in sev_part:
                                severity = sev
                                break
            
            return {
                "implications": implications,
                "recommendations": recommendations,
                "severity": severity,
                "ai_enhanced": True
            }
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            # Fallback to basic analysis
            return {
                "implications": finding_data.get('implications', 'Security risk identified.'),
                "recommendations": finding_data.get('recommendations', 'Review and remediate.'),
                "severity": finding_data.get('severity', 'medium'),
                "ai_enhanced": False
            }
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text"""
        import re
        
        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        
        # Remove italic (*text* or _text_)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove code blocks (```text```)
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove markdown headers (### Header)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    async def analyze_ssl_tls(self, url: str) -> Dict:
        """Analyze SSL/TLS configuration"""
        logger.info(f"Analyzing SSL/TLS for: {url}")
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            if parsed.scheme != 'https':
                return {
                    "enabled": False,
                    "issues": ["Site not using HTTPS"]
                }
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    protocol = ssock.version()
                    cipher = ssock.cipher()
                    
                    issues = []
                    if protocol in ['TLSv1', 'TLSv1.1']:
                        issues.append(f"Outdated protocol: {protocol}")
                    
                    return {
                        "enabled": True,
                        "protocol": protocol,
                        "cipher": cipher[0] if cipher else None,
                        "issues": issues
                    }
        except Exception as e:
            logger.error(f"SSL/TLS analysis failed: {e}")
            return {"enabled": False, "issues": [str(e)]}
    
    async def analyze_cookies(self, url: str) -> Dict:
        """Analyze cookie security"""
        logger.info(f"Analyzing cookies for: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                insecure_cookies = []
                for cookie_header in response.headers.get_list('set-cookie'):
                    cookie_lower = cookie_header.lower()
                    
                    issues = []
                    if 'secure' not in cookie_lower:
                        issues.append("Missing Secure flag")
                    if 'httponly' not in cookie_lower:
                        issues.append("Missing HttpOnly flag")
                    if 'samesite' not in cookie_lower:
                        issues.append("Missing SameSite attribute")
                    
                    if issues:
                        cookie_name = cookie_header.split('=')[0]
                        insecure_cookies.append({
                            "name": cookie_name,
                            "issues": issues
                        })
                
                return {"insecure_cookies": insecure_cookies}
        except Exception as e:
            logger.error(f"Cookie analysis failed: {e}")
            return {"insecure_cookies": []}
    
    async def check_cors(self, url: str) -> Dict:
        """Check CORS configuration"""
        logger.info(f"Checking CORS for: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.options(
                    url,
                    headers={"Origin": "https://evil.com"}
                )
                
                issues = []
                acao = response.headers.get('Access-Control-Allow-Origin')
                
                if acao == '*':
                    issues.append("CORS allows all origins (wildcard)")
                elif acao and 'evil.com' in acao:
                    issues.append("CORS reflects arbitrary origin")
                
                acac = response.headers.get('Access-Control-Allow-Credentials')
                if acac == 'true' and acao == '*':
                    issues.append("CORS allows credentials with wildcard origin")
                
                return {"issues": issues}
        except Exception as e:
            logger.error(f"CORS check failed: {e}")
            return {"issues": []}
    
    async def detect_technologies(self, url: str) -> Dict:
        """Detect web technologies"""
        logger.info(f"Detecting technologies for: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                headers = response.headers
                body = response.text
                
                technologies = []
                
                server = headers.get('Server', '')
                if server:
                    technologies.append(f"Server: {server}")
                
                powered_by = headers.get('X-Powered-By', '')
                if powered_by:
                    technologies.append(f"Framework: {powered_by}")
                
                if 'wp-content' in body or 'wp-includes' in body:
                    technologies.append("CMS: WordPress")
                if 'Drupal' in body:
                    technologies.append("CMS: Drupal")
                if 'joomla' in body.lower():
                    technologies.append("CMS: Joomla")
                if 'react' in body.lower():
                    technologies.append("Frontend: React")
                if 'vue' in body.lower():
                    technologies.append("Frontend: Vue.js")
                if 'angular' in body.lower():
                    technologies.append("Frontend: Angular")
                
                return {"technologies": technologies}
        except Exception as e:
            logger.error(f"Technology detection failed: {e}")
            return {"technologies": []}
    
    async def check_information_disclosure(self, url: str) -> Dict:
        """Check for information disclosure"""
        logger.info(f"Checking information disclosure for: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                body = response.text
                
                disclosures = []
                
                error_patterns = [
                    r'SQL.*syntax',
                    r'mysql_fetch',
                    r'Warning:.*line \d+',
                    r'Fatal error:',
                    r'Stack trace:',
                    r'Uncaught exception'
                ]
                
                for pattern in error_patterns:
                    if re.search(pattern, body, re.IGNORECASE):
                        disclosures.append(f"Error message exposure detected")
                        break
                
                comment_patterns = [
                    r'<!--.*password.*-->',
                    r'<!--.*api.*key.*-->',
                    r'<!--.*token.*-->',
                    r'<!--.*secret.*-->'
                ]
                
                for pattern in comment_patterns:
                    if re.search(pattern, body, re.IGNORECASE):
                        disclosures.append("Sensitive data in HTML comments")
                        break
                
                if '<title>Index of /' in body:
                    disclosures.append("Directory listing enabled")
                
                return {"disclosures": disclosures}
        except Exception as e:
            logger.error(f"Information disclosure check failed: {e}")
            return {"disclosures": []}
    
    async def test_rate_limiting(self, url: str) -> Dict:
        """Test rate limiting"""
        logger.info(f"Testing rate limiting for: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                requests_sent = 0
                successful = 0
                
                for _ in range(20):
                    try:
                        response = await client.get(url)
                        requests_sent += 1
                        if response.status_code == 200:
                            successful += 1
                    except:
                        break
                
                has_rate_limit = successful < requests_sent
                
                return {
                    "has_rate_limiting": has_rate_limit,
                    "requests_sent": requests_sent,
                    "successful": successful
                }
        except Exception as e:
            logger.error(f"Rate limiting test failed: {e}")
            return {"has_rate_limiting": False, "requests_sent": 0, "successful": 0}
    
    async def end_session(self):
        """Clean up session"""
        logger.info("Ending security analysis session")
        self.session_id = None
