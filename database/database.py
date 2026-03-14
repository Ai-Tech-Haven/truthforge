"""
Database module for TruthForge with dual SQLite/PostgreSQL support
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, NullPool
import logging

# Load environment variables first
load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///truthforge.db')
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
DB_POOL_PRE_PING = os.getenv('DB_POOL_PRE_PING', 'True').lower() == 'true'

# Configure engine based on database type
engine_kwargs = {}

if DB_TYPE == 'postgresql':
    # PostgreSQL with connection pooling
    engine_kwargs = {
        'poolclass': QueuePool,
        'pool_size': DB_POOL_SIZE,
        'max_overflow': DB_MAX_OVERFLOW,
        'pool_pre_ping': DB_POOL_PRE_PING,
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'connect_args': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }
    logger.info(f"Initializing PostgreSQL connection pool (size={DB_POOL_SIZE}, overflow={DB_MAX_OVERFLOW})")
else:
    # SQLite with simple pooling
    engine_kwargs = {
        'poolclass': NullPool,  # SQLite doesn't need pooling
        'connect_args': {'check_same_thread': False}
    }
    logger.info("Initializing SQLite database")

# Create engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create scoped session for thread safety
db_session = scoped_session(SessionLocal)

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to register them with Base
        from database import models
        from database.api_keys import APIKey
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully ({DB_TYPE})")
        logger.info(f"Tables created: {', '.join(Base.metadata.tables.keys())}")
        
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def get_db():
    """Dependency to get database session"""
    db = db_session()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1")).scalar()
            logger.info(f"Database connection test: {'SUCCESS' if result == 1 else 'FAILED'}")
            return result == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def get_stats():
    """Get database connection statistics"""
    stats = {
        'type': DB_TYPE,
        'url': DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'local',
        'pool_size': DB_POOL_SIZE if DB_TYPE == 'postgresql' else 'N/A',
        'active_connections': 'N/A'  # Would need pg_stat_activity for real stats
    }
    return stats