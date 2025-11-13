"""
Data Insights App - Simple AI Database Assistant
AI generates SQL, but NEVER sees the actual data
"""

import streamlit as st
import sqlite3
import pandas as pd
import logging
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os

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
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DB_PATH = "films_data.db"

# Safety: Blocked keywords
DANGEROUS_KEYWORDS = ["DELETE", "DROP", "TRUNCATE", "ALTER", "UPDATE", "INSERT"]


def is_safe_query(query):
    """Check if query is safe (SELECT only)"""
    query_upper = query.upper().strip()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in query_upper:
            return False, f"Blocked: {keyword} not allowed"
    if not query_upper.startswith("SELECT"):
        return False, "Only SELECT allowed"
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


def generate_sql(user_question):
    """
    LLM generates SQL based on question and schema.
    LLM NEVER sees actual data, only schema.
    """
    logger.info(f"User question: {user_question}")

    schema = get_database_schema()

    system_prompt = f"""You are a SQL expert. Generate ONLY a SQL query, nothing else.

{schema}

IMPORTANT Rules:
- Return ONLY the SQL query, no explanation
- Only SELECT queries
- Use proper SQL syntax for SQLite
- No DELETE, UPDATE, INSERT, DROP
- Add LIMIT if query could return many rows

CRITICAL: Always JOIN tables to show NAMES, not just IDs:
- Show product_name (not just product_id)
- Show customer_name (not just customer_id)
- Use descriptive column aliases (e.g., "total_sales", "product_name")

Good Examples:
User: "top 10 highest rated movies"
You: SELECT title, rating FROM movies ORDER BY rating DESC LIMIT 10

User: "movies by Christopher Nolan"
You: SELECT m.title, m.release_year, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name = 'Christopher Nolan' ORDER BY m.release_year

User: "total box office by genre"
You: SELECT genre, SUM(box_office_millions) as total_box_office FROM movies GROUP BY genre ORDER BY total_box_office DESC"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0
        )

        sql_query = response.choices[0].message.content.strip()

        # Clean up query (remove markdown)
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        logger.info(f"Generated SQL: {sql_query}")
        return sql_query

    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return None


def execute_query(sql_query):
    """
    Execute query locally.
    Results go DIRECTLY to user, LLM never sees them.
    """
    logger.info(f"Executing: {sql_query}")

    # Safety check
    is_safe, error_msg = is_safe_query(sql_query)
    if not is_safe:
        logger.error(f"Blocked query: {error_msg}")
        return None, error_msg

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        logger.info(f"Query successful: {len(df)} rows returned")
        return df, None

    except Exception as e:
        logger.error(f"Query error: {e}")
        return None, str(e)


def create_support_ticket(title, description):
    """Create support ticket (logged locally)"""
    ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Support ticket created: {ticket_id}")
    logger.info(f"Title: {title}")
    logger.info(f"Description: {description}")
    return ticket_id


def main():
    st.set_page_config(page_title="Data Insights", page_icon="📊", layout="wide")

    st.title("🎬 Films Database Assistant")
    st.caption("🔒 AI generates SQL but NEVER sees your data")

    if not OPENAI_API_KEY:
        st.error("⚠️ Set OPENAI_API_KEY in .env file")
        return

    # Sidebar
    st.sidebar.success("🔒 **100% Data Privacy**\n\nAI only sees schema (table names, column names).\nActual data NEVER sent to AI.")

    st.sidebar.header("📋 Database Info")

    # Show film database stats
    try:
        conn = sqlite3.connect(DB_PATH)

        # Get counts
        movies_count = pd.read_sql_query("SELECT COUNT(*) as count FROM movies", conn).iloc[0]['count']
        directors_count = pd.read_sql_query("SELECT COUNT(*) as count FROM directors", conn).iloc[0]['count']
        actors_count = pd.read_sql_query("SELECT COUNT(*) as count FROM actors", conn).iloc[0]['count']

        st.sidebar.metric("Movies", movies_count)
        st.sidebar.metric("Directors", directors_count)
        st.sidebar.metric("Actors", actors_count)

        # Average rating
        avg_rating = pd.read_sql_query("SELECT AVG(rating) as avg FROM movies", conn).iloc[0]['avg']
        st.sidebar.metric("Average Rating", f"{avg_rating:.1f}/10")

        # Total box office
        total_box = pd.read_sql_query("SELECT SUM(box_office_millions) as total FROM movies", conn).iloc[0]['total']
        st.sidebar.metric("Total Box Office", f"${total_box:,.0f}M")

        conn.close()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

    # Sample questions
    st.sidebar.header("💡 Try These")
    samples = [
        "Show top 10 highest rated movies",
        "Which director has made the most movies?",
        "List all movies by Christopher Nolan",
        "What's the total box office by genre?",
        "Show movies with rating above 9",
        "Who are the top 5 actors by number of films?",
    ]

    for q in samples:
        if st.sidebar.button(q, key=q):
            st.session_state.current_question = q
            st.rerun()

    # Main area
    st.header("Ask Questions")

    # Input
    col1, col2 = st.columns([4, 1])
    with col1:
        user_question = st.text_input(
            "Your question:",
            value=st.session_state.get('current_question', ''),
            placeholder="Example: What is our total revenue?"
        )
    with col2:
        st.write("")
        st.write("")
        ask_button = st.button("🔍 Ask", type="primary")

    if ask_button and user_question:
        st.session_state.current_question = ""

        # Step 1: Generate SQL
        with st.spinner("🤖 Generating SQL query..."):
            sql_query = generate_sql(user_question)

        if not sql_query:
            st.error("Failed to generate SQL query")
            return

        # Show generated SQL
        st.subheader("📝 Generated SQL")
        st.code(sql_query, language="sql")

        # Step 2: Execute locally
        with st.spinner("⚡ Executing query..."):
            df, error = execute_query(sql_query)

        if error:
            st.error(f"❌ Error: {error}")
            st.info("💡 Try rephrasing your question or click 'Contact Support'")
        elif df is not None:
            # Step 3: Show results DIRECTLY to user (LLM never sees this!)
            st.subheader("📊 Results")

            if len(df) == 0:
                st.info("No results found")
            elif len(df) == 1 and len(df.columns) == 1:
                # Single value result
                value = df.iloc[0, 0]
                col_name = df.columns[0].replace('_', ' ').title()
                st.metric(col_name, f"{value:,.2f}" if isinstance(value, (int, float)) else value)
            else:
                # Table result - format columns nicely
                df.columns = [col.replace('_', ' ').title() for col in df.columns]
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"✓ Found {len(df)} result(s)")

    # Support button
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🎫 Contact Support"):
            ticket_id = create_support_ticket(
                "User requested support",
                f"Question: {user_question if user_question else 'N/A'}"
            )
            st.success(f"✅ Ticket created: {ticket_id}")

    # Footer
    st.markdown("---")
    st.markdown("*🔒 Privacy: AI only generates SQL. Your data stays on your computer.*")


if __name__ == "__main__":
    logger.info("=== Data Insights App Started ===")
    main()
