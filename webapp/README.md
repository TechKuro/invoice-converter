# PDF Invoice Converter - Web Application

A modern Flask-based web application for processing PDF invoices with user authentication, database storage, and a beautiful interface.

## Features

- **User Authentication**: Secure login/registration system
- **File Upload**: Drag-and-drop interface for PDF uploads
- **Real-time Processing**: Track processing status with live updates
- **Database Storage**: Store extracted data with full history
- **Dashboard**: View statistics and recent processing sessions
- **Excel Export**: Download comprehensive results in Excel format
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

1. **Install Dependencies**:
   ```bash
   cd webapp
   pip install -r ../requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python run_webapp.py
   ```

3. **Access the Application**:
   - Open your browser to `http://localhost:5000`
   - Default login: `admin` / `admin123`

## Project Structure

```
webapp/
├── app.py                 # Main Flask application
├── run_webapp.py         # Simple run script
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # User dashboard
│   ├── upload.html       # File upload page
│   └── session_detail.html # Processing session details
├── static/               # Static files (CSS, JS, images)
│   ├── css/             
│   └── js/              
└── uploads/              # User uploaded files (auto-created)
```

## Database

The application uses SQLite by default (`pdf_converter.db`) with the following models:

- **User**: User accounts with authentication
- **UploadSession**: File upload/processing sessions
- **ProcessedFile**: Individual PDF files and their status
- **InvoiceData**: Extracted invoice information
- **LineItem**: Individual line items from invoices

## API Endpoints

- `POST /api/process/<session_id>` - Start processing an upload session
- All other endpoints are web pages with forms

## Environment Variables

- `SECRET_KEY` - Flask secret key (defaults to dev key)
- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `FLASK_ENV` - Flask environment (development/production)

## Development

To modify the application:

1. **Frontend**: Edit templates in `templates/` and static files in `static/`
2. **Backend**: Modify `app.py` for routes, models, and business logic
3. **Database**: Models are defined in `app.py` using SQLAlchemy

## Deployment

For production deployment:

1. Set a secure `SECRET_KEY` environment variable
2. Use a production database (PostgreSQL recommended)
3. Set `FLASK_ENV=production`
4. Use a proper WSGI server like Gunicorn
5. Configure reverse proxy (nginx recommended)

## Integration with CLI Tool

The web application reuses the existing `pdf_to_excel_converter.py` module for PDF processing, ensuring consistency between the CLI and web versions. 