"""
CDC Diabetes Health Data Explorer

A friendly tool that lets you ask questions about real CDC health survey data.
We use AI to help you explore 253,680 patient records from the 2014 BRFSS survey.
The cool part? Your questions get turned into database queries automatically!
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

# Set up logging so we can see what's happening behind the scenes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load your OpenAI API key from the .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Where our database lives
DB_PATH = "diabetes_health.db"

# We block these database operations to keep the data safe
# (we only want to read data, not modify or delete it)
DANGEROUS_KEYWORDS = ["DELETE", "DROP", "TRUNCATE", "ALTER", "UPDATE", "INSERT"]


def is_safe_query(query):
    """
    Check if a database query is safe to run.
    We only allow SELECT queries to keep the data protected.
    """
    query_upper = query.upper().strip()

    # Check for dangerous operations that could modify or delete data
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in query_upper:
            logger.warning(f"Whoa! Blocked a dangerous operation: {keyword}")
            return False, f"Sorry, {keyword} operations aren't allowed for safety reasons"

    # Make sure it's a SELECT query (read-only)
    if not query_upper.startswith("SELECT"):
        logger.warning("Blocked a non-SELECT query")
        return False, "We can only run SELECT queries to keep the data safe"

    return True, None


def get_database_schema():
    """
    Get the structure of our database (what tables and columns exist).

    Important: This only returns the database structure, NOT any actual patient data.
    The AI uses this to understand what questions it can answer.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        schema = "Database Schema:\n\n"

        # Find all the tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # For each table, list its columns
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema += f"\nTable: {table}\n"
            schema += "Columns:\n"
            for col in columns:
                schema += f"  - {col[1]} ({col[2]})\n"

        # Also check if there are any pre-made views (like summary tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]

        if views:
            schema += "\nViews (pre-made summaries):\n"
            for view in views:
                schema += f"  - {view}\n"

        conn.close()
        logger.info("Successfully got the database structure")
        return schema

    except Exception as e:
        logger.error(f"Oops! Couldn't get the database structure: {e}")
        return None


def execute_sql_query(sql_query):
    """
    Run a database query and return the results.
    This function is called by the AI when it needs to get data.
    """
    logger.info(f"Running query: {sql_query}")

    # First, make sure the query is safe to run
    is_safe, error_msg = is_safe_query(sql_query)
    if not is_safe:
        logger.error(f"Query blocked for safety: {error_msg}")
        return json.dumps({"error": error_msg, "blocked": True})

    try:
        # Connect to the database and run the query
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        # Package up the results
        result = {
            "success": True,
            "rows": len(df),
            "data": df.to_dict('records')[:100]  # We limit to 100 rows for display
        }

        logger.info(f"Query worked! Got {len(df)} rows")
        return json.dumps(result)

    except Exception as e:
        logger.error(f"Query failed: {e}")
        return json.dumps({"error": str(e), "success": False})


def get_database_statistics():
    """
    Get high-level statistics about the entire database.
    This gives a quick overview without showing individual patient records.
    """
    logger.info("Getting overall database statistics")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        stats = {}

        # Count total patients
        cursor.execute("SELECT COUNT(*) FROM patient_health_data")
        stats['total_patients'] = cursor.fetchone()[0]

        # Count how many have diabetes
        cursor.execute("SELECT SUM(Diabetes_binary) FROM patient_health_data")
        diabetic_count = cursor.fetchone()[0]
        stats['diabetic_patients'] = diabetic_count
        stats['diabetes_rate_pct'] = round(diabetic_count / stats['total_patients'] * 100, 2)

        # Calculate average BMI
        cursor.execute("SELECT AVG(BMI) FROM patient_health_data")
        stats['avg_bmi'] = round(cursor.fetchone()[0], 1)

        # Calculate high blood pressure rate
        cursor.execute("SELECT SUM(HighBP) FROM patient_health_data")
        high_bp_count = cursor.fetchone()[0]
        stats['high_bp_rate_pct'] = round(high_bp_count / stats['total_patients'] * 100, 1)

        # Calculate smoker rate
        cursor.execute("SELECT SUM(Smoker) FROM patient_health_data")
        smoker_count = cursor.fetchone()[0]
        stats['smoker_rate_pct'] = round(smoker_count / stats['total_patients'] * 100, 1)

        conn.close()

        logger.info(f"Got stats for {stats['total_patients']:,} patients")
        return json.dumps(stats)

    except Exception as e:
        logger.error(f"Couldn't get statistics: {e}")
        return json.dumps({"error": str(e)})


def create_support_ticket(issue_description, user_question=""):
    """
    Create a support ticket when someone needs help.
    This logs all the details so we can follow up.
    """
    ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info("=" * 50)
    logger.info("NEW SUPPORT TICKET")
    logger.info(f"Ticket ID: {ticket_id}")
    logger.info(f"Issue: {issue_description}")
    if user_question:
        logger.info(f"Original Question: {user_question}")
    logger.info(f"Created: {datetime.now()}")
    logger.info("=" * 50)

    return json.dumps({
        "ticket_id": ticket_id,
        "status": "created",
        "message": "Your support ticket has been created and logged for review."
    })


# Define what tools the AI can use
# These are like giving the AI superpowers to access the database
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Run a database query to get specific health data. Use this when you need detailed information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "A SELECT query to run on the database"
                    }
                },
                "required": ["sql_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_statistics",
            "description": "Get a quick overview of the database - total patients, diabetes rates, average BMI, etc.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket when you can't help or the user needs human assistance",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_description": {
                        "type": "string",
                        "description": "What's the problem or what help is needed"
                    },
                    "user_question": {
                        "type": "string",
                        "description": "What the user originally asked"
                    }
                },
                "required": ["issue_description"]
            }
        }
    }
]


# Connect the tool names to our actual Python functions
available_functions = {
    "execute_sql_query": execute_sql_query,
    "get_database_statistics": get_database_statistics,
    "create_support_ticket": create_support_ticket
}


def process_user_query(user_question):
    """
    Process a user's question and get an AI-powered answer.
    The AI will automatically decide which tools to use.
    """
    logger.info(f"Processing question: {user_question}")

    # Get the database structure (but not the actual data)
    schema = get_database_schema()
    if not schema:
        return None, "Sorry, I couldn't access the database structure right now."

    system_prompt = f"""You're a friendly health data assistant helping people explore CDC diabetes survey data.

{schema}

What you're working with:
- Real survey data from the CDC (2014 BRFSS)
- 253,680 actual patient responses
- 21 different health indicators

IMPORTANT - How to read the data:

Binary fields (0 or 1):
- Diabetes_binary: 0 = no diabetes, 1 = has diabetes or prediabetes
- HighBP: 1 = has high blood pressure, 0 = does not
- HighChol: 1 = has high cholesterol, 0 = does not
- Smoker: 1 = current smoker, 0 = not a smoker
- PhysActivity: 1 = physically active, 0 = not active
- Sex: 0 = female, 1 = male

Age categories (CRITICAL - Age is NOT actual age, it's a category number):
- Age = 1: 18-24 years old
- Age = 2: 25-29 years old
- Age = 3: 30-34 years old
- Age = 4: 35-39 years old
- Age = 5: 40-44 years old
- Age = 6: 45-49 years old
- Age = 7: 50-54 years old
- Age = 8: 55-59 years old
- Age = 9: 60-64 years old
- Age = 10: 65-69 years old
- Age = 11: 70-74 years old
- Age = 12: 75-79 years old
- Age = 13: 80+ years old

Examples of age queries:
- "under 30" means Age IN (1, 2)
- "over 65" means Age IN (10, 11, 12, 13)
- "between 40 and 60" means Age IN (5, 6, 7, 8, 9)
- "in their 50s" means Age IN (7, 8)

Other numeric fields:
- BMI: body mass index (typical range: 15-50, higher = more overweight)
- GenHlth: general health rating (1 = excellent, 2 = very good, 3 = good, 4 = fair, 5 = poor)
- MentHlth: number of days with poor mental health in past 30 days (0-30)
- PhysHlth: number of days with poor physical health in past 30 days (0-30)

How to help:
- Use execute_sql_query when you need specific data
- Use get_database_statistics for quick overviews
- Use create_support_ticket if you can't help
- Always add LIMIT to queries that might return lots of rows
- When querying Age, ALWAYS use the category numbers (1-13), never use actual age numbers
- Explain your findings in plain English, converting Age categories back to age ranges"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    try:
        # Ask the AI what to do
        logger.info("Asking AI how to answer this...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Sometimes the AI can answer without using any tools
        if not tool_calls:
            logger.info("AI answered directly without tools")
            return None, response_message.content

        # The AI wants to use some tools - let's run them
        messages.append(response_message)
        executed_tools = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            logger.info(f"AI is calling: {function_name}")
            logger.info(f"  With arguments: {function_args}")

            # Run the function the AI requested
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args)

            # Keep track of what we did
            executed_tools.append({
                "name": function_name,
                "args": function_args,
                "result": function_response
            })

            # Send the results back to the AI
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response
            })

        # Now get the AI's final answer based on the tool results
        logger.info("Getting AI's final answer...")
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        final_message = final_response.choices[0].message.content
        logger.info("Query processing complete")

        return executed_tools, final_message

    except Exception as e:
        logger.error(f"Something went wrong: {e}")
        return None, f"Sorry, I ran into a problem: {str(e)}"


def main():
    st.set_page_config(
        page_title="CDC Diabetes Data Explorer",
        page_icon="🔬",
        layout="wide"
    )

    st.title("CDC Diabetes Data Explorer")
    st.caption("Ask questions about real CDC health survey data from 2014 (253,680 patient responses)")

    if not OPENAI_API_KEY:
        st.error("Missing OpenAI API key")
        st.info("Create a `.env` file and add: `OPENAI_API_KEY=your_key_here`\n\nGet a key at https://platform.openai.com/api-keys")
        return

    # Sidebar with quick info
    with st.sidebar:
        st.header("Quick Stats")

        # Show a snapshot of the data
        try:
            conn = sqlite3.connect(DB_PATH)

            total = pd.read_sql_query("SELECT COUNT(*) as c FROM patient_health_data", conn).iloc[0]['c']
            st.metric("Total Patients", f"{total:,}")

            diabetic = pd.read_sql_query("SELECT SUM(Diabetes_binary) as c FROM patient_health_data", conn).iloc[0]['c']
            st.metric("With Diabetes", f"{diabetic:,}", f"{diabetic/total*100:.1f}%")

            avg_bmi = pd.read_sql_query("SELECT AVG(BMI) as a FROM patient_health_data", conn).iloc[0]['a']
            st.metric("Average BMI", f"{avg_bmi:.1f}")

            high_bp = pd.read_sql_query("SELECT SUM(HighBP) as c FROM patient_health_data", conn).iloc[0]['c']
            st.metric("High Blood Pressure", f"{high_bp/total*100:.1f}%")

            conn.close()
        except Exception as e:
            st.error(f"Couldn't load stats: {e}")

        st.header("Example Questions")

        # Example questions to get started
        samples = [
            "Show me diabetes rates by age group",
            "Is there a connection between BMI and diabetes?",
            "How many people have high blood pressure?",
            "Compare health by general health rating",
            "Do smokers have higher diabetes rates?",
            "Give me an overview of the database",
        ]

        for q in samples:
            if st.button(q, key=q):
                st.session_state.current_question = q
                st.rerun()

    # Main query area
    st.header("Ask a Question")

    col1, col2 = st.columns([4, 1])
    with col1:
        user_question = st.text_input(
            "What would you like to know?",
            value=st.session_state.get('current_question', ''),
            placeholder="e.g., What's the diabetes rate among smokers?"
        )
    with col2:
        st.write("")
        st.write("")
        ask_button = st.button("Ask", type="primary")

    if ask_button and user_question:
        st.session_state.current_question = ""

        with st.spinner("Processing your question..."):
            tool_results, ai_response = process_user_query(user_question)

        # Show what happened behind the scenes
        if tool_results:
            st.subheader("Functions Called")

            for i, tool in enumerate(tool_results, 1):
                with st.expander(f"{i}. {tool['name']}", expanded=True):
                    # Show SQL query in proper format
                    if tool['name'] == 'execute_sql_query' and 'sql_query' in tool['args']:
                        st.markdown("**SQL Query:**")
                        st.code(tool['args']['sql_query'], language="sql")
                    elif tool['args']:
                        st.markdown("**Function Arguments:**")
                        st.code(json.dumps(tool['args'], indent=2), language="json")

                    st.divider()

                    # Show the results
                    result = json.loads(tool['result'])

                    if tool['name'] == 'execute_sql_query':
                        if result.get('success'):
                            st.markdown(f"**Query Results:** {result.get('rows', 0)} rows returned")
                            if result.get('data'):
                                df = pd.DataFrame(result['data'])
                                st.dataframe(df, use_container_width=True)
                                if result['rows'] > len(df):
                                    st.caption(f"Showing first {len(df)} of {result['rows']} rows")
                            else:
                                st.info("Query executed successfully but returned no data")
                        else:
                            st.error(f"Query failed: {result.get('error', 'Unknown error')}")

                    elif tool['name'] == 'get_database_statistics':
                        if 'total_patients' in result:
                            st.markdown("**Database Statistics:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Patients", f"{result['total_patients']:,}")
                                st.metric("Average BMI", result['avg_bmi'])
                                st.metric("High BP Rate", f"{result['high_bp_rate_pct']}%")
                            with col2:
                                st.metric("Diabetic Patients", f"{result['diabetic_patients']:,}")
                                st.metric("Diabetes Rate", f"{result['diabetes_rate_pct']}%")
                                st.metric("Smoker Rate", f"{result['smoker_rate_pct']}%")
                        else:
                            st.error(f"Error: {result.get('error', 'Unknown error')}")

                    elif tool['name'] == 'create_support_ticket':
                        if result.get('status') == 'created':
                            st.success(f"Ticket created: {result.get('ticket_id')}")
                            st.info(result.get('message'))
                        else:
                            st.json(result)
                    else:
                        st.markdown("**Response:**")
                        st.json(result)

        # Show the answer
        if ai_response:
            st.subheader("Answer")
            st.write(ai_response)

    # Help button
    st.divider()

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Need Help?"):
            with st.spinner("Creating support ticket..."):
                result = create_support_ticket(
                    "User requested assistance",
                    user_question if user_question else "General inquiry"
                )
                ticket_info = json.loads(result)
                st.success(f"{ticket_info['message']}\n\nTicket: {ticket_info['ticket_id']}")

    # Footer
    st.markdown("---")
    st.caption("Real CDC BRFSS 2014 data - Privacy protected: AI only sees data structure, not patient details")


if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Starting CDC Diabetes Data Explorer")
    logger.info("="*50)
    main()
