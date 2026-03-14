"""
Database Manager for TruthForge

Provides utilities for database operations, connection management,
and health checks.
"""
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from database.database import db_session, engine, test_connection, get_stats

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    @staticmethod
    def get_session():
        """Get a database session"""
        return db_session()
    
    @staticmethod
    @contextmanager
    def session_scope():
        """
        Provide a transactional scope for database operations.
        
        Usage:
            with DatabaseManager.session_scope() as session:
                session.add(obj)
                # Automatically commits on success, rolls back on error
        """
        session = db_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def health_check() -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            Dict with health status and statistics
        """
        try:
            is_connected = test_connection()
            stats = get_stats()
            
            return {
                'status': 'healthy' if is_connected else 'unhealthy',
                'connected': is_connected,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
    
    @staticmethod
    def close_all_sessions():
        """Close all database sessions"""
        try:
            db_session.remove()
            logger.info("All database sessions closed")
        except Exception as e:
            logger.error(f"Error closing sessions: {e}")
    
    @staticmethod
    def dispose_engine():
        """Dispose of the database engine and connection pool"""
        try:
            engine.dispose()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.error(f"Error disposing engine: {e}")


# Convenience functions
def get_db_session():
    """Get a new database session"""
    return DatabaseManager.get_session()


def with_db_session(func):
    """
    Decorator to provide database session to function.
    
    Usage:
        @with_db_session
        def my_function(session, other_args):
            session.add(obj)
    """
    def wrapper(*args, **kwargs):
        with DatabaseManager.session_scope() as session:
            return func(session, *args, **kwargs)
    return wrapper
