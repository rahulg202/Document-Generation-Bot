import streamlit as st
import google.generativeai as genai
import os
import re
from tqdm import tqdm
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from bs4 import BeautifulSoup
import markdown

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def preprocess_text(text):
    """Preprocess text for embedding and retrieval."""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks."""
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed the chunk size
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            # Keep the overlap from the end of the current chunk
            if len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def create_embeddings(chunks):
    """Create TF-IDF embeddings for text chunks."""
    # Process chunks for TF-IDF
    processed_chunks = [preprocess_text(chunk) for chunk in chunks]
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(processed_chunks)
    
    return tfidf_matrix, vectorizer

def retrieve_relevant_chunks(query, chunks, tfidf_matrix, vectorizer, top_k=3):
    """Retrieve the most relevant chunks for a query using TF-IDF similarity."""
    # Process the query
    processed_query = preprocess_text(query)
    
    # Transform the query to TF-IDF
    query_vector = vectorizer.transform([processed_query])
    
    # Calculate similarity scores
    similarity_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # Get the indices of the top_k most similar chunks
    top_indices = similarity_scores.argsort()[-top_k:][::-1]
    
    # Return the top chunks and their scores
    return [(chunks[i], similarity_scores[i]) for i in top_indices]

def generate_rag_content(user_query, variables, knowledge_data):
    """Generate content using RAG approach with local knowledge."""
    if not knowledge_data:
        return {}
    
    # Chunk the knowledge data
    chunks = chunk_text(knowledge_data)
    
    # Create embeddings
    tfidf_matrix, vectorizer = create_embeddings(chunks)
    
    # Retrieve relevant chunks
    relevant_chunks = retrieve_relevant_chunks(
        user_query, chunks, tfidf_matrix, vectorizer
    )
    
    # Format relevant chunks for the prompt
    formatted_chunks = "\n\n".join(
        [f"CHUNK (relevance: {score:.2f}):\n{chunk}" for chunk, score in relevant_chunks]
    )
    
    # Generate content with Gemini
    prompt = f"""
    Generate content for a document based on the following:
    
    User Query: {user_query}
    
    Relevant Knowledge:
    {formatted_chunks}
    
    Please provide content for the following variables to be used in a document template:
    {', '.join(variables)}
    
    For each variable, provide accurate, relevant, and well-written content based on the information in the sources.
    Format your response as JSON with each variable as a key.
    Ensure the content is properly formatted and professional.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        content = response.text
        
        # Try to find JSON in the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Assume the entire response is JSON
            json_str = content
            
        # Clean up the JSON string
        json_str = json_str.strip()
        
        # Parse JSON
        try:
            import json
            variables_content = json.loads(json_str)
            
            # Clean up any markdown formatting from the content
            for key in variables_content:
                if isinstance(variables_content[key], str):
                    # Remove markdown headings, bold, italic, etc.
                    variables_content[key] = re.sub(r'^#+\s+', '', variables_content[key], flags=re.MULTILINE)  # Remove heading markers
                    variables_content[key] = re.sub(r'\*\*(.*?)\*\*', r'\1', variables_content[key])  # Remove bold
                    variables_content[key] = re.sub(r'\*(.*?)\*', r'\1', variables_content[key])  # Remove italic
                    variables_content[key] = re.sub(r'`(.*?)`', r'\1', variables_content[key])  # Remove code ticks
                    variables_content[key] = re.sub(r'```.*?```', '', variables_content[key], flags=re.DOTALL)  # Remove code blocks
                    variables_content[key] = re.sub(r'<[^>]*>', '', variables_content[key])  # Remove HTML tags
            
            return variables_content
        except json.JSONDecodeError:
            # If parsing fails, try to create a JSON object manually
            variables_content = {}
            for var in variables:
                pattern = fr'["\']?{var}["\']?\s*:\s*["\']([^"\']+)["\']'
                match = re.search(pattern, json_str)
                if match:
                    variables_content[var] = match.group(1)
                else:
                    variables_content[var] = f"[Content for {var} not found]"
            return variables_content
            
    except Exception as e:
        logger.error(f"Error generating content with RAG: {str(e)}")
        return {var: f"[Error generating content for {var}]" for var in variables}

def extract_text_from_html(html_content):
    """Extract plain text from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def create_rag_from_scraped_content(search_results, scraped_contents, user_query, variables):
    """Create RAG from scraped web content."""
    if not search_results or not scraped_contents:
        return {}
    
    # Combine all scraped content
    combined_content = "\n\n".join(scraped_contents)
    
    # Chunk the combined content
    chunks = chunk_text(combined_content)
    
    # Create embeddings
    tfidf_matrix, vectorizer = create_embeddings(chunks)
    
    # Retrieve relevant chunks
    relevant_chunks = retrieve_relevant_chunks(
        user_query, chunks, tfidf_matrix, vectorizer, top_k=5
    )
    
    # Format relevant chunks for the prompt with their sources
    formatted_chunks = ""
    for i, (chunk, score) in enumerate(relevant_chunks):
        source_idx = 0
        for j, content in enumerate(scraped_contents):
            if chunk in content:
                source_idx = j
                break
        
        if source_idx < len(search_results):
            source_info = f"Source: {search_results[source_idx]['title']} ({search_results[source_idx]['link']})"
        else:
            source_info = "Source: Unknown"
            
        formatted_chunks += f"CHUNK {i+1} (relevance: {score:.2f}):\n{source_info}\n{chunk}\n\n"
    
    # Generate content with Gemini
    prompt = f"""
    Generate content for a document based on the following:
    
    User Query: {user_query}
    
    Relevant Knowledge:
    {formatted_chunks}
    
    Please provide content for the following variables to be used in a document template:
    {', '.join(variables)}
    
    For each variable, provide accurate, relevant, and well-written content based on the information in the sources.
    Format your response as JSON with each variable as a key.
    Ensure the content is properly formatted and professional.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        content = response.text
        
        # Parse JSON
        try:
            import json
            # Try to find JSON in the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Assume the entire response is JSON
                json_str = content
                
            # Clean up the JSON string
            json_str = json_str.strip()
            
            variables_content = json.loads(json_str)
            
            # Clean up any markdown formatting from the content
            for key in variables_content:
                if isinstance(variables_content[key], str):
                    # Remove markdown headings, bold, italic, etc.
                    variables_content[key] = re.sub(r'^#+\s+', '', variables_content[key], flags=re.MULTILINE)  # Remove heading markers
                    variables_content[key] = re.sub(r'\*\*(.*?)\*\*', r'\1', variables_content[key])  # Remove bold
                    variables_content[key] = re.sub(r'\*(.*?)\*', r'\1', variables_content[key])  # Remove italic
                    variables_content[key] = re.sub(r'`(.*?)`', r'\1', variables_content[key])  # Remove code ticks
                    variables_content[key] = re.sub(r'```.*?```', '', variables_content[key], flags=re.DOTALL)  # Remove code blocks
                    variables_content[key] = re.sub(r'<[^>]*>', '', variables_content[key])  # Remove HTML tags
            
            return variables_content
        except json.JSONDecodeError:
            # If parsing fails, try to create a JSON object manually
            variables_content = {}
            for var in variables:
                pattern = fr'["\']?{var}["\']?\s*:\s*["\']([^"\']+)["\']'
                match = re.search(pattern, json_str)
                if match:
                    variables_content[var] = match.group(1)
                else:
                    variables_content[var] = f"[Content for {var} not found]"
            return variables_content
            
    except Exception as e:
        logger.error(f"Error generating content with web RAG: {str(e)}")
        return {var: f"[Error generating content for {var}]" for var in variables}