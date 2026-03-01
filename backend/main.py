"""
Bounty Recon AI - Backend API  
Amazon Nova Hackathon 2026
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import asyncio
import logging
from datetime import datetime
from nova_act_sdk import NovaActAgent  # Real Nova SDK

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
    evidence: Optional[str] = None
    screenshot_url: Optional[str] = None
    discovered_at: datetime

class ScanResult(BaseModel):
    scan_id: str
    target: str
    scan_type: str
    status: str
    findings: List[Finding]
    statistics: Dict[str, int]
    report_url: Optional[str] = None
    completed_at: datetime

# IN-MEMORY STORAGE
scans: Dict[str, ScanResult] = {}
active_scans: Dict[str, ScanStatus] = {}

# RECON ENGINE

class ReconEngine:
    """Core reconnaissance engine using Amazon Nova Act"""
    
    def __init__(self):
        self.agent = NovaActAgent()
    
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
            
            if request.include_subdomains:
                logger.info("Discovering endpoints...")
                endpoints = await self.agent.discover_endpoints(str(request.target_url))
                
                for endpoint in endpoints:
                    finding = Finding(
                        title=f"Endpoint Discovered: {endpoint}",
                        severity="info",
                        category="endpoint",
                        description=f"Found accessible endpoint: {endpoint}",
                        discovered_at=datetime.now()
                    )
                    findings.append(finding)
                
                active_scans[scan_id].progress = 50
                active_scans[scan_id].findings = len(findings)
            
            headers_result = await self.agent.check_security_headers(str(request.target_url))
            
            for missing_header in headers_result["missing_headers"]:
                finding = Finding(
                    title=f"Missing Security Header: {missing_header}",
                    severity="medium",
                    category="header",
                    description=f"The {missing_header} header is not set.",
                    discovered_at=datetime.now()
                )
                findings.append(finding)
            
            for weak_header in headers_result["weak_headers"]:
                finding = Finding(
                    title=f"Weak Security Header: {weak_header['header']}",
                    severity="high",
                    category="header",
                    description=weak_header['issue'],
                    evidence=f"Value: {weak_header['value']}",
                    discovered_at=datetime.now()
                )
                findings.append(finding)
            
            active_scans[scan_id].progress = 70
            active_scans[scan_id].findings = len(findings)
            
            if request.include_screenshots:
                screenshot_url = await self.agent.capture_screenshot(str(request.target_url))
                active_scans[scan_id].progress = 90
            
            await self.agent.end_session()
            
            stats = {
                "total_findings": len(findings),
                "critical": sum(1 for f in findings if f.severity == "critical"),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
                "info": sum(1 for f in findings if f.severity == "info")
            }
            
            result = ScanResult(
                scan_id=scan_id,
                target=str(request.target_url),
                scan_type=request.scan_type,
                status="completed",
                findings=findings,
                statistics=stats,
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

recon_engine = ReconEngine()

# API ENDPOINTS

@app.get("/")
async def root():
    return {
        "name": "Bounty Recon AI API",
        "version": "1.0.0",
        "status": "operational",
        "powered_by": "Amazon Nova Act"
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

@app.get("/scans", response_model=List[ScanStatus])
async def list_scans(limit: int = 10):
    return list(active_scans.values())[-limit:]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
