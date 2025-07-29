"""
Database Connection Module

This module handles database connections, session management, and initialization
for the healthcare management system.
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from config.settings import Config
from database.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.config = Config()
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create database engine
            self.engine = create_engine(
                self.config.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
            
            # Create tables
            self.create_tables()
            
            self._initialized = True
            logger.info("Database initialization completed")
            
        except OperationalError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get database session directly (manual cleanup required)"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information"""
        if not self.engine:
            return {"status": "not_initialized"}
        
        return {
            "host": self.config.DATABASE_HOST,
            "port": self.config.DATABASE_PORT,
            "database": self.config.DATABASE_NAME,
            "user": self.config.DATABASE_USER,
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow()
        }

# Global database manager instance
db_manager = DatabaseManager()

def init_database():
    """Initialize the database connection"""
    db_manager.initialize()

def get_db_session():
    """Get database session context manager"""
    return db_manager.get_session()

def get_db_session_direct():
    """Get database session directly"""
    return db_manager.get_session_direct()

def check_database_health():
    """Check database health"""
    return db_manager.health_check()

def get_database_info():
    """Get database connection information"""
    return db_manager.get_connection_info()
