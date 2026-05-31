import pandas as pd
import json
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any


class ExportHandler:
    """Handle exports of query results"""
    
    @staticmethod
    def export_to_csv(rows: List[Dict[str, Any]], filename: str = None) -> bytes:
        """Export results to CSV"""
        if not filename:
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = pd.DataFrame(rows)
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        return csv_buffer.getvalue()
    
    @staticmethod
    def export_to_json(rows: List[Dict[str, Any]], filename: str = None) -> bytes:
        """Export results to JSON"""
        if not filename:
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        json_str = json.dumps(rows, indent=2, default=str)
        return json_str.encode('utf-8')
    
    @staticmethod
    def export_to_pdf(rows: List[Dict[str, Any]], title: str = "Query Results", filename: str = None) -> bytes:
        """Export results to PDF"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.units import inch
            
            if not filename:
                filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=12
            )
            elements.append(Paragraph(title, title_style))
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 0.3 * inch))
            
            # Convert data to table
            if rows:
                df = pd.DataFrame(rows)
                data = [list(df.columns)] + df.values.tolist()
                
                table = Table(data, colWidths=[1.5 * inch] * len(df.columns))
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                elements.append(table)
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            raise Exception("reportlab not installed. Run: pip install reportlab")
