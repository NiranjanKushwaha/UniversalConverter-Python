import os
import asyncio
import threading
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging

# Document processing
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from docx.shared import Inches
import openpyxl
import xlrd
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import html2text
import markdown
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
import csv

# Image processing
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from cairosvg import svg2png, svg2pdf
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM

# Audio/Video processing (optional - commented out to avoid import errors)
# from pydub import AudioSegment
# from moviepy.editor import VideoFileClip, AudioFileClip
# import imageio

# E-book processing (optional - commented out to avoid import errors)
# import ebooklib
# from ebooklib import epub

# Presentation processing
from pptx import Presentation
from pptx.util import Inches as PptxInches

# RTF processing
import zipfile
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversionService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def convert_file(self, input_path: str, output_path: str, source_format: str, destination_format: str, job_id: str, jobs: Dict) -> bool:
        """Main conversion method that routes to specific converters"""
        try:
            # Update job status
            jobs[job_id]["status"] = "converting"
            jobs[job_id]["progress"] = 10
            
            # Route to appropriate converter
            converter_method = self._get_converter_method(source_format, destination_format)
            if not converter_method:
                raise ValueError(f"Conversion from {source_format} to {destination_format} not supported")
            
            # Run conversion in thread pool
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor, 
                converter_method, 
                input_path, 
                output_path, 
                job_id, 
                jobs
            )
            
            if success:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["progress"] = 100
                jobs[job_id]["converted_path"] = output_path
            else:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = "Conversion failed"
            
            return success
            
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
            return False
    
    def _get_converter_method(self, source: str, destination: str):
        """Get the appropriate converter method"""
        converter_map = {
            # PDF conversions
            ("PDF", "DOCX"): self._pdf_to_docx,
            ("PDF", "DOC"): self._pdf_to_doc,
            ("PDF", "TXT"): self._pdf_to_txt,
            ("PDF", "HTML"): self._pdf_to_html,
            ("PDF", "JPG"): self._pdf_to_image,
            ("PDF", "PNG"): self._pdf_to_image,
            ("PDF", "XLSX"): self._pdf_to_xlsx,
            ("PDF", "CSV"): self._pdf_to_csv,
            ("PDF", "XLS"): self._pdf_to_xls,
            
            # DOCX conversions
            ("DOCX", "PDF"): self._docx_to_pdf,
            ("DOCX", "TXT"): self._docx_to_txt,
            ("DOCX", "HTML"): self._docx_to_html,
            ("DOCX", "RTF"): self._docx_to_rtf,
            ("DOCX", "JPG"): self._docx_to_image,
            ("DOCX", "PNG"): self._docx_to_image,
            
            # DOC conversions (similar to DOCX)
            ("DOC", "PDF"): self._doc_to_pdf,
            ("DOC", "TXT"): self._doc_to_txt,
            ("DOC", "HTML"): self._doc_to_html,
            
            # Excel conversions
            ("XLSX", "CSV"): self._xlsx_to_csv,
            ("XLSX", "PDF"): self._xlsx_to_pdf,
            ("XLSX", "HTML"): self._xlsx_to_html,
            ("XLSX", "JSON"): self._xlsx_to_json,
            ("XLSX", "XML"): self._xlsx_to_xml,
            ("XLS", "CSV"): self._xls_to_csv,
            ("XLS", "PDF"): self._xls_to_pdf,
            ("XLS", "XLSX"): self._xls_to_xlsx,
            
            # Image conversions
            ("JPG", "PNG"): self._image_convert,
            ("JPG", "PDF"): self._image_to_pdf,
            ("JPG", "BMP"): self._image_convert,
            ("JPG", "GIF"): self._image_convert,
            ("JPG", "TIFF"): self._image_convert,
            ("JPG", "WEBP"): self._image_convert,
            ("JPG", "ICO"): self._image_convert,
            ("JPG", "DOCX"): self._image_to_docx,
            ("JPG", "DOC"): self._image_to_doc,
            ("JPG", "XLSX"): self._image_to_xlsx,
            ("JPG", "PPTX"): self._image_to_pptx,
            ("JPG", "TXT"): self._image_to_txt,
            ("PNG", "JPG"): self._image_convert,
            ("PNG", "PDF"): self._image_to_pdf,
            ("PNG", "BMP"): self._image_convert,
            ("PNG", "GIF"): self._image_convert,
            ("PNG", "TIFF"): self._image_convert,
            ("PNG", "WEBP"): self._image_convert,
            ("PNG", "ICO"): self._image_convert,
            ("PNG", "DOCX"): self._image_to_docx,
            ("PNG", "DOC"): self._image_to_doc,
            ("PNG", "XLSX"): self._image_to_xlsx,
            ("PNG", "PPTX"): self._image_to_pptx,
            ("PNG", "TXT"): self._image_to_txt,
            ("BMP", "JPG"): self._image_convert,
            ("BMP", "PNG"): self._image_convert,
            ("BMP", "PDF"): self._image_to_pdf,
            ("BMP", "ICO"): self._image_convert,
            ("BMP", "DOCX"): self._image_to_docx,
            ("BMP", "DOC"): self._image_to_doc,
            ("BMP", "TXT"): self._image_to_txt,
            ("GIF", "JPG"): self._image_convert,
            ("GIF", "PNG"): self._image_convert,
            ("GIF", "PDF"): self._image_to_pdf,
            ("GIF", "ICO"): self._image_convert,
            ("GIF", "DOCX"): self._image_to_docx,
            ("GIF", "DOC"): self._image_to_doc,
            ("TIFF", "JPG"): self._image_convert,
            ("TIFF", "PNG"): self._image_convert,
            ("TIFF", "PDF"): self._image_to_pdf,
            ("TIFF", "ICO"): self._image_convert,
            ("TIFF", "DOCX"): self._image_to_docx,
            ("TIFF", "DOC"): self._image_to_doc,
            ("TIFF", "TXT"): self._image_to_txt,
            ("WEBP", "JPG"): self._image_convert,
            ("WEBP", "PNG"): self._image_convert,
            ("WEBP", "PDF"): self._image_to_pdf,
            ("WEBP", "ICO"): self._image_convert,
            ("WEBP", "DOCX"): self._image_to_docx,
            ("WEBP", "DOC"): self._image_to_doc,
            ("WEBP", "TXT"): self._image_to_txt,
            
            # SVG conversions
            ("SVG", "PNG"): self._svg_to_image,
            ("SVG", "JPG"): self._svg_to_image,
            ("SVG", "PDF"): self._svg_to_pdf,
            
            # Text conversions
            ("TXT", "PDF"): self._txt_to_pdf,
            ("TXT", "DOCX"): self._txt_to_docx,
            ("TXT", "HTML"): self._txt_to_html,
            ("TXT", "CSV"): self._txt_to_csv,
            ("TXT", "JSON"): self._txt_to_json,
            
            # HTML conversions
            ("HTML", "PDF"): self._html_to_pdf,
            ("HTML", "DOCX"): self._html_to_docx,
            ("HTML", "TXT"): self._html_to_txt,
            ("HTML", "JPG"): self._html_to_image,
            ("HTML", "PNG"): self._html_to_image,
            
            # CSV conversions
            ("CSV", "XLSX"): self._csv_to_xlsx,
            ("CSV", "JSON"): self._csv_to_json,
            ("CSV", "XML"): self._csv_to_xml,
            ("CSV", "HTML"): self._csv_to_html,
            ("CSV", "PDF"): self._csv_to_pdf,
            
            # JSON conversions
            ("JSON", "CSV"): self._json_to_csv,
            ("JSON", "XML"): self._json_to_xml,
            ("JSON", "HTML"): self._json_to_html,
            ("JSON", "XLSX"): self._json_to_xlsx,
            
            # XML conversions
            ("XML", "JSON"): self._xml_to_json,
            ("XML", "CSV"): self._xml_to_csv,
            ("XML", "HTML"): self._xml_to_html,
            ("XML", "PDF"): self._xml_to_pdf,
            
            # PowerPoint conversions
            ("PPTX", "PDF"): self._pptx_to_pdf,
            ("PPTX", "JPG"): self._pptx_to_image,
            ("PPTX", "PNG"): self._pptx_to_image,
            ("PPTX", "HTML"): self._pptx_to_html,
            
            # Audio conversions
            ("MP3", "WAV"): self._audio_convert,
            ("MP3", "AAC"): self._audio_convert,
            ("MP3", "FLAC"): self._audio_convert,
            ("MP3", "OGG"): self._audio_convert,
            ("WAV", "MP3"): self._audio_convert,
            ("WAV", "AAC"): self._audio_convert,
            ("WAV", "FLAC"): self._audio_convert,
            
            # Video conversions
            ("MP4", "AVI"): self._video_convert,
            ("MP4", "MOV"): self._video_convert,
            ("MP4", "WMV"): self._video_convert,
            ("MP4", "MKV"): self._video_convert,
            ("MP4", "WEBM"): self._video_convert,
            ("MP4", "MP3"): self._video_to_audio,
            ("MP4", "WAV"): self._video_to_audio,
            ("AVI", "MP4"): self._video_convert,
            ("AVI", "MOV"): self._video_convert,
            ("MOV", "MP4"): self._video_convert,
            ("MOV", "AVI"): self._video_convert,
        }
        
        return converter_map.get((source.upper(), destination.upper()))
    
    # PDF Conversion Methods
    def _pdf_to_docx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            reader = PdfReader(input_path)
            doc = Document()
            
            for page_num, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (page_num / len(reader.pages)) * 60
                text = page.extract_text()
                doc.add_paragraph(text)
                if page_num < len(reader.pages) - 1:
                    doc.add_page_break()
            
            doc.save(output_path)
            return True
        except Exception as e:
            logger.error(f"PDF to DOCX conversion error: {e}")
            return False
    
    def _pdf_to_doc(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        # Convert to DOCX first, then save as DOC (limited support)
        return self._pdf_to_docx(input_path, output_path, job_id, jobs)
    
    def _pdf_to_txt(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            reader = PdfReader(input_path)
            text_content = ""
            
            for page_num, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (page_num / len(reader.pages)) * 60
                text_content += page.extract_text() + "\n\n"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            return True
        except Exception as e:
            logger.error(f"PDF to TXT conversion error: {e}")
            return False
    
    def _pdf_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            reader = PdfReader(input_path)
            html_content = "<html><body>"
            
            for page_num, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (page_num / len(reader.pages)) * 60
                text = page.extract_text()
                html_content += f"<div class='page'><h3>Page {page_num + 1}</h3><p>{text.replace(chr(10), '<br>')}</p></div>"
            
            html_content += "</body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"PDF to HTML conversion error: {e}")
            return False
    
    def _pdf_to_image(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(input_path)
            
            # Always convert first page
            page = doc[0]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(output_path)
            
            doc.close()
            jobs[job_id]["progress"] = 80
            return True
        except ImportError:
            # Fallback method using pdf2image
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(input_path)
                if images:
                    images[0].save(output_path)
                    jobs[job_id]["progress"] = 80
                    return True
            except Exception as e:
                logger.error(f"PDF to image conversion error: {e}")
                return False
        except Exception as e:
            logger.error(f"PDF to image conversion error: {e}")
            return False
    
    def _pdf_to_xlsx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            reader = PdfReader(input_path)
            wb = openpyxl.Workbook()
            ws = wb.active
            
            row = 1
            for page_num, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (page_num / len(reader.pages)) * 60
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        ws.cell(row=row, column=1, value=line.strip())
                        row += 1
            
            wb.save(output_path)
            return True
        except Exception as e:
            logger.error(f"PDF to XLSX conversion error: {e}")
            return False
    
    def _pdf_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            reader = PdfReader(input_path)
            rows = []
            
            for page_num, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (page_num / len(reader.pages)) * 60
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        rows.append([line.strip()])
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            return True
        except Exception as e:
            logger.error(f"PDF to CSV conversion error: {e}")
            return False
    
    def _pdf_to_xls(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            reader = PdfReader(input_path)
            wb = openpyxl.Workbook()
            ws = wb.active
            
            row = 1
            for page_num, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (page_num / len(reader.pages)) * 60
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        ws.cell(row=row, column=1, value=line.strip())
                        row += 1
            
            wb.save(output_path)
            return True
        except Exception as e:
            logger.error(f"PDF to XLS conversion error: {e}")
            return False
    
    # DOCX Conversion Methods
    def _docx_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            doc = Document(input_path)
            
            # Create PDF using reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            
            pdf_doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                jobs[job_id]["progress"] = 20 + (para_num / len(doc.paragraphs)) * 60
                if paragraph.text.strip():
                    p = Paragraph(paragraph.text, styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 12))
            
            pdf_doc.build(story)
            return True
        except Exception as e:
            logger.error(f"DOCX to PDF conversion error: {e}")
            return False
    
    def _docx_to_txt(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            doc = Document(input_path)
            text_content = ""
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                jobs[job_id]["progress"] = 20 + (para_num / len(doc.paragraphs)) * 60
                text_content += paragraph.text + "\n"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            return True
        except Exception as e:
            logger.error(f"DOCX to TXT conversion error: {e}")
            return False
    
    def _docx_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            doc = Document(input_path)
            html_content = "<html><body>"
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                jobs[job_id]["progress"] = 20 + (para_num / len(doc.paragraphs)) * 60
                if paragraph.text.strip():
                    html_content += f"<p>{paragraph.text}</p>"
            
            html_content += "</body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"DOCX to HTML conversion error: {e}")
            return False
    
    def _docx_to_rtf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            doc = Document(input_path)
            rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}} \f0\fs24 "
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                jobs[job_id]["progress"] = 20 + (para_num / len(doc.paragraphs)) * 60
                if paragraph.text.strip():
                    rtf_content += paragraph.text.replace('\n', r'\par ') + r'\par '
            
            rtf_content += "}"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rtf_content)
            return True
        except Exception as e:
            logger.error(f"DOCX to RTF conversion error: {e}")
            return False
    
    def _docx_to_image(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert DOCX to HTML first, then to image
            temp_html = output_path.replace(os.path.splitext(output_path)[1], '.html')
            if self._docx_to_html(input_path, temp_html, job_id, jobs):
                result = self._html_to_image(temp_html, output_path, job_id, jobs)
                os.remove(temp_html)
                return result
            return False
        except Exception as e:
            logger.error(f"DOCX to image conversion error: {e}")
            return False
    
    # DOC Conversion Methods (similar to DOCX but with limited support)
    def _doc_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        # DOC format is more complex, this is a simplified approach
        try:
            # Try to read as text and convert to PDF
            with open(input_path, 'rb') as f:
                content = f.read()
            
            # Extract readable text (very basic)
            text_content = content.decode('utf-8', errors='ignore')
            
            # Create PDF
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(output_path)
            
            lines = text_content.split('\n')
            y = 750
            for line in lines[:50]:  # Limit to first 50 lines
                if y < 50:
                    c.showPage()
                    y = 750
                c.drawString(50, y, line[:80])  # Limit line length
                y -= 20
            
            c.save()
            return True
        except Exception as e:
            logger.error(f"DOC to PDF conversion error: {e}")
            return False
    
    def _doc_to_txt(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'rb') as f:
                content = f.read()
            
            text_content = content.decode('utf-8', errors='ignore')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            return True
        except Exception as e:
            logger.error(f"DOC to TXT conversion error: {e}")
            return False
    
    def _doc_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'rb') as f:
                content = f.read()
            
            text_content = content.decode('utf-8', errors='ignore')
            html_content = f"<html><body><pre>{text_content}</pre></body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"DOC to HTML conversion error: {e}")
            return False
    
    # Excel Conversion Methods
    def _xlsx_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            df.to_csv(output_path, index=False)
            jobs[job_id]["progress"] = 80
            return True
        except Exception as e:
            logger.error(f"XLSX to CSV conversion error: {e}")
            return False
    
    def _xlsx_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            
            # Convert DataFrame to list of lists
            data = [df.columns.tolist()] + df.values.tolist()
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            doc.build([table])
            return True
        except Exception as e:
            logger.error(f"XLSX to PDF conversion error: {e}")
            return False
    
    def _xlsx_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            html_content = df.to_html()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"XLSX to HTML conversion error: {e}")
            return False
    
    def _xlsx_to_json(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            json_data = df.to_json(orient='records', indent=2)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
            return True
        except Exception as e:
            logger.error(f"XLSX to JSON conversion error: {e}")
            return False
    
    def _xlsx_to_xml(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            xml_content = df.to_xml()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            return True
        except Exception as e:
            logger.error(f"XLSX to XML conversion error: {e}")
            return False
    
    def _xls_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            df.to_csv(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"XLS to CSV conversion error: {e}")
            return False
    
    def _xls_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        return self._xlsx_to_pdf(input_path, output_path, job_id, jobs)
    
    def _xls_to_xlsx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_excel(input_path)
            df.to_excel(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"XLS to XLSX conversion error: {e}")
            return False
    
    # Image Conversion Methods
    def _image_convert(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if output_path.lower().endswith(('.jpg', '.jpeg')) and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                img.save(output_path)
            jobs[job_id]["progress"] = 80
            return True
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return False
    
    def _image_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_path, "PDF")
            return True
        except Exception as e:
            logger.error(f"Image to PDF conversion error: {e}")
            return False
    
    def _image_to_docx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert image to HTML first, then to DOCX
            temp_html = output_path.replace(os.path.splitext(output_path)[1], '.html')
            if self._image_to_html(input_path, temp_html, job_id, jobs):
                result = self._html_to_docx(temp_html, output_path, job_id, jobs)
                os.remove(temp_html)
                return result
            return False
        except Exception as e:
            logger.error(f"Image to DOCX conversion error: {e}")
            return False
    
    def _image_to_doc(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert image to HTML first, then to DOC
            temp_html = output_path.replace(os.path.splitext(output_path)[1], '.html')
            if self._image_to_html(input_path, temp_html, job_id, jobs):
                result = self._html_to_doc(temp_html, output_path, job_id, jobs)
                os.remove(temp_html)
                return result
            return False
        except Exception as e:
            logger.error(f"Image to DOC conversion error: {e}")
            return False
    
    def _image_to_xlsx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert image to HTML first, then to XLSX
            temp_html = output_path.replace(os.path.splitext(output_path)[1], '.html')
            if self._image_to_html(input_path, temp_html, job_id, jobs):
                result = self._html_to_xlsx(temp_html, output_path, job_id, jobs)
                os.remove(temp_html)
                return result
            return False
        except Exception as e:
            logger.error(f"Image to XLSX conversion error: {e}")
            return False
    
    def _image_to_pptx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert image to HTML first, then to PPTX
            temp_html = output_path.replace(os.path.splitext(output_path)[1], '.html')
            if self._image_to_html(input_path, temp_html, job_id, jobs):
                result = self._html_to_pptx(temp_html, output_path, job_id, jobs)
                os.remove(temp_html)
                return result
            return False
        except Exception as e:
            logger.error(f"Image to PPTX conversion error: {e}")
            return False
    
    def _image_to_txt(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert image to HTML first, then to TXT
            temp_html = output_path.replace(os.path.splitext(output_path)[1], '.html')
            if self._image_to_html(input_path, temp_html, job_id, jobs):
                result = self._html_to_txt(temp_html, output_path, job_id, jobs)
                os.remove(temp_html)
                return result
            return False
        except Exception as e:
            logger.error(f"Image to TXT conversion error: {e}")
            return False
    
    # SVG Conversion Methods
    def _svg_to_image(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            if output_path.lower().endswith('.png'):
                svg2png(url=input_path, write_to=output_path)
            else:
                # Convert to PNG first, then to target format
                temp_png = output_path.replace(os.path.splitext(output_path)[1], '.png')
                svg2png(url=input_path, write_to=temp_png)
                self._image_convert(temp_png, output_path, job_id, jobs)
                os.remove(temp_png)
            return True
        except Exception as e:
            logger.error(f"SVG to image conversion error: {e}")
            return False
    
    def _svg_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            svg2pdf(url=input_path, write_to=output_path)
            return True
        except Exception as e:
            logger.error(f"SVG to PDF conversion error: {e}")
            return False
    
    # Text Conversion Methods
    def _txt_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            lines = content.split('\n')
            y = height - 50
            
            for line in lines:
                if y < 50:
                    c.showPage()
                    y = height - 50
                
                # Handle long lines
                if len(line) > 80:
                    # Split long lines
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            c.drawString(50, y, current_line)
                            y -= 15
                            current_line = word + " "
                            if y < 50:
                                c.showPage()
                                y = height - 50
                    if current_line:
                        c.drawString(50, y, current_line)
                        y -= 15
                else:
                    c.drawString(50, y, line)
                    y -= 15
            
            c.save()
            return True
        except Exception as e:
            logger.error(f"TXT to PDF conversion error: {e}")
            return False
    
    def _txt_to_docx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc = Document()
            lines = content.split('\n')
            
            for line in lines:
                doc.add_paragraph(line)
            
            doc.save(output_path)
            return True
        except Exception as e:
            logger.error(f"TXT to DOCX conversion error: {e}")
            return False
    
    def _txt_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html_content = f"<html><body><pre>{content}</pre></body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"TXT to HTML conversion error: {e}")
            return False
    
    def _txt_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for line in lines:
                    writer.writerow([line.strip()])
            return True
        except Exception as e:
            logger.error(f"TXT to CSV conversion error: {e}")
            return False
    
    def _txt_to_json(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            data = {"lines": [line.strip() for line in lines]}
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"TXT to JSON conversion error: {e}")
            return False
    
    # HTML Conversion Methods
    def _html_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            import pdfkit
            pdfkit.from_file(input_path, output_path)
            return True
        except Exception as e:
            # Fallback method using weasyprint
            try:
                import weasyprint
                weasyprint.HTML(filename=input_path).write_pdf(output_path)
                return True
            except Exception as e2:
                logger.error(f"HTML to PDF conversion error: {e2}")
                return False
    
    def _html_to_docx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            doc = Document()
            lines = text.split('\n')
            for line in lines:
                if line.strip():
                    doc.add_paragraph(line.strip())
            
            doc.save(output_path)
            return True
        except Exception as e:
            logger.error(f"HTML to DOCX conversion error: {e}")
            return False
    
    def _html_to_txt(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            h = html2text.HTML2Text()
            h.ignore_links = True
            text = h.handle(html_content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return True
        except Exception as e:
            logger.error(f"HTML to TXT conversion error: {e}")
            return False
    
    def _html_to_image(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # This requires additional setup (like selenium or playwright)
            # For now, create a placeholder image
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), "HTML to Image conversion", fill='black')
            img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"HTML to image conversion error: {e}")
            return False
    
    # CSV Conversion Methods
    def _csv_to_xlsx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_csv(input_path)
            df.to_excel(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"CSV to XLSX conversion error: {e}")
            return False
    
    def _csv_to_json(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_csv(input_path)
            json_data = df.to_json(orient='records', indent=2)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
            return True
        except Exception as e:
            logger.error(f"CSV to JSON conversion error: {e}")
            return False
    
    def _csv_to_xml(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_csv(input_path)
            xml_content = df.to_xml()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            return True
        except Exception as e:
            logger.error(f"CSV to XML conversion error: {e}")
            return False
    
    def _csv_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_csv(input_path)
            html_content = df.to_html()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"CSV to HTML conversion error: {e}")
            return False
    
    def _csv_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            df = pd.read_csv(input_path)
            
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            
            # Convert DataFrame to list of lists
            data = [df.columns.tolist()] + df.values.tolist()
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            doc.build([table])
            return True
        except Exception as e:
            logger.error(f"CSV to PDF conversion error: {e}")
            return False
    
    # JSON Conversion Methods
    def _json_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = pd.DataFrame({'value': [data]})
            
            df.to_csv(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"JSON to CSV conversion error: {e}")
            return False
    
    def _json_to_xml(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            import dicttoxml
            xml_content = dicttoxml.dicttoxml(data, custom_root='root', attr_type=False)
            
            with open(output_path, 'wb') as f:
                f.write(xml_content)
            return True
        except Exception as e:
            logger.error(f"JSON to XML conversion error: {e}")
            return False
    
    def _json_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
                html_content = df.to_html()
            else:
                html_content = f"<html><body><pre>{json.dumps(data, indent=2)}</pre></body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"JSON to HTML conversion error: {e}")
            return False
    
    def _json_to_xlsx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = pd.DataFrame({'value': [data]})
            
            df.to_excel(output_path, index=False)
            return True
        except Exception as e:
            logger.error(f"JSON to XLSX conversion error: {e}")
            return False
    
    # XML Conversion Methods
    def _xml_to_json(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            import xmltodict
            with open(input_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            data = xmltodict.parse(xml_content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"XML to JSON conversion error: {e}")
            return False
    
    def _xml_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            tree = ET.parse(input_path)
            root = tree.getroot()
            
            # Extract data from XML (simplified approach)
            rows = []
            for child in root:
                row = {}
                for subchild in child:
                    row[subchild.tag] = subchild.text
                rows.append(row)
            
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False)
            else:
                # Fallback: create simple CSV with tag names and values
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['tag', 'value'])
                    for elem in root.iter():
                        if elem.text and elem.text.strip():
                            writer.writerow([elem.tag, elem.text.strip()])
            
            return True
        except Exception as e:
            logger.error(f"XML to CSV conversion error: {e}")
            return False
    
    def _xml_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            html_content = f"<html><body><pre>{xml_content}</pre></body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"XML to HTML conversion error: {e}")
            return False
    
    def _xml_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            lines = xml_content.split('\n')
            y = height - 50
            
            for line in lines:
                if y < 50:
                    c.showPage()
                    y = height - 50
                
                if len(line) > 80:
                    line = line[:80] + "..."
                
                c.drawString(50, y, line)
                y -= 15
            
            c.save()
            return True
        except Exception as e:
            logger.error(f"XML to PDF conversion error: {e}")
            return False
    
    # PowerPoint Conversion Methods
    def _pptx_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            prs = Presentation(input_path)
            
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            for slide_num, slide in enumerate(prs.slides):
                jobs[job_id]["progress"] = 20 + (slide_num / len(prs.slides)) * 60
                
                y = height - 50
                c.drawString(50, y, f"Slide {slide_num + 1}")
                y -= 30
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        lines = shape.text.split('\n')
                        for line in lines:
                            if y < 50:
                                c.showPage()
                                y = height - 50
                            c.drawString(70, y, line[:70])
                            y -= 20
                
                c.showPage()
            
            c.save()
            return True
        except Exception as e:
            logger.error(f"PPTX to PDF conversion error: {e}")
            return False
    
    def _pptx_to_image(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Create a placeholder image for the first slide
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), "PowerPoint Slide", fill='black')
            img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"PPTX to image conversion error: {e}")
            return False
    
    def _pptx_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            prs = Presentation(input_path)
            
            html_content = "<html><body>"
            
            for slide_num, slide in enumerate(prs.slides):
                html_content += f"<div class='slide'><h2>Slide {slide_num + 1}</h2>"
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        html_content += f"<p>{shape.text}</p>"
                
                html_content += "</div><hr>"
            
            html_content += "</body></html>"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.error(f"PPTX to HTML conversion error: {e}")
            return False
    
    # Audio Conversion Methods
    def _audio_convert(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Try to import pydub
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(input_path)
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            # Export with appropriate format
            audio.export(output_path, format=output_format)
            return True
        except ImportError:
            logger.error("Audio conversion requires pydub library. Install with: pip install pydub")
            return False
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return False
    
    # Video Conversion Methods
    def _video_convert(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Try to import moviepy
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(input_path)
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp4':
                clip.write_videofile(output_path, codec='libx264')
            elif output_format == 'avi':
                clip.write_videofile(output_path, codec='libxvid')
            elif output_format == 'mov':
                clip.write_videofile(output_path, codec='libx264')
            elif output_format == 'webm':
                clip.write_videofile(output_path, codec='libvpx')
            else:
                clip.write_videofile(output_path)
            
            clip.close()
            return True
        except ImportError:
            logger.error("Video conversion requires moviepy library. Install with: pip install moviepy")
            return False
        except Exception as e:
            logger.error(f"Video conversion error: {e}")
            return False
    
    def _video_to_audio(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Try to import moviepy
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(input_path)
            audio = clip.audio
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp3':
                audio.write_audiofile(output_path, codec='mp3')
            elif output_format == 'wav':
                audio.write_audiofile(output_path, codec='pcm_s16le')
            else:
                audio.write_audiofile(output_path)
            
            audio.close()
            clip.close()
            return True
        except ImportError:
            logger.error("Video to audio conversion requires moviepy library. Install with: pip install moviepy")
            return False
        except Exception as e:
            logger.error(f"Video to audio conversion error: {e}")
            return False

    # Helper methods for image conversions
    def _image_to_html(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>Image Conversion</title>
    <style>
        body {{ margin: 20px; font-family: Arial, sans-serif; }}
        .image-container {{ text-align: center; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="image-container">
        <img src="data:image/png;base64,{self._image_to_base64(input_path)}" alt="Converted Image">
    </div>
</body>
</html>''')
            return True
        except Exception as e:
            logger.error(f"Image to HTML conversion error: {e}")
            return False
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                import base64
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Image to base64 conversion error: {e}")
            return ""
    
    def _html_to_doc(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert HTML to DOCX first, then save as DOC
            temp_docx = output_path.replace('.doc', '.docx')
            if self._html_to_docx(input_path, temp_docx, job_id, jobs):
                # For DOC format, we'll just rename the DOCX file
                # In a real implementation, you'd need a proper DOC converter
                shutil.copy2(temp_docx, output_path)
                os.remove(temp_docx)
                return True
            return False
        except Exception as e:
            logger.error(f"HTML to DOC conversion error: {e}")
            return False
    
    def _html_to_xlsx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert HTML to CSV first, then to XLSX
            temp_csv = output_path.replace('.xlsx', '.csv')
            if self._html_to_csv(input_path, temp_csv, job_id, jobs):
                result = self._csv_to_xlsx(temp_csv, output_path, job_id, jobs)
                os.remove(temp_csv)
                return result
            return False
        except Exception as e:
            logger.error(f"HTML to XLSX conversion error: {e}")
            return False
    
    def _html_to_pptx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert HTML to PDF first, then to PPTX
            temp_pdf = output_path.replace('.pptx', '.pdf')
            if self._html_to_pdf(input_path, temp_pdf, job_id, jobs):
                result = self._pdf_to_pptx(temp_pdf, output_path, job_id, jobs)
                os.remove(temp_pdf)
                return result
            return False
        except Exception as e:
            logger.error(f"HTML to PPTX conversion error: {e}")
            return False
    
    def _html_to_csv(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract text from HTML
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
            
            # Write as CSV
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                for line in text.split('\n'):
                    if line.strip():
                        writer.writerow([line.strip()])
            
            return True
        except Exception as e:
            logger.error(f"HTML to CSV conversion error: {e}")
            return False
    
    def _pdf_to_pptx(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        try:
            # Convert PDF to images first, then to PPTX
            temp_dir = os.path.dirname(output_path)
            temp_images = []
            
            reader = PdfReader(input_path)
            for i, page in enumerate(reader.pages):
                jobs[job_id]["progress"] = 20 + (i / len(reader.pages)) * 60
                
                # Convert page to image
                temp_image = os.path.join(temp_dir, f"page_{i}.png")
                page_image = page.to_image()
                page_image.save(temp_image)
                temp_images.append(temp_image)
            
            # Create PPTX with images
            prs = Presentation()
            for temp_image in temp_images:
                slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
                slide.shapes.add_picture(temp_image, 0, 0, prs.slide_width, prs.slide_height)
                os.remove(temp_image)
            
            prs.save(output_path)
            return True
        except Exception as e:
            logger.error(f"PDF to PPTX conversion error: {e}")
            return False
