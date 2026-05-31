import os
import json
import time
import re
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from databases.models import QueryResult, ChatMessage, Dataset
import uuid
from datetime import datetime
import pandas as pd
from agents.query_validator import QueryValidator
from agents.data_insights import DataInsights
from agents.query_cache import query_cache

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datachat.db")


class SQLAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
        )
        self.validator = QueryValidator()
        self.insights = DataInsights()

    def get_table_info(self, table_name: str) -> str:
        """Get table schema information"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            
            schema = f"Table: {table_name}\n"
            schema += "Columns:\n"
            for col in columns:
                schema += f"  - {col['name']} ({col['type']})\n"
            
            return schema
        except Exception as e:
            return f"Could not get table info: {str(e)}"

    def generate_sql(self, question: str, dataset: Dataset) -> str:
        """Generate SQL query from natural language question using Gemini"""
        try:
            # Build table name from dataset ID
            table_name = f"{dataset.id}_datachat_sample_sales"
            
            # Build prompt with table information
            table_info = "\n".join([
                f"- {col}" for col in (dataset.columns or [])
            ])
            
            prompt = f"""You are a SQL expert. Generate a valid SQLite SQL query to answer this question.

Question: {question}

Database table name: {table_name}
Columns in the table:
{table_info}

Row count: {dataset.row_count}

IMPORTANT RULES:
1. Return ONLY the SELECT query, nothing else - no explanations
2. Do NOT include markdown code blocks (no ``` or ```sql)
3. Use SQLite syntax
4. Use the exact table name: {table_name}
5. Limit results to 100 rows max
6. Use proper GROUP BY clauses when needed

Generate the SQL query:"""
            
            response = self.llm.invoke(prompt)
            sql_query = response.content.strip()
            
            # Clean up the response - remove markdown code blocks
            if "```" in sql_query:
                # Extract content between ``` markers
                parts = sql_query.split("```")
                sql_query = parts[1] if len(parts) > 1 else parts[0]
            
            # Remove language identifiers like "sql" or "sqlite"
            sql_query = sql_query.strip()
            if sql_query.lower().startswith("sql"):
                # Remove 'sql' or 'sqlite' prefix (case-insensitive)
                if sql_query.lower().startswith("sqlite"):
                    sql_query = sql_query[6:].strip()
                else:
                    sql_query = sql_query[3:].strip()
            
            sql_query = sql_query.strip()
            return sql_query
            
        except Exception as e:
            raise Exception(f"Error generating SQL: {str(e)}")

    def execute_query(self, sql_query: str) -> dict:
        """Execute SQL query and return results"""
        try:
            # Validate SQL query starts with SELECT
            if not sql_query.strip().upper().startswith("SELECT"):
                raise Exception("Invalid query: must be a SELECT statement")
            
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                
                # Get column names
                columns = [col for col in result.keys()]
                
                # Fetch results
                rows = []
                for row in result.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    rows.append(row_dict)
                
                return {
                    "columns": columns,
                    "rows": rows
                }
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    def generate_follow_up_questions(self, question: str, results_sample: list, dataset: Dataset, chat_history: list) -> list:
        """Generate suggested follow-up questions based on current results and context"""
        try:
            # Build context from recent chat history
            context_str = ""
            if chat_history:
                context_str = "Recent conversation:\n"
                for msg in chat_history[-6:]:  # Last 6 messages (3 exchanges)
                    context_str += f"- {msg['sender']}: {msg['content']}\n"
            
            # Get sample results summary
            sample_summary = ""
            if results_sample:
                sample_summary = f"Last query returned {len(results_sample)} results with columns: {', '.join(results_sample[0].keys() if results_sample[0] else [])}"
            
            prompt = f"""You are a data analysis assistant. Generate 3 insightful follow-up questions based on the conversation and data.

Current question: {question}
Data insight: {sample_summary}

{context_str}

Generate exactly 3 follow-up questions that would provide deeper insights into the data. Questions should:
1. Build on the current findings
2. Be answerable with the available data
3. Explore different angles or drill down deeper
4. Be concise (under 15 words each)

Format your response as a JSON array with exactly 3 questions:
["Question 1?", "Question 2?", "Question 3?"]

Return ONLY the JSON array, nothing else."""
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON array
            try:
                # Try to find and parse JSON array
                if "[" in response_text and "]" in response_text:
                    start = response_text.index("[")
                    end = response_text.rindex("]") + 1
                    json_str = response_text[start:end]
                    questions = json.loads(json_str)
                    # Ensure we have exactly 3 questions
                    return questions[:3] if isinstance(questions, list) else []
            except json.JSONDecodeError:
                pass
            
            return []
            
        except Exception as e:
            print(f"Error generating follow-up questions: {str(e)}")
            return []

    def query(self, question: str, dataset_id: str, db_session: Session) -> dict:
        """Execute natural language query against dataset with caching"""
        try:
            start_time = time.time()
            
            # Get dataset
            dataset = db_session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return {
                    "success": False,
                    "error": "Dataset not found"
                }
            
            # Check cache first
            cached_result = query_cache.get(dataset_id, question)
            if cached_result:
                execution_time = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "data": cached_result["result"],
                    "cache": {
                        "hit": True,
                        "cachedAt": cached_result["cached_at"]
                    },
                    "executionTime": execution_time
                }
            
            # Validate query before processing
            validation_result = self.validator.validate(question, dataset)
            
            if not validation_result["is_valid"] and validation_result["confidence"] > 0.8:
                # High confidence that query is invalid
                return {
                    "success": False,
                    "error": f"Invalid query: {validation_result['reason']}",
                    "validation": validation_result
                }
            
            # Generate SQL
            sql_query = self.generate_sql(question, dataset)
            
            # Execute query
            result = self.execute_query(sql_query)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Store query result
            query_record = QueryResult(
                id=f"query_{uuid.uuid4().hex[:12]}",
                dataset_id=dataset_id,
                query=question,
                sql_query=sql_query,
                rows_data=result["rows"],
                execution_time=execution_time,
                created_at=datetime.utcnow()
            )
            db_session.add(query_record)
            
            # Fetch chat history for context
            chat_history = db_session.query(ChatMessage).filter(
                ChatMessage.dataset_id == dataset_id
            ).order_by(ChatMessage.timestamp.asc()).all()
            
            chat_history_list = [
                {"sender": m.sender, "content": m.content}
                for m in chat_history
            ]
            
            # Store messages
            user_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                dataset_id=dataset_id,
                content=question,
                sender="user",
                timestamp=datetime.utcnow()
            )
            
            assistant_msg = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                dataset_id=dataset_id,
                content=f"Found {len(result['rows'])} results in {execution_time}ms",
                sender="assistant",
                timestamp=datetime.utcnow()
            )
            
            db_session.add(user_msg)
            db_session.add(assistant_msg)
            db_session.commit()
            
            # Generate follow-up questions with context
            follow_up_questions = self.generate_follow_up_questions(
                question,
                result["rows"][:10],  # Pass sample of results
                dataset,
                chat_history_list
            )
            
            # Generate insights from results
            insights_result = self.insights.analyze(
                question,
                result["rows"],
                result["columns"],
                dataset
            )
            
            # Build response before caching
            response_data = {
                "id": query_record.id,
                "query": question,
                "rows": result["rows"],
                "columns": result["columns"],
                "executionTime": execution_time,
                "followUpQuestions": follow_up_questions,
                "insights": insights_result,
                "validation": validation_result if validation_result["confidence"] < 1.0 else None,
                "cache": {
                    "hit": False
                }
            }
            
            # Store in cache for next time
            query_cache.set(dataset_id, question, response_data)
            
            return {
                "success": True,
                "data": response_data
            }
            
        except Exception as e:
            db_session.rollback()
            return {
                "success": False,
                "error": str(e)
            }


# Global agent instance
_agent = None


def get_sql_agent():
    global _agent
    if _agent is None:
        _agent = SQLAgent()
    return _agent


def get_sql_agent_for_dataset(dataset_id: str, db_session: Session):
    """Get SQL agent for a specific dataset"""
    try:
        dataset = db_session.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return None
        return get_sql_agent()
    except Exception as e:
        print(f"Error creating agent: {e}")
        return None
