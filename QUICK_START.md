# 🚀 DataChat - Complete Setup & Quick Start Guide

## ✅ Project Status: READY TO RUN

All features have been implemented and integrated. Follow these steps to start the complete project.

---

## 📋 Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **npm or yarn** (for package management)
- **Git** (for version control)

---

## 🔧 Installation & Configuration

### Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Backend Configuration

Create a `.env` file in the backend directory:

```env
# Google Gemini API Key (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your_gemini_api_key_here

# Database Configuration
# Option 1: SQLite (default, no setup needed)
DATABASE_URL=sqlite:///./datachat.db

# Option 2: PostgreSQL (Supabase or local)
# DATABASE_URL=postgresql://user:password@localhost:5432/datachat

# Option 3: MySQL
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/datachat

# Server Configuration
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Email Configuration (for scheduled reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Step 3: Start Backend Server

```bash
# From backend directory with virtual environment activated
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [1234]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open http://localhost:8000/docs to see API documentation.

---

### Step 4: Frontend Setup

In a NEW terminal window:

```bash
# Navigate to frontend
cd my-app

# Install dependencies
npm install
# or
yarn install
```

### Step 5: Frontend Configuration

Create `.env.local` in the `my-app` directory:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 6: Start Frontend Server

```bash
# From my-app directory
npm run dev
# or
yarn dev
```

**Expected Output:**
```
  ▲ Next.js 16.2.6
  - Local:        http://localhost:3000
  - Environments: .env.local
```

Open http://localhost:3000 in your browser.

---

## 🎯 Features Quick Start

### 1. **Chat Interface** (Main Page)
- **URL:** http://localhost:3000
- **Steps:**
  1. Click "Upload CSV" or drag-and-drop a file
  2. Type a question about your data (e.g., "What are the top 5 sales?")
  3. See results with AI insights
  4. View follow-up question suggestions
  5. Create charts with advanced visualizations

### 2. **Custom Dashboards**
- **URL:** http://localhost:3000/dashboards
- **Steps:**
  1. Click "New Dashboard"
  2. Enter dashboard name
  3. Click "Edit" to open dashboard builder
  4. Click "Add Widget" to add charts/tables
  5. Arrange widgets by dragging
  6. Save dashboard layout

### 3. **Scheduled Reports**
- **Location:** http://localhost:3000/dashboards/[id]/reports
- **Steps:**
  1. Go to a dashboard
  2. Click "Scheduled Reports" tab
  3. Click "New Report"
  4. Configure frequency (daily/weekly/monthly)
  5. Add recipient emails
  6. Choose format (PDF/Excel/HTML)
  7. Save and enable

### 4. **Saved Queries**
- **URL:** http://localhost:3000/saved-queries
- **Steps:**
  1. After running a query, click "Save Query"
  2. Give it a name and tags
  3. Mark as favorite if desired
  4. Access anytime from Saved Queries page
  5. Search and filter by tags

### 5. **Data Profiling**
- **Location:** Chat interface, "Data Profile" tab
- **Shows:**
  - Row/column counts
  - Data types
  - Missing values
  - Statistics (mean, median, std)
  - Data quality score

### 6. **Export Results**
- **Location:** Results panel (right side of chat)
- **Formats:**
  - CSV (spreadsheet)
  - JSON (structured data)
  - PDF (professional report)

---

## 📊 Sample Workflow

### Complete Data Analysis Workflow

```
1. Upload Data
   └─ automatic data profiling

2. Ask Question
   "What were my top-selling products last quarter?"
   └─ AI generates SQL
   └─ Results returned
   └─ Insights generated
   └─ Follow-up suggestions shown

3. View Results
   - Data table (first 10 rows)
   - Row count and execution time
   - Key insights and patterns

4. Visualize
   - Click "Chart Builder" for quick viz
   - Click "Advanced Charts" for more options
   - Choose chart type (bar, line, scatter, etc.)
   - Select X/Y axes

5. Explore Further
   - Click on suggested follow-up questions
   - Ask new questions with new filters
   - Export results to CSV/PDF

6. Create Dashboard
   - Save analysis as dashboard
   - Add multiple related queries as widgets
   - Share with team
   - Schedule automated reports

7. Share & Export
   - Export results (CSV, PDF)
   - Share dashboard link
   - Schedule report emails
```

---

## 🔌 API Testing

### Using cURL

```bash
# Upload dataset
curl -X POST "http://localhost:8000/api/datasets/upload" \
  -F "file=@data.csv"

# Execute query
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "dataset-id",
    "question": "Show me the top 5 products"
  }'

# Get follow-up questions
curl -X POST "http://localhost:8000/api/queries/query-id/follow-ups"

# Create dashboard
curl -X POST "http://localhost:8000/api/dashboards?user_id=user1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Dashboard",
    "description": "Q4 Sales Analysis"
  }'
```

### Using Swagger UI

Visit http://localhost:8000/docs for interactive API documentation.

---

## 🆘 Troubleshooting

### Backend Issues

**Issue: Port 8000 already in use**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill process or use different port
python main.py --port 8001
```

**Issue: Google API Key error**
```
Error: "GOOGLE_API_KEY not found"
Solution: Add valid API key to .env file
- Go to https://makersuite.google.com/app/apikey
- Create new API key
- Add to GOOGLE_API_KEY in .env
```

**Issue: Database connection error**
```
Error: "Could not connect to database"
Solution: Check DATABASE_URL in .env
- SQLite: Automatic (no setup needed)
- PostgreSQL: Verify server is running
- MySQL: Verify server is running
```

### Frontend Issues

**Issue: Cannot connect to backend**
```
Error: "Failed to fetch from API"
Solution: Check NEXT_PUBLIC_API_URL in .env.local
- Should be http://localhost:8000
- Ensure backend is running
- Check ALLOWED_ORIGINS in backend .env
```

**Issue: Port 3000 already in use**
```bash
# Use different port
npm run dev -- -p 3001

# Or find and kill process
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # macOS/Linux
```

---

## 📱 Testing with Sample Data

Download sample CSV files from:
- [Kaggle Datasets](https://kaggle.com/datasets)
- [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/)

### Sample Questions to Try

**Sales Data:**
- "What was our total revenue by month?"
- "Which regions had the highest growth?"
- "What's the average order value?"

**Customer Data:**
- "How many customers are in each segment?"
- "What's the customer retention rate?"
- "Which customers spent the most?"

**Product Data:**
- "Which products are out of stock?"
- "What's the inventory turnover?"
- "Which categories are growing fastest?"

---

## 🚀 Production Deployment

### Docker Deployment

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./backend/uploads:/app/uploads

  frontend:
    build: ./my-app
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=datachat
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Cloud Deployment Options

- **AWS:** Elastic Beanstalk, Lambda + RDS
- **Azure:** App Service, Azure SQL
- **Google Cloud:** Cloud Run, Cloud SQL
- **Heroku:** Free tier for testing
- **Railway.app:** Simple deploy

---

## 📈 Monitoring & Logging

### Backend Logging
```python
# Add to main.py for better logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Frontend Error Tracking
```typescript
// Add error boundary in layout.tsx
if (error) {
  console.error('Application error:', error);
  // Send to monitoring service (Sentry, DataDog, etc.)
}
```

---

## 🔐 Security Checklist

- [ ] Change default database password
- [ ] Use strong ALLOWED_ORIGINS in backend
- [ ] Enable HTTPS in production
- [ ] Set secure cookies
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Use environment variables for secrets
- [ ] Enable SQL injection protection
- [ ] Add CORS headers properly
- [ ] Regular security updates

---

## 📞 Support & Resources

- **API Documentation:** http://localhost:8000/docs
- **Frontend Type Definitions:** `my-app/types/index.ts`
- **Backend Models:** `backend/databases/models.py`
- **Components:** `my-app/components/`

---

## ✨ What's Next?

With the complete DataChat system running, consider:

1. **User Authentication** - Add login system
2. **Team Management** - Invite users to teams
3. **Advanced Permissions** - Role-based access
4. **Real-time Updates** - WebSocket for live queries
5. **Caching Layer** - Redis for faster responses
6. **Monitoring** - Sentry for error tracking
7. **Analytics** - Track user behavior
8. **API Keys** - Programmatic access

---

## 🎉 Congratulations!

You now have a fully-functional, enterprise-ready data analysis platform with:

✅ AI-powered natural language queries  
✅ Custom dashboards and widgets  
✅ Automated scheduled reports  
✅ Context-aware suggestions  
✅ Advanced analytics and profiling  
✅ Multi-format export  
✅ Complete REST API  

Happy analyzing! 🚀
