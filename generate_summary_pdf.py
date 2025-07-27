#!/usr/bin/env python3
"""
Generate a beautiful PDF summary report from the latest test summary CSV.
"""
import os
import glob
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

def generate_summary_pdf():
    """Generate the PDF summary report."""
    # Find the latest test_summary_*.csv
    summary_files = sorted(glob.glob('test_outputs/test_summary_*.csv'))
    if not summary_files:
        print("No test summary CSV found in test_outputs/.")
        return
    latest_csv = summary_files[-1]
    df = pd.read_csv(latest_csv)

    # Prepare PDF in landscape mode
    pdf_path = "summaryReport.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_LEFT))

    # Title
    title_style = ParagraphStyle('title', parent=styles['Title'], alignment=TA_CENTER, fontSize=22, spaceAfter=20)
    story.append(Paragraph("Universal File Converter - Test Summary Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Summary stats
    total = len(df)
    success = df['Success'].sum()
    failure = total - success
    success_rate = (success / total) * 100 if total else 0

    summary_data = [
        ["Total Tests", total],
        ["Successful", success],
        ["Failed", failure],
        ["Success Rate", f"{success_rate:.1f}%"]
    ]
    summary_table = Table(summary_data, hAlign='LEFT', colWidths=[2.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 18))

    # Conversion Table with wrapped text
    df['Error/Warning'] = df['Error'].fillna('') + df['Warning'].fillna('')
    table_data = [["Input File", "Output File", "Source", "Output", "Status", "Method", "Content Preserved", "Details"]]
    
    for _, row in df.iterrows():
        # Wrap text in Paragraph objects
        input_file_p = Paragraph(row['Test File'], styles['Justify'])
        output_file_p = Paragraph(row['Test File'].split('.')[0] + f".{row['Destination Format'].lower()}", styles['Justify'])
        details_p = Paragraph(row['Error/Warning'], styles['Justify'])
        
        status = "Success" if row['Success'] else "Fail"
        
        table_data.append([
            input_file_p,
            output_file_p,
            row['Source Format'],
            row['Destination Format'],
            status,
            row.get('Conversion Method', ''),
            "Yes" if row.get('Content Preserved', False) else "No",
            details_p
        ])

    col_widths = [1.5*inch, 1.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 1*inch, 1*inch, 3.5*inch]
    conv_table = Table(table_data, repeatRows=1, colWidths=col_widths)
    conv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    for i, row in enumerate(table_data[1:], start=1):
        status = row[4]
        color = colors.green if status == "Success" else colors.red
        conv_table.setStyle([('TEXTCOLOR', (4, i), (4, i), color)])
        if status == "Fail":
            conv_table.setStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffeaea'))])
        else:
            conv_table.setStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#eaffea'))])
            
    story.append(Paragraph("<b>Conversion Results</b>", styles['Heading2']))
    story.append(conv_table)
    story.append(Spacer(1, 18))

    # Recommendations and Warnings
    recommendations = df['Warning'].dropna().unique()
    errors = df['Error'].dropna().unique()

    if len(recommendations) > 0 or len(errors) > 0:
        story.append(Paragraph("<b>Recommendations & Warnings</b>", styles['Heading2']))
        
        if len(errors) > 0:
            error_section = Table(
                [[Paragraph("<b>Errors</b>", styles['Normal']), '']],
                colWidths=[1.5*inch, 8.5*inch], 
                style=[('VALIGN', (0,0), (-1,-1), 'TOP')]
            )
            story.append(error_section)
            for e in errors:
                story.append(Paragraph(f"• {e}", styles['Normal']))
            story.append(Spacer(1, 12))

        if len(recommendations) > 0:
            rec_section = Table(
                [[Paragraph("<b>Warnings</b>", styles['Normal']), '']],
                colWidths=[1.5*inch, 8.5*inch],
                style=[('VALIGN', (0,0), (-1,-1), 'TOP')]
            )
            story.append(rec_section)
            for r in recommendations:
                story.append(Paragraph(f"• {r}", styles['Normal']))

    # Build PDF
    print(f"Generating {pdf_path} from {latest_csv} ...")
    doc.build(story)
    print(f"Done! Open {pdf_path} to view the summary report.")

if __name__ == "__main__":
    generate_summary_pdf()
