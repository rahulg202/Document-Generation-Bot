# GenAI Document Generation Bot

A powerful Streamlit application that leverages Generative AI to create custom documents based on templates and various knowledge sources.

## ✨ Features

- **Multiple Knowledge Sources**: Upload documents (PDF, DOCX, TXT), search the web, or specify a URL to gather information
- **Template Management**: Use predefined templates, search for templates, or upload custom templates
- **Jinja2 Template Support**: Utilize the power of Jinja2 templating for flexible document creation
- **RAG (Retrieval-Augmented Generation)**: Improve document relevance by focusing on your knowledge source
- **Multi-format Export**: Download your generated documents in PDF, DOCX, or Markdown format
- **Template Library**: Save and reuse templates for future document generation

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Required Python packages (see `requirements.txt`)
- Google API key for Gemini AI (set as environment variable)
- SERP API key for web searches (set as environment variable)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rahulg202/Document-Generation-Bot.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   SERP_API_KEY=your_serp_api_key
   ```

4. Run the application:
   ```bash
   streamlit run main.py
   ```

## 🔍 How It Works

1. **Input Information**:
   - Enter your document requirements
   - Select a knowledge source (upload a document, search the web, or specify a URL)
   - Choose a template (predefined, search for one, or upload custom)

2. **Verification**:
   - Review your selections
   - Choose between standard AI generation or RAG (Retrieval-Augmented Generation)
   - Perform web searches if needed

3. **Results**:
   - View your generated document
   - Download in your preferred format (PDF, DOCX, or Markdown)
   - Provide feedback for improvement

## 📑 Template System

The application uses Jinja2 for templating, which allows for powerful and flexible document creation:

- Variables are defined using `{{ variable_name }}` syntax
- Templates can be saved for future use
- Custom templates can be uploaded in various formats (TXT, J2, JINJA, HTML, MD)

## 🧠 AI Capabilities

The system leverages Google's Gemini AI to:

- Generate document content based on templates
- Extract relevant information from knowledge sources
- Create new templates based on user requirements
- Implement RAG for improved relevance

## 📋 Project Structure

```
genai-document-generator/
│
├── main.py                  # Main application entry point
├── components/              # UI components
│   ├── input_page.py        # Document requirements input
│   ├── verify_page.py       # Verification and generation  
│   └── results_page.py      # Results display and export
│
├── utils/                   # Utility functions
│   ├── ai_tools.py          # AI integration tools
│   ├── document_processing.py # Document handling
│   ├── pdf_tools.py         # PDF generation utilities
│   ├── rag_tools.py         # RAG implementation
│   ├── template_manager.py  # Template management
│   └── web_tools.py         # Web searching and scraping
│
├── templates/               # Template storage
│   ├── index.json           # Template index
│   └── *.txt                # Template files
│
└── requirements.txt         # Python dependencies
```

## 📊 RAG Implementation

The application includes a robust implementation of Retrieval-Augmented Generation:

1. Text is preprocessed and chunked for efficient retrieval
2. TF-IDF vectorization is used for embedding
3. Cosine similarity determines the most relevant chunks
4. Relevant information is fed to Gemini AI with the user query
5. The generated content is formatted and rendered using the chosen template

## 🛠️ Future Improvements

- Vector database integration for more efficient RAG
- Template categories and tags for better organization
- Collaborative document editing
- API access for programmatic document generation
- Additional output formats and styling options
