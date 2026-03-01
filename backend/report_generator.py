"""
Professional PDF Report Generator for Bug Bounty Reconnaissance
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path
import tempfile

def generate_pdf_report(scan_result):
    """Generate professional PDF report"""
    
    # Create temp file
    temp_dir = Path("/tmp/bounty-reports")
    temp_dir.mkdir(exist_ok=True)
    pdf_path = temp_dir / f"report-{scan_result.scan_id}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        textColor=colors.HexColor('#1F2937'),
        backColor=colors.HexColor('#F3F4F6'),
        leftIndent=20,
        spaceAfter=12
    )
    
    # Title Page
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Bug Bounty Reconnaissance Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Target: {scan_result.target}", ParagraphStyle(
        'Subtitle',
        parent=body_style,
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6366F1')
    )))
    elements.append(Spacer(1, 0.5*inch))
    
    # Report metadata
    metadata = [
        ["Scan ID:", scan_result.scan_id],
        ["Scan Type:", scan_result.scan_type.upper()],
        ["Completed:", scan_result.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["Total Findings:", str(scan_result.statistics['total_findings'])],
        ["Powered By:", "Amazon Nova Act AI"],
    ]
    
    metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    
    elements.append(metadata_table)
    elements.append(PageBreak())
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(scan_result.summary, body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Risk Overview Table
    elements.append(Paragraph("Risk Overview", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    risk_data = [
        ["Severity", "Count", "Priority"],
        ["Critical", str(scan_result.statistics['critical']), "Immediate"],
        ["High", str(scan_result.statistics['high']), "Urgent"],
        ["Medium", str(scan_result.statistics['medium']), "Important"],
        ["Low", str(scan_result.statistics['low']), "Review"],
        ["Info", str(scan_result.statistics['info']), "Note"],
    ]
    
    risk_table = Table(risk_data, colWidths=[2*inch, 1.5*inch, 2*inch])
    risk_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, 1), [colors.HexColor('#FEE2E2')]),
        ('ROWBACKGROUNDS', (0, 2), (-1, 2), [colors.HexColor('#FED7AA')]),
        ('ROWBACKGROUNDS', (0, 3), (-1, 3), [colors.HexColor('#FEF3C7')]),
        ('ROWBACKGROUNDS', (0, 4), (-1, 4), [colors.HexColor('#DBEAFE')]),
        ('ROWBACKGROUNDS', (0, 5), (-1, 5), [colors.HexColor('#F3F4F6')]),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    
    elements.append(risk_table)
    elements.append(PageBreak())
    
    # Detailed Findings
    elements.append(Paragraph("Detailed Findings", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Sort findings by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(scan_result.findings, key=lambda x: severity_order.get(x.severity, 5))
    
    for idx, finding in enumerate(sorted_findings, 1):
        # Finding header
        severity_colors = {
            "critical": colors.HexColor('#DC2626'),
            "high": colors.HexColor('#EA580C'),
            "medium": colors.HexColor('#CA8A04'),
            "low": colors.HexColor('#2563EB'),
            "info": colors.HexColor('#6B7280')
        }
        
        finding_title = f"{idx}. {finding.title}"
        elements.append(Paragraph(finding_title, subheading_style))
        
        # Severity badge
        severity_text = f"<font color='{severity_colors[finding.severity]}'><b>[{finding.severity.upper()}]</b></font>"
        elements.append(Paragraph(severity_text, body_style))
        
        if finding.cvss_score:
            elements.append(Paragraph(f"<b>CVSS Score:</b> {finding.cvss_score}/10.0", body_style))
        
        # Description
        elements.append(Paragraph(f"<b>Description:</b>", body_style))
        elements.append(Paragraph(finding.description, body_style))
        
        # Implications
        elements.append(Paragraph(f"<b>Security Implications:</b>", body_style))
        elements.append(Paragraph(finding.implications, body_style))
        
        # Recommendations
        elements.append(Paragraph(f"<b>Recommendations:</b>", body_style))
        elements.append(Paragraph(finding.recommendations, body_style))
        
        # Evidence
        if finding.evidence:
            elements.append(Paragraph(f"<b>Evidence:</b>", body_style))
            elements.append(Paragraph(f"<font face='Courier'>{finding.evidence}</font>", code_style))
        
        # Metadata
        metadata_text = f"<i>Category: {finding.category} | Discovered: {finding.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}</i>"
        elements.append(Paragraph(metadata_text, ParagraphStyle(
            'Metadata',
            parent=body_style,
            fontSize=8,
            textColor=colors.HexColor('#9CA3AF')
        )))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Page break after every 2 findings to avoid clutter
        if idx % 2 == 0 and idx < len(sorted_findings):
            elements.append(PageBreak())
    
    # Conclusion
    elements.append(PageBreak())
    elements.append(Paragraph("Conclusion & Next Steps", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    conclusion = f"""
    This reconnaissance scan identified {scan_result.statistics['total_findings']} findings across multiple 
    categories. The security assessment reveals potential vulnerabilities that require attention based on their 
    severity levels.
    <br/><br/>
    <b>Immediate Actions Required:</b><br/>
    • Address all Critical and High severity findings within 24-48 hours<br/>
    • Review Medium severity findings and prioritize based on business impact<br/>
    • Document and track all findings for future reference<br/>
    • Implement security headers and configuration hardening<br/>
    • Conduct follow-up scans after remediation
    <br/><br/>
    <b>Report Generated By:</b> Bounty Recon AI powered by Amazon Nova Act<br/>
    <b>Methodology:</b> Automated reconnaissance using AI-driven browser automation and security analysis<br/>
    <b>Disclaimer:</b> This report is for authorized security testing only. Results should be verified manually 
    before submission to bug bounty programs.
    """
    
    elements.append(Paragraph(conclusion, body_style))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path
