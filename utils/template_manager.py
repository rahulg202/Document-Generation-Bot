import os
import json
import re
from pathlib import Path
import logging
from jinja2 import Template
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the path to the templates directory
TEMPLATES_DIR = Path("templates")

# Ensure the templates directory exists
TEMPLATES_DIR.mkdir(exist_ok=True)
TEMPLATES_INDEX = TEMPLATES_DIR / "index.json"

# Default templates as fallback
DEFAULT_TEMPLATES = {
    "customer_complaint_response": """
Dear {{ customer_name }},

Thank you for bringing your concerns to our attention regarding {{ issue_summary }}. We at {{ company_name }} take all customer feedback seriously.

{{ detailed_response }}

If you have any further questions or concerns, please don't hesitate to contact us at {{ contact_info }}.

Sincerely,
{{ agent_name }}
{{ company_name }}
    """,
    
    "product_report": """
# {{ product_name }} Analysis Report
**Date**: {{ date }}
**Prepared by**: {{ author }}

## Executive Summary
{{ executive_summary }}

## Product Details
{{ product_details }}

## Market Analysis
{{ market_analysis }}

## Recommendations
{{ recommendations }}

## Conclusion
{{ conclusion }}
    """
}

def initialize_templates():
    """Initialize the templates directory with default templates if it doesn't exist."""
    # Create the templates index file if it doesn't exist
    if not TEMPLATES_INDEX.exists():
        template_index = {}
        
        # Add default templates to the index and save to files
        for name, content in DEFAULT_TEMPLATES.items():
            template_path = TEMPLATES_DIR / f"{name}.txt"
            
            # Save template content to file
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Add to index
            template_index[name] = {
                "path": str(template_path.relative_to(TEMPLATES_DIR)),
                "description": f"Default {name.replace('_', ' ')} template",
                "category": "default",
                "source": "default"
            }
        
        # Save the index
        with open(TEMPLATES_INDEX, 'w', encoding='utf-8') as f:
            json.dump(template_index, f, indent=2)
        
        logger.info(f"Initialized templates directory with {len(DEFAULT_TEMPLATES)} default templates")
    else:
        logger.info("Templates directory already initialized")

def get_template_list():
    """Get a list of all available templates."""
    # Make sure templates are initialized
    initialize_templates()
    
    # Load the template index
    with open(TEMPLATES_INDEX, 'r', encoding='utf-8') as f:
        template_index = json.load(f)
    
    return template_index

def get_template_content(template_name):
    """Get the content of a specific template."""
    # Make sure templates are initialized
    initialize_templates()
    
    # Load the template index
    with open(TEMPLATES_INDEX, 'r', encoding='utf-8') as f:
        template_index = json.load(f)
    
    # Check if the template exists
    if template_name not in template_index:
        logger.warning(f"Template '{template_name}' not found")
        return None
    
    # Get the template path
    template_path = TEMPLATES_DIR / template_index[template_name]["path"]
    
    # Read the template content
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading template '{template_name}': {str(e)}")
        return None

def save_new_template(template_name, template_content, description="", category="user", source="web_search"):
    """Save a new template to the templates directory."""
    # Make sure templates are initialized
    initialize_templates()
    
    # Sanitize the template name for filename
    safe_name = re.sub(r'[^\w\s-]', '', template_name).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    
    # Load the template index
    with open(TEMPLATES_INDEX, 'r', encoding='utf-8') as f:
        template_index = json.load(f)
    
    # Define the template file path
    template_path = f"{safe_name}.txt"
    full_path = TEMPLATES_DIR / template_path
    
    # Save the template content to file
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    # Add to index
    template_index[safe_name] = {
        "path": template_path,
        "description": description or f"Template for {template_name}",
        "category": category,
        "source": source,
        "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save the updated index
    with open(TEMPLATES_INDEX, 'w', encoding='utf-8') as f:
        json.dump(template_index, f, indent=2)
    
    logger.info(f"Saved new template: {safe_name}")
    return safe_name

def extract_variables_from_template(template_text):
    """Extract Jinja2 variables from a template."""
    variable_pattern = r'{{\s*(\w+)\s*}}'
    matches = re.findall(variable_pattern, template_text)
    return list(set(matches))  # Return unique variable names

def validate_template(template_text):
    """Validate that a template is properly formatted."""
    try:
        Template(template_text)
        return True, "Template is valid"
    except Exception as e:
        return False, f"Template validation error: {str(e)}"

def display_template_preview(template_text):
    """Display a template in a user-friendly format without showing raw code."""
    # Extract variables for explanation
    variables = extract_variables_from_template(template_text)
    
    # Create a simplified version of the template for display
    # Replace Jinja variables with highlighted placeholders
    simplified_template = template_text
    for var in variables:
        simplified_template = simplified_template.replace(f"{{{{ {var} }}}}", f"[{var}]")
    
    # Remove any HTML+Django or CSS markers that might be at the start
    simplified_template = re.sub(r'^html\+django\s*', '', simplified_template)
    simplified_template = re.sub(r'^html\+jinja\s*', '', simplified_template)
    simplified_template = re.sub(r'^body\s*{.*?}\s*h1,\s*h2,\s*h3\s*{.*?}\s*table\s*{.*?}.*?$', '', simplified_template, flags=re.MULTILINE)
    
    # Apply some basic styling for better readability
    styled_preview = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">
        <div style="white-space: pre-wrap;">{simplified_template}</div>
        <hr>
        <p><strong>Template Variables:</strong> {', '.join(variables)}</p>
    </div>
    """
    
    return styled_preview