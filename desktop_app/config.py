# --- Application Configuration ---
APP_VERSION = "2.1.0-refactored"
APP_TITLE = "PDF Invoice Converter"
PAGE_ICON = "📄"

# --- Database Configuration ---
DATABASE_NAME = "pdf_converter.db"

# --- Page Configuration ---
PAGES = {
    "Dashboard": {
        "icon": "📊",
        "title": "Dashboard",
        "func": "show_dashboard"
    },
    "Upload PDFs": {
        "icon": "📤",
        "title": "Upload and Process PDFs",
        "func": "show_upload_page"
    },
    "My Sessions": {
        "icon": "📁",
        "title": "My Processing Sessions",
        "func": "show_sessions_page"
    },
    "Settings": {
        "icon": "⚙️",
        "title": "Settings",
        "func": "show_settings_page"
    }
} 