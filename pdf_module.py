
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import datetime

def generate_pdf(table_data, model_name):
    doc = SimpleDocTemplate("Pump_Report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Logos
    try:
        elements.append(Image("logo1.png", width=200, height=60))
        elements.append(Image("logo2.png", width=150, height=50))
    except:
        pass

    elements.append(Spacer(1,10))

    # Title
    elements.append(Paragraph("Pump Performance Guarantee Table", styles['Title']))
    elements.append(Spacer(1,10))

    # Model
    elements.append(Paragraph(f"Pump Model: {model_name}", styles['Normal']))
    elements.append(Spacer(1,10))

    # Table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ]))
    elements.append(table)

    elements.append(Spacer(1,20))

    # Date
    today = datetime.date.today().strftime("%d-%m-%Y")
    elements.append(Paragraph(f"Date: {today}", styles['Normal']))
    elements.append(Spacer(1,20))

    # Signature
    elements.append(Paragraph("Hydrotech for Engineering and Technical Services", styles['Normal']))

    doc.build(elements)
