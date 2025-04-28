import streamlit as st

# Import utilities
from utils.template_manager import (
    display_template_preview,
    extract_variables_from_template
)
from utils.web_tools import (
    search_web, 
    scrape_webpage, 
    format_source_data
)
from utils.ai_tools import generate_document_with_gemini
from utils.rag_tools import (
    generate_rag_content,
    create_rag_from_scraped_content
)

def render_verify_page():
    """Render the verification page."""
    st.header("Verify Your Document Generation Settings")
    
    # Display summary of choices
    st.subheader("Document Requirements")
    st.write(st.session_state.user_query)
    
    st.subheader("Template Preview")
    with st.expander("View Template"):
        st.write(display_template_preview(st.session_state.template_text), unsafe_allow_html=True)
    
    # Knowledge source verification
    st.subheader("Knowledge Source")
    st.write(f"Selected source: {st.session_state.knowledge_source}")
    
    # Prepare knowledge data based on the selected source
    if st.session_state.knowledge_source == "Search the Web":
        if st.button("Perform Web Search Now", key="search_web_button"):
            with st.spinner("Searching the web for relevant information..."):
                search_results = search_web(st.session_state.user_query)
                
                if not search_results:
                    st.error("Could not find relevant information. Please try a different query.")
                    st.stop()
                
                # Scrape content from search results
                scraped_contents = []
                progress_bar = st.progress(0)
                
                for i, result in enumerate(search_results):
                    st.write(f"Scraping: {result['title']}")
                    content = scrape_webpage(result["link"])
                    scraped_contents.append(content)
                    progress_bar.progress((i + 1) / len(search_results))
                
                # Save search results and scraped contents
                st.session_state.search_results = search_results
                st.session_state.scraped_contents = scraped_contents
                
                # Display search results
                st.success("Web search completed!")
                for i, result in enumerate(search_results):
                    st.write(f"**Source {i+1}:** [{result['title']}]({result['link']})")
                    st.write(result['snippet'])
                    
    elif st.session_state.knowledge_source == "Upload Document" or st.session_state.knowledge_source == "Specific URL":
        if st.session_state.knowledge_data:
            with st.expander("View Knowledge Source Content"):
                st.write(st.session_state.knowledge_data[:1000] + "..." if len(st.session_state.knowledge_data) > 1000 else st.session_state.knowledge_data)
        else:
            st.error("No knowledge source data available. Please go back and provide a valid document or URL.")
    
    # Choose content generation method
    st.subheader("Content Generation Method")
    generation_method = st.radio(
        "Select content generation method",
        ["Standard AI Generation", "RAG (Retrieval-Augmented Generation)"],
        help="RAG improves document relevance by focusing on your knowledge source"
    )
    
    # Save generation method to session state
    st.session_state.generation_method = generation_method
    
    # Buttons for navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Back to Input", key="back_button"):
            st.session_state.page = 'input'
            st.rerun()
    
    with col3:
        # Generate document button
        if st.button("Generate Document →", key="generate_button"):
            with st.spinner("Generating document..."):
                # Extract variables from template
                variables = extract_variables_from_template(st.session_state.template_text)
                
                # Generate document content based on selected method
                if generation_method == "Standard AI Generation":
                    # Prepare source data
                    if st.session_state.knowledge_source == "Search the Web":
                        if not st.session_state.search_results:
                            st.error("Please perform web search first.")
                            st.stop()
                        source_data = format_source_data(st.session_state.search_results, st.session_state.scraped_contents)
                    else:
                        # Use uploaded document or specific URL content
                        source_data = f"## SOURCE DATA:\n\n{st.session_state.knowledge_data}"
                    
                    # Generate document content with standard method
                    content_variables = generate_document_with_gemini(st.session_state.user_query, variables, source_data)
                
                else:  # RAG method
                    # Generate document content with RAG
                    if st.session_state.knowledge_source == "Search the Web":
                        if not st.session_state.search_results:
                            st.error("Please perform web search first.")
                            st.stop()
                        # Use RAG with web search results
                        content_variables = create_rag_from_scraped_content(
                            st.session_state.search_results,
                            st.session_state.scraped_contents,
                            st.session_state.user_query,
                            variables
                        )
                    else:
                        # Use RAG with uploaded document or specific URL
                        content_variables = generate_rag_content(
                            st.session_state.user_query,
                            variables,
                            st.session_state.knowledge_data
                        )
                
                # Render the template with generated content
                try:
                    from jinja2 import Template
                    jinja_template = Template(st.session_state.template_text)
                    generated_document = jinja_template.render(**content_variables)
                    
                    # Save generated document and variables
                    st.session_state.generated_document = generated_document
                    st.session_state.content_variables = content_variables
                    
                    # Go to results page
                    st.session_state.page = 'results'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error rendering template: {str(e)}")