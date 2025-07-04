#!/usr/bin/env python3
"""
Simplified PDF to Excel Converter for Streamlit App
===================================================

Essential PDF processing functionality for the desktop application.
"""

import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Third-party imports
try:
    import pandas as pd
    import pdfplumber
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install required packages: pip install pandas pdfplumber openpyxl")
    sys.exit(1)


class PDFDataExtractor:
    """Handles extraction of data from PDF files."""
    
    def __init__(self, extract_tables: bool = True, extract_text: bool = True):
        self.extract_tables = extract_tables
        self.extract_text = extract_text
        self.logger = logging.getLogger(__name__)
    
    def extract_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract data from a single PDF file."""
        data = {
            'filename': pdf_path.name,
            'text': '',
            'tables': [],
            'line_items': [],
            'metadata': {'pages': 0}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                data['metadata']['pages'] = len(pdf.pages)
                
                if self.extract_text:
                    text_parts = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    data['text'] = '\n'.join(text_parts)
                
                if self.extract_tables:
                    for page_num, page in enumerate(pdf.pages):
                        tables = page.extract_tables()
                        for i, table in enumerate(tables or []):
                            if table and len(table) > 1:
                                data['tables'].append({
                                    'page': page_num + 1,
                                    'table_number': i + 1,
                                    'data': table
                                })
                
                # Simple line item extraction
                for table_info in data['tables']:
                    table_data = table_info['data']
                    if len(table_data) > 1:
                        for row in table_data[1:]:  # Skip header
                            if row and len(row) > 0 and str(row[0]).strip():
                                item = {
                                    'description': str(row[0]).strip(),
                                    'source': f"table_page_{table_info['page']}"
                                }
                                if len(row) > 1:
                                    item['amount'] = str(row[1]).strip()
                                data['line_items'].append(item)
        
        except Exception as e:
            self.logger.error(f"Error extracting data from {pdf_path}: {str(e)}")
            data['error'] = str(e)
        
        return data
    
    def _extract_line_items_from_tables(self, tables: List[Dict]) -> List[Dict[str, Any]]:
        """Extract line items from detected tables."""
        line_items = []
        
        for table_info in tables:
            table_data = table_info.get('data', [])
            if not table_data or len(table_data) < 2:
                continue
            
            # Try to find header row
            headers = []
            data_start_row = 0
            
            for i, row in enumerate(table_data):
                if row and any(cell and str(cell).strip() for cell in row):
                    row_text = ' '.join(str(cell).strip().lower() for cell in row if cell)
                    if any(keyword in row_text for keyword in ['description', 'item', 'product', 'quantity', 'price', 'amount']):
                        headers = [str(cell).strip() if cell else f'col_{j}' for j, cell in enumerate(row)]
                        data_start_row = i + 1
                        break
            
            # If no clear headers found, use first row as headers
            if not headers and table_data:
                headers = [f'col_{j}' for j in range(len(table_data[0]))]
                data_start_row = 0
            
            # Extract data rows
            for row in table_data[data_start_row:]:
                if row and any(cell and str(cell).strip() for cell in row):
                    # Create line item
                    item = {}
                    for j, cell in enumerate(row):
                        if j < len(headers) and cell:
                            header = headers[j].lower()
                            cell_text = str(cell).strip()
                            
                            # Map common fields
                            if any(keyword in header for keyword in ['desc', 'item', 'product', 'service']):
                                item['description'] = cell_text
                            elif any(keyword in header for keyword in ['qty', 'quantity']):
                                item['quantity'] = self._extract_number(cell_text)
                            elif any(keyword in header for keyword in ['price', 'rate', 'unit']):
                                item['unit_price'] = self._extract_amount(cell_text)
                            elif any(keyword in header for keyword in ['amount', 'total']):
                                item['amount'] = self._extract_amount(cell_text)
                    
                    # Only add if we have a description and at least one numeric field
                    if (item.get('description') and len(item.get('description', '')) > 3 and
                        (item.get('quantity') or item.get('unit_price') or item.get('amount'))):
                        item['source'] = f"table_page_{table_info['page']}"
                        line_items.append(item)
        
        return line_items
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract a number from text."""
        if not text:
            return None
        
        # Remove common non-numeric characters but keep decimal points
        cleaned = re.sub(r'[^\d.,]', '', str(text))
        
        # Handle different decimal formats
        if ',' in cleaned and '.' in cleaned:
            # Assume comma is thousands separator
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned and cleaned.count(',') == 1:
            # Assume comma is decimal separator
            cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract a monetary amount from text."""
        if not text:
            return None
        
        # Remove currency symbols and extract number
        cleaned = re.sub(r'[£$€¥₹]', '', str(text))
        return self._extract_number(cleaned)


class ExcelExporter:
    """Handles export of extracted data to Excel files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_excel(self, all_data: List[Dict[str, Any]], output_file: Path) -> None:
        """Export extracted data to Excel file with multiple sheets."""
        try:
            workbook = Workbook()
            
            # Remove default sheet
            if workbook.worksheets:
                workbook.remove(workbook.active)
            
            # Create sheets
            self.create_summary_sheet(workbook, all_data)
            self.create_line_items_sheet(workbook, all_data)
            self.create_text_data_sheet(workbook, all_data)
            self.create_tables_sheet(workbook, all_data)
            
            # Save workbook
            workbook.save(output_file)
            self.logger.info(f"Excel file saved successfully: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating Excel file: {e}")
            raise
    
    def create_summary_sheet(self, workbook: Workbook, all_data: List[Dict[str, Any]]) -> None:
        """Create summary sheet with file processing overview."""
        ws = workbook.create_sheet("Summary")
        
        # Headers
        headers = ['Filename', 'Status', 'Pages', 'Tables Found', 'Line Items', 'File Size']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Data rows
        for row, data in enumerate(all_data, 2):
            status = "Error" if 'error' in data else "Success"
            file_path = Path(data.get('filepath', ''))
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            values = [
                data['filename'],
                status,
                data.get('metadata', {}).get('pages', 0),
                len(data.get('tables', [])),
                len(data.get('line_items', [])),
                f"{file_size / 1024:.1f} KB"
            ]
            
            for col, value in enumerate(values, 1):
                ws.cell(row=row, column=col, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column if cell.value)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    def create_line_items_sheet(self, workbook: Workbook, all_data: List[Dict[str, Any]]) -> None:
        """Create line items sheet with extracted invoice items."""
        ws = workbook.create_sheet("Line Items")
        
        # Headers
        headers = ['Filename', 'Description', 'Quantity', 'Unit Price', 'Amount', 'Source']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        
        # Data rows
        row = 2
        for data in all_data:
            if 'error' not in data:
                for item in data.get('line_items', []):
                    values = [
                        data['filename'],
                        item.get('description', ''),
                        item.get('quantity', ''),
                        item.get('unit_price', ''),
                        item.get('amount', ''),
                        item.get('source', '')
                    ]
                    
                    for col, value in enumerate(values, 1):
                        ws.cell(row=row, column=col, value=value)
                    
                    row += 1
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column if cell.value)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    def create_text_data_sheet(self, workbook: Workbook, all_data: List[Dict[str, Any]]) -> None:
        """Create text data sheet with extracted text content."""
        ws = workbook.create_sheet("Text Data")
        
        # Headers
        headers = ['Filename', 'Full Text (Preview)']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        
        # Data rows
        for row, data in enumerate(all_data, 2):
            if 'error' not in data:
                text_preview = data.get('text', '')[:500] + '...' if len(data.get('text', '')) > 500 else data.get('text', '')
                
                values = [data['filename'], text_preview]
                
                for col, value in enumerate(values, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    if col == 2:  # Text column
                        cell.alignment = Alignment(wrap_text=True, vertical='top')
        
        # Set column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 80
    
    def create_tables_sheet(self, workbook: Workbook, all_data: List[Dict[str, Any]]) -> None:
        """Create tables sheet with detected table structures."""
        ws = workbook.create_sheet("Tables")
        
        # Headers
        headers = ['Filename', 'Page', 'Table #', 'Rows', 'Columns', 'Table Data (Preview)']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        # Data rows
        row = 2
        for data in all_data:
            if 'error' not in data:
                for table in data.get('tables', []):
                    # Create a preview of the table data
                    table_data = table.get('data', [])
                    preview = []
                    for table_row in table_data[:3]:  # First 3 rows
                        if table_row:
                            row_text = ' | '.join(str(cell)[:20] if cell else '' for cell in table_row[:5])  # First 5 columns
                            preview.append(row_text)
                    
                    values = [
                        data['filename'],
                        table.get('page', ''),
                        table.get('table_number', ''),
                        table.get('rows', ''),
                        table.get('columns', ''),
                        '\n'.join(preview)
                    ]
                    
                    for col, value in enumerate(values, 1):
                        cell = ws.cell(row=row, column=col, value=value)
                        if col == 6:  # Table data column
                            cell.alignment = Alignment(wrap_text=True, vertical='top')
                    
                    row += 1
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column if cell.value)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 60) 