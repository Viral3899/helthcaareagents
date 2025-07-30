"""
Database Connection Module

This module handles database connections, session management, and initialization
for the healthcare management system with async support.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from config.settings import Config
from database.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session manager with async support"""
    
    def __init__(self):
        self.config = Config()
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create synchronous database engine
            self.engine = create_engine(
                self.config.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create async database engine
            if self.config.database_url.startswith('mysql+pymysql://'):
                async_url = self.config.database_url.replace('mysql+pymysql://', 'mysql+aiomysql://')
            elif self.config.database_url.startswith('postgresql+psycopg2://'):
                async_url = self.config.database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
            else:
                async_url = self.config.database_url  # fallback, or handle other cases
            
            self.async_engine = create_async_engine(
                async_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create session factories
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.AsyncSessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.async_engine
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
    
    async def initialize_async(self):
        """Initialize database connection asynchronously"""
        try:
            # Create async database engine
            if self.config.database_url.startswith('mysql+pymysql://'):
                async_url = self.config.database_url.replace('mysql+pymysql://', 'mysql+aiomysql://')
            elif self.config.database_url.startswith('postgresql+psycopg2://'):
                async_url = self.config.database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
            else:
                async_url = self.config.database_url  # fallback, or handle other cases
            
            self.async_engine = create_async_engine(
                async_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create async session factory
            self.AsyncSessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.async_engine
            )
            
            # Test connection
            async with self.async_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                logger.info("Async database connection established successfully")
            
            # Create tables
            await self.create_tables_async()
            
            self._initialized = True
            logger.info("Async database initialization completed")
            
        except OperationalError as e:
            logger.error(f"Async database connection failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Async database initialization failed: {str(e)}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    async def create_tables_async(self):
        """Create all database tables asynchronously"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully (async)")
        except Exception as e:
            logger.error(f"Failed to create tables (async): {str(e)}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            raise
    
    async def drop_tables_async(self):
        """Drop all database tables asynchronously (use with caution)"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped (async)")
        except Exception as e:
            logger.error(f"Failed to drop tables (async): {str(e)}")
            raise
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize_async() first.")
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {str(e)}")
                raise
    
    def get_session_direct(self) -> Session:
        """Get database session directly (synchronous)"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.SessionLocal()
    
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
    
    async def get_async_session_direct(self) -> AsyncSession:
        """Get async database session directly"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize_async() first.")
        
        return self.AsyncSessionLocal()
    
    def health_check(self) -> bool:
        """Check database health (synchronous)"""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    async def health_check_async(self) -> bool:
        """Check database health asynchronously"""
        try:
            async with self.async_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Async database health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information"""
        return {
            "database_url": self.config.database_url,
            "pool_size": 10,
            "max_overflow": 20,
            "initialized": self._initialized
        }
    
    def close(self):
        """Close database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Synchronous database engine disposed")
        except Exception as e:
            logger.error(f"Error disposing synchronous engine: {str(e)}")
    
    async def close_async(self):
        """Close async database connections"""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
                logger.info("Async database engine disposed")
        except Exception as e:
            logger.error(f"Error disposing async engine: {str(e)}")

# Global database manager instance
db_manager = DatabaseManager()

def init_database():
    """Initialize database (synchronous)"""
    db_manager.initialize()

async def init_database_async():
    """Initialize database asynchronously"""
    await db_manager.initialize_async()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session (synchronous) - FIXED VERSION"""
    with db_manager.get_session() as session:
        yield session

@asynccontextmanager
async def get_db_session_async() -> AsyncGenerator[AsyncSession, None]:
    """Get database session asynchronously"""
    async with db_manager.get_async_session() as session:
        yield session

def get_db_session_direct() -> Session:
    """Get database session directly (synchronous)"""
    return db_manager.get_session_direct()

async def get_db_session_direct_async() -> AsyncSession:
    """Get database session directly (async)"""
    return await db_manager.get_async_session_direct()

def check_database_health() -> bool:
    """Check database health (synchronous)"""
    return db_manager.health_check()

async def check_database_health_async() -> bool:
    """Check database health asynchronously"""
    return await db_manager.health_check_async()

def get_database_info() -> dict:
    """Get database information"""
    return db_manager.get_connection_info()

def close_database():
    """Close database connections"""
    db_manager.close()

async def close_database_async():
    """Close async database connections"""
    await db_manager.close_async()

# Dependency injection functions for FastAPI (if needed)
def get_db():
    """FastAPI dependency for database session"""
    with db_manager.get_session() as session:
        yield session

async def get_async_db():
    """FastAPI dependency for async database session"""
    async with db_manager.get_async_session() as session:
        yield session

# Context manager classes for more explicit usage
class DatabaseSession:
    """Context manager for database sessions"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self) -> Session:
        self.session = db_manager.get_session_direct()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is None:
                    self.session.commit()
                else:
                    self.session.rollback()
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")
                self.session.rollback()
            finally:
                self.session.close()

class AsyncDatabaseSession:
    """Async context manager for database sessions"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = await db_manager.get_async_session_direct()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is None:
                    await self.session.commit()
                else:
                    await self.session.rollback()
            except Exception as e:
                logger.error(f"Error in async session cleanup: {str(e)}")
                await self.session.rollback()
            finally:
                await self.session.close()

# Usage examples for the fixed functions:
"""
# Now you can use these patterns in your routes:

# Pattern 1: Using the fixed wrapper function
with get_db_session() as session:
    # Your database operations
    pass

# Pattern 2: Using the manager directly (recommended)
with db_manager.get_session() as session:
    # Your database operations
    pass

# Pattern 3: Using the explicit context manager class
with DatabaseSession() as session:
    # Your database operations
    pass

# Pattern 4: For async operations
async with get_db_session_async() as session:
    # Your async database operations
    pass
"""