# 🎬 Films Database Assistant

An intelligent AI agent that helps users explore a films database using natural language queries. Built with **OpenAI Function Calling**, the agent uses multiple tools to safely query data while maintaining privacy - your data never leaves your computer.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Function_Calling-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Project Overview

This is a **Data Insights Application** where an AI agent assists users in getting information from a database using natural language. The agent is built with proper **function calling** and includes multiple tools for querying data, getting statistics, and creating support tickets.

### Key Features

- 🤖 **AI Agent with Function Calling** - Uses OpenAI's function calling with 4 different tools
- 🔒 **Privacy First** - AI only sees query results, never the full dataset
- 📊 **Business Intelligence** - Dashboard with stats, charts, and visualizations
- 🎫 **Support System** - Integrated GitHub Issues for support tickets
- 🛡️ **Security** - Prevents dangerous operations (DELETE, DROP, UPDATE, etc.)
- 📝 **Logging** - All operations logged to console
- 💬 **Chat Interface** - Conversational UI with chat history

---

## 🏗️ Architecture

### Privacy Model

```
User Question: "Show top 10 highest rated movies"
    ↓
AI Agent: Uses function calling to determine which tool to use
    ↓
Tool Called: query_database(sql="SELECT title, rating FROM movies ORDER BY rating DESC LIMIT 10")
    ↓
Query Executes: Locally on your database
    ↓
Results: Only the 10 results are sent back to AI (not the full 600 movies!)
    ↓
AI Response: Formats and presents the results to user
```

**IMPORTANT**: The AI never sees your full dataset. It only receives:
- Database schema (table/column names)
- Query results (limited to 100 rows max per query)
- Aggregated statistics

### Function Calling Tools

The agent has access to 4 tools:

1. **`query_database`** - Execute SQL SELECT queries on the database
2. **`get_database_stats`** - Get overall database statistics
3. **`create_github_issue`** - Create support tickets in GitHub
4. **`get_sample_queries`** - Get example questions to try

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- (Optional) GitHub Personal Access Token for support tickets

### Step 1: Clone and Navigate

```bash
cd Capstone1
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:
- `streamlit` - Web interface
- `openai` - AI agent with function calling
- `pandas` - Data manipulation
- `plotly` - Interactive charts
- `requests` - GitHub API integration
- `python-dotenv` - Environment variables

### Step 3: Generate Database

```bash
python generate_database.py
```

This creates `films_data.db` with:
- **600 movies** (1990-2024)
- **20 directors** (Christopher Nolan, Martin Scorsese, Quentin Tarantino, etc.)
- **92 actors** (Tom Hanks, Meryl Streep, Leonardo DiCaprio, etc.)
- **8 genres** (Action, Drama, Comedy, Thriller, Sci-Fi, Horror, Romance, Adventure)

### Step 4: Configure Environment

Create a `.env` file (see `.env.example`):

```env
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional (for real GitHub support tickets)
GITHUB_TOKEN=ghp_your_github_token
GITHUB_REPO=username/repository
```

**Without GitHub configuration**, support tickets are logged locally.

### Step 5: Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📖 Usage Guide

### Getting Started

1. **Ask Questions** - Type natural language questions about movies
2. **View Results** - The agent uses function calling to query and present data
3. **Explore Charts** - Check the sidebar for visual insights
4. **Get Help** - Click "Contact Support" to create a support ticket

### Example Questions

Try these questions to explore the database:

- "What are the top 10 highest rated movies?"
- "Which director has made the most films?"
- "Show me all Christopher Nolan movies"
- "What's the total box office revenue by genre?"
- "List movies with rating above 9"
- "Who are the top 5 actors by number of films?"
- "What's the average rating for each genre?"
- "Show me action movies from 2020-2024"
- "Which studio has the highest total box office?"

### Agent Behavior

The AI agent will:
- ✅ Use appropriate tools based on your question
- ✅ Generate proper SQL queries with JOINs
- ✅ Format results in a readable way
- ✅ Suggest creating a support ticket if it encounters errors
- ❌ Never execute dangerous operations (DELETE, UPDATE, DROP)
- ❌ Never see your full dataset

---

## 📊 Database Schema

### Tables

**movies**
- `movie_id` (INTEGER, PRIMARY KEY)
- `title` (TEXT)
- `director_id` (INTEGER, FOREIGN KEY → directors)
- `lead_actor_id` (INTEGER, FOREIGN KEY → actors)
- `genre` (TEXT)
- `release_year` (INTEGER)
- `runtime_minutes` (INTEGER)
- `rating` (REAL, 0-10 scale)
- `box_office_millions` (REAL)
- `studio` (TEXT)

**directors**
- `director_id` (INTEGER, PRIMARY KEY)
- `director_name` (TEXT)
- `birth_year` (INTEGER)
- `nationality` (TEXT)

**actors**
- `actor_id` (INTEGER, PRIMARY KEY)
- `actor_name` (TEXT)
- `birth_year` (INTEGER)
- `nationality` (TEXT)

---

## 🛡️ Security Features

### Query Safety

The app includes multiple layers of security:

```python
DANGEROUS_KEYWORDS = ["DELETE", "DROP", "TRUNCATE", "ALTER", "UPDATE", "INSERT"]
```

- ✅ Only SELECT queries allowed
- ✅ Dangerous keywords blocked
- ✅ All queries validated before execution
- ✅ Results limited to 100 rows per query
- ✅ Full logging of all operations

### Blocked Operations

If someone tries to execute a dangerous query:

```sql
DELETE FROM movies  -- ❌ BLOCKED
DROP TABLE movies   -- ❌ BLOCKED
UPDATE movies       -- ❌ BLOCKED
```

The system will return: `🚫 Security block: DELETE operations not allowed`

---

## 📝 Console Logging

All operations are logged to the console for monitoring:

```
2025-11-13 10:30:15 - INFO - === Films Data Insights App Started ===
2025-11-13 10:30:22 - INFO - [AGENT] Processing question: What are the top 10 highest rated movies?
2025-11-13 10:30:22 - INFO - [AGENT] Iteration 1
2025-11-13 10:30:23 - INFO - [AGENT] Calling tool: query_database
2025-11-13 10:30:23 - INFO - [TOOL] query_database called with SQL: SELECT title, rating FROM movies ORDER BY rating DESC LIMIT 10
2025-11-13 10:30:23 - INFO - [TOOL] Query successful: 10 rows
2025-11-13 10:30:24 - INFO - [AGENT] No tool calls, returning response
```

---

## 🎫 Support Ticket System

### GitHub Integration

When configured with GitHub credentials, the app can create real support tickets:

1. Click "Contact Support" button
2. Fill in issue title and description
3. Submit - creates a GitHub Issue with labels `support` and `data-insights-app`

### Local Fallback

Without GitHub configuration, tickets are logged locally with format:
```
TICKET-20251113103045
```

### Agent Auto-Suggest

The agent will proactively suggest creating a support ticket when:
- Queries fail repeatedly
- User expresses confusion
- User explicitly asks for help

---

## 📸 Screenshots

### Main Interface

![Main Interface](screenshots/main-interface.png)
*Chat interface with sample questions and database statistics*

### Query Results

![Query Results](screenshots/query-results.png)
*Agent using function calling to query and display movie data*

### Charts & Visualizations

![Charts](screenshots/charts-visualization.png)
*Genre distribution and top directors visualizations*

### Support Ticket Creation

![Support](screenshots/support-ticket.png)
*Creating a support ticket through GitHub integration*

### Console Logging

![Logs](screenshots/console-logs.png)
*All operations logged to console for monitoring*

---

## ✅ Requirements Checklist

### Functional Requirements

- ✅ **Agent assists with database queries** - Natural language to SQL
- ✅ **Data privacy** - Only query results sent to AI, not full dataset
- ✅ **Business information UI** - Dashboard with stats, charts, sample queries
- ✅ **Console logging** - All operations logged
- ✅ **Support ticket system** - GitHub Issues integration with fallback
- ✅ **Function calling** - Uses OpenAI function calling with 4 tools
- ✅ **Security** - Blocks dangerous operations (DELETE, DROP, etc.)

### Non-Functional Requirements

- ✅ **Python** - Built with Python 3.8+
- ✅ **Streamlit UI** - Modern chat interface
- ✅ **At least 2 tools** - Actually implements 4 different tools
- ✅ **500+ rows** - Database has 600 movies
- ✅ **Complete README** - Full documentation with usage examples
- ✅ **Safety features** - Multiple security layers

---

## 🎓 Technical Details

### Tools Implementation

Each tool is properly defined for OpenAI function calling:

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Execute a SQL SELECT query...",
            "parameters": {...}
        }
    },
    # ... 3 more tools
]
```

### Agent Loop

The agent implements an agentic loop:

1. Receives user question
2. Calls OpenAI with available tools
3. Executes tool calls
4. Sends results back to AI
5. Returns final formatted response

Maximum 5 iterations to prevent infinite loops.

---

## 🔧 Troubleshooting

### Database Not Found

```bash
python generate_database.py
```

### OpenAI API Error

Check your `.env` file has valid `OPENAI_API_KEY`

### GitHub Tickets Not Working

GitHub integration is optional. Tickets will be logged locally if:
- `GITHUB_TOKEN` not set
- `GITHUB_REPO` not set
- GitHub API returns error

---

## 📦 Project Structure

```
Capstone1/
├── app.py                  # Main application with agent logic
├── generate_database.py    # Database generation script
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Your configuration (create this)
├── films_data.db          # SQLite database (generated)
├── README.md              # This file
└── screenshots/           # Usage screenshots
    ├── main-interface.png
    ├── query-results.png
    ├── charts-visualization.png
    ├── support-ticket.png
    └── console-logs.png
```

---

## 🚀 Future Enhancements

Potential improvements:
- Add more visualization types
- Export results to CSV/Excel
- Voice input support
- Multi-table complex queries
- Query history and favorites
- Deploy to Hugging Face Spaces

---

## 📄 License

MIT License - feel free to use and modify

---

## 👤 Author

Built as part of Generative AI course Capstone Project

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 and function calling API
- Streamlit for the amazing web framework
- Plotly for interactive visualizations

---

**Built with Python • Streamlit • OpenAI Function Calling • SQLite • Plotly**
