import streamlit as st

def load_css(file_path):
    """Load a CSS file and inject it into the Streamlit app."""
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def check_authentication():
    """Check if user is authenticated"""
    return 'user_id' in st.session_state and 'username' in st.session_state

def format_status(status):
    """Format status with color"""
    if status == 'completed':
        return f'<span class="status-success">{status.capitalize()}</span>'
    elif status == 'processing':
        return f'<span class="status-processing">{status.capitalize()}</span>'
    elif status == 'failed':
        return f'<span class="status-failed">{status.capitalize()}</span>'
    else:
        return f'<span class="status-pending">{status.capitalize()}</span>' 