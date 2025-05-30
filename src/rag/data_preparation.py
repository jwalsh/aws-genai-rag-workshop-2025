# Data preparation utilities for RAG
import os
import json
import boto3
import requests
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
import pandas as pd


class DataPreparation:
    """Utilities for preparing data for RAG ingestion"""
    
    def __init__(self, s3_client=None):
        self.s3_client = s3_client or boto3.client('s3')
        
    def download_and_prepare_science_papers(self, 
                                          output_dir: str,
                                          paper_urls: List[str]) -> str:
        """Download scientific papers and prepare for ingestion"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, url in enumerate(paper_urls):
            response = requests.get(url)
            if response.status_code == 200:
                file_path = output_path / f"paper_{i+1}.pdf"
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Generate metadata
                metadata = {
                    "source": url,
                    "type": "scientific_paper",
                    "index": i + 1
                }
                
                metadata_path = output_path / f"paper_{i+1}.pdf.metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
        
        return str(output_path)
    
    def download_and_prepare_10k_reports(self,
                                       output_dir: str,
                                       bucket_name: str = None,
                                       region_name: str = "us-west-2") -> str:
        """Download Amazon 10-K reports, prepare metadata, and optionally upload to S3"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Define URLs of Amazon's 10-K reports to be downloaded as example documents
        urls = [
            "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/e42c2068-bad5-4ab6-ae57-36ff8b2aeffd.pdf",
            "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/c7c14359-36fa-40c3-b3ca-5bf7f3fa0b96.pdf",
            "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/d2fde7ee-05f7-419d-9ce8-186de4c96e25.pdf"
        ]
        
        years = ["2023", "2022", "2021"]
        
        for i, (url, year) in enumerate(zip(urls, years)):
            try:
                # Download the PDF
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    file_path = output_path / f"Amazon_10K_{year}.pdf"
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Generate metadata
                    metadata = {
                        "company": "Amazon.com Inc.",
                        "cik": "0001018724",
                        "year": year,
                        "document_type": "10-K",
                        "source": url,
                        "filing_date": f"{year}-02-03",  # Approximate filing dates
                        "index": i + 1
                    }
                    
                    metadata_path = output_path / f"Amazon_10K_{year}.pdf.metadata.json"
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    print(f"Downloaded Amazon 10-K report for {year}")
                else:
                    print(f"Failed to download {year} report: HTTP {response.status_code}")
            except Exception as e:
                print(f"Error downloading {year} report: {str(e)}")
        
        # Optionally upload to S3
        if bucket_name:
            self.upload_directory_to_s3(str(output_path), bucket_name, "10k-reports")
            print(f"Uploaded reports to S3 bucket: {bucket_name}")
        
        return str(output_path)
    
    def prepare_csv_data(self,
                        csv_path: str,
                        output_dir: str,
                        text_columns: List[str],
                        metadata_columns: List[str] = None) -> str:
        """Convert CSV data to documents with metadata"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        df = pd.read_csv(csv_path)
        
        for idx, row in df.iterrows():
            # Combine text columns
            text_content = "\n".join([
                f"{col}: {row[col]}" for col in text_columns 
                if col in df.columns and pd.notna(row[col])
            ])
            
            # Create document
            doc_path = output_path / f"document_{idx}.txt"
            with open(doc_path, 'w') as f:
                f.write(text_content)
            
            # Create metadata
            metadata = {"index": idx, "source": csv_path}
            if metadata_columns:
                for col in metadata_columns:
                    if col in df.columns:
                        metadata[col] = str(row[col])
            
            metadata_path = output_path / f"document_{idx}.txt.metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        return str(output_path)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    
    def upload_directory_to_s3(self,
                             local_directory: str,
                             bucket_name: str,
                             s3_prefix: str = "") -> List[str]:
        """Upload directory contents to S3"""
        uploaded_files = []
        local_path = Path(local_directory)
        
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}" if s3_prefix else str(relative_path)
                
                self.s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key
                )
                uploaded_files.append(s3_key)
        
        return uploaded_files
    
    def generate_json_metadata(self,
                             content: str,
                             metadata: Dict[str, Any],
                             output_path: str):
        """Generate JSON metadata file for a document"""
        metadata_path = Path(output_path)
        
        # Ensure metadata includes basic fields
        full_metadata = {
            "content_length": len(content),
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            **metadata
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2)