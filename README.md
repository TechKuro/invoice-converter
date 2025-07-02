# PDF to Excel Converter

A Python script that extracts data from multiple PDF files and exports the results to an Excel spreadsheet. The script supports text extraction, table detection, and structured data parsing (especially useful for invoices).

## Features

- **Multiple PDF Processing**: Process all PDFs in a directory at once
- **Text Extraction**: Extract all text content from PDFs
- **Table Detection**: Automatically detect and extract tables from PDFs
- **Invoice Data Parsing**: Special regex patterns to extract common invoice fields (invoice number, date, vendor, total amount)
- **Line Item Extraction**: Intelligently extracts individual line items (product/service names and amounts) from tables
- **Excel Export**: Creates a comprehensive Excel file with multiple sheets:
  - **Summary**: Overview of all processed files
  - **Line Items**: Individual line items with descriptions, amounts, quantities, and prices
  - **Text Data**: Extracted text and parsed invoice fields
  - **Tables**: All detected tables from PDFs
- **Error Handling**: Graceful handling of corrupted or problematic PDFs
- **Logging**: Detailed logging of the extraction process

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python pdf_to_excel_converter.py --input-dir ./pdfs --output-file results.xlsx
```

### Advanced Usage
```bash
# Process PDFs with verbose logging
python pdf_to_excel_converter.py --input-dir ./invoices --output-file invoice_data.xlsx --verbose

# Extract only text (no tables)
python pdf_to_excel_converter.py --input-dir ./documents --output-file text_only.xlsx --extract-text

# Extract only tables (no text)
python pdf_to_excel_converter.py --input-dir ./reports --output-file tables_only.xlsx --extract-tables
```

### Command Line Arguments

- `--input-dir, -i`: Directory containing PDF files (default: `./pdfs`)
- `--output-file, -o`: Output Excel file path (default: `./extracted_data.xlsx`)
- `--extract-tables`: Extract tables from PDFs (default: True)
- `--extract-text`: Extract text from PDFs (default: True)
- `--verbose, -v`: Enable verbose logging

## Setup Instructions

1. **Create a directory for your PDFs**:
```bash
mkdir pdfs
# Copy your PDF files into this directory
```

2. **Run the script**:
```bash
python pdf_to_excel_converter.py
```

3. **Check the output**:
   - The Excel file will be created as `extracted_data.xlsx` (or your specified filename)
   - A log file `pdf_converter.log` will be created with detailed processing information

## Output Structure

The generated Excel file contains four sheets:

### 1. Summary Sheet
- Filename
- Number of pages
- Number of tables found
- Number of line items found
- Whether text was extracted
- File size
- Processing status

### 2. Line Items Sheet (NEW!)
- Filename and source page
- Item description/name
- Amount/price
- Quantity (if available)
- Unit price (if available)
- Source of extraction (table or text parsing)

### 3. Text Data Sheet
- Filename
- Extracted invoice data (if applicable):
  - Invoice Number
  - Date
  - Vendor
  - Total Amount
- Full extracted text (truncated for readability)

### 4. Tables Sheet
- All tables found in the PDFs
- Organized by file, page, and table number
- Preserves original table structure

## Supported PDF Types

The script works best with:
- Text-based PDFs (not scanned images)
- Invoices and business documents
- Reports with tabular data
- Any PDF with extractable text content

**Note**: For scanned PDFs (images), you would need OCR capabilities. This script focuses on text-based PDFs.

## Troubleshooting

### Common Issues

1. **Missing dependencies**: 
   ```bash
   pip install pandas pdfplumber openpyxl
   ```

2. **No PDFs found**: 
   - Ensure PDFs are in the correct directory
   - Check file extensions (.pdf or .PDF)

3. **Permission errors**:
   - Ensure you have read permissions for PDF files
   - Ensure you have write permissions for the output directory

4. **Memory issues with large PDFs**:
   - Process PDFs in smaller batches
   - Use the `--verbose` flag to monitor progress

### Log Files

Check `pdf_converter.log` for detailed information about:
- Which files were processed successfully
- Any errors encountered
- Processing times and statistics

## Examples

### Example 1: Processing Invoice PDFs
```bash
# Put all invoice PDFs in a folder called 'invoices'
mkdir invoices
# Copy your invoice PDFs here

# Run the converter
python pdf_to_excel_converter.py --input-dir ./invoices --output-file invoice_data.xlsx --verbose
```

### Example 2: Processing Report PDFs (Tables Only)
```bash
python pdf_to_excel_converter.py --input-dir ./reports --output-file report_tables.xlsx --extract-tables --verbose
```

## Customization

The script can be easily customized:

1. **Add new regex patterns** in the `extract_invoice_data` method for different document types
2. **Modify Excel formatting** in the `ExcelExporter` class methods
3. **Add new extraction methods** in the `PDFDataExtractor` class

## License

This script is provided as-is for educational and commercial use. 