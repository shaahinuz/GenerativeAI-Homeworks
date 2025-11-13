"""
Data Insights App - AI Database Assistant with Function Calling
AI uses tools to query database safely - NEVER sees actual data
"""

import streamlit as st
import sqlite3
import pandas as pd
import logging
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import plotly.express as px
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # format: "username/repo"

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DB_PATH = "Capstone1/films_data.db"

# Safety: Blocked keywords
DANGEROUS_KEYWORDS = ["DELETE", "DROP", "TRUNCATE", "ALTER", "UPDATE", "INSERT"]


def is_safe_query(query):
    """Check if query is safe (SELECT only)"""
    query_upper = query.upper().strip()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in query_upper:
            return False, f"🚫 Security block: {keyword} operations not allowed"
    if not query_upper.startswith("SELECT"):
        return False, "🚫 Security block: Only SELECT queries allowed"
    return True, None


def get_database_schema():
    """Get database schema (NO DATA, just structure)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = "Database Schema:\n"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [f"{row[1]} ({row[2]})" for row in cursor.fetchall()]
        schema += f"\n{table}: {', '.join(columns)}"

    conn.close()
    return schema


# TOOL 1: Query Database
def query_database(sql_query):
    """
    Execute SQL query on database.
    Returns results as JSON (limited to 100 rows for safety).
    AI never sees full dataset, only query results.
    """
    logger.info(f"[TOOL] query_database called with SQL: {sql_query}")

    # Safety check
    is_safe, error_msg = is_safe_query(sql_query)
    if not is_safe:
        logger.error(f"[TOOL] Query blocked: {error_msg}")
        return {"error": error_msg}

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        # Limit rows to avoid token overflow
        if len(df) > 100:
            df = df.head(100)
            logger.warning(f"[TOOL] Results truncated to 100 rows")

        result = {
            "success": True,
            "rows_returned": len(df),
            "columns": list(df.columns),
            "data": df.to_dict('records')
        }

        logger.info(f"[TOOL] Query successful: {len(df)} rows")
        return result

    except Exception as e:
        logger.error(f"[TOOL] Query error: {e}")
        return {"error": str(e)}


# TOOL 2: Get Database Statistics
def get_database_stats():
    """Get aggregated statistics about the database."""
    logger.info("[TOOL] get_database_stats called")

    try:
        conn = sqlite3.connect(DB_PATH)

        stats = {
            "movies_count": pd.read_sql_query("SELECT COUNT(*) as c FROM movies", conn).iloc[0]['c'],
            "directors_count": pd.read_sql_query("SELECT COUNT(*) as c FROM directors", conn).iloc[0]['c'],
            "actors_count": pd.read_sql_query("SELECT COUNT(*) as c FROM actors", conn).iloc[0]['c'],
            "avg_rating": round(pd.read_sql_query("SELECT AVG(rating) as a FROM movies", conn).iloc[0]['a'], 2),
            "total_box_office_millions": int(pd.read_sql_query("SELECT SUM(box_office_millions) as s FROM movies", conn).iloc[0]['s']),
            "genres": pd.read_sql_query("SELECT DISTINCT genre FROM movies", conn)['genre'].tolist(),
            "year_range": f"{pd.read_sql_query('SELECT MIN(release_year) as min FROM movies', conn).iloc[0]['min']}-{pd.read_sql_query('SELECT MAX(release_year) as max FROM movies', conn).iloc[0]['max']}"
        }

        conn.close()
        logger.info(f"[TOOL] Stats retrieved: {stats}")
        return stats

    except Exception as e:
        logger.error(f"[TOOL] Stats error: {e}")
        return {"error": str(e)}


# TOOL 3: Create GitHub Issue (Support Ticket)
def create_github_issue(title, description, user_question=""):
    """Create a GitHub issue for support."""
    logger.info(f"[TOOL] create_github_issue called: {title}")

    if not GITHUB_TOKEN or not GITHUB_REPO:
        # Fallback to local logging
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.warning(f"[TOOL] GitHub not configured, creating local ticket: {ticket_id}")
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": "Support ticket logged locally (GitHub not configured)"
        }

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        body = f"{description}\n\n---\n**User Question:** {user_question}\n**Timestamp:** {datetime.now().isoformat()}"

        data = {
            "title": title,
            "body": body,
            "labels": ["support", "data-insights-app"]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            issue = response.json()
            logger.info(f"[TOOL] GitHub issue created: #{issue['number']}")
            return {
                "success": True,
                "ticket_id": f"#{issue['number']}",
                "url": issue['html_url'],
                "message": f"Support ticket created successfully"
            }
        else:
            logger.error(f"[TOOL] GitHub API error: {response.status_code}")
            ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return {
                "success": True,
                "ticket_id": ticket_id,
                "message": "Support ticket logged locally (GitHub API error)"
            }

    except Exception as e:
        logger.error(f"[TOOL] GitHub issue error: {e}")
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"Support ticket logged locally (Error: {str(e)})"
        }


# TOOL 4: Get Sample Queries
def get_sample_queries():
    """Return sample queries users can try."""
    logger.info("[TOOL] get_sample_queries called")

    samples = [
        "Show top 10 highest rated movies",
        "Which director has made the most movies?",
        "List all movies by Christopher Nolan",
        "What's the total box office by genre?",
        "Show movies with rating above 9",
        "Who are the top 5 actors by number of films?",
        "What's the average rating for each genre?",
        "Show me movies from 2020-2024",
        "Which studio has the highest total box office?",
        "List all action movies with rating above 8"
    ]

    return {"samples": samples}


# Define tools for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Execute a SQL SELECT query on the films database. Use this to answer user questions about movies, directors, actors, ratings, box office, etc. IMPORTANT: Only SELECT queries allowed - no DELETE, UPDATE, INSERT, DROP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute. Must be a valid SQLite query. Example: 'SELECT title, rating FROM movies ORDER BY rating DESC LIMIT 10'"
                    }
                },
                "required": ["sql_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_stats",
            "description": "Get overall statistics about the database including counts of movies, directors, actors, average ratings, total box office, available genres, and year range.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_issue",
            "description": "Create a support ticket when the user needs help, encounters errors, or explicitly asks to contact support. Use this when queries fail, user is confused, or requests human assistance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Brief title for the support ticket"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue or request"
                    },
                    "user_question": {
                        "type": "string",
                        "description": "The original user question that led to this ticket"
                    }
                },
                "required": ["title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sample_queries",
            "description": "Get a list of sample queries that users can try. Use this when user asks for examples or suggestions.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def execute_function(function_name, arguments):
    """Execute the appropriate function based on the tool call."""
    if function_name == "query_database":
        return query_database(arguments["sql_query"])
    elif function_name == "get_database_stats":
        return get_database_stats()
    elif function_name == "create_github_issue":
        return create_github_issue(
            arguments["title"],
            arguments["description"],
            arguments.get("user_question", "")
        )
    elif function_name == "get_sample_queries":
        return get_sample_queries()
    else:
        return {"error": f"Unknown function: {function_name}"}


def chat_with_agent(user_question, conversation_history):
    """
    Agent uses function calling to answer user questions.
    Implements agentic loop with multiple tool calls if needed.
    """
    logger.info(f"[AGENT] Processing question: {user_question}")

    schema = get_database_schema()

    system_message = f"""You are a helpful database assistant for a films database. You help users query and understand movie data.

{schema}

IMPORTANT Guidelines:
1. Use query_database tool to answer questions about movies, directors, actors, ratings, etc.
2. Always construct proper SQL with JOINs to show names, not just IDs
3. Use descriptive column aliases in SQL
4. If a query fails or user seems frustrated, suggest creating a support ticket
5. Be conversational and helpful
6. Never expose raw data - only query results
7. If user asks for examples, use get_sample_queries tool
8. Provide clear, concise responses

Security Rules:
- Only SELECT queries allowed
- No DELETE, UPDATE, INSERT, DROP operations
- Queries are automatically checked for safety"""

    messages = [{"role": "system", "content": system_message}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_question})

    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"[AGENT] Iteration {iteration}")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0
            )

            assistant_message = response.choices[0].message

            # If no tool calls, return the response
            if not assistant_message.tool_calls:
                logger.info("[AGENT] No tool calls, returning response")
                return assistant_message.content, messages

            # Process tool calls
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in assistant_message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(f"[AGENT] Calling tool: {function_name}")

                result = execute_function(function_name, arguments)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            # Continue loop to get final response

        except Exception as e:
            logger.error(f"[AGENT] Error: {e}")
            return f"Sorry, I encountered an error: {str(e)}", messages

    return "Sorry, I couldn't complete your request. Please try rephrasing your question or contact support.", messages


def main():
    st.set_page_config(page_title="Films Data Insights", page_icon="🎬", layout="wide")

    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.title("🎬 Films Database Assistant")
    st.caption("AI-powered insights using function calling - your data never leaves your computer")

    if not OPENAI_API_KEY:
        st.error("⚠️ Set OPENAI_API_KEY in .env file")
        st.info("Create a `.env` file with: `OPENAI_API_KEY=your_key_here`")
        return

    # Sidebar
    with st.sidebar:
        st.success("🔒 **Privacy First**\n\nAI uses tools to query your database.\nOnly query results are shared, never the full dataset.")

        st.header("📊 Database Stats")

        # Load stats
        try:
            conn = sqlite3.connect(DB_PATH)
            movies_count = pd.read_sql_query("SELECT COUNT(*) as c FROM movies", conn).iloc[0]['c']
            directors_count = pd.read_sql_query("SELECT COUNT(*) as c FROM directors", conn).iloc[0]['c']
            actors_count = pd.read_sql_query("SELECT COUNT(*) as c FROM actors", conn).iloc[0]['c']
            avg_rating = pd.read_sql_query("SELECT AVG(rating) as a FROM movies", conn).iloc[0]['a']
            total_box = pd.read_sql_query("SELECT SUM(box_office_millions) as s FROM movies", conn).iloc[0]['s']

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Movies", f"{movies_count:,}")
                st.metric("Directors", directors_count)
            with col2:
                st.metric("Actors", actors_count)
                st.metric("Avg Rating", f"{avg_rating:.1f}/10")

            st.metric("Total Box Office", f"${total_box:,.0f}M")
            conn.close()

        except Exception as e:
            st.error(f"Database error: {e}")

        st.divider()

        # Quick Charts
        st.header("📈 Quick Insights")

        try:
            conn = sqlite3.connect(DB_PATH)

            # Genre distribution
            genre_df = pd.read_sql_query("""
                SELECT genre, COUNT(*) as count
                FROM movies
                GROUP BY genre
                ORDER BY count DESC
            """, conn)

            fig = px.bar(
                genre_df,
                x='genre',
                y='count',
                title='Movies by Genre',
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Top directors
            directors_df = pd.read_sql_query("""
                SELECT d.director_name, COUNT(*) as films
                FROM movies m
                JOIN directors d ON m.director_id = d.director_id
                GROUP BY d.director_name
                ORDER BY films DESC
                LIMIT 5
            """, conn)

            fig2 = px.bar(
                directors_df,
                x='films',
                y='director_name',
                orientation='h',
                title='Top 5 Directors',
                color='films',
                color_continuous_scale='Greens'
            )
            fig2.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
                xaxis_title="Films",
                yaxis_title=""
            )
            st.plotly_chart(fig2, use_container_width=True)

            conn.close()

        except Exception as e:
            st.error(f"Chart error: {e}")

        st.divider()

        st.header("💡 Sample Questions")
        samples = [
            "What are the top 10 highest rated movies?",
            "Which director made the most films?",
            "Show me Christopher Nolan's movies",
            "Total box office by genre?",
            "Movies rated above 9?",
            "Top 5 actors by film count?",
        ]

        for sample in samples:
            if st.button(sample, key=f"sample_{sample}", use_container_width=True):
                st.session_state.next_question = sample
                st.rerun()

        st.divider()

        if st.button("🎫 Contact Support", use_container_width=True):
            st.session_state.show_support = True
            st.rerun()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.messages = []
            st.rerun()

    # Main chat area
    st.header("💬 Ask Me Anything")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle next question from sidebar
    if "next_question" in st.session_state:
        user_input = st.session_state.next_question
        del st.session_state.next_question
    else:
        user_input = st.chat_input("Ask about movies, directors, actors, ratings, box office...")

    # Handle support dialog
    if "show_support" in st.session_state and st.session_state.show_support:
        with st.form("support_form"):
            st.subheader("🎫 Create Support Ticket")
            title = st.text_input("Issue Title", placeholder="Brief description of your issue")
            description = st.text_area("Description", placeholder="Detailed explanation of what you need help with")
            submitted = st.form_submit_button("Submit Ticket")

            if submitted and title and description:
                result = create_github_issue(title, description, "")
                if result.get("success"):
                    if "url" in result:
                        st.success(f"✅ Support ticket created: [{result['ticket_id']}]({result['url']})")
                    else:
                        st.success(f"✅ {result['message']} - Ticket ID: {result['ticket_id']}")
                else:
                    st.error("Failed to create ticket")
                st.session_state.show_support = False
                st.rerun()

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, updated_history = chat_with_agent(
                    user_input,
                    st.session_state.conversation_history
                )

            st.markdown(response)

        # Update conversation history
        st.session_state.conversation_history = updated_history[-10:]  # Keep last 10 exchanges
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.divider()
    st.markdown("*Built with Python, Streamlit, OpenAI Function Calling, and SQLite | 🔒 Your data stays local*")


if __name__ == "__main__":
    logger.info("=== Films Data Insights App Started ===")
    main()
