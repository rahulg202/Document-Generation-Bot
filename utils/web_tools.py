import streamlit as st
import requests
import os
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the API key from environment variables
SERP_API_KEY = os.getenv("SERP_API_KEY")

def search_web(query, num_results=5):
    """Search the web and return top results."""
    url = "https://serpapi.com/search"
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google",
        "q": query,
        "num": num_results
    }
    
    st.info(f"Searching for information about: {query}")
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "organic_results" not in data:
            st.error("No search results found. Please try a different query.")
            return []
            
        results = []
        for result in data["organic_results"][:num_results]:
            results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        return results
    except Exception as e:
        st.error(f"Error searching the web: {str(e)}")
        logger.error(f"Search error: {str(e)}")
        return []

def scrape_webpage(url):
    """Scrape content from a webpage."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"Failed to retrieve content from {url}"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text length to prevent excessive content
        return text[:15000]  # Limit to 15k characters
        
    except Exception as e:
        logger.error(f"Scraping error ({url}): {str(e)}")
        return f"Error scraping {url}: {str(e)}"

def format_source_data(search_results, scraped_contents):
    """Format the source data for use with Gemini."""
    formatted_data = "## SOURCE DATA:\n\n"
    
    for i, result in enumerate(search_results):
        formatted_data += f"### Source {i+1}: {result['title']}\n"
        formatted_data += f"URL: {result['link']}\n"
        formatted_data += f"Description: {result['snippet']}\n\n"
        
        if i < len(scraped_contents):
            content_preview = scraped_contents[i][:500] + "..." if len(scraped_contents[i]) > 500 else scraped_contents[i]
            formatted_data += f"Content Preview: {content_preview}\n\n"
            
    return formatted_data

def search_for_template_by_name(template_name):
    """Search for a template by name on the web and return the content."""
    from utils.ai_tools import generate_template_from_search

    # First, search for the template
    search_results = search_web(f"{template_name} document template example", 3)
    
    if not search_results:
        return None
        
    # Then scrape the content from each result
    scraped_contents = []
    for result in search_results:
        content = scrape_webpage(result["link"])
        scraped_contents.append(content)
    
    # Format the data for the AI
    formatted_data = format_source_data(search_results, scraped_contents)
    
    # Generate a template using the AI
    template = generate_template_from_search(template_name, formatted_data)
    
    return template