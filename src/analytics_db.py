"""
Analytics database module for tracking email classification history.
Uses SQLite to store email metadata and provide analytics queries.
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os


class AnalyticsDB:
    """Database handler for email analytics tracking"""
    
    def __init__(self, db_path: str = "analytics.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_schema()
    
    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def _initialize_schema(self):
        """Create tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Main emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                subject TEXT,
                sender TEXT,
                category TEXT,
                category_label TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                thread_id TEXT,
                is_important BOOLEAN,
                snippet TEXT
            )
        """)
        
        # Index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON emails(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category 
            ON emails(category)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_important 
            ON emails(is_important)
        """)
        
        self.conn.commit()
    
    def record_email(self, email_id: str, subject: str, sender: str, 
                    category: str, category_label: str, is_important: bool,
                    snippet: str = "", thread_id: str = None) -> bool:
        """
        Record a classified email to the database
        
        Args:
            email_id: Gmail message ID
            subject: Email subject line
            sender: Email sender address
            category: Category key (e.g., 'interview_request')
            category_label: Display label (e.g., 'Interview 📅')
            is_important: Whether email is in important categories
            snippet: Email preview text
            thread_id: Gmail thread ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO emails 
                (id, subject, sender, category, category_label, is_important, snippet, thread_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (email_id, subject, sender, category, category_label, 
                  is_important, snippet, thread_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording email to analytics DB: {e}")
            return False
    
    def get_emails_by_date_range(self, days: int = 30) -> List[Dict]:
        """
        Get all emails from the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of email records as dictionaries
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT * FROM emails 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (cutoff_date,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_category_counts(self, days: int = 30) -> Dict[str, int]:
        """
        Get email count by category for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary mapping category_label to count
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT category_label, COUNT(*) as count
            FROM emails
            WHERE timestamp >= ?
            GROUP BY category_label
            ORDER BY count DESC
        """, (cutoff_date,))
        
        return {row['category_label']: row['count'] for row in cursor.fetchall()}
    
    def get_daily_volume(self, days: int = 30) -> List[Tuple[str, int]]:
        """
        Get daily email volume for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of (date, count) tuples
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM emails
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """, (cutoff_date,))
        
        return [(row['date'], row['count']) for row in cursor.fetchall()]
    
    def get_daily_volume_by_category(self, days: int = 30) -> Dict[str, List[Tuple[str, int]]]:
        """
        Get daily email volume broken down by category
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary mapping category_label to list of (date, count) tuples
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT category_label, DATE(timestamp) as date, COUNT(*) as count
            FROM emails
            WHERE timestamp >= ?
            GROUP BY category_label, DATE(timestamp)
            ORDER BY date ASC
        """, (cutoff_date,))
        
        result = {}
        for row in cursor.fetchall():
            category = row['category_label']
            if category not in result:
                result[category] = []
            result[category].append((row['date'], row['count']))
        
        return result
    
    def get_important_email_stats(self, days: int = 30) -> Dict:
        """
        Get statistics about important emails
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with important email metrics
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Total emails
        cursor.execute("""
            SELECT COUNT(*) as total FROM emails
            WHERE timestamp >= ?
        """, (cutoff_date,))
        total = cursor.fetchone()['total']
        
        # Important emails
        cursor.execute("""
            SELECT COUNT(*) as important FROM emails
            WHERE timestamp >= ? AND is_important = 1
        """, (cutoff_date,))
        important = cursor.fetchone()['important']
        
        # Important by category
        cursor.execute("""
            SELECT category_label, COUNT(*) as count
            FROM emails
            WHERE timestamp >= ? AND is_important = 1
            GROUP BY category_label
        """, (cutoff_date,))
        
        by_category = {row['category_label']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total_emails': total,
            'important_emails': important,
            'important_percentage': (important / total * 100) if total > 0 else 0,
            'by_category': by_category
        }
    
    def get_top_senders(self, days: int = 30, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get top email senders by volume
        
        Args:
            days: Number of days to look back
            limit: Maximum number of senders to return
            
        Returns:
            List of (sender, count) tuples
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT sender, COUNT(*) as count
            FROM emails
            WHERE timestamp >= ?
            GROUP BY sender
            ORDER BY count DESC
            LIMIT ?
        """, (cutoff_date, limit))
        
        return [(row['sender'], row['count']) for row in cursor.fetchall()]
    
    def get_total_email_count(self) -> int:
        """Get total number of emails in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM emails")
        return cursor.fetchone()['count']
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global database instance
_db_instance = None

def get_analytics_db(db_path: str = "analytics.db") -> AnalyticsDB:
    """Get or create the global analytics database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = AnalyticsDB(db_path)
    return _db_instance
