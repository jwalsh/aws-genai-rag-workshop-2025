"""PDF text extraction utilities."""

import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files for RAG processing."""
    
    def __init__(self):
        self.pypdf2_available = False
        self.pdfplumber_available = False
        
        # Try to import PDF libraries
        try:
            import PyPDF2
            self.pypdf2_available = True
            self.PyPDF2 = PyPDF2
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
        
        try:
            import pdfplumber
            self.pdfplumber_available = True
            self.pdfplumber = pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")
    
    def extract_text(self, pdf_path: str, max_pages: Optional[int] = None) -> str:
        """Extract text from PDF file."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Try pdfplumber first (better extraction)
        if self.pdfplumber_available:
            return self._extract_with_pdfplumber(pdf_path, max_pages)
        
        # Fall back to PyPDF2
        if self.pypdf2_available:
            return self._extract_with_pypdf2(pdf_path, max_pages)
        
        raise ImportError("No PDF extraction library available. Install PyPDF2 or pdfplumber.")
    
    def _extract_with_pypdf2(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using PyPDF2."""
        text_content = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = self.PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            if max_pages:
                num_pages = min(num_pages, max_pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return "\n\n".join(text_content)
    
    def _extract_with_pdfplumber(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using pdfplumber."""
        text_content = []
        
        with self.pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            
            if max_pages:
                num_pages = min(num_pages, max_pages)
            
            for page_num in range(num_pages):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return "\n\n".join(text_content)
    
    def extract_pages(self, pdf_path: str, start_page: int = 0, 
                      end_page: Optional[int] = None) -> List[str]:
        """Extract specific pages from PDF."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pages = []
        
        if self.pypdf2_available:
            with open(pdf_path, 'rb') as file:
                pdf_reader = self.PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                if end_page is None:
                    end_page = total_pages
                else:
                    end_page = min(end_page, total_pages)
                
                for page_num in range(start_page, end_page):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    pages.append(text)
        else:
            raise ImportError("PyPDF2 required for page extraction")
        
        return pages
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if self.pypdf2_available:
            with open(pdf_path, 'rb') as file:
                pdf_reader = self.PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        
        if self.pdfplumber_available:
            with self.pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        
        raise ImportError("No PDF library available")


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.pdf_extractor <pdf_file> [max_pages]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    extractor = PDFExtractor()
    try:
        text = extractor.extract_text(pdf_file, max_pages)
        print(f"Extracted {len(text)} characters")
        print("\nFirst 500 characters:")
        print(text[:500])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)