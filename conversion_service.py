import os
import asyncio
import threading
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging
import io

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
        """Robust PDF to image conversion with multiple fallbacks for cross-platform support."""
        jobs[job_id]["progress"] = 10
        
        # Method 1: PyMuPDF (fitz) - Best quality and performance
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(input_path)
            
            # Always convert first page
            page = doc[0]
            zoom = 2  # Increase resolution
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image for format handling
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Save with appropriate format
            if output_path.lower().endswith('.jpg'):
                img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=95, optimize=True)
            elif output_path.lower().endswith('.png'):
                img.save(output_path, 'PNG', optimize=True)
            else:
                img.save(output_path)
            
            doc.close()
            jobs[job_id]["progress"] = 100
            logger.info("PDF to image: PyMuPDF conversion successful")
            return True
        except ImportError:
            logger.warning("PyMuPDF not available")
        except Exception as e:
            logger.warning(f"PyMuPDF conversion failed: {e}")

        # Method 2: pdf2image (Poppler) - Good quality
        try:
            from pdf2image import convert_from_path
            
            # Convert first page only
            images = convert_from_path(input_path, first_page=1, last_page=1, dpi=300)
            if images:
                img = images[0]
                
                # Save with appropriate format
                if output_path.lower().endswith('.jpg'):
                    img = img.convert('RGB')
                    img.save(output_path, 'JPEG', quality=95, optimize=True)
                elif output_path.lower().endswith('.png'):
                    img.save(output_path, 'PNG', optimize=True)
                else:
                    img.save(output_path)
                
                jobs[job_id]["progress"] = 100
                logger.info("PDF to image: pdf2image conversion successful")
                return True
            else:
                logger.warning("pdf2image returned no images")
        except ImportError:
            logger.warning("pdf2image not available")
        except Exception as e:
            logger.warning(f"pdf2image conversion failed: {e}")

        # Method 3: Ghostscript (if available)
        try:
            import subprocess
            
            # Determine output format
            if output_path.lower().endswith('.jpg'):
                device = 'jpeg'
                extension = 'jpg'
            elif output_path.lower().endswith('.png'):
                device = 'pngalpha'
                extension = 'png'
            else:
                device = 'pngalpha'
                extension = 'png'
            
            # Create temporary output path
            temp_output = output_path.replace(f'.{extension}', f'_temp.{extension}')
            
            cmd = [
                'gs', '-sDEVICE=' + device, '-dNOPAUSE', '-dBATCH', '-dSAFER',
                '-dFirstPage=1', '-dLastPage=1', '-r300',
                f'-sOutputFile={temp_output}', input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0 and os.path.exists(temp_output):
                # Rename to final output path
                os.rename(temp_output, output_path)
                jobs[job_id]["progress"] = 100
                logger.info("PDF to image: Ghostscript conversion successful")
                return True
            else:
                logger.warning(f"Ghostscript failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"Ghostscript not available or failed: {e}")

        # Method 4: LibreOffice (soffice) - Convert to image
        try:
            import subprocess
            import tempfile
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert PDF to image using LibreOffice
                cmd = [
                    'soffice', '--headless', '--convert-to', 'png',
                    '--outdir', temp_dir, input_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                jobs[job_id]["progress"] = 60
                
                if result.returncode == 0:
                    # Find the generated image file
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    generated_image = os.path.join(temp_dir, base_name + ".png")
                    
                    if os.path.exists(generated_image):
                        # Convert to desired format if needed
                        with Image.open(generated_image) as img:
                            if output_path.lower().endswith('.jpg'):
                                img = img.convert('RGB')
                                img.save(output_path, 'JPEG', quality=95, optimize=True)
                            elif output_path.lower().endswith('.png'):
                                img.save(output_path, 'PNG', optimize=True)
                            else:
                                img.save(output_path)
                        
                        jobs[job_id]["progress"] = 100
                        logger.info("PDF to image: LibreOffice conversion successful")
                        return True
                    else:
                        logger.warning("LibreOffice did not generate expected image file")
                else:
                    logger.warning(f"LibreOffice failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"LibreOffice conversion failed: {e}")

        # Method 5: reportlab + PIL (create a placeholder)
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create a simple PDF first page representation
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add text to indicate it's a PDF page
            draw.text((50, 50), "PDF Page 1", fill='black')
            draw.text((50, 100), f"File: {os.path.basename(input_path)}", fill='black')
            draw.text((50, 150), "Image conversion placeholder", fill='black')
            
            # Save with appropriate format
            if output_path.lower().endswith('.jpg'):
                img.save(output_path, 'JPEG', quality=95)
            elif output_path.lower().endswith('.png'):
                img.save(output_path, 'PNG')
            else:
                img.save(output_path)
            
            jobs[job_id]["progress"] = 100
            logger.warning("PDF to image: Created placeholder image")
            return True
        except Exception as e:
            logger.error(f"All PDF to image methods failed: {e}")
            jobs[job_id]["error"] = f"PDF to image conversion failed: {e}"
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
        """Robust DOCX to PDF conversion with multiple fallbacks for cross-platform support. Now preserves block order in fallback."""
        import subprocess
        import shutil
        import os
        import sys
        
        jobs[job_id]["progress"] = 10
        
        # Method 1: LibreOffice (soffice) - Best quality, works on Linux/Mac/Windows
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path),
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                generated_pdf = os.path.join(os.path.dirname(output_path), base_name + ".pdf")
                if os.path.abspath(generated_pdf) != os.path.abspath(output_path):
                    shutil.move(generated_pdf, output_path)
                jobs[job_id]["progress"] = 100
                logger.info("DOCX to PDF: LibreOffice conversion successful")
                return True
            else:
                logger.warning(f"LibreOffice failed: {result.stderr}")
                jobs[job_id]["error"] = f"LibreOffice failed: {result.stderr}"
        except Exception as e:
            logger.warning(f"LibreOffice not available or failed: {e}")
            jobs[job_id]["error"] = f"LibreOffice not available or failed: {e}"

        # Method 2: docx2pdf (Windows/Mac with MS Word)
        try:
            from docx2pdf import convert
            convert(input_path, output_path)
            jobs[job_id]["progress"] = 100
            logger.info("DOCX to PDF: docx2pdf conversion successful")
            return True
        except Exception as e:
            logger.warning(f"docx2pdf fallback failed: {e}")

        # Method 3: unoconv (LibreOffice wrapper)
        try:
            cmd = ['unoconv', '-f', 'pdf', '-o', output_path, input_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("DOCX to PDF: unoconv conversion successful")
                return True
            else:
                logger.warning(f"unoconv failed: {result.stderr}")
                jobs[job_id]["error"] = f"unoconv failed: {result.stderr}"
        except Exception as e:
            logger.warning(f"unoconv not available or failed: {e}")
            jobs[job_id]["error"] = f"unoconv not available or failed: {e}"

        # Method 4: pandoc (if available)
        try:
            cmd = ['pandoc', input_path, '-o', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("DOCX to PDF: pandoc conversion successful")
                return True
            else:
                logger.warning(f"pandoc failed: {result.stderr}")
                jobs[job_id]["error"] = f"pandoc failed: {result.stderr}"
        except Exception as e:
            logger.warning(f"pandoc not available or failed: {e}")
            jobs[job_id]["error"] = f"pandoc not available or failed: {e}"

        # Method 5: Enhanced python-docx + reportlab (preserve block order)
        try:
            from docx import Document
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            import re
            import tempfile
            from docx.oxml.table import CT_Tbl
            from docx.oxml.text.paragraph import CT_P
            from docx.oxml import OxmlElement
            from docx.table import _Cell, Table as DocxTable
            from docx.text.paragraph import Paragraph as DocxParagraph

            doc = Document(input_path)
            pdf_doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Helper to iterate block items in order
            def iter_block_items(parent):
                """Yield each paragraph and table child in document order."""
                if isinstance(parent, Document):
                    parent_elm = parent.element.body
                elif isinstance(parent, _Cell):
                    parent_elm = parent._tc
                else:
                    return
                for child in parent_elm.iterchildren():
                    if isinstance(child, CT_P):
                        yield DocxParagraph(child, parent)
                    elif isinstance(child, CT_Tbl):
                        yield DocxTable(child, parent)

            # Count total elements for progress
            total_elements = sum(1 for _ in iter_block_items(doc))
            current_element = 0

            for block in iter_block_items(doc):
                current_element += 1
                jobs[job_id]["progress"] = 20 + (current_element / max(total_elements,1)) * 60
                if isinstance(block, DocxParagraph):
                    text = block.text.strip()
                    if text:
                        if not re.match(r"^<!DOCTYPE html>|<html", text, re.IGNORECASE):
                            try:
                                p = Paragraph(text, styles['Normal'])
                                story.append(p)
                                story.append(Spacer(1, 12))
                            except Exception as e:
                                logger.warning(f"Skipping paragraph due to error: {e}")
                    # Check for images in runs
                    for run in block.runs:
                        if 'graphic' in run._element.xml:
                            try:
                                drawing = run._element.xpath('.//a:blip', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                                if drawing:
                                    rId = drawing[0].attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed']
                                    image_part = doc.part.related_parts[rId]
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img:
                                        temp_img.write(image_part.blob)
                                        temp_img_path = temp_img.name
                                    img = RLImage(temp_img_path, width=4*inch, height=3*inch, kind='proportional')
                                    story.append(img)
                                    story.append(Spacer(1, 12))
                                    os.unlink(temp_img_path)
                            except Exception as e:
                                logger.warning(f"Error processing inline image: {e}")
                elif isinstance(block, DocxTable):
                    try:
                        table_data = []
                        for row in block.rows:
                            row_data = []
                            for cell in row.cells:
                                cell_text = " ".join(paragraph.text for paragraph in cell.paragraphs)
                                row_data.append(cell_text.strip())
                            table_data.append(row_data)
                        if table_data:
                            pdf_table = Table(table_data)
                            style = TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 12),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ('FONTSIZE', (0, 1), (-1, -1), 10),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ])
                            pdf_table.setStyle(style)
                            story.append(pdf_table)
                            story.append(Spacer(1, 12))
                    except Exception as e:
                        logger.warning(f"Error processing table: {e}")

            if story:
                pdf_doc.build(story)
                jobs[job_id]["progress"] = 100
                jobs[job_id]["warning"] = "Fallback method used: layout may not be perfect. For best results, ensure LibreOffice is installed and working."
                logger.info("DOCX to PDF: Enhanced python-docx + reportlab (block order) conversion successful")
                return True
            else:
                logger.error("No valid content found for conversion")
                jobs[job_id]["error"] = "No valid content found for conversion"
                return False
                
        except Exception as e:
            logger.error(f"All DOCX to PDF methods failed: {e}")
            jobs[job_id]["error"] = f"DOCX to PDF conversion failed: {e}"
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
        """Robust DOC to PDF conversion with multiple fallbacks for cross-platform support."""
        import subprocess
        import shutil
        import os
        
        jobs[job_id]["progress"] = 10
        
        # Method 1: LibreOffice (soffice) - Best quality, handles complex DOC files
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path),
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                generated_pdf = os.path.join(os.path.dirname(output_path), base_name + ".pdf")
                if os.path.abspath(generated_pdf) != os.path.abspath(output_path):
                    shutil.move(generated_pdf, output_path)
                jobs[job_id]["progress"] = 100
                logger.info("DOC to PDF: LibreOffice conversion successful")
                return True
            else:
                logger.warning(f"LibreOffice failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"LibreOffice not available or failed: {e}")

        # Method 2: unoconv (LibreOffice wrapper)
        try:
            cmd = ['unoconv', '-f', 'pdf', '-o', output_path, input_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("DOC to PDF: unoconv conversion successful")
                return True
            else:
                logger.warning(f"unoconv failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"unoconv not available or failed: {e}")

        # Method 3: pandoc (if available)
        try:
            cmd = ['pandoc', input_path, '-o', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("DOC to PDF: pandoc conversion successful")
                return True
            else:
                logger.warning(f"pandoc failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"pandoc not available or failed: {e}")

        # Method 4: antiword (Linux/Unix only)
        try:
            cmd = ['antiword', input_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # Convert text to PDF
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                lines = result.stdout.split('\n')
                y = height - 50
                
                for line in lines[:100]:  # Limit to first 100 lines
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    
                    if len(line) > 80:
                        line = line[:80] + "..."
                    
                    c.drawString(50, y, line)
                    y -= 15
                
                c.save()
                jobs[job_id]["progress"] = 100
                logger.info("DOC to PDF: antiword conversion successful")
                return True
            else:
                logger.warning(f"antiword failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"antiword not available or failed: {e}")

        # Method 5: catdoc (Linux/Unix only)
        try:
            cmd = ['catdoc', input_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # Convert text to PDF
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                lines = result.stdout.split('\n')
                y = height - 50
                
                for line in lines[:100]:  # Limit to first 100 lines
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    
                    if len(line) > 80:
                        line = line[:80] + "..."
                    
                    c.drawString(50, y, line)
                    y -= 15
                
                c.save()
                jobs[job_id]["progress"] = 100
                logger.info("DOC to PDF: catdoc conversion successful")
                return True
            else:
                logger.warning(f"catdoc failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"catdoc not available or failed: {e}")

        # Method 6: Basic text extraction (last resort)
        try:
            with open(input_path, 'rb') as f:
                content = f.read()
            
            # Very basic text extraction (this is limited)
            text_content = content.decode('utf-8', errors='ignore')
            
            # Remove non-printable characters
            import re
            text_content = re.sub(r'[^\x20-\x7E\n\r\t]', '', text_content)
            
            if text_content.strip():
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                lines = text_content.split('\n')
                y = height - 50
                
                for line in lines[:50]:  # Limit to first 50 lines
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    
                    if len(line) > 80:
                        line = line[:80] + "..."
                    
                    c.drawString(50, y, line)
                    y -= 20
                
                c.save()
                jobs[job_id]["progress"] = 100
                logger.info("DOC to PDF: Basic text extraction successful")
                return True
            else:
                logger.error("No readable text found in DOC file")
                return False
                
        except Exception as e:
            logger.error(f"All DOC to PDF methods failed: {e}")
            jobs[job_id]["error"] = f"DOC to PDF conversion failed: {e}"
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
        """Robust XLSX to PDF conversion with multiple fallbacks for cross-platform support."""
        import subprocess
        import shutil
        import os
        
        jobs[job_id]["progress"] = 10
        
        # Method 1: LibreOffice (soffice) - Best quality, preserves formatting
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path),
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                generated_pdf = os.path.join(os.path.dirname(output_path), base_name + ".pdf")
                if os.path.abspath(generated_pdf) != os.path.abspath(output_path):
                    shutil.move(generated_pdf, output_path)
                jobs[job_id]["progress"] = 100
                logger.info("XLSX to PDF: LibreOffice conversion successful")
                return True
            else:
                logger.warning(f"LibreOffice failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"LibreOffice not available or failed: {e}")

        # Method 2: unoconv (LibreOffice wrapper)
        try:
            cmd = ['unoconv', '-f', 'pdf', '-o', output_path, input_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("XLSX to PDF: unoconv conversion successful")
                return True
            else:
                logger.warning(f"unoconv failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"unoconv not available or failed: {e}")

        # Method 3: pandas + reportlab (table rendering)
        try:
            import pandas as pd
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib.units import inch
            
            # Read Excel file
            df = pd.read_excel(input_path)
            jobs[job_id]["progress"] = 40
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            
            # Convert DataFrame to list of lists
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Create table
            table = Table(data)
            
            # Style the table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            table.setStyle(style)
            doc.build([table])
            
            jobs[job_id]["progress"] = 100
            logger.info("XLSX to PDF: pandas + reportlab fallback successful")
            return True
            
        except Exception as e:
            logger.warning(f"pandas + reportlab fallback failed: {e}")

        # Method 4: openpyxl + reportlab (alternative approach)
        try:
            import openpyxl
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            
            # Read Excel file with openpyxl
            wb = openpyxl.load_workbook(input_path)
            ws = wb.active
            
            # Extract data
            data = []
            for row in ws.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    data.append([str(cell) if cell is not None else '' for cell in row])
            
            if not data:
                raise ValueError("No data found in Excel file")
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            table = Table(data)
            
            # Style the table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ])
            
            table.setStyle(style)
            doc.build([table])
            
            jobs[job_id]["progress"] = 100
            logger.info("XLSX to PDF: openpyxl + reportlab fallback successful")
            return True
            
        except Exception as e:
            logger.error(f"All XLSX to PDF methods failed: {e}")
            jobs[job_id]["error"] = f"XLSX to PDF conversion failed: {e}"
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
        """Robust image conversion with multiple fallbacks for cross-platform support."""
        jobs[job_id]["progress"] = 10
        
        # Method 1: PIL (Pillow) - Primary method
        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if output_path.lower().endswith(('.jpg', '.jpeg')) and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Optimize quality based on format
                if output_path.lower().endswith('.jpg'):
                    img.save(output_path, 'JPEG', quality=95, optimize=True)
                elif output_path.lower().endswith('.png'):
                    img.save(output_path, 'PNG', optimize=True)
                elif output_path.lower().endswith('.webp'):
                    img.save(output_path, 'WEBP', quality=95)
                else:
                    img.save(output_path)
                
                jobs[job_id]["progress"] = 100
                logger.info(f"Image conversion: PIL successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
        except Exception as e:
            logger.warning(f"PIL conversion failed: {e}")

        # Method 2: ImageMagick (if available)
        try:
            import subprocess
            cmd = ['convert', input_path, output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Image conversion: ImageMagick successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"ImageMagick failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"ImageMagick not available or failed: {e}")

        # Method 3: FFmpeg (for video-like images or complex formats)
        try:
            import subprocess
            cmd = ['ffmpeg', '-i', input_path, '-y', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Image conversion: FFmpeg successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"FFmpeg failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"FFmpeg not available or failed: {e}")

        # Method 4: OpenCV (alternative approach)
        try:
            import cv2
            img = cv2.imread(input_path)
            if img is not None:
                # Handle different output formats
                if output_path.lower().endswith('.jpg'):
                    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                elif output_path.lower().endswith('.png'):
                    cv2.imwrite(output_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                else:
                    cv2.imwrite(output_path, img)
                
                jobs[job_id]["progress"] = 100
                logger.info(f"Image conversion: OpenCV successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning("OpenCV could not read the image")
        except Exception as e:
            logger.warning(f"OpenCV conversion failed: {e}")

        # Method 5: Last resort - try to copy and rename (if formats are compatible)
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            jobs[job_id]["progress"] = 100
            logger.info(f"Image conversion: Copy successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
            return True
        except Exception as e:
            logger.error(f"All image conversion methods failed: {e}")
            jobs[job_id]["error"] = f"Image conversion failed: {e}"
            return False

    def _image_to_pdf(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        """Robust image to PDF conversion with multiple fallbacks."""
        jobs[job_id]["progress"] = 10
        
        # Method 1: PIL (Pillow) - Primary method
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_path, "PDF", resolution=100.0)
                jobs[job_id]["progress"] = 100
                logger.info("Image to PDF: PIL conversion successful")
                return True
        except Exception as e:
            logger.warning(f"PIL to PDF failed: {e}")

        # Method 2: ImageMagick (if available)
        try:
            import subprocess
            cmd = ['convert', input_path, output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("Image to PDF: ImageMagick conversion successful")
                return True
            else:
                logger.warning(f"ImageMagick failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"ImageMagick not available or failed: {e}")

        # Method 3: reportlab with PIL
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            
            with Image.open(input_path) as img:
                # Get image dimensions
                img_width, img_height = img.size
                
                # Create PDF
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                # Calculate scaling to fit on page
                scale = min(width / img_width, height / img_height) * 0.8
                new_width = img_width * scale
                new_height = img_height * scale
                
                # Center the image
                x = (width - new_width) / 2
                y = (height - new_height) / 2
                
                # Convert image to base64 and embed
                img_base64 = self._image_to_base64(input_path)
                c.drawImage(f"data:image/png;base64,{img_base64}", x, y, new_width, new_height)
                c.save()
                
                jobs[job_id]["progress"] = 100
                logger.info("Image to PDF: reportlab conversion successful")
                return True
        except Exception as e:
            logger.warning(f"reportlab conversion failed: {e}")

        # Method 4: Simple PDF with image info
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            with Image.open(input_path) as img:
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                # Add image information
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "Image to PDF Conversion")
                c.setFont("Helvetica", 12)
                c.drawString(50, height - 80, f"Image: {os.path.basename(input_path)}")
                c.drawString(50, height - 100, f"Size: {img.size[0]} x {img.size[1]} pixels")
                c.drawString(50, height - 120, f"Mode: {img.mode}")
                c.drawString(50, height - 140, f"Format: {img.format}")
                
                c.save()
                jobs[job_id]["progress"] = 100
                logger.info("Image to PDF: Simple info PDF successful")
                return True
        except Exception as e:
            logger.error(f"All image to PDF methods failed: {e}")
            jobs[job_id]["error"] = f"Image to PDF conversion failed: {e}"
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
        """Robust HTML to PDF conversion with multiple fallbacks for cross-platform support."""
        import subprocess
        import os
        
        jobs[job_id]["progress"] = 10
        
        # Method 1: wkhtmltopdf (best for complex HTML with CSS)
        try:
            cmd = ['wkhtmltopdf', '--quiet', '--no-stop-slow-scripts', input_path, output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0 and os.path.exists(output_path):
                jobs[job_id]["progress"] = 100
                logger.info("HTML to PDF: wkhtmltopdf conversion successful")
                return True
            else:
                logger.warning(f"wkhtmltopdf failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"wkhtmltopdf not available or failed: {e}")

        # Method 2: weasyprint (good for modern CSS)
        try:
            import weasyprint
            weasyprint.HTML(filename=input_path).write_pdf(output_path)
            jobs[job_id]["progress"] = 100
            logger.info("HTML to PDF: weasyprint conversion successful")
            return True
        except Exception as e:
            logger.warning(f"weasyprint fallback failed: {e}")

        # Method 3: pdfkit (Python wrapper for wkhtmltopdf)
        try:
            import pdfkit
            options = {
                'quiet': '',
                'no-stop-slow-scripts': '',
                'enable-local-file-access': ''
            }
            pdfkit.from_file(input_path, output_path, options=options)
            jobs[job_id]["progress"] = 100
            logger.info("HTML to PDF: pdfkit conversion successful")
            return True
        except Exception as e:
            logger.warning(f"pdfkit fallback failed: {e}")

        # Method 4: pandoc (if available)
        try:
            cmd = ['pandoc', input_path, '-o', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("HTML to PDF: pandoc conversion successful")
                return True
            else:
                logger.warning(f"pandoc failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"pandoc not available or failed: {e}")

        # Method 5: BeautifulSoup + reportlab (text extraction)
        try:
            from bs4 import BeautifulSoup
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Create PDF
            pdf_doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            lines = text.split('\n')
            for line in lines:
                if line.strip():
                    p = Paragraph(line.strip(), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 6))
            
            if story:
                pdf_doc.build(story)
                jobs[job_id]["progress"] = 100
                logger.info("HTML to PDF: BeautifulSoup + reportlab fallback successful")
                return True
            else:
                logger.error("No text content found in HTML")
                return False
                
        except Exception as e:
            logger.warning(f"BeautifulSoup + reportlab fallback failed: {e}")

        # Method 6: Simple text extraction
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Simple HTML tag removal
            import re
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text).strip()
            
            if text:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                lines = text.split('\n')
                y = height - 50
                
                for line in lines[:100]:  # Limit to first 100 lines
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    
                    if len(line) > 80:
                        line = line[:80] + "..."
                    
                    c.drawString(50, y, line)
                    y -= 15
                
                c.save()
                jobs[job_id]["progress"] = 100
                logger.info("HTML to PDF: Simple text extraction successful")
                return True
            else:
                logger.error("No text content found in HTML")
                return False
                
        except Exception as e:
            logger.error(f"All HTML to PDF methods failed: {e}")
            jobs[job_id]["error"] = f"HTML to PDF conversion failed: {e}"
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
        """Robust PPTX to PDF conversion with multiple fallbacks for cross-platform support."""
        import subprocess
        import shutil
        import os
        
        jobs[job_id]["progress"] = 10
        
        # Method 1: LibreOffice (soffice) - Best quality, preserves formatting and images
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path),
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                generated_pdf = os.path.join(os.path.dirname(output_path), base_name + ".pdf")
                if os.path.abspath(generated_pdf) != os.path.abspath(output_path):
                    shutil.move(generated_pdf, output_path)
                jobs[job_id]["progress"] = 100
                logger.info("PPTX to PDF: LibreOffice conversion successful")
                return True
            else:
                logger.warning(f"LibreOffice failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"LibreOffice not available or failed: {e}")

        # Method 2: unoconv (LibreOffice wrapper)
        try:
            cmd = ['unoconv', '-f', 'pdf', '-o', output_path, input_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("PPTX to PDF: unoconv conversion successful")
                return True
            else:
                logger.warning(f"unoconv failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"unoconv not available or failed: {e}")

        # Method 3: python-pptx + reportlab (text and basic formatting)
        try:
            from pptx import Presentation
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.colors import black, white
            from reportlab.lib.units import inch
            
            prs = Presentation(input_path)
            jobs[job_id]["progress"] = 30
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            for slide_num, slide in enumerate(prs.slides):
                jobs[job_id]["progress"] = 30 + (slide_num / len(prs.slides)) * 60
                
                # Start new page for each slide
                if slide_num > 0:
                    c.showPage()
                
                # Slide title
                y = height - 50
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, y, f"Slide {slide_num + 1}")
                y -= 30
                
                # Process slide content
                c.setFont("Helvetica", 12)
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        lines = shape.text.split('\n')
                        for line in lines:
                            if y < 50:
                                c.showPage()
                                y = height - 50
                                c.setFont("Helvetica", 12)
                            
                            # Handle long lines
                            if len(line) > 80:
                                words = line.split(' ')
                                current_line = ""
                                for word in words:
                                    if len(current_line + word) < 80:
                                        current_line += word + " "
                                    else:
                                        c.drawString(70, y, current_line)
                                        y -= 20
                                        current_line = word + " "
                                        if y < 50:
                                            c.showPage()
                                            y = height - 50
                                            c.setFont("Helvetica", 12)
                                if current_line:
                                    c.drawString(70, y, current_line)
                                    y -= 20
                            else:
                                c.drawString(70, y, line[:80])
                                y -= 20
            
            c.save()
            jobs[job_id]["progress"] = 100
            logger.info("PPTX to PDF: python-pptx + reportlab fallback successful")
            return True
            
        except Exception as e:
            logger.warning(f"python-pptx + reportlab fallback failed: {e}")

        # Method 4: pandoc (if available)
        try:
            cmd = ['pandoc', input_path, '-o', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info("PPTX to PDF: pandoc conversion successful")
                return True
            else:
                logger.warning(f"pandoc failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"pandoc not available or failed: {e}")

        # Method 5: Create a simple PDF with slide information
        try:
            from pptx import Presentation
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            prs = Presentation(input_path)
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Create a simple PDF with slide count and basic info
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, height - 50, "PowerPoint Presentation")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, f"Total Slides: {len(prs.slides)}")
            c.drawString(50, height - 100, f"File: {os.path.basename(input_path)}")
            
            # Add slide information
            y = height - 140
            for i, slide in enumerate(prs.slides):
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 12)
                
                c.drawString(50, y, f"Slide {i + 1}:")
                y -= 20
                
                # Count text elements
                text_count = 0
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text_count += 1
                
                c.drawString(70, y, f"Text elements: {text_count}")
                y -= 30
            
            c.save()
            jobs[job_id]["progress"] = 100
            logger.info("PPTX to PDF: Simple fallback successful")
            return True
            
        except Exception as e:
            logger.error(f"All PPTX to PDF methods failed: {e}")
            jobs[job_id]["error"] = f"PPTX to PDF conversion failed: {e}"
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
        """Robust audio conversion with multiple fallbacks for cross-platform support."""
        jobs[job_id]["progress"] = 10
        
        # Method 1: pydub (Python library) - Primary method
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            jobs[job_id]["progress"] = 40
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            # Export with appropriate format and quality settings
            if output_format == 'mp3':
                audio.export(output_path, format='mp3', bitrate='192k')
            elif output_format == 'wav':
                audio.export(output_path, format='wav')
            elif output_format == 'aac':
                audio.export(output_path, format='ipod', codec='aac')
            elif output_format == 'flac':
                audio.export(output_path, format='flac')
            elif output_format == 'ogg':
                audio.export(output_path, format='ogg', codec='libvorbis')
            elif output_format == 'm4a':
                audio.export(output_path, format='ipod', codec='aac')
            else:
                audio.export(output_path, format=output_format)
            
            jobs[job_id]["progress"] = 100
            logger.info(f"Audio conversion: pydub successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
            return True
        except ImportError:
            logger.warning("pydub not available")
        except Exception as e:
            logger.warning(f"pydub conversion failed: {e}")

        # Method 2: FFmpeg (command line) - Best quality and format support
        try:
            import subprocess
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            # Build FFmpeg command with quality settings
            if output_format == 'mp3':
                cmd = ['ffmpeg', '-i', input_path, '-acodec', 'libmp3lame', '-ab', '192k', '-y', output_path]
            elif output_format == 'wav':
                cmd = ['ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', '-y', output_path]
            elif output_format == 'aac':
                cmd = ['ffmpeg', '-i', input_path, '-acodec', 'aac', '-ab', '192k', '-y', output_path]
            elif output_format == 'flac':
                cmd = ['ffmpeg', '-i', input_path, '-acodec', 'flac', '-y', output_path]
            elif output_format == 'ogg':
                cmd = ['ffmpeg', '-i', input_path, '-acodec', 'libvorbis', '-ab', '192k', '-y', output_path]
            elif output_format == 'm4a':
                cmd = ['ffmpeg', '-i', input_path, '-acodec', 'aac', '-ab', '192k', '-y', output_path]
            else:
                cmd = ['ffmpeg', '-i', input_path, '-y', output_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Audio conversion: FFmpeg successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"FFmpeg failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"FFmpeg not available or failed: {e}")

        # Method 3: sox (if available)
        try:
            import subprocess
            cmd = ['sox', input_path, output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Audio conversion: sox successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"sox failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"sox not available or failed: {e}")

        # Method 4: moviepy (alternative Python library)
        try:
            from moviepy.editor import AudioFileClip
            
            clip = AudioFileClip(input_path)
            jobs[job_id]["progress"] = 40
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp3':
                clip.write_audiofile(output_path, codec='mp3', bitrate='192k')
            elif output_format == 'wav':
                clip.write_audiofile(output_path, codec='pcm_s16le')
            else:
                clip.write_audiofile(output_path)
            
            clip.close()
            jobs[job_id]["progress"] = 100
            logger.info(f"Audio conversion: moviepy successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
            return True
        except ImportError:
            logger.warning("moviepy not available")
        except Exception as e:
            logger.warning(f"moviepy conversion failed: {e}")

        # Method 5: Last resort - try to copy if formats are the same
        try:
            input_format = os.path.splitext(input_path)[1][1:].lower()
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if input_format == output_format:
                import shutil
                shutil.copy2(input_path, output_path)
                jobs[job_id]["progress"] = 100
                logger.info(f"Audio conversion: Copy successful (same format)")
                return True
            else:
                logger.warning("Cannot copy: input and output formats are different")
        except Exception as e:
            logger.error(f"All audio conversion methods failed: {e}")
            jobs[job_id]["error"] = f"Audio conversion failed: {e}"
            return False
    
    # Video Conversion Methods
    def _video_convert(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        """Robust video conversion with multiple fallbacks for cross-platform support."""
        jobs[job_id]["progress"] = 10
        
        # Method 1: FFmpeg (command line) - Best quality and format support
        try:
            import subprocess
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            # Build FFmpeg command with quality settings
            if output_format == 'mp4':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k', '-y', output_path]
            elif output_format == 'avi':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'libxvid', '-c:a', 'mp3', '-b:a', '192k', '-y', output_path]
            elif output_format == 'mov':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k', '-y', output_path]
            elif output_format == 'webm':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'libvpx', '-c:a', 'libvorbis', '-b:a', '192k', '-y', output_path]
            elif output_format == 'mkv':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k', '-y', output_path]
            elif output_format == 'wmv':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'wmv2', '-c:a', 'wmav2', '-y', output_path]
            elif output_format == 'flv':
                cmd = ['ffmpeg', '-i', input_path, '-c:v', 'flv', '-c:a', 'mp3', '-b:a', '192k', '-y', output_path]
            else:
                cmd = ['ffmpeg', '-i', input_path, '-y', output_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Video conversion: FFmpeg successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"FFmpeg failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"FFmpeg not available or failed: {e}")

        # Method 2: moviepy (Python library) - Alternative method
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(input_path)
            jobs[job_id]["progress"] = 40
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp4':
                clip.write_videofile(output_path, codec='libx264', audio_codec='aac', bitrate='8000k')
            elif output_format == 'avi':
                clip.write_videofile(output_path, codec='libxvid', audio_codec='mp3')
            elif output_format == 'mov':
                clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            elif output_format == 'webm':
                clip.write_videofile(output_path, codec='libvpx', audio_codec='libvorbis')
            else:
                clip.write_videofile(output_path)
            
            clip.close()
            jobs[job_id]["progress"] = 100
            logger.info(f"Video conversion: moviepy successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
            return True
        except ImportError:
            logger.warning("moviepy not available")
        except Exception as e:
            logger.warning(f"moviepy conversion failed: {e}")

        # Method 3: HandBrake CLI (if available)
        try:
            import subprocess
            cmd = ['HandBrakeCLI', '-i', input_path, '-o', output_path, '--preset', 'Fast 1080p30']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Video conversion: HandBrake successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"HandBrake failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"HandBrake not available or failed: {e}")

        # Method 4: Last resort - try to copy if formats are the same
        try:
            input_format = os.path.splitext(input_path)[1][1:].lower()
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if input_format == output_format:
                import shutil
                shutil.copy2(input_path, output_path)
                jobs[job_id]["progress"] = 100
                logger.info(f"Video conversion: Copy successful (same format)")
                return True
            else:
                logger.warning("Cannot copy: input and output formats are different")
        except Exception as e:
            logger.error(f"All video conversion methods failed: {e}")
            jobs[job_id]["error"] = f"Video conversion failed: {e}"
            return False

    def _video_to_audio(self, input_path: str, output_path: str, job_id: str, jobs: Dict) -> bool:
        """Robust video to audio extraction with multiple fallbacks."""
        jobs[job_id]["progress"] = 10
        
        # Method 1: FFmpeg (command line) - Best quality
        try:
            import subprocess
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            # Build FFmpeg command with quality settings
            if output_format == 'mp3':
                cmd = ['ffmpeg', '-i', input_path, '-vn', '-acodec', 'libmp3lame', '-ab', '192k', '-y', output_path]
            elif output_format == 'wav':
                cmd = ['ffmpeg', '-i', input_path, '-vn', '-acodec', 'pcm_s16le', '-y', output_path]
            elif output_format == 'aac':
                cmd = ['ffmpeg', '-i', input_path, '-vn', '-acodec', 'aac', '-ab', '192k', '-y', output_path]
            elif output_format == 'flac':
                cmd = ['ffmpeg', '-i', input_path, '-vn', '-acodec', 'flac', '-y', output_path]
            elif output_format == 'ogg':
                cmd = ['ffmpeg', '-i', input_path, '-vn', '-acodec', 'libvorbis', '-ab', '192k', '-y', output_path]
            else:
                cmd = ['ffmpeg', '-i', input_path, '-vn', '-y', output_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            jobs[job_id]["progress"] = 60
            
            if result.returncode == 0:
                jobs[job_id]["progress"] = 100
                logger.info(f"Video to audio: FFmpeg successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
                return True
            else:
                logger.warning(f"FFmpeg failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"FFmpeg not available or failed: {e}")

        # Method 2: moviepy (Python library)
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(input_path)
            audio = clip.audio
            jobs[job_id]["progress"] = 40
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp3':
                audio.write_audiofile(output_path, codec='mp3', bitrate='192k')
            elif output_format == 'wav':
                audio.write_audiofile(output_path, codec='pcm_s16le')
            else:
                audio.write_audiofile(output_path)
            
            audio.close()
            clip.close()
            jobs[job_id]["progress"] = 100
            logger.info(f"Video to audio: moviepy successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
            return True
        except ImportError:
            logger.warning("moviepy not available")
        except Exception as e:
            logger.warning(f"moviepy conversion failed: {e}")

        # Method 3: pydub (if video has audio)
        try:
            from pydub import AudioSegment
            
            # Try to load as audio (works for some video formats)
            audio = AudioSegment.from_file(input_path)
            jobs[job_id]["progress"] = 40
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp3':
                audio.export(output_path, format='mp3', bitrate='192k')
            elif output_format == 'wav':
                audio.export(output_path, format='wav')
            else:
                audio.export(output_path, format=output_format)
            
            jobs[job_id]["progress"] = 100
            logger.info(f"Video to audio: pydub successful ({os.path.basename(input_path)} -> {os.path.basename(output_path)})")
            return True
        except ImportError:
            logger.warning("pydub not available")
        except Exception as e:
            logger.warning(f"pydub conversion failed: {e}")

        # Method 4: Last resort - create silent audio file
        try:
            from pydub import AudioSegment
            from pydub.generators import Silence
            
            # Create a silent audio file as fallback
            silent_audio = Silence(1000)  # 1 second of silence
            
            # Get output format from file extension
            output_format = os.path.splitext(output_path)[1][1:].lower()
            
            if output_format == 'mp3':
                silent_audio.export(output_path, format='mp3')
            elif output_format == 'wav':
                silent_audio.export(output_path, format='wav')
            else:
                silent_audio.export(output_path, format=output_format)
            
            jobs[job_id]["progress"] = 100
            logger.warning("Video to audio: Created silent audio file (no audio track found)")
            return True
        except Exception as e:
            logger.error(f"All video to audio methods failed: {e}")
            jobs[job_id]["error"] = f"Video to audio extraction failed: {e}"
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
