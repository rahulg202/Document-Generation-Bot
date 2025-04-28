import streamlit as st
from io import BytesIO
import markdown
import re
import logging
from bs4 import BeautifulSoup
import tempfile
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def markdown_to_pdf_weasyprint(markdown_text):
    """Convert Markdown to PDF using WeasyPrint for better formatting."""
    try:
        # Try to import WeasyPrint - not included in requirements.txt
        # so we'll need to add a fallback method
        try:
            from weasyprint import HTML, CSS
            
            # Convert Markdown to HTML
            html = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
            
            # Add CSS styling
            css = CSS(string='''
                @page {
                    margin: 1cm;
                }
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    font-size: 12pt;
                    color: #333;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #2c3e50;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }
                h1 { font-size: 24pt; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
                h2 { font-size: 18pt; }
                h3 { font-size: 14pt; }
                p { margin-bottom: 1em; }
                ul, ol { padding-left: 2em; margin-bottom: 1em; }
                li { margin-bottom: 0.5em; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
                th, td { padding: 8px; text-align: left; border: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                blockquote { background-color: #f9f9f9; border-left: 4px solid #ccc; margin: 1em 0; padding: 0.5em 1em; }
                a { color: #3498db; text-decoration: none; }
                img { max-width: 100%; }
                pre { background-color: #f5f5f5; padding: 1em; border-radius: 3px; overflow-x: auto; }
                code { background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
            ''')
            
            # Create complete HTML document
            complete_html = f'''<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Generated Document</title>
            </head>
            <body>
                {html}
            </body>
            </html>
            '''
            
            # Convert HTML to PDF
            pdf_buffer = BytesIO()
            HTML(string=complete_html).write_pdf(pdf_buffer, stylesheets=[css])
            pdf_buffer.seek(0)
            
            return pdf_buffer.getvalue()
            
        except ImportError:
            logger.warning("WeasyPrint not installed. Falling back to alternative method.")
            return _fallback_pdf_generation(markdown_text)
            
    except Exception as e:
        logger.error(f"Error converting to PDF with WeasyPrint: {str(e)}")
        # Try fallback method
        return _fallback_pdf_generation(markdown_text)

def _fallback_pdf_generation(markdown_text):
    """Fallback method for PDF generation using ReportLab or FPDF."""
    try:
        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_text)
        
        # Try to use ReportLab
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            # Extract text and structure from HTML using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create a PDF buffer
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            heading2_style = ParagraphStyle(
                'Heading2',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                textColor=colors.darkblue
            )
            
            heading3_style = ParagraphStyle(
                'Heading3',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                textColor=colors.darkblue
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                spaceAfter=8
            )
            
            # Build the PDF content
            content = []
            
            # Process HTML elements
            for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li', 'table']):
                if element.name == 'h1':
                    content.append(Paragraph(element.get_text(), title_style))
                elif element.name == 'h2':
                    content.append(Paragraph(element.get_text(), heading2_style))
                elif element.name == 'h3':
                    content.append(Paragraph(element.get_text(), heading3_style))
                elif element.name == 'p':
                    content.append(Paragraph(element.get_text(), normal_style))
                elif element.name == 'ul' or element.name == 'ol':
                    for li in element.find_all('li'):
                        bullet = "• " if element.name == 'ul' else f"{element.find_all('li').index(li) + 1}. "
                        content.append(Paragraph(f"{bullet}{li.get_text()}", normal_style))
                elif element.name == 'table':
                    # Process table - this is a simplified approach
                    table_data = []
                    for row in element.find_all('tr'):
                        table_row = []
                        for cell in row.find_all(['td', 'th']):
                            table_row.append(cell.get_text())
                        table_data.append(table_row)
                    
                    if table_data:
                        # Create table
                        t = Table(table_data)
                        # Add basic styling
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        content.append(t)
                        content.append(Spacer(1, 12))
            
            # Build the PDF
            doc.build(content)
            
            # Get the PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except ImportError:
            logger.warning("ReportLab not installed. Trying FPDF...")
            
            # Try FPDF as a last resort
            from fpdf import FPDF
            
            # Simple HTML to text to remove tags
            text = re.sub(r'<[^>]*>', '', html_content)
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Split text to fit on page
            for line in text.split('\n'):
                if line.strip():
                    if line.startswith('# '):  # h1
                        pdf.set_font("Arial", 'B', 16)
                        pdf.cell(0, 10, line[2:], ln=True)
                        pdf.set_font("Arial", size=12)
                    elif line.startswith('## '):  # h2
                        pdf.set_font("Arial", 'B', 14)
                        pdf.cell(0, 10, line[3:], ln=True)
                        pdf.set_font("Arial", size=12)
                    elif line.startswith('### '):  # h3
                        pdf.set_font("Arial", 'B', 12)
                        pdf.cell(0, 10, line[4:], ln=True)
                        pdf.set_font("Arial", size=12)
                    else:
                        pdf.multi_cell(0, 10, line)
                        pdf.ln(2)
            
            return pdf.output(dest='S').encode('latin1')
            
    except Exception as e:
        logger.error(f"All PDF generation methods failed: {str(e)}")
        st.warning("PDF generation failed. Please try downloading as DOCX or Markdown instead.")
        return None

def markdown_to_html_with_toc(markdown_text):
    """Convert markdown to HTML with a table of contents."""
    # Process the markdown to HTML
    html_content = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
    
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all headings
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    # Only generate TOC if there are headings
    if headings:
        # Generate TOC
        toc_html = '<div class="toc"><h2>Table of Contents</h2><ul>'
        
        for heading in headings:
            # Clean the heading text
            heading_text = heading.get_text()
            heading_id = re.sub(r'[^a-z0-9]', '-', heading_text.lower())
            
            # Add ID to the heading
            heading['id'] = heading_id
            
            # Calculate indentation based on heading level
            level = int(heading.name[1])
            indent = (level - 1) * 20
            
            # Add entry to TOC
            toc_html += f'<li style="margin-left: {indent}px;"><a href="#{heading_id}">{heading_text}</a></li>'
        
        toc_html += '</ul></div><hr>'
        
        # Add TOC to the beginning of the document
        full_html = toc_html + str(soup)
    else:
        # If no headings, just use the content as is
        full_html = str(soup)
    
    # Add styling
    styled_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Document</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 2cm;
                color: #333;
            }}
            .toc {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .toc h2 {{
                margin-top: 0;
            }}
            .toc ul {{
                list-style-type: none;
                padding-left: 0;
            }}
            .toc a {{
                text-decoration: none;
                color: #0366d6;
            }}
            .toc a:hover {{
                text-decoration: underline;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{ font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.5em; }}
            p {{ margin-bottom: 1em; }}
            ul, ol {{ padding-left: 2em; margin-bottom: 1em; }}
            li {{ margin-bottom: 0.5em; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
            th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            blockquote {{ background-color: #f9f9f9; border-left: 4px solid #ccc; margin: 1em 0; padding: 0.5em 1em; }}
            pre {{ background-color: #f5f5f5; padding: 1em; border-radius: 3px; overflow-x: auto; }}
            code {{ background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        {full_html}
    </body>
    </html>
    """
    
    return styled_html