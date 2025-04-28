import streamlit as st
import google.generativeai as genai
import os
import json
import re
import logging
from jinja2 import Template

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def generate_template_from_search(template_name, source_data):
    """Use Gemini to generate a template based on search results."""
    prompt = f"""
    Based on the following search results and content, create a professional Jinja2 template for a "{template_name}".
    
    {source_data}
    
    Generate a template with appropriate variables in Jinja2 format (using {{ variable_name }} syntax).
    Include sections that would typically be found in a {template_name} document.
    Format the template to be clean and professional. Do not include explanations, just return the template.
    Do not include CSS styling or HTML tags in the template, just focus on content structure.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        generated_template = response.text
        
        # Clean up the template to ensure proper Jinja format
        generated_template = re.sub(r'```jinja2?|```', '', generated_template)
        generated_template = generated_template.strip()
        
        # Remove any CSS styling that might have been included
        generated_template = re.sub(r'^body\s*{.*?}\s*h1,\s*h2,\s*h3\s*{.*?}\s*table\s*{.*?}.*?$', '', generated_template, flags=re.MULTILINE)
        
        # Validate the template
        try:
            Template(generated_template)
            return generated_template
        except Exception as e:
            logger.error(f"Generated template was invalid: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        return None

def generate_document_with_gemini(user_query, template_vars, source_data):
    """Use Gemini to generate content for the document based on user query and sources."""
    prompt = f"""
    Generate content for a document based on the following:
    
    User Query: {user_query}
    
    {source_data}
    
    Please provide content for the following variables to be used in a document template:
    {', '.join(template_vars)}
    
    For each variable, provide accurate, relevant, and well-written content based on the information in the sources.
    Format your response as JSON with each variable as a key.
    Ensure the content is properly formatted and professional.
    Do NOT include markdown syntax in your responses - provide plain text that can be formatted by the template system.
    Do NOT include any HTML or CSS code - provide clean text only.
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
            variables = json.loads(json_str)
            
            # Clean up any markdown formatting from the content
            for key in variables:
                if isinstance(variables[key], str):
                    # Remove markdown headings, bold, italic, etc.
                    variables[key] = re.sub(r'^#+\s+', '', variables[key], flags=re.MULTILINE)  # Remove heading markers
                    variables[key] = re.sub(r'\*\*(.*?)\*\*', r'\1', variables[key])  # Remove bold
                    variables[key] = re.sub(r'\*(.*?)\*', r'\1', variables[key])  # Remove italic
                    variables[key] = re.sub(r'`(.*?)`', r'\1', variables[key])  # Remove code ticks
                    variables[key] = re.sub(r'```.*?```', '', variables[key], flags=re.DOTALL)  # Remove code blocks
                    variables[key] = re.sub(r'<[^>]*>', '', variables[key])  # Remove HTML tags
            
            return variables
        except json.JSONDecodeError:
            # If parsing fails, try to create a JSON object manually
            variables = {}
            for var in template_vars:
                pattern = fr'["\']?{var}["\']?\s*:\s*["\']([^"\']+)["\']'
                match = re.search(pattern, json_str)
                if match:
                    variables[var] = match.group(1)
                else:
                    variables[var] = f"[Content for {var} not found]"
            return variables
            
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {str(e)}")
        return {var: f"[Error generating content for {var}]" for var in template_vars}