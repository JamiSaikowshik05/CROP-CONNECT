"""
Utility functions for CropConnect
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def ensure_default_crops():
    """Create the portal's standard crops if they are missing."""
    from .models import Crop

    defaults = (
        ('Paddy', '2441.00'),
        ('Groundnut', '7517.00'),
    )
    for name, msp in defaults:
        crop, _ = Crop.objects.get_or_create(
            name=name,
            defaults={
                'msp_per_quintal': msp,
                'season': 'Kharif 2026-27',
                'unit': 'Quintal',
                'is_active': True,
            },
        )
        if not crop.is_active:
            crop.is_active = True
            crop.save(update_fields=['is_active', 'updated_at'])


def generate_pdf_invoice(bill):
    """Generate PDF invoice for a bill."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    title_style = ParagraphStyle(
        'PortalTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=6,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Government of India", title_style))
    elements.append(Paragraph("CropConnect", styles['Heading2']))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("TAX INVOICE / BILL", ParagraphStyle('InvTitle', parent=styles['Heading2'], fontSize=14, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.2 * inch))

    # Bill details
    procurement = bill.procurement
    booking = procurement.booking
    farmer = booking.farmer
    crop = booking.slot.crop

    data = [
        ['Bill Number', bill.bill_number],
        ['Date', bill.created_at.strftime('%d-%m-%Y')],
        ['Farmer Name', farmer.user.get_full_name() or farmer.user.username],
        ['Aadhaar', farmer.aadhaar],
        ['Village/Mandal', f"{farmer.village}, {farmer.mandal}"],
        ['District', farmer.district],
        ['Crop', crop.name],
        ['Quantity (Quintal)', str(bill.quantity_quintals)],
        ['MSP per Quintal (₹)', str(bill.msp_per_quintal)],
        ['Total Amount (₹)', str(bill.total_amount)],
    ]
    t = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("This is a computer-generated invoice.", styles['Normal']))
    doc.build(elements)
    return buffer.getvalue()
