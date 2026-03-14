#!/usr/bin/env python3
"""
Database Migration Script for TruthForge
Handles schema updates and data migrations
"""
import logging
import sys
from datetime import datetime, timezone

from database.database import init_db, test_connection, engine, Base
from database import models
from database.api_keys import APIKey

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate():
    """Run database migrations"""
    try:
        logger.info("Starting database migration...")
        
        # Test connection
        if not test_connection():
            logger.error("Database connection failed!")
            return False
        
        logger.info("Database connection successful")
        
        # Create all tables
        logger.info("Creating/updating tables...")
        Base.metadata.create_all(bind=engine)
        
        # List created tables
        tables = Base.metadata.tables.keys()
        logger.info(f"Tables in database: {', '.join(tables)}")
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
