#!/usr/bin/env python3
"""
Initialize TruthForge Database
Creates all required tables for production
"""
import logging
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import init_db, test_connection, get_stats
from database import models
from database.api_keys import APIKey

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize database"""
    try:
        logger.info("=" * 60)
        logger.info("TruthForge Database Initialization")
        logger.info("=" * 60)
        
        # Test connection first
        logger.info("Testing database connection...")
        if not test_connection():
            logger.error("❌ Database connection failed!")
            logger.error("Please check your DATABASE_URL in .env file")
            return False
        
        logger.info("✅ Database connection successful")
        
        # Get database stats
        stats = get_stats()
        logger.info(f"Database Type: {stats['type']}")
        logger.info(f"Database URL: {stats['url']}")
        
        # Initialize database (create tables)
        logger.info("\nCreating database tables...")
        init_db()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("=" * 60)
        logger.info("\nTables created:")
        logger.info("  - verifications")
        logger.info("  - agent_status")
        logger.info("  - shipments")
        logger.info("  - port_trust_receipts")
        logger.info("  - audit_trails")
        logger.info("  - dashboard_metrics")
        logger.info("  - api_keys")
        logger.info("\nYou can now start the TruthForge system with:")
        logger.info("  python main.py")
        logger.info("  OR")
        logger.info("  start_production.bat")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Database initialization failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
