"""
Bounty Recon AI - Backend API  
Amazon Nova Hackathon 2026
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import asyncio
import logging
from datetime import datetime
from nova_pro_sdk import SecurityAnalysisAgent
import httpx
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bounty Recon AI API",
    description="AI-Powered Bug Bounty Reconnaissance using Amazon Nova Act",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DATA MODELS

class ScanRequest(BaseModel):
    target_url: HttpUrl
    scan_type: str = "quick"
    include_subdomains: bool = True
    include_screenshots: bool = True
    max_depth: int = 3

class ScanStatus(BaseModel):
    scan_id: str
    status: str
    progress: int
    findings: int
    started_at: datetime
    estimated_completion: Optional[datetime] = None

class Finding(BaseModel):
    title: str
    severity: str
    category: str
    description: str
    implications: str  # Security impact
    recommendations: str  # How to fix
    evidence: Optional[str] = None
    screenshot_url: Optional[str] = None
    discovered_at: datetime
    cvss_score: Optional[float] = None  # CVSS score if applicable

class ScanResult(BaseModel):
    scan_id: str
    target: str
    scan_type: str
    status: str
    findings: List[Finding]
    statistics: Dict[str, int]
    report_url: Optional[str] = None
    completed_at: datetime
    summary: str  # Executive summary

# IN-MEMORY STORAGE
scans: Dict[str, ScanResult] = {}
active_scans: Dict[str, ScanStatus] = {}

# Security knowledge base for implications and recommendations
SECURITY_KB = {
    "Content-Security-Policy": {
        "implications": "Without CSP, the application is vulnerable to XSS attacks. Attackers can inject malicious scripts that steal user data, session tokens, or perform actions on behalf of users.",
        "recommendations": "Implement a Content-Security-Policy header with strict directives. Start with 'default-src self' and gradually allow necessary resources. Use nonces or hashes for inline scripts.",
        "severity": "high",
        "cvss": 7.5
    },
    "X-Frame-Options": {
        "implications": "Missing X-Frame-Options allows clickjacking attacks where attackers can embed your site in an iframe and trick users into clicking malicious elements by overlaying them on legitimate UI.",
        "recommendations": "Set X-Frame-Options to 'DENY' or 'SAMEORIGIN'. For modern browsers, also implement Content-Security-Policy with frame-ancestors directive.",
        "severity": "medium",
        "cvss": 4.3
    },
    "Strict-Transport-Security": {
        "implications": "Without HSTS, users can be vulnerable to SSL stripping attacks where attackers downgrade HTTPS connections to HTTP, exposing sensitive data in transit.",
        "recommendations": "Set Strict-Transport-Security header with 'max-age=31536000; includeSubDomains; preload'. Consider submitting domain to HSTS preload list.",
        "severity": "high",
        "cvss": 6.5
    },
    "X-Content-Type-Options": {
        "implications": "Allows MIME-sniffing attacks where browsers can execute files as different content types, potentially leading to XSS or code execution vulnerabilities.",
        "recommendations": "Set X-Content-Type-Options to 'nosniff' to prevent browsers from MIME-sniffing responses away from declared content type.",
        "severity": "medium",
        "cvss": 5.3
    },
    ".git/config": {
        "implications": "Exposed .git directory allows attackers to download entire source code, revealing API keys, database credentials, business logic vulnerabilities, and internal architecture.",
        "recommendations": "Block access to .git directory in web server configuration. Add deny rules in .htaccess or nginx.conf. Never deploy .git folders to production.",
        "severity": "critical",
        "cvss": 9.1
    },
    ".env": {
        "implications": "Exposed .env file contains database credentials, API keys, secrets, and other sensitive configuration data. Full system compromise is likely.",
        "recommendations": "Immediately rotate all exposed credentials. Block access to .env files in web server config. Use environment variables or secure vaults for sensitive data.",
        "severity": "critical",
        "cvss": 9.8
    }
}

async def verify_endpoint(url: str) -> Dict:
    """Verify if endpoint exists and get status code"""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            response = await client.head(url, follow_redirects=False)
            return {
                "exists": response.status_code < 404,
                "status_code": response.status_code,
                "accessible": response.status_code == 200
            }
    except Exception as e:
        logger.error(f"Error verifying {url}: {e}")
        return {"exists": False, "status_code": 0, "accessible": False}

# RECON ENGINE

class ReconEngine:
    """Core reconnaissance engine using Amazon Nova Pro for AI-enhanced analysis"""
    
    def __init__(self):
        self.agent = SecurityAnalysisAgent()
    
    async def run_scan(self, scan_id: str, request: ScanRequest):
        logger.info(f"Starting scan {scan_id} for {request.target_url}")
        
        try:
            active_scans[scan_id].status = "running"
            active_scans[scan_id].progress = 10
            
            await self.agent.start_session()
            active_scans[scan_id].progress = 20
            
            nav_result = await self.agent.navigate_to(str(request.target_url))
            active_scans[scan_id].progress = 30
            
            findings = []
            
            # Endpoint discovery with verification
            if request.include_subdomains:
                logger.info("Discovering and verifying endpoints...")
                endpoints = await self.agent.discover_endpoints(str(request.target_url))
                
                for endpoint in endpoints:
                    verification = await verify_endpoint(endpoint)
                    
                    # Only report accessible or sensitive endpoints
                    if verification["accessible"]:
                        finding = Finding(
                            title=f"Accessible Endpoint: {endpoint}",
                            severity="info",
                            category="endpoint",
                            description=f"Endpoint is publicly accessible (HTTP {verification['status_code']})",
                            implications="Publicly accessible endpoints should be reviewed for proper authentication and authorization. Unauthenticated access to sensitive endpoints can lead to data exposure.",
                            recommendations="Review endpoint for sensitive data exposure. Implement authentication and authorization. Apply rate limiting to prevent abuse.",
                            discovered_at=datetime.now()
                        )
                        findings.append(finding)
                    elif endpoint.endswith(('.git/config', '.env', 'config.php', 'wp-config.php')):
                        # Report sensitive files even if not accessible (important to verify they're blocked)
                        if verification["status_code"] == 403:
                            finding = Finding(
                                title=f"Sensitive File Protected: {endpoint}",
                                severity="info",
                                category="security",
                                description=f"Sensitive file is properly blocked (HTTP {verification['status_code']})",
                                implications="File is protected but presence indicates technology stack. Ensure protection is consistent across all environments.",
                                recommendations="Verify this protection applies to all sensitive files. Monitor for configuration changes.",
                                discovered_at=datetime.now()
                            )
                            findings.append(finding)
                        elif verification["status_code"] == 200:
                            kb_entry = SECURITY_KB.get(endpoint.split('/')[-1], {})
                            finding = Finding(
                                title=f"CRITICAL: Exposed Sensitive File - {endpoint}",
                                severity="critical",
                                category="exposure",
                                description=f"Sensitive file is publicly accessible (HTTP {verification['status_code']})",
                                implications=kb_entry.get("implications", "Exposure of sensitive configuration files can lead to full system compromise."),
                                recommendations=kb_entry.get("recommendations", "Immediately block access and rotate all credentials."),
                                evidence=f"HTTP {verification['status_code']} - File is downloadable",
                                discovered_at=datetime.now(),
                                cvss_score=kb_entry.get("cvss", 9.0)
                            )
                            findings.append(finding)
                
                active_scans[scan_id].progress = 50
                active_scans[scan_id].findings = len(findings)
            
            # Security headers analysis
            headers_result = await self.agent.check_security_headers(str(request.target_url))
            
            for missing_header in headers_result["missing_headers"]:
                kb_entry = SECURITY_KB.get(missing_header, {})
                finding = Finding(
                    title=f"Missing Security Header: {missing_header}",
                    severity=kb_entry.get("severity", "medium"),
                    category="header",
                    description=f"The {missing_header} header is not set, leaving the application vulnerable to related attacks.",
                    implications=kb_entry.get("implications", f"Missing {missing_header} can expose users to security risks."),
                    recommendations=kb_entry.get("recommendations", f"Implement {missing_header} header with appropriate values."),
                    discovered_at=datetime.now(),
                    cvss_score=kb_entry.get("cvss")
                )
                findings.append(finding)
            
            for weak_header in headers_result["weak_headers"]:
                finding = Finding(
                    title=f"Weak Security Header: {weak_header['header']}",
                    severity="high",
                    category="header",
                    description=weak_header['issue'],
                    implications="Weak or disabled security headers leave users vulnerable to XSS and injection attacks. Modern browsers will not apply protection.",
                    recommendations=f"Update {weak_header['header']} to recommended value. For XSS protection, remove header and implement CSP instead.",
                    evidence=f"Current value: {weak_header['value']}",
                    discovered_at=datetime.now(),
                    cvss_score=6.5
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 55
            active_scans[scan_id].findings = len(findings)
            
            # SSL/TLS Analysis
            logger.info("Analyzing SSL/TLS configuration...")
            ssl_result = await self.agent.analyze_ssl_tls(str(request.target_url))
            if ssl_result.get("enabled") and ssl_result.get("issues"):
                for issue in ssl_result["issues"]:
                    finding = Finding(
                        title=f"SSL/TLS Issue: {issue}",
                        severity="high",
                        category="ssl",
                        description=f"SSL/TLS configuration weakness detected: {issue}",
                        implications="Outdated SSL/TLS protocols can be exploited through downgrade attacks, allowing attackers to decrypt traffic. This exposes credentials, session tokens, and sensitive data.",
                        recommendations="Disable TLS 1.0 and 1.1. Enable TLS 1.2 and 1.3 only. Configure strong cipher suites. Regularly update SSL/TLS configuration.",
                        discovered_at=datetime.now(),
                        cvss_score=7.4
                    )
                    findings.append(finding)
            elif not ssl_result.get("enabled"):
                finding = Finding(
                    title="No HTTPS Encryption",
                    severity="critical",
                    category="ssl",
                    description="Site is not using HTTPS encryption",
                    implications="All data transmitted between users and server is sent in plain text. Attackers on the network can intercept credentials, session cookies, personal data, and inject malicious content.",
                    recommendations="Implement HTTPS immediately. Obtain SSL/TLS certificate from Let's Encrypt or commercial CA. Redirect all HTTP traffic to HTTPS. Enable HSTS header.",
                    discovered_at=datetime.now(),
                    cvss_score=9.3
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 60
            
            # Cookie Security Analysis
            logger.info("Analyzing cookie security...")
            cookie_result = await self.agent.analyze_cookies(str(request.target_url))
            for cookie in cookie_result.get("insecure_cookies", []):
                severity = "high" if len(cookie["issues"]) >= 2 else "medium"
                finding = Finding(
                    title=f"Insecure Cookie: {cookie['name']}",
                    severity=severity,
                    category="cookie",
                    description=f"Cookie has security issues: {', '.join(cookie['issues'])}",
                    implications="Insecure cookies can be stolen via XSS attacks (no HttpOnly), transmitted over HTTP (no Secure), or used in CSRF attacks (no SameSite). This can lead to session hijacking and account takeover.",
                    recommendations="Set Secure flag for HTTPS-only transmission. Set HttpOnly to prevent JavaScript access. Set SameSite=Strict or Lax to prevent CSRF. Apply to all authentication cookies.",
                    evidence=f"Issues: {', '.join(cookie['issues'])}",
                    discovered_at=datetime.now(),
                    cvss_score=7.1 if severity == "high" else 5.8
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 65
            
            # CORS Configuration Check
            logger.info("Checking CORS configuration...")
            cors_result = await self.agent.check_cors(str(request.target_url))
            for issue in cors_result.get("issues", []):
                finding = Finding(
                    title=f"CORS Misconfiguration",
                    severity="high",
                    category="cors",
                    description=issue,
                    implications="Permissive CORS allows malicious sites to read sensitive data from your application. With credentials enabled and wildcard origin, attackers can steal user data, API responses, and perform actions on behalf of users.",
                    recommendations="Restrict Access-Control-Allow-Origin to specific trusted domains. Never use wildcard (*) with credentials. Implement proper origin validation. Use CORS only when necessary.",
                    evidence=issue,
                    discovered_at=datetime.now(),
                    cvss_score=7.7
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 68
            
            # Technology Detection
            logger.info("Detecting technologies...")
            tech_result = await self.agent.detect_technologies(str(request.target_url))
            if tech_result.get("technologies"):
                tech_list = tech_result["technologies"]
                finding = Finding(
                    title=f"Technology Stack Fingerprinted",
                    severity="info",
                    category="recon",
                    description=f"Detected technologies: {', '.join(tech_list)}",
                    implications="Technology fingerprinting helps attackers identify known vulnerabilities in specific versions. Exposed version information reduces the time needed to find exploits.",
                    recommendations="Remove or obfuscate version information in headers (Server, X-Powered-By). Keep all software up-to-date. Monitor security advisories for detected technologies.",
                    evidence="\n".join(tech_list),
                    discovered_at=datetime.now()
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 72
            
            # Information Disclosure Check
            logger.info("Checking for information disclosure...")
            disclosure_result = await self.agent.check_information_disclosure(str(request.target_url))
            for disclosure in disclosure_result.get("disclosures", []):
                finding = Finding(
                    title="Information Disclosure",
                    severity="medium",
                    category="disclosure",
                    description=disclosure,
                    implications="Information disclosure reveals internal system details, file paths, database structures, or technology stack. This information helps attackers craft targeted exploits and reduces reconnaissance time.",
                    recommendations="Disable detailed error messages in production. Remove sensitive comments from HTML. Configure web server to suppress version info. Implement custom error pages.",
                    evidence=disclosure,
                    discovered_at=datetime.now(),
                    cvss_score=5.3
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 76
            
            # Rate Limiting Test
            logger.info("Testing rate limiting...")
            rate_result = await self.agent.test_rate_limiting(str(request.target_url))
            if not rate_result.get("has_rate_limiting"):
                finding = Finding(
                    title="No Rate Limiting Detected",
                    severity="medium",
                    category="configuration",
                    description=f"Application accepted {rate_result['successful']} rapid requests without throttling",
                    implications="Without rate limiting, attackers can perform brute force attacks on login endpoints, enumerate users, scrape data at scale, and launch denial-of-service attacks. API abuse and credential stuffing become trivial.",
                    recommendations="Implement rate limiting per IP and per user. Use exponential backoff for failed authentication. Consider implementing CAPTCHA after multiple failures. Monitor for abuse patterns.",
                    evidence=f"Sent {rate_result['requests_sent']} requests, all succeeded",
                    discovered_at=datetime.now(),
                    cvss_score=5.3
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 80
            active_scans[scan_id].findings = len(findings)
            
            # AI Enhancement with Nova Pro
            logger.info("Enhancing findings with Nova Pro AI...")
            for i, finding in enumerate(findings):
                # Only enhance critical and high severity findings with AI to save costs
                if finding.severity in ['critical', 'high'] and i < 5:  # Limit to first 5 for demo
                    try:
                        enhanced = await self.agent.enhance_finding_with_ai({
                            'title': finding.title,
                            'category': finding.category,
                            'description': finding.description,
                            'severity': finding.severity,
                            'implications': finding.implications,
                            'recommendations': finding.recommendations
                        })
                        
                        if enhanced.get('ai_enhanced'):
                            # Update finding with AI-enhanced content
                            finding.implications = enhanced['implications']
                            finding.recommendations = enhanced['recommendations']
                            finding.severity = enhanced['severity']
                            logger.info(f"Enhanced finding with Nova Pro: {finding.title}")
                    except Exception as e:
                        logger.error(f"Failed to enhance finding with AI: {e}")
            
            active_scans[scan_id].progress = 85
            
            if request.include_screenshots:
                screenshot_url = await self.agent.capture_screenshot(str(request.target_url))
                active_scans[scan_id].progress = 90
            
            await self.agent.end_session()
            
            # Calculate statistics
            stats = {
                "total_findings": len(findings),
                "critical": sum(1 for f in findings if f.severity == "critical"),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
                "info": sum(1 for f in findings if f.severity == "info")
            }
            
            # Generate executive summary
            summary = self._generate_summary(findings, stats, str(request.target_url))
            
            result = ScanResult(
                scan_id=scan_id,
                target=str(request.target_url),
                scan_type=request.scan_type,
                status="completed",
                findings=findings,
                statistics=stats,
                summary=summary,
                completed_at=datetime.now()
            )
            
            scans[scan_id] = result
            active_scans[scan_id].status = "completed"
            active_scans[scan_id].progress = 100
            
            logger.info(f"Scan {scan_id} completed with {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {str(e)}")
            active_scans[scan_id].status = "failed"
            raise
    
    def _generate_summary(self, findings: List[Finding], stats: Dict, target: str) -> str:
        """Generate executive summary"""
        critical_count = stats.get("critical", 0)
        high_count = stats.get("high", 0)
        
        if critical_count > 0:
            risk_level = "CRITICAL"
            summary = f"Security assessment of {target} revealed {critical_count} critical vulnerabilities requiring immediate attention. "
        elif high_count > 0:
            risk_level = "HIGH"
            summary = f"Security assessment of {target} identified {high_count} high-severity issues that should be addressed promptly. "
        else:
            risk_level = "MODERATE"
            summary = f"Security assessment of {target} found {stats['total_findings']} findings for review. "
        
        summary += f"The scan detected {stats['total_findings']} total findings across endpoint discovery and security header analysis. "
        summary += "Immediate remediation is recommended for critical and high-severity findings to prevent potential exploitation."
        
        return summary

recon_engine = ReconEngine()

# API ENDPOINTS

@app.get("/")
async def root():
    return {
        "name": "Bounty Recon AI API",
        "version": "1.0.0",
        "status": "operational",
        "powered_by": "Amazon Nova Pro"
    }

@app.post("/scans", response_model=ScanStatus)
async def create_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    scan_id = f"scan-{datetime.now().timestamp()}"
    
    status = ScanStatus(
        scan_id=scan_id,
        status="pending",
        progress=0,
        findings=0,
        started_at=datetime.now()
    )
    
    active_scans[scan_id] = status
    background_tasks.add_task(recon_engine.run_scan, scan_id, request)
    
    logger.info(f"Created scan {scan_id} for {request.target_url}")
    return status

@app.get("/scans/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return active_scans[scan_id]

@app.get("/scans/{scan_id}/results", response_model=ScanResult)
async def get_scan_results(scan_id: str):
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan results not found")
    return scans[scan_id]

@app.get("/scans/{scan_id}/report/pdf")
async def download_pdf_report(scan_id: str):
    """Generate and download professional PDF report"""
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    from report_generator import generate_pdf_report
    
    result = scans[scan_id]
    pdf_path = generate_pdf_report(result)
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"bounty-recon-{scan_id}.pdf"
    )

@app.get("/scans", response_model=List[ScanStatus])
async def list_scans(limit: int = 10):
    return list(active_scans.values())[-limit:]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
