"""
Database utilities for Captura portfolio management.
Handles SQLite database operations for portfolios and holdings.
"""

import sqlite3
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages SQLite database operations for portfolio data.
    """
    
    def __init__(self, db_path: str = "captura.db"):
        """
        Initialize database manager.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        # Get the absolute path to the schema file
        self.schema_path = self._get_schema_path()
        self._initialize_database()
    
    def _get_schema_path(self):
        """
        Get the absolute path to the database schema file.
        Works from any directory by finding the backend directory.
        """
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Navigate to the backend directory (parent of utils)
        backend_dir = os.path.dirname(current_dir)
        
        # Construct the schema file path
        schema_path = os.path.join(backend_dir, "database_schema.sql")
        
        logger.info(f"Looking for schema file at: {schema_path}")
        return schema_path
    
    def _initialize_database(self):
        """
        Initialize database by creating it and running schema if needed.
        Always ensures schema is applied, even for existing databases.
        """
        try:
            # Check if database exists
            if not os.path.exists(self.db_path):
                logger.info(f"Creating new database: {self.db_path}")
                self._create_database()
            else:
                logger.info(f"Using existing database: {self.db_path}")
                # Always ensure schema is applied for existing databases
                self._ensure_schema_applied()
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _create_database(self):
        """
        Create database and run schema.
        """
        try:
            # Read and execute schema
            if os.path.exists(self.schema_path):
                logger.info(f"Applying schema from: {self.schema_path}")
                self._execute_schema()
            else:
                logger.warning(f"Schema file not found: {self.schema_path}")
                # Create basic tables if schema file is missing
                self._create_basic_tables()
                
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            raise
    
    def _ensure_schema_applied(self):
        """
        Ensure schema is applied to existing database.
        Checks if tables exist and applies schema if needed.
        """
        try:
            with self.get_connection() as conn:
                # Check if portfolios table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='portfolios'
                """)
                
                if not cursor.fetchone():
                    logger.info("Portfolios table not found, applying schema")
                    if os.path.exists(self.schema_path):
                        self._execute_schema()
                    else:
                        logger.warning("Schema file not found, creating basic tables")
                        self._create_basic_tables()
                else:
                    logger.info("Database schema already applied")
                    
        except Exception as e:
            logger.error(f"Failed to ensure schema applied: {str(e)}")
            raise
    
    def _execute_schema(self):
        """
        Execute the database schema from the schema file.
        """
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as schema_file:
                schema_sql = schema_file.read()
            
            logger.info(f"Schema file content length: {len(schema_sql)} characters")
            
            with self.get_connection() as conn:
                # Split schema into individual statements
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                logger.info(f"Found {len(statements)} statements to execute")
                
                executed_count = 0
                for i, statement in enumerate(statements):
                    # Execute all non-empty statements
                    if statement.strip():
                        try:
                            conn.execute(statement)
                            executed_count += 1
                            logger.debug(f"Executed statement {i+1}: {statement[:50]}...")
                        except sqlite3.Error as e:
                            # Some statements might fail if they already exist (like CREATE TABLE IF NOT EXISTS)
                            if "already exists" not in str(e).lower():
                                logger.error(f"Statement {i+1} failed: {str(e)}")
                                logger.error(f"Failed statement: {statement}")
                                raise
                            else:
                                logger.debug(f"Statement {i+1} skipped (already exists): {statement[:50]}...")
                
                conn.commit()
                logger.info(f"Database schema executed successfully - {executed_count} statements executed")
                
                # Verify tables were created
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Tables created: {tables}")
                
        except Exception as e:
            logger.error(f"Failed to execute schema: {str(e)}")
            raise
    
    def _create_basic_tables(self):
        """
        Create basic tables if schema file is not available.
        """
        with self.get_connection() as conn:
            # Create portfolios table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_name TEXT NOT NULL
                )
            """)
            
            # Create holdings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    shares REAL NOT NULL,
                    purchase_price REAL NOT NULL,
                    purchase_date DATE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolios_upload_date ON portfolios(upload_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id ON holdings(portfolio_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_holdings_ticker ON holdings(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_holdings_purchase_date ON holdings(purchase_date)")
            
            conn.commit()
            logger.info("Basic database tables created")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_portfolio(self, user_id: str, file_name: str) -> int:
        """
        Insert a new portfolio record.
        
        Args:
            user_id (str): User identifier
            file_name (str): Original filename of uploaded CSV
            
        Returns:
            int: Portfolio ID of the inserted record
            
        Raises:
            Exception: If insertion fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO portfolios (user_id, file_name) VALUES (?, ?)",
                    (user_id, file_name)
                )
                portfolio_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Inserted portfolio {portfolio_id} for user {user_id}")
                return portfolio_id
                
        except Exception as e:
            logger.error(f"Failed to insert portfolio: {str(e)}")
            raise
    
    def insert_holdings(self, portfolio_id: int, holdings_list: List[Dict[str, Any]]) -> int:
        """
        Insert multiple holdings for a portfolio.
        
        Args:
            portfolio_id (int): Portfolio ID to associate holdings with
            holdings_list (List[Dict]): List of holding dictionaries
            
        Returns:
            int: Number of holdings inserted
            
        Raises:
            Exception: If insertion fails
        """
        try:
            with self.get_connection() as conn:
                inserted_count = 0
                
                for holding in holdings_list:
                    cursor = conn.execute(
                        """INSERT INTO holdings 
                           (portfolio_id, ticker, shares, purchase_price, purchase_date) 
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            portfolio_id,
                            holding['ticker'],
                            holding['shares'],
                            holding['purchase_price'],
                            holding['purchase_date']
                        )
                    )
                    inserted_count += 1
                
                conn.commit()
                logger.info(f"Inserted {inserted_count} holdings for portfolio {portfolio_id}")
                return inserted_count
                
        except Exception as e:
            logger.error(f"Failed to insert holdings: {str(e)}")
            raise
    
    def get_portfolio_by_id(self, portfolio_id: int) -> Optional[Dict[str, Any]]:
        """
        Get portfolio information by ID.
        
        Args:
            portfolio_id (int): Portfolio ID to retrieve
            
        Returns:
            Optional[Dict]: Portfolio data or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM portfolios WHERE id = ?",
                    (portfolio_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get portfolio {portfolio_id}: {str(e)}")
            raise
    
    def get_holdings_by_portfolio(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """
        Get all holdings for a specific portfolio.
        
        Args:
            portfolio_id (int): Portfolio ID to get holdings for
            
        Returns:
            List[Dict]: List of holding dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """SELECT h.*, p.file_name, p.upload_date 
                       FROM holdings h 
                       JOIN portfolios p ON h.portfolio_id = p.id 
                       WHERE h.portfolio_id = ? 
                       ORDER BY h.ticker""",
                    (portfolio_id,)
                )
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get holdings for portfolio {portfolio_id}: {str(e)}")
            raise
    
    def get_portfolios_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all portfolios for a specific user.
        
        Args:
            user_id (str): User ID to get portfolios for
            
        Returns:
            List[Dict]: List of portfolio dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """SELECT p.*, COUNT(h.id) as holdings_count,
                              SUM(h.shares * h.purchase_price) as total_invested
                       FROM portfolios p
                       LEFT JOIN holdings h ON p.id = h.portfolio_id
                       WHERE p.user_id = ?
                       GROUP BY p.id, p.user_id, p.upload_date, p.file_name
                       ORDER BY p.upload_date DESC""",
                    (user_id,)
                )
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get portfolios for user {user_id}: {str(e)}")
            raise
    
    def get_portfolio_summary(self, portfolio_id: int) -> Optional[Dict[str, Any]]:
        """
        Get portfolio summary with aggregated data.
        
        Args:
            portfolio_id (int): Portfolio ID to get summary for
            
        Returns:
            Optional[Dict]: Portfolio summary or None if not found
        """
        try:
            with self.get_connection() as conn:
                # Get portfolio info
                portfolio = self.get_portfolio_by_id(portfolio_id)
                if not portfolio:
                    return None
                
                # Get aggregated holdings data
                cursor = conn.execute(
                    """SELECT 
                           COUNT(*) as total_holdings,
                           SUM(shares * purchase_price) as total_invested,
                           AVG(purchase_price) as avg_price,
                           MIN(purchase_date) as earliest_purchase,
                           MAX(purchase_date) as latest_purchase
                       FROM holdings 
                       WHERE portfolio_id = ?""",
                    (portfolio_id,)
                )
                summary = cursor.fetchone()
                
                # Combine portfolio and summary data
                result = dict(portfolio)
                if summary:
                    result.update(dict(summary))
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get portfolio summary {portfolio_id}: {str(e)}")
            raise
    
    def delete_portfolio(self, portfolio_id: int) -> bool:
        """
        Delete a portfolio and all its holdings.
        
        Args:
            portfolio_id (int): Portfolio ID to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                # Check if portfolio exists
                portfolio = self.get_portfolio_by_id(portfolio_id)
                if not portfolio:
                    logger.warning(f"Portfolio {portfolio_id} not found for deletion")
                    return False
                
                # Delete portfolio (holdings will be deleted automatically due to CASCADE)
                cursor = conn.execute(
                    "DELETE FROM portfolios WHERE id = ?",
                    (portfolio_id,)
                )
                conn.commit()
                
                logger.info(f"Deleted portfolio {portfolio_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete portfolio {portfolio_id}: {str(e)}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dict: Database statistics
        """
        try:
            with self.get_connection() as conn:
                # Get portfolio count
                cursor = conn.execute("SELECT COUNT(*) as count FROM portfolios")
                portfolio_count = cursor.fetchone()['count']
                
                # Get holdings count
                cursor = conn.execute("SELECT COUNT(*) as count FROM holdings")
                holdings_count = cursor.fetchone()['count']
                
                # Get unique users count
                cursor = conn.execute("SELECT COUNT(DISTINCT user_id) as count FROM portfolios")
                user_count = cursor.fetchone()['count']
                
                # Get unique tickers count
                cursor = conn.execute("SELECT COUNT(DISTINCT ticker) as count FROM holdings")
                ticker_count = cursor.fetchone()['count']
                
                return {
                    'portfolios': portfolio_count,
                    'holdings': holdings_count,
                    'users': user_count,
                    'unique_tickers': ticker_count,
                    'database_path': self.db_path
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            raise


# Global database manager instance
# Use absolute path to ensure database is created in the backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(backend_dir, "captura.db")
db_manager = DatabaseManager(db_path)


# Convenience functions for easy access
def insert_portfolio(user_id: str, file_name: str) -> int:
    """Insert a new portfolio record."""
    return db_manager.insert_portfolio(user_id, file_name)


def insert_holdings(portfolio_id: int, holdings_list: List[Dict[str, Any]]) -> int:
    """Insert multiple holdings for a portfolio."""
    return db_manager.insert_holdings(portfolio_id, holdings_list)


def get_portfolio_by_id(portfolio_id: int) -> Optional[Dict[str, Any]]:
    """Get portfolio information by ID."""
    return db_manager.get_portfolio_by_id(portfolio_id)


def get_holdings_by_portfolio(portfolio_id: int) -> List[Dict[str, Any]]:
    """Get all holdings for a specific portfolio."""
    return db_manager.get_holdings_by_portfolio(portfolio_id)


def get_portfolios_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all portfolios for a specific user."""
    return db_manager.get_portfolios_by_user(user_id)


def get_portfolio_summary(portfolio_id: int) -> Optional[Dict[str, Any]]:
    """Get portfolio summary with aggregated data."""
    return db_manager.get_portfolio_summary(portfolio_id)


def delete_portfolio(portfolio_id: int) -> bool:
    """Delete a portfolio and all its holdings."""
    return db_manager.delete_portfolio(portfolio_id)


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    return db_manager.get_database_stats()


# Example usage and testing
if __name__ == "__main__":
    # Test database operations
    try:
        # Test database initialization
        print("Testing database initialization...")
        stats = get_database_stats()
        print(f"Database stats: {stats}")
        
        # Test portfolio insertion
        print("\nTesting portfolio insertion...")
        portfolio_id = insert_portfolio("test_user@example.com", "test_portfolio.csv")
        print(f"Inserted portfolio with ID: {portfolio_id}")
        
        # Test holdings insertion
        print("\nTesting holdings insertion...")
        sample_holdings = [
            {
                'ticker': 'AAPL',
                'shares': 50.0,
                'purchase_price': 175.43,
                'purchase_date': '2024-01-15'
            },
            {
                'ticker': 'MSFT',
                'shares': 30.0,
                'purchase_price': 378.85,
                'purchase_date': '2024-01-20'
            }
        ]
        
        holdings_count = insert_holdings(portfolio_id, sample_holdings)
        print(f"Inserted {holdings_count} holdings")
        
        # Test retrieval
        print("\nTesting data retrieval...")
        portfolio = get_portfolio_by_id(portfolio_id)
        print(f"Retrieved portfolio: {portfolio}")
        
        holdings = get_holdings_by_portfolio(portfolio_id)
        print(f"Retrieved {len(holdings)} holdings")
        
        summary = get_portfolio_summary(portfolio_id)
        print(f"Portfolio summary: {summary}")
        
        # Test user portfolios
        user_portfolios = get_portfolios_by_user("test_user@example.com")
        print(f"User has {len(user_portfolios)} portfolios")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        logger.error(f"Database test failed: {str(e)}")
