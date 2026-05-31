from sqlalchemy import Column, String, Integer, DateTime, Text, LargeBinary, JSON, create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datachat.db")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    } if "sqlite" in DATABASE_URL else {
        "connect_timeout": 10,
    },
    pool_pre_ping=True,  # Verify connection health
    pool_recycle=3600,   # Recycle connections every hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    filename = Column(String)
    row_count = Column(Integer)
    columns = Column(JSON)  # Store column names as JSON
    profile = Column(JSON)  # Store data profile (summary, stats, quality)
    owner_id = Column(String, nullable=True)  # Optional owner reference
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, index=True)
    content = Column(Text)
    sender = Column(String)  # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)


class QueryResult(Base):
    __tablename__ = "query_results"

    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, index=True)
    query = Column(String)
    sql_query = Column(String)
    rows_data = Column(JSON)  # Store results as JSON
    execution_time = Column(Integer)  # milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)


# Initialize tables on first use
def init_db():
    """Initialize database tables"""
    try:
        # Import collaboration models to register them with Base
        from databases.collaboration_models import (
            User, Team, TeamMember, Dashboard, Widget, 
            ScheduledReport, ReportRun, SavedQuery, QueryHistory
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
