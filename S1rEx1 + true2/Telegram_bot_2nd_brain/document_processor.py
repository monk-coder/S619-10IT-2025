"""
Document processing utilities for PDF and image extraction
"""
import os
import logging
import io
from typing import Optional, Tuple
from PIL import Image
import pytesseract
import PyPDF2
from config import config

logger = logging.getLogger(__name__)

# Configure Tesseract if path is specified
if config.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd


class DocumentProcessor:
    """Process various document types"""
    
    @staticmethod
    async def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF file content as bytes
        
        Returns:
            Tuple of (extracted_text, page_count)
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num}: {e}")
                    text_content.append(f"--- Page {page_num} ---\n[Could not extract text]")
            
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                return "No text could be extracted from the PDF. It may contain only images.", page_count
            
            return full_text, page_count
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    @staticmethod
    async def extract_text_from_image(image_bytes: bytes) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image_bytes: Image file content as bytes
        
        Returns:
            Extracted text from the image
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(image, lang='eng+rus')
            
            if not extracted_text.strip():
                return "No text could be extracted from the image."
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            
            # Check if Tesseract is installed
            if "tesseract is not installed" in str(e).lower():
                return ("OCR is not available. Please install Tesseract OCR to extract text from images.\n"
                       "Linux/Mac: apt-get install tesseract-ocr\n"
                       "Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            
            raise Exception(f"Failed to process image: {str(e)}")
    
    @staticmethod
    def summarize_document(text: str, max_length: int = 1000) -> str:
        """
        Create a summary of document text
        
        Args:
            text: Document text to summarize
            max_length: Maximum length of summary
        
        Returns:
            Summary of the document
        """
        if len(text) <= max_length:
            return text
        
        # Simple truncation with word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    @staticmethod
    def extract_key_points(text: str, max_points: int = 10) -> list:
        """
        Extract key points from document text
        
        Args:
            text: Document text
            max_points: Maximum number of key points
        
        Returns:
            List of key points
        """
        # Simple extraction based on paragraphs and sentences
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 30:  # Skip very short lines
                # Look for lines that might be headers or important points
                if any(char in line for char in ['•', '●', '○', '■', '□', '-', '*']) or \
                   line[0].isupper() or \
                   any(word in line.lower() for word in ['important', 'key', 'note', 'summary']):
                    key_points.append(line[:200])  # Limit length of each point
                    if len(key_points) >= max_points:
                        break
        
        return key_points if key_points else ["No clear key points could be extracted."]
    
    @staticmethod
    async def process_file(file_bytes: bytes, file_type: str) -> dict:
        """
        Process a file and extract information
        
        Args:
            file_bytes: File content as bytes
            file_type: Type of file ('pdf', 'image')
        
        Returns:
            Dictionary with extracted information
        """
        result = {
            'success': False,
            'text': '',
            'summary': '',
            'key_points': [],
            'metadata': {}
        }
        
        try:
            if file_type == 'pdf':
                text, page_count = await DocumentProcessor.extract_text_from_pdf(file_bytes)
                result['metadata']['page_count'] = page_count
                result['metadata']['type'] = 'PDF'
            elif file_type in ['image', 'photo']:
                text = await DocumentProcessor.extract_text_from_image(file_bytes)
                result['metadata']['type'] = 'Image'
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            result['text'] = text
            result['summary'] = DocumentProcessor.summarize_document(text, max_length=500)
            result['key_points'] = DocumentProcessor.extract_key_points(text, max_points=5)
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            result['error'] = str(e)
        
        return result
