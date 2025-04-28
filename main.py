import streamlit as st
from dotenv import load_dotenv
import os

# Import components
from components.input_page import render_input_page
from components.verify_page import render_verify_page
from components.results_page import render_results_page

# Must be the first Streamlit command
st.set_page_config(layout="wide", page_title="GenAI Document Generation Bot")

# Load environment variables
load_dotenv()

# Configure APIs from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

def sidebar_navigation():
    """Display the sidebar navigation."""
    with st.sidebar:
        st.title("Navigation")
        
        # Add logo or app name at the top
        st.image("https://www.freepnglogos.com/uploads/document-png/document-png-benefits-paperless-processing-docuware-2.png", width=100)
        st.markdown("### GenAI Document Generator")
        
        st.divider()
        
        # Navigation options
        if st.session_state.page == 'input':
            st.markdown("**1. Input Information**", unsafe_allow_html=True)
            st.markdown("2. Verify Settings", unsafe_allow_html=True)
            st.markdown("3. View Results", unsafe_allow_html=True)
        elif st.session_state.page == 'verify':
            st.markdown("1. Input Information", unsafe_allow_html=True)
            st.markdown("**2. Verify Settings**", unsafe_allow_html=True)
            st.markdown("3. View Results", unsafe_allow_html=True)
        elif st.session_state.page == 'results':
            st.markdown("1. Input Information", unsafe_allow_html=True)
            st.markdown("2. Verify Settings", unsafe_allow_html=True)
            st.markdown("**3. View Results**", unsafe_allow_html=True)
            
        st.divider()
        
        # Quick actions based on current page
        if st.session_state.page == 'input':
            if st.button("Help"):
                st.info("""
                **Getting Started:**
                1. Enter your document requirements
                2. Select a knowledge source
                3. Choose a template
                4. Click 'Continue to Verification'
                """)
        elif st.session_state.page == 'verify':
            if st.button("Go Back"):
                st.session_state.page = 'input'
                st.rerun()
        elif st.session_state.page == 'results':
            if st.button("Create New Document"):
                # Reset session state
                st.session_state.user_query = ''
                st.session_state.template_text = None
                st.session_state.knowledge_source = None
                st.session_state.knowledge_data = None
                st.session_state.search_results = None
                st.session_state.scraped_contents = None
                st.session_state.generated_document = None
                st.session_state.content_variables = None
                st.session_state.page = 'input'
                st.rerun()

def main():
    """Main application entry point."""
    # Session state initialization
    if 'page' not in st.session_state:
        st.session_state.page = 'input'
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ''
    if 'template_text' not in st.session_state:
        st.session_state.template_text = None
    if 'knowledge_source' not in st.session_state:
        st.session_state.knowledge_source = None
    if 'knowledge_data' not in st.session_state:
        st.session_state.knowledge_data = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'scraped_contents' not in st.session_state:
        st.session_state.scraped_contents = None
    if 'generated_document' not in st.session_state:
        st.session_state.generated_document = None
    if 'content_variables' not in st.session_state:
        st.session_state.content_variables = None
    
    # Display sidebar navigation
    sidebar_navigation()
    
    # Main content area
    # Title
    st.title("GenAI Document Generation Bot")
    
    # Render the appropriate page based on session state
    if st.session_state.page == 'input':
        render_input_page()
    elif st.session_state.page == 'verify':
        render_verify_page()
    elif st.session_state.page == 'results':
        render_results_page()

if __name__ == "__main__":
    main()