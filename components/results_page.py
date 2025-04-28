import streamlit as st
import time

# Import utilities
from utils.document_processing import (
    markdown_to_html, 
    html_to_docx
)
from utils.pdf_tools import (
    markdown_to_pdf_weasyprint,
    markdown_to_html_with_toc
)

def render_results_page():
    """Render the results page."""
    st.header("Generated Document")
    
    # Display generation method used
    if 'generation_method' in st.session_state:
        method_used = st.session_state.generation_method
        st.info(f"Document generated using: {method_used}")
    
    # Display the generated document in a stylish way
    if 'generation_method' in st.session_state and st.session_state.generation_method == "RAG (Retrieval-Augmented Generation)":
        # Use the version with Table of Contents for RAG
        html_doc = markdown_to_html_with_toc(st.session_state.generated_document)
    else:
        # Use standard HTML for regular generation
        html_doc = markdown_to_html(st.session_state.generated_document)
        
    st.components.v1.html(html_doc, height=600, scrolling=True)
    
    # Download options
    st.subheader("Download Options")
    
    # Create columns for the download section
    col1, col2 = st.columns([1, 1])
    
    with col1:
        doc_format = st.radio("Select format", ["PDF", "DOCX", "Markdown"])
    
    with col2:
        # Download button based on selected format
        if doc_format == "PDF":
            # Use improved PDF generation
            pdf_content = markdown_to_pdf_weasyprint(st.session_state.generated_document)
            
            if pdf_content:
                st.download_button(
                    label="Download Document",
                    data=pdf_content,
                    file_name=f"generated_document_{int(time.time())}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )
            else:
                st.error("Error generating PDF. Please try another format.")
        elif doc_format == "DOCX":
            # Convert markdown to HTML, then to DOCX
            html_content = markdown_to_html(st.session_state.generated_document)
            docx_content = html_to_docx(html_content)
            
            if docx_content:
                st.download_button(
                    label="Download Document",
                    data=docx_content,
                    file_name=f"generated_document_{int(time.time())}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_docx"
                )
        else:  # Markdown
            st.download_button(
                label="Download Document",
                data=st.session_state.generated_document,
                file_name=f"generated_document_{int(time.time())}.md",
                mime="text/markdown",
                key="download_md"
            )
    
    # Show document metadata
    with st.expander("Document Metadata"):
        if 'content_variables' in st.session_state and st.session_state.content_variables:
            st.write("Template Variables Used:")
            for var, value in st.session_state.content_variables.items():
                st.write(f"**{var}:** {value[:100]}..." if len(str(value)) > 100 else f"**{var}:** {value}")
    
    # Show sources if applicable
    if st.session_state.knowledge_source == "Search the Web" and st.session_state.search_results:
        with st.expander("View Sources"):
            for i, result in enumerate(st.session_state.search_results):
                st.write(f"**Source {i+1}:** [{result['title']}]({result['link']})")
                st.write(result['snippet'])
    
    # Feedback mechanism
    st.header("Document Feedback")
    satisfaction = st.slider("How satisfied are you with this document? (1-5)", 1, 5, 3)
    feedback = st.text_area("Provide specific feedback for improvement:")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! It will help improve future document generation.")