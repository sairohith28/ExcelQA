# Excel QA System - RAG with PostgreSQL + Gemini Embeddings

Query your Excel files using natural language powered by Google Gemini with RAG (Retrieval Augmented Generation) approach.

## Architecture

This system uses a sophisticated RAG approach:

1. **Data Storage**: Excel data → PostgreSQL database
2. **Embeddings**: Generate embeddings for each row using Gemini's text-embedding-004 model
3. **Vector Storage**: Store embeddings in PostgreSQL with pgvector extension
4. **Query Processing**:
   - User question → Generate embedding
   - Retrieve top-k most similar rows using cosine similarity
   - Pass relevant data + conversation history to Gemini LLM
   - Generate accurate answer and 3 follow-up questions

## Features

✅ **RAG Architecture** - Semantic search with embeddings + LLM generation  
✅ **PostgreSQL Backend** - Persistent storage with pgvector for fast similarity search  
✅ **Context-Aware** - Maintains conversation history for contextual understanding  
✅ **3 Follow-up Questions** - Auto-generated after each query  
✅ **Accurate Retrieval** - Finds most relevant data using embeddings  
✅ **Scalable** - Works with 100-10,000+ rows efficiently  

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
```powershell
# Download installer from: https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql15

# Or use Docker Desktop:
docker run -d --name excelqa-postgres -e POSTGRES_DB=excelqa -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg16
```

### 3. Install pgvector (Recommended for Performance)

```bash
# macOS
brew install pgvector

# Ubuntu/Debian
sudo apt install postgresql-15-pgvector

# Or build from source: https://github.com/pgvector/pgvector#installation
```

### 4. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE excelqa;

# Enable pgvector extension
\c excelqa
CREATE EXTENSION vector;
\q
```

## Setup

1. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Edit `excel_qa.py` and update configuration:
   ```python
   GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
   
   DB_CONFIG = {
       'host': 'localhost',
       'port': 5432,
       'database': 'excelqa',
       'user': 'postgres',
       'password': 'your_password'
   }
   ```

3. Place your Excel file or let it create a sample:
   ```python
   EXCEL_FILE = "your_file.xlsx"
   ```

## Usage

### Run with demo queries:
```bash
python excel_qa.py
```

The system will:
1. Load Excel data into PostgreSQL
2. Generate embeddings for all rows (may take a few minutes)
3. Run demo queries showing RAG in action

### Enable interactive mode:
Uncomment the interactive mode section in `excel_qa.py` (lines ~570-595)

```bash
python excel_qa.py
```

Then ask questions like:
- "How many employees are in Engineering?"
- "Show me high performers with good ratings"
- "What's their average salary?" (context-aware)
- "Who has the most experience?"

## How It Works

### RAG Pipeline

1. **Initialization**:
   - Load Excel → PostgreSQL
   - Generate embeddings for each row
   - Store in pgvector for fast retrieval

2. **Query Processing**:
   ```
   User Question
        ↓
   Generate Query Embedding (Gemini)
        ↓
   Similarity Search (PostgreSQL + pgvector)
        ↓
   Retrieve Top-K Relevant Rows
        ↓
   LLM Generation (Gemini + Context History)
        ↓
   Answer + Follow-up Questions
   ```

3. **Context Management**:
   - Stores last 3 Q&A exchanges
   - Understands references like "those", "that", "previous"

## Why This Approach?

### ✅ Advantages
- **Semantic Search**: Finds relevant data even with different wording
- **Scalable**: Handles 100-100K+ rows efficiently
- **Context-Aware**: Maintains conversation flow
- **Accurate**: Retrieves only relevant data for LLM
- **Persistent**: Data stays in PostgreSQL for reuse

### 🔧 When to Use
- Medium to large datasets (100+ rows)
- Need semantic understanding of queries
- Want to reuse embeddings across sessions
- Multiple users querying same dataset
- Complex natural language queries

### ⚡ Performance
- **With pgvector**: Sub-second similarity search
- **Without pgvector**: Falls back to in-memory computation (slower but works)

## API

```python
# Initialize
qa_system = ExcelQASystem(
    excel_path="data.xlsx",
    api_key="GEMINI_API_KEY",
    db_config={
        'host': 'localhost',
        'port': 5432,
        'database': 'excelqa',
        'user': 'postgres',
        'password': 'password'
    }
)

# Ask questions with RAG
response = qa_system.ask("Your question here", top_k=10)

# Clear conversation history
qa_system.clear_history()

# Preview data from PostgreSQL
qa_system.show_data_preview(n=5)
```

## Response Format

```python
{
    'success': True,
    'question': "...",
    'answer': "...",  # Generated by LLM based on relevant data
    'relevant_data': [  # Top-k retrieved rows with similarity scores
        {'row_id': 1, 'content': '...', 'similarity': 0.85},
        ...
    ],
    'followup_questions': ["...", "...", "..."]
}
```

## Troubleshooting

### pgvector not available
The system will automatically fall back to JSON storage and in-memory similarity computation. It will still work but slower for large datasets.

### PostgreSQL connection error
- Ensure PostgreSQL is running:
  - macOS: `brew services list`
  - Linux: `sudo systemctl status postgresql`
  - Windows: `Get-Service -Name postgresql*` (PowerShell)
- Check credentials in DB_CONFIG
- Verify database exists: `psql -l` (or `psql -U postgres -l` on Windows)

### Slow embedding generation
- Gemini API has rate limits
- ~1-2 seconds per row
- For 100 rows: ~2-3 minutes initial setup
- Embeddings are reused, so subsequent runs are instant
```
