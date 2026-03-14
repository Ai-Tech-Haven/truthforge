"""
Migration script to move data from SQLite to PostgreSQL
Run only once when switching to production
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import logging
from database.database import Base
from database.models import *  # Import your models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Source: SQLite
    source_url = os.getenv('SQLITE_URL', 'sqlite:///truthforge.db')
    # Target: PostgreSQL
    target_url = os.getenv('DATABASE_URL')
    
    if not target_url or 'postgres' not in target_url:
        logger.error("PostgreSQL DATABASE_URL not configured")
        return False
    
    logger.info(f"Source: {source_url}")
    logger.info(f"Target: {target_url.split('@')[-1]}")
    
    # Create engines
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)
    
    # Create target tables
    Base.metadata.create_all(bind=target_engine)
    logger.info("Target tables created")
    
    # Check if source database exists
    try:
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Source database not accessible: {e}")
        logger.info("No data to migrate - starting fresh")
        return True
    
    # Get all tables
    inspector = inspect(source_engine)
    tables = inspector.get_table_names()
    
    if not tables:
        logger.info("No tables found in source database")
        return True
    
    for table in tables:
        logger.info(f"Migrating table: {table}")
        
        # Read from source
        with source_engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table}"))
            data = result.fetchall()
            columns = result.keys()
        
        if not data:
            logger.info(f"  No data in {table}")
            continue
        
        # Write to target
        with target_engine.connect() as conn:
            for row in data:
                # Create parameterized query
                placeholders = ', '.join([f':{col}' for col in columns])
                insert_stmt = text(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})")
                
                # Convert row to dict
                row_dict = dict(zip(columns, row))
                conn.execute(insert_stmt, row_dict)
            
            conn.commit()
        
        logger.info(f"  Migrated {len(data)} rows from {table}")
    
    logger.info("Migration complete!")
    return True

if __name__ == "__main__":
    migrate_data()