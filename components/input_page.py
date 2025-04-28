import streamlit as st
import os

# Import utilities
from utils.template_manager import (
    get_template_list, 
    get_template_content, 
    display_template_preview,
    save_new_template
)
from utils.document_processing import extract_text_from_uploaded_file
from utils.web_tools import scrape_webpage, search_for_template_by_name

def render_input_page():
    """Render the input page."""
    st.write("Generate custom documents based on templates and various knowledge sources")
    
    # 1. User query
    st.header("1. Enter Your Document Requirements")
    user_query = st.text_area(
        "Describe what you need (e.g., 'Create a customer response letter about a delayed shipment')", 
        height=100
    )
    
    # 2. Knowledge source selection
    st.header("2. Select Knowledge Source")
    knowledge_source = st.radio(
        "Choose your knowledge source",
        ["Upload Document", "Search the Web", "Specific URL"]
    )
    
    knowledge_data = None
    
    if knowledge_source == "Upload Document":
        uploaded_file = st.file_uploader("Upload a document (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
        if uploaded_file:
            st.info(f"Processing {uploaded_file.name}...")
            knowledge_data = extract_text_from_uploaded_file(uploaded_file)
            st.success(f"Successfully extracted content from {uploaded_file.name}")
            with st.expander("Preview Extracted Content"):
                st.write(knowledge_data[:1000] + "..." if len(knowledge_data) > 1000 else knowledge_data)
    
    elif knowledge_source == "Search the Web":
        st.info("The system will search the web for relevant information based on your query.")
        
    elif knowledge_source == "Specific URL":
        specific_url = st.text_input("Enter the URL of the webpage to use as a knowledge source")
        if specific_url and st.button("Fetch Content"):
            st.info(f"Fetching content from {specific_url}...")
            knowledge_data = scrape_webpage(specific_url)
            st.success("Content fetched successfully!")
            with st.expander("Preview Extracted Content"):
                st.write(knowledge_data[:1000] + "..." if len(knowledge_data) > 1000 else knowledge_data)
    
    # 3. Template selection
    st.header("3. Select Template")
    
    template_option = st.radio(
        "Choose template option",
        ["Use Predefined Template", "Search for Template", "Upload Custom Template"]
    )
    
    template_text = None
    
    if template_option == "Use Predefined Template":
        # Get list of template names from file system
        templates = get_template_list()
        template_options = list(templates.keys())
        
        selected_template = st.selectbox(
            "Choose a predefined template",
            template_options
        )
        
        template_text = get_template_content(selected_template)
        with st.expander("Preview Template"):
            st.write(display_template_preview(template_text), unsafe_allow_html=True)
    
    elif template_option == "Search for Template":
        # Fixed alignment issue with template search
        col1, col2 = st.columns([3, 1])
        with col1:
            template_search = st.text_input("Enter template name (e.g., 'sales proposal', 'technical report')")
        with col2:
            st.write("")  # Add spacing for alignment
            search_button = st.button("Search Template", key="search_template_button")
        
        if template_search and search_button:
            with st.spinner(f"Searching for {template_search} template..."):
                found_template = search_for_template_by_name(template_search)
                if found_template:
                    template_text = found_template
                    st.session_state.found_template = found_template  # Save to session state
                    
                    # Save the new template to the filesystem for future use
                    template_name = save_new_template(
                        template_search, 
                        found_template,
                        description=f"Template for {template_search}",
                        category="searched",
                        source="web_search"
                    )
                    
                    st.success(f"Template for '{template_search}' found and saved for future use!")
                    with st.expander("Preview Template"):
                        st.write(display_template_preview(template_text), unsafe_allow_html=True)
                else:
                    st.error(f"Could not find a template for '{template_search}'. Please try a different term or use an existing template.")
        
        # Check if we have a previously found template in the session state
        if not template_text and 'found_template' in st.session_state:
            template_text = st.session_state.found_template
            with st.expander("Preview Template"):
                st.write(display_template_preview(template_text), unsafe_allow_html=True)
    
    elif template_option == "Upload Custom Template":
        uploaded_template = st.file_uploader("Upload a Jinja2 template file", type=["txt", "j2", "jinja", "html", "md"])
        if uploaded_template:
            template_text = uploaded_template.getvalue().decode("utf-8")
            st.session_state.uploaded_template = template_text  # Save to session state
            
            # Option to save the uploaded template for future use
            save_option = st.checkbox("Save this template for future use")
            if save_option:
                template_name = st.text_input("Enter a name for this template")
                if template_name and st.button("Save Template"):
                    save_new_template(
                        template_name, 
                        template_text,
                        description=f"User uploaded template: {template_name}",
                        category="uploaded",
                        source="user_upload"
                    )
                    st.success(f"Template '{template_name}' saved successfully!")
            
            st.success("Custom template uploaded successfully!")
            with st.expander("Preview Template"):
                st.write(display_template_preview(template_text), unsafe_allow_html=True)
        elif 'uploaded_template' in st.session_state:
            template_text = st.session_state.uploaded_template
            with st.expander("Preview Template"):
                st.write(display_template_preview(template_text), unsafe_allow_html=True)
    
    # Continue button
    continue_button = st.button("Continue to Verification", key="continue_button")
    if continue_button:
        if not user_query:
            st.error("Please enter your document requirements.")
        elif not template_text and template_option == "Upload Custom Template":
            st.error("Please upload a template.")
        elif not template_text and template_option == "Search for Template" and 'found_template' not in st.session_state:
            st.error("Please search for a template first.")
        elif not template_text:
            st.error("Please select or upload a template.")
        else:
            # For search template option, use the found template if available
            if template_option == "Search for Template" and not template_text and 'found_template' in st.session_state:
                template_text = st.session_state.found_template
            
            # Save data to session state
            st.session_state.user_query = user_query
            st.session_state.template_text = template_text
            st.session_state.knowledge_source = knowledge_source
            st.session_state.knowledge_data = knowledge_data
            
            # Proceed to verification page
            st.session_state.page = 'verify'
            st.rerun()