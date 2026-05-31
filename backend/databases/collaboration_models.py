"""Dashboard models for custom dashboards and team collaboration"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from databases.models import Base

# Association table for dashboard sharing
dashboard_share_table = Table(
    'dashboard_shares',
    Base.metadata,
    Column('dashboard_id', String, ForeignKey('dashboards.id')),
    Column('user_id', String, ForeignKey('users.id'))
)

# Association table for dashboard widgets
dashboard_widget_table = Table(
    'dashboard_widgets',
    Base.metadata,
    Column('dashboard_id', String, ForeignKey('dashboards.id')),
    Column('widget_id', String, ForeignKey('widgets.id'))
)


class User(Base):
    """User model for team collaboration"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # admin, editor, viewer
    
    # Relationships
    dashboards = relationship("Dashboard", back_populates="owner")
    teams = relationship("Team", back_populates="owner")
    shared_dashboards = relationship(
        "Dashboard",
        secondary=dashboard_share_table,
        back_populates="shared_with"
    )


class Team(Base):
    """Team model for collaboration"""
    __tablename__ = "teams"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Team member model"""
    __tablename__ = "team_members"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    role = Column(String, default="member")  # admin, editor, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="members")


class Dashboard(Base):
    """Custom dashboard model"""
    __tablename__ = "dashboards"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    dataset_ids = Column(JSON, default=list)  # List of dataset IDs
    layout = Column(JSON, default=dict)  # Grid layout configuration
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="dashboards")
    shared_with = relationship(
        "User",
        secondary=dashboard_share_table,
        back_populates="shared_dashboards"
    )
    widgets = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")
    reports = relationship("ScheduledReport", back_populates="dashboard", cascade="all, delete-orphan")


class Widget(Base):
    """Dashboard widget (chart, table, KPI, etc.)"""
    __tablename__ = "widgets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dashboard_id = Column(String, ForeignKey('dashboards.id'), nullable=False)
    title = Column(String, nullable=False)
    widget_type = Column(String, nullable=False)  # chart, table, kpi, metric
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)
    height = Column(Integer, default=3)
    config = Column(JSON, default=dict)  # Chart/widget specific config
    query_id = Column(String, nullable=True)  # Link to saved query
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")


class ScheduledReport(Base):
    """Scheduled report model"""
    __tablename__ = "scheduled_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dashboard_id = Column(String, ForeignKey('dashboards.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    schedule = Column(String, nullable=False)  # cron expression: '0 9 * * MON', '0 0 * * *'
    frequency = Column(String, nullable=False)  # daily, weekly, monthly
    recipients = Column(JSON, default=list)  # Email addresses
    format = Column(String, default="pdf")  # pdf, excel, html
    include_insights = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="reports")
    runs = relationship("ReportRun", back_populates="report", cascade="all, delete-orphan")


class ReportRun(Base):
    """Individual report run history"""
    __tablename__ = "report_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('scheduled_reports.id'), nullable=False)
    status = Column(String, default="pending")  # pending, completed, failed
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    sent_to = Column(JSON, default=list)  # Emails successfully sent to
    
    # Relationships
    report = relationship("ScheduledReport", back_populates="runs")


class SavedQuery(Base):
    """Saved query model for dashboard widgets"""
    __tablename__ = "saved_queries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    dataset_id = Column(String, ForeignKey('datasets.id'), nullable=False)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    question = Column(String, nullable=False)
    query_result_id = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QueryHistory(Base):
    """Enhanced query history with context"""
    __tablename__ = "query_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    dataset_id = Column(String, ForeignKey('datasets.id'), nullable=False)
    question = Column(String, nullable=False)
    generated_sql = Column(String, nullable=True)
    status = Column(String, default="completed")  # completed, failed
    execution_time = Column(Integer, nullable=True)  # milliseconds
    row_count = Column(Integer, default=0)
    follow_up_questions = Column(JSON, default=list)
    insights = Column(JSON, default=dict)
    parent_query_id = Column(String, nullable=True)  # For follow-up queries
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
