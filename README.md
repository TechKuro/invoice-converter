# PDF Invoice Converter - Streamlit Desktop App

A powerful **Streamlit-based desktop application** for extracting data from PDF invoices and exporting to Excel. Features a modern interface with user authentication, database storage, and comprehensive data extraction capabilities.

## 🚀 Quick Start

**1. Launch the Application:**
```bash
# Super Simple (recommended)
python launch_app.py

# Windows Batch File
run_desktop_app.bat

# Manual Launch
cd desktop_app
python run_app.py
```

**2. Access the App:**
- Opens automatically in your browser at `http://localhost:8501`
- **Default login:** `admin` / `admin123`

**3. Start Processing:**
- Upload your PDF invoices using the drag-and-drop interface
- Watch real-time processing progress
- Download comprehensive Excel results

## ✨ Features

### 🖥️ **Modern Desktop Interface**
- **Streamlit-powered** - Beautiful, responsive web interface running locally
- **User Authentication** - Secure login system with user accounts
- **Dashboard** - Overview of processing statistics and recent sessions
- **Real-time Progress** - Live updates during PDF processing
- **Session History** - Track all your processing sessions with detailed results

### 📊 **Advanced PDF Processing**
- **Smart Line Item Detection** - AI-powered extraction of individual invoice items
- **Table Recognition** - Automatically detects and extracts tabular data
- **Invoice Data Parsing** - Extracts invoice numbers, dates, vendors, totals
- **Multi-format Support** - Works with various PDF invoice layouts
- **Error Handling** - Graceful handling of corrupted or problematic PDFs

### 📈 **Comprehensive Excel Export**
- **Multiple Sheets**: Summary, Line Items, Text Data, Tables
- **Structured Data**: Individual line items with descriptions, quantities, prices
- **Invoice Metadata**: Extracted invoice fields (number, date, vendor, total)
- **Source Tracking**: Know which table/method extracted each data point

### 🔧 **Additional Tools**

**Command Line Processing** (for bulk operations):
```bash
# Windows
run_converter.bat

# Or run directly  
python pdf_to_excel_converter.py --input-dir ./pdfs --output-file results.xlsx
```

## 📁 Project Structure

```
pdf_invoice_converter/
├── desktop_app/              # Streamlit desktop application
│   ├── main.py              # Main Streamlit app
│   ├── database.py          # Database operations
│   ├── auth.py              # User authentication
│   └── run_app.py           # Launch script
├── pdf_to_excel_converter.py # Core PDF processing engine
├── requirements.txt          # Dependencies
├── run_desktop_app.bat      # Windows launcher for desktop app
└── run_converter.bat        # Windows launcher for CLI tool
```

## 🔧 Installation

**Prerequisites:**
- Python 3.7+ installed and added to PATH
- Windows (batch files) or run Python scripts directly on other platforms

**Auto-Installation:**
- Dependencies install automatically when you first run the app
- Or manually install: `pip install -r requirements.txt`

## 📝 Usage Examples

### Desktop App Usage
1. **Launch**: Double-click `run_desktop_app.bat`
2. **Login**: Use `admin` / `admin123` or create your own account
3. **Upload**: Drag and drop PDF files or use the file browser
4. **Process**: Watch real-time progress as files are processed
5. **Download**: Get your Excel file with comprehensive extracted data

### Command Line Usage
```bash
# Process all PDFs in a directory
python pdf_to_excel_converter.py --input-dir ./invoices --output-file invoice_data.xlsx --verbose

# Quick processing with default settings
python pdf_to_excel_converter.py
```

## 💾 Database Storage

The desktop app uses SQLite to store:
- **User accounts** and authentication
- **Processing sessions** with full history
- **Extracted data** for future reference
- **File metadata** and processing statistics

Database file: `desktop_app/pdf_converter.db`

## 🔐 Database Encryption (NEW!)

Your sensitive data is protected with **AES-256 encryption**:

**Setup Encryption:**
```bash
python setup_encryption.py
```

**Features:**
- ✅ **Complete database encryption** - All invoice data, line items, and user info
- ✅ **Automatic migration** - Existing data is safely converted
- ✅ **Transparent operation** - No changes to your workflow
- ✅ **Strong security** - Military-grade AES-256 encryption

**Important:** 
- Backup your encryption key (`desktop_app/.db_key`) immediately
- Without the key, your data cannot be recovered
- See [ENCRYPTION_SETUP.md](ENCRYPTION_SETUP.md) for detailed instructions

## 🎯 Output Structure

### Excel Export Sheets:
1. **Summary** - Overview of all processed files
2. **Line Items** - Individual invoice items with quantities/prices
3. **Text Data** - Extracted invoice metadata and full text
4. **Tables** - All detected tables with original structure

### Data Fields Extracted:
- Invoice numbers, dates, vendors, totals
- Line item descriptions, quantities, unit prices, amounts
- VAT/tax information
- Table structures and free-form text

## 🔍 Supported PDF Types

**Best Results:**
- Text-based PDFs (not scanned images)
- Standard invoice formats
- Business documents with tabular data

**Note:** For scanned PDFs, consider adding OCR preprocessing

## 🛠️ Troubleshooting

**Common Issues:**

1. **Port already in use**: Close other Streamlit apps or change port in `run_app.py`
2. **No PDFs detected**: Ensure files have `.pdf` extension and are readable
3. **Permission errors**: Run as administrator or check file permissions
4. **Memory issues**: Process large PDFs in smaller batches

**Logs:**
- Desktop app: Check Streamlit terminal output
- CLI tool: See `pdf_converter.log` for detailed processing information

## 🔄 Command Line Arguments

```bash
python pdf_to_excel_converter.py [options]

Options:
  --input-dir, -i     Directory containing PDF files (default: ./pdfs)
  --output-file, -o   Output Excel file path (default: ./extracted_data.xlsx)
  --extract-tables    Extract tables from PDFs (default: True)
  --extract-text      Extract text from PDFs (default: True)
  --verbose, -v       Enable verbose logging
```

## 🎨 Customization

**Desktop App:**
- Modify UI in `desktop_app/main.py`
- Update database schema in `desktop_app/database.py`
- Customize authentication in `desktop_app/auth.py`

**Processing Engine:**
- Add extraction patterns in `pdf_to_excel_converter.py`
- Modify Excel formatting in the `ExcelExporter` class
- Extend data validation and cleaning logic

## 📄 License

This application is provided for educational and commercial use.

---

## 🆘 Quick Help

**Need to process PDFs quickly?** Use the **desktop app** for an intuitive interface with progress tracking and session history.

**Need bulk processing?** Use the **command line tool** for maximum control and automation.

**Default credentials**: `admin` / `admin123`

**Having issues?** Check the terminal output for error messages and consult the troubleshooting section above. 