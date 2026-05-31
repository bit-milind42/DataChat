"""Database configuration module - Support for multiple database types"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class DatabaseConfig:
    """Manages database connections for different providers"""
    
    # Default SQLite connection
    DEFAULT_DATABASE_URL = "sqlite:///./datachat.db"
    
    @staticmethod
    def validate_connection_string(connection_string: str) -> bool:
        """Validate if a connection string is valid"""
        try:
            if not connection_string:
                return False
            
            # Check for common database schemes
            valid_schemes = ['sqlite://', 'postgresql://', 'mysql+pymysql://', 'mysql+mysqlconnector://']
            return any(connection_string.startswith(scheme) for scheme in valid_schemes)
        except Exception:
            return False
    
    @staticmethod
    def create_engine_for_db(database_url: Optional[str] = None) -> Engine:
        """Create SQLAlchemy engine for specified database"""
        try:
            url = database_url or os.getenv("DATABASE_URL", DatabaseConfig.DEFAULT_DATABASE_URL)
            
            if not DatabaseConfig.validate_connection_string(url):
                url = DatabaseConfig.DEFAULT_DATABASE_URL
            
            # SQLite specific args
            if "sqlite" in url:
                return create_engine(
                    url,
                    connect_args={"check_same_thread": False}
                )
            
            # PostgreSQL / MySQL
            return create_engine(
                url,
                pool_pre_ping=True,  # Test connections before use
                pool_recycle=3600,    # Recycle connections every hour
                connect_args={"timeout": 10}
            )
        
        except Exception as e:
            print(f"Database connection error: {e}")
            # Fallback to SQLite
            return create_engine(
                DatabaseConfig.DEFAULT_DATABASE_URL,
                connect_args={"check_same_thread": False}
            )
    
    @staticmethod
    def get_driver_name(database_url: str) -> str:
        """Get database driver name from connection string"""
        if "postgresql" in database_url:
            return "postgresql"
        elif "mysql" in database_url:
            return "mysql"
        elif "sqlite" in database_url:
            return "sqlite"
        return "unknown"
    
    @staticmethod
    def get_database_info(database_url: str) -> dict:
        """Extract database information from connection string"""
        driver = DatabaseConfig.get_driver_name(database_url)
        
        info = {
            "driver": driver,
            "display_name": driver.upper()
        }
        
        # Parse connection details
        if driver == "sqlite":
            info["path"] = database_url.replace("sqlite:///", "")
        elif driver == "postgresql":
            info["type"] = "PostgreSQL"
            info["port"] = "5432 (default)"
        elif driver == "mysql":
            info["type"] = "MySQL"
            info["port"] = "3306 (default)"
        
        return info
