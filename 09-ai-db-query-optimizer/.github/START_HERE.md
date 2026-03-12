# Start Here — 5-Minute Setup

Get the AI Database Query Optimizer running in 5 minutes.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| PostgreSQL | 14+ | https://postgresql.org |
| Ollama | latest | https://ollama.com |

> **Skip PostgreSQL?** The app has a full Demo Mode that works without any database.

---

## Step 1 — Install Python dependencies

```bash
cd 09-ai-db-query-optimizer
pip install -r requirements.txt
```

---

## Step 2 — Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your database credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=demo_db
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

Leave Ollama settings as-is unless you're using a different model.

---

## Step 3 — (Optional) Set up the demo database

This creates a realistic e-commerce database with intentionally bad queries to demo the optimizer.

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE demo_db;"

# Load the schema and sample data (~2 million rows — takes 30-60 seconds)
psql -U postgres demo_db < demo/sample_db/setup_demo_db.sql
```

**Windows:** Use pgAdmin's query tool or the psql shell from the PostgreSQL installation folder.

---

## Step 4 — Start Ollama and pull the AI model

```bash
# Start Ollama (runs in background)
ollama serve

# In a new terminal, pull the model (one-time download ~2GB)
ollama pull llama3.2
```

---

## Step 5 — Run the dashboard

```bash
streamlit run app.py
```

Open your browser to: **http://localhost:8501**

---

## Step 6 — Try Demo Mode (no DB required)

If you don't have PostgreSQL set up yet:

1. Open the dashboard
2. In the left sidebar, click **"Enable Demo Mode"**
3. All 4 tabs work with realistic hardcoded data:
   - Slow Query Scanner: shows 847-query N+1 pattern, 3.1s query
   - N+1 Detector: pre-loaded with demo query log
   - Index Analyzer: shows sequential scan on `orders`
   - Cost Calculator: shows $2,400/year waste from one missing index

---

## Quick Reference

```bash
# Run app
streamlit run app.py

# Reset demo DB
psql -U postgres -c "DROP DATABASE IF EXISTS demo_db;"
psql -U postgres -c "CREATE DATABASE demo_db;"
psql -U postgres demo_db < demo/sample_db/setup_demo_db.sql

# Check Ollama status
ollama list

# Install specific model
ollama pull llama3.2
```

---

## Troubleshooting

**"psycopg2 not installed"**
```bash
pip install psycopg2-binary
```

**"Connection refused on port 5432"**
- Start PostgreSQL: `pg_ctl start` or open pgAdmin

**"Ollama not found"**
- Install from https://ollama.com
- On Windows, ensure Ollama is on PATH (restart terminal after install)

**"Model not found"**
```bash
ollama pull llama3.2
```

**AI analysis returns nothing**
- Check that `ollama serve` is running in a separate terminal
- Test: `ollama run llama3.2 "Hello"` — should respond within 30s

---

Next: see `IMPLEMENTATION_GUIDE.md` for the full 7-day build plan.
