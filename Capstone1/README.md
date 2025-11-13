# 🎬 Films Database Assistant

AI-powered database query tool for films data. **AI NEVER sees your actual data.**

---

## 🔒 Privacy Model

```
User asks: "Show top 10 highest rated movies"
    ↓
AI sees: Only schema (table names, column names)
    ↓
AI generates: SQL query
    ↓
Query executes: On your computer
    ↓
Results show: Directly to you
    ↓
AI NEVER SEES: The actual movie data
```

---

## 🚀 Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate films database
python generate_database.py

# 3. Set API key in .env
OPENAI_API_KEY=your_key_here

# 4. Run app
streamlit run app.py
```

---

## 📊 Database

- **600 movies** (1990-2024)
- **20 directors** (Nolan, Scorsese, Tarantino, etc.)
- **92 actors** (Tom Hanks, Meryl Streep, Zendaya, etc.)
- **8 genres** (Action, Drama, Comedy, etc.)
- Data includes: titles, ratings, box office, runtime

**Tables:**
- `movies` - Movie details with foreign keys
- `directors` - Director information
- `actors` - Actor information

---

## ✨ Features

1. **AI SQL Generation** - Natural language to SQL
2. **100% Data Privacy** - AI only sees schema
3. **Safety Features** - SELECT only, no DELETE/UPDATE
4. **Console Logging** - All operations logged
5. **Support Tickets** - Create tickets for help

---

## 💡 Example Questions

- "Show top 10 highest rated movies"
- "Which director has made the most movies?"
- "List all movies by Christopher Nolan"
- "What's the total box office by genre?"
- "Show movies with rating above 9"
- "Who are the top 5 actors by number of films?"

---

## 🔐 Safety

- Only SELECT queries allowed
- Dangerous operations blocked (DELETE, DROP, etc.)
- All queries logged to console
- Data never sent to OpenAI

---

## 📁 Files

- `app.py` - Main application
- `generate_database.py` - Creates films database
- `films_data.db` - SQLite database (600 movies)
- `requirements.txt` - Dependencies
- `.env` - Your API key

---

## 🎯 Requirements Met

✅ Agent assists with database queries
✅ Data doesn't go to LLM (only schema)
✅ UI shows business info (sidebar stats)
✅ Console logging enabled
✅ Support ticket system
✅ Function calling (no data exposure)
✅ Safety features (SELECT only)
✅ 600 rows (> 500 requirement)
✅ Python + Streamlit
✅ Simple and clear

---

**Built with Python, Streamlit, OpenAI GPT-4, SQLite**
