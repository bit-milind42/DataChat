# DataChat Backend - Setup & Development Guide

## Overview

DataChat Backend is a FastAPI application that:
- Handles CSV file uploads
- Converts natural language questions to SQL queries using LangChain + Gemini
- Executes queries and returns results
- Manages chat history and query results

## Project Structure

```
backend/
├── main.py                 # FastAPI app & entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
│
├── api/
│   ├── __init__.py
│   ├── routes.py          # API endpoints
│   └── schemas.py         # Pydantic models
│
├── agents/
│   ├── __init__.py
│   └── sql_agent.py       # LangChain SQL Agent
│
├── databases/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   └── dataset_manager.py # Dataset management
│
├── uploads/               # Uploaded CSV files
└── venv/                  # Virtual environment
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Update `.env` with your credentials:

```env
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here

# Server
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy and paste into `.env`

### 4. Start Backend Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

## 📁 Key Components

### Models (databases/models.py)

Three main database models:

1. **Dataset** - CSV file metadata
   - id, name, filename, row_count, columns
   
2. **ChatMessage** - Chat history
   - id, dataset_id, content, sender, timestamp
   
3. **QueryResult** - Query execution results
   - id, dataset_id, query, sql_query, rows_data, execution_time

### Dataset Manager (databases/dataset_manager.py)

Handles:
- CSV upload & processing with pandas
- Dataset CRUD operations
- File storage management

### SQL Agent (agents/sql_agent.py)

LangChain agent that:
- Converts natural language → SQL queries
- Uses Gemini 2.5 Flash model
- Executes queries against database
- Returns structured results

### Routes (api/routes.py)

API endpoints:

```
POST   /api/datasets/upload     # Upload CSV file
POST   /api/query               # Execute natural language query
GET    /api/datasets            # List all datasets
GET    /api/datasets/{id}       # Get dataset info
DELETE /api/datasets/{id}       # Delete dataset
GET    /api/chat-history/{id}   # Get chat history
```

## 🔌 API Endpoints

### Upload Dataset

```bash
POST /api/datasets/upload
Content-Type: multipart/form-data

Request:
- file: CSV file

Response:
{
  "success": true,
  "data": {
    "id": "dataset_abc123",
    "name": "sales",
    "filename": "sales.csv",
    "rowCount": 1000,
    "columns": ["date", "amount", "product"],
    "uploadedAt": "2026-05-22T10:30:00"
  }
}
```

### Query Dataset

```bash
POST /api/query
Content-Type: application/json

Request:
{
  "datasetId": "dataset_abc123",
  "question": "How many sales did we have last month?"
}

Response:
{
  "success": true,
  "data": {
    "id": "query_xyz789",
    "query": "How many sales did we have last month?",
    "rows": [
      {"month": "April", "total_sales": 5000},
      {"month": "May", "total_sales": 7500}
    ],
    "columns": ["month", "total_sales"],
    "executionTime": 245
  }
}
```

### List Datasets

```bash
GET /api/datasets

Response:
{
  "success": true,
  "data": [
    {
      "id": "dataset_abc123",
      "name": "sales",
      "filename": "sales.csv",
      "rowCount": 1000,
      "columns": ["date", "amount", "product"],
      "uploadedAt": "2026-05-22T10:30:00"
    }
  ]
}
```

### Get Chat History

```bash
GET /api/chat-history/dataset_abc123

Response:
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg_123",
        "content": "How many sales?",
        "sender": "user",
        "timestamp": "2026-05-22T10:30:00"
      },
      {
        "id": "msg_124",
        "content": "Found 10 results",
        "sender": "assistant",
        "timestamp": "2026-05-22T10:30:05"
      }
    ],
    "datasetId": "dataset_abc123",
    "createdAt": "2026-05-22T10:30:00",
    "updatedAt": "2026-05-22T10:30:05"
  }
}
```

## 🤖 How It Works

### Query Execution Flow

```
1. User asks question in natural language
   ↓
2. Question sent to /api/query endpoint
   ↓
3. LangChain SQL Agent processes question
   ↓
4. Agent converts to SQL using Gemini model
   ↓
5. Execute SQL against database
   ↓
6. Format results as JSON
   ↓
7. Store in database (chat history, query results)
   ↓
8. Return to frontend
```

### Database Schema

The system uses a simple SQLite/PostgreSQL schema:

```sql
-- Datasets table
CREATE TABLE datasets (
  id VARCHAR PRIMARY KEY,
  name VARCHAR,
  filename VARCHAR,
  row_count INTEGER,
  columns JSON,
  created_at DATETIME,
  updated_at DATETIME
);

-- Chat messages
CREATE TABLE chat_messages (
  id VARCHAR PRIMARY KEY,
  dataset_id VARCHAR,
  content TEXT,
  sender VARCHAR,
  timestamp DATETIME
);

-- Query results
CREATE TABLE query_results (
  id VARCHAR PRIMARY KEY,
  dataset_id VARCHAR,
  query VARCHAR,
  sql_query VARCHAR,
  rows_data JSON,
  execution_time INTEGER,
  created_at DATETIME
);
```

## 🔑 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `GOOGLE_API_KEY` | Gemini API key | `AIza...` |
| `PORT` | Server port | `8000` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

## 📦 Dependencies

### Core
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

### LLM & AI
- **LangChain** - LLM orchestration
- **Google Generative AI** - Gemini models
- **SQLDatabase** - SQL toolkit

### Data
- **Pandas** - CSV processing
- **psycopg2** - PostgreSQL adapter

## 🧪 Testing Endpoints

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List datasets
curl http://localhost:8000/api/datasets

# Upload CSV
curl -X POST -F "file=@data.csv" http://localhost:8000/api/datasets/upload

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"dataset_abc","question":"What is the total?"}'
```

### Using Python

```python
import requests

# Query dataset
response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "datasetId": "dataset_abc123",
        "question": "What are the top 5 products?"
    }
)
print(response.json())
```

## 🔍 Debugging

### Enable verbose logging

In `agents/sql_agent.py`, the agent is already set to `verbose=True`.

### Check database

```bash
# Connect to PostgreSQL (if using Supabase)
psql postgresql://user:password@host:port/database

# View datasets
SELECT * FROM datasets;

# View chat messages
SELECT * FROM chat_messages;

# View query results
SELECT * FROM query_results;
```

### API Documentation

FastAPI automatically generates interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## ⚠️ Common Issues

### Google API Key errors
- Ensure key is valid and has Generative AI API enabled
- Check `.env` has correct key format

### Database connection errors
- Verify DATABASE_URL is correct
- For Supabase: ensure IP whitelist includes your IP
- Test connection: `psql "your_connection_string"`

### CSV upload fails
- Check file format is valid CSV
- Ensure file is not too large (>100MB may have issues)
- Headers must be on first row

### Query execution slow
- Large datasets may take longer
- Consider adding database indexes
- Use query optimization in SQL Agent

## 🚀 Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -b 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

- Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
- Never commit API keys to git
- Use `.env.production` for production settings

## 📚 Next Steps

1. ✅ Install dependencies
2. ✅ Get Gemini API key
3. ✅ Configure database
4. 🚀 Start server
5. 🧪 Test endpoints
6. 🔗 Connect frontend

## Support

- Check API docs at `/docs`
- Review error responses carefully
- Enable verbose logging for debugging
- Check database records for query history

---

Built with FastAPI, LangChain, and Google Gemini
